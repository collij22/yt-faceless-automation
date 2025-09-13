"""Enhanced configuration management with validation and health checks."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Final, Optional
from urllib.parse import urlparse

from ..core.errors import ConfigurationError


# Default values
DEFAULT_ASSETS_DIR: Final[str] = "assets"
DEFAULT_OUTPUT_DIR: Final[str] = "output"
DEFAULT_CONTENT_DIR: Final[str] = "content"
DEFAULT_DATA_DIR: Final[str] = "data"
DEFAULT_CACHE_DIR: Final[str] = ".cache"
DEFAULT_LOGS_DIR: Final[str] = "logs"
DEFAULT_FFMPEG_BIN: Final[str] = "ffmpeg"


@dataclass(slots=True)
class DirectoryConfig:
    """Directory configuration."""
    assets_dir: Path
    output_dir: Path
    content_dir: Path
    data_dir: Path
    cache_dir: Path
    logs_dir: Path
    
    def create_all(self) -> None:
        """Create all directories if they don't exist."""
        for dir_path in [
            self.assets_dir, self.output_dir, self.content_dir,
            self.data_dir, self.cache_dir, self.logs_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """Validate directory configuration."""
        issues = []
        for name, dir_path in [
            ("assets", self.assets_dir),
            ("output", self.output_dir),
            ("content", self.content_dir),
            ("data", self.data_dir),
            ("cache", self.cache_dir),
            ("logs", self.logs_dir),
        ]:
            if not dir_path.parent.exists():
                issues.append(f"{name}_dir parent directory does not exist: {dir_path.parent}")
        return issues


@dataclass(slots=True)
class WebhookConfig:
    """n8n webhook configuration."""
    tts_url: str
    upload_url: str
    analytics_url: str
    asset_url: Optional[str] = None
    error_url: Optional[str] = None
    # Phase 8 webhooks
    shortener_url: Optional[str] = None
    crosspost_url: Optional[str] = None
    localization_url: Optional[str] = None
    pin_comment_url: Optional[str] = None
    revenue_track_url: Optional[str] = None
    # Additional Phase 8 webhooks
    tiktok_upload_url: Optional[str] = None
    instagram_upload_url: Optional[str] = None
    x_upload_url: Optional[str] = None
    translation_url: Optional[str] = None
    moderation_url: Optional[str] = None
    scheduled_upload_url: Optional[str] = None

    def validate(self) -> list[str]:
        """Validate webhook URLs."""
        issues = []
        for name, url in [
            ("TTS", self.tts_url),
            ("Upload", self.upload_url),
            ("Analytics", self.analytics_url),
            ("Asset", self.asset_url),
            ("Error", self.error_url),
            ("Shortener", self.shortener_url),
            ("Crosspost", self.crosspost_url),
            ("Localization", self.localization_url),
            ("Pin Comment", self.pin_comment_url),
            ("Revenue Track", self.revenue_track_url),
        ]:
            if url:
                parsed = urlparse(url)
                if not parsed.scheme in ["http", "https"]:
                    issues.append(f"{name} webhook URL must use http/https: {url}")
                if not parsed.netloc:
                    issues.append(f"{name} webhook URL is invalid: {url}")
        return issues


@dataclass(slots=True)
class APIConfig:
    """API keys and endpoints configuration."""
    brave_search_key: Optional[str] = None
    firecrawl_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    google_search_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    n8n_api_key: Optional[str] = None
    n8n_api_url: Optional[str] = None
    
    def validate(self) -> list[str]:
        """Validate API configuration."""
        issues = []
        # Note: Firecrawl and YouTube keys are optional but recommended
        # They will generate warnings in health_check() if missing
        return issues
    
    def mask_keys(self) -> Dict[str, str]:
        """Return masked API keys for logging (slots-safe)."""
        from dataclasses import fields
        masked: Dict[str, str] = {}
        for f in fields(self):
            key = f.name
            value = getattr(self, key)
            if isinstance(value, str) and value and "key" in key.lower():
                masked[key] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                masked[key] = value if value is not None else "Not set"
        return masked


@dataclass(slots=True)
class TTSConfig:
    """TTS provider configuration."""
    provider: str = "elevenlabs"
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    elevenlabs_model: str = "eleven_monolingual_v1"
    playht_api_key: Optional[str] = None
    playht_user_id: Optional[str] = None
    playht_voice_id: Optional[str] = None
    google_cloud_project_id: Optional[str] = None
    google_cloud_key_file: Optional[str] = None
    
    def validate(self) -> list[str]:
        """Validate TTS configuration."""
        issues = []
        if self.provider == "elevenlabs":
            if not self.elevenlabs_api_key:
                issues.append("ElevenLabs API key required for elevenlabs provider")
            if not self.elevenlabs_voice_id:
                issues.append("ElevenLabs voice ID required for elevenlabs provider")
        elif self.provider == "playht":
            if not self.playht_api_key:
                issues.append("PlayHT API key required for playht provider")
            if not self.playht_user_id:
                issues.append("PlayHT user ID required for playht provider")
        elif self.provider == "google":
            if not self.google_cloud_project_id:
                issues.append("Google Cloud project ID required for google provider")
            if self.google_cloud_key_file:
                if not Path(self.google_cloud_key_file).exists():
                    issues.append(f"Google Cloud key file not found: {self.google_cloud_key_file}")
        else:
            issues.append(f"Unknown TTS provider: {self.provider}")
        return issues


@dataclass(slots=True)
class VideoConfig:
    """Video production configuration."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_bitrate: str = "5000k"
    audio_bitrate: str = "192k"
    audio_sample_rate: int = 44100
    video_codec: str = "libx264"
    video_preset: str = "medium"
    video_crf: int = 23
    audio_loudness_target: int = -14
    audio_loudness_range: int = 7
    ffmpeg_bin: str = DEFAULT_FFMPEG_BIN
    
    def validate(self) -> list[str]:
        """Validate video configuration and FFmpeg availability."""
        issues = []
        
        # Validate FFmpeg
        try:
            result = subprocess.run(
                [self.ffmpeg_bin, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                issues.append(f"FFmpeg not working properly: {result.stderr}")
        except FileNotFoundError:
            issues.append(f"FFmpeg not found at: {self.ffmpeg_bin}")
        except subprocess.TimeoutExpired:
            issues.append("FFmpeg timeout - may be misconfigured")
        except Exception as e:
            issues.append(f"FFmpeg check failed: {e}")
        
        # Validate video settings
        if self.width <= 0 or self.height <= 0:
            issues.append(f"Invalid video dimensions: {self.width}x{self.height}")
        if self.fps <= 0 or self.fps > 120:
            issues.append(f"Invalid FPS: {self.fps}")
        if self.video_crf < 0 or self.video_crf > 51:
            issues.append(f"Invalid CRF value: {self.video_crf} (should be 0-51)")
        
        return issues


@dataclass(slots=True)
class ResearchConfig:
    """Research and scoring configuration."""
    max_results: int = 100
    cache_days: int = 7
    competitor_depth: int = 10
    trend_lookback_days: int = 30
    score_weight_rpm: float = 0.25
    score_weight_trend: float = 0.20
    score_weight_competition: float = 0.20
    score_weight_virality: float = 0.20
    score_weight_monetization: float = 0.15
    
    def validate(self) -> list[str]:
        """Validate research configuration."""
        issues = []
        
        # Check score weights sum to 1
        total_weight = (
            self.score_weight_rpm +
            self.score_weight_trend +
            self.score_weight_competition +
            self.score_weight_virality +
            self.score_weight_monetization
        )
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Score weights must sum to 1.0, got {total_weight}")
        
        # Validate other parameters
        if self.max_results <= 0:
            issues.append(f"Invalid max_results: {self.max_results}")
        if self.cache_days <= 0:
            issues.append(f"Invalid cache_days: {self.cache_days}")
        
        return issues


@dataclass(slots=True)
class PerformanceConfig:
    """Performance and optimization configuration."""
    max_concurrent_requests: int = 5
    max_concurrent_downloads: int = 3
    max_concurrent_tts_chunks: int = 2
    max_retry_attempts: int = 3
    retry_backoff_base: int = 2
    retry_max_wait: int = 60
    cache_max_size_mb: int = 1000
    cache_ttl_hours: int = 168
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    
    def validate(self) -> list[str]:
        """Validate performance configuration."""
        issues = []
        if self.max_concurrent_requests <= 0:
            issues.append(f"Invalid max_concurrent_requests: {self.max_concurrent_requests}")
        if self.max_retry_attempts < 0:
            issues.append(f"Invalid max_retry_attempts: {self.max_retry_attempts}")
        if self.cache_max_size_mb <= 0:
            issues.append(f"Invalid cache_max_size_mb: {self.cache_max_size_mb}")
        return issues


@dataclass
class AppConfig:
    """Complete application configuration."""
    directories: DirectoryConfig
    webhooks: WebhookConfig
    apis: APIConfig
    tts: TTSConfig
    video: VideoConfig
    research: ResearchConfig
    performance: PerformanceConfig
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "auto_thumbnail": False,
        "auto_chapters": True,
        "auto_subtitles": True,
        "auto_endscreen": True,
        "ab_testing": False,
        "shorts_generation": False,
        "multi_language": False,
        # Phase 8 features
        "affiliate_injection": True,
        "sponsorships": True,
        "multiplatform_distribution": False,
        "calendar_enabled": True,
    })
    
    # Environment settings
    debug: bool = False
    testing: bool = False
    dry_run: bool = False
    
    def validate(self) -> Dict[str, list[str]]:
        """Validate entire configuration."""
        validation_results = {
            "directories": self.directories.validate(),
            "webhooks": self.webhooks.validate(),
            "apis": self.apis.validate(),
            "tts": self.tts.validate(),
            "video": self.video.validate(),
            "research": self.research.validate(),
            "performance": self.performance.validate(),
        }
        
        # Filter out empty lists
        return {k: v for k, v in validation_results.items() if v}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "status": "healthy",
            "checks": {},
            "warnings": [],
            "errors": [],
        }
        
        # Run validation
        validation_issues = self.validate()
        if validation_issues:
            health_status["status"] = "unhealthy"
            for component, issues in validation_issues.items():
                health_status["errors"].extend([f"{component}: {issue}" for issue in issues])
        
        # Check directories
        health_status["checks"]["directories"] = {
            "assets": self.directories.assets_dir.exists(),
            "output": self.directories.output_dir.exists(),
            "content": self.directories.content_dir.exists(),
            "data": self.directories.data_dir.exists(),
            "cache": self.directories.cache_dir.exists(),
            "logs": self.directories.logs_dir.exists(),
        }
        
        # Check API keys (masked)
        health_status["checks"]["apis"] = self.apis.mask_keys()
        
        # Check FFmpeg
        try:
            result = subprocess.run(
                [self.video.ffmpeg_bin, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            health_status["checks"]["ffmpeg"] = {
                "available": result.returncode == 0,
                "path": self.video.ffmpeg_bin,
            }
        except:
            health_status["checks"]["ffmpeg"] = {
                "available": False,
                "path": self.video.ffmpeg_bin,
            }
        
        # Add warnings for optional but recommended configurations
        if not self.apis.firecrawl_key:
            health_status["warnings"].append("Firecrawl API key not configured (recommended for research functionality)")
        if not self.apis.youtube_api_key:
            health_status["warnings"].append("YouTube API key not configured (recommended for competitor analysis)")
        if not self.apis.brave_search_key:
            health_status["warnings"].append("Brave Search API key not configured (optional but recommended)")
        
        # Update overall status
        if health_status["errors"]:
            health_status["status"] = "unhealthy"
        elif health_status["warnings"]:
            health_status["status"] = "degraded"
        
        return health_status


def load_config() -> AppConfig:
    """Load configuration from environment variables with validation."""
    from dotenv import load_dotenv
    
    # Load .env file if it exists
    load_dotenv()
    
    # Load directory configuration
    directories = DirectoryConfig(
        assets_dir=Path(os.getenv("ASSETS_DIR", DEFAULT_ASSETS_DIR)),
        output_dir=Path(os.getenv("OUTPUT_DIR", DEFAULT_OUTPUT_DIR)),
        content_dir=Path(os.getenv("CONTENT_DIR", DEFAULT_CONTENT_DIR)),
        data_dir=Path(os.getenv("DATA_DIR", DEFAULT_DATA_DIR)),
        cache_dir=Path(os.getenv("CACHE_DIR", DEFAULT_CACHE_DIR)),
        logs_dir=Path(os.getenv("LOGS_DIR", DEFAULT_LOGS_DIR)),
    )
    
    # Load webhook configuration
    webhooks = WebhookConfig(
        tts_url=os.getenv("N8N_TTS_WEBHOOK_URL", ""),
        upload_url=os.getenv("N8N_UPLOAD_WEBHOOK_URL", ""),
        analytics_url=os.getenv("YOUTUBE_ANALYTICS_WEBHOOK_URL", ""),
        asset_url=os.getenv("N8N_ASSET_WEBHOOK_URL"),
        error_url=os.getenv("N8N_ERROR_WEBHOOK_URL"),
        # Phase 8 webhooks
        shortener_url=os.getenv("N8N_SHORTENER_WEBHOOK_URL"),
        crosspost_url=os.getenv("N8N_CROSSPOST_WEBHOOK_URL"),
        localization_url=os.getenv("N8N_LOCALIZATION_WEBHOOK_URL"),
        pin_comment_url=os.getenv("N8N_PIN_COMMENT_WEBHOOK_URL"),
        revenue_track_url=os.getenv("N8N_REVENUE_TRACK_WEBHOOK_URL"),
        # Additional Phase 8 webhooks
        tiktok_upload_url=os.getenv("TIKTOK_UPLOAD_WEBHOOK_URL"),
        instagram_upload_url=os.getenv("INSTAGRAM_UPLOAD_WEBHOOK_URL"),
        x_upload_url=os.getenv("X_UPLOAD_WEBHOOK_URL"),
        translation_url=os.getenv("TRANSLATION_WEBHOOK_URL"),
        moderation_url=os.getenv("MODERATION_WEBHOOK_URL"),
        scheduled_upload_url=os.getenv("SCHEDULED_UPLOAD_WEBHOOK_URL"),
    )
    
    # Validate required webhooks
    if not webhooks.tts_url:
        raise ConfigurationError("N8N_TTS_WEBHOOK_URL is required")
    if not webhooks.upload_url:
        raise ConfigurationError("N8N_UPLOAD_WEBHOOK_URL is required")
    if not webhooks.analytics_url:
        raise ConfigurationError("YOUTUBE_ANALYTICS_WEBHOOK_URL is required")
    
    # Load API configuration
    apis = APIConfig(
        brave_search_key=os.getenv("BRAVE_SEARCH_API_KEY"),
        firecrawl_key=os.getenv("FIRECRAWL_API_KEY"),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
        google_search_key=os.getenv("GOOGLE_SEARCH_API_KEY"),
        google_search_engine_id=os.getenv("GOOGLE_SEARCH_ENGINE_ID"),
        n8n_api_key=os.getenv("N8N_API_KEY"),
        n8n_api_url=os.getenv("N8N_API_URL"),
    )
    
    # Load TTS configuration
    tts = TTSConfig(
        provider=os.getenv("TTS_PROVIDER", "elevenlabs"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        elevenlabs_model=os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1"),
        playht_api_key=os.getenv("PLAYHT_API_KEY"),
        playht_user_id=os.getenv("PLAYHT_USER_ID"),
        playht_voice_id=os.getenv("PLAYHT_VOICE_ID"),
        google_cloud_project_id=os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        google_cloud_key_file=os.getenv("GOOGLE_CLOUD_TTS_KEY_FILE"),
    )
    
    # Load video configuration
    video = VideoConfig(
        width=int(os.getenv("DEFAULT_VIDEO_WIDTH", "1920")),
        height=int(os.getenv("DEFAULT_VIDEO_HEIGHT", "1080")),
        fps=int(os.getenv("DEFAULT_VIDEO_FPS", "30")),
        video_bitrate=os.getenv("DEFAULT_VIDEO_BITRATE", "5000k"),
        audio_bitrate=os.getenv("DEFAULT_AUDIO_BITRATE", "192k"),
        audio_sample_rate=int(os.getenv("DEFAULT_AUDIO_SAMPLE_RATE", "44100")),
        video_codec=os.getenv("VIDEO_CODEC", "libx264"),
        video_preset=os.getenv("VIDEO_PRESET", "medium"),
        video_crf=int(os.getenv("VIDEO_CRF", "23")),
        audio_loudness_target=int(os.getenv("AUDIO_LOUDNESS_TARGET", "-14")),
        audio_loudness_range=int(os.getenv("AUDIO_LOUDNESS_RANGE", "7")),
        ffmpeg_bin=os.getenv("FFMPEG_BIN", DEFAULT_FFMPEG_BIN),
    )
    
    # Load research configuration
    research = ResearchConfig(
        max_results=int(os.getenv("MAX_RESEARCH_RESULTS", "100")),
        cache_days=int(os.getenv("RESEARCH_CACHE_DAYS", "7")),
        competitor_depth=int(os.getenv("COMPETITOR_ANALYSIS_DEPTH", "10")),
        trend_lookback_days=int(os.getenv("TREND_LOOKBACK_DAYS", "30")),
        score_weight_rpm=float(os.getenv("SCORE_WEIGHT_RPM", "0.25")),
        score_weight_trend=float(os.getenv("SCORE_WEIGHT_TREND", "0.20")),
        score_weight_competition=float(os.getenv("SCORE_WEIGHT_COMPETITION", "0.20")),
        score_weight_virality=float(os.getenv("SCORE_WEIGHT_VIRALITY", "0.20")),
        score_weight_monetization=float(os.getenv("SCORE_WEIGHT_MONETIZATION", "0.15")),
    )
    
    # Load performance configuration
    performance = PerformanceConfig(
        max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
        max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3")),
        max_concurrent_tts_chunks=int(os.getenv("MAX_CONCURRENT_TTS_CHUNKS", "2")),
        max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
        retry_backoff_base=int(os.getenv("RETRY_BACKOFF_BASE", "2")),
        retry_max_wait=int(os.getenv("RETRY_MAX_WAIT", "60")),
        cache_max_size_mb=int(os.getenv("CACHE_MAX_SIZE_MB", "1000")),
        cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "168")),
        rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
        rate_limit_burst_size=int(os.getenv("RATE_LIMIT_BURST_SIZE", "10")),
    )
    
    # Load feature flags
    features = {
        "auto_thumbnail": os.getenv("FEATURE_AUTO_THUMBNAIL", "false").lower() == "true",
        "auto_chapters": os.getenv("FEATURE_AUTO_CHAPTERS", "true").lower() == "true",
        "auto_subtitles": os.getenv("FEATURE_AUTO_SUBTITLES", "true").lower() == "true",
        "auto_endscreen": os.getenv("FEATURE_AUTO_ENDSCREEN", "true").lower() == "true",
        "ab_testing": os.getenv("FEATURE_AB_TESTING", "false").lower() == "true",
        "shorts_generation": os.getenv("FEATURE_SHORTS_GENERATION", "true").lower() == "true",
        "multi_language": os.getenv("FEATURE_MULTI_LANGUAGE", "false").lower() == "true",
        # Phase 8 features
        "affiliate_injection": os.getenv("FEATURE_AFFILIATE_INJECTION", "true").lower() == "true",
        "sponsorships": os.getenv("FEATURE_SPONSORSHIPS", "true").lower() == "true",
        "multiplatform_distribution": os.getenv("FEATURE_MULTIPLATFORM_DISTRIBUTION", "false").lower() == "true",
        "calendar_enabled": os.getenv("FEATURE_CALENDAR_ENABLED", "true").lower() == "true",
    }
    
    # Create config object
    config = AppConfig(
        directories=directories,
        webhooks=webhooks,
        apis=apis,
        tts=tts,
        video=video,
        research=research,
        performance=performance,
        features=features,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        testing=os.getenv("TESTING", "false").lower() == "true",
        dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
    )
    
    # Create directories if they don't exist
    config.directories.create_all()
    
    # Validate configuration
    validation_issues = config.validate()
    if validation_issues:
        error_msg = "Configuration validation failed:\n"
        for component, issues in validation_issues.items():
            error_msg += f"\n{component}:\n"
            for issue in issues:
                error_msg += f"  - {issue}\n"
        raise ConfigurationError(error_msg)
    
    return config