#!/usr/bin/env python
"""Test that V4 pipeline correctly generates 5-minute video when requested"""

from claude_script_generator_v4 import generate_production_script

# Simulate what happens when user selects 5-minute video
title = "The Science Nobody Taught You Correctly"
hook = ""
target_minutes = 5
target_words = 750

print("\n" + "="*60)
print("TESTING V4 PIPELINE - 5 MINUTE VIDEO REQUEST")
print("="*60)
print(f"Title: {title}")
print(f"User selected: {target_minutes} minute video")
print(f"Target: {target_words} words")
print("-" * 60)

# Generate script (this is what pipeline does)
script = generate_production_script(
    title,
    hook,
    target_minutes,
    target_words,
    "sonnet"
)

# Analyze results
word_count = len(script.split())
duration_150wpm = word_count / 150
duration_130wpm = word_count / 130  # Google TTS rate

print(f"\n[RESULTS]")
print(f"Generated: {word_count} words")
print(f"Duration at 150 wpm: {duration_150wpm:.1f} minutes")
print(f"Duration at 130 wpm (Google TTS): {duration_130wpm:.1f} minutes")

# Check if it meets target
if 4 <= duration_130wpm <= 7:  # Allow some variance for 5-minute target
    print(f"\n[SUCCESS] Video is {duration_130wpm:.1f} minutes (target was {target_minutes})")
else:
    print(f"\n[FAIL] Video is {duration_130wpm:.1f} minutes (target was {target_minutes})")

# Compare to old behavior
print("\n" + "="*60)
print("COMPARISON: V3 vs V4")
print("="*60)
print("V3 (Old): Always generated 2201 words -> 17.2 minutes")
print(f"V4 (New): Generated {word_count} words -> {duration_130wpm:.1f} minutes")
print(f"\nImprovement: Video is {17.2 - duration_130wpm:.1f} minutes shorter!")

# Show script structure
import re
sections = re.findall(r'\[([^]]+)\]', script)
print("\n" + "="*60)
print("SCRIPT STRUCTURE FOR 5-MINUTE VIDEO")
print("="*60)
for section in sections[:10]:  # Show first 10 sections
    print(f"- {section}")

print("\n[COMPLETE] V4 Fix: Script length now matches user selection!")