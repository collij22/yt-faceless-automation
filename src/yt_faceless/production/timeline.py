"""Timeline generation and validation for video assembly."""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

from ..core.config import AppConfig
from ..core.errors import TimelineError, ValidationError
from ..core.schemas import ScriptSection
from .scene_analyzer import SceneAnalyzer, SceneSegment

logger = logging.getLogger(__name__)


@dataclass
class VisualAsset:
    """Represents a visual asset (image/video) for use in timeline."""
    path: Path
    title: str
    creator: Optional[str] = None
    license: Optional[str] = None
    source_url: Optional[str] = None
    attribution: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # For videos
    content_hash: Optional[str] = None  # For deduplication
    asset_type: Literal["image", "video"] = "image"


@dataclass
class ZoomPanEffect:
    """Ken Burns zoom/pan effect parameters."""
    zoom_start: float = 1.0  # Starting zoom level (1.0 = no zoom)
    zoom_end: float = 1.1  # Ending zoom level
    pan_x_start: float = 0.5  # Starting X position (0-1)
    pan_x_end: float = 0.5  # Ending X position
    pan_y_start: float = 0.5  # Starting Y position (0-1)
    pan_y_end: float = 0.5  # Ending Y position
    duration_frames: int = 150  # Effect duration in frames


@dataclass
class VisualShot:
    """Represents a single visual shot within a scene."""
    asset: VisualAsset
    start_time: float  # Start time relative to scene
    duration: float  # Shot duration
    kenburns_effect: Optional[ZoomPanEffect] = None
    transition_in: Optional[str] = None
    transition_out: Optional[str] = None
    transition_duration: float = 0.5
    overlay_text: Optional[str] = None
    overlay_position: str = "bottom"


@dataclass
class SceneSpec:
    """Complete specification for a scene with visuals."""
    scene_id: str
    scene_index: int
    start_time: float  # Absolute time in video
    end_time: float
    duration: float
    key_phrase: Optional[str] = None
    shots: List[VisualShot] = field(default_factory=list)
    audio_duck: bool = False  # Duck music during important narration
    scene_type: Optional[str] = None  # hook, explanation, proof, etc.


class TimelineScene(TypedDict):
    """Individual scene in video timeline."""
    scene_id: str
    clip_path: str  # Path to video/image file
    start_time: float  # Scene start in timeline (seconds)
    end_time: float  # Scene end in timeline
    source_start: float  # Start time in source clip
    source_end: float  # End time in source clip
    transition: Optional[str]  # Transition type (fade, wipe, dissolve, etc.)
    transition_duration: float  # Transition duration (seconds)
    zoom_pan: Optional[ZoomPanEffect]  # Ken Burns effect
    overlay_text: Optional[str]  # Text overlay
    overlay_position: Optional[str]  # Text position (top, bottom, center)
    audio_duck: bool  # Whether to duck music during this scene
    effects: List[str]  # Additional effects (blur, grayscale, etc.)


class Timeline(TypedDict):
    """Complete video timeline specification."""
    version: int
    slug: str
    width: int
    height: int
    fps: int
    total_duration: float  # Total video duration in seconds
    scenes: List[TimelineScene]
    music_track: Optional[str]  # Path to background music
    music_volume: float  # Music volume (0-1)
    narration_track: str  # Path to narration audio
    burn_subtitles: bool  # Whether to burn subtitles
    subtitle_path: Optional[str]  # Path to subtitle file
    loudness_target: int  # Target LUFS for normalization
    output_format: str  # Output format (mp4, webm, etc.)


