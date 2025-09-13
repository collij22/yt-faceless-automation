"""Tests for Phase 7: Analytics & Optimization functionality."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_faceless.core.schemas import (
    AnalyticsRequest,
    Anomaly,
    EnhancedAnalyticsSnapshot,
    EngagementAnalysis,
    ExperimentVariant,
    Geography,
    KPIMetrics,
    MonetizationMetrics,
    MultiVariantExperiment,
    PerformancePredictions,
    RetentionPoint,
    RolloutStage,
    RolloutStrategy,
    StatisticalConfig,
    SuccessCriteria,
    TimeWindow,
    TrafficAllocation,
    TrafficSource,
)
from yt_faceless.orchestrator import Orchestrator


class TestAnalyticsFunctionality:
    """Test analytics and optimization features."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock configuration."""
        config = MagicMock()
        config.enhanced_config.directories.data_dir = tmp_path / "data"
        config.enhanced_config.directories.output_dir = tmp_path / "output"
        return config

    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator instance."""
        with patch("yt_faceless.orchestrator.load_enhanced_config") as mock_load:
            mock_load.return_value = mock_config.enhanced_config
            with patch("yt_faceless.orchestrator.N8NClient"):
                orch = Orchestrator(mock_config)
                return orch

    @pytest.fixture
    def sample_analytics_snapshot(self):
        """Create sample analytics snapshot."""
        return EnhancedAnalyticsSnapshot(
            video_id="test_video_123",
            time_window=TimeWindow(
                start_iso="2025-01-01T00:00:00Z",
                end_iso="2025-01-28T00:00:00Z"
            ),
            kpis=KPIMetrics(
                impressions=10000,
                views=500,
                ctr=5.0,
                avg_view_duration_sec=180,
                avg_percentage_viewed=45.0,
                watch_time_hours=25.0,
            ),
            retention_curve=[
                RetentionPoint(second=0, pct_viewing=100),
                RetentionPoint(second=10, pct_viewing=85),
                RetentionPoint(second=30, pct_viewing=65),
                RetentionPoint(second=60, pct_viewing=50),
                RetentionPoint(second=120, pct_viewing=40),
                RetentionPoint(second=180, pct_viewing=35),
            ],
            traffic_sources=[
                TrafficSource(source="BROWSE", views=200, ctr=6.0),
                TrafficSource(source="SEARCH", views=150, ctr=8.0),
                TrafficSource(source="SUGGESTED", views=100, ctr=4.0),
                TrafficSource(source="EXTERNAL", views=50, ctr=3.0),
            ],
            top_geographies=[
                Geography(country="US", views=200),
                Geography(country="UK", views=100),
                Geography(country="CA", views=50),
            ],
            performance_score=65.0,
        )

    def test_fetch_analytics_by_slug(self, orchestrator, tmp_path):
        """Test fetching analytics using slug."""
        slug = "test-video"

        # Create upload manifest to resolve video ID
        output_dir = tmp_path / "output" / slug
        output_dir.mkdir(parents=True)
        manifest = {
            "response": {"video_id": "resolved_video_123"}
        }
        manifest_file = output_dir / "upload_manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        # Mock analytics response
        mock_snapshot = MagicMock(spec=EnhancedAnalyticsSnapshot)
        mock_snapshot.performance_score = 75.0
        orchestrator.n8n_client.fetch_analytics = Mock(return_value=mock_snapshot)

        # Fetch analytics
        snapshot = orchestrator.analytics(slug, lookback_days=28)

        # Verify
        assert snapshot.performance_score == 75.0
        call_args = orchestrator.n8n_client.fetch_analytics.call_args[0][0]
        assert call_args.video_id == "resolved_video_123"
        assert call_args.lookback_days == 28

    def test_fetch_analytics_by_video_id(self, orchestrator):
        """Test fetching analytics using video ID directly."""
        video_id = "video_123"

        mock_snapshot = MagicMock(spec=EnhancedAnalyticsSnapshot)
        mock_snapshot.performance_score = 80.0
        orchestrator.n8n_client.fetch_analytics = Mock(return_value=mock_snapshot)

        snapshot = orchestrator.analytics(video_id, lookback_days=7)

        assert snapshot.performance_score == 80.0
        call_args = orchestrator.n8n_client.fetch_analytics.call_args[0][0]
        assert call_args.video_id == "video_123"

    def test_propose_experiments_low_ctr(self, orchestrator, sample_analytics_snapshot):
        """Test experiment proposals for low CTR."""
        # Set low CTR
        sample_analytics_snapshot.kpis.ctr = 2.0

        proposals = orchestrator.propose_experiments(sample_analytics_snapshot)

        # Should propose thumbnail optimization
        thumbnail_proposal = next(
            (p for p in proposals if p["type"] == "thumbnail"), None
        )
        assert thumbnail_proposal is not None
        assert thumbnail_proposal["priority"] == 1
        assert "CTR" in thumbnail_proposal["hypothesis"]

    def test_propose_experiments_low_retention(self, orchestrator, sample_analytics_snapshot):
        """Test experiment proposals for low retention."""
        # Set low average percentage viewed
        sample_analytics_snapshot.kpis.avg_percentage_viewed = 35.0

        proposals = orchestrator.propose_experiments(sample_analytics_snapshot)

        # Should propose description/chapters optimization
        retention_proposal = next(
            (p for p in proposals if p["type"] == "description"), None
        )
        assert retention_proposal is not None
        assert "APV" in retention_proposal["hypothesis"]

    def test_propose_experiments_early_dropoff(self, orchestrator, sample_analytics_snapshot):
        """Test experiment proposals for early drop-off."""
        # Set high early drop-off
        sample_analytics_snapshot.retention_curve[2].pct_viewing = 50.0  # 50% at 30s

        proposals = orchestrator.propose_experiments(sample_analytics_snapshot)

        # Should propose title/hook optimization
        title_proposal = next(
            (p for p in proposals if p["type"] == "title"), None
        )
        assert title_proposal is not None
        assert "hook" in title_proposal["hypothesis"].lower()

    def test_create_experiment(self, orchestrator, tmp_path):
        """Test creating an optimization experiment."""
        video_id = "video_123"
        hypothesis = "New thumbnail will increase CTR"
        variants = [
            {"name": "Control", "changes": {}},
            {"name": "Variant A", "changes": {"thumbnail": "new_thumb.jpg"}},
        ]

        experiment = orchestrator.create_experiment(
            video_id=video_id,
            hypothesis=hypothesis,
            variants=variants,
            kpi="ctr",
        )

        # Verify experiment structure
        assert experiment.video_id == video_id
        assert experiment.hypothesis == hypothesis
        assert len(experiment.variants) == 2
        assert experiment.kpi == "ctr"
        assert experiment.allocation.method == "progressive"
        assert experiment.statistical_config.confidence_level == 0.95

        # Check experiment was saved
        exp_file = tmp_path / "data" / "experiments" / f"{experiment.id}.json"
        assert exp_file.exists()

    def test_write_analytics_report(self, orchestrator, tmp_path, sample_analytics_snapshot):
        """Test generating analytics report."""
        slug = "test-video"

        # Add some test data
        sample_analytics_snapshot.anomalies = [
            Anomaly(
                metric="ctr",
                timestamp=datetime.now().isoformat(),
                expected_value=5.0,
                actual_value=2.0,
                severity="medium",
                probable_cause="Thumbnail not resonating",
            )
        ]
        sample_analytics_snapshot.predictions = PerformancePredictions(
            views_7d=1000,
            views_30d=3000,
            revenue_30d=7.50,
            confidence=0.75,
            factors=["Strong retention signals"],
        )

        proposals = [
            {
                "type": "thumbnail",
                "priority": 1,
                "hypothesis": "Better thumbnail",
                "kpi": "ctr",
                "target_delta_pct": 25,
            }
        ]

        report_path = orchestrator.write_report(slug, sample_analytics_snapshot, proposals)

        # Verify report was created
        assert report_path.exists()
        content = report_path.read_text()

        # Check content includes key sections
        assert "Performance Summary" in content
        assert "65/100" in content  # Performance score
        assert "Recommendations" in content
        assert "Better thumbnail" in content
        assert "Anomalies Detected" in content
        assert "Thumbnail not resonating" in content
        assert "Performance Predictions" in content
        assert "1,000" in content  # 7-day views
        assert "75%" in content  # Confidence

    def test_analytics_with_anomalies(self, orchestrator):
        """Test analytics with anomaly detection."""
        mock_snapshot = EnhancedAnalyticsSnapshot(
            video_id="video_123",
            time_window=TimeWindow(
                start_iso="2025-01-01T00:00:00Z",
                end_iso="2025-01-28T00:00:00Z"
            ),
            kpis=KPIMetrics(
                impressions=10000,
                views=100,  # Very low views
                ctr=1.0,  # Very low CTR
                avg_view_duration_sec=60,
                avg_percentage_viewed=20.0,  # Very low retention
                watch_time_hours=1.67,
            ),
            retention_curve=[],
            traffic_sources=[],
            top_geographies=[],
            performance_score=25.0,
            anomalies=[
                Anomaly(
                    metric="ctr",
                    timestamp=datetime.now().isoformat(),
                    expected_value=4.0,
                    actual_value=1.0,
                    severity="high",
                    probable_cause="Thumbnail/title not resonating",
                ),
                Anomaly(
                    metric="retention",
                    timestamp=datetime.now().isoformat(),
                    expected_value=50.0,
                    actual_value=20.0,
                    severity="high",
                    probable_cause="Content quality issues",
                ),
            ],
        )

        orchestrator.n8n_client.fetch_analytics = Mock(return_value=mock_snapshot)

        snapshot = orchestrator.analytics("video_123")

        assert len(snapshot.anomalies) == 2
        assert all(a.severity == "high" for a in snapshot.anomalies)

    def test_analytics_with_predictions(self, orchestrator):
        """Test analytics with performance predictions."""
        mock_snapshot = EnhancedAnalyticsSnapshot(
            video_id="video_123",
            time_window=TimeWindow(
                start_iso="2025-01-01T00:00:00Z",
                end_iso="2025-01-28T00:00:00Z"
            ),
            kpis=KPIMetrics(
                impressions=50000,
                views=5000,
                ctr=10.0,
                avg_view_duration_sec=300,
                avg_percentage_viewed=75.0,
                watch_time_hours=416.67,
            ),
            retention_curve=[],
            traffic_sources=[],
            top_geographies=[],
            performance_score=90.0,
            predictions=PerformancePredictions(
                views_7d=2000,
                views_30d=8000,
                revenue_30d=20.0,
                confidence=0.85,
                factors=["High CTR driving discovery", "Strong retention signals"],
            ),
        )

        orchestrator.n8n_client.fetch_analytics = Mock(return_value=mock_snapshot)

        snapshot = orchestrator.analytics("video_123")

        assert snapshot.predictions is not None
        assert snapshot.predictions.confidence == 0.85
        assert len(snapshot.predictions.factors) == 2


class TestExperimentManagement:
    """Test experiment creation and management."""

    def test_experiment_variant_creation(self):
        """Test creating experiment variants."""
        variant = ExperimentVariant(
            variant_id="var_1",
            name="New Thumbnail",
            changes={"thumbnail": "path/to/new_thumb.jpg"},
            weight=0.5,
        )

        assert variant.variant_id == "var_1"
        assert variant.weight == 0.5
        assert "thumbnail" in variant.changes

    def test_traffic_allocation_progressive(self):
        """Test progressive traffic allocation."""
        allocation = TrafficAllocation(
            method="progressive",
            ramp_up_hours=24,
            target_impressions_per_variant=1000,
        )

        assert allocation.method == "progressive"
        assert allocation.ramp_up_hours == 24

    def test_rollout_strategy(self):
        """Test experiment rollout strategy."""
        strategy = RolloutStrategy(
            strategy="progressive",
            stages=[
                RolloutStage(
                    percentage=25,
                    duration_hours=24,
                    success_gate={"ctr_drop": -5.0},
                ),
                RolloutStage(
                    percentage=50,
                    duration_hours=24,
                    success_gate={"ctr_drop": -3.0},
                ),
                RolloutStage(
                    percentage=100,
                    duration_hours=48,
                    success_gate={"ctr_drop": -1.0},
                ),
            ],
        )

        assert len(strategy.stages) == 3
        assert strategy.stages[0].percentage == 25
        assert strategy.stages[-1].percentage == 100

    def test_success_criteria(self):
        """Test experiment success criteria."""
        criteria = SuccessCriteria(
            primary_metric="ctr",
            minimum_lift=5.0,
            guardrail_metrics={"retention": -5.0, "revenue": -10.0},
        )

        assert criteria.primary_metric == "ctr"
        assert criteria.minimum_lift == 5.0
        assert "retention" in criteria.guardrail_metrics


class TestAnalyticsRequest:
    """Test analytics request validation."""

    def test_valid_analytics_request(self):
        """Test creating valid analytics request."""
        request = AnalyticsRequest(
            video_id="video_123",
            lookback_days=28,
            granularity="daily",
            include_predictions=True,
            include_anomalies=True,
        )

        assert request.video_id == "video_123"
        assert request.granularity == "daily"

    def test_invalid_granularity(self):
        """Test invalid granularity validation."""
        with pytest.raises(ValueError):
            AnalyticsRequest(
                video_id="video_123",
                lookback_days=28,
                granularity="invalid",  # Should be daily/hourly/lifetime
            )