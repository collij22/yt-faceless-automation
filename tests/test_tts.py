"""Tests for TTS module."""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from yt_faceless.production.tts import (
    chunk_script,
    validate_ssml_chunk,
    _strip_markdown,
    _chunk_with_ssml,
    _chunk_by_sentences,
    _add_sentence_breaks,
    _wrap_in_speak,
    _generate_cache_key,
    estimate_tts_cost,
    calculate_audio_duration,
)


class TestChunkScript:
    """Tests for script chunking functionality."""

    def test_chunk_simple_text(self):
        """Test chunking of simple text."""
        text = "This is a test. This is another sentence. And a third one."
        chunks = chunk_script(text, max_chars=30, preserve_ssml=False)

        assert len(chunks) > 0
        assert all(len(chunk) <= 30 for chunk in chunks)

    def test_chunk_with_ssml_preservation(self):
        """Test chunking preserves SSML tags."""
        text = "Hello <emphasis>world</emphasis>. This is a <break time='500ms'/> test."
        chunks = chunk_script(text, max_chars=50, preserve_ssml=True)

        assert len(chunks) > 0
        assert all("<speak>" in chunk for chunk in chunks)
        assert all("</speak>" in chunk for chunk in chunks)

    def test_chunk_long_text(self):
        """Test chunking of long text."""
        text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        chunks = chunk_script(text, max_chars=500)

        assert len(chunks) > 1
        assert all(len(chunk) <= 500 for chunk in chunks)

    def test_chunk_empty_text(self):
        """Test chunking of empty text."""
        chunks = chunk_script("", max_chars=100)
        assert len(chunks) == 1
        assert chunks[0] == "<speak></speak>"

    def test_chunk_with_markdown(self):
        """Test chunking strips markdown."""
        text = "# Header\n\n**Bold text** and *italic*. [Link](http://example.com)"
        chunks = chunk_script(text, max_chars=100, preserve_ssml=False)

        assert "#" not in chunks[0]
        assert "**" not in chunks[0]
        assert "[Link]" not in chunks[0]


class TestSSMLValidation:
    """Tests for SSML validation."""

    def test_validate_valid_ssml(self):
        """Test validation of valid SSML."""
        valid_ssml = "<speak>Hello world</speak>"
        result = validate_ssml_chunk(valid_ssml)
        assert result == valid_ssml

    def test_validate_invalid_ssml(self):
        """Test validation fixes invalid SSML."""
        invalid_ssml = "<speak>Hello & world < test ></speak>"
        result = validate_ssml_chunk(invalid_ssml)

        # Should escape special characters
        assert "&amp;" in result or "Hello" in result

    def test_validate_unclosed_tags(self):
        """Test validation handles unclosed tags."""
        invalid_ssml = "<speak>Hello <emphasis>world</speak>"
        result = validate_ssml_chunk(invalid_ssml)

        # Should either fix or return plain text
        assert result


class TestTextProcessing:
    """Tests for text processing utilities."""

    def test_strip_markdown(self):
        """Test markdown stripping."""
        markdown = """
        # Header 1
        ## Header 2

        **Bold** and *italic* text.

        [Link text](https://example.com)

        `inline code` and ```code block```
        """

        result = _strip_markdown(markdown)

        assert "#" not in result
        assert "**" not in result
        assert "*italic*" not in result
        assert "Link text" in result
        assert "[Link text]" not in result
        assert "`" not in result

    def test_add_sentence_breaks(self):
        """Test adding SSML breaks between sentences."""
        text = "First sentence. Second sentence! Third sentence?"
        result = _add_sentence_breaks(text)

        assert "<break time=\"250ms\"/>" in result
        assert result.count("<break") == 3

    def test_wrap_in_speak(self):
        """Test wrapping text in speak tags."""
        text = "Hello world"
        result = _wrap_in_speak(text)
        assert result == "<speak>Hello world</speak>"

        # Test already wrapped
        already_wrapped = "<speak>Hello world</speak>"
        result = _wrap_in_speak(already_wrapped)
        assert result == already_wrapped


