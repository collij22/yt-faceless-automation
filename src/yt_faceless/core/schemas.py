"""Pydantic schemas for data validation and serialization."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
except ImportError:
    # Fallback for basic functionality without pydantic
    from dataclasses import dataclass as BaseModel
    Field = lambda default=None, **kwargs: default
    field_validator = lambda *args, **kwargs: lambda func: func
    model_validator = lambda *args, **kwargs: lambda func: func


class VideoNiche(str, Enum):
    """Supported video niches."""
    TECH_REVIEWS = "tech_reviews"
    AI_NEWS = "ai_news"
    FINANCE = "finance"
    CRYPTO = "crypto"
    PSYCHOLOGY = "psychology"
    HISTORY = "history"
    SCIENCE = "science"
    TRUE_CRIME = "true_crime"
    MOTIVATION = "motivation"
    EDUCATION = "education"
    LIFESTYLE = "lifestyle"
    HEALTH = "health"
    BUSINESS = "business"
    PRODUCTIVITY = "productivity"


class ContentStatus(str, Enum):
    """Content pipeline status."""
    PENDING = "pending"
    RESEARCHING = "researching"
    SCRIPTING = "scripting"
    PRODUCING = "producing"
    ASSEMBLING = "assembling"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"


class AssetType(str, Enum):
    """Types of assets."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    MUSIC = "music"
    SOUND_EFFECT = "sfx"


# Research Schemas

class IdeaScores(BaseModel):
    """Scoring metrics for video ideas."""
    rpm: float = Field(ge=0, le=10, description="Revenue per mille score")
    trend_velocity: float = Field(ge=0, le=10, description="Trend growth rate score")
    competition_gap: float = Field(ge=0, le=10, description="Supply/demand gap score")
    virality: float = Field(ge=0, le=10, description="Viral potential score")
    monetization: float = Field(ge=0, le=10, description="Monetization safety score")
    composite: float = Field(ge=0, le=10, description="Overall composite score")


class CompetitorAnalysis(BaseModel):
    """Competitor video analysis."""
    channel_name: str
    channel_id: Optional[str] = None
    video_title: str
    video_id: Optional[str] = None
    views: int
    likes: Optional[int] = None
    comments: Optional[int] = None
    duration_seconds: int
    published_at: datetime
    strategy_notes: Optional[str] = None


class Keywords(BaseModel):
    """SEO keywords structure."""
    primary: list[str] = Field(default_factory=list, max_length=5)
    secondary: list[str] = Field(default_factory=list, max_length=10)
    long_tail: list[str] = Field(default_factory=list, max_length=20)


class IdeaValidation(BaseModel):
    """Content validation flags."""
    youtube_safe: bool = True
    copyright_clear: bool = True
    trend_sustainable: bool = True
    monetization_eligible: bool = True


class VideoIdea(BaseModel):
    """Complete video idea with research data."""
    idea_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str = Field(min_length=10, max_length=100)
    angle: str = Field(min_length=20, max_length=500)
    niche: VideoNiche
    scores: IdeaScores
    keywords: Keywords
    competitors: list[CompetitorAnalysis] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    validation: IdeaValidation
    notes: Optional[str] = None


# Script Schemas

class ScriptSection(BaseModel):
    """Individual script section."""
    section_id: str
    section_type: str  # intro, hook, content, cta, outro
    start_time: float  # seconds
    end_time: float  # seconds
    text: str
    ssml_text: Optional[str] = None
    visual_cues: list[str] = Field(default_factory=list)
    b_roll_suggestions: list[str] = Field(default_factory=list)


class VideoScript(BaseModel):
    """Complete video script."""
    script_id: UUID = Field(default_factory=uuid4)
    idea_id: UUID
    title: str
    duration_seconds: int
    word_count: int
    sections: list[ScriptSection]
    hook_text: str
    cta_text: str
    created_at: datetime = Field(default_factory=datetime.now)


# Metadata Schemas

class TitleVariant(BaseModel):
    """Title option with metrics."""
    text: str = Field(max_length=60)
    ctr_prediction: Optional[float] = Field(None, ge=0, le=1)
    keyword_density: Optional[float] = Field(None, ge=0, le=1)
    ab_test_group: Optional[str] = None


