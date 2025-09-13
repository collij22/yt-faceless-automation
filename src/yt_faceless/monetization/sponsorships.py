"""Sponsorship management and disclosure automation."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import AppConfig
from ..core.schemas import SponsorDeal
from ..logging_setup import get_logger

logger = get_logger(__name__)


class SponsorshipManager:
    """Manages sponsorship deals and disclosures."""

    def __init__(self, config: AppConfig):
        """Initialize sponsorship manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.data_dir = config.directories.data_dir / "sponsors"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.deals_file = self.data_dir / "deals.json"
        self.deals = self._load_deals()

    def _load_deals(self) -> List[SponsorDeal]:
        """Load sponsorship deals from data file."""
        if not self.deals_file.exists():
            # Create default deals file
            default_data = {
                "deals": [
                    {
                        "sponsor": "Example Brand",
                        "flight_start_iso": "2025-01-01T00:00:00Z",
                        "flight_end_iso": "2025-12-31T23:59:59Z",
                        "deliverables": ["preroll_15s", "desc_link", "lower_third"],
                        "cta_text": "Check out Example Brand for amazing products!",
                        "landing_url": "https://example.com/youtube",
                        "disclosure_text": "This video contains paid promotion",
                        "placement": ["description", "preroll", "lower_third"],
                        "payment_amount_usd": 1000,
                        "contract_id": "EXAMPLE-001"
                    }
                ]
            }
            self.deals_file.write_text(json.dumps(default_data, indent=2))
            logger.info(f"Created default deals file at {self.deals_file}")

        with open(self.deals_file, 'r') as f:
            data = json.load(f)

        deals = []
        for deal_data in data.get("deals", []):
            deal = SponsorDeal(**deal_data)
            deals.append(deal)

        return deals

    def get_active_deals(
        self,
        slug: Optional[str] = None,
        niche: Optional[str] = None
    ) -> List[SponsorDeal]:
        """Get currently active sponsorship deals.

        Args:
            slug: Video slug for targeting
            niche: Video niche for targeting

        Returns:
            List of active sponsorship deals
        """
        active_deals = []
        # Use timezone-aware datetime for reliable comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)

        for deal in self.deals:
            # Parse ISO strings to datetime objects for proper comparison
            try:
                # Handle both Z and +00:00 timezone formats
                start_str = deal.flight_start_iso.replace('Z', '+00:00')
                end_str = deal.flight_end_iso.replace('Z', '+00:00')

                deal_start = datetime.fromisoformat(start_str)
                deal_end = datetime.fromisoformat(end_str)

                # Convert to UTC if not already
                if deal_start.tzinfo is None:
                    deal_start = deal_start.replace(tzinfo=timezone.utc)
                if deal_end.tzinfo is None:
                    deal_end = deal_end.replace(tzinfo=timezone.utc)

                # Check if deal is active
                if deal_start <= now <= deal_end:
                    # TODO: Add more sophisticated targeting based on slug/niche
                    active_deals.append(deal)
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid date format for sponsor deal {deal.sponsor}: {e}")
                continue

        return active_deals

    def generate_disclosure_text(
        self,
        deals: List[SponsorDeal],
        template: Optional[str] = None
    ) -> str:
        """Generate FTC-compliant disclosure text.

        Args:
            deals: List of sponsorship deals
            template: Optional disclosure template

        Returns:
            Formatted disclosure text
        """
        if not deals:
            return ""

        # Use template from environment or default
        if template is None:
            template = os.getenv(
                "SPONSORSHIP_DISCLOSURE_TEMPLATE",
                "Includes paid promotion by {sponsor}."
            )

        # If multiple sponsors, list them
        if len(deals) > 1:
            sponsors = ", ".join([d.sponsor for d in deals[:-1]])
            sponsors += f" and {deals[-1].sponsor}"
        else:
            sponsors = deals[0].sponsor

        disclosure = template.format(sponsor=sponsors)

        # Add any deal-specific disclosures
        for deal in deals:
            if deal.disclosure_text and deal.disclosure_text != disclosure:
                disclosure += f" {deal.disclosure_text}"

        return disclosure

    def inject_into_description(
        self,
        description: str,
        deals: List[SponsorDeal],
        disclosure: str
    ) -> str:
        """Inject sponsorship information into description.

        Args:
            description: Original video description
            deals: List of sponsorship deals
            disclosure: Disclosure text

        Returns:
            Description with sponsorship information
        """
        if not deals:
            return description

        # Build sponsorship section
        sponsor_section = [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🤝 TODAY'S SPONSOR:",
            ""
        ]

        for deal in deals:
            sponsor_section.append(f"▸ {deal.sponsor}")
            sponsor_section.append(f"  {deal.cta_text}")
            sponsor_section.append(f"  {deal.landing_url}")
            sponsor_section.append("")

        sponsor_section.extend([
            disclosure,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])

        # Insert at the beginning of description
        lines = sponsor_section + description.split('\n')

        return '\n'.join(lines)

    def generate_overlay_markers(
        self,
        deals: List[SponsorDeal],
        video_duration: float
    ) -> List[Dict[str, Any]]:
        """Generate overlay markers for video timeline.

        Args:
            deals: List of sponsorship deals
            video_duration: Total video duration in seconds

        Returns:
            List of overlay marker configurations
        """
        markers = []

        for deal in deals:
            # Pre-roll marker
            if "preroll" in deal.placement:
                markers.append({
                    "type": "sponsorship_preroll",
                    "start_sec": 0,
                    "end_sec": min(15, video_duration * 0.1),
                    "text": f"Sponsored by {deal.sponsor}",
                    "position": "top-left",
                    "style": "subtle"
                })

            # Lower third marker
            if "lower_third" in deal.placement:
                # Show at 20% and 80% of video
                for position in [0.2, 0.8]:
                    start = video_duration * position
                    markers.append({
                        "type": "sponsorship_lower_third",
                        "start_sec": start,
                        "end_sec": start + 5,
                        "text": deal.cta_text,
                        "url": deal.landing_url,
                        "position": "bottom",
                        "style": "animated"
                    })

        return markers

    def validate_compliance(
        self,
        description: str,
        deals: List[SponsorDeal]
    ) -> Dict[str, Any]:
        """Validate FTC compliance for sponsorship disclosure.

        Args:
            description: Video description
            deals: List of sponsorship deals

        Returns:
            Validation result with any issues
        """
        result = {
            "compliant": True,
            "issues": [],
            "warnings": []
        }

        if deals and not any(keyword in description.lower() for keyword in [
            "sponsor", "paid", "promotion", "partner", "ad"
        ]):
            result["compliant"] = False
            result["issues"].append("Missing sponsorship disclosure in description")

        # Check for clear and conspicuous disclosure
        if deals:
            lines = description.split('\n')
            disclosure_found = False
            for i, line in enumerate(lines[:10]):  # Check first 10 lines
                if any(keyword in line.lower() for keyword in ["sponsor", "paid promotion"]):
                    disclosure_found = True
                    break

            if not disclosure_found:
                result["warnings"].append("Disclosure should appear early in description")

        return result


