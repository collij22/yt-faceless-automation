"""Tests for video assembly module."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import json

import pytest

from yt_faceless.assembly import (
    ClipSpec,
    FiltergraphBuilder,
    build_filtergraph,
    assemble_video,
    assemble_from_timeline,
    validate_output,
)
from yt_faceless.production.timeline import Timeline, TimelineScene


class TestFiltergraphBuilder:
    """Tests for FiltergraphBuilder class."""

    def test_add_input(self):
        """Test adding input to filtergraph."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        label = builder.add_input(0)

        assert label == "[0:v]"
        assert "[0:v]" in builder.inputs

    def test_add_scale(self):
        """Test adding scale filter."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        input_label = "[0:v]"
        output = builder.add_scale(input_label, 1920, 1080)

        assert output.startswith("[scaled_")
        assert f"{input_label}scale=1920:1080" in builder.filters[-1]

    def test_add_fade_transition(self):
        """Test adding fade transition."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        output = builder.add_transition("[0:v]", "[1:v]", "fade", 1.0, 5.0)

        assert output.startswith("[trans_")
        assert "fade" in str(builder.filters)

    def test_add_zoom_pan(self):
        """Test adding zoom/pan effect."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        output = builder.add_zoom_pan(
            "[0:v]",
            zoom_start=1.0,
            zoom_end=1.2,
            pan_x_start=0.0,
            pan_x_end=0.1,
            pan_y_start=0.0,
            pan_y_end=0.1,
            duration=5.0,
            fps=30
        )

        assert output.startswith("[zoompan_")
        assert "zoompan" in str(builder.filters)

    def test_add_overlay(self):
        """Test adding overlay."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        output = builder.add_overlay("[0:v]", "[1:v]", x=100, y=200)

        assert output.startswith("[overlay_")
        assert "overlay=100:200" in builder.filters[-1]

    def test_mix_audio(self):
        """Test audio mixing."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)
        output = builder.mix_audio("[0:a]", "[1:a]", music_volume=0.3)

        assert output == "[final_audio]"
        assert "amix=inputs=2" in str(builder.filters)

    def test_build_complex_filtergraph(self):
        """Test building a complex filtergraph."""
        mock_config = MagicMock()
        builder = FiltergraphBuilder(mock_config)

        # Add inputs
        v1 = builder.add_input(0)
        v2 = builder.add_input(1)

        # Scale videos
        v1_scaled = builder.add_scale(v1, 1920, 1080)
        v2_scaled = builder.add_scale(v2, 1920, 1080)

        # Add transition
        trans = builder.add_transition(v1_scaled, v2_scaled, "fade", 1.0, 5.0)

        # Build
        filtergraph = builder.build(trans)

        assert filtergraph
        assert "scale=" in filtergraph
        assert "fade" in filtergraph


class TestBuildFiltergraph:
    """Tests for build_filtergraph function."""

    def test_simple_filtergraph(self):
        """Test building simple filtergraph."""
        clips = [
            ClipSpec(path=Path("clip1.mp4")),
            ClipSpec(path=Path("clip2.mp4"))
        ]

        filtergraph = build_filtergraph(
            config=MagicMock(),
            scenes=[],
            width=1920,
            height=1080,
            fps=30,
            music_track=None,
            music_volume=0.2,
            loudness_target=-14
        )

        assert filtergraph
        assert "concat" in filtergraph

    def test_filtergraph_with_transitions(self):
        """Test filtergraph with transitions."""
        clips = [
            ClipSpec(path=Path("clip1.mp4")),
            ClipSpec(path=Path("clip2.mp4"))
        ]

        transitions = [
            {"type": "fade", "duration": 1.0, "offset": 4.0}
        ]

        from yt_faceless.production.timeline import TimelineScene
        scenes = [
            TimelineScene(
                scene_id="1",
                clip_path="clip1.mp4",
                start_time=0.0,
                end_time=4.0,
                source_start=0.0,
                source_end=4.0,
                transition="fade",
                transition_duration=1.0,
                zoom_pan=None,
                overlay_text=None,
                overlay_position=None,
                audio_duck=False,
                effects=[]
            )
        ]
        filtergraph = build_filtergraph(
            config=MagicMock(),
            scenes=scenes,
            width=1920,
            height=1080,
            fps=30,
            music_track=None,
            music_volume=0.2,
            loudness_target=-14
        )

        assert "fade" in filtergraph or "blend" in filtergraph


class TestAssembleVideo:
    """Tests for assemble_video function."""

    def test_assemble_video_mock(self):
        """Test video assembly with mocked FFmpeg."""
        mock_config = MagicMock()
        mock_config.video.ffmpeg_bin = "ffmpeg"
        mock_config.video.default_width = 1920
        mock_config.video.default_height = 1080
        mock_config.video.default_fps = 30
        mock_config.performance.hardware_accel = "none"

        clips = [
            ClipSpec(path=Path("clip1.mp4")),
            ClipSpec(path=Path("clip2.mp4"))
        ]

        with patch("yt_faceless.assembly.run_ffmpeg") as mock_run:
            with patch("yt_faceless.assembly.validate_output"):
                assemble_video(
                    cfg=mock_config,
                    clips=clips,
                    audio_path=Path("audio.mp3"),
                    output_path=Path("output.mp4")
                )

                # Should call FFmpeg
                assert mock_run.called
                call_args = mock_run.call_args[0][1]
                assert "-i" in call_args
                assert "output.mp4" in str(call_args)


class TestAssembleFromTimeline:
    """Tests for timeline-based assembly."""

    def test_assemble_from_timeline_mock(self):
        """Test timeline assembly with mocked components."""
        mock_config = MagicMock()
        mock_config.video.ffmpeg_bin = "ffmpeg"
        mock_config.video.default_width = 1920
        mock_config.video.default_height = 1080
        mock_config.video.default_fps = 30
        mock_config.performance.hardware_accel = "none"

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

        with patch("yt_faceless.assembly.run_ffmpeg") as mock_run:
            with patch("yt_faceless.assembly.validate_output"):
                with patch("pathlib.Path.exists", return_value=True):
                    assemble_from_timeline(
                        cfg=mock_config,
                        slug="test",
                        timeline=timeline,
                        output_path=Path("output.mp4")
                    )

                    # Should call FFmpeg
                    assert mock_run.called


class TestValidateOutput:
    """Tests for output validation."""

    def test_validate_output_success(self):
        """Test successful output validation."""
        with patch("yt_faceless.assembly.probe_media_file") as mock_probe:
            mock_probe.return_value = {
                "streams": [
                    {"codec_type": "video", "width": 1920, "height": 1080},
                    {"codec_type": "audio"}
                ],
                "format": {
                    "duration": "60.0",
                    "size": "10000000"
                }
            }

            # Should not raise
            validate_output(
                output_path=Path("output.mp4"),
                expected_duration=60.0,
                tolerance=2.0
            )

    def test_validate_output_missing_file(self):
        """Test validation with missing file."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(ValueError, match="does not exist"):
                validate_output(
                    output_path=Path("missing.mp4"),
                    expected_duration=60.0
                )

    def test_validate_output_wrong_duration(self):
        """Test validation with wrong duration."""
        with patch("yt_faceless.assembly.probe_media_file") as mock_probe:
            mock_probe.return_value = {
                "streams": [
                    {"codec_type": "video"},
                    {"codec_type": "audio"}
                ],
                "format": {
                    "duration": "30.0",  # Wrong duration
                    "size": "10000000"
                }
            }

            with pytest.raises(ValueError, match="Duration mismatch"):
                validate_output(
                    output_path=Path("output.mp4"),
                    expected_duration=60.0
                )


class TestClipSpec:
    """Tests for ClipSpec class."""

    def test_clip_spec_basic(self):
        """Test basic ClipSpec creation."""
        clip = ClipSpec(path=Path("video.mp4"))

        assert clip.path == Path("video.mp4")
        assert clip.start is None
        assert clip.end is None

    def test_clip_spec_with_trim(self):
        """Test ClipSpec with trim points."""
        clip = ClipSpec(
            path=Path("video.mp4"),
            start=10.0,
            end=20.0
        )

        assert clip.path == Path("video.mp4")
        assert clip.start == 10.0
        assert clip.end == 20.0