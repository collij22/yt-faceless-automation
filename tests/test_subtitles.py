"""Tests for subtitle generation module."""

from datetime import timedelta

import pytest

from yt_faceless.core.schemas import ScriptSection
from yt_faceless.production.subtitles import (
    srt_from_sections,
    vtt_from_sections,
    _split_into_cues,
    _clean_subtitle_text,
    _split_sentences,
    _wrap_text,
    _format_srt_timecode,
    _format_vtt_timecode,
    SubtitleGenerator,
)


class TestSRTGeneration:
    """Tests for SRT subtitle generation."""

    def test_generate_simple_srt(self):
        """Test generating simple SRT from sections."""
        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="Hello world. This is a test.",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            ),
            ScriptSection(
                section_id="2",
                section_type="content",
                start_time=5.0,
                end_time=10.0,
                text="Second section here.",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        srt = srt_from_sections(sections)

        assert "1" in srt
        assert "00:00:00,000 --> " in srt
        assert "Hello world" in srt
        assert "2" in srt
        assert "Second section" in srt

    def test_srt_with_empty_sections(self):
        """Test SRT generation skips empty sections."""
        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            ),
            ScriptSection(
                section_id="2",
                section_type="content",
                start_time=5.0,
                end_time=10.0,
                text="Valid text",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        srt = srt_from_sections(sections)

        assert "Valid text" in srt
        assert srt.count("\n1\n") == 1  # Only one cue number


class TestVTTGeneration:
    """Tests for WebVTT subtitle generation."""

    def test_generate_simple_vtt(self):
        """Test generating WebVTT from sections."""
        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="Hello world",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        vtt = vtt_from_sections(sections)

        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> " in vtt
        assert "Hello world" in vtt
        assert "align:middle" in vtt

    def test_vtt_includes_style(self):
        """Test VTT includes style block."""
        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="Test",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        vtt = vtt_from_sections(sections)

        assert "STYLE" in vtt
        assert "::cue {" in vtt
        assert "font-family: Arial" in vtt


class TestCueSplitting:
    """Tests for splitting text into subtitle cues."""

    def test_split_into_cues_respects_max_chars(self):
        """Test cue splitting respects character limits."""
        text = "This is a long text that needs to be split into multiple cues for display."
        cues = _split_into_cues(text, 0.0, 10.0, max_chars_per_line=20, max_lines=2)

        for cue_text, _, _ in cues:
            lines = cue_text.split("\n")
            assert all(len(line) <= 20 for line in lines)
            assert len(lines) <= 2

    def test_split_into_cues_timing(self):
        """Test cue timing distribution."""
        text = "First sentence. Second sentence. Third sentence."
        cues = _split_into_cues(text, 0.0, 9.0, max_chars_per_line=20)

        # Check timing
        for i, (_, start, end) in enumerate(cues):
            assert start >= 0.0
            assert end <= 9.0
            if i > 0:
                # No overlap
                assert start >= cues[i-1][2]

    def test_split_empty_text(self):
        """Test splitting empty text."""
        cues = _split_into_cues("", 0.0, 5.0)
        assert len(cues) == 0


class TestTextCleaning:
    """Tests for subtitle text cleaning."""

    def test_clean_subtitle_text(self):
        """Test cleaning text for subtitles."""
        text = "<emphasis>Hello</emphasis> world <break time='500ms'/>"
        cleaned = _clean_subtitle_text(text)

        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "Hello world" in cleaned

    def test_clean_multiple_spaces(self):
        """Test cleaning multiple spaces."""
        text = "Hello    world   test"
        cleaned = _clean_subtitle_text(text)

        assert "  " not in cleaned
        assert "Hello world test" == cleaned

    def test_clean_special_characters(self):
        """Test cleaning special characters."""
        text = "Hello... world -- test"
        cleaned = _clean_subtitle_text(text)

        assert "…" in cleaned  # Ellipsis
        assert "—" in cleaned  # Em dash


class TestSentenceSplitting:
    """Tests for sentence splitting."""

    def test_split_sentences(self):
        """Test splitting text into sentences."""
        text = "First sentence. Second sentence! Third sentence? Fourth."
        sentences = _split_sentences(text)

        assert len(sentences) == 4
        assert sentences[0] == "First sentence."
        assert sentences[1] == "Second sentence!"
        assert sentences[2] == "Third sentence?"
        assert sentences[3] == "Fourth."

    def test_split_sentences_empty(self):
        """Test splitting empty text."""
        sentences = _split_sentences("")
        assert len(sentences) == 0


class TestTextWrapping:
    """Tests for text wrapping."""

    def test_wrap_text_single_line(self):
        """Test wrapping short text."""
        text = "Short text"
        wrapped = _wrap_text(text, max_chars_per_line=20, max_lines=2)

        assert len(wrapped) == 1
        assert wrapped[0] == "Short text"

    def test_wrap_text_multiple_lines(self):
        """Test wrapping to multiple lines."""
        text = "This is a longer text that needs wrapping"
        wrapped = _wrap_text(text, max_chars_per_line=15, max_lines=2)

        assert len(wrapped) > 0
        for block in wrapped:
            lines = block.split("\n")
            assert all(len(line) <= 15 for line in lines)
            assert len(lines) <= 2

    def test_wrap_text_multiple_blocks(self):
        """Test wrapping to multiple blocks."""
        text = " ".join(["word"] * 50)
        wrapped = _wrap_text(text, max_chars_per_line=10, max_lines=2)

        assert len(wrapped) > 1


class TestTimecodeFormatting:
    """Tests for timecode formatting."""

    def test_format_srt_timecode(self):
        """Test SRT timecode formatting."""
        # Test various times
        assert _format_srt_timecode(0.0) == "00:00:00,000"
        assert _format_srt_timecode(1.5) == "00:00:01,500"
        assert _format_srt_timecode(61.25) == "00:01:01,250"
        assert _format_srt_timecode(3661.5) == "01:01:01,500"

    def test_format_vtt_timecode(self):
        """Test WebVTT timecode formatting."""
        # Test various times
        assert _format_vtt_timecode(0.0) == "00:00:00.000"
        assert _format_vtt_timecode(1.5) == "00:00:01.500"
        assert _format_vtt_timecode(61.25) == "00:01:01.250"
        assert _format_vtt_timecode(3661.5) == "01:01:01.500"

    def test_timecode_precision(self):
        """Test timecode millisecond precision."""
        # Test fractional seconds
        srt_tc = _format_srt_timecode(1.123456)
        assert srt_tc == "00:00:01,123"

        vtt_tc = _format_vtt_timecode(1.123456)
        assert vtt_tc == "00:00:01.123"


class TestSubtitleGenerator:
    """Tests for SubtitleGenerator class."""

    def test_generator_initialization(self):
        """Test SubtitleGenerator initialization."""
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        generator = SubtitleGenerator(mock_config)

        assert generator.config == mock_config
        assert generator.MAX_CHARS_PER_LINE == 42
        assert generator.MAX_LINES_PER_CUE == 2

    def test_generator_srt_method(self):
        """Test generator's SRT generation method."""
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        generator = SubtitleGenerator(mock_config)

        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="Test text",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        srt = generator.generate_srt(sections)
        assert "Test text" in srt

    def test_generator_vtt_method(self):
        """Test generator's VTT generation method."""
        from unittest.mock import MagicMock

        mock_config = MagicMock()
        generator = SubtitleGenerator(mock_config)

        sections = [
            ScriptSection(
                section_id="1",
                section_type="intro",
                start_time=0.0,
                end_time=5.0,
                text="Test text",
                ssml_text=None,
                visual_cues=[],
                b_roll_suggestions=[]
            )
        ]

        vtt = generator.generate_vtt(sections)
        assert "WEBVTT" in vtt
        assert "Test text" in vtt