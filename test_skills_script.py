#!/usr/bin/env python
"""Test the improved skills script generation"""

from claude_script_generator import generate_production_script

# Test the exact title that was failing
title = "7 Skills You Need Before 2026"
hook = "The results will shock you"
target_minutes = 10
target_words = 1500

print("\n" + "="*60)
print("TESTING IMPROVED SKILLS SCRIPT")
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
        print("   STATUS: Meets 10-minute target!")
    else:
        print(f"   WARNING: Short by {1500 - word_count} words")

    # Count skill sections
    import re
    skill_sections = re.findall(r'\[SKILL \d+:', script)
    print(f"\n   Number of skills in script: {len(skill_sections)}")

    # Show a sample to verify quality
    print("\nSample of Skill 1 (first 500 chars):")
    print("-"*50)
    start = script.find("[SKILL 1:")
    if start >= 0:
        print(script[start:start+500] + "...")
else:
    print("[ERROR] Script generation failed")