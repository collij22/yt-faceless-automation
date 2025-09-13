"""Tests for Phase 8 distribution and localization features."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yt_faceless.core.config import AppConfig
from yt_faceless.core.schemas import DistributionTarget, LocalizationRequest
from yt_faceless.distribution.cross_platform import (
    CrossPlatformDistributor,
    distribute_content,
)
from yt_faceless.guardrails.safety_checker import BrandSafetyChecker, check_content_safety
from yt_faceless.localization.translator import LocalizationManager, translate_content
from yt_faceless.scheduling.calendar import ContentCalendar, schedule_content


class TestCrossPlatformDistributor:
    """Test cross-platform distribution."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.webhooks = {
            "tiktok_upload_url": "https://webhook.test/tiktok",
            "instagram_upload_url": "https://webhook.test/instagram",
            "x_upload_url": "https://webhook.test/x",
        }
        config.features = {"cross_platform": True}
        return config

    @pytest.fixture
    def distributor(self, config):
        """Create distributor."""
        return CrossPlatformDistributor(config)

    def test_adapt_for_tiktok(self, distributor, tmp_path):
        """Test TikTok platform adaptation."""
        video_path = tmp_path / "video.mp4"
        target = DistributionTarget(
            platform="tiktok",
            account_handle="@testaccount",
            webhook_url="https://webhook.test/tiktok",
            api_credentials={},
            enabled=True,
        )

        metadata = {
            "title": "Test Video Title",
            "description": "Test description",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
        }

        adaptations = distributor.adapt_for_platform(video_path, target, metadata)

        assert adaptations["aspect_ratio"] == "9:16"
        assert adaptations["max_duration"] == 60
        assert "#tag1" in adaptations["caption"]
        assert len([t for t in adaptations["caption"].split() if t.startswith("#")]) <= 5

    def test_adapt_for_instagram(self, distributor, tmp_path):
        """Test Instagram platform adaptation."""
        video_path = tmp_path / "video.mp4"
        target = DistributionTarget(
            platform="instagram",
            account_handle="@testaccount",
            webhook_url="https://webhook.test/instagram",
            api_credentials={},
            enabled=True,
        )

        metadata = {
            "title": "Test Video",
            "description": "A" * 600,  # Long description
            "tags": ["tag" + str(i) for i in range(40)],  # Many tags
        }

        adaptations = distributor.adapt_for_platform(video_path, target, metadata)

        assert adaptations["aspect_ratio"] == "9:16"
        assert adaptations["max_duration"] == 90
        assert adaptations["cover_frame"] is True
        assert len(adaptations["caption"]) <= 2200
        # Instagram allows up to 30 hashtags
        hashtags = [t for t in adaptations["caption"].split() if t.startswith("#")]
        assert len(hashtags) <= 30

    def test_adapt_for_x(self, distributor, tmp_path):
        """Test X (Twitter) platform adaptation."""
        video_path = tmp_path / "video.mp4"
        target = DistributionTarget(
            platform="x",
            account_handle="@testaccount",
            webhook_url="https://webhook.test/x",
            api_credentials={},
            enabled=True,
        )

        metadata = {
            "title": "A" * 300,  # Very long title
            "tags": ["tag1", "tag2", "tag3", "tag4"],
        }

        adaptations = distributor.adapt_for_platform(video_path, target, metadata)

        assert adaptations["aspect_ratio"] == "16:9"
        assert adaptations["max_duration"] == 140
        assert len(adaptations["caption"]) <= 280
        # X recommends 1-2 hashtags
        hashtags = [t for t in adaptations["caption"].split() if t.startswith("#")]
        assert len(hashtags) <= 2

    @pytest.mark.asyncio
    async def test_distribute_to_platform(self, distributor, tmp_path):
        """Test distributing to a platform."""
        video_path = tmp_path / "video.mp4"
        video_path.touch()

        target = DistributionTarget(
            platform="tiktok",
            account_handle="@testaccount",
            webhook_url="https://webhook.test/tiktok",
            api_credentials={"api_key": "test"},
            enabled=True,
        )

        adaptations = {"caption": "Test caption #test", "aspect_ratio": "9:16"}

        with patch.object(distributor.n8n_client, "execute_webhook") as mock_webhook:
            mock_webhook.return_value = {"status": "success", "url": "https://tiktok.com/@test/video/123"}

            result = await distributor.distribute_to_platform(video_path, target, adaptations)

            assert result["status"] == "success"
            assert "url" in result
            mock_webhook.assert_called_once()

    def test_schedule_distribution(self, distributor):
        """Test distribution scheduling."""
        targets = [
            DistributionTarget(
                platform="tiktok",
                account_handle="@test1",
                webhook_url="https://webhook.test/tiktok",
                api_credentials={},
                enabled=True,
            ),
            DistributionTarget(
                platform="instagram",
                account_handle="@test2",
                webhook_url="https://webhook.test/instagram",
                api_credentials={},
                enabled=True,
            ),
        ]

        base_time = datetime.now(timezone.utc) + timedelta(hours=2)
        schedule = distributor.schedule_distribution("test-slug", targets, base_time, stagger_minutes=30)

        assert "tiktok" in schedule
        assert "instagram" in schedule
        # Instagram should be scheduled after TikTok
        assert schedule["instagram"] > schedule["tiktok"]

    def test_get_optimal_time(self, distributor):
        """Test optimal posting time calculation."""
        # Test morning time
        base_time = datetime(2025, 1, 15, 5, 0, tzinfo=timezone.utc)
        optimal = distributor._get_optimal_time("tiktok", base_time)
        assert optimal.hour in [6, 7, 8, 9, 10]  # TikTok morning window

        # Test evening time
        base_time = datetime(2025, 1, 15, 18, 0, tzinfo=timezone.utc)
        optimal = distributor._get_optimal_time("instagram", base_time)
        assert optimal.hour in [19, 20, 21]  # Instagram evening window


