"""
Automated n8n workflow deployment and testing
This script will help you import and test all workflows automatically
"""

import json
import os
import requests
import time
import sys

BASE_URL = "http://localhost:5678"

def check_n8n_running():
    """Check if n8n is running"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def test_webhook(endpoint, data, name):
    """Test a single webhook endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/{endpoint}",
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  [OK] {name}: {result.get('status', 'success')}")
            return True
        elif response.status_code == 404:
            print(f"  [NOT FOUND] {name}: Workflow not imported or not active")
            return False
        elif response.status_code == 500:
            print(f"  [ERROR] {name}: Workflow has errors")
            return False
        else:
            print(f"  [FAIL] {name}: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] {name}: {str(e)}")
        return False

def run_all_tests():
    """Run tests for all workflows"""
    print("\n" + "="*60)
    print("TESTING ALL WORKFLOWS")
    print("="*60)

    tests = [
        ("tts-generation", {"text": "Hello world", "slug": "test"}, "TTS Generation"),
        ("youtube-upload", {"title": "Test Video", "description": "Test description"}, "YouTube Upload"),
        ("youtube-analytics", {"channel_id": "UC_test"}, "YouTube Analytics"),
        ("cross-platform-distribute", {"title": "Test Video"}, "Cross-Platform"),
        ("affiliate-shorten", {"original_url": "https://amazon.com/test"}, "Affiliate Shortener")
    ]

    success_count = 0
    failed = []

    for endpoint, data, name in tests:
        if test_webhook(endpoint, data, name):
            success_count += 1
        else:
            failed.append(name)
        time.sleep(0.5)

    print(f"\nResults: {success_count}/{len(tests)} working")

    if failed:
        print("\nFailed workflows:")
        for name in failed:
            print(f"  - {name}")

    return success_count == len(tests)

def show_import_instructions():
    """Show manual import instructions"""
    print("\n" + "="*60)
    print("MANUAL IMPORT INSTRUCTIONS")
    print("="*60)

    print("""
1. Open n8n at http://localhost:5678

2. DELETE existing workflows:
   - Go to Workflows page
   - Select each old workflow
   - Delete them

3. IMPORT new MINIMAL workflows:
   - Click 'Add Workflow'
   - Click menu (three dots) -> Import from File
   - Import these files from the workflows folder:
     *tts_webhook_MINIMAL.json
     *youtube_upload_MINIMAL.json
     *youtube_analytics_MINIMAL.json
     *cross_platform_MINIMAL.json
     *affiliate_shortener_MINIMAL.json

4. ACTIVATE each workflow:
   - Open each imported workflow
   - Toggle the activation switch (top right)
   - Switch should be green/blue when active

5. Run tests again:
   python auto_deploy_and_test.py
""")

def main():
    print("="*60)
    print("N8N WORKFLOW AUTOMATED DEPLOYMENT & TESTING")
    print("="*60)

    # Check n8n is running
    print("\n[1] Checking n8n status...")
    if not check_n8n_running():
        print("  [ERROR] n8n is not running at http://localhost:5678")
        print("  Please start n8n first!")
        sys.exit(1)
    print("  [OK] n8n is running")

    # Run tests
    print("\n[2] Testing workflows...")
    all_working = run_all_tests()

    if all_working:
        print("\n" + "="*60)
        print("SUCCESS! All workflows are working!")
        print("="*60)
        print("\nYour n8n workflows are ready to use.")
        print("\nTest endpoints:")
        print("  - POST http://localhost:5678/webhook/tts-generation")
        print("  - POST http://localhost:5678/webhook/youtube-upload")
        print("  - POST http://localhost:5678/webhook/youtube-analytics")
        print("  - POST http://localhost:5678/webhook/cross-platform-distribute")
        print("  - POST http://localhost:5678/webhook/affiliate-shorten")
    else:
        show_import_instructions()

        print("\n" + "="*60)
        print("TROUBLESHOOTING")
        print("="*60)
        print("""
Common issues:

1. "Workflow not imported or not active"
   ->Import the MINIMAL workflow files
   ->Make sure to ACTIVATE each workflow

2. "Workflow has errors"
   ->Open the workflow in n8n
   ->Check for red error indicators
   ->Make sure you imported the MINIMAL versions

3. Still not working?
   ->Delete ALL workflows in n8n
   ->Import only the 5 MINIMAL workflows
   ->Activate each one
   ->Run this test again
""")

if __name__ == "__main__":
    main()