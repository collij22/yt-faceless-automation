"""Cross-platform content distribution system for TikTok, Instagram, X."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import AppConfig
from ..core.schemas import DistributionTarget
from ..integrations.n8n_client import N8NClient
from ..logging_setup import get_logger

logger = get_logger(__name__)


class CrossPlatformDistributor:
    """Manages cross-platform content distribution."""

    def __init__(self, config: AppConfig):
        """Initialize distributor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.n8n_client = N8NClient(config)
        self.data_dir = config.directories.data_dir / "distribution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.schedule_file = self.data_dir / "schedule.json"
        self.history_file = self.data_dir / "history.json"

    def _load_schedule(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load distribution schedule from file."""
        if not self.schedule_file.exists():
            return {}

        with open(self.schedule_file, 'r') as f:
            return json.load(f)

    def _save_schedule(self, schedule: Dict[str, List[Dict[str, Any]]]) -> None:
        """Save distribution schedule to file."""
        with open(self.schedule_file, 'w') as f:
            json.dump(schedule, f, indent=2)

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load distribution history."""
        if not self.history_file.exists():
            return []

        with open(self.history_file, 'r') as f:
            return json.load(f)

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save distribution history."""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def _flatten_tags(self, tags):
        """Flatten tags from dict or list format.

        Args:
            tags: Either a dict with categorized tags or a list of tags

        Returns:
            Flat list of tags
        """
        if isinstance(tags, dict):
            return (tags.get("primary", []) + tags.get("competitive", []) +
                    tags.get("trending", []) + tags.get("long_tail", []))
        return tags or []

    def adapt_for_platform(
        self,
        video_path: Path,
        target: DistributionTarget,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt content for specific platform requirements.

        Args:
            video_path: Path to original video
            target: Target platform configuration
            metadata: Original video metadata

        Returns:
            Platform-specific adaptation settings
        """
        adaptations = {}

        if target.platform == "tiktok":
            # TikTok: 9:16, max 60 seconds for standard accounts
            adaptations["aspect_ratio"] = "9:16"
            adaptations["max_duration"] = 60 if not target.premium_account else 180
            adaptations["hashtag_limit"] = 100  # Character limit for hashtags
            adaptations["caption_limit"] = 2200

            # Adapt caption
            caption = metadata.get("title", "")[:100]
            tags = self._flatten_tags(metadata.get("tags", []))[:5]  # TikTok recommends 3-5 hashtags
            hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags])

            adaptations["caption"] = f"{caption}\n\n{hashtags}"
            adaptations["audio_sync"] = True  # TikTok favors synced audio

        elif target.platform == "instagram":
            # Instagram Reels: 9:16, max 90 seconds
            adaptations["aspect_ratio"] = "9:16"
            adaptations["max_duration"] = 90
            adaptations["hashtag_limit"] = 30  # Max 30 hashtags
            adaptations["caption_limit"] = 2200

            # Adapt caption - handle both dict and string description
            desc_raw = metadata.get("description", "")
            if isinstance(desc_raw, dict):
                desc_text = desc_raw.get("text", "")
            else:
                desc_text = str(desc_raw)
            caption = desc_text[:500]
            tags = self._flatten_tags(metadata.get("tags", []))[:30]
            hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags])

            adaptations["caption"] = f"{caption}\n.\n.\n.\n{hashtags}"
            adaptations["cover_frame"] = True  # Instagram needs cover image

        elif target.platform == "x":
            # X (Twitter): 16:9 or 1:1, max 2:20 (140 seconds)
            adaptations["aspect_ratio"] = "16:9"
            adaptations["max_duration"] = 140
            adaptations["hashtag_limit"] = 2  # X recommends 1-2 hashtags
            adaptations["caption_limit"] = 280

            # Adapt caption
            title = metadata.get("title", "")[:200]
            tags = self._flatten_tags(metadata.get("tags", []))[:2]
            hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags])

            adaptations["caption"] = f"{title} {hashtags}".strip()[:280]
            adaptations["thread_continuation"] = True  # Can create thread for context

        # Common adaptations
        adaptations["original_slug"] = metadata.get("slug", "unknown")
        adaptations["original_duration"] = metadata.get("duration", 0)
        adaptations["needs_trimming"] = adaptations["original_duration"] > adaptations["max_duration"]

        return adaptations

    async def distribute_to_platform(
        self,
        video_path: Path,
        target: DistributionTarget,
        adaptations: Dict[str, Any],
        schedule_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Distribute content to a specific platform.

        Args:
            video_path: Path to video file
            target: Target platform configuration
            adaptations: Platform-specific adaptations
            schedule_time: Optional scheduled posting time

        Returns:
            Distribution result with platform response
        """
        if not target.webhook_url:
            logger.warning(f"No webhook configured for {target.platform}")
            return {
                "status": "skipped",
                "reason": "no_webhook",
                "platform": target.platform
            }

        # Prepare payload
        payload = {
            "platform": target.platform,
            "video_path": str(video_path),
            "caption": adaptations.get("caption", ""),
            "aspect_ratio": adaptations.get("aspect_ratio"),
            "max_duration": adaptations.get("max_duration"),
            "account_handle": target.account_handle,
            "api_credentials": target.api_credentials,
            "adaptations": adaptations
        }

        if schedule_time:
            payload["schedule_time"] = schedule_time.isoformat()

        try:
            # Execute distribution webhook
            response = await self.n8n_client.execute_webhook(
                target.webhook_url,
                payload,
                timeout=60
            )

            # Log to history
            history = self._load_history()
            history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "platform": target.platform,
                "slug": adaptations.get("original_slug"),
                "status": "success",
                "response": response
            })
            self._save_history(history)

            logger.info(f"Distributed to {target.platform}: {response.get('url', 'success')}")
            return response

        except Exception as e:
            logger.error(f"Failed to distribute to {target.platform}: {e}")

            # Log failure to history
            history = self._load_history()
            history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "platform": target.platform,
                "slug": adaptations.get("original_slug"),
                "status": "failed",
                "error": str(e)
            })
            self._save_history(history)

            return {
                "status": "failed",
                "error": str(e),
                "platform": target.platform
            }

    def schedule_distribution(
        self,
        slug: str,
        targets: List[DistributionTarget],
        base_time: Optional[datetime] = None,
        stagger_minutes: int = 30
    ) -> Dict[str, List[datetime]]:
        """Schedule distribution across platforms with staggered timing.

        Args:
            slug: Video slug
            targets: List of distribution targets
            base_time: Base time for scheduling (defaults to now + 1 hour)
            stagger_minutes: Minutes between platform posts

        Returns:
            Dictionary of platform -> scheduled times
        """
        if base_time is None:
            base_time = datetime.now(timezone.utc) + timedelta(hours=1)

        schedule = self._load_schedule()
        if slug not in schedule:
            schedule[slug] = []

        platform_times = {}
        current_time = base_time

        for target in targets:
            # Check platform-specific optimal timing
            optimal_time = self._get_optimal_time(target.platform, current_time)

            platform_times[target.platform] = optimal_time

            schedule[slug].append({
                "platform": target.platform,
                "scheduled_time": optimal_time.isoformat(),
                "account": target.account_handle,
                "status": "pending"
            })

            # Stagger next platform
            current_time = optimal_time + timedelta(minutes=stagger_minutes)

        self._save_schedule(schedule)
        logger.info(f"Scheduled distribution for {slug} across {len(targets)} platforms")

        return platform_times

    def _get_optimal_time(self, platform: str, base_time: datetime) -> datetime:
        """Get optimal posting time for platform.

        Args:
            platform: Platform name
            base_time: Base time to optimize from

        Returns:
            Optimized posting time
        """
        # Platform-specific optimal posting windows (in UTC)
        optimal_windows = {
            "tiktok": [(6, 10), (19, 23)],  # 6-10 AM, 7-11 PM
            "instagram": [(11, 13), (19, 21)],  # 11 AM-1 PM, 7-9 PM
            "x": [(9, 10), (19, 21)]  # 9-10 AM, 7-9 PM
        }

        windows = optimal_windows.get(platform, [(9, 17)])  # Default 9 AM-5 PM

        # Find nearest optimal window
        hour = base_time.hour
        best_hour = hour

        for start, end in windows:
            if start <= hour < end:
                # Already in optimal window
                return base_time

            if hour < start:
                # Next window is ahead
                best_hour = start
                break
            elif hour >= end and start > hour - 24:
                # Window is tomorrow
                best_hour = start
                break

        # Adjust to optimal hour
        optimal_time = base_time.replace(hour=best_hour % 24, minute=0, second=0)
        if best_hour < hour:
            # Move to tomorrow
            optimal_time += timedelta(days=1)

        return optimal_time

    async def execute_scheduled_distributions(self) -> Dict[str, Any]:
        """Execute any pending scheduled distributions.

        Returns:
            Summary of executed distributions
        """
        schedule = self._load_schedule()
        now = datetime.now(timezone.utc)
        executed = []

        for slug, distributions in schedule.items():
            content_dir = self.config.directories.content_dir / slug
            video_path = content_dir / "final.mp4"
            metadata_path = content_dir / "metadata.json"

            if not video_path.exists():
                logger.warning(f"Video not found for scheduled distribution: {slug}")
                continue

            # Load metadata
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            for dist in distributions:
                if dist["status"] != "pending":
                    continue

                scheduled_time = datetime.fromisoformat(dist["scheduled_time"])
                if scheduled_time <= now:
                    # Time to distribute
                    platform = dist["platform"]

                    # Find target configuration
                    # This would normally come from config, using defaults for now
                    target = DistributionTarget(
                        platform=platform,
                        account_handle=dist.get("account", f"@{platform}_account"),
                        webhook_url=getattr(self.config.webhooks, f"{platform}_upload_url", None),
                        api_credentials={},  # Would be loaded from secure storage
                        enabled=True
                    )

                    # Adapt content
                    adaptations = self.adapt_for_platform(video_path, target, metadata)

                    # Distribute
                    result = await self.distribute_to_platform(
                        video_path,
                        target,
                        adaptations
                    )

                    # Update status
                    dist["status"] = "completed" if result.get("status") != "failed" else "failed"
                    dist["result"] = result
                    dist["executed_at"] = datetime.now(timezone.utc).isoformat()

                    executed.append({
                        "slug": slug,
                        "platform": platform,
                        "result": result
                    })

        # Save updated schedule
        self._save_schedule(schedule)

        return {
            "executed": executed,
            "count": len(executed),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def distribute_content(
    config: AppConfig,
    slug: str,
    platforms: Optional[List[str]] = None,
    schedule: bool = False,
    schedule_time: Optional[datetime] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Distribute content across platforms.

    Args:
        config: Application configuration
        slug: Video slug
        platforms: List of platforms to distribute to
        schedule: Whether to schedule for later
        schedule_time: Specific time to schedule
        dry_run: Simulate without distributing

    Returns:
        Distribution results
    """
    if not (config.features.get("multiplatform_distribution") or config.features.get("cross_platform")):
        logger.info("Cross-platform distribution feature is disabled")
        return {"status": "disabled"}

    distributor = CrossPlatformDistributor(config)

    # Load video and metadata
    content_dir = config.directories.content_dir / slug
    video_path = content_dir / "final.mp4"
    metadata_path = content_dir / "metadata.json"

    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        return {"status": "error", "reason": "video_not_found"}

    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # Default to all enabled platforms
    if platforms is None:
        platforms = ["tiktok", "instagram", "x"]

    # Create targets
    targets = []
    for platform in platforms:
        webhook_url = getattr(config.webhooks, f"{platform}_upload_url", None)
        if webhook_url:
            target = DistributionTarget(
                platform=platform,
                account_handle=f"@{platform}_account",  # Would come from config
                webhook_url=webhook_url,
                api_credentials={},  # Would be loaded securely
                enabled=True
            )
            targets.append(target)

    if not targets:
        logger.warning("No distribution targets configured")
        return {"status": "no_targets"}

    results = {}

    if dry_run:
        # Simulate distribution
        for target in targets:
            adaptations = distributor.adapt_for_platform(video_path, target, metadata)
            results[target.platform] = {
                "status": "dry_run",
                "adaptations": adaptations
            }
        logger.info(f"[DRY RUN] Would distribute {slug} to {len(targets)} platforms")

    elif schedule:
        # Schedule for later
        schedule_times = distributor.schedule_distribution(
            slug,
            targets,
            base_time=schedule_time
        )
        results["scheduled"] = schedule_times
        logger.info(f"Scheduled distribution of {slug} to {len(targets)} platforms")

    else:
        # Distribute immediately
        for target in targets:
            adaptations = distributor.adapt_for_platform(video_path, target, metadata)
            result = await distributor.distribute_to_platform(
                video_path,
                target,
                adaptations
            )
            results[target.platform] = result

        logger.info(f"Distributed {slug} to {len(targets)} platforms")

    return results


async def schedule_distribution(
    config: AppConfig,
    slug: str,
    platforms: List[str],
    base_time: Optional[datetime] = None,
    stagger_minutes: int = 30
) -> Dict[str, Any]:
    """Schedule content distribution across platforms.

    Args:
        config: Application configuration
        slug: Video slug
        platforms: List of platforms
        base_time: Base scheduling time
        stagger_minutes: Minutes between posts

    Returns:
        Scheduling results
    """
    return await distribute_content(
        config,
        slug,
        platforms,
        schedule=True,
        schedule_time=base_time
    )