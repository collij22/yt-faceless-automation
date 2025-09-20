#!/usr/bin/env python
"""Test the anxiety script in the context of the full pipeline"""

from claude_script_generator import generate_production_script
import os

# Simulate what the pipeline does
title = "Beat Anxiety in 10 Minutes"
hook = "The results will shock you"
target_minutes = 10
target_words = 1500

print("\n" + "="*60)
print("TESTING ANXIETY SCRIPT IN PIPELINE CONTEXT")
print("="*60)
print(f"Selected idea: {title}")
print(f"Target length: {target_minutes} minutes (~{target_words} words)")
print("")
print("Generating script...")

# Generate the script (this is what pipeline does)
script = generate_production_script(title, hook, target_minutes, target_words)

if script:
    # Count words and estimate duration
    word_count = len(script.split())
    estimated_minutes = word_count / 150  # 150 words per minute

    print(f"[SUCCESS] Script generated!")
    print(f"Word count: {word_count} words")
    print(f"Estimated duration: {estimated_minutes:.1f} minutes at 150 wpm")

    # Google TTS actually speaks slower, around 120-130 wpm
    google_tts_minutes = word_count / 130
    print(f"Google TTS duration: {google_tts_minutes:.1f} minutes at 130 wpm")

    # Check if meets target
    if google_tts_minutes >= 9.5:  # Allow small variance
        print("\n[OK] Script will produce 10-minute video with Google TTS")
    elif google_tts_minutes >= 8:
        print(f"\n[WARN] Script may be slightly short: {google_tts_minutes:.1f} minutes")
        print(f"  Consider expanding by {int((10 - google_tts_minutes) * 130)} words")
    else:
        print(f"\n[ERROR] Script too short: only {google_tts_minutes:.1f} minutes")
        print(f"  Need to add {int((10 - google_tts_minutes) * 130)} more words")

    # Save test output
    test_dir = "content/test_anxiety_fix"
    os.makedirs(test_dir, exist_ok=True)

    script_path = os.path.join(test_dir, "script.md")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"\nScript saved to: {script_path}")
    print("Ready for TTS generation!")

else:
    print("[ERROR] Script generation failed")