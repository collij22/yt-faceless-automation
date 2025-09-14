#!/usr/bin/env python3
"""
Automatically import workflows to n8n using the UI API.
This simulates what the n8n UI does when importing workflows.
"""

import requests
import json
from pathlib import Path
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

N8N_URL = "http://localhost:5678"

def check_n8n_running():
    """Check if n8n is accessible."""
    try:
        response = requests.get(N8N_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def import_workflow_via_ui_api(workflow_json):
    """Import workflow using n8n's internal API (same as UI uses)."""

    # n8n UI uses these endpoints
    endpoints_to_try = [
        f"{N8N_URL}/rest/workflows",
        f"{N8N_URL}/api/v1/workflows",
        f"{N8N_URL}/workflows"
    ]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }

    for endpoint in endpoints_to_try:
        try:
            print(f"  Trying endpoint: {endpoint}")
            response = requests.post(
                endpoint,
                json=workflow_json,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"    ✓ Success! Status: {response.status_code}")
                return True
            else:
                print(f"    × Failed. Status: {response.status_code}")
                if response.text:
                    print(f"    Response: {response.text[:200]}")
        except Exception as e:
            print(f"    × Error: {str(e)[:100]}")

    return False

def main():
    print("=" * 70)
    print("N8N WORKFLOW AUTO-IMPORTER")
    print("=" * 70)

    # Check n8n is running
    if not check_n8n_running():
        print("\n❌ ERROR: n8n is not running at http://localhost:5678")
        print("Please start n8n first!")
        return

    print("\n✓ n8n is running")

    # Get workflow files
    workflow_files = list(Path("workflows").glob("*_mcp.json"))
    print(f"\nFound {len(workflow_files)} workflow files to import:")
    for wf in workflow_files:
        print(f"  - {wf.name}")

    # Try to import each workflow
    print("\n" + "=" * 70)
    print("ATTEMPTING AUTO-IMPORT")
    print("=" * 70)

    imported = 0
    for wf in workflow_files:
        print(f"\nImporting: {wf.name}")

        try:
            with open(wf, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)

            # Ensure workflow is active
            workflow_json['active'] = True

            if import_workflow_via_ui_api(workflow_json):
                imported += 1
                print(f"  ✓ Successfully imported: {workflow_json.get('name', 'Unknown')}")
            else:
                print(f"  × Failed to import via API")

        except Exception as e:
            print(f"  × Error reading file: {e}")

    # Results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if imported > 0:
        print(f"\n✓ Successfully imported {imported}/{len(workflow_files)} workflows")
        print("\nNow testing webhooks...")
        time.sleep(2)
        test_webhooks()
    else:
        print("\n❌ Auto-import failed. Manual import required.")
        print_manual_instructions()

def test_webhooks():
    """Test if webhooks are now working."""
    test_endpoints = [
        ("tts-generation", {"text": "test", "slug": "test"}),
        ("youtube-upload", {"video_path": "test.mp4", "title": "Test"}),
        ("youtube-analytics", {"video_ids": ["test"]}),
        ("cross-platform-distribute", {"content": {"title": "Test"}, "platforms": ["twitter"]}),
        ("affiliate-shorten", {"original_url": "https://example.com"})
    ]

    working = 0
    for endpoint, data in test_endpoints:
        url = f"{N8N_URL}/webhook/{endpoint}"
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                if response.text and response.text.strip():
                    print(f"  ✓ {endpoint}: Working")
                    working += 1
                else:
                    print(f"  × {endpoint}: Empty response")
            else:
                print(f"  × {endpoint}: Status {response.status_code}")
        except:
            print(f"  × {endpoint}: Not found")

    print(f"\n{working}/{len(test_endpoints)} webhooks are working")

def print_manual_instructions():
    """Print detailed manual import instructions."""
    print("\n" + "=" * 70)
    print("MANUAL IMPORT INSTRUCTIONS")
    print("=" * 70)
    print("""
Since auto-import didn't work, please import manually:

1. OPEN N8N IN YOUR BROWSER:
   http://localhost:5678

2. FOR EACH WORKFLOW FILE:
   a) Click the "+" button (Add workflow)
   b) Click the menu (3 dots) in top right
   c) Select "Import from File"
   d) Choose one of these files:
      - workflows\\tts_webhook_mcp.json
      - workflows\\youtube_upload_mcp.json
      - workflows\\youtube_analytics_mcp.json
      - workflows\\cross_platform_mcp.json
      - workflows\\affiliate_shortener_mcp.json
   e) IMPORTANT: Toggle the workflow to ACTIVE (green switch)
   f) Click "Save"

3. VERIFY ALL 5 WORKFLOWS ARE:
   - Imported (visible in workflows list)
   - Active (green toggle ON)
   - Saved

4. TEST THE SETUP:
   Run: python verify_n8n_setup.py

The import process takes about 2-3 minutes for all 5 workflows.
""")

if __name__ == "__main__":
    main()