class TimelineBuilder:
    """Builds and validates video timelines."""

    # Available transitions
    TRANSITIONS = [
        "fade", "fadeblack", "fadewhite",
        "wipeleft", "wiperight", "wipeup", "wipedown",
        "slideleft", "slideright", "slideup", "slidedown",
        "dissolve", "pixelize", "radial", "circleopen", "circleclose"
    ]

    # Default settings
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    DEFAULT_FPS = 30
    DEFAULT_TRANSITION_DURATION = 0.5
    DEFAULT_MUSIC_VOLUME = 0.2
    DEFAULT_LOUDNESS = -14  # YouTube standard

    def __init__(self, config: AppConfig):
        self.config = config

    def build_advanced_timeline(
        self,
        slug: str,
        scene_specs: List[SceneSpec],
        music_track: Optional[str] = None,
        narration_track: Optional[str] = None,
        **kwargs
    ) -> Timeline:
        """Build an advanced timeline from scene specifications.

        Args:
            slug: Content slug identifier
            scene_specs: List of scene specifications with shots
            music_track: Optional background music path
            narration_track: Optional narration audio path
            **kwargs: Additional timeline parameters

        Returns:
            Complete timeline specification
        """
        # Convert SceneSpecs to TimelineScenes
        timeline_scenes = []

        for spec in scene_specs:
            # Process each shot in the scene
            for i, shot in enumerate(spec.shots):
                scene = TimelineScene(
                    scene_id=f"{spec.scene_id}_shot_{i}",
                    clip_path=str(shot.asset.path),
                    start_time=spec.start_time + shot.start_time,
                    end_time=spec.start_time + shot.start_time + shot.duration,
                    source_start=0,
                    source_end=shot.duration,
                    transition=shot.transition_in,
                    transition_duration=shot.transition_duration,
                    zoom_pan=shot.kenburns_effect.__dict__ if shot.kenburns_effect else None,
                    overlay_text=shot.overlay_text or spec.key_phrase,
                    overlay_position=shot.overlay_position,
                    audio_duck=spec.audio_duck,
                    effects=[]
                )
                timeline_scenes.append(scene)

        return self.build_timeline(slug, timeline_scenes, music_track, **kwargs)

    def build_timeline(
        self,
        slug: str,
        scenes: List[TimelineScene],
        music_track: Optional[str] = None,
        **kwargs
    ) -> Timeline:
        """Build a complete timeline from scenes.

        Args:
            slug: Content slug identifier
            scenes: List of scenes
            music_track: Optional background music path
            **kwargs: Additional timeline parameters

        Returns:
            Complete timeline specification
        """
        # Calculate total duration
        total_duration = max(s["end_time"] for s in scenes) if scenes else 0

        # Build timeline
        timeline = Timeline(
            version=1,
            slug=slug,
            width=kwargs.get("width", self.DEFAULT_WIDTH),
            height=kwargs.get("height", self.DEFAULT_HEIGHT),
            fps=kwargs.get("fps", self.DEFAULT_FPS),
            total_duration=total_duration,
            scenes=scenes,
            music_track=music_track,
            music_volume=kwargs.get("music_volume", self.DEFAULT_MUSIC_VOLUME),
            narration_track=kwargs.get("narration_track", ""),
            burn_subtitles=kwargs.get("burn_subtitles", False),
            subtitle_path=kwargs.get("subtitle_path"),
            loudness_target=kwargs.get("loudness_target", self.DEFAULT_LOUDNESS),
            output_format=kwargs.get("output_format", "mp4")
        )

        # Validate timeline
        validate_timeline(timeline)

        return timeline


