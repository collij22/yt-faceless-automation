#!/usr/bin/env python3
"""
Deploy n8n workflows to local n8n instance.
This script directly imports workflow JSON files into n8n.
"""

import requests
import json
import os
from pathlib import Path
import sys

# Configuration for local n8n
N8N_URL = "http://localhost:5678"
API_URL = f"{N8N_URL}/api/v1"

def check_n8n_connection():
    """Check if n8n is accessible."""
    try:
        response = requests.get(N8N_URL, timeout=5)
        return True
    except:
        return False

def get_workflow_files():
    """Get all MCP workflow JSON files."""
    workflows_dir = Path("workflows")
    return list(workflows_dir.glob("*_mcp.json"))

def import_workflow_via_api(workflow_file):
    """Import a workflow using n8n API."""
    try:
        # Read workflow JSON
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)

        # Ensure workflow is active
        workflow_data['active'] = True

        # Try to create workflow via API
        # Note: Local n8n may not require authentication
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Try different endpoints
        endpoints = [
            f"{API_URL}/workflows",
            f"{N8N_URL}/rest/workflows",
            f"{N8N_URL}/workflows"
        ]

        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    json=workflow_data,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    print(f"  SUCCESS: Imported via {endpoint}")
                    return True
            except:
                continue

        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def create_import_instructions(workflow_files):
    """Create manual import instructions."""
    print("\nMANUAL IMPORT INSTRUCTIONS:")
    print("=" * 60)
    print("Since API import isn't working, import manually:")
    print()
    print("1. Open n8n in your browser: http://localhost:5678")
    print("2. Click on 'Workflows' in the left sidebar")
    print("3. Click the menu (3 dots) -> 'Import from File'")
    print("4. Import these files one by one:")
    print()
    for wf in workflow_files:
        print(f"   - {wf.absolute()}")
    print()
    print("5. After importing, make sure each workflow is ACTIVE")
    print("   (toggle the switch to ON/green for each workflow)")
    print()
    print("6. Save each workflow after activating it")
    print("=" * 60)

def test_webhook(path):
    """Test if a webhook endpoint is responding."""
    url = f"{N8N_URL}/webhook{path}"
    try:
        response = requests.post(url, json={"test": True}, timeout=5)
        return response.status_code != 404
    except:
        return False

def main():
    print("N8N LOCAL DEPLOYMENT TOOL")
    print("=" * 60)

    # Check n8n connection
    print("\nChecking n8n connection...")
    if not check_n8n_connection():
        print("ERROR: Cannot connect to n8n at http://localhost:5678")
        print("Make sure n8n is running!")
        return False

    print("SUCCESS: n8n is running at http://localhost:5678")

    # Get workflow files
    workflow_files = get_workflow_files()
    print(f"\nFound {len(workflow_files)} workflow files")

    # Check current webhook status
    print("\nChecking webhook endpoints...")
    webhooks = [
        ("/tts-generation", "TTS Generation"),
        ("/youtube-upload", "YouTube Upload"),
        ("/youtube-analytics", "YouTube Analytics"),
        ("/cross-platform-distribute", "Cross-Platform"),
        ("/affiliate-shorten", "Affiliate Shortener")
    ]

    working_count = 0
    for path, name in webhooks:
        if test_webhook(path):
            print(f"  OK: {name} webhook is responding")
            working_count += 1
        else:
            print(f"  MISSING: {name} webhook not found")

    if working_count == len(webhooks):
        print("\nAll webhooks are already working!")
        return True

    # Try to import via API
    print("\nAttempting to import workflows via API...")
    imported = 0
    for wf in workflow_files:
        print(f"\nImporting: {wf.name}")
        if import_workflow_via_api(wf):
            imported += 1

    if imported == 0:
        print("\nAPI import didn't work (this is common for local n8n)")
        create_import_instructions(workflow_files)
    else:
        print(f"\nSuccessfully imported {imported} workflows")

    # Re-test webhooks
    print("\nRe-testing webhook endpoints...")
    working_now = 0
    for path, name in webhooks:
        if test_webhook(path):
            print(f"  WORKING: {name}")
            working_now += 1

    if working_now > working_count:
        print(f"\nProgress! {working_now - working_count} new webhooks are working")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)