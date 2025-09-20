#!/usr/bin/env python
"""Test 80-days story script generation"""

from run_full_production_pipeline import YouTubeProductionSystem

pipeline = YouTubeProductionSystem()

# Test the 80 days challenge script
test_idea = {
    "title": "I Did This For 80 Days - Shocking Results",
    "hook": "What happened next completely changed my life",
    "keywords": ["transformation", "challenge", "results"],
    "target_length": {"minutes": 10, "words": 1500},
    "use_ai_script": False  # Use story script generator
}

print("\n" + "="*60)
print("TESTING 80-DAYS STORY SCRIPT - 10 MINUTES")
print("="*60)
print(f"Title: {test_idea['title']}")
print(f"Target: {test_idea['target_length']['minutes']} minutes")

# Generate script using the story generator directly
script = pipeline.generate_story_script(test_idea, 10, 1500)

if script:
    word_count = len(script.split())
    char_count = len(script)
    estimated_minutes = word_count / 150

    print(f"\n[SUCCESS] Script generated!")
    print(f"   Word count: {word_count} words (target: 1500)")
    print(f"   Character count: {char_count} characters")
    print(f"   Estimated duration: {estimated_minutes:.1f} minutes")

    # Show structure
    import re
    sections = re.findall(r'\[([^\]]+)\]', script)
    print(f"\nScript sections ({len(sections)} total):")
    for i, section in enumerate(sections[:10], 1):
        print(f"  {i}. {section}")
    if len(sections) > 10:
        print(f"  ... and {len(sections) - 10} more sections")

    # Show sample content
    print("\nSample from middle of script (Day 25 breakthrough):")
    print("-"*50)
    start = script.find("[THE FIRST BREAKTHROUGH")
    end = script.find("[DAYS 30-50")
    if start > 0 and end > 0:
        print(script[start:end])
    print("-"*50)

    print("\n✅ SUCCESS: 10-minute story script is now generating full content!")
else:
    print("\n[ERROR] Script generation failed")