def validate_timeline(timeline: Timeline) -> None:
    """Validate timeline for consistency and correctness.

    Args:
        timeline: Timeline to validate

    Raises:
        ValidationError: If timeline is invalid
    """
    errors = []

    # Check basic parameters
    if timeline["width"] <= 0 or timeline["height"] <= 0:
        errors.append("Invalid resolution")

    if timeline["fps"] <= 0:
        errors.append("Invalid frame rate")

    if timeline["total_duration"] <= 0:
        errors.append("Invalid total duration")

    # Check scenes
    if not timeline["scenes"]:
        errors.append("No scenes in timeline")

    previous_end = 0
    for i, scene in enumerate(timeline["scenes"]):
        # Check timing
        if scene["start_time"] < 0:
            errors.append(f"Scene {i}: Negative start time")

        if scene["end_time"] <= scene["start_time"]:
            errors.append(f"Scene {i}: End time before start time")

        # Check for gaps (warning, not error)
        if scene["start_time"] > previous_end + 0.1:
            logger.warning(f"Gap detected between scenes at {previous_end:.2f}s")

        previous_end = scene["end_time"]

        # Check file paths
        clip_path = Path(scene["clip_path"])
        if not clip_path.exists() and not clip_path.is_absolute():
            # Try relative to assets directory
            assets_path = Path("assets") / timeline["slug"] / scene["clip_path"]
            if not assets_path.exists():
                errors.append(f"Scene {i}: Clip not found: {scene['clip_path']}")

        # Check transition
        if scene.get("transition"):
            if scene["transition"] not in TimelineBuilder.TRANSITIONS:
                errors.append(f"Scene {i}: Invalid transition: {scene['transition']}")

        # Check zoom/pan effect
        if scene.get("zoom_pan"):
            zp = scene["zoom_pan"]
            if zp["zoom_start"] <= 0 or zp["zoom_end"] <= 0:
                errors.append(f"Scene {i}: Invalid zoom values")
            if not (0 <= zp["pan_x_start"] <= 1 and 0 <= zp["pan_x_end"] <= 1):
                errors.append(f"Scene {i}: Pan X values out of range")
            if not (0 <= zp["pan_y_start"] <= 1 and 0 <= zp["pan_y_end"] <= 1):
                errors.append(f"Scene {i}: Pan Y values out of range")

    # Check audio tracks
    if timeline.get("narration_track"):
        narration_path = Path(timeline["narration_track"])
        if not narration_path.exists() and not narration_path.is_absolute():
            content_path = Path("content") / timeline["slug"] / "audio.wav"
            if not content_path.exists():
                errors.append(f"Narration track not found: {timeline['narration_track']}")

    if timeline.get("music_track"):
        music_path = Path(timeline["music_track"])
        if not music_path.exists() and not music_path.is_absolute():
            assets_path = Path("assets") / timeline["slug"] / "music" / Path(timeline["music_track"]).name
            if not assets_path.exists():
                errors.append(f"Music track not found: {timeline['music_track']}")

    if timeline.get("burn_subtitles") and timeline.get("subtitle_path"):
        subtitle_path = Path(timeline["subtitle_path"])
        if not subtitle_path.exists():
            errors.append(f"Subtitle file not found: {timeline['subtitle_path']}")

    # Raise validation error if any issues found
    if errors:
        raise ValidationError(f"Timeline validation failed: {'; '.join(errors)}")


