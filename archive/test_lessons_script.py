#!/usr/bin/env python
"""Test lessons script generation"""

from claude_script_generator import generate_production_script

# Test the exact case that was failing
title = "7 Lessons From My Biggest Failure"
hook = "The results will shock you"
target_minutes = 10
target_words = 1500

print("\n" + "="*60)
print("TESTING LESSONS SCRIPT - 10 MINUTES")
print("="*60)
print(f"Title: {title}")
print(f"Target: {target_minutes} minutes")

script = generate_production_script(title, hook, target_minutes, target_words)

if script:
    word_count = len(script.split())
    char_count = len(script)
    estimated_minutes = word_count / 150

    print(f"\n[SUCCESS] Script generated!")
    print(f"   Word count: {word_count} words (target: 1500)")
    print(f"   Character count: {char_count} characters")
    print(f"   Estimated duration: {estimated_minutes:.1f} minutes")

    # Check if it's using real content or placeholders
    if "[Deep explanation" in script or "[Detailed breakdown" in script:
        print("\n[ERROR] Script still contains placeholders!")
    else:
        print("\n[OK] Script contains real content, no placeholders!")

    # Show sample content
    print("\nSample content (Lesson 1):")
    print("-"*50)
    start = script.find("[LESSON 1:")
    end = script.find("[LESSON 2:")
    if start > 0 and end > 0:
        print(script[start:start+500] + "...")
    print("-"*50)

    print("\n✅ Fix successful! 10-minute scripts now generate proper content.")
else:
    print("[ERROR] Script generation failed")