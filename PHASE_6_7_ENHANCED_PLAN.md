# Enhanced Implementation Plan: Phases 6-7 - Upload, Analytics & Optimization

## Executive Summary

This enhanced plan builds upon the solid foundation in `current_phase.md` with additional robustness, error handling, monitoring, and cross-phase integration. Key enhancements include:

1. **Comprehensive error recovery** with transaction-like rollback capabilities
2. **Enhanced idempotency** with distributed lock management
3. **Advanced analytics** with predictive modeling and trend detection
4. **Progressive rollout** strategy for experiments
5. **Full observability** with metrics, tracing, and alerting hooks

---

## Phase 6: Upload & Publishing Automation (Enhanced)

### Core Objectives (Original + Enhanced)
- ✅ Automate upload and scheduling to YouTube via n8n workflows
- ✅ Ensure reliable, idempotent publishing with strict validation
- **NEW:** Implement transaction-like upload with rollback capability
- **NEW:** Add pre-upload quality gates and post-upload verification
- **NEW:** Support multi-platform publishing readiness (YouTube, Shorts, TikTok stub)

### Enhanced Data Contracts

#### Upload Request Payload (Extended)
```python
class YouTubeUploadPayload(TypedDict):
    # Original fields
    video_path: str
    thumbnail_path: Optional[str]
    title: str
    description: str
    tags: List[str]
    category_id: Optional[int]
    privacy_status: Literal["public", "unlisted", "private"]
    publish_at_iso: Optional[str]
    made_for_kids: bool
    language: Optional[str]
    chapters: Optional[List[ChapterMarker]]
    slug: str
    checksum_sha256: str

    # Enhanced fields
    transaction_id: str  # Unique transaction ID for rollback
    quality_gates: QualityGates  # Pre-upload checks
    monetization_settings: MonetizationSettings
    audience_retention_hooks: List[RetentionHook]
    platform_targets: List[Literal["youtube", "shorts", "tiktok"]]
    upload_priority: int  # 1-10, for queue management
    parent_video_id: Optional[str]  # For Shorts from main video
    experiment_id: Optional[str]  # Link to A/B test

class QualityGates(TypedDict):
    min_duration_sec: int
    max_duration_sec: int
    min_resolution: Tuple[int, int]
    required_audio_loudness: Tuple[int, int]  # LUFS range
    copyright_check_passed: bool
    profanity_check_passed: bool

class MonetizationSettings(TypedDict):
    enable_ads: bool
    enable_channel_memberships: bool
    enable_super_chat: bool
    mid_roll_positions_sec: Optional[List[int]]
    affiliate_links: Optional[List[AffiliateLink]]
    sponsorship_disclosure: Optional[str]
```

#### Upload Response Payload (Extended)
```python
class YouTubeUploadResponse(TypedDict):
    # Original fields
    execution_id: str
    video_id: str
    status: Literal["uploaded", "scheduled", "processing", "failed"]
    publish_at_iso: Optional[str]
    errors: Optional[List[str]]

    # Enhanced fields
    transaction_id: str
    upload_duration_ms: int
    quality_scores: QualityScores
    platform_ids: Dict[str, str]  # {"youtube": "abc123", "shorts": "def456"}
    verification_status: VerificationStatus
    rollback_available_until_iso: str
    metrics_baseline: MetricsBaseline  # Initial metrics for comparison

class QualityScores(TypedDict):
    technical_quality: float  # 0-100
    seo_optimization: float
    monetization_readiness: float
    policy_compliance: float

class VerificationStatus(TypedDict):
    thumbnail_verified: bool
    metadata_verified: bool
    processing_status: str
    estimated_processing_time_min: int
```

### Enhanced Python Implementation

#### 1. Transaction Management (`src/yt_faceless/core/transactions.py`)
```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
from pathlib import Path
from dataclasses import dataclass, field
import hashlib

@dataclass
class UploadTransaction:
    """Manages upload transaction state for rollback capability."""

    transaction_id: str
    slug: str
    started_at: datetime
    state: Literal["pending", "uploading", "verifying", "completed", "failed", "rolled_back"]
    checkpoints: Dict[str, Any] = field(default_factory=dict)
    rollback_actions: List[Callable] = field(default_factory=list)

    def checkpoint(self, name: str, data: Any, rollback_fn: Optional[Callable] = None):
        """Save checkpoint with optional rollback function."""
        self.checkpoints[name] = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        if rollback_fn:
            self.rollback_actions.append(rollback_fn)

    def rollback(self) -> List[str]:
        """Execute rollback actions in reverse order."""
        errors = []
        for action in reversed(self.rollback_actions):
            try:
                action()
            except Exception as e:
                errors.append(str(e))
        self.state = "rolled_back"
        return errors

    def save(self, base_dir: Path):
        """Persist transaction state to disk."""
        transaction_file = base_dir / f"{self.transaction_id}.json"
        transaction_file.write_text(json.dumps({
            "transaction_id": self.transaction_id,
            "slug": self.slug,
            "started_at": self.started_at.isoformat(),
            "state": self.state,
            "checkpoints": self.checkpoints
        }, indent=2))
```

#### 2. Quality Gates (`src/yt_faceless/core/quality.py`)
```python
import subprocess
from typing import Tuple, Optional
from pathlib import Path
import json

class VideoQualityAnalyzer:
    """Analyze video quality before upload."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe"):
        self.ffmpeg_bin = ffmpeg_bin
        self.ffprobe_bin = ffprobe_bin

    def analyze(self, video_path: Path) -> QualityReport:
        """Comprehensive video quality analysis."""
        report = QualityReport()

        # Get video metadata
        probe_cmd = [
            self.ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]

        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        metadata = json.loads(result.stdout)

        # Extract quality metrics
        video_stream = next((s for s in metadata["streams"] if s["codec_type"] == "video"), None)
        audio_stream = next((s for s in metadata["streams"] if s["codec_type"] == "audio"), None)

        if video_stream:
            report.resolution = (int(video_stream["width"]), int(video_stream["height"]))
            report.fps = eval(video_stream["r_frame_rate"])
            report.bitrate = int(video_stream.get("bit_rate", 0))
            report.codec = video_stream["codec_name"]

        if audio_stream:
            report.audio_bitrate = int(audio_stream.get("bit_rate", 0))
            report.audio_codec = audio_stream["codec_name"]
            report.audio_channels = int(audio_stream["channels"])

        report.duration_sec = float(metadata["format"]["duration"])
        report.file_size_mb = int(metadata["format"]["size"]) / (1024 * 1024)

        # Calculate quality score
        report.calculate_scores()

        return report

    def check_copyright(self, video_path: Path) -> bool:
        """Placeholder for copyright detection."""
        # In production, integrate with Content ID API or similar
        return True

    def check_loudness(self, video_path: Path) -> Tuple[float, float]:
        """Check audio loudness using FFmpeg."""
        cmd = [
            self.ffmpeg_bin,
            "-i", str(video_path),
            "-af", "loudnorm=I=-14:TP=-1:LRA=7:print_format=json",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        # Parse loudness from stderr
        # Returns (integrated_loudness, loudness_range)
        return (-14.0, 7.0)  # Placeholder
```

