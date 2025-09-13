"""Tests for configuration module."""

from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from typing import Iterator

import pytest

from yt_faceless.core.config import load_config as load_enhanced_config
from yt_faceless.core.errors import ConfigurationError


@contextmanager
def set_env(env: dict[str, str]) -> Iterator[None]:
    """Context manager to temporarily set environment variables."""
    old = {k: os.environ.get(k) for k in env}
    try:
        os.environ.update(env)
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class MockProcess:
    """Mock subprocess result."""
    
    def __init__(self, returncode: int = 0, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr


def test_load_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful configuration loading."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess, 
        "run", 
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "FIRECRAWL_API_KEY": "fc_test_key",
            "YOUTUBE_API_KEY": "yt_test_key",
            "TTS_PROVIDER": "elevenlabs",
            "ELEVENLABS_API_KEY": "el_test_key",
            "ELEVENLABS_VOICE_ID": "voice_test",
            "FFMPEG_BIN": "ffmpeg",
        }
    ):
        cfg = load_enhanced_config()
        assert cfg.webhooks.tts_url == "https://n8n.example/tts"
        assert cfg.webhooks.upload_url == "https://n8n.example/upload"
        assert cfg.apis.firecrawl_key == "fc_test_key"
        assert cfg.apis.youtube_api_key == "yt_test_key"
        assert cfg.tts.elevenlabs_api_key == "el_test_key"
        assert cfg.tts.elevenlabs_voice_id == "voice_test"


def test_load_config_missing_required_webhooks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing required webhooks raise ConfigurationError."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "",
            "N8N_UPLOAD_WEBHOOK_URL": "",
        }
    ):
        with pytest.raises(ConfigurationError) as exc_info:
            _ = load_enhanced_config()
        assert "N8N_TTS_WEBHOOK_URL is required" in str(exc_info.value)


def test_load_config_invalid_tts_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid TTS provider fails validation."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "TTS_PROVIDER": "invalid_provider",
            "FFMPEG_BIN": "ffmpeg",
        }
    ):
        with pytest.raises(ConfigurationError) as exc_info:
            _ = load_enhanced_config()
        assert "Unknown TTS provider" in str(exc_info.value)


def test_load_config_ffmpeg_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing FFmpeg fails validation."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg not found
    def mock_run(*args, **kwargs):
        raise FileNotFoundError("ffmpeg not found")
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "TTS_PROVIDER": "elevenlabs",
            "ELEVENLABS_API_KEY": "el_test_key",
            "ELEVENLABS_VOICE_ID": "voice_test",
            "FFMPEG_BIN": "ffmpeg",
        }
    ):
        with pytest.raises(ConfigurationError) as exc_info:
            _ = load_enhanced_config()
        assert "FFmpeg not found" in str(exc_info.value)


def test_load_config_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test health check functionality."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "TTS_PROVIDER": "elevenlabs",
            "ELEVENLABS_API_KEY": "el_test_key",
            "ELEVENLABS_VOICE_ID": "voice_test",
            "FFMPEG_BIN": "ffmpeg",
        }
    ):
        cfg = load_enhanced_config()
        health = cfg.health_check()
        
        assert "status" in health
        assert "checks" in health
        assert "warnings" in health
        assert "errors" in health
        
        # Should have warnings about missing optional APIs
        assert len(health["warnings"]) > 0
        assert any("Firecrawl" in w for w in health["warnings"])


def test_load_config_score_weights_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that score weights must sum to 1.0."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "TTS_PROVIDER": "elevenlabs",
            "ELEVENLABS_API_KEY": "el_test_key",
            "ELEVENLABS_VOICE_ID": "voice_test",
            "FFMPEG_BIN": "ffmpeg",
            # Invalid weights that don't sum to 1.0
            "SCORE_WEIGHT_RPM": "0.5",
            "SCORE_WEIGHT_TREND": "0.5",
            "SCORE_WEIGHT_COMPETITION": "0.5",
            "SCORE_WEIGHT_VIRALITY": "0.5",
            "SCORE_WEIGHT_MONETIZATION": "0.5",
        }
    ):
        with pytest.raises(ConfigurationError) as exc_info:
            _ = load_enhanced_config()
        assert "Score weights must sum to 1.0" in str(exc_info.value)


def test_backward_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test backward compatibility with legacy config interface."""
    from yt_faceless.config import load_config as load_legacy_config
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    with set_env(
        {
            "N8N_TTS_WEBHOOK_URL": "https://n8n.example/tts",
            "N8N_UPLOAD_WEBHOOK_URL": "https://n8n.example/upload",
            "TTS_PROVIDER": "elevenlabs",
            "ELEVENLABS_API_KEY": "el_test_key",
            "ELEVENLABS_VOICE_ID": "voice_test",
            "BRAVE_SEARCH_API_KEY": "brave_key",
            "FFMPEG_BIN": "ffmpeg",
        }
    ):
        # Legacy config should work
        cfg = load_legacy_config()
        assert cfg.n8n_tts_webhook_url == "https://n8n.example/tts"
        assert cfg.n8n_upload_webhook_url == "https://n8n.example/upload"
        assert cfg.brave_search_api_key == "brave_key"
        assert cfg.ffmpeg_bin == "ffmpeg"