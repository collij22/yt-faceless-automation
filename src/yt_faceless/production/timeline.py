"""Timeline generation and validation for video assembly."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

from ..core.config import AppConfig
from ..core.errors import TimelineError, ValidationError
from ..core.schemas import ScriptSection

logger = logging.getLogger(__name__)


class ZoomPanEffect(TypedDict):
    """Ken Burns zoom/pan effect parameters."""
    zoom_start: float  # Starting zoom level (1.0 = no zoom)
    zoom_end: float  # Ending zoom level
    pan_x_start: float  # Starting X position (0-1)
    pan_x_end: float  # Ending X position
    pan_y_start: float  # Starting Y position (0-1)
    pan_y_end: float  # Ending Y position
    duration_frames: int  # Effect duration in frames


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