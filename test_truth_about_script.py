#!/usr/bin/env python
"""Test the Truth About script generation to ensure 10-minute content"""

from claude_script_generator import generate_production_script

# Test the exact title that was having issues
title = "The Truth About Talent"
hook = "IQ is a lie. Here's what actually determines intelligence."
target_minutes = 10
target_words = 1500

print("\n" + "="*60)
print("TESTING 'TRUTH ABOUT' SCRIPT GENERATION")
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
    if "True intelligence isn't what you know" in script:
        print("   [OK] Routing: Correctly using intelligence script generator")
    else:
        print("   [WARN] Routing: May be using wrong generator")

    # Count trait sections
    import re
    trait_sections = re.findall(r'\[TRAIT \d+:', script)
    print(f"   [OK] Number of trait sections: {len(trait_sections)}")

    # Check timestamps
    if "[END - 10:05]" in script:
        print("   [OK] Timestamps: Correctly showing 10+ minutes")
    elif "[END - 5:" in script:
        print("   [WARN] Timestamps: Using 5-minute version")

    # Save to file for inspection
    with open("test_truth_about_output.md", "w", encoding="utf-8") as f:
        f.write(script)
    print("\nFull script saved to test_truth_about_output.md")

    # Show a sample
    print("\nSample of TRAIT 1 section (first 400 chars):")
    print("-"*50)
    start = script.find("[TRAIT 1:")
    if start >= 0:
        print(script[start:start+400] + "...")
else:
    print("[ERROR] Script generation failed")