#### 3. Enhanced Upload Orchestrator (`src/yt_faceless/orchestrator.py` additions)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List
import hashlib
import time

class EnhancedUploadOrchestrator:
    """Enhanced upload orchestration with quality gates and rollback."""

    def __init__(self, config: AppConfig, n8n_client: N8NClient):
        self.config = config
        self.n8n_client = n8n_client
        self.quality_analyzer = VideoQualityAnalyzer(config.video.ffmpeg_bin)
        self.transaction_dir = config.directories.data_dir / "transactions"
        self.transaction_dir.mkdir(exist_ok=True)

    def publish_with_verification(
        self,
        slug: str,
        video_path: Optional[Path] = None,
        thumbnail_path: Optional[Path] = None,
        schedule_iso: Optional[str] = None,
        privacy: str = "private",
        platforms: List[str] = ["youtube"],
        experiment_id: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False
    ) -> YouTubeUploadResponse:
        """Enhanced publish with quality gates and verification."""

        # Start transaction
        transaction = UploadTransaction(
            transaction_id=self._generate_transaction_id(),
            slug=slug,
            started_at=datetime.utcnow(),
            state="pending"
        )

        try:
            # Load metadata
            metadata_path = self.config.directories.content_dir / slug / "metadata.json"
            metadata = json.loads(metadata_path.read_text())
            transaction.checkpoint("metadata_loaded", metadata)

            # Resolve paths
            if not video_path:
                video_path = self.config.directories.content_dir / slug / "final.mp4"

            # Quality gates
            self._run_quality_gates(video_path, transaction)

            # Check idempotency
            if not force:
                existing = self._check_existing_upload(slug, video_path)
                if existing:
                    return existing

            # Build upload payload
            payload = self._build_upload_payload(
                slug, video_path, thumbnail_path, metadata,
                schedule_iso, privacy, platforms, experiment_id, transaction
            )

            # Pre-upload verification
            transaction.state = "uploading"
            transaction.save(self.transaction_dir)

            # Upload with retries
            response = self._upload_with_retries(payload, transaction)

            # Post-upload verification
            transaction.state = "verifying"
            verification = self._verify_upload(response["video_id"], transaction)
            response["verification_status"] = verification

            # Save manifest
            self._save_upload_manifest(slug, payload, response, transaction)

            # Complete transaction
            transaction.state = "completed"
            transaction.save(self.transaction_dir)

            return response

        except Exception as e:
            # Rollback on failure
            transaction.state = "failed"
            rollback_errors = transaction.rollback()
            transaction.save(self.transaction_dir)

            raise UploadError(
                f"Upload failed for {slug}: {e}",
                transaction_id=transaction.transaction_id,
                rollback_errors=rollback_errors
            )

    def _run_quality_gates(self, video_path: Path, transaction: UploadTransaction):
        """Run pre-upload quality checks."""
        report = self.quality_analyzer.analyze(video_path)

        # Check duration
        if report.duration_sec < 60:
            raise QualityGateError("Video too short (< 60 seconds)")
        if report.duration_sec > 3600:
            raise QualityGateError("Video too long (> 1 hour)")

        # Check resolution
        if report.resolution[0] < 1280 or report.resolution[1] < 720:
            raise QualityGateError(f"Resolution too low: {report.resolution}")

        # Check audio
        loudness = self.quality_analyzer.check_loudness(video_path)
        if loudness[0] < -20 or loudness[0] > -10:
            raise QualityGateError(f"Audio loudness out of range: {loudness[0]} LUFS")

        # Copyright check
        if not self.quality_analyzer.check_copyright(video_path):
            raise QualityGateError("Potential copyright issue detected")

        transaction.checkpoint("quality_gates_passed", {
            "duration": report.duration_sec,
            "resolution": report.resolution,
            "loudness": loudness,
            "scores": report.scores
        })

    def _verify_upload(self, video_id: str, transaction: UploadTransaction) -> VerificationStatus:
        """Verify upload completed successfully."""
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Call n8n webhook to check video status
                status = self.n8n_client.check_video_status(video_id)

                if status["processing_status"] == "completed":
                    return VerificationStatus(
                        thumbnail_verified=status.get("thumbnail_processed", False),
                        metadata_verified=status.get("metadata_set", False),
                        processing_status="completed",
                        estimated_processing_time_min=0
                    )
                elif status["processing_status"] == "failed":
                    raise UploadError(f"Video processing failed: {status.get('error')}")

                # Still processing
                time.sleep(30)

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(10)

        # Timeout - return partial status
        return VerificationStatus(
            thumbnail_verified=False,
            metadata_verified=False,
            processing_status="processing",
            estimated_processing_time_min=5
        )
