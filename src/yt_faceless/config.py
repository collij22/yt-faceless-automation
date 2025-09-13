"""Backward compatibility wrapper for core.config module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .core.config import (
    AppConfig as CoreAppConfig,
    load_config as core_load_config,
)

# Re-export for backward compatibility
DEFAULT_ASSETS_DIR: Final[str] = "assets"
DEFAULT_OUTPUT_DIR: Final[str] = "output"
DEFAULT_FFMPEG_BIN: Final[str] = "ffmpeg"


@dataclass(slots=True)
class AppConfig:
    """Legacy AppConfig for backward compatibility.
    
    This class maintains the original interface while using the new enhanced config.
    """
    
    assets_dir: str
    output_dir: str
    ffmpeg_bin: str
    n8n_tts_webhook_url: str
    n8n_upload_webhook_url: str
    brave_search_api_key: str | None


def load_config() -> AppConfig:
    """Load configuration maintaining backward compatibility.
    
    Returns:
        A legacy AppConfig instance for backward compatibility.
    """
    # Load the enhanced config
    enhanced_config = core_load_config()
    
    # Map to legacy format
    return AppConfig(
        assets_dir=str(enhanced_config.directories.assets_dir),
        output_dir=str(enhanced_config.directories.output_dir),
        ffmpeg_bin=enhanced_config.video.ffmpeg_bin,
        n8n_tts_webhook_url=enhanced_config.webhooks.tts_url,
        n8n_upload_webhook_url=enhanced_config.webhooks.upload_url,
        brave_search_api_key=enhanced_config.apis.brave_search_key,
    )
