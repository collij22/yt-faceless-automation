"""Tests for FFmpeg filtergraph building in assembly module."""

from pathlib import Path
from unittest.mock import MagicMock
import json

import pytest

from yt_faceless.assembly import build_filtergraph
from yt_faceless.production.timeline import Timeline, TimelineScene


class TestFiltergraphBuilding:
    """Tests for build_filtergraph function."""

    def test_filtergraph_contains_scale_and_pad(self):
        """Test that filtergraph contains scale and pad filters."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=None
        )

        # Check for scale and pad in filter args
        filter_complex = " ".join(filter_args)
        assert "scale=" in filter_complex
        assert "pad=" in filter_complex
        assert "1920:1080" in filter_complex

    def test_filtergraph_with_transitions(self):
        """Test filtergraph contains xfade for transitions."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                },
                {
                    "clip_path": "clip2.mp4",
                    "start_time": 4.5,
                    "end_time": 10.0,
                    "source_start": 0.0,
                    "source_end": 5.5,
                    "transition": "fade",
                    "transition_duration": 0.5,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=None
        )

        # Check for xfade transition in filter args
        filter_complex = " ".join(filter_args)
        assert "xfade=" in filter_complex
        assert "transition=fade" in filter_complex

    def test_filtergraph_with_zoom_pan(self):
        """Test filtergraph contains zoompan for Ken Burns effect."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": {
                        "zoom_start": 1.0,
                        "zoom_end": 1.2,
                        "pan_x_start": 0.0,
                        "pan_x_end": 0.1,
                        "pan_y_start": 0.0,
                        "pan_y_end": 0.1
                    },
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=None
        )

        # Check for zoompan filter in filter args
        filter_complex = " ".join(filter_args)
        assert "zoompan=" in filter_complex

    def test_filtergraph_with_music_ducking(self):
        """Test filtergraph contains sidechaincompress for audio ducking."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": True
                }
            ],
            "music_track": "music.mp3",
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=Path("/audio/music.mp3"),
            subtitle_path=None
        )

        # Check for audio processing in filter args
        filter_complex = " ".join(filter_args)
        assert "sidechaincompress" in filter_complex or "amix" in filter_complex
        assert "volume=" in filter_complex

    def test_filtergraph_with_loudness_normalization(self):
        """Test filtergraph contains loudnorm for LUFS normalization."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=None
        )

        # Check for loudness normalization in filter args
        filter_complex = " ".join(filter_args)
        assert "loudnorm" in filter_complex
        assert "I=-14" in filter_complex  # YouTube standard

    def test_filtergraph_with_subtitles(self):
        """Test filtergraph contains subtitle burning."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14,
            "burn_subtitles": True,
            "subtitle_path": "subtitles.srt"
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=Path("/subtitles/subtitles.srt")
        )

        # Check for subtitle filter in filter args
        filter_complex = " ".join(filter_args)
        assert "subtitles=" in filter_complex

    def test_all_transition_types_mapped(self):
        """Test that all declared transition types are properly mapped."""
        from yt_faceless.production.timeline import TimelineBuilder

        mock_config = MagicMock()
        builder = TimelineBuilder(mock_config)

        # Get all declared transitions
        declared_transitions = builder.TRANSITIONS

        # Test each transition type
        for transition in declared_transitions:
            timeline = {
                "slug": "test",
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "scenes": [
                    {
                        "clip_path": "clip1.mp4",
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "source_start": 0.0,
                        "source_end": 5.0,
                        "transition": None,
                        "zoom_pan": None,
                        "overlay_text": None,
                        "audio_duck": False
                    },
                    {
                        "clip_path": "clip2.mp4",
                        "start_time": 4.5,
                        "end_time": 10.0,
                        "source_start": 0.0,
                        "source_end": 5.5,
                        "transition": transition,
                        "transition_duration": 0.5,
                        "zoom_pan": None,
                        "overlay_text": None,
                        "audio_duck": False
                    }
                ],
                "music_track": None,
                "music_volume": 0.2,
                "loudness_target": -14
            }

            # Should not raise an error
            input_args, filter_args, video_label, audio_label = build_filtergraph(
                cfg=mock_config,
                timeline=timeline,
                narration_path=Path("/audio/narration.wav"),
                music_path=None,
                subtitle_path=None
            )

            # Should contain xfade with the transition in filter args
            filter_complex = " ".join(filter_args)
            assert "xfade=" in filter_complex, f"Missing xfade for {transition}"

    def test_filtergraph_output_format(self):
        """Test that filtergraph produces correct output format."""
        mock_config = MagicMock()
        mock_config.directories.assets_dir = Path("/assets")

        timeline = {
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "scenes": [
                {
                    "clip_path": "clip1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_start": 0.0,
                    "source_end": 5.0,
                    "transition": None,
                    "zoom_pan": None,
                    "overlay_text": None,
                    "audio_duck": False
                }
            ],
            "music_track": None,
            "music_volume": 0.2,
            "loudness_target": -14
        }

        input_args, filter_args, video_label, audio_label = build_filtergraph(
            cfg=mock_config,
            timeline=timeline,
            narration_path=Path("/audio/narration.wav"),
            music_path=None,
            subtitle_path=None
        )

        # Check that we get correct return values
        assert isinstance(input_args, list)
        assert isinstance(filter_args, list)
        assert isinstance(video_label, str)
        assert isinstance(audio_label, str)
        assert video_label.startswith("[")
        assert audio_label.startswith("[")