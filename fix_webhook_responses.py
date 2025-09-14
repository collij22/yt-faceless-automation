#!/usr/bin/env python3
"""
Fix n8n workflows to properly return responses.
The issue is that workflows are missing proper response nodes or connections.
"""

import json
from pathlib import Path

def fix_workflow_response(workflow_file):
    """Fix a workflow to ensure it returns a response."""
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    workflow_name = workflow.get('name', 'Unknown')
    print(f"\nFixing: {workflow_name}")

    # Find webhook trigger node
    webhook_node = None
    for node in workflow.get('nodes', []):
        if node.get('type') == 'n8n-nodes-base.webhook':
            webhook_node = node
            webhook_node['parameters']['responseMode'] = 'lastNode'  # Important!
            print(f"  - Found webhook trigger: {node.get('name')}")
            break

    if not webhook_node:
        print(f"  ERROR: No webhook trigger found")
        return False

    # Check if there's a response node
    has_response_node = False
    response_node = None
    for node in workflow.get('nodes', []):
        if 'respond' in node.get('type', '').lower() or 'respond' in node.get('name', '').lower():
            has_response_node = True
            response_node = node
            print(f"  - Found response node: {node.get('name')}")
            break

    # If no response node, add a simple one
    if not has_response_node:
        print("  - No response node found, adding one")

        # Find the last node position
        max_x = max([n.get('position', [0, 0])[0] for n in workflow.get('nodes', [])])

        # Add a simple response node
        response_node = {
            "parameters": {
                "mode": "runOnceForEachItem",
                "jsCode": '''// Return success response
const result = {
    success: true,
    message: "Webhook processed successfully",
    workflow: "''' + workflow_name + '''",
    timestamp: new Date().toISOString(),
    data: $json
};
return [{ json: result }];'''
            },
            "id": "response_node",
            "name": "Prepare Response",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [max_x + 200, 500]
        }

        workflow['nodes'].append(response_node)
        print("  - Added response preparation node")

    # Ensure workflow is active
    workflow['active'] = True

    # Save fixed workflow
    backup_file = workflow_file.with_suffix('.backup.json')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(json.load(open(workflow_file, 'r')), f, indent=2)
    print(f"  - Created backup: {backup_file.name}")

    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2)
    print(f"  - Fixed workflow saved")

    return True

def create_simple_test_workflow():
    """Create a simple test workflow to verify n8n is working."""
    test_workflow = {
        "name": "Simple Test Webhook",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "test-simple",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "id": "webhook1",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": "test-simple"
            },
            {
                "parameters": {
                    "mode": "runOnceForEachItem",
                    "jsCode": "return [{json: {success: true, received: $json, timestamp: new Date().toISOString()}}];"
                },
                "id": "code1",
                "name": "Return Data",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [450, 300]
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "Return Data", "type": "main", "index": 0}]]
            }
        },
        "active": true,
        "settings": {},
        "tags": []
    }

    with open('workflows/test_simple_webhook.json', 'w') as f:
        json.dump(test_workflow, f, indent=2)
    print("\nCreated simple test workflow: workflows/test_simple_webhook.json")
    print("Import this to test if n8n is working correctly")

def main():
    print("=" * 70)
    print("FIXING N8N WEBHOOK RESPONSE ISSUES")
    print("=" * 70)

    # Get all MCP workflow files
    workflows_dir = Path("workflows")
    workflow_files = list(workflows_dir.glob("*_mcp.json"))

    print(f"\nFound {len(workflow_files)} workflow files to fix")

    # Fix each workflow
    for wf in workflow_files:
        fix_workflow_response(wf)

    # Create simple test workflow
    create_simple_test_workflow()

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Re-import the fixed workflows into n8n")
    print("   - Go to http://localhost:5678")
    print("   - Delete the old workflows")
    print("   - Import the fixed ones from workflows/*_mcp.json")
    print()
    print("2. Test the simple workflow first:")
    print("   - Import workflows/test_simple_webhook.json")
    print("   - Activate it")
    print("   - Test with: curl -X POST http://localhost:5678/webhook/test-simple -d '{\"test\":true}'")
    print()
    print("3. Make sure all workflows are ACTIVE (green toggle)")
    print()
    print("4. Run the test suite again:")
    print("   python test_all_mcp_workflows.py")

if __name__ == "__main__":
    main()