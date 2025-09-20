"""Pytest for MCP/Webhook health helper functions.

These tests avoid real network calls by mocking requests to ensure logic works
and JSON output shape is correct. Integration testing should be done by running
`python mcp_health_check.py --json` outside of pytest.
"""

from __future__ import annotations

from unittest.mock import patch

import json

import mcp_health_check as hc


def test_build_webhook_url_fallback():
    env = {"N8N_BASE_URL": "http://localhost:5678"}
    url = hc.build_webhook_url(env, "/webhook/tts-generation")
    assert url == "http://localhost:5678/webhook/tts-generation"


def test_masking_short_and_long_values():
    assert hc._mask(None) == "Not set"
    assert hc._mask("short") == "***"
    assert hc._mask("0123456789abcdef").startswith("0123")
    assert hc._mask("0123456789abcdef").endswith("cdef")


def test_run_health_checks_shapes():
    # Mock all HTTP calls to avoid network
    class FakeResp:
        def __init__(self, status_code=200, json_data=None, text="ok"):
            self.status_code = status_code
            self._json_data = json_data
            self.text = text

        def json(self):
            if self._json_data is None:
                raise ValueError("no json")
            return self._json_data

    with patch("requests.get", return_value=FakeResp(200)), patch(
        "requests.post", return_value=FakeResp(200, json_data={"status": "ok"})
    ):
        summary = hc.run_health_checks(timeout_seconds=1)
        assert summary.status in {"healthy", "degraded", "unhealthy"}
        assert "n8n_base" in summary.endpoints
        assert "tts_webhook" in summary.endpoints
        # Ensure serializable
        payload = {
            "status": summary.status,
            "warnings": summary.warnings,
            "errors": summary.errors,
            "env": summary.env,
            "endpoints": {k: hc.asdict(v) for k, v in summary.endpoints.items()},
        }
        assert json.dumps(payload)


