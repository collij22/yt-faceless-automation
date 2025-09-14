#!/usr/bin/env python3
"""
Create an n8n-compatible workflow based on different n8n versions.
The "Required" error might be version-specific.
"""

import json
import uuid

def create_compatible_workflows():
    """Create workflows compatible with different n8n versions."""

    # Version 1: n8n 0.x format (older)
    v1 = {
        "name": "TTS Webhook v0.x",
        "nodes": [
            {
                "parameters": {
                    "path": "tts-generation",
                    "responseMode": "onReceived",
                    "responseData": "firstEntryJson"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": "tts-generation"
            }
        ],
        "connections": {},
        "active": False,
        "settings": {},
        "id": 1,
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z"
    }

    # Version 2: n8n 1.x format (current)
    v2 = {
        "name": "TTS Webhook v1.x",
        "nodes": [
            {
                "parameters": {
                    "path": "tts-generation",
                    "responseMode": "onReceived",
                    "responseData": "firstEntryJson",
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
        "settings": {
            "executionOrder": "v1"
        },
        "versionId": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
        "meta": {
            "instanceId": str(uuid.uuid4()).replace('-', '')
        },
        "tags": []
    }

    # Version 3: Minimal working webhook with Set node
    v3 = {
        "name": "TTS Webhook Working",
        "nodes": [
            {
                "parameters": {
                    "path": "=tts-generation",  # Note: = prefix for expression
                    "responseMode": "lastNode",
                    "options": {}
                },
                "id": "webhook1",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": "abc123"
            },
            {
                "parameters": {
                    "keepOnlySet": False,
                    "values": {
                        "string": [
                            {
                                "name": "status",
                                "value": "success"
                            },
                            {
                                "name": "message",
                                "value": "TTS webhook is working"
                            },
                            {
                                "name": "received_text",
                                "value": "={{$json[\"text\"]}}"
                            },
                            {
                                "name": "received_slug",
                                "value": "={{$json[\"slug\"]}}"
                            }
                        ]
                    },
                    "options": {}
                },
                "id": "set1",
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
        },
        "active": False,
        "settings": {},
        "id": 999,
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z"
    }

    # Version 4: Super minimal - just webhook
    v4 = {
        "nodes": [
            {
                "parameters": {
                    "path": "tts-generation"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300]
            }
        ],
        "connections": {}
    }

    # Save all versions
    versions = [
        ("tts_v0x_format.json", v1),
        ("tts_v1x_format.json", v2),
        ("tts_working.json", v3),
        ("tts_super_minimal.json", v4)
    ]

    for filename, workflow in versions:
        filepath = f"workflows/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        print(f"Created: {filepath}")

    print("\n" + "="*60)
    print("COMPATIBILITY TEST")
    print("="*60)
    print("""
Try importing these workflows to identify your n8n version:

1. tts_super_minimal.json - Bare minimum structure
2. tts_v0x_format.json - n8n 0.x format (integer IDs)
3. tts_v1x_format.json - n8n 1.x format (UUID IDs)
4. tts_working.json - Full working webhook with response

One of these SHOULD work with your n8n version.

Also check your n8n version:
- Go to n8n Settings -> About
- Or check the bottom of the left sidebar
- Report the version number (e.g., 0.236.0 or 1.25.0)
""")

if __name__ == "__main__":
    create_compatible_workflows()