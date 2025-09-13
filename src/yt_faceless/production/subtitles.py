"""Subtitle generation module for SRT and VTT formats."""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from ..core.config import AppConfig
from ..core.schemas import ScriptSection

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Generates subtitles in various formats from script sections."""

    # Subtitle formatting constraints
    MAX_CHARS_PER_LINE = 42
    MAX_LINES_PER_CUE = 2
    MIN_CUE_DURATION = 0.7  # seconds
    MAX_CUE_DURATION = 7.0  # seconds

    def __init__(self, config: AppConfig):
        self.config = config

    def generate_srt(self, sections: List[ScriptSection]) -> str:
        """Generate SRT format subtitles."""
        return srt_from_sections(sections)

    def generate_vtt(self, sections: List[ScriptSection]) -> str:
        """Generate WebVTT format subtitles."""
        return vtt_from_sections(sections)


def srt_from_sections(sections: List[ScriptSection]) -> str:
    """Convert script sections to SRT format.

    Args:
        sections: List of script sections with timing

    Returns:
        SRT formatted subtitle string
    """
    srt_lines = []
    cue_number = 1

    for section in sections:
        # Skip empty sections
        if not section.text or not section.text.strip():
            continue

        # Split section into subtitle cues
        cues = _split_into_cues(
            section.text,
            section.start_time,
            section.end_time
        )

        for cue_text, start_time, end_time in cues:
            # Format timecode
            start_tc = _format_srt_timecode(start_time)
            end_tc = _format_srt_timecode(end_time)

            # Add SRT cue
            srt_lines.append(str(cue_number))
            srt_lines.append(f"{start_tc} --> {end_tc}")
            srt_lines.append(cue_text)
            srt_lines.append("")  # Empty line between cues

            cue_number += 1

    return "\n".join(srt_lines)


def vtt_from_sections(sections: List[ScriptSection]) -> str:
    """Convert script sections to WebVTT format.

    Args:
        sections: List of script sections with timing

    Returns:
        WebVTT formatted subtitle string
    """
    vtt_lines = ["WEBVTT", ""]

    # Optional style block
    vtt_lines.extend([
        "STYLE",
        "::cue {",
        "  font-family: Arial, sans-serif;",
        "  font-size: 18px;",
        "  color: white;",
        "  background-color: rgba(0, 0, 0, 0.8);",
        "}",
        ""
    ])

    for section in sections:
        # Skip empty sections
        if not section.text or not section.text.strip():
            continue

        # Split section into subtitle cues
        cues = _split_into_cues(
            section.text,
            section.start_time,
            section.end_time
        )

        for cue_text, start_time, end_time in cues:
            # Format timecode
            start_tc = _format_vtt_timecode(start_time)
            end_tc = _format_vtt_timecode(end_time)

            # Add VTT cue with optional positioning
            vtt_lines.append(f"{start_tc} --> {end_tc} align:middle line:85%")
            vtt_lines.append(cue_text)
            vtt_lines.append("")  # Empty line between cues

    return "\n".join(vtt_lines)


def _split_into_cues(
    text: str,
    start_time: float,
    end_time: float,
    max_chars_per_line: int = 42,
    max_lines: int = 2
) -> List[Tuple[str, float, float]]:
    """Split text into subtitle cues with proper timing.

    Args:
        text: Text to split
        start_time: Section start time in seconds
        end_time: Section end time in seconds
        max_chars_per_line: Maximum characters per line
        max_lines: Maximum lines per cue

    Returns:
        List of (cue_text, start_time, end_time) tuples
    """
    cues = []

    # Clean text
    text = _clean_subtitle_text(text)

    # Calculate words per second for timing
    words = text.split()
    total_words = len(words)
    duration = end_time - start_time

    if total_words == 0 or duration <= 0:
        return cues

    words_per_second = total_words / duration

    # Split into sentences first
    sentences = _split_sentences(text)

    current_time = start_time

    for sentence in sentences:
        # Wrap sentence to fit subtitle constraints
        wrapped_lines = _wrap_text(sentence, max_chars_per_line, max_lines)

        for wrapped_text in wrapped_lines:
            # Calculate cue duration based on word count
            cue_words = len(wrapped_text.split())
            cue_duration = cue_words / words_per_second

            # Apply duration constraints
            cue_duration = max(SubtitleGenerator.MIN_CUE_DURATION, cue_duration)
            cue_duration = min(SubtitleGenerator.MAX_CUE_DURATION, cue_duration)

            # Calculate cue timing
            cue_start = current_time
            cue_end = min(current_time + cue_duration, end_time)

            cues.append((wrapped_text, cue_start, cue_end))

            current_time = cue_end

            # Stop if we've reached the end time
            if current_time >= end_time:
                break

    return cues


def _clean_subtitle_text(text: str) -> str:
    """Clean text for subtitle display.

    Args:
        text: Raw text

    Returns:
        Cleaned text suitable for subtitles
    """
    # Remove SSML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Fix common issues
    text = text.replace('...', '…')  # Use ellipsis character
    text = text.replace('--', '—')  # Use em dash

    return text


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def _wrap_text(
    text: str,
    max_chars_per_line: int,
    max_lines: int
) -> List[str]:
    """Wrap text to fit subtitle constraints.

    Args:
        text: Text to wrap
        max_chars_per_line: Maximum characters per line
        max_lines: Maximum lines per cue

    Returns:
        List of wrapped text blocks
    """
    wrapped_blocks = []
    words = text.split()

    if not words:
        return wrapped_blocks

    current_block = []
    current_line = []
    current_line_length = 0
    line_count = 0

    for word in words:
        word_length = len(word)

        # Check if word fits on current line
        if current_line_length + word_length + 1 <= max_chars_per_line:
            # Add word to current line
            current_line.append(word)
            current_line_length += word_length + 1
        else:
            # Start new line
            if current_line:
                current_block.append(" ".join(current_line))
                line_count += 1

            # Check if we need a new block
            if line_count >= max_lines:
                # Save current block and start new one
                wrapped_blocks.append("\n".join(current_block))
                current_block = []
                line_count = 0

            # Start new line with current word
            current_line = [word]
            current_line_length = word_length

    # Add remaining line
    if current_line:
        current_block.append(" ".join(current_line))

    # Add remaining block
    if current_block:
        wrapped_blocks.append("\n".join(current_block))

    return wrapped_blocks


def _format_srt_timecode(seconds: float) -> str:
    """Format time in SRT format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        SRT formatted timecode
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_timecode(seconds: float) -> str:
    """Format time in WebVTT format (HH:MM:SS.mmm).

    Args:
        seconds: Time in seconds

    Returns:
        WebVTT formatted timecode
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def write_subtitles_for_slug(
    cfg: AppConfig,
    slug: str,
    sections: List[ScriptSection],
    format: str = "srt"
) -> Path:
    """Write subtitle file for a content slug.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        sections: Script sections with timing
        format: Subtitle format (srt or vtt)

    Returns:
        Path to generated subtitle file
    """
    content_dir = cfg.directories.content_dir / slug
    content_dir.mkdir(parents=True, exist_ok=True)

    # Generate subtitles
    if format == "vtt":
        subtitle_text = vtt_from_sections(sections)
        subtitle_path = content_dir / "subtitles.vtt"
    else:
        subtitle_text = srt_from_sections(sections)
        subtitle_path = content_dir / "subtitles.srt"

    # Write file
    subtitle_path.write_text(subtitle_text, encoding="utf-8")

    logger.info(f"Generated {format.upper()} subtitles: {subtitle_path}")
    return subtitle_path


def extract_sections_from_script(
    script_path: Path,
    words_per_minute: int = 150
) -> List[ScriptSection]:
    """Extract script sections with estimated timing from script file.

    Args:
        script_path: Path to script.md file
        words_per_minute: Speaking rate for timing estimation

    Returns:
        List of script sections with timing
    """
    import json

    sections = []

    # Check for existing metadata with sections
    metadata_path = script_path.parent / "metadata.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text())
            if "sections" in metadata:
                # Use existing sections with timing
                for section_data in metadata["sections"]:
                    sections.append(ScriptSection(**section_data))
                return sections
        except Exception as e:
            logger.warning(f"Could not load sections from metadata: {e}")

    # Parse script and estimate timing
    script_text = script_path.read_text(encoding="utf-8")

    # Split by markdown sections or paragraphs
    paragraphs = re.split(r'\n\n+', script_text)

    current_time = 0.0
    section_id = 1

    for paragraph in paragraphs:
        # Skip empty paragraphs
        if not paragraph.strip():
            continue

        # Clean text
        text = re.sub(r'^#+\s+', '', paragraph)  # Remove headers
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # Remove formatting

        # Calculate duration
        word_count = len(text.split())
        duration = (word_count / words_per_minute) * 60  # Convert to seconds

        # Create section
        section = ScriptSection(
            section_id=f"section_{section_id}",
            section_type="content",
            start_time=current_time,
            end_time=current_time + duration,
            text=text,
            ssml_text=None,
            visual_cues=[],
            b_roll_suggestions=[]
        )

        sections.append(section)

        current_time += duration
        section_id += 1

    return sections