class VideoDescription(BaseModel):
    """Video description with SEO elements."""
    text: str = Field(min_length=100, max_length=5000)
    keywords_included: list[str] = Field(default_factory=list)
    timestamps: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)


class VideoTags(BaseModel):
    """Categorized video tags."""
    primary: list[str] = Field(default_factory=list, max_length=10)
    competitive: list[str] = Field(default_factory=list, max_length=15)
    trending: list[str] = Field(default_factory=list, max_length=15)
    long_tail: list[str] = Field(default_factory=list, max_length=10)


class VideoMetadata(BaseModel):
    """Complete video metadata for upload."""
    video_id: UUID = Field(default_factory=uuid4)
    script_id: UUID
    titles: list[TitleVariant]
    description: VideoDescription
    tags: VideoTags
    category_id: Optional[int] = None  # YouTube category ID
    thumbnail_path: Optional[str] = None
    chapters: list[tuple[float, str]] = Field(default_factory=list)
    end_screen_elements: list[dict] = Field(default_factory=list)
    cards: list[dict] = Field(default_factory=list)
    playlist_id: Optional[str] = None
    language: str = "en"
    caption_file: Optional[str] = None


# Asset Schemas

class Asset(BaseModel):
    """Individual asset information."""
    asset_id: UUID = Field(default_factory=uuid4)
    asset_type: AssetType
    url: str
    local_path: Optional[str] = None
    attribution: Optional[str] = None
    license: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetCollection(BaseModel):
    """Collection of assets for a video."""
    video_id: UUID
    assets: list[Asset] = Field(default_factory=list)
    total_size_bytes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


# Production Schemas

class TTSRequest(BaseModel):
    """TTS generation request."""
    text: str
    voice_id: str
    model: str = "eleven_monolingual_v1"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(0, ge=-20, le=20)
    emphasis: float = Field(1.0, ge=0, le=2)
    ssml_enabled: bool = False


class TTSResponse(BaseModel):
    """TTS generation response."""
    audio_url: Optional[str] = None
    audio_path: str
    duration_seconds: float
    character_count: int
    cost_estimate: Optional[float] = None


class VideoAssemblyRequest(BaseModel):
    """Video assembly parameters."""
    video_id: UUID
    clips: list[str]  # paths to video clips
    audio_path: str
    subtitle_path: Optional[str] = None
    music_path: Optional[str] = None
    output_path: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"
    crf: int = 23


# Analytics Schemas

class VideoPerformance(BaseModel):
    """Video performance metrics."""
    video_id: UUID
    youtube_video_id: str
    views: int
    likes: int
    comments: int
    shares: int
    watch_time_hours: float
    average_view_duration: float
    click_through_rate: float
    impressions: int
    revenue_usd: float
    rpm: float
    retrieved_at: datetime = Field(default_factory=datetime.now)


class ChannelAnalytics(BaseModel):
    """Channel-level analytics."""
    channel_id: str
    subscribers: int
    total_views: int
    total_videos: int
    average_rpm: float
    top_performing_niches: list[VideoNiche]
    growth_rate_weekly: float
    retrieved_at: datetime = Field(default_factory=datetime.now)


# Phase 6: Upload & Publishing Schemas

class ChapterMarker(BaseModel):
    """Video chapter marker."""
    start: str  # Format: "00:00"
    title: str

    @field_validator('start')
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        import re
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError('Invalid timestamp format. Use MM:SS')
        return v


class QualityGates(BaseModel):
    """Pre-upload quality validation gates."""
    min_duration_sec: int = 60
    max_duration_sec: int = 3600
    min_resolution: tuple[int, int] = (1280, 720)
    required_audio_loudness: tuple[int, int] = (-20, -10)  # LUFS range
    copyright_check_passed: bool = True  # Default to True unless explicitly failed
    profanity_check_passed: bool = True


class AffiliateLink(BaseModel):
    """Affiliate link information."""
    url: str
    description: str
    position: Optional[str] = None  # "description", "comment_pinned"


