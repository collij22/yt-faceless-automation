"""Tests for timeline generation and validation module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_faceless.core.errors import ValidationError
from yt_faceless.production.timeline import (
    Timeline,
    TimelineScene,
    TimelineBuilder,
    validate_timeline,
    _generate_ken_burns_effect,
    merge_timeline_scenes,
)


class TestTimelineValidation:
    """Tests for timeline validation."""

    def test_validate_valid_timeline(self):
        """Test validation of a valid timeline."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=1920,
            height=1080,
            fps=30,
            total_duration=10.0,
            scenes=[
                TimelineScene(
                    scene_id="1",
                    clip_path="clip1.mp4",
                    start_time=0.0,
                    end_time=5.0,
                    source_start=0.0,
                    source_end=5.0,
                    transition=None,
                    transition_duration=0.5,
                    zoom_pan=None,
                    overlay_text=None,
                    overlay_position=None,
                    audio_duck=False,
                    effects=[]
                ),
                TimelineScene(
                    scene_id="2",
                    clip_path="clip2.mp4",
                    start_time=5.0,
                    end_time=10.0,
                    source_start=0.0,
                    source_end=5.0,
                    transition="fade",
                    transition_duration=0.5,
                    zoom_pan=None,
                    overlay_text=None,
                    overlay_position=None,
                    audio_duck=False,
                    effects=[]
                )
            ],
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            # Should not raise
            validate_timeline(timeline)

    def test_validate_invalid_resolution(self):
        """Test validation fails for invalid resolution."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=-1920,  # Invalid
            height=1080,
            fps=30,
            total_duration=10.0,
            scenes=[],
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_timeline(timeline)

        assert "Invalid resolution" in str(exc_info.value)

    def test_validate_invalid_fps(self):
        """Test validation fails for invalid FPS."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=1920,
            height=1080,
            fps=0,  # Invalid
            total_duration=10.0,
            scenes=[],
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_timeline(timeline)

        assert "Invalid frame rate" in str(exc_info.value)

    def test_validate_no_scenes(self):
        """Test validation fails for timeline with no scenes."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=1920,
            height=1080,
            fps=30,
            total_duration=10.0,
            scenes=[],  # No scenes
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_timeline(timeline)

        assert "No scenes" in str(exc_info.value)

    def test_validate_invalid_scene_timing(self):
        """Test validation fails for invalid scene timing."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=1920,
            height=1080,
            fps=30,
            total_duration=10.0,
            scenes=[
                TimelineScene(
                    scene_id="1",
                    clip_path="clip.mp4",
                    start_time=5.0,
                    end_time=3.0,  # End before start
                    source_start=0.0,
                    source_end=2.0,
                    transition=None,
                    transition_duration=0.5,
                    zoom_pan=None,
                    overlay_text=None,
                    overlay_position=None,
                    audio_duck=False,
                    effects=[]
                )
            ],
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_timeline(timeline)

        assert "End time before start time" in str(exc_info.value)

    def test_validate_invalid_transition(self):
        """Test validation fails for invalid transition type."""
        timeline = Timeline(
            version=1,
            slug="test",
            width=1920,
            height=1080,
            fps=30,
            total_duration=10.0,
            scenes=[
                TimelineScene(
                    scene_id="1",
                    clip_path="clip.mp4",
                    start_time=0.0,
                    end_time=5.0,
                    source_start=0.0,
                    source_end=5.0,
                    transition="invalid_transition",  # Invalid
                    transition_duration=0.5,
                    zoom_pan=None,
                    overlay_text=None,
                    overlay_position=None,
                    audio_duck=False,
                    effects=[]
                )
            ],
            music_track=None,
            music_volume=0.2,
            narration_track="audio.wav",
            burn_subtitles=False,
            subtitle_path=None,
            loudness_target=-14,
            output_format="mp4"
        )

        with patch("pathlib.Path.exists", return_value=True):
            with pytest.raises(ValidationError) as exc_info:
                validate_timeline(timeline)

            assert "Invalid transition" in str(exc_info.value)