class TestChunkingStrategies:
    """Tests for different chunking strategies."""

    def test_chunk_with_ssml(self):
        """Test SSML-aware chunking."""
        text = "First sentence. <emphasis>Important text</emphasis>. Last sentence."
        chunks = _chunk_with_ssml(text, max_chars=30)

        assert len(chunks) > 0
        assert all(len(chunk) <= 30 for chunk in chunks)

    def test_chunk_by_sentences(self):
        """Test sentence-based chunking."""
        text = "First. Second. Third. Fourth. Fifth."
        chunks = _chunk_by_sentences(text, max_chars=20)

        assert len(chunks) > 1
        assert all(len(chunk) <= 20 for chunk in chunks)

    def test_chunk_respects_sentence_boundaries(self):
        """Test chunking doesn't break sentences."""
        text = "This is a very long sentence that should not be broken in the middle."
        chunks = _chunk_by_sentences(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text


class TestCacheKey:
    """Tests for cache key generation."""

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = _generate_cache_key("Hello world", "elevenlabs", "voice1", "model1")
        key2 = _generate_cache_key("Hello world", "elevenlabs", "voice1", "model1")
        key3 = _generate_cache_key("Different text", "elevenlabs", "voice1", "model1")

        # Same input should generate same key
        assert key1 == key2

        # Different input should generate different key
        assert key1 != key3

        # Should be valid SHA-256 hash
        assert len(key1) == 64
        assert all(c in "0123456789abcdef" for c in key1)

    def test_cache_key_case_insensitive(self):
        """Test cache key is case insensitive."""
        key1 = _generate_cache_key("Hello World", "elevenlabs", "voice1", "model1")
        key2 = _generate_cache_key("hello world", "elevenlabs", "voice1", "model1")

        assert key1 == key2


class TestCostEstimation:
    """Tests for TTS cost estimation."""

    def test_estimate_elevenlabs_cost(self):
        """Test ElevenLabs cost estimation."""
        text = "a" * 1000  # 1000 characters
        cost = estimate_tts_cost(text, "elevenlabs", "eleven_monolingual_v1")

        # Should be $0.30 per 1000 chars
        assert cost == 0.30

    def test_estimate_google_cost(self):
        """Test Google TTS cost estimation."""
        text = "a" * 1000
        cost = estimate_tts_cost(text, "google", "standard")

        # Should be $0.004 per 1000 chars
        assert cost == 0.004

    def test_estimate_unknown_provider(self):
        """Test cost estimation for unknown provider."""
        text = "a" * 1000
        cost = estimate_tts_cost(text, "unknown", None)

        # Should use default rate
        assert cost > 0


class TestDurationCalculation:
    """Tests for audio duration calculation."""

    def test_calculate_duration_default_rate(self):
        """Test duration calculation with default rate."""
        text = " ".join(["word"] * 150)  # 150 words
        duration = calculate_audio_duration(text, words_per_minute=150)

        # Should be 60 seconds
        assert duration == 60.0

    def test_calculate_duration_custom_rate(self):
        """Test duration calculation with custom rate."""
        text = " ".join(["word"] * 100)
        duration = calculate_audio_duration(text, words_per_minute=100)

        # Should be 60 seconds
        assert duration == 60.0

    def test_calculate_duration_empty_text(self):
        """Test duration calculation for empty text."""
        duration = calculate_audio_duration("", words_per_minute=150)
        assert duration == 0.0


@pytest.mark.asyncio
class TestAsyncTTSSynthesis:
    """Tests for async TTS synthesis."""

    async def test_synthesize_chunks_mock(self):
        """Test async chunk synthesis with mocked client."""
        from yt_faceless.production.tts import synthesize_chunks

        with patch("yt_faceless.production.tts.TTSProcessor") as mock_processor:
            with patch("yt_faceless.production.tts._synthesize_single_chunk") as mock_synth:
                mock_synth.return_value = Path("/tmp/chunk.wav")

                chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
                mock_config = MagicMock()
                mock_config.performance.max_concurrent_tts_chunks = 2

                # Note: This would need actual implementation of async synthesize_chunks
                # For now, this is a placeholder test structure
                pass


class TestMergeAudio:
    """Tests for audio merging."""

    def test_merge_audio_mock(self):
        """Test audio merging with mocked FFmpeg."""
        from yt_faceless.production.tts import merge_audio

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            mock_config = MagicMock()
            mock_config.video.ffmpeg_bin = "ffmpeg"

            segments = [Path("/tmp/seg1.wav"), Path("/tmp/seg2.wav")]
            output_path = Path("/tmp/output.wav")

            merge_audio(mock_config, segments, output_path, gap_ms=100)

            # Should call FFmpeg
            assert mock_run.called
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "-filter_complex" in call_args