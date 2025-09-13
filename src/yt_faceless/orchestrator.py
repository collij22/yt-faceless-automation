from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .assembly import ClipSpec, assemble_video
from .config import AppConfig
from .core.config import load_config as load_enhanced_config
from .core.errors import ConfigurationError
from .core.schemas import (
    AnalyticsRequest,
    ChapterMarker,
    EnhancedAnalyticsSnapshot,
    ExperimentResult,
    ExperimentVariant,
    MonetizationSettings,
    MultiVariantExperiment,
    QualityGates,
    RolloutStage,
    RolloutStrategy,
    StatisticalConfig,
    SuccessCriteria,
    TrafficAllocation,
    YouTubeUploadPayload,
    YouTubeUploadResponse,
)
from .integrations.n8n_client import N8NClient
from .logging_setup import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class Orchestrator:
    """High-level pipeline orchestrator with Phase 6-7 functionality.

    Handles video assembly, upload with idempotency, analytics, and experiments.
    """

    config: AppConfig
    enhanced_config: AppConfig = field(init=False)
    n8n_client: N8NClient = field(init=False)
    transaction_dir: Path = field(init=False)

    def __post_init__(self):
        """Initialize enhanced components."""
        # Load enhanced config for new features
        self.enhanced_config = load_enhanced_config()
        self.n8n_client = N8NClient(self.enhanced_config)
        self.transaction_dir = self.enhanced_config.directories.data_dir / "transactions"
        self.transaction_dir.mkdir(parents=True, exist_ok=True)

    def assemble(
        self, *, clip_paths: Iterable[Path], audio_path: Path, output_path: Path
    ) -> None:
        """Assemble video from clips and audio."""
        clips = [ClipSpec(path=p) for p in clip_paths]
        assemble_video(self.config, clips, audio_path, output_path)
        logger.info("Assembled video at %s", output_path)

    # Phase 6: Upload & Publishing

    def publish(
        self,
        slug: str,
        override_paths: Optional[Dict[str, Any]] = None,
        schedule_iso: Optional[str] = None,
        privacy: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
        verify: bool = True,
    ) -> YouTubeUploadResponse:
        """Publish video with idempotency and verification.

        Args:
            slug: Content slug identifier
            override_paths: Optional path overrides for video/thumbnail
            schedule_iso: ISO timestamp for scheduled publishing
            privacy: Privacy status (public/unlisted/private)
            dry_run: Simulate upload without actual execution
            force: Force upload even if already exists
            verify: Whether to verify upload after completion

        Returns:
            Upload response with video ID and status
        """
        # Start transaction
        transaction_id = self._generate_transaction_id()
        logger.info(f"Starting upload transaction {transaction_id} for slug: {slug}")

        try:
            # Load metadata
            metadata_path = self.enhanced_config.directories.content_dir / slug / "metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata not found for slug: {slug}")

            with open(metadata_path) as f:
                metadata = json.load(f)

            # Resolve paths
            video_path = Path(override_paths.get("video")) if override_paths and "video" in override_paths else None
            if not video_path:
                video_path = self.enhanced_config.directories.content_dir / slug / "final.mp4"

            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            thumbnail_path = Path(override_paths.get("thumbnail")) if override_paths and "thumbnail" in override_paths else None
            if not thumbnail_path:
                thumbnail_path = self.enhanced_config.directories.content_dir / slug / "thumbnail.jpg"
                if not thumbnail_path.exists():
                    thumbnail_path = None

            # Calculate checksum for idempotency
            checksum = self._calculate_file_checksum(video_path)

            # Check for existing upload (idempotency)
            if not force:
                existing = self._check_existing_upload(slug, checksum)
                if existing:
                    logger.info(f"Found existing upload for slug {slug} with matching checksum")
                    return existing

            # Prepare chapters
            chapters = None
            if metadata.get("chapters"):
                chapters = [
                    ChapterMarker(start=c["start"], title=c["title"])
                    for c in metadata["chapters"]
                ]

            # Build upload payload
            payload = YouTubeUploadPayload(
                video_path=str(video_path),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                title=metadata.get("title", metadata.get("titles", [{}])[0].get("text", f"Video {slug}")),
                description=metadata.get("description", {}).get("text", ""),
                tags=metadata.get("tags", {}).get("primary", []) + metadata.get("tags", {}).get("competitive", []),
                category_id=metadata.get("category_id"),
                privacy_status=privacy or os.getenv("DEFAULT_PRIVACY_STATUS", "private"),
                publish_at_iso=schedule_iso,
                made_for_kids=metadata.get("made_for_kids", False),
                language=metadata.get("language", "en"),
                chapters=chapters,
                slug=slug,
                checksum_sha256=checksum,
                transaction_id=transaction_id,
                # Don't send quality_gates unless actually validated
                monetization_settings=MonetizationSettings(
                    enable_ads=metadata.get("monetization", {}).get("enable_ads", True)
                ),
                platform_targets=["youtube"],
                upload_priority=5,
            )

            if dry_run:
                logger.info("Dry run mode - skipping actual upload")
                return YouTubeUploadResponse(
                    execution_id="dry_run",
                    video_id="dry_run_video_id",
                    status="scheduled" if schedule_iso else "uploaded",
                    transaction_id=transaction_id,
                    upload_duration_ms=0,
                )

            # Perform upload
            response = self.n8n_client.upload_video(payload)

            # Save upload manifest for idempotency
            self._save_upload_manifest(slug, payload, response)

            # Verify upload if requested
            if verify and response.status in ["uploaded", "scheduled"]:
                self._verify_upload(response.video_id)

            logger.info(f"Successfully uploaded video {response.video_id} for slug {slug}")
            return response

        except Exception as e:
            logger.error(f"Upload failed for {slug}: {e}")
            # Could implement rollback here if needed
            raise

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        return f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _check_existing_upload(self, slug: str, checksum: str) -> Optional[YouTubeUploadResponse]:
        """Check if video was already uploaded (idempotency)."""
        manifest_path = self.enhanced_config.directories.output_dir / slug / "upload_manifest.json"

        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Check if same checksum
            if manifest.get("checksum") == checksum:
                logger.info(f"Found existing upload for slug {slug} with matching checksum")
                return YouTubeUploadResponse(**manifest["response"])

        return None

    def _save_upload_manifest(
        self,
        slug: str,
        payload: YouTubeUploadPayload,
        response: YouTubeUploadResponse
    ) -> None:
        """Save upload manifest for idempotency and auditing."""
        manifest_dir = self.enhanced_config.directories.output_dir / slug
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = manifest_dir / "upload_manifest.json"

        manifest = {
            "slug": slug,
            "transaction_id": payload.transaction_id,
            "checksum": payload.checksum_sha256,
            "uploaded_at": datetime.now().isoformat(),
            "request": {
                "title": payload.title,
                "privacy_status": payload.privacy_status,
                "publish_at_iso": payload.publish_at_iso,
                "tags_count": len(payload.tags),
            },
            "response": response.model_dump() if hasattr(response, 'model_dump') else response.__dict__,
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.debug(f"Saved upload manifest to {manifest_path}")

    def _verify_upload(self, video_id: str) -> bool:
        """Verify video was uploaded successfully."""
        try:
            status = self.n8n_client.check_video_status(video_id)
            if status.get("processing_status") == "completed":
                logger.info(f"Video {video_id} processing completed")
                return True
            elif status.get("processing_status") == "failed":
                logger.error(f"Video {video_id} processing failed")
                return False
            else:
                logger.info(f"Video {video_id} still processing")
                return True  # Assume success, will check later
        except Exception as e:
            logger.warning(f"Could not verify upload status: {e}")
            return True  # Assume success if can't verify

    # Phase 7: Analytics & Optimization

    def analytics(
        self,
        slug_or_video_id: str,
        lookback_days: Optional[int] = None
    ) -> EnhancedAnalyticsSnapshot:
        """Fetch analytics for a video.

        Args:
            slug_or_video_id: Content slug or YouTube video ID
            lookback_days: Days to look back (default from config)

        Returns:
            Enhanced analytics snapshot with KPIs and predictions
        """
        # Resolve video ID if slug provided
        # YouTube video IDs are 11 characters long with specific charset
        youtube_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{11}$')

        video_id = slug_or_video_id

        # Check if it looks like a YouTube video ID
        is_youtube_id = bool(youtube_id_pattern.match(video_id))

        # If it doesn't look like a YouTube ID, treat as slug
        if not is_youtube_id:
            # Try to resolve from manifest
            manifest_path = self.enhanced_config.directories.output_dir / slug_or_video_id / "upload_manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                video_id = manifest["response"]["video_id"]
                logger.info(f"Resolved slug '{slug_or_video_id}' to video ID: {video_id}")
            else:
                # Still use it as-is but warn
                logger.warning(f"Could not verify if '{slug_or_video_id}' is a valid video ID or resolve it as slug")

        # Create analytics request
        request = AnalyticsRequest(
            video_id=video_id,
            lookback_days=lookback_days or int(os.getenv("ANALYTICS_LOOKBACK_DAYS", "28")),
            granularity="daily",
            include_predictions=True,
            include_anomalies=True,
        )

        # Fetch analytics
        snapshot = self.n8n_client.fetch_analytics(request)

        logger.info(f"Fetched analytics for {video_id}: Score={snapshot.performance_score}/100")

        return snapshot

    def propose_experiments(
        self,
        snapshot: EnhancedAnalyticsSnapshot,
        baselines: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Propose optimization experiments based on analytics.

        Args:
            snapshot: Analytics snapshot
            baselines: Optional baseline thresholds

        Returns:
            List of prioritized experiment proposals
        """
        proposals = []

        # Default baselines
        if not baselines:
            baselines = {
                "ctr_low": 4.0,
                "apv_low": 45.0,
                "avd_low_sec": 120,
            }

        # CTR optimization
        if snapshot.kpis.ctr < baselines["ctr_low"]:
            proposals.append({
                "type": "thumbnail",
                "priority": 1,
                "hypothesis": f"New thumbnail can improve CTR from {snapshot.kpis.ctr:.1f}% to >{baselines['ctr_low']}%",
                "kpi": "ctr",
                "target_delta_pct": 25.0,
            })

        # Retention optimization
        if snapshot.kpis.avg_percentage_viewed < baselines["apv_low"]:
            proposals.append({
                "type": "description",
                "priority": 2,
                "hypothesis": f"Better description/chapters can improve APV from {snapshot.kpis.avg_percentage_viewed:.1f}% to >{baselines['apv_low']}%",
                "kpi": "apv",
                "target_delta_pct": 15.0,
            })

        # Early drop-off
        if snapshot.retention_curve and len(snapshot.retention_curve) > 0:
            first_30s_retention = next((p.pct_viewing for p in snapshot.retention_curve if p.second == 30), 100)
            if first_30s_retention < 70:
                proposals.append({
                    "type": "title",
                    "priority": 1,
                    "hypothesis": f"Stronger title/hook can reduce 30s drop-off from {100-first_30s_retention:.0f}% to <30%",
                    "kpi": "retention_30s",
                    "target_delta_pct": 20.0,
                })

        # Sort by priority
        proposals.sort(key=lambda x: x["priority"])

        return proposals

    def create_experiment(
        self,
        video_id: str,
        hypothesis: str,
        variants: List[Dict[str, Any]],
        kpi: str = "ctr",
        allocation_method: str = "progressive"
    ) -> MultiVariantExperiment:
        """Create a new optimization experiment.

        Args:
            video_id: YouTube video ID
            hypothesis: Experiment hypothesis
            variants: List of variant configurations
            kpi: Primary KPI to optimize
            allocation_method: Traffic allocation method

        Returns:
            Configured experiment ready for execution
        """
        experiment_id = f"exp_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create experiment configuration
        experiment = MultiVariantExperiment(
            id=experiment_id,
            video_id=video_id,
            hypothesis=hypothesis,
            kpi=kpi,
            target_delta_pct=10.0,
            priority=1,
            variants=[
                ExperimentVariant(
                    variant_id=f"var_{i}",
                    name=v.get("name", f"Variant {i}"),
                    changes=v.get("changes", {}),
                    weight=1.0 / len(variants),
                )
                for i, v in enumerate(variants)
            ],
            allocation=TrafficAllocation(
                method=allocation_method,
                ramp_up_hours=24 if allocation_method == "progressive" else 0,
                target_impressions_per_variant=1000,
            ),
            statistical_config=StatisticalConfig(
                confidence_level=0.95,
                minimum_sample_size=1000,
                test_type="bayesian",
                early_stopping_enabled=True,
            ),
            rollout_strategy=RolloutStrategy(
                strategy="progressive" if allocation_method == "progressive" else "immediate",
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
            ),
            success_criteria=SuccessCriteria(
                primary_metric=kpi,
                minimum_lift=5.0,
                guardrail_metrics={"retention": -5.0},
            ),
        )

        # Save experiment configuration
        exp_dir = self.enhanced_config.directories.data_dir / "experiments"
        exp_dir.mkdir(exist_ok=True)

        exp_file = exp_dir / f"{experiment_id}.json"
        with open(exp_file, "w") as f:
            json.dump(experiment.model_dump() if hasattr(experiment, 'model_dump') else experiment.__dict__, f, indent=2, default=str)

        logger.info(f"Created experiment {experiment_id} for video {video_id}")

        return experiment

    def write_report(
        self,
        slug: str,
        snapshot: EnhancedAnalyticsSnapshot,
        proposals: List[Dict[str, Any]]
    ) -> Path:
        """Write analytics report with recommendations.

        Args:
            slug: Content slug
            snapshot: Analytics snapshot
            proposals: Experiment proposals

        Returns:
            Path to generated report
        """
        reports_dir = self.enhanced_config.directories.data_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        report_path = reports_dir / f"{datetime.now().strftime('%Y%m%d')}_{slug}.md"

        # Generate report content
        content = f"""# Analytics Report: {slug}
Generated: {datetime.now().isoformat()}

## Performance Summary
- **Performance Score**: {snapshot.performance_score:.0f}/100
- **Views**: {snapshot.kpis.views:,}
- **CTR**: {snapshot.kpis.ctr:.1f}%
- **Average View Duration**: {snapshot.kpis.avg_view_duration_sec:.0f}s
- **Average Percentage Viewed**: {snapshot.kpis.avg_percentage_viewed:.1f}%

## Recommendations
"""
        for i, proposal in enumerate(proposals, 1):
            content += f"""
### {i}. {proposal['hypothesis']}
- **Type**: {proposal['type']}
- **Priority**: {proposal['priority']}
- **Target KPI**: {proposal['kpi']}
- **Target Improvement**: {proposal['target_delta_pct']:.0f}%
"""

        # Add anomalies if present
        if snapshot.anomalies:
            content += "\n## Anomalies Detected\n"
            for anomaly in snapshot.anomalies:
                content += f"- **{anomaly.metric}**: {anomaly.probable_cause} (severity: {anomaly.severity})\n"

        # Add predictions if present
        if snapshot.predictions:
            content += f"""
## Performance Predictions
- **7-Day Views**: {snapshot.predictions.views_7d:,}
- **30-Day Views**: {snapshot.predictions.views_30d:,}
- **30-Day Revenue**: ${snapshot.predictions.revenue_30d:.2f}
- **Confidence**: {snapshot.predictions.confidence:.0%}
"""

        # Write report
        with open(report_path, "w") as f:
            f.write(content)

        logger.info(f"Generated report: {report_path}")

        return report_path
