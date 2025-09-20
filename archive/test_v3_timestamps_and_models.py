#!/usr/bin/env python
"""Test V3 features: Accurate timestamps and model selection"""

from claude_script_generator_v3 import generate_production_script
import re

print("\n" + "="*60)
print("TESTING V3: TIMESTAMPS AND MODEL SELECTION")
print("="*60)

# Test different models
models = ["claude", "haiku", "sonnet"]
test_title = "5 Skills That Will Define 2025"

for model in models:
    print(f"\n[TEST] Model: {model.upper()}")
    print("-" * 40)

    # Generate script with each model
    script = generate_production_script(
        test_title,
        "",
        10,  # 10 minute target
        1500,  # 1500 words target
        model=model
    )

    # Extract metrics
    word_count = len(script.split())
    duration_150wpm = word_count / 150
    duration_130wpm = word_count / 130

    print(f"Word count: {word_count} words")
    print(f"Duration at 150 wpm: {duration_150wpm:.1f} minutes")
    print(f"Duration at 130 wpm: {duration_130wpm:.1f} minutes")

    # Check END timestamp
    end_match = re.search(r'\[END - ([\d:]+)\]', script)
    if end_match:
        end_timestamp = end_match.group(1)
        # Parse timestamp
        if ':' in end_timestamp:
            minutes, seconds = map(int, end_timestamp.split(':'))
            total_minutes = minutes + seconds/60
            print(f"END timestamp: [{end_timestamp}] = {total_minutes:.1f} minutes")

            # Verify it matches actual duration
            expected_minutes = duration_130wpm  # Google TTS rate
            difference = abs(total_minutes - expected_minutes)

            if difference < 0.5:  # Within 30 seconds
                print("[PASS] END timestamp matches actual duration!")
            else:
                print(f"[WARN] END timestamp off by {difference:.1f} minutes")
    else:
        print("[FAIL] No END timestamp found!")

    # Check for model metadata
    if f"Model used: {model.upper()}" in script or f"Model: Using {model.upper()}" in script:
        print(f"[PASS] Model {model.upper()} is recorded in metadata")

    # Check for placeholders
    placeholders = re.findall(r'\[.*?\.\.\.\]', script)
    if placeholders:
        print(f"[FAIL] Found placeholders: {placeholders[:3]}")
    else:
        print("[PASS] No placeholders found")

print("\n" + "="*60)
print("TIMESTAMP ACCURACY TEST")
print("="*60)

# Test with a longer script
print("\n[TEST] 30-minute script timestamp")
script = generate_production_script(
    "Complete Guide to Python Programming",
    "",
    30,  # 30 minute target
    4500,  # 4500 words
    model="sonnet"
)

word_count = len(script.split())
duration_130wpm = word_count / 130

print(f"Word count: {word_count} words")
print(f"Expected duration: {duration_130wpm:.1f} minutes")

# Extract END timestamp
end_match = re.search(r'\[END - ([\d:]+)\]', script)
if end_match:
    end_timestamp = end_match.group(1)
    minutes, seconds = map(int, end_timestamp.split(':'))
    total_minutes = minutes + seconds/60
    print(f"END timestamp: [{end_timestamp}] = {total_minutes:.1f} minutes")

    difference = abs(total_minutes - duration_130wpm)
    if difference < 1.0:  # Within 1 minute for longer videos
        print("[PASS] Timestamp accurate for long-form content!")
    else:
        print(f"[WARN] Timestamp off by {difference:.1f} minutes")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("Key improvements in V3:")
print("1. END timestamps now match actual script length")
print("2. Model selection (claude/haiku/sonnet) supported")
print("3. Model choice propagated through entire pipeline")
print("4. No more hardcoded [END - 10:05] regardless of length")
print("\nUsage:")
print("  python run_full_production_pipeline_v3.py --model sonnet")
print("  python run_full_production_pipeline_v3.py --model haiku")
print("  python run_full_production_pipeline_v3.py --model claude")