def build_visual_timeline(
    cfg: AppConfig,
    slug: str,
    use_scene_analysis: bool = True,
    auto_transitions: bool = True,
    ken_burns: bool = True
) -> Timeline:
    """Build a visual timeline with dynamic scene-based composition.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        use_scene_analysis: Whether to use scene analyzer
        auto_transitions: Whether to add automatic transitions
        ken_burns: Whether to add Ken Burns effects to images

    Returns:
        Generated timeline with visual shots
    """
    content_dir = cfg.directories.content_dir / slug
    assets_dir = cfg.directories.assets_dir / slug

    # Load metadata and manifest
    metadata_path = content_dir / "metadata.json"
    manifest_path = assets_dir / "manifest.json"
    script_path = content_dir / "script.md"
    audio_path = content_dir / "audio.wav"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text())

    # Load asset manifest
    assets = []
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assets = manifest.get("assets", [])

    # Analyze script into scenes if requested
    if use_scene_analysis and script_path.exists():
        from .scene_analyzer import SceneAnalyzer
        analyzer = SceneAnalyzer()
        script_text = script_path.read_text()

        # Get audio duration if available
        audio_duration = None
        if audio_path.exists():
            # Use ffprobe to get actual duration for perfect sync
            try:
                import subprocess
                import json as json_lib
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(audio_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    data = json_lib.loads(result.stdout)
                    if 'format' in data and 'duration' in data['format']:
                        audio_duration = float(data['format']['duration'])
                        logger.info(f"Got audio duration from ffprobe: {audio_duration:.2f}s")
            except Exception as e:
                logger.warning(f"Failed to get audio duration with ffprobe: {e}, using estimate")
                # Fallback to word count estimate
                word_count = len(script_text.split())
                audio_duration = (word_count / 150) * 60

        scene_segments = analyzer.analyze_script(script_text, metadata, audio_duration)
    else:
        # Fall back to metadata sections
        scene_segments = _segments_from_metadata(metadata)

    # Build scene specifications with visual shots
    scene_specs = _build_scene_specs(
        scene_segments,
        assets,
        auto_transitions,
        ken_burns,
        cfg.video.fps  # Pass the configured FPS for Ken Burns effects
    )

    # Get music track
    music_track = None
    music_assets = [a for a in assets if a.get("type") == "music"]
    if music_assets:
        music_track = music_assets[0].get("local_path")

    # Build timeline
    builder = TimelineBuilder(cfg)
    timeline = builder.build_advanced_timeline(
        slug=slug,
        scene_specs=scene_specs,
        music_track=music_track,
        narration_track=str(audio_path) if audio_path.exists() else None,
        burn_subtitles=cfg.features.get("auto_subtitles", True),
        subtitle_path=str(content_dir / "subtitles.srt") if (content_dir / "subtitles.srt").exists() else None,
        width=cfg.video.width,
        height=cfg.video.height,
        fps=cfg.video.fps
    )

    # Save timeline
    timeline_path = content_dir / "timeline.json"
    with open(timeline_path, "w") as f:
        json.dump(timeline, f, indent=2)

    logger.info(f"Generated visual timeline with {len(scene_specs)} scenes for {slug}")
    return timeline


def _segments_from_metadata(metadata: Dict[str, Any]) -> List[SceneSegment]:
    """Convert metadata sections to scene segments."""
    from .scene_analyzer import SceneSegment
    segments = []

    for i, section in enumerate(metadata.get("sections", [])):
        segment = SceneSegment(
            index=i,
            start_time=section.get("start_time", 0),
            end_time=section.get("end_time", 0),
            duration=section.get("end_time", 0) - section.get("start_time", 0),
            text=section.get("text", ""),
            section_marker=section.get("type"),
            keywords=[],
            search_queries=[],
            key_phrase=None,
            visual_cues=section.get("visual_cues", []),
            b_roll_suggestions=section.get("b_roll_suggestions", [])
        )
        segments.append(segment)

    return segments


def _build_scene_specs(
    segments: List[SceneSegment],
    assets: List[Dict[str, Any]],
    auto_transitions: bool,
    ken_burns: bool,
    fps: int = 30
) -> List[SceneSpec]:
    """Build scene specifications with visual shots."""
    scene_specs = []

    # Convert assets to VisualAsset objects
    visual_assets = []
    for asset in assets:
        if asset.get("type") in ["image", "video"]:
            va = VisualAsset(
                path=Path(asset["local_path"]) if asset.get("local_path") else Path(asset["url"]),
                title=asset.get("title", "Untitled"),
                creator=asset.get("creator"),
                license=asset.get("license"),
                source_url=asset.get("source_url"),
                attribution=asset.get("attribution"),
                width=asset.get("width"),
                height=asset.get("height"),
                duration=asset.get("duration_seconds"),
                content_hash=asset.get("sha256"),
                asset_type=asset.get("type", "image")
            )
            visual_assets.append(va)

    # Generate fallback visuals if no assets found
    if not visual_assets:
        logger.warning("No visual assets found, generating fallback visuals")
        from .fallbacks import VisualFallbackGenerator

        generator = VisualFallbackGenerator()
        visual_assets = []

        # Generate unique fallbacks for different scene types
        scene_types = set(s.section_marker for s in segments if s.section_marker)
        if not scene_types:
            scene_types = {"default"}

        # Create a pool of fallback assets
        for i, scene_type in enumerate(scene_types):
            for j in range(3):  # 3 variations per scene type
                fallback_path = generator.generate_gradient_card(
                    text=f"{scene_type.replace('_', ' ').title()}",
                    scene_type=scene_type.lower() if scene_type else "default",
                    seed=i * 10 + j
                )

                fallback_asset = VisualAsset(
                    path=fallback_path,
                    title=f"Fallback {scene_type} {j+1}",
                    creator="System",
                    license="cc0",
                    source_url="",
                    width=1920,
                    height=1080,
                    asset_type="image"
                )
                visual_assets.append(fallback_asset)

        logger.info(f"Generated {len(visual_assets)} fallback visuals")

    # Assign shots to each scene
    for segment in segments:
        spec = SceneSpec(
            scene_id=f"scene_{segment.index}",
            scene_index=segment.index,
            start_time=segment.start_time,
            end_time=segment.end_time,
            duration=segment.duration,
            key_phrase=segment.key_phrase,
            scene_type=segment.section_marker
        )

        # Determine number of shots based on duration
        if segment.duration <= 7:
            num_shots = 1
        elif segment.duration <= 15:
            num_shots = 2
        else:
            num_shots = min(3, int(segment.duration / 8))

        shot_duration = segment.duration / num_shots

        # Select assets for this scene
        selected_assets = _select_assets_for_scene(
            segment,
            visual_assets,
            num_shots
        )

        # Create shots
        for i in range(num_shots):
            asset = selected_assets[i % len(selected_assets)] if selected_assets else visual_assets[0]

            shot = VisualShot(
                asset=asset,
                start_time=i * shot_duration,
                duration=shot_duration,
                overlay_text=segment.key_phrase if i == 0 else None
            )

            # Add Ken Burns to images
            if ken_burns and asset.asset_type == "image":
                shot.kenburns_effect = _generate_dynamic_ken_burns(
                    shot_duration,
                    fps,  # Use the fps parameter passed to the function
                    segment.index + i
                )

            # Add transitions
            if auto_transitions:
                if i > 0:
                    shot.transition_in = _select_transition(segment.scene_type)
                if i == num_shots - 1 and segment.index < len(segments) - 1:
                    shot.transition_out = _select_transition(segment.scene_type)

            spec.shots.append(shot)

        scene_specs.append(spec)

    return scene_specs


def _select_assets_for_scene(
    segment: SceneSegment,
    available_assets: List[VisualAsset],
    num_needed: int
) -> List[VisualAsset]:
    """Select appropriate assets for a scene with smart scoring."""
    if not available_assets:
        # Generate fallbacks if no assets available
        from .fallbacks import ensure_minimum_assets
        return ensure_minimum_assets([], num_needed, segment.section_marker)

    # Build search terms for matching
    search_terms = set()
    if segment.keywords:
        search_terms.update(term.lower() for term in segment.keywords)
    if segment.search_queries:
        search_terms.update(query.lower() for query in segment.search_queries)
    if segment.visual_cues:
        search_terms.update(cue.lower() for cue in segment.visual_cues)
    if segment.section_marker:
        search_terms.add(segment.section_marker.lower())

    # Score each asset
    scored_assets = []
    for asset in available_assets:
        score = 0

        # Build asset text for matching
        asset_text = asset.title.lower() if asset.title else ""

        # Check for matches
        for term in search_terms:
            if term in asset_text:
                score += 10  # Exact match
            else:
                # Check word-level matches
                term_words = term.split()
                asset_words = asset_text.split()
                matches = sum(1 for tw in term_words if any(tw in aw for aw in asset_words))
                score += matches * 3

        # Quality bonus for high resolution
        if asset.width and asset.width >= 1920:
            score += 5
        elif asset.width and asset.width >= 1280:
            score += 2

        # License preference (prefer CC0/PD)
        if asset.license and asset.license.lower() in ['cc0', 'pd', 'publicdomain']:
            score += 3

        scored_assets.append((score, asset))

    # Sort by score (highest first)
    scored_assets.sort(key=lambda x: x[0], reverse=True)

    # Select with creator diversity
    selected = []
    used_creators = set()

    for score, asset in scored_assets:
        if len(selected) >= num_needed:
            break

        # Prefer diverse creators for variety
        creator = asset.creator or "unknown"
        if creator not in used_creators or len(selected) < num_needed // 2:
            selected.append(asset)
            used_creators.add(creator)

    # Fill remaining slots if needed
    if len(selected) < num_needed:
        remaining = [asset for _, asset in scored_assets if asset not in selected]
        selected.extend(remaining[:num_needed - len(selected)])

    # Generate fallbacks if still not enough
    if len(selected) < num_needed:
        from .fallbacks import ensure_minimum_assets
        selected = ensure_minimum_assets(selected, num_needed, segment.section_marker)

    return selected


def _generate_dynamic_ken_burns(
    duration: float,
    fps: int,
    seed: int
) -> ZoomPanEffect:
    """Generate varied Ken Burns effects."""
    random.seed(seed)  # Reproducible randomness

    # Alternate between zoom in/out
    zoom_in = seed % 2 == 0

    if zoom_in:
        zoom_start = 1.0
        zoom_end = random.uniform(1.05, 1.2)
    else:
        zoom_start = random.uniform(1.05, 1.2)
        zoom_end = 1.0

    # Varied pan patterns
    pan_patterns = [
        (0.5, 0.5, 0.5, 0.5),  # Static
        (0.3, 0.5, 0.7, 0.5),  # Left to right
        (0.7, 0.5, 0.3, 0.5),  # Right to left
        (0.5, 0.3, 0.5, 0.7),  # Top to bottom
        (0.5, 0.7, 0.5, 0.3),  # Bottom to top
        (0.3, 0.3, 0.7, 0.7),  # Diagonal
        (0.7, 0.3, 0.3, 0.7),  # Reverse diagonal
    ]

    pan = random.choice(pan_patterns)

    return ZoomPanEffect(
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_x_start=pan[0],
        pan_x_end=pan[2],
        pan_y_start=pan[1],
        pan_y_end=pan[3],
        duration_frames=int(duration * fps)
    )


def _select_transition(scene_type: Optional[str]) -> str:
    """Select appropriate transition based on scene type."""
    if scene_type in ["HOOK", "TEASER"]:
        return random.choice(["fade", "fadewhite"])
    elif scene_type in ["PROOF", "DEMONSTRATION"]:
        return random.choice(["dissolve", "fade"])  # Fixed: replaced "crossfade" with "fade"
    elif scene_type in ["CTA", "OUTRO"]:
        return random.choice(["fadeblack", "fade"])
    else:
        return random.choice(["fade", "dissolve", "wipeleft", "wiperight"])


def infer_timeline_from_script(
    cfg: AppConfig,
    slug: str,
    auto_transitions: bool = True,
    ken_burns: bool = True
) -> Timeline:
    """Automatically generate timeline from script and assets.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        auto_transitions: Whether to add automatic transitions
        ken_burns: Whether to add Ken Burns effects to images

    Returns:
        Generated timeline
    """
    content_dir = cfg.directories.content_dir / slug
    assets_dir = cfg.directories.assets_dir / slug

    # Load metadata and manifest
    metadata_path = content_dir / "metadata.json"
    manifest_path = assets_dir / "manifest.json"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text())

    # Load asset manifest if exists
    assets = []
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assets = manifest.get("assets", [])

    # If still no assets, generate fallback visuals so scenes always have content
    if not assets:
        from .fallbacks import ensure_minimum_assets
        fallback_list = ensure_minimum_assets([], 12, scene_type=None)
        assets = [
            {
                "type": "image",
                "url": str(a.path),
                "local_path": str(a.path),
                "license": "cc0",
                "title": a.title,
                "tags": [],
            }
            for a in fallback_list
        ]

    # Get script sections
    sections = metadata.get("sections", [])
    if not sections:
        raise TimelineError("No script sections found in metadata")

    # Categorize assets
    video_clips = [a for a in assets if a["type"] == "video"]
    images = [a for a in assets if a["type"] == "image"]
    music_tracks = [a for a in assets if a["type"] == "music"]

    # Build scenes from sections
    scenes = []
    available_clips = video_clips + images  # Pool of visual assets

    for i, section in enumerate(sections):
        section_data = ScriptSection(**section) if isinstance(section, dict) else section

        # Select visual asset for this section
        if available_clips:
            # Try to match based on visual cues
            matched_asset = None
            for cue in section_data.visual_cues + section_data.b_roll_suggestions:
                for asset in available_clips:
                    if any(tag in cue.lower() for tag in asset.get("tags", [])):
                        matched_asset = asset
                        break
                if matched_asset:
                    break

            # If no match, pick random
            if not matched_asset:
                matched_asset = random.choice(available_clips)

            # Create scene
            scene = TimelineScene(
                scene_id=f"scene_{i}",
                clip_path=matched_asset["local_path"],
                start_time=section_data.start_time,
                end_time=section_data.end_time,
                source_start=0,
                source_end=section_data.end_time - section_data.start_time,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )

            # Add transition if not first scene
            if auto_transitions and i > 0:
                scene["transition"] = random.choice([
                    "fade", "dissolve", "wipeleft", "wiperight"
                ])

            # Add Ken Burns effect to images
            if ken_burns and matched_asset["type"] == "image":
                scene["zoom_pan"] = _generate_ken_burns_effect(
                    duration=section_data.end_time - section_data.start_time,
                    fps=cfg.video.fps
                )

            scenes.append(scene)

    # If we still have no scenes (e.g., all downloads failed), synthesize scenes from fallbacks
    if not scenes:
        from .fallbacks import ensure_minimum_assets
        fallback_assets = ensure_minimum_assets([], 12, scene_type=None)
        # Spread fallbacks over the full narration duration if available
        total = (content_dir / "audio.wav")
        total_dur = 0.0
        if total.exists():
            try:
                import subprocess, json as _json
                r = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format',str(total)], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    d = _json.loads(r.stdout)
                    total_dur = float(d.get('format',{}).get('duration',0))
            except Exception:
                pass
        # Default to 8s per scene if duration unknown
        per = 8.0 if total_dur <= 0 else max(6.0, min(12.0, total_dur / max(1, len(fallback_assets))))
        t = 0.0
        idx = 0
        while total_dur == 0 or t < total_dur:
            fa = fallback_assets[idx % len(fallback_assets)]
            scenes.append({
                "scene_id": f"fb_{idx}",
                "clip_path": str(fa.path),
                "start_time": t,
                "end_time": t + per,
                "source_start": 0,
                "source_end": per,
                "transition": "fade" if idx > 0 else None,
                "transition_duration": 0.5,
                "zoom_pan": None,
                "overlay_text": None,
                "overlay_position": None,
                "audio_duck": False,
                "effects": []
            })
            idx += 1
            t += per
            if total_dur == 0 and idx >= len(fallback_assets):
                break

    # Select background music
    music_track = None
    if music_tracks:
        music_track = music_tracks[0]["local_path"]

    # Get audio and subtitle paths
    narration_path = content_dir / "audio.wav"
    subtitle_path = content_dir / "subtitles.srt"

    # Build timeline
    builder = TimelineBuilder(cfg)
    timeline = builder.build_timeline(
        slug=slug,
        scenes=scenes,
        music_track=music_track,
        narration_track=str(narration_path) if narration_path.exists() else "",
        subtitle_path=str(subtitle_path) if subtitle_path.exists() else None,
        burn_subtitles=cfg.features.get("auto_subtitles", True),
        width=cfg.video.width,
        height=cfg.video.height,
        fps=cfg.video.fps
    )

    # Save timeline
    timeline_path = content_dir / "timeline.json"
    with open(timeline_path, "w") as f:
        json.dump(timeline, f, indent=2)

    logger.info(f"Generated timeline with {len(scenes)} scenes for {slug}")
    return timeline


