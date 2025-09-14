#!/usr/bin/env python3
"""
Diagnose the exact import error by testing different workflow structures.
"""

import json
import uuid

def create_test_workflows():
    """Create various test workflows to identify the exact issue."""

    tests = []

    # Test 1: Absolute minimal webhook
    test1 = {
        "name": "Test1 Minimal",
        "nodes": [
            {
                "parameters": {
                    "path": "test1"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ],
        "connections": {}
    }
    tests.append(("test1_minimal.json", test1))

    # Test 2: With IDs
    test2 = {
        "name": "Test2 With IDs",
        "nodes": [
            {
                "parameters": {
                    "path": "test2"
                },
                "id": "webhook1",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ],
        "connections": {}
    }
    tests.append(("test2_with_ids.json", test2))

    # Test 3: With UUID IDs
    test3 = {
        "name": "Test3 UUID IDs",
        "nodes": [
            {
                "parameters": {
                    "path": "test3"
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            }
        ],
        "connections": {}
    }
    tests.append(("test3_uuid_ids.json", test3))

    # Test 4: With all metadata
    test4 = {
        "name": "Test4 Full Metadata",
        "nodes": [
            {
                "parameters": {
                    "path": "test4",
                    "responseMode": "onReceived",
                    "options": {}
                },
                "id": str(uuid.uuid4()),
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": str(uuid.uuid4())
            }
        ],
        "connections": {},
        "active": False,
        "settings": {},
        "versionId": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
        "tags": []
    }

    tests.append(("test4_full_metadata.json", test4))

    # Test 5: With Set node (2 nodes)
    test5 = {
        "name": "Test5 Two Nodes",
        "nodes": [
            {
                "parameters": {
                    "path": "test5",
                    "responseMode": "lastNode"
                },
                "id": "webhook_" + str(uuid.uuid4())[:8],
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "keepOnlySet": False,
                    "values": {
                        "string": [
                            {
                                "name": "message",
                                "value": "test"
                            }
                        ]
                    }
                },
                "id": "set_" + str(uuid.uuid4())[:8],
                "name": "Set",
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": [450, 300]
            }
        ],
        "connections": {
            "Webhook": {
                "main": [
                    [
                        {
                            "node": "Set",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
    }
    tests.append(("test5_two_nodes.json", test5))

    # Save all test files
    for filename, workflow in tests:
        filepath = f"workflows/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        print(f"Created: {filepath}")

    print("\n" + "="*60)
    print("TEST IMPORT INSTRUCTIONS")
    print("="*60)
    print("""
Try importing these test workflows IN ORDER:

1. test1_minimal.json - Absolute minimal
2. test2_with_ids.json - With simple IDs
3. test3_uuid_ids.json - With UUID IDs
4. test4_full_metadata.json - With all metadata fields
5. test5_two_nodes.json - With connection between nodes

The FIRST one that imports successfully shows what's required.
The FIRST one that fails shows what's causing the problem.

Report which ones work and which ones fail!
""")

if __name__ == "__main__":
    create_test_workflows()