#!/usr/bin/env python
"""Test the anxiety script generation to ensure 10-minute content"""

from claude_script_generator import generate_production_script

# Test the exact title that was having issues
title = "Beat Anxiety in 10 Minutes"
hook = "The results will shock you"
target_minutes = 10
target_words = 1500

print("\n" + "="*60)
print("TESTING ANXIETY SCRIPT GENERATION")
print("="*60)
print(f"Title: {title}")
print(f"Target: {target_minutes} minutes ({target_words} words)")

# Generate the script
script = generate_production_script(title, hook, target_minutes, target_words)

if script:
    # Count words and estimate duration
    word_count = len(script.split())
    estimated_minutes = word_count / 150  # 150 words per minute

    print(f"\n[SUCCESS] Script generated!")
    print(f"   Word count: {word_count} words")
    print(f"   Estimated duration: {estimated_minutes:.1f} minutes")

    # Check if it meets the target
    if word_count >= 1400:  # Allow some flexibility
        print("   [OK] STATUS: Meets 10-minute target!")
    else:
        print(f"   [WARN] WARNING: Short by {1500 - word_count} words")

    # Check for proper routing
    if "5-4-3-2-1 GROUNDING" in script:
        print("   [OK] Routing: Correctly using anxiety script generator")
    elif "[Detailed explanation" in script or "[Common belief" in script:
        print("   [ERROR] Routing: Using placeholder template!")
    else:
        print("   [WARN] Routing: Unknown generator")

    # Check for placeholders
    import re
    placeholders = re.findall(r'\[[\w\s]+\.\.\.\]', script)
    if placeholders:
        print(f"   [ERROR] Found {len(placeholders)} placeholders: {placeholders[:3]}")
    else:
        print("   [OK] No placeholders found - real content!")

    # Check timestamps
    if "[END - 13:" in script or "[END - 12:" in script:
        print("   [OK] Timestamps: Shows 12+ minutes (appropriate for content)")
    elif "[END - 10:" in script:
        print("   [OK] Timestamps: Shows 10 minutes")
    elif "[END - 5:" in script:
        print("   [WARN] Timestamps: Using 5-minute version")

    # Save to file for inspection
    with open("test_anxiety_output.md", "w", encoding="utf-8") as f:
        f.write(script)
    print("\nFull script saved to test_anxiety_output.md")

    # Show first technique to verify quality
    print("\nSample of TECHNIQUE 1 (first 500 chars):")
    print("-"*50)
    start = script.find("[TECHNIQUE 1:")
    if start >= 0:
        print(script[start:start+500] + "...")
else:
    print("[ERROR] Script generation failed")