def _generate_ken_burns_effect(
    duration: float,
    fps: int,
    max_zoom: float = 1.2
) -> ZoomPanEffect:
    """Generate random Ken Burns effect parameters.

    Args:
        duration: Effect duration in seconds
        fps: Frame rate
        max_zoom: Maximum zoom level

    Returns:
        Ken Burns effect parameters
    """
    # Random zoom direction
    if random.random() > 0.5:
        # Zoom in
        zoom_start = 1.0
        zoom_end = random.uniform(1.05, max_zoom)
    else:
        # Zoom out
        zoom_start = random.uniform(1.05, max_zoom)
        zoom_end = 1.0

    # Random pan direction
    pan_directions = [
        (0.5, 0.5, 0.5, 0.5),  # No pan
        (0.3, 0.5, 0.7, 0.5),  # Pan left to right
        (0.7, 0.5, 0.3, 0.5),  # Pan right to left
        (0.5, 0.3, 0.5, 0.7),  # Pan top to bottom
        (0.5, 0.7, 0.5, 0.3),  # Pan bottom to top
    ]

    pan_x_start, pan_y_start, pan_x_end, pan_y_end = random.choice(pan_directions)

    return ZoomPanEffect(
        zoom_start=zoom_start,
        zoom_end=zoom_end,
        pan_x_start=pan_x_start,
        pan_x_end=pan_x_end,
        pan_y_start=pan_y_start,
        pan_y_end=pan_y_end,
        duration_frames=int(duration * fps)
    )


