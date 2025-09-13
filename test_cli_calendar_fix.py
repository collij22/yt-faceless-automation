#!/usr/bin/env python
"""Test that the CLI calendar dry-run print key is fixed."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_cli_calendar_print():
    """Test CLI calendar dry-run print uses correct key."""
    print("\n[TEST] CLI calendar dry-run print key...")

    try:
        with open("src/yt_faceless/cli.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for the correct key usage
        has_correct_key = "result['would_schedule']['scheduled_time']" in content
        has_wrong_key = "result['would_schedule']['publish_date']" in content

        if has_correct_key and not has_wrong_key:
            print("  [PASS] CLI uses correct 'scheduled_time' key")
            return True
        elif has_wrong_key:
            print("  [FAIL] CLI still uses wrong 'publish_date' key")
            return False
        else:
            print("  [WARN] Could not find the print statement")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_calendar_function_return():
    """Test that schedule_content returns the expected keys."""
    print("\n[TEST] Calendar schedule_content return value...")

    try:
        from yt_faceless.schedule.calendar import CalendarStore
        from yt_faceless.core.config import AppConfig
        import asyncio
        from datetime import datetime, timezone
        import tempfile

        # Create temp config
        temp_dir = Path(tempfile.mkdtemp())

        class MockConfig:
            class Dirs:
                data_dir = temp_dir
            directories = Dirs()

        config = MockConfig()

        # Import the async function
        from yt_faceless.schedule.calendar import schedule_content

        # Test dry-run mode
        result = asyncio.run(schedule_content(
            config,
            "test-slug",
            dry_run=True
        ))

        # Check return structure
        if "would_schedule" in result:
            item = result["would_schedule"]
            if "scheduled_time" in item:
                print("  [PASS] Dry-run returns 'scheduled_time' in would_schedule")
                return True
            else:
                print(f"  [FAIL] would_schedule missing 'scheduled_time', has: {item.keys()}")
                return False
        else:
            print(f"  [FAIL] Missing 'would_schedule' in result: {result.keys()}")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests for CLI calendar fix."""
    print("=" * 60)
    print("CLI CALENDAR FIX VERIFICATION")
    print("=" * 60)

    tests = [
        ("CLI print key", test_cli_calendar_print),
        ("Calendar return value", test_calendar_function_return),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, passed_test in results:
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] CLI calendar dry-run fix verified!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())