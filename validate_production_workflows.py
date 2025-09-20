#!/usr/bin/env python3
"""Validate n8n production workflow structure after fixes."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

def validate_workflow_structure(workflow: Dict[str, Any], workflow_name: str) -> Tuple[bool, List[str]]:
    """Validate workflow structure and connections."""
    errors = []

    # Check required fields
    if 'name' not in workflow:
        errors.append("Missing 'name' field")
    if 'nodes' not in workflow or not isinstance(workflow['nodes'], list):
        errors.append("Missing or invalid 'nodes' field")
    if 'connections' not in workflow or not isinstance(workflow['connections'], dict):
        errors.append("Missing or invalid 'connections' field")

    if errors:
        return False, errors

    nodes = workflow['nodes']
    connections = workflow['connections']

    # Find webhook node
    webhook_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.webhook']
    if not webhook_nodes:
        errors.append("No webhook trigger node found")
        return False, errors

    webhook_node = webhook_nodes[0]
    expected_paths = {
        'TTS Production Workflow': 'tts-generation',
        'YouTube Upload Production': 'youtube-upload',
        'YouTube Analytics Production': 'youtube-analytics',
        'Cross-Platform Distribution Production': 'cross-platform-distribute',
        'Affiliate Link Shortener Production': 'affiliate-shorten'
    }

    expected_path = expected_paths.get(workflow['name'])
    if expected_path:
        actual_path = webhook_node.get('parameters', {}).get('path', '')
        if actual_path != expected_path:
            errors.append(f"Expected webhook path '{expected_path}', got '{actual_path}'")

    # Check all nodes have required fields
    node_ids = set()
    for node in nodes:
        if 'id' not in node:
            errors.append(f"Node missing 'id' field")
            continue
        if node['id'] in node_ids:
            errors.append(f"Duplicate node id: {node['id']}")
        node_ids.add(node['id'])

        required_fields = ['id', 'name', 'type', 'position']
        for field in required_fields:
            if field not in node:
                errors.append(f"Node '{node.get('id', 'unknown')}' missing field: {field}")

    # Check connections reference valid nodes
    for source_node, outputs in connections.items():
        if source_node not in node_ids:
            errors.append(f"Connection references unknown source node: {source_node}")
            continue

        if not isinstance(outputs, dict) or 'main' not in outputs:
            errors.append(f"Invalid connection structure for node: {source_node}")
            continue

        for output_connections in outputs['main']:
            if not isinstance(output_connections, list):
                continue
            for connection in output_connections:
                if not isinstance(connection, dict) or 'node' not in connection:
                    errors.append(f"Invalid connection in node: {source_node}")
                    continue
                target_node = connection['node']
                if target_node not in node_ids:
                    errors.append(f"Connection references unknown target node: {target_node}")

    # Check that error nodes are properly connected
    error_nodes = [n for n in nodes if 'error' in n.get('name', '').lower()]
    for error_node in error_nodes:
        error_id = error_node['id']
        if error_id not in connections:
            errors.append(f"Error node '{error_id}' is not connected to any output")

    # Find final response nodes
    function_nodes = [n for n in nodes if n.get('type') == 'n8n-nodes-base.function']
    if not function_nodes:
        errors.append("No final response node (Function) found")

    return len(errors) == 0, errors

def validate_production_workflows():
    """Validate all production workflow files."""
    workflows_dir = Path('workflows')

    production_files = {
        'tts_webhook_PRODUCTION.json': 'TTS Production Workflow',
        'youtube_upload_PRODUCTION.json': 'YouTube Upload Production',
        'youtube_analytics_PRODUCTION.json': 'YouTube Analytics Production',
        'cross_platform_PRODUCTION.json': 'Cross-Platform Distribution Production',
        'affiliate_shortener_PRODUCTION.json': 'Affiliate Link Shortener Production'
    }

    print("=" * 60)
    print("PRODUCTION WORKFLOW VALIDATION")
    print("=" * 60)

    all_valid = True
    results = {}

    for filename, expected_name in production_files.items():
        filepath = workflows_dir / filename
        print(f"\nValidating {filename}...")

        if not filepath.exists():
            print(f"   [ERROR] File not found: {filepath}")
            results[filename] = {"valid": False, "errors": ["File not found"]}
            all_valid = False
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                workflow = json.load(f)

            # Basic JSON structure check
            if workflow.get('name') != expected_name:
                print(f"   [WARNING] Name mismatch: expected '{expected_name}', got '{workflow.get('name')}'")

            # Structural validation
            is_valid, errors = validate_workflow_structure(workflow, expected_name)
            results[filename] = {"valid": is_valid, "errors": errors}

            if is_valid:
                print(f"   [OK] Valid structure")
                print(f"   Nodes: {len(workflow.get('nodes', []))}")
                print(f"   Connections: {len(workflow.get('connections', {}))}")
            else:
                print(f"   [ERROR] Invalid structure")
                for error in errors:
                    print(f"       - {error}")
                all_valid = False

        except json.JSONDecodeError as e:
            print(f"   [ERROR] Invalid JSON: {e}")
            results[filename] = {"valid": False, "errors": [f"Invalid JSON: {e}"]}
            all_valid = False
        except Exception as e:
            print(f"   [ERROR] Error: {e}")
            results[filename] = {"valid": False, "errors": [f"Error: {e}"]}
            all_valid = False

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    valid_count = sum(1 for r in results.values() if r["valid"])
    total_count = len(results)

    print(f"\n[OK] Valid workflows: {valid_count}/{total_count}")
    print(f"[ERROR] Invalid workflows: {total_count - valid_count}/{total_count}")

    if all_valid:
        print("\nALL PRODUCTION WORKFLOWS ARE VALID!")
        print("   Ready for deployment to n8n")
    else:
        print("\nSome workflows need attention before deployment")

    return all_valid

if __name__ == "__main__":
    success = validate_production_workflows()
    exit(0 if success else 1)