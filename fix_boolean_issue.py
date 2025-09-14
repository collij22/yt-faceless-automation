#!/usr/bin/env python3
"""
Fix the boolean issue in the WORKING files.
Python outputs False (capital F) but n8n expects false (lowercase).
"""

import json
import os

def fix_workflow_files():
    """Fix all WORKING workflow files to have proper JSON booleans."""

    working_files = [
        "workflows/tts_webhook_WORKING.json",
        "workflows/youtube_upload_WORKING.json",
        "workflows/youtube_analytics_WORKING.json",
        "workflows/cross_platform_WORKING.json",
        "workflows/affiliate_shortener_WORKING.json"
    ]

    for filepath in working_files:
        if os.path.exists(filepath):
            # Read the file as text
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace Python booleans with JSON booleans
            content = content.replace(': False', ': false')
            content = content.replace(': True', ': true')

            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Fixed: {filepath}")

    # Also create a simple test to verify
    test_workflow = {
        "name": "Boolean Test",
        "nodes": [
            {
                "parameters": {
                    "path": "boolean-test"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "keepOnlySet": False,  # This will be false in JSON
                    "values": {
                        "string": [
                            {"name": "test", "value": "working"}
                        ]
                    }
                },
                "name": "Set",
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": [450, 300]
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "Set", "type": "main", "index": 0}]]
            }
        }
    }

    # Save with proper JSON serialization
    with open('workflows/boolean_test.json', 'w') as f:
        json.dump(test_workflow, f, indent=2)

    print("\nCreated: workflows/boolean_test.json")
    print("\nAll files fixed! The boolean values are now lowercase 'false' as required by JSON.")

if __name__ == "__main__":
    fix_workflow_files()