def apply_sponsorship_disclosure(
    config: AppConfig,
    slug: str,
    description: str,
    video_duration: float = 600,
    niche: Optional[str] = None,
    apply_overlay: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Apply sponsorship disclosure to video metadata.

    Args:
        config: Application configuration
        slug: Video slug
        description: Original video description
        video_duration: Video duration in seconds
        niche: Video niche for targeting
        apply_overlay: Whether to generate overlay markers
        dry_run: Simulate without making changes

    Returns:
        Dictionary with updated metadata and markers
    """
    if not config.features.get("sponsorships"):
        logger.info("Sponsorship feature is disabled")
        return {"description": description}

    manager = SponsorshipManager(config)

    # Get active deals
    deals = manager.get_active_deals(slug, niche)

    if not deals:
        logger.info(f"No active sponsorship deals for {slug}")
        return {"description": description}

    result = {}

    # Generate disclosure
    disclosure = manager.generate_disclosure_text(deals)

    if not dry_run:
        # Update description
        result["description"] = manager.inject_into_description(
            description,
            deals,
            disclosure
        )

        # Generate overlay markers if requested
        if apply_overlay:
            result["overlay_markers"] = manager.generate_overlay_markers(
                deals,
                video_duration
            )

        # Add monetization settings
        result["monetization_settings"] = {
            "sponsorship_disclosure": disclosure,
            "enable_ads": True,  # Can still have ads with sponsorships
        }

        # Validate compliance
        validation = manager.validate_compliance(result["description"], deals)
        if not validation["compliant"]:
            logger.warning(f"Compliance issues: {validation['issues']}")

        logger.info(f"Applied {len(deals)} sponsorship disclosures for {slug}")
    else:
        # Dry run - just return what would be done
        result["description"] = description
        result["deals"] = [d.dict() for d in deals]
        result["disclosure"] = disclosure
        result["dry_run"] = True
        logger.info(f"[DRY RUN] Would apply {len(deals)} sponsorship disclosures for {slug}")

    return result