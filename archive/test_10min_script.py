#!/usr/bin/env python
"""Test 10-minute script generation"""

from run_full_production_pipeline import YouTubeProductionSystem

pipeline = YouTubeProductionSystem()

# Test "I Tested X" story format for 10 minutes
test_idea = {
    "title": "I Tested 11 AI Tools - These 5 Won",
    "hook": "The results shocked me",
    "keywords": ["ai", "tools", "productivity"],
    "target_length": {"minutes": 10, "words": 1500},
    "use_ai_script": True
}

print("\n" + "="*60)
print("TESTING 10-MINUTE SCRIPT GENERATION")
print("="*60)
print(f"Title: {test_idea['title']}")
print(f"Target: {test_idea['target_length']['minutes']} minutes")
print(f"Target words: {test_idea['target_length']['words']}")

# Generate script
print("\n[INFO] Generating script...")
script = pipeline.generate_ai_script(test_idea, 10, 1500)

if script:
    print("\nScript Generated Successfully!")
    print("-"*60)

    # Show structure
    import re
    sections = re.findall(r'\[([^\]]+)\]', script)
    print(f"\nScript Structure ({len(sections)} sections):")
    for i, section in enumerate(sections[:15], 1):  # Show first 15 sections
        print(f"  {i}. {section}")

    if len(sections) > 15:
        print(f"  ... and {len(sections) - 15} more sections")

    # Calculate metrics
    word_count = len(script.split())
    char_count = len(script)

    # Estimate reading time (150 words per minute average speaking rate)
    estimated_minutes = word_count / 150

    print(f"\nMetrics:")
    print(f"  Word count: {word_count} (target: {test_idea['target_length']['words']})")
    print(f"  Character count: {char_count}")
    print(f"  Estimated duration: {estimated_minutes:.1f} minutes")

    # Show a sample from the middle
    print(f"\nMid-section sample (chars 2000-2500):")
    print("-"*40)
    print(script[2000:2500] if len(script) > 2500 else script[1000:1500])
    print("...")

else:
    print("\n[ERROR] Script generation failed")

# Test another type - list format
print("\n" + "="*60)
print("TESTING LIST FORMAT FOR 10 MINUTES")
print("="*60)

list_idea = {
    "title": "15 ChatGPT Tricks That Save Hours",
    "hook": "Number 7 is insane",
    "keywords": ["chatgpt", "ai", "productivity"],
    "target_length": {"minutes": 10, "words": 1500},
    "use_ai_script": True
}

script2 = pipeline.generate_ai_script(list_idea, 10, 1500)
if script2:
    word_count2 = len(script2.split())
    estimated_minutes2 = word_count2 / 150
    print(f"List script generated:")
    print(f"  Word count: {word_count2}")
    print(f"  Estimated duration: {estimated_minutes2:.1f} minutes")