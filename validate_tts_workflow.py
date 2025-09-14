#!/usr/bin/env python3
"""
Script to validate the TTS workflow and identify import issues
"""

import json
import sys
from pathlib import Path

def validate_n8n_workflow(workflow_path):
    """Validate n8n workflow structure and identify potential import issues"""
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        print(f"[OK] Successfully loaded workflow from: {workflow_path}")
        print(f"  Name: {workflow.get('name', 'Unknown')}")
        print(f"  Nodes: {len(workflow.get('nodes', []))}")
        print(f"  Active: {workflow.get('active', False)}")

        # Check required top-level fields
        required_fields = ['name', 'nodes', 'connections']
        missing_fields = []

        for field in required_fields:
            if field not in workflow:
                missing_fields.append(field)

        if missing_fields:
            print(f"[ERROR] Missing required top-level fields: {missing_fields}")
            return False

        # Validate nodes structure
        nodes = workflow.get('nodes', [])
        if not nodes:
            print("[ERROR] No nodes found in workflow")
            return False

        print(f"\n=== Node Validation ===")
        node_issues = []

        for i, node in enumerate(nodes):
            node_name = node.get('name', f'Node_{i}')
            node_type = node.get('type', 'unknown')

            print(f"Node {i+1}: {node_name} ({node_type})")

            # Check required node fields
            required_node_fields = ['name', 'type', 'typeVersion', 'position']
            missing_node_fields = []

            for field in required_node_fields:
                if field not in node:
                    missing_node_fields.append(field)

            if missing_node_fields:
                issue = f"  [ERROR] Missing required fields: {missing_node_fields}"
                print(issue)
                node_issues.append(f"{node_name}: {issue}")

            # Check node-specific requirements
            if node_type == 'n8n-nodes-base.webhook':
                webhook_issues = validate_webhook_node(node)
                if webhook_issues:
                    node_issues.extend([f"{node_name}: {issue}" for issue in webhook_issues])

            # Validate position format
            position = node.get('position')
            if position and (not isinstance(position, list) or len(position) != 2):
                issue = f"  [ERROR] Invalid position format: {position}"
                print(issue)
                node_issues.append(f"{node_name}: {issue}")

        # Validate connections
        print(f"\n=== Connection Validation ===")
        connections = workflow.get('connections', {})
        connection_issues = validate_connections(nodes, connections)

        # Summary
        print(f"\n=== Validation Summary ===")
        total_issues = len(node_issues) + len(connection_issues)

        if total_issues == 0:
            print("[OK] Workflow validation passed - no issues found")
            return True
        else:
            print(f"[ERROR] Found {total_issues} validation issues:")

            if node_issues:
                print("\nNode Issues:")
                for issue in node_issues:
                    print(f"  - {issue}")

            if connection_issues:
                print("\nConnection Issues:")
                for issue in connection_issues:
                    print(f"  - {issue}")

            return False

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Validation error: {e}")
        return False

def validate_webhook_node(node):
    """Validate webhook node specific requirements"""
    issues = []
    parameters = node.get('parameters', {})

    # Common webhook requirements
    if 'path' not in parameters:
        issues.append("Missing required 'path' parameter")

    if 'httpMethod' not in parameters:
        issues.append("Missing required 'httpMethod' parameter")

    # Check for webhook ID if needed
    webhook_id = node.get('webhookId')
    if not webhook_id:
        issues.append("Missing 'webhookId' field")

    return issues

def validate_connections(nodes, connections):
    """Validate workflow connections"""
    issues = []

    # Create node name lookup
    node_names = {node.get('name'): i for i, node in enumerate(nodes)}

    # Check each connection
    for source_node, connections_data in connections.items():
        if source_node not in node_names:
            issues.append(f"Connection source node '{source_node}' not found in nodes")
            continue

        main_connections = connections_data.get('main', [])
        for i, connection_group in enumerate(main_connections):
            for connection in connection_group:
                target_node = connection.get('node')
                if target_node and target_node not in node_names:
                    issues.append(f"Connection target node '{target_node}' not found in nodes")

    return issues

def create_minimal_tts_webhook():
    """Create a minimal working TTS webhook workflow"""
    minimal_workflow = {
        "name": "Minimal TTS Webhook",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "minimal-tts",
                    "responseMode": "lastNode"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [240, 300],
                "webhookId": "minimal-tts"
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
                            }
                        ]
                    }
                },
                "name": "Set Response",
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": [460, 300]
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
        "active": False,
        "settings": {},
        "versionId": None,
        "id": None,
        "tags": ["tts", "webhook", "minimal"]
    }

    return minimal_workflow

if __name__ == "__main__":
    # Validate the problematic workflow
    workflow_path = Path("workflows/tts_webhook_mcp_fixed.json")

    if not workflow_path.exists():
        print(f"[ERROR] Workflow file not found: {workflow_path}")
        sys.exit(1)

    print("=== Validating TTS Webhook MCP Fixed ===")
    is_valid = validate_n8n_workflow(workflow_path)

    # Create minimal workflow
    print(f"\n=== Creating Minimal Working Workflow ===")
    minimal_workflow = create_minimal_tts_webhook()

    minimal_path = Path("workflows/tts_webhook_minimal.json")
    with open(minimal_path, 'w', encoding='utf-8') as f:
        json.dump(minimal_workflow, f, indent=2)

    print(f"[OK] Created minimal workflow: {minimal_path}")

    # Validate minimal workflow
    print(f"\n=== Validating Minimal Workflow ===")
    minimal_valid = validate_n8n_workflow(minimal_path)

    if not is_valid and minimal_valid:
        print(f"\n=== RECOMMENDATION ===")
        print(f"The original workflow has validation issues.")
        print(f"Use the minimal workflow ({minimal_path}) as a starting point.")
        print(f"It should import without errors and can be extended gradually.")