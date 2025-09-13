"""Production phase modules for video creation."""

# Import with error handling for missing dependencies
try:
    from .tts import (
        TTSProcessor,
        chunk_script,
        synthesize_chunks,
        merge_audio,
        voiceover_for_slug,
    )
except ImportError:
    TTSProcessor = None
    chunk_script = None
    synthesize_chunks = None
    merge_audio = None
    voiceover_for_slug = None

try:
    from .subtitles import (
        SubtitleGenerator,
        srt_from_sections,
        vtt_from_sections,
        write_subtitles_for_slug,
    )
except ImportError:
    SubtitleGenerator = None
    srt_from_sections = None
    vtt_from_sections = None
    write_subtitles_for_slug = None

try:
    from .assets import (
        AssetManager,
        AssetManifest,
        plan_assets_for_slug,
        download_assets,
        write_attribution,
    )
except ImportError:
    AssetManager = None
    AssetManifest = None
    plan_assets_for_slug = None
    download_assets = None
    write_attribution = None

try:
    from .timeline import (
        Timeline,
        TimelineScene,
        TimelineBuilder,
        validate_timeline,
        infer_timeline_from_script,
        verify_assets_for_timeline,
    )
except ImportError:
    Timeline = None
    TimelineScene = None
    TimelineBuilder = None
    validate_timeline = None
    infer_timeline_from_script = None
    verify_assets_for_timeline = None

__all__ = [
    # TTS
    "TTSProcessor",
    "chunk_script",
    "synthesize_chunks",
    "merge_audio",
    "voiceover_for_slug",
    # Subtitles
    "SubtitleGenerator",
    "srt_from_sections",
    "vtt_from_sections",
    "write_subtitles_for_slug",
    # Assets
    "AssetManager",
    "AssetManifest",
    "plan_assets_for_slug",
    "download_assets",
    "write_attribution",
    # Timeline
    "Timeline",
    "TimelineScene",
    "TimelineBuilder",
    "validate_timeline",
    "infer_timeline_from_script",
    "verify_assets_for_timeline",
]