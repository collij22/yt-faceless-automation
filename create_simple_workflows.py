#!/usr/bin/env python3
"""Create simple, working versions of the workflows."""

import json
from pathlib import Path

def create_simple_workflow(name, path, webhook_id):
    """Create a simple working workflow."""
    return {
        "name": name,
        "nodes": [
            {
                "parameters": {
                    "path": path,
                    "responseMode": "lastNode",
                    "options": {}
                },
                "id": "webhook",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": webhook_id
            },
            {
                "parameters": {
                    "values": {
                        "string": [
                            {
                                "name": "status",
                                "value": "success"
                            },
                            {
                                "name": "workflow",
                                "value": name
                            },
                            {
                                "name": "message",
                                "value": f"{name} webhook is working!"
                            },
                            {
                                "name": "received_data",
                                "value": "={{JSON.stringify($json)}}"
                            },
                            {
                                "name": "timestamp",
                                "value": "={{new Date().toISOString()}}"
                            }
                        ]
                    },
                    "options": {}
                },
                "id": "set",
                "name": "Set Response",
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
                            "node": "Set Response",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        },
        "active": True,
        "settings": {},
        "versionId": "1.0",
        "id": webhook_id.replace("-", "_"),
        "meta": {
            "instanceId": f"{webhook_id}-instance"
        },
        "tags": ["simple", "webhook", "working"]
    }

# Create simple versions of all workflows
workflows = [
    ("TTS Generation Simple", "tts-generation", "tts-generation"),
    ("YouTube Upload Simple", "youtube-upload", "youtube-upload"),
    ("YouTube Analytics Simple", "youtube-analytics", "youtube-analytics"),
    ("Cross-Platform Simple", "cross-platform-distribute", "cross-platform"),
    ("Affiliate Shortener Simple", "affiliate-shorten", "affiliate-shorten")
]

print("Creating simple working workflows...")
print("=" * 50)

for name, path, webhook_id in workflows:
    workflow = create_simple_workflow(name, path, webhook_id)
    filename = f"workflows/{webhook_id.replace('-', '_')}_simple.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2)

    print(f"Created: {filename}")

print("\n" + "=" * 50)
print("IMPORT INSTRUCTIONS")
print("=" * 50)
print("""
1. DELETE the problematic workflows from n8n

2. IMPORT these simple workflows:
   - tts_generation_simple.json
   - youtube_upload_simple.json
   - youtube_analytics_simple.json
   - cross_platform_simple.json
   - affiliate_shorten_simple.json

3. ACTIVATE each workflow (green toggle)

4. TEST with:
   python test_all_mcp_workflows.py

These simple workflows will:
- Accept any JSON input
- Return a success response
- Include the received data in the response

Once these work, you can gradually add complexity.
""")