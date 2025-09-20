#!/usr/bin/env python
"""Debug why scripts are generating short versions"""

from claude_script_generator import generate_production_script

# Test a script that's generating short content
title = "18 Skills You Need Before 2026"
hook = ""
target_minutes = 10
target_words = 1500

print(f"\nDebugging: {title}")
print(f"Target minutes: {target_minutes}")
print(f"Target words: {target_words}")

# Generate the script
script = generate_production_script(title, hook, target_minutes, target_words)

# Check length
if script:
    word_count = len(script.split())
    print(f"\nGenerated {word_count} words")

    # Check which version was generated
    if "[THE SHIFT - 0:20]" in script:
        print("Generated LONG version (10+ minutes)")
    elif "[THE SHIFT - 0:15]" in script:
        print("Generated SHORT version (5 minutes)")
    else:
        print("Unknown version generated")

    # Show first 500 chars to verify
    print(f"\nFirst 500 chars of script:")
    print(script[:500])