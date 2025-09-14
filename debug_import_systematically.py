#!/usr/bin/env python3
"""
Systematically debug what's causing the import error.
"""

import json

def create_debug_workflows():
    """Create increasingly complex workflows to find the breaking point."""

    # 1. Absolute bare minimum - no parameters at all
    bare = {
        "nodes": [
            {
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300]
            }
        ]
    }

    # 2. With name only
    with_name = {
        "name": "Debug Test",
        "nodes": [
            {
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300]
            }
        ]
    }

    # 3. With parameters object (empty)
    with_params_empty = {
        "name": "Debug Test Params",
        "nodes": [
            {
                "parameters": {},
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300]
            }
        ]
    }

    # 4. With path parameter
    with_path = {
        "name": "Debug Test Path",
        "nodes": [
            {
                "parameters": {
                    "path": "test-path"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300]
            }
        ]
    }

    # 5. With typeVersion
    with_version = {
        "name": "Debug Test Version",
        "nodes": [
            {
                "parameters": {
                    "path": "test-version"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ]
    }

    # 6. With connections object (empty)
    with_connections = {
        "name": "Debug Test Connections",
        "nodes": [
            {
                "parameters": {
                    "path": "test-connections"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ],
        "connections": {}
    }

    # 7. Try the EXACT content from test1_minimal that worked
    copy_test1 = {
        "name": "Copy of Test1",
        "nodes": [
            {
                "parameters": {
                    "path": "test1-copy"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ],
        "connections": {}
    }

    # Save all debug files
    debug_files = [
        ("debug_1_bare.json", bare),
        ("debug_2_with_name.json", with_name),
        ("debug_3_params_empty.json", with_params_empty),
        ("debug_4_with_path.json", with_path),
        ("debug_5_with_version.json", with_version),
        ("debug_6_with_connections.json", with_connections),
        ("debug_7_copy_test1.json", copy_test1)
    ]

    print("=" * 60)
    print("SYSTEMATIC DEBUG WORKFLOWS")
    print("=" * 60)
    print()

    for filename, workflow in debug_files:
        filepath = f"workflows/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        print(f"Created: {filepath}")

    print("\n" + "=" * 60)
    print("IMPORT THESE IN ORDER")
    print("=" * 60)
    print("""
Import these files ONE BY ONE in order:

1. debug_1_bare.json         - Absolute minimum
2. debug_2_with_name.json    - Adds workflow name
3. debug_3_params_empty.json - Adds empty parameters
4. debug_4_with_path.json    - Adds webhook path
5. debug_5_with_version.json - Adds typeVersion
6. debug_6_with_connections.json - Adds connections
7. debug_7_copy_test1.json  - Copy of working test1

The FIRST one that FAILS will tell us exactly what field is causing the problem.

Please report:
- Which number first FAILS
- The EXACT error message
- Your n8n version (check Help -> About or bottom of sidebar)
""")

if __name__ == "__main__":
    create_debug_workflows()