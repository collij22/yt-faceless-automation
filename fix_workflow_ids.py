#!/usr/bin/env python3
"""
Fix n8n workflow by adding missing node IDs
"""

import json
import sys
from pathlib import Path
import re

def generate_node_id(node_name):
    """Generate a node ID from the node name"""
    # Convert to lowercase, replace spaces and special chars with underscores
    node_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_name.lower())
    # Remove multiple consecutive underscores
    node_id = re.sub(r'_+', '_', node_id)
    # Remove leading/trailing underscores
    node_id = node_id.strip('_')
    return node_id

def fix_workflow_ids(workflow_path):
    """Add missing node IDs to workflow"""
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        print(f"Processing workflow: {workflow_path}")
        print(f"  Name: {workflow.get('name', 'Unknown')}")
        print(f"  Nodes: {len(workflow.get('nodes', []))}")

        # Fix missing node IDs
        nodes = workflow.get('nodes', [])
        nodes_fixed = 0

        for i, node in enumerate(nodes):
            if 'id' not in node:
                # Generate ID from node name
                node_name = node.get('name', f'node_{i+1}')
                node_id = generate_node_id(node_name)

                # Ensure unique ID (check if already exists)
                existing_ids = {n.get('id') for n in nodes if 'id' in n}
                original_id = node_id
                counter = 1
                while node_id in existing_ids:
                    node_id = f"{original_id}_{counter}"
                    counter += 1

                node['id'] = node_id
                nodes_fixed += 1
                print(f"    Added ID '{node_id}' to node '{node_name}'")

        if nodes_fixed > 0:
            # Create output filename
            output_path = workflow_path.parent / f"{workflow_path.stem}_id_fixed.json"

            # Save fixed workflow
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2)

            print(f"  Fixed {nodes_fixed} nodes")
            print(f"  Saved to: {output_path}")
            return True
        else:
            print("  No missing IDs found")
            return False

    except Exception as e:
        print(f"Error processing {workflow_path}: {e}")
        return False

def create_minimal_tts_with_ids():
    """Create a minimal TTS workflow with proper IDs"""
    minimal_workflow = {
        "name": "Minimal TTS Webhook (Fixed)",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "tts-generation",
                    "responseMode": "lastNode",
                    "options": {
                        "cors": {
                            "enabled": True
                        },
                        "timeout": 30000
                    }
                },
                "id": "webhook_trigger",
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [240, 300],
                "webhookId": "tts-generation"
            },
            {
                "parameters": {
                    "values": {
                        "string": [
                            {
                                "name": "message",
                                "value": "TTS webhook received successfully"
                            },
                            {
                                "name": "timestamp",
                                "value": "={{new Date().toISOString()}}"
                            },
                            {
                                "name": "text_received",
                                "value": "={{$json.text || 'No text provided'}}"
                            },
                            {
                                "name": "slug_received",
                                "value": "={{$json.slug || 'No slug provided'}}"
                            }
                        ]
                    },
                    "options": {}
                },
                "id": "set_response",
                "name": "Set Response",
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": [460, 300]
            }
        ],
        "connections": {
            "Webhook Trigger": {
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
        "active": False,
        "settings": {},
        "versionId": None,
        "id": None,
        "tags": ["tts", "webhook", "minimal", "fixed"]
    }

    return minimal_workflow

if __name__ == "__main__":
    workflows_dir = Path("workflows")

    # Fix the specific problematic workflow
    tts_workflow = workflows_dir / "tts_webhook_mcp_fixed.json"

    if tts_workflow.exists():
        print("=== Fixing TTS Webhook MCP Fixed ===")
        success = fix_workflow_ids(tts_workflow)

        if success:
            print("\n[OK] Fixed workflow with missing IDs")
        else:
            print("\n[INFO] Workflow already has all required IDs")
    else:
        print(f"[ERROR] Workflow not found: {tts_workflow}")

    # Create minimal working version
    print("\n=== Creating Minimal TTS Workflow with IDs ===")
    minimal_workflow = create_minimal_tts_with_ids()

    minimal_path = workflows_dir / "tts_webhook_minimal_fixed.json"
    with open(minimal_path, 'w', encoding='utf-8') as f:
        json.dump(minimal_workflow, f, indent=2)

    print(f"[OK] Created minimal workflow: {minimal_path}")

    # Also fix any other workflows that need IDs
    print("\n=== Checking Other Fixed Workflows ===")
    other_fixed_workflows = list(workflows_dir.glob("*_mcp_fixed.json"))

    for workflow_file in other_fixed_workflows:
        if workflow_file.name != "tts_webhook_mcp_fixed.json":
            print(f"\nProcessing: {workflow_file.name}")
            fix_workflow_ids(workflow_file)

    print("\n=== Summary ===")
    print("All workflows with '_mcp_fixed' suffix have been processed.")
    print("Use the '_id_fixed' versions for import into n8n.")
    print("The minimal workflow should import without any issues.")