class MonetizationSettings(BaseModel):
    """Video monetization configuration."""
    enable_ads: bool = True
    enable_channel_memberships: bool = False
    enable_super_chat: bool = False
    mid_roll_positions_sec: Optional[list[int]] = None
    affiliate_links: Optional[list[AffiliateLink]] = None
    sponsorship_disclosure: Optional[str] = None


class RetentionHook(BaseModel):
    """Audience retention optimization hook."""
    timestamp_sec: int
    hook_type: str  # "visual", "audio", "narrative"
    description: str


class YouTubeUploadPayload(BaseModel):
    """YouTube upload request payload."""
    video_path: str
    thumbnail_path: Optional[str] = None
    title: str = Field(max_length=100)
    description: str = Field(max_length=5000)
    tags: list[str] = Field(max_items=500)  # Combined length ≤ 500 chars
    category_id: Optional[int] = None
    privacy_status: str = Field(default="private", pattern="^(public|unlisted|private)$")
    publish_at_iso: Optional[str] = None
    made_for_kids: bool = False
    language: Optional[str] = "en"
    chapters: Optional[list[ChapterMarker]] = None
    slug: str
    checksum_sha256: str

    # Enhanced fields
    transaction_id: str
    quality_gates: Optional[QualityGates] = None
    monetization_settings: Optional[MonetizationSettings] = None
    audience_retention_hooks: Optional[list[RetentionHook]] = None
    platform_targets: list[str] = Field(default_factory=lambda: ["youtube"])
    upload_priority: int = Field(default=5, ge=1, le=10)
    parent_video_id: Optional[str] = None  # For Shorts from main video
    experiment_id: Optional[str] = None  # Link to A/B test

    @field_validator('tags')
    def validate_tags_length(cls, v):
        """Validate combined tags length."""
        combined = ','.join(v)
        if len(combined) > 500:
            raise ValueError(f'Combined tags length ({len(combined)}) exceeds 500 characters')
        return v


class QualityScores(BaseModel):
    """Video quality assessment scores."""
    technical_quality: float = Field(ge=0, le=100)
    seo_optimization: float = Field(ge=0, le=100)
    monetization_readiness: float = Field(ge=0, le=100)
    policy_compliance: float = Field(ge=0, le=100)


class VerificationStatus(BaseModel):
    """Upload verification status."""
    thumbnail_verified: bool = False
    metadata_verified: bool = False
    processing_status: str = "pending"
    estimated_processing_time_min: int = 5


class MetricsBaseline(BaseModel):
    """Initial metrics baseline for comparison."""
    impressions_first_hour: int = 0
    views_first_hour: int = 0
    ctr_first_hour: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class YouTubeUploadResponse(BaseModel):
    """YouTube upload response."""
    execution_id: str
    video_id: str
    status: str = Field(pattern="^(uploaded|scheduled|processing|failed)$")
    publish_at_iso: Optional[str] = None
    errors: Optional[list[str]] = None

    # Enhanced fields
    transaction_id: str
    upload_duration_ms: int
    quality_scores: Optional[QualityScores] = None
    platform_ids: dict[str, str] = Field(default_factory=dict)
    verification_status: Optional[VerificationStatus] = None
    rollback_available_until_iso: Optional[str] = None
    metrics_baseline: Optional[MetricsBaseline] = None


# Phase 7: Analytics & Optimization Schemas

class TimeWindow(BaseModel):
    """Analytics time window."""
    start_iso: str
    end_iso: str


class RetentionPoint(BaseModel):
    """Audience retention data point."""
    second: int
    pct_viewing: float = Field(ge=0, le=100)


class TrafficSource(BaseModel):
    """Traffic source breakdown."""
    source: str
    views: int
    ctr: Optional[float] = None
    avg_view_duration: Optional[float] = None


class Geography(BaseModel):
    """Geographic breakdown."""
    country: str
    views: int
    avg_view_duration: Optional[float] = None


class KPIMetrics(BaseModel):
    """Key performance indicators."""
    impressions: int
    views: int
    ctr: float = Field(ge=0, le=100)
    avg_view_duration_sec: float
    avg_percentage_viewed: float = Field(ge=0, le=100)
    watch_time_hours: float


class Anomaly(BaseModel):
    """Performance anomaly detection."""
    metric: str
    timestamp: str
    expected_value: float
    actual_value: float
    severity: str = Field(pattern="^(low|medium|high)$")
    probable_cause: str