def verify_assets_for_timeline(
    cfg: AppConfig,
    slug: str,
    timeline: Timeline
) -> List[str]:
    """Verify all assets referenced in timeline exist.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        timeline: Timeline to verify

    Returns:
        List of missing assets (empty if all found)
    """
    missing = []

    # Check scene clips
    for scene in timeline["scenes"]:
        clip_path = Path(scene["clip_path"])

        # Try absolute path first
        if not clip_path.exists():
            # Try relative to assets directory
            assets_path = cfg.directories.assets_dir / slug / scene["clip_path"]
            if not assets_path.exists():
                # Try relative to project root
                root_path = Path(scene["clip_path"])
                if not root_path.exists():
                    missing.append(f"Scene clip: {scene['clip_path']}")

    # Check narration track
    if timeline.get("narration_track"):
        narration_path = Path(timeline["narration_track"])
        if not narration_path.exists():
            content_path = cfg.directories.content_dir / slug / "audio.wav"
            if not content_path.exists():
                missing.append(f"Narration: {timeline['narration_track']}")

    # Check music track
    if timeline.get("music_track"):
        music_path = Path(timeline["music_track"])
        if not music_path.exists():
            assets_path = cfg.directories.assets_dir / slug / "music" / Path(timeline["music_track"]).name
            if not assets_path.exists():
                missing.append(f"Music: {timeline['music_track']}")

    # Check subtitle file
    if timeline.get("subtitle_path"):
        subtitle_path = Path(timeline["subtitle_path"])
        if not subtitle_path.exists():
            content_path = cfg.directories.content_dir / slug / Path(timeline["subtitle_path"]).name
            if not content_path.exists():
                missing.append(f"Subtitles: {timeline['subtitle_path']}")

    return missing


