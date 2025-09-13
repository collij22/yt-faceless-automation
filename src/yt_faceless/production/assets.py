"""Asset curation and management module for video production."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import shutil
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict
from urllib.request import urlopen, urlretrieve

from ..core.config import AppConfig
from ..core.errors import AssetError, ConfigurationError
from ..integrations.n8n_client import N8NClient
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class AssetEntry(TypedDict):
    """Individual asset metadata."""
    type: Literal["video", "image", "music", "sfx"]
    url: str
    local_path: str
    sha256: str
    license: str
    attribution: Optional[str]
    duration_seconds: Optional[float]
    resolution: Optional[tuple[int, int]]
    file_size_bytes: int
    source: str
    tags: List[str]


class AssetManifest(TypedDict):
    """Asset collection manifest."""
    assets: List[AssetEntry]
    created_at: str
    updated_at: str
    attribution_required: bool
    total_size_bytes: int
    slug: str
    version: int


class AssetManager:
    """Manages asset discovery, download, and attribution."""

    # License priorities (higher = more preferred)
    LICENSE_PRIORITY = {
        "CC0": 100,  # Public Domain
        "PD": 100,  # Public Domain
        "CC-BY": 90,  # Attribution only
        "CC-BY-SA": 80,  # Attribution + ShareAlike
        "RF": 70,  # Royalty Free
        "CC-BY-NC": 60,  # Non-commercial
        "Stock": 50,  # Stock footage
    }

    # Supported asset formats
    SUPPORTED_FORMATS = {
        "video": [".mp4", ".webm", ".mov", ".avi"],
        "image": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
        "music": [".mp3", ".wav", ".aac", ".ogg"],
        "sfx": [".mp3", ".wav", ".ogg"],
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self.n8n_client = N8NClient(config) if config.webhooks.asset_url else None
        self.assets_dir = config.directories.assets_dir
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def search_assets(
        self,
        query: str,
        asset_type: str,
        license_filter: Optional[List[str]] = None,
        max_results: int = 20
    ) -> List[AssetEntry]:
        """Search for assets using configured providers.

        Args:
            query: Search query
            asset_type: Type of asset (video, image, music)
            license_filter: Allowed licenses
            max_results: Maximum results to return

        Returns:
            List of asset entries matching criteria
        """
        assets = []

        # Default license filter
        if license_filter is None:
            license_filter = ["CC0", "PD", "CC-BY", "RF"]

        # Search via different sources
        # Note: In production, these would call actual APIs
        # For now, returning mock data for testing

        if asset_type == "image":
            assets.extend(self._search_unsplash(query, license_filter, max_results))
            assets.extend(self._search_pexels(query, license_filter, max_results))
        elif asset_type == "video":
            assets.extend(self._search_pexels_videos(query, license_filter, max_results))
            assets.extend(self._search_pixabay(query, license_filter, max_results))
        elif asset_type == "music":
            assets.extend(self._search_freesound(query, license_filter, max_results))

        # Sort by license priority
        assets.sort(
            key=lambda a: self.LICENSE_PRIORITY.get(a["license"], 0),
            reverse=True
        )

        return assets[:max_results]

    def _search_unsplash(self, query: str, licenses: List[str], limit: int) -> List[AssetEntry]:
        """Search Unsplash for images (mock implementation)."""
        # In production, use Unsplash API
        return []

    def _search_pexels(self, query: str, licenses: List[str], limit: int) -> List[AssetEntry]:
        """Search Pexels for images (mock implementation)."""
        # In production, use Pexels API
        return []

    def _search_pexels_videos(self, query: str, licenses: List[str], limit: int) -> List[AssetEntry]:
        """Search Pexels for videos (mock implementation)."""
        # In production, use Pexels Videos API
        return []

    def _search_pixabay(self, query: str, licenses: List[str], limit: int) -> List[AssetEntry]:
        """Search Pixabay for videos (mock implementation)."""
        # In production, use Pixabay API
        return []

    def _search_freesound(self, query: str, licenses: List[str], limit: int) -> List[AssetEntry]:
        """Search Freesound for audio (mock implementation)."""
        # In production, use Freesound API
        return []


def plan_assets_for_slug(
    cfg: AppConfig,
    slug: str,
    max_assets: int = 30
) -> AssetManifest:
    """Plan assets for a video based on script and metadata.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        max_assets: Maximum number of assets to plan

    Returns:
        Asset manifest with planned assets
    """
    content_dir = cfg.directories.content_dir / slug
    metadata_path = content_dir / "metadata.json"
    script_path = content_dir / "script.md"

    # Load metadata and script
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text())

    # Extract keywords and visual cues
    keywords = []
    visual_cues = []

    # Get keywords from metadata
    if "tags" in metadata:
        tags = metadata["tags"]
        if isinstance(tags, dict):
            keywords.extend(tags.get("primary", []))
            keywords.extend(tags.get("competitive", []))
        elif isinstance(tags, list):
            keywords.extend(tags)

    # Get visual cues from script sections
    if "sections" in metadata:
        for section in metadata["sections"]:
            visual_cues.extend(section.get("visual_cues", []))
            visual_cues.extend(section.get("b_roll_suggestions", []))

    # If script exists, parse for additional cues
    if script_path.exists():
        script_text = script_path.read_text()
        # Extract bracketed cues like [B-ROLL: cityscape]
        import re
        cue_matches = re.findall(r'\[B-ROLL:\s*([^\]]+)\]', script_text, re.IGNORECASE)
        visual_cues.extend(cue_matches)

    # Deduplicate and clean
    keywords = list(set(k.strip() for k in keywords if k))[:20]
    visual_cues = list(set(v.strip() for v in visual_cues if v))[:30]

    # Plan asset distribution
    asset_plan = {
        "video": int(max_assets * 0.4),  # 40% video clips
        "image": int(max_assets * 0.4),  # 40% images
        "music": 2,  # Background music tracks
        "sfx": int(max_assets * 0.1),  # 10% sound effects
    }

    # Search for assets
    manager = AssetManager(cfg)
    planned_assets = []

    # Search for video clips based on visual cues
    for cue in visual_cues[:asset_plan["video"]]:
        results = manager.search_assets(
            cue,
            "video",
            license_filter=["CC0", "PD", "CC-BY"],
            max_results=1
        )
        if results:
            planned_assets.extend(results)

    # Search for images based on keywords
    for keyword in keywords[:asset_plan["image"]]:
        results = manager.search_assets(
            keyword,
            "image",
            license_filter=["CC0", "PD", "CC-BY"],
            max_results=1
        )
        if results:
            planned_assets.extend(results)

    # Search for background music
    music_queries = ["ambient", "background", "cinematic"]
    for query in music_queries[:asset_plan["music"]]:
        results = manager.search_assets(
            query,
            "music",
            license_filter=["CC0", "CC-BY"],
            max_results=1
        )
        if results:
            planned_assets.extend(results)

    # Check if attribution is required
    attribution_required = any(
        asset["license"] not in ["CC0", "PD"]
        for asset in planned_assets
    )

    # Create manifest
    manifest = AssetManifest(
        assets=planned_assets,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        attribution_required=attribution_required,
        total_size_bytes=sum(a.get("file_size_bytes", 0) for a in planned_assets),
        slug=slug,
        version=1
    )

    # Save manifest
    assets_dir = cfg.directories.assets_dir / slug
    assets_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = assets_dir / "manifest.json"

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Planned {len(planned_assets)} assets for {slug}")
    return manifest


async def download_assets(
    cfg: AppConfig,
    manifest: AssetManifest,
    parallel: bool = True,
    force_download: bool = False
) -> AssetManifest:
    """Download assets from manifest.

    Args:
        cfg: Application configuration
        manifest: Asset manifest to download
        parallel: Whether to download in parallel
        force_download: Force re-download even if exists

    Returns:
        Updated manifest with local paths
    """
    slug = manifest["slug"]
    assets_dir = cfg.directories.assets_dir / slug

    # Create asset type directories
    for asset_type in ["video", "image", "music", "sfx"]:
        (assets_dir / asset_type).mkdir(parents=True, exist_ok=True)

    updated_assets = []

    if parallel:
        # Download in parallel with concurrency limit
        semaphore = asyncio.Semaphore(cfg.performance.max_concurrent_downloads)

        async def download_asset(asset: AssetEntry) -> AssetEntry:
            async with semaphore:
                return await _download_single_asset(
                    cfg, asset, assets_dir, force_download
                )

        tasks = [download_asset(asset) for asset in manifest["assets"]]
        updated_assets = await asyncio.gather(*tasks)
    else:
        # Download sequentially
        for asset in manifest["assets"]:
            updated = await _download_single_asset(
                cfg, asset, assets_dir, force_download
            )
            updated_assets.append(updated)

    # Update manifest with local paths
    manifest["assets"] = updated_assets
    manifest["updated_at"] = datetime.now().isoformat()
    manifest["total_size_bytes"] = sum(
        a["file_size_bytes"] for a in updated_assets
    )

    # Save updated manifest
    manifest_path = assets_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Generate attribution file
    if manifest["attribution_required"]:
        write_attribution(manifest, assets_dir / "ATTRIBUTION.txt")

    logger.info(f"Downloaded {len(updated_assets)} assets for {slug}")
    return manifest


async def _download_single_asset(
    cfg: AppConfig,
    asset: AssetEntry,
    assets_dir: Path,
    force_download: bool
) -> AssetEntry:
    """Download a single asset.

    Args:
        cfg: Application configuration
        asset: Asset entry to download
        assets_dir: Directory to save assets
        force_download: Force re-download

    Returns:
        Updated asset entry with local path
    """
    # Generate local filename
    url_parsed = urllib.parse.urlparse(asset["url"])
    filename = Path(url_parsed.path).name

    # Sanitize filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    # Add hash prefix for uniqueness
    url_hash = hashlib.sha256(asset["url"].encode()).hexdigest()[:8]
    filename = f"{url_hash}_{filename}"

    # Determine local path
    local_path = assets_dir / asset["type"] / filename

    # Check if already exists
    if local_path.exists() and not force_download:
        # Verify SHA256 if provided
        if asset.get("sha256"):
            existing_hash = _calculate_file_hash(local_path)
            if existing_hash == asset["sha256"]:
                logger.debug(f"Asset already exists: {filename}")
                asset["local_path"] = str(local_path)
                return asset

    # Download via n8n webhook if configured
    if cfg.webhooks.asset_url:
        n8n_client = N8NClient(cfg)
        response = n8n_client.trigger_asset_webhook(
            asset_urls=[asset["url"]],
            destination_dir=str(local_path.parent),
            parallel=False
        )

        if response.get("success"):
            downloaded_paths = response.get("paths", [])
            if downloaded_paths:
                # Move to expected location
                downloaded = Path(downloaded_paths[0])
                if downloaded != local_path:
                    shutil.move(str(downloaded), str(local_path))
        else:
            raise AssetError(f"Asset download failed: {response.get('error')}")
    else:
        # Direct download
        try:
            urlretrieve(asset["url"], local_path)
        except Exception as e:
            logger.error(f"Failed to download {asset['url']}: {e}")
            raise AssetError(f"Download failed: {e}")

    # Calculate SHA256
    asset["sha256"] = _calculate_file_hash(local_path)
    asset["local_path"] = str(local_path)
    asset["file_size_bytes"] = local_path.stat().st_size

    # Extract metadata if possible
    if asset["type"] in ["video", "image"]:
        asset["resolution"] = _get_media_resolution(local_path)
    if asset["type"] in ["video", "music", "sfx"]:
        asset["duration_seconds"] = _get_media_duration(local_path)

    logger.debug(f"Downloaded: {filename}")
    return asset


def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash hex string
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _get_media_resolution(file_path: Path) -> Optional[tuple[int, int]]:
    """Get resolution of image/video file.

    Args:
        file_path: Path to media file

    Returns:
        (width, height) tuple or None
    """
    # In production, use ffprobe or PIL
    # For now, return mock data
    return None


def _get_media_duration(file_path: Path) -> Optional[float]:
    """Get duration of audio/video file.

    Args:
        file_path: Path to media file

    Returns:
        Duration in seconds or None
    """
    # In production, use ffprobe
    # For now, return mock data
    return None


def write_attribution(manifest: AssetManifest, output_path: Path) -> None:
    """Write attribution file for assets requiring attribution.

    Args:
        manifest: Asset manifest
        output_path: Path to write attribution file
    """
    lines = [
        "ASSET ATTRIBUTION",
        "=" * 50,
        "",
        f"Generated: {datetime.now().isoformat()}",
        f"Project: {manifest['slug']}",
        "",
        "The following assets require attribution:",
        "",
    ]

    attribution_count = 0

    for asset in manifest["assets"]:
        if asset["license"] not in ["CC0", "PD"]:
            attribution_count += 1
            lines.extend([
                f"{attribution_count}. {Path(asset['local_path']).name}",
                f"   Type: {asset['type']}",
                f"   License: {asset['license']}",
                f"   Source: {asset.get('source', 'Unknown')}",
            ])

            if asset.get("attribution"):
                lines.append(f"   Attribution: {asset['attribution']}")

            lines.append(f"   URL: {asset['url']}")
            lines.append("")

    if attribution_count == 0:
        lines.extend([
            "No attribution required for assets in this project.",
            "All assets are CC0 or Public Domain.",
        ])

    # Write file
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Wrote attribution file: {output_path}")


def verify_asset_integrity(manifest: AssetManifest) -> List[str]:
    """Verify integrity of downloaded assets.

    Args:
        manifest: Asset manifest to verify

    Returns:
        List of error messages (empty if all valid)
    """
    errors = []

    for asset in manifest["assets"]:
        local_path = asset.get("local_path")

        if not local_path:
            errors.append(f"No local path for {asset['url']}")
            continue

        path = Path(local_path)

        if not path.exists():
            errors.append(f"Missing file: {local_path}")
            continue

        # Verify SHA256 if provided
        if asset.get("sha256"):
            actual_hash = _calculate_file_hash(path)
            if actual_hash != asset["sha256"]:
                errors.append(f"Hash mismatch for {local_path}")

        # Verify file size
        actual_size = path.stat().st_size
        if asset.get("file_size_bytes") and actual_size != asset["file_size_bytes"]:
            errors.append(f"Size mismatch for {local_path}")

    return errors