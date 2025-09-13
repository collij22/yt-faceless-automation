"""YouTube Shorts generation from long-form videos."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import AppConfig
from ..core.schemas import ShortsGenerationConfig, ShortsSegment
from ..logging_setup import get_logger

logger = get_logger(__name__)


class ShortsGenerator:
    """Generate YouTube Shorts from long-form videos."""

    def __init__(self, config: AppConfig):
        """Initialize Shorts generator.

        Args:
            config: Application configuration
        """
        self.config = config
        self.ffmpeg_bin = config.video.ffmpeg_bin

    def analyze_video_for_segments(
        self,
        video_path: Path,
        metadata_path: Optional[Path] = None
    ) -> List[Tuple[float, float, str]]:
        """Analyze video to identify high-retention segments.

        Args:
            video_path: Path to source video
            metadata_path: Optional path to video metadata

        Returns:
            List of (start_sec, end_sec, hook_type) tuples
        """
        segments = []

        # Always include the hook (first 30-60 seconds)
        segments.append((0, 30, "intro"))

        # If we have metadata, use section information
        if metadata_path and metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Look for high-value sections
            sections = metadata.get("sections", [])
            for section in sections:
                # Identify promise/payoff sections
                if any(keyword in section.get("title", "").lower() for keyword in [
                    "reveal", "secret", "truth", "answer", "how to", "step"
                ]):
                    start = section.get("start_time", 0)
                    end = min(start + 60, section.get("end_time", start + 30))
                    segments.append((start, end, "promise"))

        # Add cliffhanger segments (typically near transitions)
        # These would ideally come from analytics data
        default_positions = [0.25, 0.5, 0.75]  # 25%, 50%, 75% through video

        # Get video duration
        duration = self._get_video_duration(video_path)

        for position in default_positions:
            start = duration * position
            end = min(start + 45, duration)
            segments.append((start, end, "payoff"))

        # Limit to reasonable number of segments
        return segments[:10]

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        cmd = [
            self.ffmpeg_bin,
            "-i", str(video_path),
            "-f", "null",
            "-"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse duration from stderr
            for line in result.stderr.split('\n'):
                if "Duration:" in line:
                    # Format: Duration: 00:10:30.50
                    duration_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = duration_str.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s)

        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            return 600  # Default 10 minutes

        return 600

    def extract_segment(
        self,
        video_path: Path,
        output_path: Path,
        start_sec: float,
        end_sec: float,
        aspect_ratio: str = "9:16",
        burn_captions: bool = True,
        caption_style: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Extract and format a video segment for Shorts.

        Args:
            video_path: Path to source video
            output_path: Path for output Short
            start_sec: Start time in seconds
            end_sec: End time in seconds
            aspect_ratio: Target aspect ratio
            burn_captions: Whether to burn captions
            caption_style: Caption styling options

        Returns:
            True if successful
        """
        # Calculate dimensions based on aspect ratio
        if aspect_ratio == "9:16":
            width, height = 1080, 1920
            crop_filter = f"crop=ih*9/16:ih"  # Center crop to 9:16
        elif aspect_ratio == "1:1":
            width, height = 1080, 1080
            crop_filter = f"crop=ih:ih"  # Center crop to square
        else:  # 4:5
            width, height = 1080, 1350
            crop_filter = f"crop=ih*4/5:ih"  # Center crop to 4:5

        # Build filter chain
        filters = [
            crop_filter,
            f"scale={width}:{height}",
            "fps=30"
        ]

        # Add caption burning if requested
        if burn_captions:
            # Look for subtitle file (standard name is subtitles.srt)
            subtitle_path = video_path.parent / "subtitles.srt"
            if subtitle_path.exists():
                # Build subtitle filter with styling
                style = caption_style or {
                    "font": "Arial",
                    "size": 48,
                    "color": "white",
                    "background": "black@0.5",
                    "position": "bottom"
                }

                # Escape subtitle path for FFmpeg filter (Windows-safe)
                path_str = str(subtitle_path)
                if os.name == "nt":
                    # On Windows, escape backslashes, colons, and quotes
                    escaped_path = path_str.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
                else:
                    # On Unix, just escape quotes
                    escaped_path = path_str.replace("'", "\\'")

                subtitle_filter = (
                    f"subtitles=filename='{escaped_path}':"
                    f"force_style='FontName={style['font']},"
                    f"FontSize={style['size']},"
                    f"PrimaryColour=&H{self._color_to_hex(style['color'])},"
                    f"BackColour=&H{self._color_to_hex(style['background'])},"
                    f"Alignment=2'"  # Bottom center
                )
                filters.append(subtitle_filter)

        # Build FFmpeg command
        duration = end_sec - start_sec
        cmd = [
            self.ffmpeg_bin,
            "-i", str(video_path),
            "-ss", str(start_sec),
            "-t", str(duration),
            "-vf", ",".join(filters),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-y",
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False

            logger.info(f"Generated Short: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout while generating Short")
            return False
        except Exception as e:
            logger.error(f"Failed to generate Short: {e}")
            return False

    def _color_to_hex(self, color: str) -> str:
        """Convert color name or hex to ASS hex format.

        Args:
            color: Color name or hex value

        Returns:
            ASS-compatible hex color
        """
        colors = {
            "white": "FFFFFF",
            "black": "000000",
            "red": "0000FF",
            "blue": "FF0000",
            "green": "00FF00",
            "yellow": "00FFFF"
        }

        if color.startswith("#"):
            return color[1:]
        elif color.startswith("0x"):
            return color[2:]
        elif "@" in color:
            # Handle transparency (e.g., "black@0.5")
            color = color.split("@")[0]

        return colors.get(color.lower(), "FFFFFF")

    def generate_metadata(
        self,
        segment: ShortsSegment,
        original_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metadata for a Shorts video.

        Args:
            segment: Shorts segment configuration
            original_metadata: Original video metadata

        Returns:
            Shorts-optimized metadata
        """
        # Shorten title and add #Shorts
        original_title = original_metadata.get("title", "Video")
        if len(original_title) > 40:
            title = f"{original_title[:37]}... #Shorts"
        else:
            title = f"{original_title} #Shorts"

        # Build description
        description_lines = [
            f"Watch the full video: [link to main video]",
            "",
            "#Shorts #YouTubeShorts"
        ]

        # Add relevant tags from original (handle dict structure)
        tags_dict = original_metadata.get("tags", {})
        if isinstance(tags_dict, dict):
            original_tags = (tags_dict.get("primary", []) +
                           tags_dict.get("competitive", []))[:8]
        else:
            original_tags = tags_dict[:8] if isinstance(tags_dict, list) else []
        shorts_tags = ["shorts", "youtubeshorts"] + original_tags

        return {
            "title": title,
            "description": "\n".join(description_lines),
            "tags": shorts_tags,
            "category_id": original_metadata.get("category_id"),
            "segment_info": {
                "source_video": segment.source_slug,
                "start_time": segment.start_sec,
                "end_time": segment.end_sec,
                "hook_type": segment.hook_type
            }
        }


def generate_shorts(
    config: AppConfig,
    slug: str,
    count: int = 3,
    segments: Optional[List[Tuple[float, float]]] = None,
    burn_captions: bool = True,
    dry_run: bool = False
) -> List[ShortsSegment]:
    """Generate Shorts from a long-form video.

    Args:
        config: Application configuration
        slug: Video slug
        count: Number of Shorts to generate
        segments: Optional specific segments to extract
        burn_captions: Whether to burn captions
        dry_run: Simulate without generating files

    Returns:
        List of generated Shorts segments
    """
    if not config.features.get("shorts_generation"):
        logger.info("Shorts generation feature is disabled")
        return []

    generator = ShortsGenerator(config)

    # Find source video
    content_dir = config.directories.content_dir / slug
    video_path = content_dir / "final.mp4"

    if not video_path.exists():
        logger.error(f"Source video not found: {video_path}")
        return []

    # Create Shorts output directory
    shorts_dir = content_dir / "shorts"
    shorts_dir.mkdir(parents=True, exist_ok=True)

    # Load original metadata
    metadata_path = content_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            original_metadata = json.load(f)
    else:
        original_metadata = {}

    # Generate or use provided segments
    if segments is None:
        video_segments = generator.analyze_video_for_segments(
            video_path,
            metadata_path
        )[:count]
    else:
        video_segments = [(s[0], s[1], "custom") for s in segments[:count]]

    generated_shorts = []

    for i, (start, end, hook_type) in enumerate(video_segments):
        segment_id = f"{slug}_short_{i+1:02d}"
        output_path = shorts_dir / f"short_{i+1:02d}.mp4"

        segment = ShortsSegment(
            segment_id=segment_id,
            source_slug=slug,
            start_sec=start,
            end_sec=end,
            output_path=str(output_path),
            title=f"Short {i+1}",
            description="",
            tags=[],
            hook_type=hook_type
        )

        if not dry_run:
            # Generate the Short
            success = generator.extract_segment(
                video_path,
                output_path,
                start,
                end,
                burn_captions=burn_captions
            )

            if success:
                # Generate metadata
                shorts_metadata = generator.generate_metadata(
                    segment,
                    original_metadata
                )

                # Update segment with metadata
                segment.title = shorts_metadata["title"]
                segment.description = shorts_metadata["description"]
                segment.tags = shorts_metadata["tags"]

                # Save metadata
                metadata_file = shorts_dir / f"short_{i+1:02d}_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(shorts_metadata, f, indent=2)

                generated_shorts.append(segment)
                logger.info(f"Generated Short {i+1}/{count}: {segment_id}")
        else:
            generated_shorts.append(segment)
            logger.info(f"[DRY RUN] Would generate Short {i+1}/{count}: {segment_id}")

    return generated_shorts