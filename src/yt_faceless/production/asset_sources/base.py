"""Base class for asset source providers."""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass
class AssetSearchResult:
    """Individual asset search result."""

    url: str
    thumbnail_url: Optional[str]
    title: str
    creator: Optional[str]
    license: str
    license_url: Optional[str]
    source: str
    source_url: str
    width: Optional[int]
    height: Optional[int]
    tags: List[str]
    attribution: Optional[str]

    @property
    def resolution(self) -> Optional[tuple[int, int]]:
        """Get resolution as tuple."""
        if self.width and self.height:
            return (self.width, self.height)
        return None

    @property
    def is_high_res(self) -> bool:
        """Check if asset meets minimum resolution requirements."""
        return self.width >= 1280 if self.width else False


class AssetSource(ABC):
    """Abstract base class for asset sources."""

    # Allowed licenses for commercial use
    ALLOWED_LICENSES = {
        "cc0", "pdm", "pd", "publicdomain",  # Public domain
        "by", "cc-by", "by-sa", "cc-by-sa",  # Creative Commons with attribution
    }

    # Denied licenses (non-commercial, no derivatives)
    DENIED_LICENSES = {
        "by-nc", "by-nd", "by-nc-sa", "by-nc-nd",
        "cc-by-nc", "cc-by-nd", "cc-by-nc-sa", "cc-by-nc-nd",
    }

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_days: int = 7):
        """Initialize asset source.

        Args:
            cache_dir: Directory for caching responses
            cache_ttl_days: Cache time-to-live in days
        """
        self.cache_dir = cache_dir or Path(".cache/assets")
        self.cache_ttl = timedelta(days=cache_ttl_days)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
        min_width: Optional[int] = 1280
    ) -> List[AssetSearchResult]:
        """Search for assets.

        Args:
            query: Search query
            limit: Maximum results per page
            page: Page number (1-indexed)
            min_width: Minimum image width

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the source name for attribution."""
        pass

    def is_license_allowed(self, license_code: str) -> bool:
        """Check if license is allowed for commercial use.

        Args:
            license_code: License identifier

        Returns:
            True if license is allowed
        """
        if not license_code:
            return False

        # Normalize license code
        normalized = license_code.lower().replace("_", "-").strip()

        # Check against denied list first
        for denied in self.DENIED_LICENSES:
            if denied in normalized:
                return False

        # Check against allowed list
        for allowed in self.ALLOWED_LICENSES:
            if allowed in normalized:
                return True

        # Default to deny unknown licenses
        logger.warning(f"Unknown license: {license_code}")
        return False

    def get_cache_key(self, query: str, **params) -> str:
        """Generate cache key for query.

        Args:
            query: Search query
            **params: Additional parameters

        Returns:
            Cache key string
        """
        # Combine query and params into stable key
        key_data = {"query": query, **params}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        cache_file = self.cache_dir / f"{self.get_source_name()}_{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            # Check if cache is still valid
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > self.cache_ttl:
                logger.debug(f"Cache expired for key {cache_key}")
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"Cache hit for key {cache_key}")
                return data

        except Exception as e:
            logger.error(f"Error reading cache {cache_file}: {e}")
            return None

    def save_cache_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save response to cache.

        Args:
            cache_key: Cache key
            data: Response data to cache
        """
        cache_file = self.cache_dir / f"{self.get_source_name()}_{cache_key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                logger.debug(f"Cached response for key {cache_key}")

        except Exception as e:
            logger.error(f"Error saving cache {cache_file}: {e}")

    def filter_by_license(self, results: List[AssetSearchResult]) -> List[AssetSearchResult]:
        """Filter results by allowed licenses.

        Args:
            results: Search results to filter

        Returns:
            Filtered results with allowed licenses
        """
        filtered = []
        for result in results:
            if self.is_license_allowed(result.license):
                filtered.append(result)
            else:
                logger.debug(f"Filtered out {result.title} with license {result.license}")

        return filtered

    def filter_by_resolution(
        self,
        results: List[AssetSearchResult],
        min_width: int = 1280
    ) -> List[AssetSearchResult]:
        """Filter results by minimum resolution.

        Args:
            results: Search results to filter
            min_width: Minimum width requirement

        Returns:
            Filtered results meeting resolution requirements
        """
        filtered = []
        for result in results:
            if result.width is None or result.width >= min_width:
                filtered.append(result)
            else:
                logger.debug(f"Filtered out {result.title} with width {result.width}")

        return filtered

    def deduplicate_results(
        self,
        results: List[AssetSearchResult],
        existing_urls: Optional[set] = None
    ) -> List[AssetSearchResult]:
        """Remove duplicate results.

        Args:
            results: Search results to deduplicate
            existing_urls: Set of URLs already used

        Returns:
            Deduplicated results
        """
        seen_urls = existing_urls or set()
        unique = []

        for result in results:
            if result.url not in seen_urls:
                unique.append(result)
                seen_urls.add(result.url)

        return unique