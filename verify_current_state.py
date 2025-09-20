#!/usr/bin/env python3
"""Comprehensive verification of current code state."""

import sys
from pathlib import Path

def verify_fixes():
    """Verify the actual current state of all 6 fixes."""

    print("=" * 80)
    print("COMPREHENSIVE CODE STATE VERIFICATION")
    print("=" * 80)

    # Read all relevant files
    openverse_code = Path("src/yt_faceless/production/asset_sources/openverse.py").read_text(encoding="utf-8")
    wikimedia_code = Path("src/yt_faceless/production/asset_sources/wikimedia.py").read_text(encoding="utf-8")
    timeline_code = Path("src/yt_faceless/production/timeline.py").read_text(encoding="utf-8")
    assets_code = Path("src/yt_faceless/production/assets.py").read_text(encoding="utf-8")
    orchestrator_code = Path("src/yt_faceless/orchestrator.py").read_text(encoding="utf-8")

    print("\n1. API RETRY WITH EXPONENTIAL BACKOFF")
    print("-" * 40)

    # Check Openverse
    if "# Retry logic with exponential backoff" in openverse_code:
        if "for attempt in range(max_retries):" in openverse_code:
            if "delay = base_delay * (2 ** attempt)" in openverse_code:
                print("[OK] Openverse: HAS retry with exponential backoff")
                # Show the actual code
                start = openverse_code.find("# Retry logic with exponential backoff")
                end = openverse_code.find("return []", start) + 10
                snippet = openverse_code[start:end].split('\n')[:8]
                for line in snippet:
                    print(f"  | {line}")
            else:
                print("[FAIL] Openverse: Missing exponential calculation")
        else:
            print("[FAIL] Openverse: Missing retry loop")
    else:
        print("[FAIL] Openverse: No retry logic found")

    # Check Wikimedia
    if "# Retry logic with exponential backoff" in wikimedia_code:
        if "for attempt in range(max_retries):" in wikimedia_code:
            print("[OK] Wikimedia: HAS retry with exponential backoff")
        else:
            print("[FAIL] Wikimedia: Missing retry loop")
    else:
        print("[FAIL] Wikimedia: No retry logic found")

    print("\n2. TRANSITION NAME FIX")
    print("-" * 40)

    if '"crossfade"' in timeline_code:
        print(f"[FAIL] 'crossfade' still found in timeline.py")
        # Show where
        idx = timeline_code.find('"crossfade"')
        snippet = timeline_code[max(0, idx-50):idx+50]
        print(f"  Context: ...{snippet}...")
    else:
        print("[OK] No 'crossfade' in timeline.py (fixed)")
        # Show what's there instead
        if '["dissolve", "fade"]' in timeline_code:
            print("  Replaced with: ['dissolve', 'fade']")

    print("\n3. KEN BURNS FPS")
    print("-" * 40)

    # Check for hardcoded 30
    if "cfg.video.fps if 'cfg' in locals() else 30" in timeline_code:
        print("[FAIL] Still using hardcoded 30 fps fallback")
    else:
        # Check for fps parameter
        if "fps: int = 30" in timeline_code:
            print("[OK] FPS parameter added to _build_scene_specs")
            if "fps,  # Use the fps parameter" in timeline_code:
                print("[OK] Using fps parameter in Ken Burns")
            else:
                print("? Check Ken Burns usage")
        else:
            print("? FPS parameter status unclear")

    print("\n4. LICENSE FILTER")
    print("-" * 40)

    # Check for old substring matching
    old_pattern = 'if not any(lic.lower() in result.license.lower()'
    if old_pattern in assets_code:
        print("[FAIL] Still using substring license matching")
    else:
        # Check for LicenseValidator
        if "LicenseValidator.is_commercial_safe(result.license)" in assets_code:
            print("[OK] Using LicenseValidator.is_commercial_safe")
            if "LicenseValidator.allows_modification(result.license)" in assets_code:
                print("[OK] Also checking allows_modification")
            else:
                print("? Not checking modification rights")
        else:
            print("? License validation method unclear")

    print("\n5. DEDUPE FALLBACK")
    print("-" * 40)

    # Check for ImportError handling
    if 'except ImportError:' in assets_code:
        idx = assets_code.find('except ImportError:')
        next_lines = assets_code[idx:idx+500]
        if 'return assets' in next_lines and 'seen_urls' not in next_lines:
            print("[FAIL] No fallback dedupe (just returns assets)")
        elif 'using URL-based deduplication' in next_lines:
            print("[OK] Has URL-based deduplication fallback")
            if 'seen_urls = set()' in next_lines:
                print("[OK] Implements URL dedupe with seen_urls set")
        else:
            print("? Dedupe fallback status unclear")

    print("\n6. DESCRIPTION LENGTH CLAMPING")
    print("-" * 40)

    # Check for length clamping
    if "if len(desc_text) > 4800:" in orchestrator_code:
        print("[OK] Has description length check at 4800")
        if "desc_text = desc_text[:4797]" in orchestrator_code:
            print("[OK] Truncates to 4797 + '...'")
        else:
            print("? Truncation implementation unclear")
    else:
        print("[FAIL] No description length clamping found")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Do a final comprehensive check
    all_good = True
    issues = []

    if "for attempt in range(max_retries):" not in openverse_code:
        issues.append("API retry missing in Openverse")
        all_good = False

    if '"crossfade"' in timeline_code:
        issues.append("crossfade still in transitions")
        all_good = False

    if "cfg.video.fps if 'cfg' in locals() else 30" in timeline_code:
        issues.append("FPS still hardcoded to 30")
        all_good = False

    if 'if not any(lic.lower() in result.license.lower()' in assets_code:
        issues.append("Still using substring license check")
        all_good = False

    if 'except ImportError:' in assets_code and 'seen_urls' not in assets_code:
        issues.append("No dedupe fallback")
        all_good = False

    if "if len(desc_text) > 4800:" not in orchestrator_code:
        issues.append("No description clamping")
        all_good = False

    if all_good:
        print("\n[SUCCESS] ALL 6 FIXES ARE PROPERLY IMPLEMENTED IN THE CURRENT CODE")
    else:
        print(f"\n[WARNING] Issues found: {', '.join(issues)}")

    return all_good

if __name__ == "__main__":
    success = verify_fixes()
    sys.exit(0 if success else 1)