"""Enhanced video assembly module with advanced filtergraph support."""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import AppConfig
from .core.config import load_config as load_enhanced_config
from .core.errors import VideoAssemblyError, ValidationError
from .logging_setup import get_logger
from .production.timeline import Timeline, TimelineScene, validate_timeline

logger = get_logger(__name__)


@dataclass(slots=True)
class ClipSpec:
    """Spec for a single video segment to concatenate."""
    path: Path
    start: float | None = None
    end: float | None = None


class FiltergraphBuilder:
    """Builds complex FFmpeg filtergraphs for advanced video assembly."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.filters = []
        self.inputs = []
        self.output_labels = {}

    def add_input(self, path: Path, label: str) -> str:
        """Add input file and return its stream labels."""
        self.inputs.append(str(path))
        return f"[{len(self.inputs)-1}:v]", f"[{len(self.inputs)-1}:a]"

    def scale_and_pad(self, input_label: str, width: int, height: int, fps: int) -> str:
        """Scale and pad video to target resolution."""
        output_label = f"[scaled_{len(self.filters)}]"

        # Scale with padding to maintain aspect ratio
        filter_str = (
            f"{input_label}scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={fps}{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def add_transition(
        self,
        input1: str,
        input2: str,
        transition_type: str,
        duration: float,
        offset: float
    ) -> str:
        """Add transition between two video streams."""
        output_label = f"[trans_{len(self.filters)}]"

        # Map transition types to xfade transitions
        transition_map = {
            "fade": "fade",
            "fadeblack": "fadeblack",
            "fadewhite": "fadewhite",
            "dissolve": "dissolve",
            "wipe": "wipeleft",
            "wipeleft": "wipeleft",
            "wiperight": "wiperight",
            "wipeup": "wipeup",
            "wipedown": "wipedown",
            "slideleft": "slideleft",
            "slideright": "slideright",
            "slideup": "slideup",
            "slidedown": "slidedown",
            "circleopen": "circleopen",
            "circleclose": "circleclose",
            "pixelize": "pixelize",
            "radial": "radial"
        }

        xfade_transition = transition_map.get(transition_type, "fade")

        filter_str = (
            f"{input1}{input2}xfade=transition={xfade_transition}:"
            f"duration={duration}:offset={offset}{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def add_zoom_pan(
        self,
        input_label: str,
        zoom_start: float,
        zoom_end: float,
        pan_x_start: float,
        pan_x_end: float,
        pan_y_start: float,
        pan_y_end: float,
        duration_frames: int,
        width: int,
        height: int
    ) -> str:
        """Add Ken Burns zoom/pan effect."""
        output_label = f"[zoompan_{len(self.filters)}]"

        # Build zoompan expression
        zoom_expr = f"'min(zoom+{(zoom_end-zoom_start)/duration_frames},1.5)'"
        x_expr = f"'iw/2+({pan_x_end-pan_x_start})*on/{duration_frames}*iw'"
        y_expr = f"'ih/2+({pan_y_end-pan_y_start})*on/{duration_frames}*ih'"

        filter_str = (
            f"{input_label}zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}:"
            f"d={duration_frames}:s={width}x{height}{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def add_text_overlay(
        self,
        input_label: str,
        text: str,
        position: str = "bottom",
        font_size: int = 48,
        font_color: str = "white"
    ) -> str:
        """Add text overlay to video."""
        output_label = f"[text_{len(self.filters)}]"

        # Escape text for FFmpeg
        escaped_text = text.replace("'", "\\'").replace(":", "\\:")

        # Position mapping
        position_map = {
            "top": "x=(w-text_w)/2:y=50",
            "bottom": "x=(w-text_w)/2:y=h-100",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "topleft": "x=50:y=50",
            "topright": "x=w-text_w-50:y=50",
            "bottomleft": "x=50:y=h-100",
            "bottomright": "x=w-text_w-50:y=h-100"
        }

        pos_expr = position_map.get(position, position_map["bottom"])

        filter_str = (
            f"{input_label}drawtext=text='{escaped_text}':"
            f"fontsize={font_size}:fontcolor={font_color}:"
            f"{pos_expr}:shadowcolor=black:shadowx=2:shadowy=2{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def add_subtitles(self, input_label: str, subtitle_path: Path) -> str:
        """Burn subtitles into video."""
        output_label = f"[subs_{len(self.filters)}]"

        # Escape path for FFmpeg
        escaped_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:")

        filter_str = (
            f"{input_label}subtitles='{escaped_path}':"
            f"force_style='FontName=Arial,FontSize=22,PrimaryColour=&HFFFFFF,"
            f"OutlineColour=&H000000,BorderStyle=1,Outline=2'{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def mix_audio(
        self,
        narration_label: str,
        music_label: Optional[str] = None,
        music_volume: float = 0.2
    ) -> str:
        """Mix narration with optional background music."""
        if music_label:
            # Duck music under narration using sidechain compression
            output_label = f"[mixed_audio]"

            # First, adjust music volume
            music_adjusted = f"[music_vol]"
            self.filters.append(
                f"{music_label}volume={music_volume}{music_adjusted}"
            )

            # Apply sidechain compression to duck music when narration is present
            # Use narration as the sidechain source to control music ducking
            filter_str = (
                f"{music_adjusted}{narration_label}sidechaincompress="
                f"threshold=0.02:ratio=5:attack=0.1:release=0.2[ducked_music];"
                f"[ducked_music]{narration_label}amix=inputs=2:duration=longest{output_label}"
            )

            self.filters.append(filter_str)
            return output_label
        else:
            # Just use narration
            return narration_label

    def normalize_loudness(self, input_label: str, target_lufs: int = -14) -> str:
        """Normalize audio loudness to target LUFS."""
        output_label = f"[normalized]"

        filter_str = (
            f"{input_label}loudnorm=I={target_lufs}:TP=-1.5:LRA=11{output_label}"
        )

        self.filters.append(filter_str)
        return output_label

    def build(self) -> List[str]:
        """Build complete filtergraph arguments."""
        if not self.filters:
            return []

        # Join all filters with semicolons
        filtergraph = ";".join(self.filters)

        return ["-filter_complex", filtergraph]


def run_ffmpeg(ffmpeg_bin: str, args: Sequence[str], show_progress: bool = True) -> None:
    """Run ffmpeg with provided args and robust error handling."""
    cmd = [ffmpeg_bin, *args]
    logger.info("Running: %s", " ".join(shlex.quote(c) for c in cmd))

    try:
        if show_progress:
            # Show FFmpeg progress
            subprocess.run(cmd, check=True)
        else:
            # Hide output
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found; set FFMPEG_BIN or install ffmpeg") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed with exit code {exc.returncode}") from exc


def probe_media_file(ffmpeg_bin: str, file_path: Path) -> Dict[str, Any]:
    """Probe media file for metadata using ffprobe.

    Args:
        ffmpeg_bin: Path to ffmpeg/ffprobe binary
        file_path: Path to media file

    Returns:
        Media metadata dictionary
    """
    # Use ffprobe (usually in same directory as ffmpeg)
    ffprobe_bin = ffmpeg_bin.replace("ffmpeg", "ffprobe")

    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        metadata = json.loads(result.stdout)

        # Extract useful information
        info = {
            "duration": float(metadata.get("format", {}).get("duration", 0)),
            "width": None,
            "height": None,
            "fps": None,
            "has_audio": False,
            "has_video": False
        }

        for stream in metadata.get("streams", []):
            if stream["codec_type"] == "video":
                info["has_video"] = True
                info["width"] = stream.get("width")
                info["height"] = stream.get("height")

                # Calculate FPS
                if "r_frame_rate" in stream:
                    num, den = map(int, stream["r_frame_rate"].split("/"))
                    info["fps"] = num / den if den > 0 else 0

            elif stream["codec_type"] == "audio":
                info["has_audio"] = True

        return info

    except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to probe {file_path}: {e}")
        return {}


def build_filtergraph(
    cfg: AppConfig,
    timeline: Timeline,
    narration_path: Path,
    music_path: Optional[Path] = None,
    subtitle_path: Optional[Path] = None
) -> Tuple[List[str], List[str], str, str]:
    """Build advanced filtergraph for timeline-based assembly.

    Args:
        cfg: Application configuration
        timeline: Video timeline specification
        narration_path: Path to narration audio
        music_path: Optional background music
        subtitle_path: Optional subtitles to burn in

    Returns:
        Tuple of (input_args, filter_args, video_output_label, audio_output_label)
    """
    builder = FiltergraphBuilder(cfg)

    # Collect unique input files
    input_files = []
    input_map = {}  # Map file path to input index

    # Add scene clips
    for scene in timeline["scenes"]:
        clip_path = Path(scene["clip_path"])
        if not clip_path.is_absolute():
            # Try relative paths
            clip_path = cfg.directories.assets_dir / timeline["slug"] / scene["clip_path"]

        if str(clip_path) not in input_map:
            input_map[str(clip_path)] = len(input_files)
            input_files.append(str(clip_path))

    # Add audio inputs
    narration_idx = len(input_files)
    input_files.append(str(narration_path))

    if music_path:
        music_idx = len(input_files)
        input_files.append(str(music_path))

    # Build input arguments
    input_args = []
    for file_path in input_files:
        input_args.extend(["-i", file_path])

    # Process scenes
    scene_outputs = []

    for i, scene in enumerate(timeline["scenes"]):
        clip_path = Path(scene["clip_path"])
        if not clip_path.is_absolute():
            clip_path = cfg.directories.assets_dir / timeline["slug"] / scene["clip_path"]

        input_idx = input_map[str(clip_path)]
        video_label = f"[{input_idx}:v]"

        # Trim if needed
        if scene["source_start"] > 0 or scene["source_end"] < scene["end_time"] - scene["start_time"]:
            trim_label = f"[trim_{i}]"
            trim_filter = (
                f"{video_label}trim=start={scene['source_start']}:"
                f"end={scene['source_end']},setpts=PTS-STARTPTS{trim_label}"
            )
            builder.filters.append(trim_filter)
            video_label = trim_label

        # Scale and pad
        video_label = builder.scale_and_pad(
            video_label,
            timeline["width"],
            timeline["height"],
            timeline["fps"]
        )

        # Apply zoom/pan if specified
        if scene.get("zoom_pan"):
            zp = scene["zoom_pan"]
            video_label = builder.add_zoom_pan(
                video_label,
                zp["zoom_start"],
                zp["zoom_end"],
                zp["pan_x_start"],
                zp["pan_x_end"],
                zp["pan_y_start"],
                zp["pan_y_end"],
                zp["duration_frames"],
                timeline["width"],
                timeline["height"]
            )

        # Add text overlay if specified
        if scene.get("overlay_text"):
            video_label = builder.add_text_overlay(
                video_label,
                scene["overlay_text"],
                scene.get("overlay_position", "bottom")
            )

        scene_outputs.append(video_label)

    # Concatenate scenes with transitions
    if len(scene_outputs) > 1:
        current_output = scene_outputs[0]

        for i in range(1, len(scene_outputs)):
            scene = timeline["scenes"][i]

            if scene.get("transition"):
                # Calculate offset for transition
                offset = timeline["scenes"][i-1]["end_time"] - scene["transition_duration"]

                current_output = builder.add_transition(
                    current_output,
                    scene_outputs[i],
                    scene["transition"],
                    scene["transition_duration"],
                    offset
                )
            else:
                # Simple concatenation
                concat_label = f"[concat_{i}]"
                concat_filter = f"{current_output}{scene_outputs[i]}concat=n=2:v=1:a=0{concat_label}"
                builder.filters.append(concat_filter)
                current_output = concat_label

        video_output = current_output
    else:
        video_output = scene_outputs[0] if scene_outputs else "[0:v]"

    # Add subtitles if requested
    if timeline.get("burn_subtitles") and subtitle_path:
        video_output = builder.add_subtitles(video_output, subtitle_path)

    # Process audio
    narration_label = f"[{narration_idx}:a]"

    if music_path:
        music_label = f"[{music_idx}:a]"
        audio_output = builder.mix_audio(
            narration_label,
            music_label,
            timeline.get("music_volume", 0.2)
        )
    else:
        audio_output = narration_label

    # Normalize loudness
    audio_output = builder.normalize_loudness(
        audio_output,
        timeline.get("loudness_target", -14)
    )

    # Build filter arguments
    filter_args = builder.build()

    return input_args, filter_args, video_output, audio_output


def assemble_from_timeline(
    cfg: AppConfig,
    slug: str,
    timeline: Optional[Timeline] = None,
    burn_subtitles: Optional[bool] = None,
    music_gain_db: float = -16.0,
    output_path: Optional[Path] = None
) -> Path:
    """Assemble video from timeline specification.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        timeline: Timeline specification (loaded from file if None)
        burn_subtitles: Override timeline subtitle burning setting
        music_gain_db: Music gain adjustment in dB
        output_path: Output file path (default: content/{slug}/final.mp4)

    Returns:
        Path to assembled video
    """
    # Load enhanced config for paths
    enhanced_cfg = load_enhanced_config()

    content_dir = enhanced_cfg.directories.content_dir / slug

    # Load timeline if not provided
    if timeline is None:
        timeline_path = content_dir / "timeline.json"
        if not timeline_path.exists():
            raise FileNotFoundError(f"Timeline not found: {timeline_path}")

        with open(timeline_path) as f:
            timeline = json.load(f)

    # Validate timeline
    validate_timeline(timeline)

    # Set paths
    narration_path = content_dir / "audio.wav"
    if not narration_path.exists():
        raise FileNotFoundError(f"Narration not found: {narration_path}")

    subtitle_path = None
    if burn_subtitles or (burn_subtitles is None and timeline.get("burn_subtitles")):
        subtitle_path = content_dir / "subtitles.srt"
        if not subtitle_path.exists():
            subtitle_path = content_dir / "subtitles.vtt"

        if not subtitle_path.exists():
            logger.warning("Subtitles requested but not found")
            subtitle_path = None

    music_path = None
    if timeline.get("music_track"):
        music_path = Path(timeline["music_track"])
        if not music_path.is_absolute():
            music_path = enhanced_cfg.directories.assets_dir / slug / "music" / music_path.name

        if not music_path.exists():
            logger.warning(f"Music track not found: {music_path}")
            music_path = None

    # Set output path
    if output_path is None:
        output_path = content_dir / "final.mp4"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build filtergraph
    input_args, filter_args, video_label, audio_label = build_filtergraph(
        cfg,
        timeline,
        narration_path,
        music_path,
        subtitle_path
    )

    # Build FFmpeg command
    ffmpeg_args = [
        "-y",  # Overwrite output
        *input_args,
        *filter_args,
        "-map", video_label,
        "-map", audio_label,
        "-c:v", timeline.get("video_codec", "libx264"),
        "-preset", timeline.get("preset", "medium"),
        "-crf", str(timeline.get("crf", 23)),
        "-c:a", timeline.get("audio_codec", "aac"),
        "-b:a", timeline.get("audio_bitrate", "192k"),
        "-ar", str(timeline.get("audio_sample_rate", 44100)),
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",  # YouTube compatibility
        str(output_path)
    ]

    # Run FFmpeg
    try:
        run_ffmpeg(enhanced_cfg.video.ffmpeg_bin, ffmpeg_args)
    except Exception as e:
        raise VideoAssemblyError(f"Assembly failed: {e}")

    # Validate output
    if not output_path.exists():
        raise VideoAssemblyError("Output file was not created")

    # Probe output for validation
    output_info = probe_media_file(enhanced_cfg.video.ffmpeg_bin, output_path)

    if output_info:
        logger.info(
            f"Assembled video: {output_path} "
            f"({output_info['width']}x{output_info['height']}, "
            f"{output_info['duration']:.1f}s, "
            f"{output_info['fps']:.1f}fps)"
        )

    return output_path


def assemble_video(cfg: AppConfig, clips: Sequence[ClipSpec], audio_path: Path, output_path: Path) -> None:
    """Legacy function for simple concatenation (backward compatibility).

    This minimal reference uses stream copy for video when possible and overlays
    narration as primary audio.
    """
    workdir = output_path.parent
    os.makedirs(workdir, exist_ok=True)

    # Build concat list
    list_path = workdir / "inputs.txt"
    lines: list[str] = []
    for clip in clips:
        if clip.start is None and clip.end is None:
            lines.append(f"file '{clip.path.as_posix()}'")
        else:
            # For simplicity, we require pre-trimmed clips in this version.
            raise ValueError("start/end trimming not supported in simple concat mode")
    list_path.write_text("\n".join(lines), encoding="utf-8")

    # Basic concat for video
    temp_video = workdir / "temp_concat.mp4"
    run_ffmpeg(
        cfg.ffmpeg_bin,
        [
            "-f", "concat",
            "-safe", "0",
            "-i", list_path.as_posix(),
            "-c", "copy",
            temp_video.as_posix(),
        ],
    )

    # Combine with narration and normalize loudness
    run_ffmpeg(
        cfg.ffmpeg_bin,
        [
            "-i", temp_video.as_posix(),
            "-i", audio_path.as_posix(),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path.as_posix(),
        ],
    )

    try:
        temp_video.unlink(missing_ok=True)
        list_path.unlink(missing_ok=True)
    except Exception:
        pass


def validate_output(
    output_path: Path,
    expected_duration: float,
    tolerance: float = 2.0
) -> bool:
    """Validate assembled video output.

    Args:
        output_path: Path to video file
        expected_duration: Expected duration in seconds
        tolerance: Acceptable difference in seconds

    Returns:
        True if valid, False otherwise
    """
    if not output_path.exists():
        logger.error(f"Output file not found: {output_path}")
        return False

    # Check file size
    file_size = output_path.stat().st_size
    if file_size < 1000:  # Less than 1KB
        logger.error(f"Output file too small: {file_size} bytes")
        return False

    # Load config for ffmpeg path
    cfg = load_enhanced_config()

    # Probe file
    info = probe_media_file(cfg.video.ffmpeg_bin, output_path)

    if not info:
        logger.error("Could not probe output file")
        return False

    # Check duration
    actual_duration = info.get("duration", 0)
    duration_diff = abs(actual_duration - expected_duration)

    if duration_diff > tolerance:
        logger.error(
            f"Duration mismatch: expected {expected_duration:.1f}s, "
            f"got {actual_duration:.1f}s (diff: {duration_diff:.1f}s)"
        )
        return False

    # Check streams
    if not info.get("has_video"):
        logger.error("Output has no video stream")
        return False

    if not info.get("has_audio"):
        logger.error("Output has no audio stream")
        return False

    logger.info(f"Output validation passed: {output_path}")
    return True