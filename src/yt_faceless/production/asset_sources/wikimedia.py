"""Wikimedia Commons API client for free public domain and CC images."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .base import AssetSearchResult, AssetSource

logger = logging.getLogger(__name__)


class WikimediaSource(AssetSource):
    """Wikimedia Commons API client for searching free images."""

    BASE_URL = "https://commons.wikimedia.org/w/api.php"
    RATE_LIMIT = 200  # requests per minute (Wikimedia is more generous)
    REQUEST_DELAY = 0.3  # seconds between requests

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_days: int = 7):
        """Initialize Wikimedia source."""
        super().__init__(cache_dir, cache_ttl_days)
        self.last_request_time = 0

    def get_source_name(self) -> str:
        """Get the source name for attribution."""
        return "wikimedia"

    def search(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
        min_width: Optional[int] = 1280
    ) -> List[AssetSearchResult]:
        """Search Wikimedia Commons for images.

        Args:
            query: Search query
            limit: Maximum results per page
            page: Page number (1-indexed)
            min_width: Minimum image width

        Returns:
            List of search results
        """
        # Check cache first
        cache_key = self.get_cache_key(query, limit=limit, page=page, min_width=min_width)
        cached = self.get_cached_response(cache_key)
        if cached:
            return self._parse_response(cached)

        # Rate limiting
        self._rate_limit()

        # Calculate offset for pagination
        offset = (page - 1) * limit

        # Build query parameters for image search
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",  # Search only image files
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": min(limit, 50),  # Wikimedia max is 50
            "gsroffset": offset,
            "prop": "imageinfo|categories",
            "iiprop": "url|size|extmetadata|mime",
            "iiextmetadatafilter": "License|LicenseShortName|UsageTerms|Attribution|Artist|Credit|ImageDescription",
            "iiurlwidth": 1920,  # Request scaled URL
        }

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Make API request
                url = f"{self.BASE_URL}?{urlencode(params)}"
                request = Request(url)
                request.add_header("User-Agent", "YT-Faceless-Automation/1.0 (https://github.com/yt-faceless)")

                logger.debug(f"Searching Wikimedia: {query} (page {page}, attempt {attempt + 1}/{max_retries})")

                with urlopen(request, timeout=30) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))

                        # Check for query continuation (pagination)
                        if "continue" in data:
                            data["has_more"] = True

                        # Cache successful response
                        self.save_cache_response(cache_key, data)

                        # Parse and filter results
                        results = self._parse_response(data)
                        results = self.filter_by_license(results)
                        if min_width:
                            results = self.filter_by_resolution(results, min_width)

                        return results
                    else:
                        logger.warning(f"Wikimedia API error: HTTP {response.status} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # Retry for non-200 status codes
                            delay = base_delay * (2 ** attempt)
                            logger.debug(f"Retrying in {delay:.1f} seconds...")
                            time.sleep(delay)
                            continue
                        return []

            except (HTTPError, URLError) as e:
                logger.warning(f"Wikimedia request error: {e} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    logger.debug(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Wikimedia search failed after {max_retries} attempts: {e}")
                    return []
            except Exception as e:
                logger.error(f"Wikimedia search failed: {e}")
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
        """Parse Wikimedia API response.

        Args:
            data: API response data

        Returns:
            List of search results
        """
        results = []

        # Extract pages from query response
        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            try:
                # Skip if no imageinfo
                if "imageinfo" not in page_data or not page_data["imageinfo"]:
                    continue

                info = page_data["imageinfo"][0]
                metadata = info.get("extmetadata", {})

                # Extract license information
                license_info = self._extract_license(metadata)
                if not license_info["license"]:
                    logger.debug(f"Skipping {page_data.get('title')} - no license info")
                    continue

                # Extract creator/artist
                creator = self._extract_creator(metadata)

                # Extract description
                description = self._extract_description(metadata)

                # Build title from filename
                title = page_data.get("title", "").replace("File:", "").replace("_", " ")
                if title.endswith((".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp")):
                    title = title.rsplit(".", 1)[0]

                # Extract tags from categories
                tags = self._extract_tags(page_data.get("categories", []))

                # Build attribution
                attribution = self._build_attribution(
                    title,
                    creator,
                    license_info["license"],
                    info.get("descriptionurl", "")
                )

                # Get image URLs
                image_url = info.get("url", "")
                thumb_url = info.get("thumburl", info.get("url", ""))

                result = AssetSearchResult(
                    url=image_url,
                    thumbnail_url=thumb_url,
                    title=title or description[:100],
                    creator=creator,
                    license=license_info["license"],
                    license_url=license_info["license_url"],
                    source="Wikimedia Commons",
                    source_url=info.get("descriptionurl", ""),
                    width=info.get("width"),
                    height=info.get("height"),
                    tags=tags,
                    attribution=attribution,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error parsing Wikimedia item: {e}")
                continue

        logger.info(f"Wikimedia returned {len(results)} results")
        return results

    def _extract_license(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract license information from metadata.

        Args:
            metadata: Wikimedia extmetadata

        Returns:
            Dict with license and license_url
        """
        license_info = {"license": "", "license_url": ""}

        # Try different license fields
        license_fields = ["LicenseShortName", "License", "UsageTerms"]

        for field in license_fields:
            if field in metadata and metadata[field].get("value"):
                license_raw = metadata[field]["value"]

                # Clean up license string
                license_clean = self._clean_html(license_raw).lower()

                # Map to standard license codes
                if "cc0" in license_clean or "public domain" in license_clean:
                    license_info["license"] = "cc0"
                    license_info["license_url"] = "https://creativecommons.org/publicdomain/zero/1.0/"
                elif "cc-by-sa" in license_clean or "cc by-sa" in license_clean:
                    # Extract version number if present
                    import re
                    version_match = re.search(r"(\d+\.\d+)", license_clean)
                    version = version_match.group(1) if version_match else "4.0"
                    license_info["license"] = f"cc-by-sa-{version}"
                    license_info["license_url"] = f"https://creativecommons.org/licenses/by-sa/{version}/"
                elif "cc-by" in license_clean or "cc by" in license_clean:
                    import re
                    version_match = re.search(r"(\d+\.\d+)", license_clean)
                    version = version_match.group(1) if version_match else "4.0"
                    license_info["license"] = f"cc-by-{version}"
                    license_info["license_url"] = f"https://creativecommons.org/licenses/by/{version}/"
                elif "pd" in license_clean or "no known copyright" in license_clean:
                    license_info["license"] = "pd"
                    license_info["license_url"] = "https://creativecommons.org/publicdomain/mark/1.0/"
                else:
                    # Use as-is if we can't map it
                    license_info["license"] = license_clean[:50]

                break

        return license_info

    def _extract_creator(self, metadata: Dict[str, Any]) -> str:
        """Extract creator/artist from metadata.

        Args:
            metadata: Wikimedia extmetadata

        Returns:
            Creator name or 'Unknown'
        """
        # Try different creator fields
        creator_fields = ["Artist", "Author", "Credit", "Attribution"]

        for field in creator_fields:
            if field in metadata and metadata[field].get("value"):
                creator_raw = metadata[field]["value"]
                creator_clean = self._clean_html(creator_raw)
                if creator_clean:
                    return creator_clean[:100]  # Limit length

        return "Unknown"

    def _extract_description(self, metadata: Dict[str, Any]) -> str:
        """Extract description from metadata.

        Args:
            metadata: Wikimedia extmetadata

        Returns:
            Description text
        """
        desc_fields = ["ImageDescription", "ObjectName"]

        for field in desc_fields:
            if field in metadata and metadata[field].get("value"):
                desc_raw = metadata[field]["value"]
                desc_clean = self._clean_html(desc_raw)
                if desc_clean:
                    return desc_clean[:500]  # Limit length

        return ""

    def _extract_tags(self, categories: List[Dict[str, Any]]) -> List[str]:
        """Extract tags from categories.

        Args:
            categories: List of category objects

        Returns:
            List of tag strings
        """
        tags = []

        for cat in categories:
            if "title" in cat:
                # Remove "Category:" prefix and clean
                tag = cat["title"].replace("Category:", "").replace("_", " ").strip()

                # Filter out meta categories
                skip_patterns = [
                    "commons", "media", "files", "pages", "uploaded",
                    "license", "copyright", "pd", "cc-"
                ]

                if not any(p in tag.lower() for p in skip_patterns):
                    tags.append(tag)

        return tags[:10]  # Limit number of tags

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text.

        Args:
            text: Text possibly containing HTML

        Returns:
            Clean text
        """
        import re

        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Remove wiki markup
        clean = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", clean)
        # Clean whitespace
        clean = " ".join(clean.split())

        return clean.strip()

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
        parts = []

        if title:
            parts.append(f'"{title}"')

        if creator and creator != "Unknown":
            parts.append(f"by {creator}")

        parts.append("via Wikimedia Commons")

        if license:
            if license in ["cc0", "pd", "public domain"]:
                parts.append("(Public Domain)")
            else:
                parts.append(f"({license.upper()})")

        if url:
            parts.append(f"- {url}")

        return " ".join(parts)