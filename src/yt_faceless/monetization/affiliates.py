"""Affiliate link management system with UTM tracking and shortening."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse, urlunparse

from ..core.config import AppConfig
from ..core.schemas import (
    AffiliateProgram,
    AffiliatePlacement,
    AffiliatePlacementPosition,
)
from ..integrations.n8n_client import N8NClient
from ..logging_setup import get_logger
from ..utils.retry import retry_with_backoff

logger = get_logger(__name__)


class AffiliateManager:
    """Manages affiliate programs and link generation."""

    def __init__(self, config: AppConfig):
        """Initialize affiliate manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.n8n_client = N8NClient(config)
        self.data_dir = config.directories.data_dir / "affiliates"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.programs_file = self.data_dir / "programs.json"
        self.cache_file = self.data_dir / "links_cache.json"

        self.programs = self._load_programs()
        self.cache = self._load_cache()

    def _load_programs(self) -> Dict[str, AffiliateProgram]:
        """Load affiliate programs from data file."""
        if not self.programs_file.exists():
            # Create default programs file
            default_data = {
                "programs": [
                    {
                        "name": "Amazon",
                        "base_url": "https://www.amazon.com/dp/",
                        "utm_defaults": {
                            "utm_source": "youtube",
                            "utm_medium": "description",
                            "utm_campaign": "video"
                        },
                        "shorten": True,
                        "commission_rate": 0.03,
                        "cookie_duration_days": 1
                    }
                ],
                "placements": {
                    "default": [
                        {
                            "program": "Amazon",
                            "description": "As an Amazon Associate I earn from qualifying purchases",
                            "position": "description"
                        }
                    ]
                }
            }
            self.programs_file.write_text(json.dumps(default_data, indent=2))
            logger.info(f"Created default programs file at {self.programs_file}")

        with open(self.programs_file, 'r') as f:
            data = json.load(f)

        programs = {}
        for program_data in data.get("programs", []):
            program = AffiliateProgram(**program_data)
            programs[program.name] = program

        return programs

    def _load_cache(self) -> Dict[str, str]:
        """Load link cache from file."""
        if not self.cache_file.exists():
            return {}

        with open(self.cache_file, 'r') as f:
            return json.load(f)

    def _save_cache(self) -> None:
        """Save link cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def generate_affiliate_url(
        self,
        program_name: str,
        product_id: str,
        utm_overrides: Optional[Dict[str, str]] = None,
        slug: Optional[str] = None
    ) -> str:
        """Generate affiliate URL with UTM parameters.

        Args:
            program_name: Name of affiliate program
            product_id: Product identifier
            utm_overrides: Optional UTM parameter overrides
            slug: Video slug for tracking

        Returns:
            Complete affiliate URL with tracking
        """
        if program_name not in self.programs:
            raise ValueError(f"Unknown affiliate program: {program_name}")

        program = self.programs[program_name]

        # Build base URL
        if program.base_url.endswith('/'):
            url = f"{program.base_url}{product_id}"
        else:
            url = f"{program.base_url}/{product_id}"

        # Build UTM parameters
        utm_params = program.utm_defaults.copy()
        if slug:
            utm_params['utm_content'] = slug
        if utm_overrides:
            utm_params.update(utm_overrides)

        # Add UTM parameters to URL
        parsed = urlparse(url)
        if parsed.query:
            url = f"{url}&{urlencode(utm_params)}"
        else:
            url = f"{url}?{urlencode(utm_params)}"

        return url

    async def shorten_url(self, url: str) -> str:
        """Shorten URL using n8n webhook.

        Args:
            url: Long URL to shorten

        Returns:
            Shortened URL or original if shortening fails
        """
        # Check cache first
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        if url_hash in self.cache:
            return self.cache[url_hash]

        if not self.config.webhooks.shortener_url:
            logger.warning("Shortener webhook not configured, using original URL")
            return url

        try:
            response = await self.n8n_client.execute_webhook(
                self.config.webhooks.shortener_url,
                {
                    "url": url,
                    "custom_alias": url_hash
                }
            )

            short_url = response.get("short_url", url)

            # Cache the result
            self.cache[url_hash] = short_url
            self._save_cache()

            return short_url

        except Exception as e:
            logger.error(f"Failed to shorten URL: {e}")
            return url

    def get_placements_for_slug(
        self,
        slug: str,
        niche: Optional[str] = None
    ) -> List[AffiliatePlacement]:
        """Get affiliate placements for a video slug.

        Args:
            slug: Video slug
            niche: Video niche for targeted placements

        Returns:
            List of affiliate placements
        """
        placements = []

        # Load placement configuration
        with open(self.programs_file, 'r') as f:
            data = json.load(f)

        # Get default placements
        default_placements = data.get("placements", {}).get("default", [])

        # Get niche-specific placements if available
        if niche:
            niche_placements = data.get("placements", {}).get(niche, [])
            default_placements.extend(niche_placements)

        # Convert to AffiliatePlacement objects
        for placement_data in default_placements:
            # Generate URL if not provided but product_id exists
            url = placement_data.get("url", "")
            if not url and placement_data.get("product_id"):
                url = self.generate_affiliate_url(
                    placement_data["program"],
                    placement_data["product_id"],
                    placement_data.get("utm_overrides"),
                    slug
                )

            # Skip placement if no URL could be generated or provided
            if not url:
                logger.warning(
                    f"Skipping placement for {placement_data['program']}: "
                    f"no URL provided and no product_id to generate from"
                )
                continue

            placement = AffiliatePlacement(
                program_name=placement_data["program"],
                url=url,
                description=placement_data["description"],
                position=AffiliatePlacementPosition(placement_data.get("position", "description")),
                utm_overrides=placement_data.get("utm_overrides"),
                priority=placement_data.get("priority", 5),
                tracking_id=placement_data.get("product_id")  # Store product_id for reference
            )
            placements.append(placement)

        # Sort by priority
        placements.sort(key=lambda p: p.priority, reverse=True)

        return placements

    async def inject_into_description(
        self,
        description: str,
        placements: List[AffiliatePlacement],
        disclosure: Optional[str] = None
    ) -> str:
        """Inject affiliate links into video description.

        Args:
            description: Original video description
            placements: List of affiliate placements
            disclosure: Optional disclosure text

        Returns:
            Description with affiliate links injected
        """
        if not placements:
            return description

        # Default disclosure if not provided
        if disclosure is None:
            disclosure = "This video contains affiliate links; we may earn a commission."

        # Build affiliate section
        affiliate_section = [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📦 MENTIONED IN THIS VIDEO:",
            ""
        ]

        for placement in placements[:5]:  # Limit to top 5
            # Skip placements without URLs
            if not placement.url:
                logger.warning(f"Skipping placement '{placement.description}' - no URL available")
                continue

            # Get the program to check if shortening is needed
            program = self.programs.get(placement.program_name)
            if program and program.shorten:
                url = await self.shorten_url(placement.url)
            else:
                url = placement.url

            # Double-check URL is not empty after processing
            if not url:
                logger.warning(f"Skipping placement '{placement.description}' - URL processing failed")
                continue

            affiliate_section.append(f"▸ {placement.description}")
            affiliate_section.append(f"  {url}")
            affiliate_section.append("")

        affiliate_section.extend([
            disclosure,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])

        # Find insertion point (after first paragraph or at start)
        lines = description.split('\n')
        insert_index = 0

        for i, line in enumerate(lines):
            if i > 0 and line.strip() == "":
                insert_index = i
                break

        # Insert affiliate section
        lines[insert_index:insert_index] = affiliate_section

        return '\n'.join(lines)

    async def generate_pinned_comment(
        self,
        placements: List[AffiliatePlacement],
        disclosure: Optional[str] = None
    ) -> str:
        """Generate pinned comment with affiliate links.

        Args:
            placements: List of affiliate placements
            disclosure: Optional disclosure text

        Returns:
            Formatted pinned comment text
        """
        if not placements:
            return ""

        # Default disclosure if not provided
        if disclosure is None:
            disclosure = "Affiliate links below ⬇️"

        comment_lines = [
            "📌 " + disclosure,
            ""
        ]

        for placement in placements[:3]:  # Top 3 for pinned comment
            # Skip placements without URLs
            if not placement.url:
                logger.warning(f"Skipping placement '{placement.description}' in pinned comment - no URL")
                continue

            # Get the program to check if shortening is needed
            program = self.programs.get(placement.program_name)
            if program and program.shorten:
                url = await self.shorten_url(placement.url)
            else:
                url = placement.url

            # Double-check URL is not empty
            if not url:
                logger.warning(f"Skipping placement '{placement.description}' in pinned comment - URL processing failed")
                continue

            comment_lines.append(f"• {placement.description}: {url}")

        return '\n'.join(comment_lines)


async def inject_affiliate_links(
    config: AppConfig,
    slug: str,
    description: str,
    niche: Optional[str] = None,
    pin_comment: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Inject affiliate links into video metadata.

    Args:
        config: Application configuration
        slug: Video slug
        description: Original video description
        niche: Video niche for targeted placements
        pin_comment: Whether to generate pinned comment
        dry_run: Simulate without making changes

    Returns:
        Dictionary with updated description and optional pinned comment
    """
    if not config.features.get("affiliate_injection"):
        logger.info("Affiliate injection feature is disabled")
        return {"description": description}

    manager = AffiliateManager(config)

    # Get placements for this video
    placements = manager.get_placements_for_slug(slug, niche)

    if not placements:
        logger.info(f"No affiliate placements configured for {slug}")
        return {"description": description}

    result = {}

    # Get disclosure from environment
    import os
    disclosure = os.getenv("AFFILIATE_DEFAULT_DISCLOSURE")

    if not dry_run:
        # Inject into description
        result["description"] = await manager.inject_into_description(
            description,
            placements,
            disclosure
        )

        # Generate pinned comment if requested
        if pin_comment:
            result["pinned_comment"] = await manager.generate_pinned_comment(
                placements,
                disclosure
            )

        # Return structured affiliate links for monetization settings
        affiliate_links = []
        for placement in placements:
            if placement.url:
                # Shorten URL if needed
                program = manager.programs.get(placement.program_name)
                url = placement.url
                if program and program.shorten:
                    url = await manager.shorten_url(url)

                # Final check that URL is not empty after processing
                if url:
                    affiliate_links.append({
                        "program": placement.program_name,
                        "description": placement.description,
                        "url": url,
                        "position": placement.position.value if placement.position else "description"
                    })

        result["affiliate_links"] = affiliate_links
        logger.info(f"Injected {len(placements)} affiliate links for {slug}")
    else:
        # Dry run - just return what would be done
        result["description"] = description
        result["placements"] = [p.dict() for p in placements]
        result["dry_run"] = True
        logger.info(f"[DRY RUN] Would inject {len(placements)} affiliate links for {slug}")

    return result