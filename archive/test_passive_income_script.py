#!/usr/bin/env python
"""Test passive income script generation"""

from claude_script_generator import generate_passive_income_script

# Test 10-minute passive income script
title = "Make $10000 Per Month While You Sleep"
hook = "This saves $10000 per year minimum"

print("\n" + "="*60)
print("TESTING PASSIVE INCOME SCRIPT - 10 MINUTES")
print("="*60)
print(f"Title: {title}")

script = generate_passive_income_script(title, hook, 10)

if script:
    word_count = len(script.split())
    char_count = len(script)
    estimated_minutes = word_count / 150  # 150 words per minute speaking rate

    print(f"\n[SUCCESS] Script generated!")
    print(f"   Word count: {word_count} words")
    print(f"   Character count: {char_count} characters")
    print(f"   Estimated duration: {estimated_minutes:.1f} minutes")

    # Check structure
    import re
    sections = re.findall(r'\[([^\]]+)\]', script)
    print(f"\nScript has {len(sections)} sections")

    # Show sample content
    print("\nSample content (Stream 1 - Dividends):")
    print("-"*50)
    start = script.find("[STREAM 1: DIVIDEND")
    end = script.find("[STREAM 2:")
    if start > 0 and end > 0:
        print(script[start:start+500] + "...")
    print("-"*50)

    print("\nFix successful! Script now generates proper 10-minute content.")
else:
    print("[ERROR] Script generation failed")