class TestTimelineBuilder:
    """Tests for TimelineBuilder class."""

    def test_builder_initialization(self):
        """Test TimelineBuilder initialization."""
        mock_config = MagicMock()
        builder = TimelineBuilder(mock_config)

        assert builder.config == mock_config
        assert len(builder.TRANSITIONS) > 0
        assert builder.DEFAULT_WIDTH == 1920
        assert builder.DEFAULT_HEIGHT == 1080

    def test_build_simple_timeline(self):
        """Test building a simple timeline."""
        mock_config = MagicMock()
        builder = TimelineBuilder(mock_config)

        scenes = [
            TimelineScene(
                scene_id="1",
                clip_path="clip1.mp4",
                start_time=0.0,
                end_time=5.0,
                source_start=0.0,
                source_end=5.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )
        ]

        with patch("yt_faceless.production.timeline.validate_timeline"):
            timeline = builder.build_timeline(
                slug="test",
                scenes=scenes,
                music_track="music.mp3"
            )

        assert timeline["slug"] == "test"
        assert timeline["scenes"] == scenes
        assert timeline["music_track"] == "music.mp3"
        assert timeline["width"] == 1920
        assert timeline["height"] == 1080

    def test_build_timeline_with_custom_params(self):
        """Test building timeline with custom parameters."""
        mock_config = MagicMock()
        builder = TimelineBuilder(mock_config)

        scenes = []

        with patch("yt_faceless.production.timeline.validate_timeline"):
            timeline = builder.build_timeline(
                slug="test",
                scenes=scenes,
                width=1280,
                height=720,
                fps=60,
                music_volume=0.5
            )

        assert timeline["width"] == 1280
        assert timeline["height"] == 720
        assert timeline["fps"] == 60
        assert timeline["music_volume"] == 0.5


class TestKenBurnsEffect:
    """Tests for Ken Burns effect generation."""

    def test_generate_ken_burns_effect(self):
        """Test Ken Burns effect generation."""
        effect = _generate_ken_burns_effect(duration=5.0, fps=30, max_zoom=1.5)

        assert "zoom_start" in effect
        assert "zoom_end" in effect
        assert "pan_x_start" in effect
        assert "pan_x_end" in effect
        assert "pan_y_start" in effect
        assert "pan_y_end" in effect
        assert "duration_frames" in effect

        # Check zoom values
        assert 1.0 <= effect["zoom_start"] <= 1.5
        assert 1.0 <= effect["zoom_end"] <= 1.5

        # Check pan values
        assert 0.0 <= effect["pan_x_start"] <= 1.0
        assert 0.0 <= effect["pan_x_end"] <= 1.0
        assert 0.0 <= effect["pan_y_start"] <= 1.0
        assert 0.0 <= effect["pan_y_end"] <= 1.0

        # Check duration
        assert effect["duration_frames"] == 150  # 5.0 * 30

    def test_ken_burns_random_variation(self):
        """Test Ken Burns effect has random variation."""
        # Generate multiple effects
        effects = [
            _generate_ken_burns_effect(duration=5.0, fps=30)
            for _ in range(10)
        ]

        # Should have some variation
        zoom_starts = [e["zoom_start"] for e in effects]
        zoom_ends = [e["zoom_end"] for e in effects]

        # Not all should be identical
        assert len(set(zoom_starts)) > 1 or len(set(zoom_ends)) > 1


class TestSceneMerging:
    """Tests for scene merging functionality."""

    def test_merge_adjacent_scenes(self):
        """Test merging adjacent scenes with same clip."""
        scenes = [
            TimelineScene(
                scene_id="1",
                clip_path="clip.mp4",
                start_time=0.0,
                end_time=5.0,
                source_start=0.0,
                source_end=5.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            ),
            TimelineScene(
                scene_id="2",
                clip_path="clip.mp4",  # Same clip
                start_time=5.0,  # Adjacent
                end_time=10.0,
                source_start=5.0,
                source_end=10.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )
        ]

        merged = merge_timeline_scenes(scenes, gap_threshold=0.1)

        assert len(merged) == 1
        assert merged[0]["start_time"] == 0.0
        assert merged[0]["end_time"] == 10.0

    def test_dont_merge_different_clips(self):
        """Test not merging scenes with different clips."""
        scenes = [
            TimelineScene(
                scene_id="1",
                clip_path="clip1.mp4",
                start_time=0.0,
                end_time=5.0,
                source_start=0.0,
                source_end=5.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            ),
            TimelineScene(
                scene_id="2",
                clip_path="clip2.mp4",  # Different clip
                start_time=5.0,
                end_time=10.0,
                source_start=0.0,
                source_end=5.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )
        ]

        merged = merge_timeline_scenes(scenes, gap_threshold=0.1)

        assert len(merged) == 2

    def test_dont_merge_with_gap(self):
        """Test not merging scenes with gap between them."""
        scenes = [
            TimelineScene(
                scene_id="1",
                clip_path="clip.mp4",
                start_time=0.0,
                end_time=5.0,
                source_start=0.0,
                source_end=5.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            ),
            TimelineScene(
                scene_id="2",
                clip_path="clip.mp4",
                start_time=5.5,  # Gap of 0.5s
                end_time=10.0,
                source_start=5.5,
                source_end=10.0,
                transition=None,
                transition_duration=0.5,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )
        ]

        merged = merge_timeline_scenes(scenes, gap_threshold=0.1)

        assert len(merged) == 2