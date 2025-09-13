"""Content calendar and batch scheduling system."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import AppConfig
from ..integrations.n8n_client import N8NClient
from ..logging_setup import get_logger

logger = get_logger(__name__)


class ContentCalendar:
    """Manages content scheduling and publishing calendar."""

    def __init__(self, config: AppConfig):
        """Initialize content calendar.

        Args:
            config: Application configuration
        """
        self.config = config
        self.n8n_client = N8NClient(config)
        self.data_dir = config.directories.data_dir / "calendar"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.calendar_file = self.data_dir / "schedule.json"
        self.analytics_file = self.data_dir / "analytics.json"
        self.templates_file = self.data_dir / "templates.json"

        self.calendar = self._load_calendar()
        self.templates = self._load_templates()

    def _load_calendar(self) -> Dict[str, Any]:
        """Load content calendar."""
        if not self.calendar_file.exists():
            # Create default calendar structure
            default_calendar = {
                "scheduled": [],
                "published": [],
                "drafts": [],
                "recurring": [],
                "holidays": self._get_default_holidays()
            }
            self.calendar_file.write_text(json.dumps(default_calendar, indent=2))
            logger.info(f"Created default calendar at {self.calendar_file}")

        with open(self.calendar_file, 'r') as f:
            return json.load(f)

    def _save_calendar(self) -> None:
        """Save content calendar."""
        with open(self.calendar_file, 'w') as f:
            json.dump(self.calendar, f, indent=2, default=str)

    def _load_templates(self) -> Dict[str, Any]:
        """Load scheduling templates."""
        if not self.templates_file.exists():
            # Create default templates
            default_templates = {
                "daily": {
                    "name": "Daily Upload",
                    "frequency": "daily",
                    "times": ["09:00", "18:00"],
                    "timezone": "UTC",
                    "active": False
                },
                "weekday": {
                    "name": "Weekday Upload",
                    "frequency": "weekday",
                    "days": ["monday", "wednesday", "friday"],
                    "time": "15:00",
                    "timezone": "UTC",
                    "active": True
                },
                "weekend": {
                    "name": "Weekend Special",
                    "frequency": "weekly",
                    "days": ["saturday"],
                    "time": "12:00",
                    "timezone": "UTC",
                    "active": False
                },
                "optimal": {
                    "name": "Optimal Times",
                    "frequency": "custom",
                    "schedule": {
                        "monday": ["09:00", "17:00"],
                        "tuesday": ["10:00", "19:00"],
                        "wednesday": ["09:00", "18:00"],
                        "thursday": ["10:00", "20:00"],
                        "friday": ["09:00", "17:00"],
                        "saturday": ["11:00"],
                        "sunday": ["12:00", "20:00"]
                    },
                    "timezone": "UTC",
                    "active": False
                }
            }
            self.templates_file.write_text(json.dumps(default_templates, indent=2))
            logger.info(f"Created default templates at {self.templates_file}")

        with open(self.templates_file, 'r') as f:
            return json.load(f)

    def _get_default_holidays(self) -> List[Dict[str, str]]:
        """Get default holiday schedule."""
        current_year = datetime.now().year
        return [
            {"date": f"{current_year}-01-01", "name": "New Year's Day", "strategy": "avoid"},
            {"date": f"{current_year}-02-14", "name": "Valentine's Day", "strategy": "themed"},
            {"date": f"{current_year}-03-17", "name": "St. Patrick's Day", "strategy": "themed"},
            {"date": f"{current_year}-07-04", "name": "Independence Day", "strategy": "avoid"},
            {"date": f"{current_year}-10-31", "name": "Halloween", "strategy": "themed"},
            {"date": f"{current_year}-11-11", "name": "Veterans Day", "strategy": "special"},
            {"date": f"{current_year}-12-25", "name": "Christmas", "strategy": "avoid"},
            {"date": f"{current_year}-12-31", "name": "New Year's Eve", "strategy": "special"}
        ]

    def get_optimal_publish_time(
        self,
        date: datetime,
        niche: Optional[str] = None,
        audience_timezone: str = "UTC"
    ) -> datetime:
        """Get optimal publishing time for a date.

        Args:
            date: Target date
            niche: Content niche
            audience_timezone: Primary audience timezone

        Returns:
            Optimal publishing datetime
        """
        # Default optimal times by day of week (in local timezone)
        optimal_times = {
            0: [9, 17],      # Monday
            1: [10, 19],     # Tuesday
            2: [9, 18],      # Wednesday
            3: [10, 20],     # Thursday
            4: [9, 17],      # Friday
            5: [11, 15],     # Saturday
            6: [12, 20]      # Sunday
        }

        # Niche-specific adjustments
        niche_adjustments = {
            "gaming": 2,      # Later in the day
            "education": -1,  # Earlier in the day
            "entertainment": 1,  # Slightly later
            "business": -2,   # Much earlier
            "lifestyle": 0    # No adjustment
        }

        day_of_week = date.weekday()
        base_hours = optimal_times.get(day_of_week, [9, 17])

        # Apply niche adjustment
        adjustment = niche_adjustments.get(niche, 0)
        adjusted_hours = [h + adjustment for h in base_hours]

        # Pick the first available slot
        optimal_hour = adjusted_hours[0] if datetime.now().hour < adjusted_hours[0] else adjusted_hours[-1]

        # Create datetime with optimal time
        optimal_dt = date.replace(
            hour=optimal_hour % 24,
            minute=0,
            second=0,
            microsecond=0
        )

        return optimal_dt

    def schedule_content(
        self,
        slug: str,
        publish_date: Optional[datetime] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Schedule content for publishing.

        Args:
            slug: Content slug
            publish_date: Specific publish date/time
            template: Scheduling template to use
            metadata: Content metadata

        Returns:
            Scheduling confirmation
        """
        # Use template if provided
        if template and template in self.templates:
            template_config = self.templates[template]
            if not publish_date:
                # Calculate next available slot based on template
                publish_date = self._get_next_template_slot(template_config)

        # Use optimal time if no date provided
        if not publish_date:
            publish_date = self.get_optimal_publish_time(
                datetime.now(timezone.utc) + timedelta(days=1),
                niche=metadata.get("niche") if metadata else None
            )

        # Check for conflicts
        conflicts = self._check_scheduling_conflicts(publish_date)
        if conflicts:
            logger.warning(f"Scheduling conflict detected: {conflicts}")
            # Find next available slot
            publish_date = self._find_next_available_slot(publish_date)

        # Add to calendar
        scheduled_item = {
            "slug": slug,
            "scheduled_time": publish_date.isoformat(),
            "status": "scheduled",
            "template": template,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        self.calendar["scheduled"].append(scheduled_item)
        self._save_calendar()

        logger.info(f"Scheduled {slug} for {publish_date}")

        return {
            "slug": slug,
            "scheduled_time": publish_date,
            "conflicts_resolved": len(conflicts) > 0,
            "status": "scheduled"
        }

    def _get_next_template_slot(self, template: Dict[str, Any]) -> datetime:
        """Get next available slot based on template.

        Args:
            template: Template configuration

        Returns:
            Next available datetime
        """
        now = datetime.now(timezone.utc)
        frequency = template.get("frequency")

        if frequency == "daily":
            times = template.get("times", ["09:00"])
            # Find next available time today or tomorrow
            for time_str in times:
                hour, minute = map(int, time_str.split(":"))
                slot = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if slot > now:
                    return slot
            # All times passed today, use first time tomorrow
            hour, minute = map(int, times[0].split(":"))
            return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)

        elif frequency == "weekday":
            days = template.get("days", ["monday"])
            time_str = template.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))

            # Find next matching weekday
            days_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2,
                "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
            }

            for i in range(7):
                check_date = now + timedelta(days=i)
                day_name = list(days_map.keys())[check_date.weekday()]
                if day_name in days:
                    slot = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if slot > now:
                        return slot

        return now + timedelta(days=1)  # Default to tomorrow

    def _check_scheduling_conflicts(self, publish_date: datetime) -> List[Dict[str, Any]]:
        """Check for scheduling conflicts.

        Args:
            publish_date: Proposed publish date

        Returns:
            List of conflicts
        """
        conflicts = []

        # Check for same-day posts (within 4 hours)
        for item in self.calendar.get("scheduled", []):
            scheduled_time = datetime.fromisoformat(item["scheduled_time"])
            time_diff = abs((scheduled_time - publish_date).total_seconds())
            if time_diff < 4 * 3600:  # Within 4 hours
                conflicts.append({
                    "type": "time_proximity",
                    "item": item["slug"],
                    "scheduled_time": scheduled_time
                })

        # Check for holiday conflicts
        date_str = publish_date.strftime("%Y-%m-%d")
        for holiday in self.calendar.get("holidays", []):
            if holiday["date"] == date_str and holiday.get("strategy") == "avoid":
                conflicts.append({
                    "type": "holiday",
                    "name": holiday["name"],
                    "strategy": holiday["strategy"]
                })

        return conflicts

    def _find_next_available_slot(
        self,
        start_date: datetime,
        max_days: int = 7
    ) -> datetime:
        """Find next available publishing slot.

        Args:
            start_date: Starting date to search from
            max_days: Maximum days to search ahead

        Returns:
            Next available datetime
        """
        current_date = start_date

        for _ in range(max_days * 4):  # Check 4 slots per day
            conflicts = self._check_scheduling_conflicts(current_date)
            if not conflicts:
                return current_date

            # Try next slot (6 hours later)
            current_date += timedelta(hours=6)

        # If no slot found, return original date + max_days
        return start_date + timedelta(days=max_days)

    def get_upcoming_schedule(
        self,
        days_ahead: int = 7,
        include_published: bool = False
    ) -> List[Dict[str, Any]]:
        """Get upcoming scheduled content.

        Args:
            days_ahead: Days to look ahead
            include_published: Include recently published content

        Returns:
            List of scheduled items
        """
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        upcoming = []

        # Get scheduled items
        for item in self.calendar.get("scheduled", []):
            scheduled_time = datetime.fromisoformat(item["scheduled_time"])
            if datetime.now(timezone.utc) <= scheduled_time <= cutoff_date:
                upcoming.append(item)

        # Include recently published if requested
        if include_published:
            cutoff_past = datetime.now(timezone.utc) - timedelta(days=7)
            for item in self.calendar.get("published", []):
                published_time = datetime.fromisoformat(item.get("published_time", item.get("scheduled_time")))
                if cutoff_past <= published_time <= datetime.now(timezone.utc):
                    upcoming.append(item)

        # Sort by time
        upcoming.sort(key=lambda x: x.get("scheduled_time", x.get("published_time")))

        return upcoming

    def mark_as_published(
        self,
        slug: str,
        video_id: Optional[str] = None,
        url: Optional[str] = None,
        analytics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark scheduled content as published.

        Args:
            slug: Content slug
            video_id: Platform video ID
            url: Published URL
            analytics: Initial analytics data

        Returns:
            Success status
        """
        # Find in scheduled items
        scheduled_items = self.calendar.get("scheduled", [])
        published_item = None

        for i, item in enumerate(scheduled_items):
            if item["slug"] == slug:
                published_item = item
                scheduled_items.pop(i)
                break

        if not published_item:
            logger.warning(f"Scheduled item not found: {slug}")
            return False

        # Update item
        published_item.update({
            "status": "published",
            "published_time": datetime.now(timezone.utc).isoformat(),
            "video_id": video_id,
            "url": url,
            "analytics": analytics or {}
        })

        # Move to published
        self.calendar["published"].append(published_item)
        self._save_calendar()

        logger.info(f"Marked {slug} as published")
        return True

    def analyze_publishing_patterns(self) -> Dict[str, Any]:
        """Analyze publishing patterns and performance.

        Returns:
            Analytics insights
        """
        published = self.calendar.get("published", [])

        if not published:
            return {"status": "no_data"}

        # Analyze by day of week
        day_performance = {i: [] for i in range(7)}
        hour_performance = {i: [] for i in range(24)}

        for item in published:
            published_time = datetime.fromisoformat(item.get("published_time", item["scheduled_time"]))
            analytics = item.get("analytics", {})

            # Get performance metric (views in first 24h)
            performance = analytics.get("views_24h", 0)

            day_performance[published_time.weekday()].append(performance)
            hour_performance[published_time.hour].append(performance)

        # Calculate averages
        best_days = []
        for day, performances in day_performance.items():
            if performances:
                avg = sum(performances) / len(performances)
                best_days.append((day, avg))

        best_days.sort(key=lambda x: x[1], reverse=True)

        best_hours = []
        for hour, performances in hour_performance.items():
            if performances:
                avg = sum(performances) / len(performances)
                best_hours.append((hour, avg))

        best_hours.sort(key=lambda x: x[1], reverse=True)

        return {
            "total_published": len(published),
            "best_days": best_days[:3],
            "best_hours": best_hours[:3],
            "average_views_24h": sum(item.get("analytics", {}).get("views_24h", 0) for item in published) / len(published) if published else 0,
            "recommendations": self._generate_schedule_recommendations(best_days, best_hours)
        }

    def _generate_schedule_recommendations(
        self,
        best_days: List[Tuple[int, float]],
        best_hours: List[Tuple[int, float]]
    ) -> List[str]:
        """Generate scheduling recommendations.

        Args:
            best_days: Best performing days
            best_hours: Best performing hours

        Returns:
            List of recommendations
        """
        recommendations = []

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        if best_days:
            top_days = [day_names[d] for d, _ in best_days[:2]]
            recommendations.append(f"Focus publishing on {' and '.join(top_days)}")

        if best_hours:
            top_hours = [f"{h}:00" for h, _ in best_hours[:2]]
            recommendations.append(f"Optimal posting times: {' and '.join(top_hours)} UTC")

        # Check for consistency
        published = self.calendar.get("published", [])
        if len(published) > 10:
            # Calculate posting frequency
            dates = [datetime.fromisoformat(item.get("published_time", item["scheduled_time"])) for item in published[-10:]]
            dates.sort()

            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0

            if avg_gap > 3:
                recommendations.append("Consider more frequent posting (current avg gap: {:.1f} days)".format(avg_gap))
            elif avg_gap < 1:
                recommendations.append("Space out posts more to avoid audience fatigue")

        return recommendations

    async def execute_scheduled_uploads(self) -> Dict[str, Any]:
        """Execute scheduled uploads that are due.

        Returns:
            Execution summary
        """
        now = datetime.now(timezone.utc)
        executed = []
        failed = []

        for item in self.calendar.get("scheduled", []):
            scheduled_time = datetime.fromisoformat(item["scheduled_time"])

            if scheduled_time <= now:
                slug = item["slug"]
                content_dir = self.config.directories.content_dir / slug

                if not content_dir.exists():
                    logger.error(f"Content directory not found for scheduled upload: {slug}")
                    failed.append(slug)
                    continue

                # Trigger upload via webhook
                if self.config.webhooks.get("scheduled_upload_url"):
                    try:
                        response = await self.n8n_client.execute_webhook(
                            self.config.webhooks.scheduled_upload_url,
                            {
                                "slug": slug,
                                "scheduled_time": item["scheduled_time"],
                                "metadata": item.get("metadata", {})
                            },
                            timeout=60
                        )

                        if response.get("success"):
                            self.mark_as_published(
                                slug,
                                video_id=response.get("video_id"),
                                url=response.get("url")
                            )
                            executed.append(slug)
                        else:
                            failed.append(slug)

                    except Exception as e:
                        logger.error(f"Failed to execute scheduled upload for {slug}: {e}")
                        failed.append(slug)
                else:
                    logger.warning("Scheduled upload webhook not configured")

        return {
            "executed": executed,
            "failed": failed,
            "timestamp": now.isoformat()
        }


async def schedule_content(
    config: AppConfig,
    slug: str,
    publish_date: Optional[datetime] = None,
    template: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Schedule content for publishing.

    Args:
        config: Application configuration
        slug: Content slug
        publish_date: Specific publish date
        template: Scheduling template
        dry_run: Simulate without scheduling

    Returns:
        Scheduling result
    """
    if not config.features.get("content_calendar"):
        logger.info("Content calendar feature is disabled")
        return {"status": "disabled"}

    calendar = ContentCalendar(config)

    # Load metadata
    content_dir = config.directories.content_dir / slug
    metadata_path = content_dir / "metadata.json"

    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

    if dry_run:
        # Simulate scheduling
        if not publish_date:
            publish_date = calendar.get_optimal_publish_time(
                datetime.now(timezone.utc) + timedelta(days=1),
                niche=metadata.get("niche")
            )

        return {
            "status": "dry_run",
            "would_schedule": {
                "slug": slug,
                "publish_date": publish_date.isoformat(),
                "template": template
            }
        }

    # Actually schedule
    result = calendar.schedule_content(
        slug,
        publish_date=publish_date,
        template=template,
        metadata=metadata
    )

    return result


def get_publishing_schedule(
    config: AppConfig,
    days_ahead: int = 7,
    analyze: bool = False
) -> Dict[str, Any]:
    """Get upcoming publishing schedule.

    Args:
        config: Application configuration
        days_ahead: Days to look ahead
        analyze: Include analytics

    Returns:
        Schedule and optional analytics
    """
    calendar = ContentCalendar(config)

    result = {
        "upcoming": calendar.get_upcoming_schedule(days_ahead),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if analyze:
        result["analytics"] = calendar.analyze_publishing_patterns()

    return result