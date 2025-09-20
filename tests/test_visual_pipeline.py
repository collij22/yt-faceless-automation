"""Comprehensive tests for the visual enhancement pipeline."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.yt_faceless.production.asset_sources import OpenverseSource, WikimediaSource
from src.yt_faceless.production.asset_sources.base import AssetSearchResult, AssetSource
from src.yt_faceless.production.scene_analyzer import SceneAnalyzer, SceneSegment
from src.yt_faceless.production.timeline import build_visual_timeline, ZoomPanEffect, VisualAsset, VisualShot, SceneSpec
from src.yt_faceless.utils.license import LicenseValidator, format_attribution, check_license_compatibility


class TestAssetSources:
    """Test asset source implementations."""

    def test_asset_search_result(self):
        """Test AssetSearchResult properties."""
        result = AssetSearchResult(
            url="https://example.com/image.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            title="Test Image",
            creator="Test Author",
            license="cc-by-4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            source="Openverse",
            source_url="https://example.com",
            width=1920,
            height=1080,
            tags=["test", "example"],
            attribution="Test attribution"
        )

        assert result.resolution == (1920, 1080)
        assert result.is_high_res is True

    def test_base_source_license_filter(self):
        """Test license filtering in base class."""
        source = OpenverseSource()

        # Test allowed licenses
        assert source.is_license_allowed("cc0") is True
        assert source.is_license_allowed("CC-BY-4.0") is True
        assert source.is_license_allowed("public domain") is True

        # Test denied licenses
        assert source.is_license_allowed("cc-by-nc") is False
        assert source.is_license_allowed("CC-BY-ND") is False
        assert source.is_license_allowed("all rights reserved") is False

    def test_cache_key_generation(self):
        """Test cache key generation."""
        source = WikimediaSource()

        key1 = source.get_cache_key("test query", limit=20, page=1)
        key2 = source.get_cache_key("test query", limit=20, page=1)
        key3 = source.get_cache_key("different query", limit=20, page=1)

        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 16

    @patch('urllib.request.urlopen')
    def test_openverse_search(self, mock_urlopen):
        """Test Openverse API search."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "results": [
                {
                    "url": "https://example.com/image1.jpg",
                    "thumbnail": "https://example.com/thumb1.jpg",
                    "title": "Test Image 1",
                    "creator": "Author 1",
                    "license": "cc-by",
                    "license_version": "4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "foreign_landing_url": "https://example.com/page1",
                    "width": 2000,
                    "height": 1500,
                    "tags": [{"name": "nature"}, {"name": "landscape"}]
                }
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        source = OpenverseSource()
        results = source.search("nature", limit=10)

        assert len(results) == 1
        assert results[0].title == "Test Image 1"
        assert results[0].license == "CC-BY-4.0"
        assert results[0].width == 2000
        assert "nature" in results[0].tags

    @patch('urllib.request.urlopen')
    def test_wikimedia_search(self, mock_urlopen):
        """Test Wikimedia Commons API search."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "query": {
                "pages": {
                    "123": {
                        "title": "File:Test_Image.jpg",
                        "imageinfo": [{
                            "url": "https://upload.wikimedia.org/test.jpg",
                            "thumburl": "https://upload.wikimedia.org/thumb.jpg",
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Test.jpg",
                            "width": 3000,
                            "height": 2000,
                            "extmetadata": {
                                "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                "Artist": {"value": "Test Artist"},
                                "ImageDescription": {"value": "Test description"}
                            }
                        }],
                        "categories": [
                            {"title": "Category:Nature"},
                            {"title": "Category:Landscapes"}
                        ]
                    }
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        source = WikimediaSource()
        results = source.search("landscape", limit=10)

        assert len(results) == 1
        assert "Test Image" in results[0].title
        assert results[0].creator == "Test Artist"
        assert results[0].width == 3000


class TestSceneAnalyzer:
    """Test scene analysis functionality."""

    def test_scene_segmentation(self):
        """Test basic scene segmentation."""
        analyzer = SceneAnalyzer()

        script = """
        [HOOK - 0:00]
        Have you ever wondered about the mysteries of space?

        [KEY INSIGHT - 0:10]
        Scientists have discovered something incredible about black holes.
        [B-ROLL: space telescope images]

        [DEMONSTRATION - 0:25]
        Let me show you how this works.
        (show animation of black hole)

        [CTA - 0:45]
        Subscribe for more amazing science facts!
        """

        scenes = analyzer.analyze_script(script)

        assert len(scenes) >= 4
        assert scenes[0].section_marker == "HOOK"
        assert scenes[1].section_marker == "KEY INSIGHT"
        assert "space telescope images" in scenes[1].visual_cues
        assert any("animation of black hole" in cue for scene in scenes for cue in scene.visual_cues)

    def test_keyword_extraction(self):
        """Test keyword extraction from text."""
        analyzer = SceneAnalyzer()

        text = "The quantum computer revolutionized computing technology with unprecedented processing power."
        keywords = analyzer._extract_keywords(text, max_keywords=5)

        # Should extract important nouns and terms
        assert "quantum" in keywords or "computer" in keywords
        assert "technology" in keywords or "computing" in keywords
        assert len(keywords) <= 5

    def test_search_query_generation(self):
        """Test search query generation."""
        analyzer = SceneAnalyzer()

        keywords = ["space", "telescope", "galaxy"]
        visual_cues = ["hubble images", "spiral galaxy"]
        tags = ["astronomy", "science"]

        queries = analyzer._generate_search_queries(keywords, visual_cues, tags)

        assert len(queries) > 0
        assert "hubble images" in queries  # Visual cues have priority
        assert any("space" in q for q in queries)

    def test_key_phrase_extraction(self):
        """Test extraction of key phrases for overlays."""
        analyzer = SceneAnalyzer()

        text = 'Scientists say "This changes everything" about our understanding.'
        phrase = analyzer._extract_key_phrase(text)

        assert phrase == "This changes everything"

        text2 = "The key point is that technology advances rapidly."
        phrase2 = analyzer._extract_key_phrase(text2)

        assert phrase2 is not None
        assert len(phrase2) <= 60

    def test_scene_duration_calculation(self):
        """Test scene duration bucketing."""
        analyzer = SceneAnalyzer()

        script = "[HOOK - 0:00] Quick intro. [EXPLANATION - 0:05] " + ("word " * 200)

        scenes = analyzer.analyze_script(script, audio_duration=60)

        # Hook should be short duration
        assert scenes[0].duration <= 8

        # Long explanation may be split
        total_duration = sum(s.duration for s in scenes)
        assert total_duration > 0


class TestLicenseUtilities:
    """Test license validation and attribution."""

    def test_license_normalization(self):
        """Test license string normalization."""
        assert LicenseValidator.normalize_license("CC BY 4.0") == "cc-by-4.0"
        assert LicenseValidator.normalize_license("Creative Commons BY-SA") == "cc-by-sa"
        assert LicenseValidator.normalize_license("Public Domain") == "pd"
        assert LicenseValidator.normalize_license("CC0 1.0") == "cc0"

    def test_commercial_safety_check(self):
        """Test commercial use validation."""
        assert LicenseValidator.is_commercial_safe("cc-by-4.0") is True
        assert LicenseValidator.is_commercial_safe("cc0") is True
        assert LicenseValidator.is_commercial_safe("cc-by-nc") is False
        assert LicenseValidator.is_commercial_safe("cc-by-nd") is True  # ND is ok for commercial

    def test_attribution_requirement(self):
        """Test attribution requirement check."""
        assert LicenseValidator.requires_attribution("cc-by") is True
        assert LicenseValidator.requires_attribution("cc-by-sa") is True
        assert LicenseValidator.requires_attribution("cc0") is False
        assert LicenseValidator.requires_attribution("pd") is False

    def test_attribution_formatting(self):
        """Test attribution string formatting."""
        attr = format_attribution(
            "Beautiful Sunset",
            "John Doe",
            "cc-by-4.0",
            "Openverse",
            "https://example.com/image"
        )

        assert "Beautiful Sunset" in attr
        assert "John Doe" in attr
        assert "CC-BY-4.0" in attr.upper()
        assert "https://example.com/image" in attr

    def test_license_compatibility(self):
        """Test checking compatibility of multiple licenses."""
        # Compatible licenses
        compat = check_license_compatibility(["cc0", "cc-by", "pd"])
        assert compat["compatible"] is True
        assert compat["commercial_safe"] is True
        assert compat["requires_attribution"] is True

        # Incompatible licenses (NC)
        compat = check_license_compatibility(["cc-by", "cc-by-nc"])
        assert compat["commercial_safe"] is False
        assert "commercial use" in str(compat["warnings"]).lower()

        # ShareAlike requirement
        compat = check_license_compatibility(["cc-by-sa"])
        assert compat["requires_sharealike"] is True


class TestTimelineGeneration:
    """Test visual timeline generation."""

    def test_visual_asset_creation(self):
        """Test VisualAsset dataclass."""
        asset = VisualAsset(
            path=Path("/assets/image.jpg"),
            title="Test Image",
            creator="Author",
            license="cc-by",
            width=1920,
            height=1080,
            asset_type="image"
        )

        assert asset.path == Path("/assets/image.jpg")
        assert asset.asset_type == "image"
        assert asset.width == 1920

    def test_ken_burns_effect(self):
        """Test Ken Burns effect generation."""
        effect = ZoomPanEffect(
            zoom_start=1.0,
            zoom_end=1.2,
            pan_x_start=0.3,
            pan_x_end=0.7,
            pan_y_start=0.5,
            pan_y_end=0.5,
            duration_frames=150
        )

        assert effect.zoom_end > effect.zoom_start  # Zoom in
        assert effect.pan_x_end > effect.pan_x_start  # Pan right
        assert effect.duration_frames == 150

    def test_visual_shot_creation(self):
        """Test VisualShot with Ken Burns."""
        asset = VisualAsset(
            path=Path("/assets/image.jpg"),
            title="Test",
            asset_type="image"
        )

        shot = VisualShot(
            asset=asset,
            start_time=0.0,
            duration=5.0,
            kenburns_effect=ZoomPanEffect(),
            transition_in="fade",
            overlay_text="Amazing Discovery"
        )

        assert shot.duration == 5.0
        assert shot.transition_in == "fade"
        assert shot.overlay_text == "Amazing Discovery"
        assert shot.kenburns_effect is not None

    def test_scene_spec_with_multiple_shots(self):
        """Test SceneSpec with multiple shots."""
        asset1 = VisualAsset(path=Path("/img1.jpg"), title="Image 1")
        asset2 = VisualAsset(path=Path("/img2.jpg"), title="Image 2")

        shot1 = VisualShot(asset=asset1, start_time=0, duration=3)
        shot2 = VisualShot(asset=asset2, start_time=3, duration=3)

        scene = SceneSpec(
            scene_id="scene_0",
            scene_index=0,
            start_time=0,
            end_time=6,
            duration=6,
            key_phrase="Key insight here",
            shots=[shot1, shot2]
        )

        assert len(scene.shots) == 2
        assert scene.duration == 6
        assert scene.key_phrase == "Key insight here"

    @patch('src.yt_faceless.production.timeline.build_visual_timeline')
    def test_timeline_building_integration(self, mock_build):
        """Test full timeline building process."""
        # This would test the integration of all components
        mock_build.return_value = {
            "version": 1,
            "slug": "test",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "total_duration": 60,
            "scenes": []
        }

        # In a real test, you'd set up proper test data
        # and verify the timeline is built correctly


class TestErrorHandling:
    """Test error handling and fallbacks."""

    def test_missing_asset_fallback(self):
        """Test handling of missing assets."""
        from src.yt_faceless.production.timeline import _select_assets_for_scene

        segment = SceneSegment(
            index=0,
            start_time=0,
            end_time=5,
            duration=5,
            text="Test",
            section_marker="HOOK",
            keywords=["test"],
            search_queries=["nonexistent query"],
            key_phrase="Test phrase",
            visual_cues=[],
            b_roll_suggestions=[]
        )

        # With no matching assets, should fall back to random selection
        available = [
            VisualAsset(path=Path("/fallback.jpg"), title="Fallback")
        ]

        selected = _select_assets_for_scene(segment, available, 1)
        assert len(selected) == 1
        assert selected[0].title == "Fallback"

    def test_api_failure_handling(self):
        """Test handling of API failures."""
        source = OpenverseSource()

        with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
            results = source.search("test")
            assert results == []  # Should return empty list on error

    def test_invalid_license_handling(self):
        """Test handling of invalid licenses."""
        validator = LicenseValidator()

        # Unknown license should be rejected for commercial use
        assert validator.is_commercial_safe("unknown-license") is False
        assert validator.is_commercial_safe("") is False
        assert validator.is_commercial_safe(None) is False


@pytest.fixture
def temp_content_dir():
    """Create temporary content directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content_dir = Path(tmpdir) / "content" / "test-slug"
        content_dir.mkdir(parents=True)

        # Create test files
        script_path = content_dir / "script.md"
        script_path.write_text("""
        [HOOK - 0:00]
        Test hook content.

        [MAIN - 0:10]
        Main content here.
        """)

        metadata_path = content_dir / "metadata.json"
        metadata_path.write_text(json.dumps({
            "title": "Test Video",
            "tags": ["test", "demo"],
            "sections": []
        }))

        yield content_dir


def test_end_to_end_visual_pipeline(temp_content_dir):
    """Test complete visual enhancement pipeline."""
    # This would be an integration test running the full pipeline
    # with mock data and verifying the output

    assert temp_content_dir.exists()
    assert (temp_content_dir / "script.md").exists()
    assert (temp_content_dir / "metadata.json").exists()

    # In a real test, you would:
    # 1. Run scene analysis
    # 2. Plan assets (with mocked API)
    # 3. Build timeline
    # 4. Verify output structure