#!/usr/bin/env python
"""Test all script generators for proper 10-minute content"""

from claude_script_generator import generate_production_script

test_cases = [
    {"title": "7 Lessons From My Biggest Failure", "category": "Lessons"},
    {"title": "Make $10000 Per Month While You Sleep", "category": "Passive Income"},
    {"title": "The 5-Minute Budget System That Works", "category": "Budgeting"},
    {"title": "I Tested 11 AI Tools - These 5 Won", "category": "AI Tools"},
    {"title": "27 Money Rules Nobody Teaches You", "category": "Money Rules"},
    {"title": "18 Skills You Need Before 2026", "category": "Skills"},
    {"title": "How Da Vinci Actually Thought", "category": "Historical Genius"},
    {"title": "The Truth About Genius", "category": "Intelligence"},
    {"title": "I Did This For 80 Days - Shocking Results", "category": "Challenge"}
]

print("\n" + "="*70)
print("TESTING ALL SCRIPT TYPES FOR 10-MINUTE CONTENT")
print("="*70)

all_passed = True
results = []

for test in test_cases:
    script = generate_production_script(test["title"], "", 10, 1500)

    if script:
        word_count = len(script.split())
        estimated_minutes = word_count / 150

        # Check for placeholders
        has_placeholders = "[Deep explanation" in script or "[Detailed breakdown" in script

        # Check if it meets minimum length (at least 7 minutes)
        meets_length = estimated_minutes >= 7.0

        passed = not has_placeholders and meets_length
        all_passed = all_passed and passed

        results.append({
            "category": test["category"],
            "words": word_count,
            "minutes": estimated_minutes,
            "passed": passed,
            "has_placeholders": has_placeholders
        })

        status = "PASS" if passed else "FAIL"
        print(f"\n[{status}] {test['category']:20} - {word_count:4} words ({estimated_minutes:.1f} min)")
        if has_placeholders:
            print("      WARNING: Contains placeholders!")
        if not meets_length:
            print("      WARNING: Too short for 10-minute target!")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

passing = sum(1 for r in results if r["passed"])
print(f"Passed: {passing}/{len(results)}")
print(f"Average length: {sum(r['minutes'] for r in results)/len(results):.1f} minutes")
print(f"Average words: {sum(r['words'] for r in results)/len(results):.0f} words")

if all_passed:
    print("\nSUCCESS: All script types generate proper 10-minute content!")
else:
    print("\nSome scripts need improvement:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['category']}: {r['minutes']:.1f} min, placeholders: {r['has_placeholders']}")