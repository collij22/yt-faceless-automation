#!/usr/bin/env python
"""Quick integration test for Phase 8 features."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config_loading():
    """Test that config loads with new webhook fields."""
    from yt_faceless.core.config import load_config

    print("Testing config loading...")
    config = load_config()

    # Check new webhook fields exist
    assert hasattr(config.webhooks, 'tiktok_upload_url')
    assert hasattr(config.webhooks, 'instagram_upload_url')
    assert hasattr(config.webhooks, 'x_upload_url')
    assert hasattr(config.webhooks, 'translation_url')
    assert hasattr(config.webhooks, 'moderation_url')
    assert hasattr(config.webhooks, 'scheduled_upload_url')

    print("[OK] Config loads successfully with new webhook fields")


def test_distribution_target():
    """Test DistributionTarget schema."""
    from yt_faceless.core.schemas import DistributionTarget

    print("Testing DistributionTarget schema...")

    target = DistributionTarget(
        platform="tiktok",
        account_handle="@test",
        webhook_url="https://test.webhook",
        api_credentials={"key": "value"},
        enabled=True,
        premium_account=False
    )

    assert target.platform == "tiktok"
    assert target.account_handle == "@test"
    assert target.webhook_url == "https://test.webhook"

    print("[OK] DistributionTarget schema works correctly")


def test_imports():
    """Test that all new modules can be imported."""
    print("Testing module imports...")

    try:
        from yt_faceless.distribution.cross_platform import CrossPlatformDistributor
        from yt_faceless.localization.translator import LocalizationManager
        from yt_faceless.guardrails.safety_checker import BrandSafetyChecker
        from yt_faceless.scheduling.calendar import ContentCalendar
        from yt_faceless.monetization.affiliates import AffiliateManager
        from yt_faceless.monetization.sponsorships import SponsorshipManager
        from yt_faceless.production.shorts import ShortsGenerator
        print("[OK] All modules import successfully")
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False

    return True


def test_cli_commands():
    """Test that CLI commands are registered."""
    import subprocess

    print("Testing CLI commands...")

    # Test that help shows new commands
    result = subprocess.run(
        [sys.executable, "-m", "yt_faceless.cli", "--help"],
        capture_output=True,
        text=True
    )

    help_text = result.stdout

    # Check for new commands
    commands = ["distribute", "localize", "safety", "calendar", "monetize", "shorts", "revenue"]
    missing = []

    for cmd in commands:
        if cmd not in help_text:
            missing.append(cmd)

    if missing:
        print(f"[FAIL] Missing commands: {missing}")
        return False

    print("[OK] All CLI commands are registered")
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("Phase 8 Integration Tests")
    print("=" * 50)

    tests = [
        test_config_loading,
        test_distribution_target,
        test_imports,
        test_cli_commands
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("[SUCCESS] All tests passed! Phase 8 implementation is working.")
    else:
        print("[ERROR] Some tests failed. Please review the errors above.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())