class PerformancePredictions(BaseModel):
    """Performance predictions."""
    views_7d: int
    views_30d: int
    revenue_30d: float
    confidence: float = Field(ge=0, le=1)
    factors: list[str]


class EngagementAnalysis(BaseModel):
    """Engagement pattern analysis."""
    peak_engagement_times: list[tuple[int, float]]  # (second, engagement_rate)
    drop_off_points: list[tuple[int, float, str]]  # (second, drop_rate, reason)
    replay_segments: list[tuple[int, int]]  # Most replayed segments
    engagement_score: float = Field(ge=0, le=100)


class MonetizationMetrics(BaseModel):
    """Monetization performance metrics."""
    estimated_revenue: float
    rpm: float
    cpm: float
    ad_impressions: int
    ad_click_rate: float
    viewer_demographics: dict[str, Any]


class AnalyticsRequest(BaseModel):
    """Analytics fetch request."""
    video_id: str
    lookback_days: int = 28
    granularity: str = Field(default="daily", pattern="^(daily|hourly|lifetime)$")

    # Enhanced fields
    metrics: Optional[list[str]] = None
    dimensions: Optional[list[str]] = None
    filters: Optional[dict[str, Any]] = None
    compare_to: Optional[str] = None
    include_predictions: bool = False
    include_anomalies: bool = False


class EnhancedAnalyticsSnapshot(BaseModel):
    """Enhanced analytics snapshot with predictions."""
    video_id: str
    time_window: TimeWindow
    kpis: KPIMetrics
    retention_curve: list[RetentionPoint]
    traffic_sources: list[TrafficSource]
    top_geographies: list[Geography]

    # Enhanced fields
    performance_score: float = Field(ge=0, le=100)
    anomalies: Optional[list[Anomaly]] = None
    predictions: Optional[PerformancePredictions] = None
    comparative_analysis: Optional[dict[str, Any]] = None
    engagement_patterns: Optional[EngagementAnalysis] = None
    monetization_metrics: Optional[MonetizationMetrics] = None


class ExperimentVariant(BaseModel):
    """Experiment variant configuration."""
    variant_id: str
    name: str
    changes: dict[str, Any]
    weight: float = Field(ge=0, le=1)
    original_state: Optional[dict[str, Any]] = None


class TrafficAllocation(BaseModel):
    """Experiment traffic allocation."""
    method: str = Field(pattern="^(random|deterministic|progressive)$")
    ramp_up_hours: int = 0
    target_impressions_per_variant: int = 1000


class StatisticalConfig(BaseModel):
    """Experiment statistical configuration."""
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    minimum_sample_size: int = 1000
    test_type: str = Field(default="bayesian", pattern="^(frequentist|bayesian)$")
    early_stopping_enabled: bool = True


class RolloutStage(BaseModel):
    """Experiment rollout stage."""
    percentage: int = Field(ge=0, le=100)
    duration_hours: int
    success_gate: dict[str, float]


class RolloutStrategy(BaseModel):
    """Experiment rollout strategy."""
    strategy: str = Field(pattern="^(immediate|progressive|scheduled)$")
    stages: list[RolloutStage]


class SuccessCriteria(BaseModel):
    """Experiment success criteria."""
    primary_metric: str
    minimum_lift: float
    guardrail_metrics: dict[str, float]


class MultiVariantExperiment(BaseModel):
    """Multi-variant experiment configuration."""
    id: str
    video_id: str
    hypothesis: str
    kpi: str
    target_delta_pct: float
    priority: int = Field(ge=1, le=10)

    variants: list[ExperimentVariant]
    allocation: TrafficAllocation
    statistical_config: StatisticalConfig
    rollout_strategy: RolloutStrategy
    success_criteria: SuccessCriteria

    status: str = Field(default="pending", pattern="^(pending|running|completed|failed|rolled_back)$")
    created_at: datetime = Field(default_factory=datetime.now)


class ExperimentResult(BaseModel):
    """Experiment execution result."""
    experiment_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    stage_results: list[dict[str, Any]] = Field(default_factory=list)
    analysis: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    failure_reason: Optional[str] = None