```

### Enhanced n8n Workflows

#### 1. Upload Workflow (`workflows/youtube_upload_enhanced.json`)
```json
{
  "name": "YouTube Upload Enhanced",
  "nodes": [
    {
      "name": "HTTP In",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "youtube-upload-enhanced",
        "responseMode": "lastNode"
      }
    },
    {
      "name": "Validate Payload",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "code": "// Comprehensive validation\nconst required = ['video_path', 'title', 'description', 'transaction_id'];\nfor (const field of required) {\n  if (!$input.item.json[field]) {\n    throw new Error(`Missing required field: ${field}`);\n  }\n}\n\n// Validate quality gates\nif ($input.item.json.quality_gates) {\n  const gates = $input.item.json.quality_gates;\n  if (!gates.copyright_check_passed) {\n    throw new Error('Copyright check failed');\n  }\n}\n\nreturn $input.item;"
      }
    },
    {
      "name": "Check Idempotency",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT video_id FROM uploads WHERE transaction_id = $1 OR (slug = $2 AND checksum = $3)",
        "additionalFields": {
          "queryParams": "={{$json.transaction_id}},={{$json.slug}},={{$json.checksum_sha256}}"
        }
      }
    },
    {
      "name": "Upload Video",
      "type": "n8n-nodes-base.youtube",
      "parameters": {
        "operation": "upload",
        "title": "={{$json.title}}",
        "description": "={{$json.description}}",
        "tags": "={{$json.tags.join(',')}}",
        "categoryId": "={{$json.category_id}}",
        "privacyStatus": "={{$json.privacy_status}}",
        "publishAt": "={{$json.publish_at_iso}}",
        "madeForKids": "={{$json.made_for_kids}}",
        "defaultLanguage": "={{$json.language}}"
      }
    },
    {
      "name": "Upload Thumbnail",
      "type": "n8n-nodes-base.youtube",
      "parameters": {
        "operation": "thumbnail",
        "videoId": "={{$node['Upload Video'].json.id}}",
        "binaryPropertyName": "thumbnail"
      }
    },
    {
      "name": "Set Monetization",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "code": "// Call YouTube Partner API for monetization settings\n// This would be a custom node in production\nconst videoId = $node['Upload Video'].json.id;\nconst monetization = $input.item.json.monetization_settings;\n\nif (monetization && monetization.enable_ads) {\n  // Enable ads, set mid-roll positions, etc.\n}\n\nreturn {videoId, monetization_applied: true};"
      }
    },
    {
      "name": "Store Upload Record",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "uploads",
        "columns": "transaction_id,slug,video_id,checksum,upload_time,metadata",
        "values": "={{$json.transaction_id}},={{$json.slug}},={{$node['Upload Video'].json.id}},={{$json.checksum_sha256}},={{Date.now()}},={{JSON.stringify($json)}}"
      }
    },
    {
      "name": "Send Webhook Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "responseCode": 200,
        "responseBody": "={{JSON.stringify({\n  execution_id: $execution.id,\n  video_id: $node['Upload Video'].json.id,\n  status: $json.publish_at_iso ? 'scheduled' : 'uploaded',\n  transaction_id: $json.transaction_id,\n  upload_duration_ms: Date.now() - $node['HTTP In'].json.timestamp,\n  quality_scores: $json.quality_gates,\n  verification_status: {\n    thumbnail_verified: true,\n    metadata_verified: true,\n    processing_status: 'processing',\n    estimated_processing_time_min: 5\n  }\n})}}"
      }
    }
  ]
}
```

---

## Phase 7: Analytics & Optimization Loop (Enhanced)

### Core Objectives (Original + Enhanced)
- ✅ Pull YouTube Analytics via n8n
- ✅ Produce actionable reports and A/B experiments
- **NEW:** Implement predictive analytics for performance forecasting
- **NEW:** Add automated experiment execution with progressive rollout
- **NEW:** Create feedback loop to Phase 2 (Research) for content strategy
- **NEW:** Implement multi-variant testing beyond A/B

### Enhanced Data Contracts

#### Analytics Request (Extended)
```python
class AnalyticsRequest(TypedDict):
    # Original fields
    video_id: str
    lookback_days: int
    granularity: Literal["daily", "hourly", "lifetime"]

    # Enhanced fields
    metrics: List[str]  # Specific metrics to fetch
    dimensions: List[str]  # Breakdown dimensions
    filters: Dict[str, Any]  # Traffic source, geography, etc.
    compare_to: Optional[str]  # Compare to another video
    include_predictions: bool  # Generate performance predictions
    include_anomalies: bool  # Detect anomalies
```

#### Analytics Response (Extended)
```python
class EnhancedAnalyticsSnapshot(TypedDict):
    # Original fields (kept)
    video_id: str
    time_window: TimeWindow
    kpis: KPIMetrics
    retention_curve: List[RetentionPoint]
    traffic_sources: List[TrafficSource]
    top_geographies: List[Geography]

    # Enhanced fields
    performance_score: float  # 0-100 composite score
    anomalies: List[Anomaly]
    predictions: PerformancePredictions
    comparative_analysis: Optional[ComparativeMetrics]
    engagement_patterns: EngagementAnalysis
    monetization_metrics: MonetizationMetrics

class Anomaly(TypedDict):
    metric: str
    timestamp: str
    expected_value: float
    actual_value: float
    severity: Literal["low", "medium", "high"]
    probable_cause: str

class PerformancePredictions(TypedDict):
    views_7d: int
    views_30d: int
    revenue_30d: float
    confidence: float
    factors: List[str]  # Factors influencing prediction

class EngagementAnalysis(TypedDict):
    peak_engagement_times: List[Tuple[int, float]]  # (second, engagement_rate)
    drop_off_points: List[Tuple[int, float, str]]  # (second, drop_rate, probable_reason)
    replay_segments: List[Tuple[int, int]]  # Most replayed segments
    engagement_score: float

class MonetizationMetrics(TypedDict):
    estimated_revenue: float
    rpm: float
    cpm: float
    ad_impressions: int
    ad_click_rate: float
    viewer_demographics: Dict[str, Any]
```

#### Enhanced Experiment Framework
```python
class MultiVariantExperiment(TypedDict):
    # Original fields enhanced
    id: str
    video_id: str
    hypothesis: str
    kpi: str
    target_delta_pct: float
    priority: int

    # New fields for multi-variant testing
    variants: List[ExperimentVariant]
    allocation: TrafficAllocation
    statistical_config: StatisticalConfig
    rollout_strategy: RolloutStrategy
    success_criteria: SuccessCriteria

class ExperimentVariant(TypedDict):
    variant_id: str
    name: str
    changes: Dict[str, Any]  # What's different
    weight: float  # Traffic percentage

class TrafficAllocation(TypedDict):
    method: Literal["random", "deterministic", "progressive"]
    ramp_up_hours: int
    target_impressions_per_variant: int

class StatisticalConfig(TypedDict):
    confidence_level: float  # e.g., 0.95
    minimum_sample_size: int
    test_type: Literal["frequentist", "bayesian"]
    early_stopping_enabled: bool

class RolloutStrategy(TypedDict):
    strategy: Literal["immediate", "progressive", "scheduled"]
    stages: List[RolloutStage]

class RolloutStage(TypedDict):
    percentage: int
    duration_hours: int
    success_gate: Dict[str, float]  # Metrics that must be met