def write_timeline_for_slug(
    cfg: AppConfig,
    slug: str,
    timeline: Timeline
) -> Path:
    """Write timeline to file for a content slug.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        timeline: Timeline to write

    Returns:
        Path to timeline file
    """
    content_dir = cfg.directories.content_dir / slug
    content_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = content_dir / "timeline.json"

    with open(timeline_path, "w") as f:
        json.dump(timeline, f, indent=2)

    logger.info(f"Wrote timeline: {timeline_path}")
    return timeline_path


def merge_timeline_scenes(
    scenes: List[TimelineScene],
    gap_threshold: float = 0.1
) -> List[TimelineScene]:
    """Merge adjacent scenes with small gaps.

    Args:
        scenes: List of scenes to merge
        gap_threshold: Maximum gap to merge (seconds)

    Returns:
        Merged scenes list
    """
    if not scenes:
        return scenes

    merged = []
    current = scenes[0].copy()

    for scene in scenes[1:]:
        gap = scene["start_time"] - current["end_time"]

        if gap <= gap_threshold and scene["clip_path"] == current["clip_path"]:
            # Extend current scene
            current["end_time"] = scene["end_time"]
            current["source_end"] = scene["source_end"]
        else:
            # Start new scene
            merged.append(current)
            current = scene.copy()

    # Add last scene
    merged.append(current)

    return merged