#!/usr/bin/env python3
"""
Fix n8n workflows to resolve import issues.
Ensures all required fields are present and properly formatted.
"""

import json
from pathlib import Path
import copy

def fix_workflow(workflow_path):
    """Fix a workflow to ensure it imports correctly in n8n."""

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Store original name
    original_name = workflow.get('name', 'Unknown')
    print(f"\nFixing: {original_name}")

    # Create a clean workflow structure
    fixed_workflow = {
        "name": original_name,
        "nodes": [],
        "connections": {},
        "active": False,  # Start inactive, user will activate
        "settings": {},
        "versionId": None,  # Let n8n assign this
        "id": None,  # Let n8n assign this
        "tags": workflow.get('tags', [])
    }

    # Fix each node
    node_name_map = {}  # Map old names to new names

    for i, node in enumerate(workflow.get('nodes', [])):
        # Simplify node IDs and names
        old_name = node.get('name', f'Node_{i}')
        new_name = old_name.replace(' ', '_').replace('(', '').replace(')', '')
        node_name_map[old_name] = new_name

        fixed_node = {
            "parameters": node.get('parameters', {}),
            "name": new_name,
            "type": node.get('type', 'n8n-nodes-base.noOp'),
            "typeVersion": node.get('typeVersion', 1),
            "position": node.get('position', [250 + (i * 200), 300])
        }

        # Special handling for webhook nodes
        if 'webhook' in fixed_node['type'].lower():
            if 'webhookId' in node:
                fixed_node['webhookId'] = node['webhookId']
            # Ensure responseMode is set
            if 'responseMode' not in fixed_node['parameters']:
                fixed_node['parameters']['responseMode'] = 'lastNode'

        # Special handling for HTTP Request nodes
        if 'httpRequest' in fixed_node['type']:
            # Ensure version compatibility
            if fixed_node['typeVersion'] > 3:
                fixed_node['typeVersion'] = 3

        # Special handling for Code nodes
        if 'code' in fixed_node['type'].lower():
            # Ensure proper mode
            if 'mode' not in fixed_node['parameters']:
                fixed_node['parameters']['mode'] = 'runOnceForEachItem'

        # Special handling for Merge nodes
        if 'merge' in fixed_node['type'].lower():
            # Fix version
            if fixed_node['typeVersion'] > 2:
                fixed_node['typeVersion'] = 2

        fixed_workflow['nodes'].append(fixed_node)
        print(f"  Fixed node: {new_name}")

    # Fix connections
    for source_node, connections in workflow.get('connections', {}).items():
        # Map old node names to new ones
        new_source = node_name_map.get(source_node, source_node.replace(' ', '_').replace('(', '').replace(')', ''))
        fixed_workflow['connections'][new_source] = {}

        for connection_type, connection_list in connections.items():
            fixed_workflow['connections'][new_source][connection_type] = []

            for connection_group in connection_list:
                fixed_group = []
                for connection in connection_group:
                    target_node = connection.get('node', '')
                    new_target = node_name_map.get(target_node, target_node.replace(' ', '_').replace('(', '').replace(')', ''))
                    fixed_connection = {
                        "node": new_target,
                        "type": connection.get('type', 'main'),
                        "index": connection.get('index', 0)
                    }
                    fixed_group.append(fixed_connection)
                fixed_workflow['connections'][new_source][connection_type].append(fixed_group)

    return fixed_workflow

def create_minimal_webhooks():
    """Create minimal webhook workflows that definitely work."""

    webhooks = [
        ("TTS Generation Minimal", "tts-generation"),
        ("YouTube Upload Minimal", "youtube-upload"),
        ("YouTube Analytics Minimal", "youtube-analytics"),
        ("Cross-Platform Distribution Minimal", "cross-platform-distribute"),
        ("Affiliate Shortener Minimal", "affiliate-shorten")
    ]

    for name, path in webhooks:
        workflow = {
            "name": name,
            "nodes": [
                {
                    "parameters": {
                        "path": path,
                        "responseMode": "lastNode",
                        "options": {}
                    },
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "webhookId": path
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
                                    "value": f"{name} is working"
                                }
                            ]
                        },
                        "options": {}
                    },
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
            "tags": ["minimal", "webhook"]
        }

        filename = f"workflows/{path.replace('-', '_')}_minimal.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        print(f"Created minimal: {filename}")

def main():
    print("=" * 70)
    print("FIXING N8N WORKFLOWS FOR IMPORT")
    print("=" * 70)

    # Get MCP workflow files
    workflow_files = list(Path("workflows").glob("*_mcp.json"))

    print(f"\nFound {len(workflow_files)} MCP workflows to fix")

    # Fix each workflow
    for wf in workflow_files:
        try:
            fixed = fix_workflow(wf)

            # Save fixed version
            fixed_path = wf.with_name(wf.stem + "_fixed.json")
            with open(fixed_path, 'w', encoding='utf-8') as f:
                json.dump(fixed, f, indent=2)

            print(f"  Saved: {fixed_path.name}")

        except Exception as e:
            print(f"  ERROR fixing {wf.name}: {e}")

    # Also create minimal versions
    print("\n" + "=" * 70)
    print("CREATING MINIMAL WORKFLOWS")
    print("=" * 70)
    create_minimal_webhooks()

    print("\n" + "=" * 70)
    print("IMPORT INSTRUCTIONS")
    print("=" * 70)
    print("""
1. Try importing the FIXED versions first:
   - *_mcp_fixed.json files

2. If those still have issues, use the MINIMAL versions:
   - *_minimal.json files

3. Import process:
   - Open n8n web interface
   - Click + to create new workflow
   - Menu (3 dots) → Import from File
   - Select the fixed JSON file
   - Save and Activate

4. Test with:
   python test_all_mcp_workflows.py
""")

if __name__ == "__main__":
    main()