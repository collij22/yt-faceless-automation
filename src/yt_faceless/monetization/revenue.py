"""Revenue tracking and reporting system."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import AppConfig
from ..core.schemas import RevenueEvent, RevenueReport, RevenueSource
from ..logging_setup import get_logger

logger = get_logger(__name__)


class RevenueTracker:
    """Track and analyze revenue from all sources."""

    def __init__(self, config: AppConfig):
        """Initialize revenue tracker.

        Args:
            config: Application configuration
        """
        self.config = config
        self.data_dir = config.directories.data_dir / "revenue"
        self.events_dir = self.data_dir / "events"
        self.reports_dir = self.data_dir / "reports"

        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def record_event(self, event: RevenueEvent) -> None:
        """Record a revenue event.

        Args:
            event: Revenue event to record
        """
        # Create event file path (grouped by month)
        event_date = datetime.fromisoformat(event.timestamp_iso.replace('Z', '+00:00'))
        month_dir = self.events_dir / event_date.strftime("%Y-%m")
        month_dir.mkdir(exist_ok=True)

        event_file = month_dir / f"{event.video_slug}_{event.source.value}.json"

        # Load existing events or create new list
        if event_file.exists():
            with open(event_file, 'r') as f:
                events = json.load(f)
        else:
            events = []

        # Append new event
        events.append(event.dict())

        # Save updated events
        with open(event_file, 'w') as f:
            json.dump(events, f, indent=2)

        logger.info(f"Recorded revenue event: {event.source} - ${event.amount_usd:.2f}")

    def get_events_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        source: Optional[RevenueSource] = None
    ) -> List[RevenueEvent]:
        """Get revenue events for a time period.

        Args:
            start_date: Start of period
            end_date: End of period
            source: Optional filter by source

        Returns:
            List of revenue events
        """
        events = []

        # Iterate through month directories
        for month_dir in self.events_dir.iterdir():
            if not month_dir.is_dir():
                continue

            month = datetime.strptime(month_dir.name, "%Y-%m")
            if month.year < start_date.year or month.year > end_date.year:
                continue
            if month.year == start_date.year and month.month < start_date.month:
                continue
            if month.year == end_date.year and month.month > end_date.month:
                continue

            # Load events from this month
            for event_file in month_dir.glob("*.json"):
                with open(event_file, 'r') as f:
                    file_events = json.load(f)

                for event_data in file_events:
                    event = RevenueEvent(**event_data)

                    # Filter by date
                    event_date = datetime.fromisoformat(
                        event.timestamp_iso.replace('Z', '+00:00')
                    )
                    if not (start_date <= event_date <= end_date):
                        continue

                    # Filter by source if specified
                    if source and event.source != source:
                        continue

                    events.append(event)

        return sorted(events, key=lambda e: e.timestamp_iso)

    def calculate_rpm(
        self,
        revenue: float,
        views: int
    ) -> float:
        """Calculate Revenue Per Mille (RPM).

        Args:
            revenue: Total revenue
            views: Total views

        Returns:
            RPM value
        """
        if views == 0:
            return 0.0
        return (revenue / views) * 1000

    def generate_monthly_report(
        self,
        year: int,
        month: int
    ) -> RevenueReport:
        """Generate monthly revenue report.

        Args:
            year: Report year
            month: Report month (1-12)

        Returns:
            Revenue report
        """
        # Get events for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

        events = self.get_events_for_period(start_date, end_date)

        # Aggregate by source
        revenue_by_source = defaultdict(float)
        revenue_by_video = defaultdict(float)

        for event in events:
            revenue_by_source[event.source.value] += event.amount_usd
            revenue_by_video[event.video_slug] += event.amount_usd

        # Calculate totals
        total_revenue = sum(revenue_by_source.values())

        # Get top performers
        top_videos = sorted(
            revenue_by_video.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        top_performers = [
            {"slug": slug, "revenue": revenue}
            for slug, revenue in top_videos
        ]

        # Calculate RPM (would need view data from analytics)
        # For now, using placeholder
        rpm_average = 5.0
        rpm_delta_pct = 15.0

        # Generate insights
        insights = []
        if revenue_by_source.get("affiliate", 0) > revenue_by_source.get("youtube", 0) * 0.3:
            insights.append("Affiliate revenue performing strongly (>30% of AdSense)")
        if revenue_by_source.get("sponsor", 0) > 0:
            insights.append(f"Sponsorship deals contributed ${revenue_by_source['sponsor']:.2f}")
        if len(top_performers) > 0:
            insights.append(f"Top video generated ${top_performers[0]['revenue']:.2f}")

        # Generate recommendations
        recommendations = []
        if rpm_average < 4:
            recommendations.append("Consider higher-RPM niches or improve CTR")
        if revenue_by_source.get("affiliate", 0) < total_revenue * 0.2:
            recommendations.append("Increase affiliate link placements")
        if not revenue_by_source.get("sponsor", 0):
            recommendations.append("Explore sponsorship opportunities")

        report = RevenueReport(
            month=f"{year:04d}-{month:02d}",
            total_revenue_usd=total_revenue,
            revenue_by_source=dict(revenue_by_source),
            top_performers=top_performers,
            rpm_average=rpm_average,
            rpm_delta_pct=rpm_delta_pct,
            insights=insights,
            recommendations=recommendations
        )

        # Save report
        report_file = self.reports_dir / f"revenue_{year:04d}_{month:02d}.json"
        with open(report_file, 'w') as f:
            json.dump(report.dict(), f, indent=2)

        # Generate markdown report
        self._generate_markdown_report(report)

        return report

    def _generate_markdown_report(self, report: RevenueReport) -> None:
        """Generate markdown version of revenue report.

        Args:
            report: Revenue report
        """
        md_lines = [
            f"# Revenue Report - {report.month}",
            "",
            "## Summary",
            f"- **Total Revenue**: ${report.total_revenue_usd:,.2f}",
            f"- **Average RPM**: ${report.rpm_average:.2f} ({report.rpm_delta_pct:+.1f}%)",
            "",
            "## Revenue Breakdown",
            ""
        ]

        # Add source breakdown
        for source, amount in report.revenue_by_source.items():
            percentage = (amount / report.total_revenue_usd) * 100
            md_lines.append(f"- **{source.title()}**: ${amount:,.2f} ({percentage:.1f}%)")

        md_lines.extend([
            "",
            "## Top Performing Videos",
            ""
        ])

        # Add top performers
        for i, video in enumerate(report.top_performers, 1):
            md_lines.append(f"{i}. `{video['slug']}`: ${video['revenue']:.2f}")

        # Add insights
        if report.insights:
            md_lines.extend([
                "",
                "## Key Insights",
                ""
            ])
            for insight in report.insights:
                md_lines.append(f"- {insight}")

        # Add recommendations
        if report.recommendations:
            md_lines.extend([
                "",
                "## Recommendations",
                ""
            ])
            for rec in report.recommendations:
                md_lines.append(f"- {rec}")

        md_lines.extend([
            "",
            "---",
            f"*Generated: {datetime.now().isoformat()}*"
        ])

        # Save markdown report
        md_file = self.reports_dir / f"revenue_{report.month}.md"
        md_file.write_text("\n".join(md_lines))


def generate_revenue_report(
    config: AppConfig,
    month: Optional[str] = None,
    output_json: bool = False
) -> Dict[str, Any]:
    """Generate revenue report for specified month.

    Args:
        config: Application configuration
        month: Month in YYYY-MM format (default: current month)
        output_json: Whether to output JSON format

    Returns:
        Report data
    """
    tracker = RevenueTracker(config)

    # Parse month or use current
    if month:
        year, month_num = map(int, month.split('-'))
    else:
        now = datetime.now()
        year, month_num = now.year, now.month

    # Generate report
    report = tracker.generate_monthly_report(year, month_num)

    logger.info(f"Generated revenue report for {year:04d}-{month_num:02d}")

    if output_json:
        return report.dict()
    else:
        # Return summary
        return {
            "month": report.month,
            "total_revenue": f"${report.total_revenue_usd:,.2f}",
            "rpm": f"${report.rpm_average:.2f}",
            "top_video": report.top_performers[0] if report.top_performers else None,
            "report_path": str(tracker.reports_dir / f"revenue_{report.month}.md")
        }