"""Openverse API client for free Creative Commons images."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .base import AssetSearchResult, AssetSource

logger = logging.getLogger(__name__)


class OpenverseSource(AssetSource):
    """Openverse API client for searching Creative Commons images."""

    BASE_URL = "https://api.openverse.engineering/v1"
    RATE_LIMIT = 100  # requests per minute
    REQUEST_DELAY = 0.6  # seconds between requests

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_days: int = 7):
        """Initialize Openverse source."""
        super().__init__(cache_dir, cache_ttl_days)
        self.last_request_time = 0

    def get_source_name(self) -> str:
        """Get the source name for attribution."""
        return "openverse"

    def search(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
        min_width: Optional[int] = 1280
    ) -> List[AssetSearchResult]:
        """Search Openverse for images.

        Args:
            query: Search query
            limit: Maximum results per page (max 20 for Openverse)
            page: Page number (1-indexed)
            min_width: Minimum image width

        Returns:
            List of search results
        """
        # Enforce Openverse limits
        limit = min(limit, 20)

        # Check cache first
        cache_key = self.get_cache_key(query, limit=limit, page=page, min_width=min_width)
        cached = self.get_cached_response(cache_key)
        if cached:
            return self._parse_response(cached)

        # Rate limiting
        self._rate_limit()

        # Build query parameters
        params = {
            "q": query,
            "page_size": limit,
            "page": page,
            "mature": "false",
            # Filter for CC licenses only (excludes copyrighted content)
            "license_type": "commercial,modification",
            # Request additional fields
            "unstable__include_sensitive_results": "false",
        }

        # Add resolution filter if specified
        if min_width:
            params["aspect_ratio"] = "wide"  # Prefer landscape images for video
            # Note: Openverse doesn't have direct width filter, using aspect ratio as proxy

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Make API request
                url = f"{self.BASE_URL}/images/?{urlencode(params)}"
                request = Request(url)
                request.add_header("User-Agent", "YT-Faceless-Automation/1.0")

                logger.debug(f"Searching Openverse: {query} (page {page}, attempt {attempt + 1}/{max_retries})")

                with urlopen(request, timeout=30) as response:
                    if response.status == 200:
                        import json
                        data = json.loads(response.read().decode("utf-8"))

                        # Cache successful response
                        self.save_cache_response(cache_key, data)

                        # Parse and filter results
                        results = self._parse_response(data)
                        results = self.filter_by_license(results)
                        if min_width:
                            results = self.filter_by_resolution(results, min_width)

                        return results
                    else:
                        logger.warning(f"Openverse API error: HTTP {response.status} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # Retry for non-200 status codes
                            delay = base_delay * (2 ** attempt)
                            logger.debug(f"Retrying in {delay:.1f} seconds...")
                            time.sleep(delay)
                            continue
                        return []

            except (HTTPError, URLError) as e:
                logger.warning(f"Openverse request error: {e} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    logger.debug(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Openverse search failed after {max_retries} attempts: {e}")
                    return []
            except Exception as e:
                logger.error(f"Openverse search failed: {e}")
                return []

        return []

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _parse_response(self, data: Dict[str, Any]) -> List[AssetSearchResult]:
        """Parse Openverse API response.

        Args:
            data: API response data

        Returns:
            List of search results
        """
        results = []

        for item in data.get("results", []):
            try:
                # Extract license info
                license_code = item.get("license", "unknown")
                license_version = item.get("license_version", "")
                license_url = item.get("license_url", "")

                # Format license string
                if license_version:
                    license_full = f"{license_code}-{license_version}"
                else:
                    license_full = license_code

                # Build attribution
                creator = item.get("creator") or item.get("source") or "Unknown"
                title = item.get("title") or "Untitled"
                attribution = self._build_attribution(title, creator, license_full, item.get("url"))

                # Extract tags
                tags = []
                for tag in item.get("tags", []):
                    if isinstance(tag, dict):
                        tags.append(tag.get("name", ""))
                    else:
                        tags.append(str(tag))

                result = AssetSearchResult(
                    url=item.get("url", ""),
                    thumbnail_url=item.get("thumbnail", item.get("url")),
                    title=title,
                    creator=creator,
                    license=license_full,
                    license_url=license_url,
                    source="Openverse",
                    source_url=item.get("foreign_landing_url", item.get("url", "")),
                    width=item.get("width"),
                    height=item.get("height"),
                    tags=[t for t in tags if t],  # Filter empty tags
                    attribution=attribution,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error parsing Openverse item: {e}")
                continue

        logger.info(f"Openverse returned {len(results)} results")
        return results

    def _build_attribution(
        self,
        title: str,
        creator: str,
        license: str,
        url: str
    ) -> str:
        """Build attribution string for an asset.

        Args:
            title: Asset title
            creator: Creator name
            license: License code
            url: Source URL

        Returns:
            Attribution string
        """
        # Follow Creative Commons attribution best practices
        parts = []

        if title and title != "Untitled":
            parts.append(f'"{title}"')

        if creator and creator != "Unknown":
            parts.append(f"by {creator}")

        if license:
            parts.append(f"is licensed under {license.upper()}")

        if url:
            parts.append(f"({url})")

        return " ".join(parts) if parts else "No attribution required"

    def get_image_details(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific image.

        Args:
            image_id: Openverse image ID

        Returns:
            Image details or None if not found
        """
        # Rate limiting
        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/images/{image_id}/"
            request = Request(url)
            request.add_header("User-Agent", "YT-Faceless-Automation/1.0")

            with urlopen(request, timeout=30) as response:
                if response.status == 200:
                    import json
                    return json.loads(response.read().decode("utf-8"))
                else:
                    logger.error(f"Failed to get image {image_id}: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching image details: {e}")
            return None