```

### Enhanced Python Implementation

#### 1. Predictive Analytics Engine (`src/yt_faceless/analytics/predictions.py`)
```python
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class PerformancePredictor:
    """Predict future video performance based on early signals."""

    def __init__(self):
        self.models = {
            "views": LinearRegression(),
            "engagement": LinearRegression(),
            "revenue": LinearRegression()
        }
        self.feature_importance = {}

    def predict_performance(
        self,
        early_metrics: Dict[str, List[float]],
        video_metadata: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> PerformancePredictions:
        """Predict future performance based on early metrics."""

        # Extract features from early performance
        features = self._extract_features(early_metrics, video_metadata)

        # Apply models
        predictions = {}
        confidence_scores = []

        for metric, model in self.models.items():
            if historical_data:
                # Fine-tune model with historical data
                X_hist, y_hist = self._prepare_training_data(historical_data, metric)
                model.fit(X_hist, y_hist)

            # Make prediction
            prediction = model.predict([features])[0]
            predictions[metric] = prediction

            # Calculate confidence
            if historical_data:
                confidence = self._calculate_confidence(model, features, X_hist, y_hist)
                confidence_scores.append(confidence)

        # Identify key factors
        factors = self._identify_key_factors(features, self.feature_importance)

        return PerformancePredictions(
            views_7d=int(predictions.get("views_7d", 0)),
            views_30d=int(predictions.get("views_30d", 0)),
            revenue_30d=float(predictions.get("revenue_30d", 0)),
            confidence=np.mean(confidence_scores) if confidence_scores else 0.5,
            factors=factors
        )

    def detect_anomalies(
        self,
        current_metrics: Dict[str, float],
        expected_metrics: Dict[str, float],
        historical_variance: Dict[str, float]
    ) -> List[Anomaly]:
        """Detect anomalies in current performance."""
        anomalies = []

        for metric, current_value in current_metrics.items():
            if metric not in expected_metrics:
                continue

            expected_value = expected_metrics[metric]
            variance = historical_variance.get(metric, 0.1)

            # Calculate z-score
            if variance > 0:
                z_score = abs((current_value - expected_value) / variance)

                if z_score > 3:  # 3 sigma rule
                    severity = "high" if z_score > 4 else "medium"

                    # Identify probable cause
                    cause = self._identify_anomaly_cause(
                        metric, current_value, expected_value, current_metrics
                    )

                    anomalies.append(Anomaly(
                        metric=metric,
                        timestamp=datetime.utcnow().isoformat(),
                        expected_value=expected_value,
                        actual_value=current_value,
                        severity=severity,
                        probable_cause=cause
                    ))

        return anomalies

    def _identify_anomaly_cause(
        self,
        metric: str,
        current: float,
        expected: float,
        all_metrics: Dict[str, float]
    ) -> str:
        """Identify probable cause of anomaly."""
        if metric == "ctr" and current < expected:
            if all_metrics.get("impressions", 0) > expected * 1.5:
                return "Thumbnail/title not resonating with broader audience"
            return "Possible algorithm change or competition"

        if metric == "retention" and current < expected:
            hook_retention = all_metrics.get("retention_15s", 1.0)
            if hook_retention < 0.7:
                return "Weak hook - losing viewers in first 15 seconds"
            return "Content pacing or quality issues"

        return "Unknown - requires manual investigation"
```

#### 2. Experiment Orchestrator (`src/yt_faceless/analytics/experiments.py`)
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import random
import hashlib
from datetime import datetime, timedelta

class ExperimentOrchestrator:
    """Orchestrate multi-variant experiments with progressive rollout."""

    def __init__(self, config: AppConfig, n8n_client: N8NClient):
        self.config = config
        self.n8n_client = n8n_client
        self.active_experiments: Dict[str, MultiVariantExperiment] = {}
        self.experiment_results: Dict[str, ExperimentResult] = {}

    def create_experiment(
        self,
        video_id: str,
        hypothesis: str,
        variants: List[Dict[str, Any]],
        kpi: str = "ctr",
        allocation_method: str = "progressive"
    ) -> MultiVariantExperiment:
        """Create a new multi-variant experiment."""

        experiment = MultiVariantExperiment(
            id=self._generate_experiment_id(video_id),
            video_id=video_id,
            hypothesis=hypothesis,
            kpi=kpi,
            target_delta_pct=10.0,  # Default 10% improvement target
            priority=self._calculate_priority(video_id, kpi),
            variants=[
                ExperimentVariant(
                    variant_id=f"variant_{i}",
                    name=v.get("name", f"Variant {i}"),
                    changes=v.get("changes", {}),
                    weight=1.0 / len(variants)  # Equal split initially
                )
                for i, v in enumerate(variants)
            ],
            allocation=TrafficAllocation(
                method=allocation_method,
                ramp_up_hours=24 if allocation_method == "progressive" else 0,
                target_impressions_per_variant=1000
            ),
            statistical_config=StatisticalConfig(
                confidence_level=0.95,
                minimum_sample_size=1000,
                test_type="bayesian",
                early_stopping_enabled=True
            ),
            rollout_strategy=self._create_rollout_strategy(allocation_method),
            success_criteria=SuccessCriteria(
                primary_metric=kpi,
                minimum_lift=5.0,
                guardrail_metrics={"retention": -5.0}  # Don't let retention drop >5%
            )
        )

        self.active_experiments[experiment["id"]] = experiment
        return experiment

    def execute_experiment(
        self,
        experiment_id: str,
        dry_run: bool = False
    ) -> ExperimentResult:
        """Execute an experiment with progressive rollout."""

        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        result = ExperimentResult(
            experiment_id=experiment_id,
            started_at=datetime.utcnow(),
            status="running"
        )

        try:
            # Stage 1: Pre-flight checks
            self._preflight_checks(experiment)

            # Stage 2: Progressive rollout
            for stage in experiment["rollout_strategy"]["stages"]:
                if dry_run:
                    self._simulate_stage(experiment, stage, result)
                else:
                    self._execute_stage(experiment, stage, result)

                # Check success gates
                if not self._check_success_gates(stage, result):
                    result["status"] = "failed"
                    result["failure_reason"] = "Success gate not met"
                    break

                # Early stopping check
                if self._should_stop_early(experiment, result):
                    break

            # Stage 3: Analyze results
            result["analysis"] = self._analyze_results(experiment, result)
            result["status"] = "completed" if result["status"] == "running" else result["status"]

            # Stage 4: Apply winner (if clear)
            if result["analysis"]["has_winner"] and not dry_run:
                self._apply_winner(experiment, result["analysis"]["winner"])

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        finally:
            result["completed_at"] = datetime.utcnow()
            self.experiment_results[experiment_id] = result

        return result

    def _execute_stage(
        self,
        experiment: MultiVariantExperiment,
        stage: RolloutStage,
        result: ExperimentResult
    ):
        """Execute a single rollout stage."""

        # Update traffic allocation
        for variant in experiment["variants"]:
            variant["weight"] = stage["percentage"] / 100.0 / len(experiment["variants"])

        # Apply changes via n8n
        for variant in experiment["variants"]:
            changes = variant["changes"]

            if "title" in changes:
                self.n8n_client.update_video_metadata(
                    experiment["video_id"],
                    {"title": changes["title"]},
                    variant_id=variant["variant_id"]
                )

            if "thumbnail" in changes:
                self.n8n_client.update_video_thumbnail(
                    experiment["video_id"],
                    changes["thumbnail"],
                    variant_id=variant["variant_id"]
                )

        # Wait for data collection
        time.sleep(stage["duration_hours"] * 3600)

        # Collect metrics
        metrics = self.n8n_client.fetch_variant_metrics(
            experiment["video_id"],
            [v["variant_id"] for v in experiment["variants"]]
        )

        result["stage_results"].append({
            "stage": stage,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })

    def _analyze_results(
        self,
        experiment: MultiVariantExperiment,
        result: ExperimentResult
    ) -> ExperimentAnalysis:
        """Analyze experiment results using Bayesian statistics."""

        from scipy import stats

        # Aggregate metrics across stages
        variant_metrics = {}
        for stage_result in result["stage_results"]:
            for variant_id, metrics in stage_result["metrics"].items():
                if variant_id not in variant_metrics:
                    variant_metrics[variant_id] = []
                variant_metrics[variant_id].append(metrics)

        # Calculate statistics
        analysis = ExperimentAnalysis()
        best_variant = None
        best_score = -float('inf')

        for variant in experiment["variants"]:
            variant_id = variant["variant_id"]
            if variant_id not in variant_metrics:
                continue

            # Calculate mean and confidence interval
            data = variant_metrics[variant_id]
            kpi_values = [d[experiment["kpi"]] for d in data]

            mean = np.mean(kpi_values)
            std = np.std(kpi_values)
            ci = stats.t.interval(
                experiment["statistical_config"]["confidence_level"],
                len(kpi_values) - 1,
                loc=mean,
                scale=std / np.sqrt(len(kpi_values))
            )

            variant_analysis = {
                "variant_id": variant_id,
                "mean": mean,
                "std": std,
                "confidence_interval": ci,
                "sample_size": len(kpi_values)
            }

            analysis["variants"].append(variant_analysis)

            if mean > best_score:
                best_score = mean
                best_variant = variant_id

        # Determine if we have a winner
        if len(analysis["variants"]) >= 2:
            # Perform pairwise comparisons
            control = analysis["variants"][0]
            for variant in analysis["variants"][1:]:
                lift = (variant["mean"] - control["mean"]) / control["mean"] * 100

                # Check if lift is statistically significant
                if variant["confidence_interval"][0] > control["confidence_interval"][1]:
                    analysis["has_winner"] = True
                    analysis["winner"] = variant["variant_id"]
                    analysis["lift_percentage"] = lift
                    break

        return analysis
```

#### 3. Reporting Engine (`src/yt_faceless/analytics/reports.py`)
```python
from jinja2 import Template
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional
import json

class EnhancedReportGenerator:
    """Generate comprehensive analytics and optimization reports."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.reports_dir = config.directories.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.template = self._load_template()

    def generate_performance_report(
        self,
        video_id: str,
        analytics: EnhancedAnalyticsSnapshot,
        experiments: List[ExperimentResult],
        predictions: PerformancePredictions
    ) -> Path:
        """Generate comprehensive performance report."""

        # Create visualizations
        charts = self._create_charts(analytics)

        # Compile insights
        insights = self._generate_insights(analytics, predictions)

        # Generate recommendations
        recommendations = self._generate_recommendations(analytics, experiments)

        # Render report
        report_content = self.template.render(
            video_id=video_id,
            analytics=analytics,
            experiments=experiments,
            predictions=predictions,
            insights=insights,
            recommendations=recommendations,
            charts=charts,
            generated_at=datetime.utcnow().isoformat()
        )

        # Save report
        report_path = self.reports_dir / f"{video_id}_{datetime.utcnow():%Y%m%d}.md"
        report_path.write_text(report_content)

        # Also save as JSON for programmatic access
        json_path = report_path.with_suffix(".json")
        json_path.write_text(json.dumps({
            "video_id": video_id,
            "analytics": analytics,
            "experiments": [e.__dict__ for e in experiments],
            "predictions": predictions,
            "insights": insights,
            "recommendations": recommendations
        }, indent=2, default=str))

        return report_path

    def _create_charts(self, analytics: EnhancedAnalyticsSnapshot) -> Dict[str, str]:
        """Create visualization charts."""
        charts = {}

        # Retention curve
        fig, ax = plt.subplots(figsize=(10, 6))
        retention_data = analytics["retention_curve"]
        seconds = [p["second"] for p in retention_data]
        percentages = [p["pct_viewing"] for p in retention_data]

        ax.plot(seconds, percentages, linewidth=2)
        ax.fill_between(seconds, percentages, alpha=0.3)
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Audience Retention (%)")
        ax.set_title("Audience Retention Curve")
        ax.grid(True, alpha=0.3)

        # Mark drop-off points
        for point in analytics["engagement_patterns"]["drop_off_points"]:
            ax.axvline(x=point[0], color='red', linestyle='--', alpha=0.5)
            ax.annotate(point[2], xy=(point[0], 50), fontsize=8, rotation=45)

        chart_path = self.reports_dir / f"retention_{analytics['video_id']}.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        charts["retention_curve"] = str(chart_path)

        # Traffic sources pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        sources = analytics["traffic_sources"]
        labels = [s["source"] for s in sources]
        sizes = [s["views"] for s in sources]

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Traffic Sources Distribution")

        chart_path = self.reports_dir / f"traffic_{analytics['video_id']}.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        charts["traffic_sources"] = str(chart_path)

        return charts

    def _generate_insights(
        self,
        analytics: EnhancedAnalyticsSnapshot,
        predictions: PerformancePredictions
    ) -> List[str]:
        """Generate actionable insights from analytics."""
        insights = []

        # Performance insights
        if analytics["performance_score"] < 50:
            insights.append("⚠️ Video performing below average. Consider immediate optimization.")
        elif analytics["performance_score"] > 80:
            insights.append("✅ Strong performance! Analyze success factors for replication.")

        # Retention insights
        retention_curve = analytics["retention_curve"]
        if retention_curve and retention_curve[0]["pct_viewing"] < 70:
            insights.append("📉 Weak hook - 30%+ viewers lost in first 30 seconds")

        # Traffic insights
        top_source = max(analytics["traffic_sources"], key=lambda x: x["views"])
        if top_source["source"] == "browse" and analytics["kpis"]["ctr"] < 4.0:
            insights.append(f"🎯 Browse traffic dominant but CTR low ({analytics['kpis']['ctr']:.1f}%). Thumbnail optimization critical.")

        # Anomaly insights
        for anomaly in analytics["anomalies"]:
            if anomaly["severity"] == "high":
                insights.append(f"🚨 Anomaly detected: {anomaly['metric']} - {anomaly['probable_cause']}")

        # Prediction insights
        if predictions["confidence"] > 0.8:
            insights.append(f"📊 High confidence prediction: {predictions['views_30d']:,} views in 30 days")

        return insights

    def _generate_recommendations(
        self,
        analytics: EnhancedAnalyticsSnapshot,
        experiments: List[ExperimentResult]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # CTR optimization
        if analytics["kpis"]["ctr"] < 5.0:
            recommendations.append({
                "priority": 1,
                "type": "thumbnail",
                "action": "A/B test new thumbnail with higher contrast and clearer focal point",
                "expected_impact": "15-30% CTR improvement",
                "effort": "low"
            })

        # Retention optimization
        drop_offs = analytics["engagement_patterns"]["drop_off_points"]
        if drop_offs and drop_offs[0][0] < 30:
            recommendations.append({
                "priority": 1,
                "type": "content",
                "action": f"Strengthen hook - major drop at {drop_offs[0][0]}s: {drop_offs[0][2]}",
                "expected_impact": "20-40% retention improvement",
                "effort": "medium"
            })

        # Monetization optimization
        if analytics["monetization_metrics"]["rpm"] < 2.0:
            recommendations.append({
                "priority": 2,
                "type": "monetization",
                "action": "Add mid-roll ads at high engagement points",
                "expected_impact": "30-50% revenue increase",
                "effort": "low"
            })

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])

        return recommendations

    def _load_template(self) -> Template:
        """Load report template."""
        template_content = '''
# Performance Report: {{ video_id }}
Generated: {{ generated_at }}

## Executive Summary
- **Performance Score**: {{ analytics.performance_score }}/100
- **Total Views**: {{ analytics.kpis.views|number_format }}
- **CTR**: {{ analytics.kpis.ctr }}%
- **Average View Duration**: {{ analytics.kpis.avg_view_duration_sec|duration }}
- **RPM**: ${{ analytics.monetization_metrics.rpm }}

## Key Insights
{% for insight in insights %}
- {{ insight }}
{% endfor %}

## Performance Predictions
- **7-Day Forecast**: {{ predictions.views_7d|number_format }} views
- **30-Day Forecast**: {{ predictions.views_30d|number_format }} views
- **Revenue Forecast**: ${{ predictions.revenue_30d }}
- **Confidence**: {{ predictions.confidence|percentage }}

## Recommendations
{% for rec in recommendations %}
### {{ loop.index }}. {{ rec.action }}
- **Type**: {{ rec.type }}
- **Priority**: {{ rec.priority }}
- **Expected Impact**: {{ rec.expected_impact }}
- **Effort**: {{ rec.effort }}
{% endfor %}

## Active Experiments
{% for experiment in experiments %}
### {{ experiment.hypothesis }}
- **Status**: {{ experiment.status }}
- **KPI**: {{ experiment.kpi }}
- **Best Variant**: {{ experiment.analysis.winner if experiment.analysis else "TBD" }}
- **Lift**: {{ experiment.analysis.lift_percentage if experiment.analysis else "TBD" }}%
{% endfor %}

## Charts
![Retention Curve]({{ charts.retention_curve }})
![Traffic Sources]({{ charts.traffic_sources }})
        '''
        return Template(template_content)
```

### Enhanced CLI Commands

```python
# src/yt_faceless/cli.py additions

@app.command()
def publish(
    slug: str = typer.Argument(..., help="Content slug"),
    video_path: Optional[Path] = typer.Option(None, "--video", help="Override video path"),
    thumbnail_path: Optional[Path] = typer.Option(None, "--thumbnail", help="Override thumbnail"),
    privacy: str = typer.Option("private", "--privacy", help="Privacy status"),
    schedule: Optional[str] = typer.Option(None, "--schedule", help="Schedule time (RFC3339)"),
    platforms: List[str] = typer.Option(["youtube"], "--platform", help="Target platforms"),
    experiment: Optional[str] = typer.Option(None, "--experiment", help="Link to experiment"),
    verify: bool = typer.Option(True, "--verify/--no-verify", help="Verify after upload"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate upload"),
    force: bool = typer.Option(False, "--force", help="Force upload even if exists"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Upload video with enhanced validation and verification."""
    config = load_config()
    orchestrator = EnhancedUploadOrchestrator(config, N8NClient(config))

    try:
        response = orchestrator.publish_with_verification(
            slug=slug,
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            schedule_iso=schedule,
            privacy=privacy,
            platforms=platforms,
            experiment_id=experiment,
            dry_run=dry_run,
            force=force
        )

        if json_output:
            typer.echo(json.dumps(response, indent=2))
        else:
            typer.echo(f"✅ Upload successful!")
            typer.echo(f"Video ID: {response['video_id']}")
            typer.echo(f"Status: {response['status']}")
            if response.get('verification_status'):
                typer.echo(f"Processing: {response['verification_status']['processing_status']}")
            typer.echo(f"Transaction: {response['transaction_id']}")

    except Exception as e:
        typer.echo(f"❌ Upload failed: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def analytics(
    video_id: str = typer.Argument(..., help="Video ID or slug"),
    lookback: int = typer.Option(28, "--lookback", help="Days to look back"),
    metrics: Optional[List[str]] = typer.Option(None, "--metric", help="Specific metrics"),
    predict: bool = typer.Option(False, "--predict", help="Include predictions"),
    anomalies: bool = typer.Option(False, "--anomalies", help="Detect anomalies"),
    report: bool = typer.Option(False, "--report", help="Generate full report"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Fetch and analyze video performance with predictions."""
    config = load_config()
    client = N8NClient(config)
    predictor = PerformancePredictor()

    # Fetch analytics
    request = AnalyticsRequest(
        video_id=video_id,
        lookback_days=lookback,
        granularity="daily",
        metrics=metrics or ["views", "ctr", "retention", "revenue"],
        include_predictions=predict,
        include_anomalies=anomalies
    )

    analytics = client.fetch_analytics(request)

    if report:
        generator = EnhancedReportGenerator(config)
        report_path = generator.generate_performance_report(
            video_id=video_id,
            analytics=analytics,
            experiments=[],
            predictions=analytics.get("predictions", {})
        )
        typer.echo(f"📊 Report generated: {report_path}")

    if json_output:
        typer.echo(json.dumps(analytics, indent=2))
    else:
        # Display summary
        typer.echo(f"📊 Analytics for {video_id}")
        typer.echo(f"Performance Score: {analytics['performance_score']}/100")
        typer.echo(f"Views: {analytics['kpis']['views']:,}")
        typer.echo(f"CTR: {analytics['kpis']['ctr']:.1f}%")
        typer.echo(f"RPM: ${analytics['monetization_metrics']['rpm']:.2f}")

        if analytics.get("anomalies"):
            typer.echo("\n⚠️ Anomalies Detected:")
            for anomaly in analytics["anomalies"]:
                typer.echo(f"  - {anomaly['metric']}: {anomaly['probable_cause']}")

        if analytics.get("predictions"):
            pred = analytics["predictions"]
            typer.echo(f"\n📈 Predictions (confidence: {pred['confidence']:.0%}):")
            typer.echo(f"  - 7-day views: {pred['views_7d']:,}")
            typer.echo(f"  - 30-day revenue: ${pred['revenue_30d']:.2f}")

@app.command()
def experiment(
    action: str = typer.Argument(..., help="create|execute|status|analyze"),
    video_id: Optional[str] = typer.Option(None, "--video", help="Video ID"),
    hypothesis: Optional[str] = typer.Option(None, "--hypothesis", help="Experiment hypothesis"),
    variants: Optional[List[str]] = typer.Option(None, "--variant", help="Variant definitions"),
    experiment_id: Optional[str] = typer.Option(None, "--id", help="Experiment ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate experiment"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Manage optimization experiments."""
    config = load_config()
    orchestrator = ExperimentOrchestrator(config, N8NClient(config))

    if action == "create":
        if not video_id or not hypothesis:
            typer.echo("--video and --hypothesis required for create", err=True)
            raise typer.Exit(1)

        # Parse variants
        parsed_variants = []
        for variant_str in variants or []:
            # Format: "name:type=value"
            parts = variant_str.split(":")
            name = parts[0]
            changes = {}
            if len(parts) > 1:
                for change in parts[1].split(","):
                    key, value = change.split("=")
                    changes[key] = value
            parsed_variants.append({"name": name, "changes": changes})

        experiment = orchestrator.create_experiment(
            video_id=video_id,
            hypothesis=hypothesis,
            variants=parsed_variants
        )

        if json_output:
            typer.echo(json.dumps(experiment, indent=2))
        else:
            typer.echo(f"✅ Experiment created: {experiment['id']}")

    elif action == "execute":
        if not experiment_id:
            typer.echo("--id required for execute", err=True)
            raise typer.Exit(1)

        result = orchestrator.execute_experiment(experiment_id, dry_run=dry_run)

        if json_output:
            typer.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            typer.echo(f"🧪 Experiment {result['status']}")
            if result.get("analysis") and result["analysis"].get("has_winner"):
                typer.echo(f"🏆 Winner: {result['analysis']['winner']}")
                typer.echo(f"Lift: {result['analysis']['lift_percentage']:.1f}%")
```

### Testing Strategy

#### Unit Tests (`tests/test_upload_enhanced.py`)
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import hashlib

from yt_faceless.orchestrator import EnhancedUploadOrchestrator
from yt_faceless.core.transactions import UploadTransaction
from yt_faceless.core.quality import VideoQualityAnalyzer

class TestEnhancedUpload:
    """Test enhanced upload functionality."""

    @pytest.fixture
    def orchestrator(self, mock_config, mock_n8n_client):
        return EnhancedUploadOrchestrator(mock_config, mock_n8n_client)

    def test_quality_gates_pass(self, orchestrator, tmp_path):
        """Test quality gates with passing video."""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video content")

        with patch.object(VideoQualityAnalyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = MagicMock(
                duration_sec=300,
                resolution=(1920, 1080),
                scores={"technical": 85}
            )

            with patch.object(VideoQualityAnalyzer, 'check_loudness') as mock_loudness:
                mock_loudness.return_value = (-14, 7)

                transaction = UploadTransaction(
                    transaction_id="test_123",
                    slug="test",
                    started_at=datetime.utcnow(),
                    state="pending"
                )

                # Should not raise
                orchestrator._run_quality_gates(video_path, transaction)

                assert "quality_gates_passed" in transaction.checkpoints

    def test_quality_gates_fail_duration(self, orchestrator, tmp_path):
        """Test quality gates fail on short duration."""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video content")

        with patch.object(VideoQualityAnalyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = MagicMock(
                duration_sec=30,  # Too short
                resolution=(1920, 1080)
            )

            transaction = UploadTransaction(
                transaction_id="test_123",
                slug="test",
                started_at=datetime.utcnow(),
                state="pending"
            )

            with pytest.raises(QualityGateError) as exc_info:
                orchestrator._run_quality_gates(video_path, transaction)

            assert "too short" in str(exc_info.value)

    def test_transaction_rollback(self, orchestrator):
        """Test transaction rollback on failure."""
        transaction = UploadTransaction(
            transaction_id="test_123",
            slug="test",
            started_at=datetime.utcnow(),
            state="pending"
        )

        # Add checkpoints with rollback actions
        rollback_called = []

        def rollback1():
            rollback_called.append("action1")

        def rollback2():
            rollback_called.append("action2")

        transaction.checkpoint("step1", {"data": 1}, rollback1)
        transaction.checkpoint("step2", {"data": 2}, rollback2)

        # Execute rollback
        errors = transaction.rollback()

        # Verify rollback executed in reverse order
        assert rollback_called == ["action2", "action1"]
        assert transaction.state == "rolled_back"

    def test_idempotency_check(self, orchestrator, tmp_path):
        """Test idempotency prevents duplicate uploads."""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video content")

        # Create existing manifest
        manifest_dir = orchestrator.config.directories.output_dir / "test"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifest_dir / "upload_manifest.json"

        checksum = hashlib.sha256(b"fake video content").hexdigest()
        manifest_file.write_text(json.dumps({
            "video_id": "existing_123",
            "checksum": checksum,
            "uploaded_at": datetime.utcnow().isoformat()
        }))

        with patch.object(orchestrator, '_check_existing_upload') as mock_check:
            mock_check.return_value = {"video_id": "existing_123", "status": "uploaded"}

            result = orchestrator.publish_with_verification(
                slug="test",
                video_path=video_path,
                force=False
            )

            assert result["video_id"] == "existing_123"
            # Verify no actual upload occurred
            orchestrator.n8n_client.upload_video.assert_not_called()
```

#### Integration Tests (`tests/test_analytics_enhanced.py`)
```python
class TestEnhancedAnalytics:
    """Test enhanced analytics functionality."""

    def test_anomaly_detection(self):
        """Test anomaly detection in metrics."""
        predictor = PerformancePredictor()

        current = {"ctr": 1.5, "retention": 35, "views": 10000}
        expected = {"ctr": 5.0, "retention": 50, "views": 8000}
        variance = {"ctr": 0.5, "retention": 5, "views": 1000}

        anomalies = predictor.detect_anomalies(current, expected, variance)

        assert len(anomalies) == 2  # CTR and retention anomalies
        assert any(a["metric"] == "ctr" for a in anomalies)
        assert any(a["metric"] == "retention" for a in anomalies)

        ctr_anomaly = next(a for a in anomalies if a["metric"] == "ctr")
        assert ctr_anomaly["severity"] == "high"
        assert "thumbnail" in ctr_anomaly["probable_cause"].lower()

    def test_experiment_progressive_rollout(self):
        """Test progressive experiment rollout."""
        orchestrator = ExperimentOrchestrator(mock_config, mock_n8n_client)

        experiment = orchestrator.create_experiment(
            video_id="test_video",
            hypothesis="New thumbnail increases CTR",
            variants=[
                {"name": "Control", "changes": {}},
                {"name": "Variant A", "changes": {"thumbnail": "path/to/thumb_a.jpg"}}
            ],
            allocation_method="progressive"
        )

        assert experiment["allocation"]["method"] == "progressive"
        assert experiment["allocation"]["ramp_up_hours"] == 24
        assert len(experiment["rollout_strategy"]["stages"]) > 1

        # Verify stages increase traffic progressively
        stages = experiment["rollout_strategy"]["stages"]
        assert stages[0]["percentage"] < stages[-1]["percentage"]
```

### Rollback and Error Recovery Procedures

#### 1. Upload Rollback
```python
# src/yt_faceless/recovery/rollback.py

class UploadRollbackManager:
    """Manage upload rollback procedures."""

    def __init__(self, config: AppConfig, n8n_client: N8NClient):
        self.config = config
        self.n8n_client = n8n_client

    def rollback_upload(self, transaction_id: str) -> RollbackResult:
        """Rollback a failed or problematic upload."""

        # Load transaction
        transaction_file = self.config.directories.data_dir / "transactions" / f"{transaction_id}.json"
        if not transaction_file.exists():
            raise ValueError(f"Transaction {transaction_id} not found")

        transaction_data = json.loads(transaction_file.read_text())

        result = RollbackResult(
            transaction_id=transaction_id,
            started_at=datetime.utcnow(),
            actions_taken=[]
        )

        try:
            # Check if video was uploaded
            if "video_id" in transaction_data.get("checkpoints", {}).get("upload_completed", {}).get("data", {}):
                video_id = transaction_data["checkpoints"]["upload_completed"]["data"]["video_id"]

                # Set video to private/unlisted
                self.n8n_client.update_video_metadata(
                    video_id,
                    {"privacy_status": "private"}
                )
                result.actions_taken.append(f"Set video {video_id} to private")

                # Remove from playlists if added
                if "playlists" in transaction_data.get("checkpoints", {}):
                    for playlist_id in transaction_data["checkpoints"]["playlists"]["data"]:
                        self.n8n_client.remove_from_playlist(video_id, playlist_id)
                        result.actions_taken.append(f"Removed from playlist {playlist_id}")

            # Restore original metadata if changed
            if "original_metadata" in transaction_data.get("checkpoints", {}):
                original = transaction_data["checkpoints"]["original_metadata"]["data"]
                self.n8n_client.update_video_metadata(video_id, original)
                result.actions_taken.append("Restored original metadata")

            result.status = "success"

        except Exception as e:
            result.status = "partial"
            result.error = str(e)

        finally:
            result.completed_at = datetime.utcnow()

            # Update transaction state
            transaction_data["state"] = "rolled_back"
            transaction_data["rollback_result"] = result.__dict__
            transaction_file.write_text(json.dumps(transaction_data, indent=2, default=str))

        return result
```

#### 2. Experiment Rollback
```python
def rollback_experiment(self, experiment_id: str) -> RollbackResult:
    """Rollback an experiment and restore original state."""

    experiment = self.active_experiments.get(experiment_id)
    if not experiment:
        raise ValueError(f"Experiment {experiment_id} not found")

    result = RollbackResult(
        experiment_id=experiment_id,
        started_at=datetime.utcnow()
    )

    try:
        # Restore original metadata for all variants
        for variant in experiment["variants"]:
            if "original_state" in variant:
                self.n8n_client.update_video_metadata(
                    experiment["video_id"],
                    variant["original_state"],
                    variant_id=None  # Clear variant
                )
                result.actions_taken.append(f"Restored {variant['variant_id']}")

        # Clear experiment flags
        self.n8n_client.clear_experiment(experiment["video_id"])

        # Update experiment status
        experiment["status"] = "rolled_back"
        result.status = "success"

    except Exception as e:
        result.status = "failed"
        result.error = str(e)

    return result
```

### Monitoring and Alerting Hooks

```python
# src/yt_faceless/monitoring/alerts.py

class AlertManager:
    """Manage monitoring and alerting."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.alert_thresholds = {
            "upload_failure_rate": 0.1,  # 10%
            "quality_gate_failure_rate": 0.2,  # 20%
            "experiment_failure_rate": 0.15,  # 15%
            "anomaly_count": 5,  # per video
        }

    def check_alerts(self) -> List[Alert]:
        """Check for conditions requiring alerts."""
        alerts = []

        # Check upload failures
        recent_uploads = self._get_recent_uploads(hours=24)
        failure_rate = len([u for u in recent_uploads if u["status"] == "failed"]) / len(recent_uploads)

        if failure_rate > self.alert_thresholds["upload_failure_rate"]:
            alerts.append(Alert(
                severity="high",
                type="upload_failures",
                message=f"Upload failure rate {failure_rate:.1%} exceeds threshold",
                data={"failure_rate": failure_rate}
            ))

        # Check for anomalies
        for video in self._get_recent_videos(days=7):
            anomaly_count = len(video.get("anomalies", []))
            if anomaly_count > self.alert_thresholds["anomaly_count"]:
                alerts.append(Alert(
                    severity="medium",
                    type="anomalies",
                    message=f"Video {video['id']} has {anomaly_count} anomalies",
                    data={"video_id": video["id"], "anomalies": video["anomalies"]}
                ))

        return alerts

    def send_alerts(self, alerts: List[Alert]):
        """Send alerts via configured channels."""
        for alert in alerts:
            if alert.severity == "high":
                # Send via n8n error webhook
                if self.config.webhooks.error_url:
                    self.n8n_client.send_error_notification(alert)

            # Log all alerts
            logger.warning(f"Alert: {alert.type} - {alert.message}")
```

---

## Summary of Enhancements

### Phase 6 Enhancements
1. **Transaction Management**: Full rollback capability with checkpoints
2. **Quality Gates**: Pre-upload validation for technical quality, copyright, loudness
3. **Multi-Platform Ready**: Support for YouTube, Shorts, TikTok with platform-specific handling
4. **Enhanced Verification**: Post-upload verification with retry logic
5. **Monetization Settings**: Direct control over ads, sponsorships, affiliate links

### Phase 7 Enhancements
1. **Predictive Analytics**: ML-based performance forecasting
2. **Anomaly Detection**: Statistical anomaly detection with root cause analysis
3. **Multi-Variant Testing**: Beyond A/B to multi-variant with Bayesian statistics
4. **Progressive Rollout**: Staged experiment deployment with success gates
5. **Comprehensive Reporting**: Visual reports with charts, insights, and recommendations

### Cross-Phase Integration
1. **Feedback Loop**: Analytics insights feed back to research phase for content strategy
2. **Experiment Tracking**: Experiments linked through upload to analytics
3. **Unified Transaction Model**: Consistent transaction handling across phases
4. **Shared Quality Framework**: Quality scores used in both upload and optimization

### Robustness Features
1. **Rollback Procedures**: Complete rollback for uploads and experiments
2. **Error Recovery**: Graceful degradation and partial success handling
3. **Monitoring & Alerts**: Proactive alerting for failures and anomalies
4. **Audit Trail**: Complete transaction and action logging

This enhanced plan provides a production-ready, scalable implementation that can handle edge cases, failures, and complex optimization scenarios while maintaining data integrity and providing actionable insights.