"""Tests for Phase 6: Upload & Publishing functionality."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_faceless.core.schemas import (
    QualityScores,
    VerificationStatus,
    YouTubeUploadPayload,
    YouTubeUploadResponse,
)
from yt_faceless.orchestrator import Orchestrator


class TestUploadFunctionality:
    """Test upload and publishing features."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock configuration."""
        config = MagicMock()
        config.enhanced_config.directories.content_dir = tmp_path / "content"
        config.enhanced_config.directories.output_dir = tmp_path / "output"
        config.enhanced_config.directories.data_dir = tmp_path / "data"
        return config

    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator instance."""
        with patch("yt_faceless.orchestrator.load_enhanced_config") as mock_load:
            mock_load.return_value = mock_config.enhanced_config
            with patch("yt_faceless.orchestrator.N8NClient"):
                orch = Orchestrator(mock_config)
                return orch

    def test_publish_with_valid_data(self, orchestrator, tmp_path):
        """Test successful video upload."""
        # Setup test data
        slug = "test-video"
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)

        # Create metadata file
        metadata = {
            "title": "Test Video Title",
            "description": {"text": "Test description"},
            "tags": {"primary": ["test", "video"], "competitive": ["youtube"]},
            "category_id": 28,
            "made_for_kids": False,
            "language": "en",
            "chapters": [{"start": "00:00", "title": "Introduction"}],
        }
        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata))

        # Create video file
        video_file = content_dir / "final.mp4"
        video_file.write_bytes(b"fake video content")

        # Mock upload response
        mock_response = YouTubeUploadResponse(
            execution_id="exec_123",
            video_id="video_abc123",
            status="uploaded",
            transaction_id="tx_test",
            upload_duration_ms=5000,
            quality_scores=QualityScores(
                technical_quality=85,
                seo_optimization=75,
                monetization_readiness=60,
                policy_compliance=95,
            ),
            verification_status=VerificationStatus(
                thumbnail_verified=False,
                metadata_verified=True,
                processing_status="processing",
                estimated_processing_time_min=5,
            ),
        )

        orchestrator.n8n_client.upload_video = Mock(return_value=mock_response)

        # Execute publish
        response = orchestrator.publish(slug=slug, privacy="private")

        # Verify
        assert response.video_id == "video_abc123"
        assert response.status == "uploaded"
        orchestrator.n8n_client.upload_video.assert_called_once()

        # Check manifest was saved
        manifest_file = tmp_path / "output" / slug / "upload_manifest.json"
        assert manifest_file.exists()

    def test_idempotency_check(self, orchestrator, tmp_path):
        """Test idempotency prevents duplicate uploads."""
        slug = "test-video"

        # Setup directories
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)
        output_dir = tmp_path / "output" / slug
        output_dir.mkdir(parents=True)

        # Create metadata
        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps({"title": "Test"}))

        # Create video file
        video_file = content_dir / "final.mp4"
        video_content = b"fake video content"
        video_file.write_bytes(video_content)

        # Calculate checksum
        checksum = hashlib.sha256(video_content).hexdigest()

        # Create existing manifest
        manifest = {
            "slug": slug,
            "checksum": checksum,
            "response": {
                "video_id": "existing_video_123",
                "status": "uploaded",
                "execution_id": "exec_old",
                "transaction_id": "tx_old",
                "upload_duration_ms": 0,
            },
        }
        manifest_file = output_dir / "upload_manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        # Attempt upload without force
        response = orchestrator.publish(slug=slug)

        # Should return existing upload
        assert response.video_id == "existing_video_123"
        # upload_video should not be called
        orchestrator.n8n_client.upload_video.assert_not_called()

    def test_quality_validation(self, orchestrator, tmp_path):
        """Test quality gates validation."""
        slug = "test-video"
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)

        # Create metadata with invalid title (too long)
        metadata = {
            "title": "x" * 101,  # Exceeds 100 char limit
            "description": {"text": "Test"},
        }
        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata))

        video_file = content_dir / "final.mp4"
        video_file.write_bytes(b"video")

        # Mock n8n_client to raise validation error
        orchestrator.n8n_client.upload_video.side_effect = ValueError("Title exceeds 100 characters")

        # Should raise error
        with pytest.raises(ValueError) as exc_info:
            orchestrator.publish(slug=slug)

        # Check for either Pydantic validation error or custom error
        error_msg = str(exc_info.value)
        assert "String should have at most 100 characters" in error_msg or "Title exceeds" in error_msg

    def test_schedule_upload(self, orchestrator, tmp_path):
        """Test scheduled upload."""
        slug = "test-video"
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)

        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps({"title": "Scheduled Video"}))

        video_file = content_dir / "final.mp4"
        video_file.write_bytes(b"video")

        schedule_time = "2025-01-01T15:00:00Z"

        mock_response = YouTubeUploadResponse(
            execution_id="exec_123",
            video_id="video_123",
            status="scheduled",
            transaction_id="tx_test",
            upload_duration_ms=3000,
            publish_at_iso=schedule_time,
        )

        orchestrator.n8n_client.upload_video = Mock(return_value=mock_response)

        response = orchestrator.publish(
            slug=slug, schedule_iso=schedule_time, privacy="private"
        )

        assert response.status == "scheduled"
        assert response.publish_at_iso == schedule_time

    def test_dry_run_mode(self, orchestrator, tmp_path):
        """Test dry run doesn't perform actual upload."""
        slug = "test-video"
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)

        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps({"title": "Test"}))

        video_file = content_dir / "final.mp4"
        video_file.write_bytes(b"video")

        response = orchestrator.publish(slug=slug, dry_run=True)

        assert response.video_id == "dry_run_video_id"
        assert response.status == "uploaded"
        # No actual upload should occur
        orchestrator.n8n_client.upload_video.assert_not_called()

    def test_force_upload_bypasses_idempotency(self, orchestrator, tmp_path):
        """Test force flag bypasses idempotency check."""
        slug = "test-video"

        # Setup with existing manifest
        content_dir = tmp_path / "content" / slug
        content_dir.mkdir(parents=True)
        output_dir = tmp_path / "output" / slug
        output_dir.mkdir(parents=True)

        metadata_file = content_dir / "metadata.json"
        metadata_file.write_text(json.dumps({"title": "Test"}))

        video_file = content_dir / "final.mp4"
        video_file.write_bytes(b"video")

        # Create existing manifest
        manifest_file = output_dir / "upload_manifest.json"
        manifest_file.write_text(json.dumps({
            "slug": slug,
            "checksum": "old_checksum",
            "response": {"video_id": "old_video"}
        }))

        mock_response = YouTubeUploadResponse(
            execution_id="new_exec",
            video_id="new_video_123",
            status="uploaded",
            transaction_id="tx_new",
            upload_duration_ms=4000,
        )

        orchestrator.n8n_client.upload_video = Mock(return_value=mock_response)

        # Upload with force
        response = orchestrator.publish(slug=slug, force=True)

        assert response.video_id == "new_video_123"
        orchestrator.n8n_client.upload_video.assert_called_once()


