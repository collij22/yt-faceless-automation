#!/usr/bin/env python3
"""
Debug script to analyze n8n workflow execution and identify issues
with the YouTube Analytics webhook returning empty responses.
"""

import requests
import json
import time
from datetime import datetime

def test_webhook_detailed():
    """Test the webhook with detailed debugging"""
    url = 'http://localhost:5678/webhook/youtube-analytics'
    
    # Test different payloads
    test_cases = [
        {'channel_id': 'test'},
        {'channel_id': 'test', 'date_range': 'last_30_days'},
        {'channel_id': 'test', 'include_demographics': True, 'include_traffic_sources': True},
        {},  # Empty payload
        {'channel_id': 'test', 'include_demographics': False, 'include_traffic_sources': False},
    ]
    
    for i, payload in enumerate(test_cases, 1):
        print(f"\n=== TEST CASE {i} ===")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Status: {response.status_code}")
            print(f"Content-Length: {len(response.content)}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.content:
                try:
                    data = response.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Raw content: {response.text[:500]}")
            else:
                print("Empty response!")
                
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)  # Brief pause between tests

def check_n8n_health():
    """Check n8n server health and basic info"""
    try:
        # Health check
        health_response = requests.get('http://localhost:5678/healthz', timeout=5)
        print(f"n8n Health: {health_response.status_code} - {health_response.text}")
        
        # Try to get some basic info (might need auth)
        try:
            info_response = requests.get('http://localhost:5678/api/v1/workflows', timeout=5)
            print(f"Workflows API: {info_response.status_code}")
            if info_response.status_code == 401:
                print("API requires authentication")
        except:
            pass
            
    except Exception as e:
        print(f"Health check error: {e}")

def test_workflow_import():
    """Test if we can programmatically check the workflow file"""
    workflow_path = "workflows/youtube_analytics_PRODUCTION.json"
    
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        print(f"\n=== WORKFLOW ANALYSIS ===")
        print(f"Workflow name: {workflow_data.get('name', 'Unknown')}")
        print(f"Number of nodes: {len(workflow_data.get('nodes', []))}")
        
        # Check key nodes
        nodes = {node['id']: node for node in workflow_data.get('nodes', [])}
        
        critical_nodes = ['webhook', 'generate_insights', 'webhook_response']
        for node_id in critical_nodes:
            if node_id in nodes:
                node = nodes[node_id]
                print(f"[OK] {node_id}: {node['name']} ({node['type']})")
            else:
                print(f"[ERROR] Missing critical node: {node_id}")
        
        # Check connections
        connections = workflow_data.get('connections', {})
        print(f"\nConnections: {len(connections)} nodes have outgoing connections")
        
        # Trace the path from webhook to response
        print("\n=== EXECUTION PATH ===")
        current = 'webhook'
        path = []
        
        while current:
            path.append(current)
            if current in connections:
                main_connections = connections[current].get('main', [[]])
                if main_connections and main_connections[0]:
                    next_node = main_connections[0][0]['node']
                    print(f"{current} -> {next_node}")
                    current = next_node
                    if len(path) > 20:  # Prevent infinite loops
                        break
                else:
                    print(f"{current} -> (no connections)")
                    break
            else:
                print(f"{current} -> (end node)")
                break
        
        print(f"\nFinal path: {' -> '.join(path)}")
        
        if 'webhook_response' not in path:
            print("[WARNING] webhook_response not in execution path!")
        else:
            print("[OK] webhook_response is in execution path")
        
    except Exception as e:
        print(f"Workflow analysis error: {e}")

if __name__ == "__main__":
    print("=== N8N WORKFLOW DEBUGGER ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    check_n8n_health()
    test_workflow_import()
    test_webhook_detailed()