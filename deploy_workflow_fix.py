#!/usr/bin/env python3
"""
Deploy the fixed YouTube Analytics workflow to n8n.
This script will help ensure the workflow in n8n matches our fixed version.
"""

import json
import requests
import time
from pathlib import Path

def check_current_workflow():
    """Check if the current workflow is working"""
    url = 'http://localhost:5678/webhook/youtube-analytics'
    
    test_payloads = [
        {'channel_id': 'test1'},
        {'channel_id': 'test2', 'include_demographics': False, 'include_traffic_sources': False}
    ]
    
    for i, payload in enumerate(test_payloads, 1):
        print(f"\n--- Test {i} ---")
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Content-Length: {len(response.content)}")
            
            if response.content:
                try:
                    data = response.json()
                    print("[OK] Got JSON response!")
                    print(f"Status: {data.get('status', 'unknown')}")
                    print(f"Message: {data.get('message', 'none')}")
                    return True  # Working!
                except json.JSONDecodeError:
                    print("[ERROR] Invalid JSON response")
                    print(f"Raw: {response.text[:200]}")
            else:
                print("[ERROR] Empty response")
                
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    return False

def create_minimal_test_workflow():
    """Create a minimal test workflow to verify n8n is working"""
    
    minimal_workflow = {
        "name": "Test Analytics (Minimal)",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "test-analytics",
                    "responseMode": "responseNode",
                    "responseNode": "Webhook Response",
                    "options": {}
                },
                "id": "webhook_test",
                "name": "Webhook Test",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "functionCode": "// Simple test function\\nreturn [{ json: { status: 'success', message: 'Test webhook working', data: $json } }];"
                },
                "id": "test_function",
                "name": "Test Function",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "respondWith": "allEntries",
                    "options": {}
                },
                "id": "webhook_response_test",
                "name": "Webhook Response",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1,
                "position": [650, 300]
            }
        ],
        "connections": {
            "webhook_test": {
                "main": [
                    [
                        {
                            "node": "test_function",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "test_function": {
                "main": [
                    [
                        {
                            "node": "webhook_response_test",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
    }
    
    # Save the minimal workflow
    with open('workflows/test_analytics_minimal.json', 'w') as f:
        json.dump(minimal_workflow, f, indent=2)
    
    print("Created minimal test workflow: workflows/test_analytics_minimal.json")
    return minimal_workflow

def test_minimal_workflow():
    """Test the minimal workflow"""
    
    url = 'http://localhost:5678/webhook/test-analytics'
    payload = {'test': 'data', 'channel_id': 'minimal_test'}
    
    print(f"\nTesting minimal workflow at: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text}")
        
        if response.content:
            data = response.json()
            return data.get('status') == 'success'
        else:
            print("Minimal workflow also returns empty response!")
            return False
            
    except Exception as e:
        print(f"Minimal workflow test error: {e}")
        return False

def analyze_workflow_differences():
    """Compare our workflow file with what might be expected"""
    
    workflow_file = Path('workflows/youtube_analytics_PRODUCTION.json')
    
    if not workflow_file.exists():
        print("ERROR: Workflow file not found!")
        return False
        
    with open(workflow_file, 'r') as f:
        workflow_data = json.load(f)
    
    print("=== WORKFLOW FILE ANALYSIS ===")
    print(f"File: {workflow_file}")
    print(f"Workflow name: {workflow_data.get('name')}")
    print(f"Nodes: {len(workflow_data.get('nodes', []))}")
    print(f"Connections: {len(workflow_data.get('connections', {}))}")
    
    # Check specific configurations that might cause issues
    nodes = {node['id']: node for node in workflow_data['nodes']}
    
    # Check webhook configuration
    webhook_node = nodes.get('webhook')
    if webhook_node:
        params = webhook_node['parameters']
        print(f"\\nWebhook configuration:")
        print(f"  Path: {params.get('path')}")
        print(f"  Response mode: {params.get('responseMode')}")
        print(f"  Response node: {params.get('responseNode')}")
        
    # Check webhook response configuration
    response_node = nodes.get('webhook_response')
    if response_node:
        params = response_node['parameters']
        print(f"\\nWebhook Response configuration:")
        print(f"  Respond with: {params.get('respondWith')}")
        print(f"  Node type: {response_node['type']}")
        
    # Check function node
    function_node = nodes.get('generate_insights')
    if function_node:
        func_code = function_node['parameters']['functionCode']
        print(f"\\nFunction node:")
        print(f"  Code length: {len(func_code)}")
        print(f"  Has return statement: {'return' in func_code}")
        print(f"  Has JSON structure: {'json:' in func_code}")
        
        # Check for specific patterns that might fail
        if '$input.first()' in func_code:
            print("  [OK] Uses $input.first()")
        elif '$input' in func_code:
            print("  [WARNING] Uses $input but not $input.first()")
        else:
            print("  [ERROR] Doesn't use $input")
    
    return True

def main():
    print("=== N8N WORKFLOW DEPLOYMENT FIXER ===")
    print()
    
    # First, analyze our current workflow file
    if not analyze_workflow_differences():
        return
    
    # Test current workflow
    print("\\n=== TESTING CURRENT WORKFLOW ===")
    if check_current_workflow():
        print("[OK] Current workflow is working! No need to fix.")
        return
    
    print("[ERROR] Current workflow is not working correctly.")
    
    # Create and test minimal workflow
    print("\\n=== CREATING MINIMAL TEST ===")
    create_minimal_test_workflow()
    
    print("\\nTo test the minimal workflow:")
    print("1. Import workflows/test_analytics_minimal.json into n8n")
    print("2. Activate the workflow")
    print("3. Run this script again with --test-minimal flag")
    print()
    
    print("To fix the main workflow:")
    print("1. In n8n, delete the existing 'YouTube Analytics Production' workflow")
    print("2. Import workflows/youtube_analytics_PRODUCTION.json")
    print("3. Activate the workflow")
    print("4. Test with: POST http://localhost:5678/webhook/youtube-analytics")
    
    # Show manual import instructions
    print("\\n=== MANUAL IMPORT INSTRUCTIONS ===")
    print("Since n8n API requires authentication, please manually:")
    print("1. Open n8n in browser: http://localhost:5678")
    print("2. Go to Workflows")
    print("3. Click 'Import workflow'") 
    print("4. Upload: workflows/youtube_analytics_PRODUCTION.json")
    print("5. Make sure to activate the workflow!")
    print("6. Test the webhook endpoint")

if __name__ == "__main__":
    import sys
    
    if '--test-minimal' in sys.argv:
        print("Testing minimal workflow...")
        if test_minimal_workflow():
            print("[OK] Minimal workflow works! The issue might be with the main workflow.")
        else:
            print("[ERROR] Even minimal workflow fails. n8n might have a configuration issue.")
    else:
        main()