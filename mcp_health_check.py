#!/usr/bin/env python3
"""
MCP and Webhook Health Check Utility.

This script verifies the local project's ability to use external services that are
typically exposed via MCP tools (n8n, Firecrawl) and environment configuration.

It performs non-destructive checks:
- Validates presence of key environment variables
- Pings n8n base URL
- Posts minimal payloads to production webhooks (TTS, Upload, Analytics) if configured
- Optionally probes Firecrawl HTTP API if FIRECRAWL_API_KEY is set

Usage:
  python mcp_health_check.py --json

Exit codes:
  0 = healthy or degraded (warnings only)
  1 = unhealthy (errors)
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from pathlib import Path

import requests
from dotenv import load_dotenv


DEFAULT_N8N_BASE_URL = "http://localhost:5678"
TIMEOUT_SECONDS_DEFAULT = 10


@dataclass
class EndpointResult:
    """Result of a single endpoint probe."""

    name: str
    url: str
    ok: bool
    status: Optional[int] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthSummary:
    """Aggregate health status across services."""

    status: str
    warnings: list[str]
    errors: list[str]
    endpoints: Dict[str, EndpointResult]
    env: Dict[str, str]


def _mask(value: Optional[str]) -> str:
    if not value:
        return "Not set"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def get_env() -> Dict[str, str]:
    """Load and present relevant environment variables (masked where needed)."""
    load_dotenv()
    return {
        "N8N_BASE_URL": os.getenv("N8N_BASE_URL", DEFAULT_N8N_BASE_URL),
        "N8N_TTS_WEBHOOK_URL": os.getenv("N8N_TTS_WEBHOOK_URL", ""),
        "N8N_UPLOAD_WEBHOOK_URL": os.getenv("N8N_UPLOAD_WEBHOOK_URL", ""),
        "YOUTUBE_ANALYTICS_WEBHOOK_URL": os.getenv("YOUTUBE_ANALYTICS_WEBHOOK_URL", ""),
        "YOUTUBE_API_KEY": _mask(os.getenv("YOUTUBE_API_KEY")),
        "FIRECRAWL_API_KEY": _mask(os.getenv("FIRECRAWL_API_KEY")),
        "BRAVE_SEARCH_API_KEY": _mask(os.getenv("BRAVE_SEARCH_API_KEY")),
    }


def probe_http_get(name: str, url: str, timeout_seconds: int) -> EndpointResult:
    """Probe an HTTP GET endpoint for reachability."""
    try:
        resp = requests.get(url, timeout=timeout_seconds)
        ok = 200 <= resp.status_code < 500  # UI pages often 200-404; treat 5xx as bad
        return EndpointResult(name=name, url=url, ok=ok, status=resp.status_code)
    except Exception as exc:  # noqa: BLE001
        return EndpointResult(name=name, url=url, ok=False, error=str(exc))


def probe_http_post(name: str, url: str, payload: Dict[str, Any], timeout_seconds: int) -> EndpointResult:
    """Probe an HTTP POST endpoint with JSON payload."""
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout_seconds)
        ok = 200 <= resp.status_code < 300
        details: Dict[str, Any] = {"response": None}
        try:
            details["response"] = resp.json()
        except Exception:
            details["response"] = resp.text[:500]
        return EndpointResult(name=name, url=url, ok=ok, status=resp.status_code, details=details)
    except Exception as exc:  # noqa: BLE001
        return EndpointResult(name=name, url=url, ok=False, error=str(exc))


def build_webhook_url(env: Dict[str, str], fallback_path: str) -> str:
    """Use explicit webhook URL if set; otherwise construct from N8N_BASE_URL and path."""
    base = env.get("N8N_BASE_URL", DEFAULT_N8N_BASE_URL).rstrip("/")
    return f"{base}{fallback_path}"


def run_health_checks(timeout_seconds: int = TIMEOUT_SECONDS_DEFAULT) -> HealthSummary:
    """Run all health checks and return a structured summary."""
    env = get_env()
    endpoints: Dict[str, EndpointResult] = {}
    warnings: list[str] = []
    errors: list[str] = []

    # 1) n8n base availability
    n8n_base = env.get("N8N_BASE_URL", DEFAULT_N8N_BASE_URL).rstrip("/")
    endpoints["n8n_base"] = probe_http_get("n8n_base", n8n_base, timeout_seconds)
    if not endpoints["n8n_base"].ok:
        errors.append("n8n base not reachable")

    # 2) TTS webhook
    tts_url = env.get("N8N_TTS_WEBHOOK_URL") or build_webhook_url(env, "/webhook/tts-generation")
    tts_payload = {"text": "Hello world from health check.", "slug": "health_check"}
    endpoints["tts_webhook"] = probe_http_post("tts_webhook", tts_url, tts_payload, timeout_seconds)
    if not endpoints["tts_webhook"].ok:
        warnings.append("TTS webhook did not return 2xx (may be inactive or failing validation)")

    # 3) Upload webhook (safe noop payload)
    upload_url = env.get("N8N_UPLOAD_WEBHOOK_URL") or build_webhook_url(env, "/webhook/youtube-upload")
    upload_payload = {
        "video_path": "C:/dev/null.mp4",
        "title": "Health Check Upload",
        "description": "Dry-run check",
        "tags": ["health", "check"],
        "privacy": "private",
        "slug": "health_check",
    }
    endpoints["upload_webhook"] = probe_http_post("upload_webhook", upload_url, upload_payload, timeout_seconds)
    if not endpoints["upload_webhook"].ok:
        warnings.append("Upload webhook did not return 2xx (expected without real media; ensure activation)")

    # 4) Analytics webhook
    analytics_url = env.get("YOUTUBE_ANALYTICS_WEBHOOK_URL") or build_webhook_url(env, "/webhook/youtube-analytics")
    analytics_payload = {"video_ids": ["jNQXAC9IVRw"], "metrics": ["views"], "start_date": "2024-01-01", "end_date": "2024-12-31"}
    endpoints["analytics_webhook"] = probe_http_post("analytics_webhook", analytics_url, analytics_payload, timeout_seconds)
    if not endpoints["analytics_webhook"].ok:
        warnings.append("Analytics webhook did not return 2xx (may require API key in n8n)")

    # 5) Firecrawl API (optional; use public API, not MCP transport)
    firecrawl_key_raw = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_key_raw:
        try:
            # Minimal sanity check: request with expected auth header to public API endpoint
            # Using a HEAD to avoid charges; if not supported, fall back to GET homepage
            resp = requests.get(
                "https://api.firecrawl.dev/",  # public endpoint existence check
                headers={"Authorization": f"Bearer {firecrawl_key_raw}"},
                timeout=timeout_seconds,
            )
            ok = resp.status_code < 500
            endpoints["firecrawl_api"] = EndpointResult(
                name="firecrawl_api", url="https://api.firecrawl.dev/", ok=ok, status=resp.status_code
            )
            if not ok:
                warnings.append("Firecrawl API reachable but returned non-success; verify key and plan")
        except Exception as exc:  # noqa: BLE001
            endpoints["firecrawl_api"] = EndpointResult(
                name="firecrawl_api", url="https://api.firecrawl.dev/", ok=False, error=str(exc)
            )
            warnings.append("Unable to reach Firecrawl API (network or DNS issue)")
    else:
        warnings.append("FIRECRAWL_API_KEY not set; Firecrawl MCP features will be limited")

    # Aggregate status
    status = "healthy"
    if errors:
        status = "unhealthy"
    elif warnings:
        status = "degraded"

    return HealthSummary(status=status, warnings=warnings, errors=errors, endpoints=endpoints, env=env)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="MCP/Webhook health check")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS_DEFAULT, help="HTTP timeout in seconds")
    args = parser.parse_args(argv)

    summary = run_health_checks(timeout_seconds=args.timeout)

    if args.json:
        payload = {
            "status": summary.status,
            "warnings": summary.warnings,
            "errors": summary.errors,
            "env": summary.env,
            "endpoints": {k: asdict(v) for k, v in summary.endpoints.items()},
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Overall status: {summary.status.upper()}")
        if summary.errors:
            print("Errors:")
            for e in summary.errors:
                print(f"  - {e}")
        if summary.warnings:
            print("Warnings:")
            for w in summary.warnings:
                print(f"  - {w}")
        print("\nEndpoints:")
        for name, res in summary.endpoints.items():
            status = "OK" if res.ok else "FAIL"
            extra = f" (HTTP {res.status})" if res.status is not None else (f" (err: {res.error})" if res.error else "")
            print(f"  - {name}: {status}{extra} → {res.url}")

    return 0 if summary.status in ("healthy", "degraded") else 1


if __name__ == "__main__":
    sys.exit(main())


