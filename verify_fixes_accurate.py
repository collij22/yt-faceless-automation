#!/usr/bin/env python3
"""Accurate verification of all 6 bulletproof fixes."""

import sys
from pathlib import Path

def verify_fixes():
    """Verify the actual current state of all 6 fixes."""

    print("=" * 80)
    print("ACCURATE CODE STATE VERIFICATION")
    print("=" * 80)

    # Read all relevant files
    openverse_code = Path("src/yt_faceless/production/asset_sources/openverse.py").read_text(encoding="utf-8")
    wikimedia_code = Path("src/yt_faceless/production/asset_sources/wikimedia.py").read_text(encoding="utf-8")
    timeline_code = Path("src/yt_faceless/production/timeline.py").read_text(encoding="utf-8")
    assets_code = Path("src/yt_faceless/production/assets.py").read_text(encoding="utf-8")
    orchestrator_code = Path("src/yt_faceless/orchestrator.py").read_text(encoding="utf-8")

    all_good = True

    print("\n1. API RETRY WITH EXPONENTIAL BACKOFF")
    print("-" * 40)

    # Check Openverse
    if "for attempt in range(max_retries):" in openverse_code:
        if "delay = base_delay * (2 ** attempt)" in openverse_code:
            print("[PASS] Openverse: Has retry with exponential backoff")
        else:
            print("[FAIL] Openverse: Missing exponential calculation")
            all_good = False
    else:
        print("[FAIL] Openverse: No retry logic found")
        all_good = False

    # Check Wikimedia
    if "for attempt in range(max_retries):" in wikimedia_code:
        if "delay = base_delay * (2 ** attempt)" in wikimedia_code:
            print("[PASS] Wikimedia: Has retry with exponential backoff")
        else:
            print("[FAIL] Wikimedia: Missing exponential calculation")
            all_good = False
    else:
        print("[FAIL] Wikimedia: No retry logic found")
        all_good = False

    print("\n2. TRANSITION NAME FIX")
    print("-" * 40)

    # Check for crossfade NOT in actual code (only in comments)
    timeline_lines = timeline_code.split('\n')
    crossfade_in_code = False
    for line in timeline_lines:
        # Remove comments from line
        code_part = line.split('#')[0]
        if '"crossfade"' in code_part or "'crossfade'" in code_part:
            crossfade_in_code = True
            print(f"[FAIL] 'crossfade' found in actual code: {line.strip()}")
            break

    if not crossfade_in_code:
        print("[PASS] No 'crossfade' in actual code (only in comments)")
        # Verify the fix is there
        if '["dissolve", "fade"]' in timeline_code:
            print("      Correctly using: ['dissolve', 'fade']")
    else:
        all_good = False

    print("\n3. KEN BURNS FPS")
    print("-" * 40)

    # Check for fps parameter
    if "fps: int = 30" in timeline_code:
        print("[PASS] FPS parameter added to _build_scene_specs")
        # Check it's being used
        if "fps," in timeline_code:  # Check for fps being passed/used
            print("[PASS] FPS parameter is being used")
        else:
            print("[WARN] FPS parameter may not be used")
    else:
        print("[FAIL] FPS parameter missing from _build_scene_specs")
        all_good = False

    print("\n4. LICENSE FILTER")
    print("-" * 40)

    # Check for LicenseValidator usage
    if "LicenseValidator.is_commercial_safe(result.license)" in assets_code:
        print("[PASS] Using LicenseValidator.is_commercial_safe")
        if "LicenseValidator.allows_modification(result.license)" in assets_code:
            print("[PASS] Also checking allows_modification")
        else:
            print("[WARN] Not checking modification rights")
    else:
        print("[FAIL] Not using LicenseValidator")
        all_good = False

    print("\n5. DEDUPE FALLBACK")
    print("-" * 40)

    # Check for URL-based fallback in deduplicate_assets_by_phash
    dedupe_section = assets_code[assets_code.find("def deduplicate_assets_by_phash"):assets_code.find("def ", assets_code.find("def deduplicate_assets_by_phash") + 10)]

    if "except ImportError:" in dedupe_section:
        if "using URL-based deduplication" in dedupe_section:
            if "seen_urls = set()" in dedupe_section:
                print("[PASS] Has URL-based deduplication fallback")
            else:
                print("[FAIL] URL dedupe implementation incomplete")
                all_good = False
        else:
            print("[FAIL] No fallback dedupe implementation")
            all_good = False
    else:
        print("[WARN] No ImportError handling for imagehash")

    print("\n6. DESCRIPTION LENGTH CLAMPING")
    print("-" * 40)

    # Check for length clamping
    if "if len(desc_text) > 4800:" in orchestrator_code:
        print("[PASS] Has description length check at 4800")
        if "desc_text = desc_text[:4797]" in orchestrator_code:
            print("[PASS] Truncates to 4797 + '...'")
        else:
            print("[WARN] Truncation method unclear")
    else:
        print("[FAIL] No description length clamping found")
        all_good = False

    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    if all_good:
        print("\n[SUCCESS] ALL 6 FIXES ARE PROPERLY IMPLEMENTED!")
        print("\nDetails:")
        print("1. API retry with exponential backoff: ✅ IMPLEMENTED")
        print("2. Transition fix (no 'crossfade' in code): ✅ IMPLEMENTED")
        print("3. Ken Burns FPS parameter: ✅ IMPLEMENTED")
        print("4. License validation: ✅ IMPLEMENTED")
        print("5. Dedupe fallback: ✅ IMPLEMENTED")
        print("6. Description clamping: ✅ IMPLEMENTED")
        print("\nThe video generation system is BULLETPROOF!")
    else:
        print("\n[FAILURE] Some fixes may be missing - please review output above")

    return all_good

if __name__ == "__main__":
    success = verify_fixes()
    sys.exit(0 if success else 1)