class TestUploadPayloadValidation:
    """Test upload payload validation."""

    def test_tags_length_validation(self):
        """Test tags combined length validation."""
        # Valid tags
        payload = YouTubeUploadPayload(
            video_path="/path/to/video.mp4",
            title="Test Video",
            description="Test description",
            tags=["tag1", "tag2", "tag3"],
            slug="test",
            checksum_sha256="abc123",
            transaction_id="tx_123",
        )
        assert len(",".join(payload.tags)) <= 500

        # Invalid tags (too long)
        with pytest.raises(ValueError) as exc_info:
            YouTubeUploadPayload(
                video_path="/path/to/video.mp4",
                title="Test",
                description="Test",
                tags=["x" * 100 for _ in range(10)],  # Way too long
                slug="test",
                checksum_sha256="abc123",
                transaction_id="tx_123",
            )
        assert "exceeds 500 characters" in str(exc_info.value)

    def test_chapter_timestamp_validation(self):
        """Test chapter timestamp format validation."""
        from yt_faceless.core.schemas import ChapterMarker

        # Valid format
        chapter = ChapterMarker(start="00:00", title="Introduction")
        assert chapter.start == "00:00"

        # Invalid format
        with pytest.raises(ValueError) as exc_info:
            ChapterMarker(start="0:0", title="Invalid")
        assert "Invalid timestamp format" in str(exc_info.value)

    def test_privacy_status_validation(self):
        """Test privacy status validation."""
        # Valid status
        payload = YouTubeUploadPayload(
            video_path="/path/to/video.mp4",
            title="Test",
            description="Test",
            tags=[],
            privacy_status="public",
            slug="test",
            checksum_sha256="abc123",
            transaction_id="tx_123",
        )
        assert payload.privacy_status == "public"

        # Invalid status
        with pytest.raises(ValueError):
            YouTubeUploadPayload(
                video_path="/path/to/video.mp4",
                title="Test",
                description="Test",
                tags=[],
                privacy_status="invalid_status",
                slug="test",
                checksum_sha256="abc123",
                transaction_id="tx_123",
            )