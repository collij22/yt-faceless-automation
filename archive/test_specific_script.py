#!/usr/bin/env python
"""Test specific script generation for numbered titles"""

from run_full_production_pipeline import YouTubeProductionSystem

# Create pipeline
pipeline = YouTubeProductionSystem()

# Test idea with specific number
test_idea = {
    "title": "7 Money Rules Nobody Teaches You",
    "hook": "Rule #3 alone will save you thousands",
    "keywords": ["money", "finance", "wealth"],
    "target_length": {"minutes": 5, "words": 750},
    "use_ai_script": True
}

print("\n" + "="*60)
print("TESTING SPECIFIC SCRIPT FOR: 7 Money Rules")
print("="*60)

# Generate script
script = pipeline.generate_ai_script(test_idea, 5, 750)

if script:
    print("\nGenerated Script:")
    print("-"*40)
    print(script)
    print("-"*40)

    # Count actual rules mentioned
    import re
    rule_mentions = len(re.findall(r'Rule #?\d+', script, re.IGNORECASE))
    print(f"\nActual rules mentioned in script: {rule_mentions}")
    print(f"Script length: {len(script)} characters")
    print(f"Word count: {len(script.split())} words")
else:
    print("Script generation failed")

# Test for a different type
test_idea2 = {
    "title": "How to Use School to Make Millions",
    "hook": "The strategy nobody talks about",
    "keywords": ["education", "money", "success"],
    "target_length": {"minutes": 5, "words": 750},
    "custom": True
}

print("\n" + "="*60)
print("TESTING CUSTOM IDEA SCRIPT")
print("="*60)

script2 = pipeline.generate_high_retention_script(test_idea2)
if script2:
    print("\nScript preview (first 800 chars):")
    print("-"*40)
    print(script2[:800])
    print("...")
    print("-"*40)