class TestLocalizationManager:
    """Test content localization."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.webhooks = {
            "translation_url": "https://webhook.test/translate",
            "tts_url": "https://webhook.test/tts",
        }
        config.features = {"localization": True}
        return config

    @pytest.fixture
    def manager(self, config):
        """Create localization manager."""
        return LocalizationManager(config)

    @pytest.mark.asyncio
    async def test_translate_text(self, manager):
        """Test text translation."""
        with patch.object(manager.n8n_client, "execute_webhook") as mock_webhook:
            mock_webhook.return_value = {"translated_text": "Hola Mundo"}

            result = await manager.translate_text("Hello World", "es", "en")

            assert result == "Hola Mundo"
            mock_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_translate_metadata(self, manager):
        """Test metadata translation."""
        metadata = {
            "title": "Amazing Video",
            "description": {"text": "This is a great video"},
            "tags": ["tutorial", "howto", "guide"],
        }

        with patch.object(manager, "translate_text") as mock_translate:
            # Mock translation responses
            mock_translate.side_effect = [
                "Video Increíble",  # Title
                "Este es un gran video",  # Description
                "tutorial",  # Tag 1
                "cómo",  # Tag 2
                "guía",  # Tag 3
            ]

            result = await manager.translate_metadata(metadata, "es", "en")

            assert result["title"] == "Video Increíble"
            assert result["description"]["text"] == "Este es un gran video"
            assert "tutorial" in result["tags"]
            assert "guía" in result["tags"]
            assert result["localization"]["target_language"] == "es"

    def test_parse_srt(self, manager):
        """Test SRT subtitle parsing."""
        srt_content = """1
00:00:00,000 --> 00:00:02,500
Hello World

2
00:00:03,000 --> 00:00:05,000
This is a test

3
00:00:05,500 --> 00:00:08,000
Final subtitle"""

        segments = manager._parse_srt(srt_content)

        assert len(segments) == 3
        assert segments[0]["text"] == "Hello World"
        assert segments[1]["text"] == "This is a test"
        assert segments[2]["index"] == 3

    def test_generate_srt(self, manager):
        """Test SRT subtitle generation."""
        segments = [
            {
                "index": 1,
                "start_str": "00:00:00,000",
                "end_str": "00:00:02,500",
                "text": "Translated text 1",
            },
            {
                "index": 2,
                "start_str": "00:00:03,000",
                "end_str": "00:00:05,000",
                "text": "Translated text 2",
            },
        ]

        srt = manager._generate_srt(segments)

        assert "1\n00:00:00,000 --> 00:00:02,500\nTranslated text 1" in srt
        assert "2\n00:00:03,000 --> 00:00:05,000\nTranslated text 2" in srt

    def test_get_market_priority(self, manager):
        """Test language market priority."""
        # Large markets
        assert manager.get_market_priority("es") == 3  # Spanish
        assert manager.get_market_priority("zh") == 3  # Chinese
        assert manager.get_market_priority("hi") == 3  # Hindi

        # Medium markets
        assert manager.get_market_priority("fr") == 2  # French
        assert manager.get_market_priority("de") == 2  # German

        # Unknown market
        assert manager.get_market_priority("unknown") == 0


class TestBrandSafetyChecker:
    """Test brand safety and compliance checking."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.webhooks = {"moderation_url": "https://webhook.test/moderate"}
        config.features = {"brand_safety": True}
        return config

    @pytest.fixture
    def checker(self, config):
        """Create safety checker."""
        return BrandSafetyChecker(config)

    def test_check_prohibited_terms(self, checker):
        """Test prohibited term detection."""
        # Text with prohibited terms
        text = "This video shows how to make a bomb for science class"
        violations = checker.check_prohibited_terms(text)
        assert len(violations) > 0
        assert any(v["category"] == "violence" for v in violations)

        # Clean text
        clean_text = "This video shows how to bake a cake"
        violations = checker.check_prohibited_terms(clean_text)
        assert len(violations) == 0

    def test_check_sensitive_topics(self, checker):
        """Test sensitive topic detection."""
        text = "Let's discuss politics and religion in this controversial video"
        violations = checker.check_sensitive_topics(text)
        assert len(violations) > 0
        assert any("politics" in v.get("topic", "") for v in violations)
        assert any("religion" in v.get("topic", "") for v in violations)

    def test_check_required_disclosures(self, checker):
        """Test disclosure requirement checking."""
        # Affiliate content without disclosure
        text = "Buy this product using my link below"
        context = {"has_affiliates": True}
        violations = checker.check_required_disclosures(text, context)
        assert len(violations) > 0
        assert any(v["category"] == "affiliate" for v in violations)

        # Properly disclosed
        text_disclosed = "Buy this product using my affiliate link below. I earn a commission from purchases."
        violations = checker.check_required_disclosures(text_disclosed, context)
        assert len(violations) == 0

    def test_check_platform_compliance(self, checker):
        """Test platform-specific compliance."""
        # YouTube metadata
        metadata = {
            "title": "CLICK HERE NOW!!! SUBSCRIBE!!!",  # Prohibited terms
            "description": "A" * 6000,  # Too long
            "tags": ["tag" + str(i) for i in range(100)],  # Many tags
        }

        violations = checker.check_platform_compliance(metadata, "youtube")
        assert len(violations) > 0
        assert any("exceeds_length" in v.get("issue", "") for v in violations)
        assert any("prohibited_term" in v.get("issue", "") for v in violations)

    def test_check_advertiser_friendly(self, checker):
        """Test advertiser-friendliness check."""
        # Controversial content
        metadata = {
            "title": "SHOCKING Truth About Natural Disasters",
            "description": "Disturbing footage of tragedy and controversial opinions",
        }

        result = checker.check_advertiser_friendly(metadata)
        assert result["score"] < 100
        assert not result["advertiser_friendly"]
        assert len(result["issues"]) > 0

        # Clean content
        clean_metadata = {
            "title": "How to Bake the Perfect Chocolate Cake",
            "description": "Easy recipe for beginners with step-by-step instructions",
        }

        result = checker.check_advertiser_friendly(clean_metadata)
        assert result["score"] >= 80
        assert result["advertiser_friendly"]


