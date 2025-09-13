"""Tests for Phase 8 monetization features."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yt_faceless.core.config import AppConfig
from yt_faceless.core.schemas import (
    AffiliateProgram,
    AffiliatePlacement,
    AffiliatePlacementPosition,
    SponsorDeal,
)
from yt_faceless.monetization.affiliates import AffiliateManager, inject_affiliate_links
from yt_faceless.monetization.sponsorships import (
    SponsorshipManager,
    apply_sponsorship_disclosure,
)
from yt_faceless.production.shorts import ShortsGenerator, generate_shorts


class TestAffiliateManager:
    """Test affiliate link management."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.webhooks.shortener_url = "https://test.webhook/shorten"
        config.features = {"affiliate_injection": True}
        return config

    @pytest.fixture
    def manager(self, config):
        """Create affiliate manager."""
        return AffiliateManager(config)

    def test_generate_affiliate_url(self, manager):
        """Test affiliate URL generation."""
        # Setup test program
        manager.programs["TestProgram"] = AffiliateProgram(
            name="TestProgram",
            base_url="https://example.com/products",
            utm_defaults={"utm_source": "youtube", "utm_medium": "video"},
            shorten=False,
        )

        # Generate URL
        url = manager.generate_affiliate_url(
            "TestProgram",
            "ABC123",
            utm_overrides={"utm_campaign": "test"},
            slug="test-video",
        )

        assert "https://example.com/products/ABC123" in url
        assert "utm_source=youtube" in url
        assert "utm_medium=video" in url
        assert "utm_campaign=test" in url
        assert "utm_content=test-video" in url

    @pytest.mark.asyncio
    async def test_shorten_url(self, manager, config):
        """Test URL shortening."""
        # Mock webhook response
        with patch.object(manager.n8n_client, "execute_webhook") as mock_webhook:
            mock_webhook.return_value = {"short_url": "https://short.link/abc123"}

            short_url = await manager.shorten_url("https://example.com/very/long/url")

            assert short_url == "https://short.link/abc123"
            mock_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_inject_into_description(self, manager):
        """Test injecting affiliate links into description."""
        description = "Check out this amazing video!\n\nDon't forget to subscribe!"

        placements = [
            AffiliatePlacement(
                program_name="TestProgram",
                url="https://example.com/product1",
                description="Product mentioned at 2:30",
                position=AffiliatePlacementPosition.DESCRIPTION,
            ),
            AffiliatePlacement(
                program_name="TestProgram",
                url="https://example.com/product2",
                description="Alternative option",
                position=AffiliatePlacementPosition.DESCRIPTION,
            ),
        ]

        result = await manager.inject_into_description(description, placements)

        assert "MENTIONED IN THIS VIDEO" in result
        assert "Product mentioned at 2:30" in result
        assert "https://example.com/product1" in result
        assert "Alternative option" in result
        assert "affiliate links" in result.lower()

    @pytest.mark.asyncio
    async def test_inject_affiliate_links_integration(self, config, tmp_path):
        """Test full affiliate injection flow."""
        # Create test content
        slug = "test-video"
        content_dir = config.directories.content_dir / slug
        content_dir.mkdir(parents=True)

        metadata = {
            "title": "Test Video",
            "description": "Original description",
            "niche": "tech",
        }

        metadata_path = content_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))

        # Run injection
        with patch("yt_faceless.monetization.affiliates.AffiliateManager.shorten_url") as mock_shorten:
            mock_shorten.return_value = "https://short.link/test"

            result = await inject_affiliate_links(
                config, slug, metadata["description"], niche="tech", dry_run=False
            )

        assert "description" in result
        assert "affiliate_links" in result


