#!/usr/bin/env python3
"""
Validate the YouTube Analytics workflow JSON structure.
"""

import json
import sys
from typing import Dict, Any, List

def validate_workflow_structure(workflow_path: str) -> Dict[str, Any]:
    """Validate the workflow JSON structure."""
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        return {"valid": False, "error": f"Failed to load workflow: {str(e)}"}
    
    # Check basic structure
    if not isinstance(workflow, dict):
        return {"valid": False, "error": "Workflow is not a dict"}
    
    if "nodes" not in workflow:
        return {"valid": False, "error": "No 'nodes' key in workflow"}
    
    if "connections" not in workflow:
        return {"valid": False, "error": "No 'connections' key in workflow"}
    
    nodes = workflow["nodes"]
    connections = workflow["connections"]
    
    # Build node lookup
    node_lookup = {node["id"]: node for node in nodes}
    node_names = {node["name"]: node["id"] for node in nodes}
    
    print(f"Found {len(nodes)} nodes:")
    for node in nodes:
        print(f"  - {node['name']} ({node['id']})")
    
    # Validate connections
    print(f"\nValidating connections...")
    connection_issues = []
    
    for source_node, targets in connections.items():
        if source_node not in node_names:
            connection_issues.append(f"Source node '{source_node}' not found in nodes")
            continue
            
        source_id = node_names[source_node]
        
        if "main" in targets:
            for branch_idx, branch in enumerate(targets["main"]):
                for connection in branch:
                    target_node_id = connection["node"]
                    if target_node_id not in node_lookup:
                        connection_issues.append(
                            f"Target node '{target_node_id}' in connection from '{source_node}' not found"
                        )
    
    # Trace the workflow path
    print(f"\nTracing workflow path...")
    path = []
    
    # Start from webhook
    current = "Webhook"
    visited = set()
    max_steps = 20  # Prevent infinite loops
    step = 0
    
    while current and current not in visited and step < max_steps:
        path.append(current)
        visited.add(current)
        
        # Find next node
        if current in connections and "main" in connections[current]:
            # Take the first branch for now
            first_branch = connections[current]["main"][0]
            if first_branch:
                current = first_branch[0]["node"]
                # Convert node ID back to name
                for node in nodes:
                    if node["id"] == current:
                        current = node["name"]
                        break
            else:
                break
        else:
            break
        step += 1
    
    print(f"Workflow path: {' -> '.join(path)}")
    
    # Check for merge nodes
    merge_nodes = [node for node in nodes if node["type"] == "n8n-nodes-base.merge"]
    print(f"\nFound {len(merge_nodes)} merge nodes:")
    for node in merge_nodes:
        print(f"  - {node['name']}: {node['parameters'].get('combinationMode', 'default')}")
    
    # Check webhook response configuration
    webhook_response = next((node for node in nodes if node["type"] == "n8n-nodes-base.respondToWebhook"), None)
    if webhook_response:
        print(f"\nWebhook Response configuration:")
        print(f"  - respondWith: {webhook_response['parameters'].get('respondWith', 'default')}")
    else:
        connection_issues.append("No webhook response node found")
    
    result = {
        "valid": len(connection_issues) == 0,
        "node_count": len(nodes),
        "connection_count": len(connections),
        "workflow_path": path,
        "merge_nodes": len(merge_nodes),
        "issues": connection_issues
    }
    
    return result

def main():
    """Main validation function."""
    
    workflow_path = "workflows/youtube_analytics_PRODUCTION.json"
    
    print("=" * 60)
    print("YouTube Analytics Workflow Validation")
    print("=" * 60)
    
    result = validate_workflow_structure(workflow_path)
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    if result["valid"]:
        print("SUCCESS: Workflow structure is VALID")
        print(f"   - {result['node_count']} nodes")
        print(f"   - {result['connection_count']} connection groups")
        print(f"   - {result['merge_nodes']} merge nodes")
        print(f"   - Workflow path has {len(result['workflow_path'])} steps")
    else:
        print("ERROR: Workflow structure has ISSUES:")
        for issue in result["issues"]:
            print(f"   - {issue}")
    
    return 0 if result["valid"] else 1

if __name__ == "__main__":
    sys.exit(main())