class TestContentCalendar:
    """Test content calendar and scheduling."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config."""
        config = MagicMock(spec=AppConfig)
        config.directories.data_dir = tmp_path / "data"
        config.directories.content_dir = tmp_path / "content"
        config.webhooks = {"scheduled_upload_url": "https://webhook.test/upload"}
        config.features = {"content_calendar": True}
        return config

    @pytest.fixture
    def calendar(self, config):
        """Create content calendar."""
        return ContentCalendar(config)

    def test_get_optimal_publish_time(self, calendar):
        """Test optimal publishing time calculation."""
        # Monday morning
        date = datetime(2025, 1, 20, 0, 0, tzinfo=timezone.utc)  # Monday
        optimal = calendar.get_optimal_publish_time(date, niche="business")
        assert optimal.hour in [7, 8, 9]  # Business content earlier

        # Weekend entertainment
        date = datetime(2025, 1, 25, 0, 0, tzinfo=timezone.utc)  # Saturday
        optimal = calendar.get_optimal_publish_time(date, niche="entertainment")
        assert optimal.hour in [11, 12, 13, 14, 15, 16]  # Entertainment later on weekends

    def test_schedule_content(self, calendar):
        """Test content scheduling."""
        slug = "test-video"
        publish_date = datetime.now(timezone.utc) + timedelta(days=2)

        result = calendar.schedule_content(slug, publish_date=publish_date)

        assert result["slug"] == slug
        assert result["scheduled_time"] == publish_date
        assert result["status"] == "scheduled"

        # Check it was saved
        upcoming = calendar.get_upcoming_schedule(days_ahead=7)
        assert any(item["slug"] == slug for item in upcoming)

    def test_check_scheduling_conflicts(self, calendar):
        """Test conflict detection."""
        # Add existing scheduled item
        existing_time = datetime.now(timezone.utc) + timedelta(hours=2)
        calendar.calendar["scheduled"] = [
            {"slug": "existing-video", "scheduled_time": existing_time.isoformat(), "status": "scheduled"}
        ]

        # Try to schedule at same time
        conflicts = calendar._check_scheduling_conflicts(existing_time)
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "time_proximity"

        # Schedule far enough away (5 hours later)
        no_conflict_time = existing_time + timedelta(hours=5)
        conflicts = calendar._check_scheduling_conflicts(no_conflict_time)
        assert len(conflicts) == 0

    def test_mark_as_published(self, calendar):
        """Test marking content as published."""
        # Schedule content
        slug = "test-video"
        calendar.calendar["scheduled"] = [
            {
                "slug": slug,
                "scheduled_time": datetime.now(timezone.utc).isoformat(),
                "status": "scheduled",
            }
        ]

        # Mark as published
        success = calendar.mark_as_published(slug, video_id="abc123", url="https://youtube.com/watch?v=abc123")

        assert success is True
        assert len(calendar.calendar["scheduled"]) == 0
        assert len(calendar.calendar["published"]) == 1
        assert calendar.calendar["published"][0]["video_id"] == "abc123"