class TestSponsorshipManager:
    """Test sponsorship management."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.features = {"sponsorships": True}
        return config

    @pytest.fixture
    def manager(self, config):
        """Create sponsorship manager."""
        return SponsorshipManager(config)

    def test_get_active_deals(self, manager):
        """Test getting active sponsorship deals."""
        now = datetime.now(timezone.utc)

        # Add test deals
        manager.deals = [
            SponsorDeal(
                sponsor="Active Sponsor",
                flight_start_iso=(now - timedelta(days=1)).isoformat(),
                flight_end_iso=(now + timedelta(days=1)).isoformat(),
                deliverables=["preroll_15s"],
                cta_text="Check out Active Sponsor!",
                landing_url="https://sponsor.com",
                disclosure_text="Sponsored content",
                placement=["description"],
            ),
            SponsorDeal(
                sponsor="Expired Sponsor",
                flight_start_iso=(now - timedelta(days=10)).isoformat(),
                flight_end_iso=(now - timedelta(days=5)).isoformat(),
                deliverables=["preroll_15s"],
                cta_text="Old sponsor",
                landing_url="https://old.com",
                disclosure_text="Expired",
                placement=["description"],
            ),
        ]

        active = manager.get_active_deals()
        assert len(active) == 1
        assert active[0].sponsor == "Active Sponsor"

    def test_generate_disclosure_text(self, manager):
        """Test FTC-compliant disclosure generation."""
        deals = [
            SponsorDeal(
                sponsor="Sponsor A",
                flight_start_iso="2025-01-01T00:00:00Z",
                flight_end_iso="2025-12-31T23:59:59Z",
                deliverables=["preroll"],
                cta_text="Check it out",
                landing_url="https://a.com",
                disclosure_text="Custom disclosure A",
                placement=["description"],
            ),
            SponsorDeal(
                sponsor="Sponsor B",
                flight_start_iso="2025-01-01T00:00:00Z",
                flight_end_iso="2025-12-31T23:59:59Z",
                deliverables=["desc_link"],
                cta_text="Learn more",
                landing_url="https://b.com",
                disclosure_text="Custom disclosure B",
                placement=["description"],
            ),
        ]

        disclosure = manager.generate_disclosure_text(deals)
        assert "Sponsor A" in disclosure
        assert "Sponsor B" in disclosure
        assert "paid promotion" in disclosure.lower()

    def test_inject_into_description(self, manager):
        """Test injecting sponsorship into description."""
        description = "Original video description"
        deals = [
            SponsorDeal(
                sponsor="Test Sponsor",
                flight_start_iso="2025-01-01T00:00:00Z",
                flight_end_iso="2025-12-31T23:59:59Z",
                deliverables=["desc_link"],
                cta_text="Amazing products!",
                landing_url="https://sponsor.com/youtube",
                disclosure_text="This video contains paid promotion",
                placement=["description"],
            )
        ]

        disclosure = "This video contains paid promotion"
        result = manager.inject_into_description(description, deals, disclosure)

        assert "TODAY'S SPONSOR" in result
        assert "Test Sponsor" in result
        assert "Amazing products!" in result
        assert "https://sponsor.com/youtube" in result
        assert disclosure in result

    def test_validate_compliance(self, manager):
        """Test FTC compliance validation."""
        description_with_disclosure = "This video is sponsored by Example Brand."
        description_without = "Check out this cool product!"

        deals = [
            SponsorDeal(
                sponsor="Example Brand",
                flight_start_iso="2025-01-01T00:00:00Z",
                flight_end_iso="2025-12-31T23:59:59Z",
                deliverables=["preroll"],
                cta_text="Buy now",
                landing_url="https://example.com",
                disclosure_text="Sponsored",
                placement=["description"],
            )
        ]

        # With disclosure
        result_compliant = manager.validate_compliance(description_with_disclosure, deals)
        assert result_compliant["compliant"] is True
        assert len(result_compliant["issues"]) == 0

        # Without disclosure
        result_noncompliant = manager.validate_compliance(description_without, deals)
        assert result_noncompliant["compliant"] is False
        assert len(result_noncompliant["issues"]) > 0


class TestShortsGenerator:
    """Test YouTube Shorts generation."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.content_dir = tmp_path / "content"
        config.video.ffmpeg_bin = "ffmpeg"
        config.features = {"shorts_generation": True}
        return config

    @pytest.fixture
    def generator(self, config):
        """Create Shorts generator."""
        return ShortsGenerator(config)

    def test_analyze_video_for_segments(self, generator, tmp_path):
        """Test video segment analysis."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        metadata_path = tmp_path / "metadata.json"
        metadata = {
            "sections": [
                {
                    "title": "Introduction",
                    "start_time": 0,
                    "end_time": 30,
                },
                {
                    "title": "Secret Revealed",
                    "start_time": 60,
                    "end_time": 120,
                },
                {
                    "title": "How to Apply",
                    "start_time": 150,
                    "end_time": 210,
                },
            ]
        }
        metadata_path.write_text(json.dumps(metadata))

        segments = generator.analyze_video_for_segments(video_path, metadata_path)

        assert len(segments) > 0
        assert segments[0][2] == "intro"  # First segment should be intro

        # Should identify promise/payoff sections
        promise_segments = [s for s in segments if s[2] == "promise"]
        assert len(promise_segments) > 0

    def test_generate_metadata(self, generator):
        """Test Shorts metadata generation."""
        from yt_faceless.core.schemas import ShortsSegment

        segment = ShortsSegment(
            segment_id="test_short_01",
            source_slug="original-video",
            start_sec=30,
            end_sec=75,
            output_path="/path/to/short.mp4",
            title="Short 1",
            description="",
            tags=[],
            hook_type="promise",
        )

        original_metadata = {
            "title": "Original Long Video Title That Is Very Descriptive",
            "tags": {
                "primary": ["tag1", "tag2", "tag3"],
                "competitive": ["tag4", "tag5"],
            },
            "category_id": "22",
        }

        result = generator.generate_metadata(segment, original_metadata)

        assert "#Shorts" in result["title"]
        assert len(result["title"]) <= 100
        assert "shorts" in result["tags"]
        assert "youtubeshorts" in result["tags"]
        assert result["category_id"] == "22"
        assert "segment_info" in result

    @patch("subprocess.run")
    def test_extract_segment(self, mock_run, generator, tmp_path):
        """Test video segment extraction."""
        video_path = tmp_path / "source.mp4"
        video_path.touch()
        output_path = tmp_path / "short.mp4"

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        success = generator.extract_segment(
            video_path, output_path, start_sec=30, end_sec=60, aspect_ratio="9:16"
        )

        assert success is True
        mock_run.assert_called_once()

        # Check FFmpeg command includes correct parameters
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" in call_args[0] or call_args[0] == "ffmpeg"
        assert "-ss" in call_args
        assert "-t" in call_args
        assert "9:16" in str(call_args) or "1080:1920" in str(call_args)

    @pytest.mark.asyncio
    async def test_generate_shorts_integration(self, config, tmp_path):
        """Test full Shorts generation flow."""
        slug = "test-video"
        content_dir = config.directories.content_dir / slug
        content_dir.mkdir(parents=True)

        # Create fake video file
        video_path = content_dir / "final.mp4"
        video_path.touch()

        # Create metadata
        metadata = {
            "title": "Original Video",
            "description": "Original description",
            "tags": ["tag1", "tag2"],
            "sections": [
                {"title": "Intro", "start_time": 0, "end_time": 30},
                {"title": "Main Content", "start_time": 30, "end_time": 300},
            ],
        }
        metadata_path = content_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))

        # Mock FFmpeg execution
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="Duration: 00:10:00")

            result = generate_shorts(config, slug, count=2, dry_run=True)

        assert len(result) == 2
        assert all(s.segment_id.startswith(slug) for s in result)
        assert all(s.hook_type in ["intro", "promise", "payoff", "custom"] for s in result)