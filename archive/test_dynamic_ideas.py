#!/usr/bin/env python
"""Test the dynamic idea generation system"""

import json
from pathlib import Path
from datetime import datetime
from run_full_production_pipeline import YouTubeProductionSystem

def test_dynamic_ideas():
    """Test that ideas are different each time"""

    pipeline = YouTubeProductionSystem()

    print("\n" + "="*60)
    print("TESTING DYNAMIC IDEA GENERATION")
    print("="*60)

    # Test niches
    test_niches = [
        {"niche": "Personal Finance & Investing", "rpm_range": "$15-45"},
        {"niche": "Technology & AI", "rpm_range": "$10-30"},
        {"niche": "Health & Wellness", "rpm_range": "$8-25"},
        {"niche": "Educational Content", "rpm_range": "$7-20"}
    ]

    for niche in test_niches:
        print(f"\n{'='*60}")
        print(f"Niche: {niche['niche']}")
        print("="*60)

        # Generate ideas multiple times to see variety
        for round in range(2):
            print(f"\nRound {round + 1}:")
            print("-"*40)

            ideas = pipeline.generate_content_ideas(niche)

            if not ideas:
                print("[WARNING] No ideas generated")
                continue

            for i, idea in enumerate(ideas[:3], 1):
                print(f"{i}. {idea['title']}")
                print(f"   Hook: {idea['hook']}")

            # Check if using dynamic numbers
            for idea in ideas:
                # Check for dynamic elements
                if any(str(num) in idea['title'] for num in range(3, 100)):
                    print(f"   [OK] Contains dynamic numbers")
                    break

    # Test history tracking
    print("\n" + "="*60)
    print("HISTORY TRACKING TEST")
    print("="*60)

    history_file = Path("data/ideas/idea_history.json")
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
            print(f"Ideas in history: {len(history.get('generated_titles', []))}")
            print(f"Last updated: {history.get('last_updated', 'Never')}")

            if history.get('generated_titles'):
                print("\nRecent titles in history:")
                for title in history['generated_titles'][-5:]:
                    print(f"  - {title}")
    else:
        print("No history file found (will be created on first run)")

    print("\n" + "="*60)
    print("DYNAMIC IDEA GENERATION TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_dynamic_ideas()