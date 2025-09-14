#!/usr/bin/env python3
"""Test and validate n8n workflows created with MCP."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple

def validate_workflow_structure(workflow: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate basic workflow structure."""
    errors = []

    # Check required top-level fields
    if 'name' not in workflow:
        errors.append("Missing 'name' field")
    if 'nodes' not in workflow:
        errors.append("Missing 'nodes' field")
    elif not isinstance(workflow['nodes'], list):
        errors.append("'nodes' must be a list")
    elif len(workflow['nodes']) == 0:
        errors.append("Workflow has no nodes")

    return len(errors) == 0, errors

def validate_node_structure(node: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate individual node structure."""
    errors = []

    # Check required node fields
    required_fields = ['id', 'name', 'type', 'position']
    for field in required_fields:
        if field not in node:
            errors.append(f"Node missing required field: {field}")

    # Validate position
    if 'position' in node:
        if not isinstance(node['position'], list) or len(node['position']) != 2:
            errors.append(f"Node {node.get('name', 'unknown')}: position must be [x, y]")

    # Validate parameters
    if 'parameters' in node and not isinstance(node['parameters'], dict):
        errors.append(f"Node {node.get('name', 'unknown')}: parameters must be a dict")

    return len(errors) == 0, errors

def validate_webhook_workflow(workflow: Dict[str, Any], expected_path: str) -> Tuple[bool, List[str]]:
    """Validate webhook-specific workflow requirements."""
    errors = []

    # Find webhook trigger node
    webhook_nodes = [n for n in workflow.get('nodes', [])
                     if n.get('type') == 'n8n-nodes-base.webhook']

    if not webhook_nodes:
        errors.append("No webhook trigger node found")
    else:
        webhook_node = webhook_nodes[0]
        path = webhook_node.get('parameters', {}).get('path', '')
        if path != expected_path:
            errors.append(f"Expected webhook path '{expected_path}', got '{path}'")

    # Check for response node
    response_nodes = [n for n in workflow.get('nodes', [])
                     if 'respond' in n.get('type', '').lower() or
                     n.get('name', '').lower().startswith('respond')]

    if not response_nodes:
        errors.append("No response node found (webhook should respond)")

    return len(errors) == 0, errors

def test_workflow_file(filepath: Path) -> Dict[str, Any]:
    """Test a single workflow file."""
    result = {
        'file': filepath.name,
        'exists': filepath.exists(),
        'valid_json': False,
        'valid_structure': False,
        'node_count': 0,
        'errors': []
    }

    if not filepath.exists():
        result['errors'].append("File does not exist")
        return result

    # Try to load JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        result['valid_json'] = True
    except json.JSONDecodeError as e:
        result['errors'].append(f"Invalid JSON: {e}")
        return result
    except Exception as e:
        result['errors'].append(f"Error reading file: {e}")
        return result

    # Validate structure
    valid, errors = validate_workflow_structure(workflow)
    if not valid:
        result['errors'].extend(errors)
    else:
        result['valid_structure'] = True
        result['node_count'] = len(workflow.get('nodes', []))

        # Validate each node
        for node in workflow.get('nodes', []):
            node_valid, node_errors = validate_node_structure(node)
            if not node_valid:
                result['errors'].extend(node_errors)

        # Workflow-specific validation
        if 'tts_webhook' in filepath.name:
            webhook_valid, webhook_errors = validate_webhook_workflow(workflow, 'tts-generation')
            result['errors'].extend(webhook_errors)
        elif 'youtube_upload' in filepath.name:
            webhook_valid, webhook_errors = validate_webhook_workflow(workflow, 'youtube-upload')
            result['errors'].extend(webhook_errors)
        elif 'youtube_analytics' in filepath.name:
            webhook_valid, webhook_errors = validate_webhook_workflow(workflow, 'youtube-analytics')
            result['errors'].extend(webhook_errors)
        elif 'cross_platform' in filepath.name:
            webhook_valid, webhook_errors = validate_webhook_workflow(workflow, 'cross-platform-distribute')
            result['errors'].extend(webhook_errors)
        elif 'affiliate_shortener' in filepath.name:
            webhook_valid, webhook_errors = validate_webhook_workflow(workflow, 'affiliate-shorten')
            result['errors'].extend(webhook_errors)

    return result

def main():
    """Test all MCP workflow files."""
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    workflows_dir = Path('workflows')

    # Find all MCP workflow files
    mcp_workflows = list(workflows_dir.glob('*mcp*.json'))

    print("=" * 60)
    print("N8N MCP WORKFLOW VALIDATION REPORT")
    print("=" * 60)
    print()

    if not mcp_workflows:
        print("❌ No MCP workflow files found in workflows directory")
        return

    print(f"Found {len(mcp_workflows)} MCP workflow files to test")
    print()

    all_valid = True
    results = []

    for workflow_file in sorted(mcp_workflows):
        result = test_workflow_file(workflow_file)
        results.append(result)

        # Print result
        status = "✅" if len(result['errors']) == 0 else "❌"
        print(f"{status} {result['file']}")

        if result['valid_json']:
            print(f"   - Nodes: {result['node_count']}")

        if result['errors']:
            all_valid = False
            for error in result['errors']:
                print(f"   ⚠️  {error}")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    valid_count = sum(1 for r in results if len(r['errors']) == 0)
    total_nodes = sum(r['node_count'] for r in results)

    print(f"Total workflows: {len(results)}")
    print(f"Valid workflows: {valid_count}")
    print(f"Invalid workflows: {len(results) - valid_count}")
    print(f"Total nodes across all workflows: {total_nodes}")
    print()

    if all_valid:
        print("✅ ALL WORKFLOWS ARE VALID AND READY FOR DEPLOYMENT!")
    else:
        print("⚠️  Some workflows have issues that need to be addressed")

    # List expected features
    print()
    print("=" * 60)
    print("EXPECTED FEATURES")
    print("=" * 60)
    print()
    print("1. TTS Webhook (/tts-generation)")
    print("   - Text chunking at 5000 chars")
    print("   - Multi-provider support (ElevenLabs, Google)")
    print("   - Audio file saving")
    print()
    print("2. YouTube Upload (/youtube-upload)")
    print("   - Video upload with OAuth2")
    print("   - Metadata processing")
    print("   - Thumbnail and playlist support")
    print()
    print("3. YouTube Analytics (/youtube-analytics)")
    print("   - Fetch video statistics")
    print("   - Calculate engagement metrics")
    print("   - Batch video processing")
    print()
    print("4. Cross-Platform Distribution (/cross-platform-distribute)")
    print("   - Multi-platform posting")
    print("   - Platform-specific formatting")
    print("   - Result aggregation")
    print()
    print("5. Affiliate Shortener (/affiliate-shorten)")
    print("   - URL shortening with tracking")
    print("   - UTM parameter generation")
    print("   - QR code creation")

    return all_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)