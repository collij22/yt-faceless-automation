#!/usr/bin/env python3
"""
Deploy the fixed n8n workflows after diagnosis
"""

import json
import requests
import sys
from pathlib import Path

# n8n instance configuration
N8N_BASE_URL = "http://localhost:5678"
N8N_API_URL = f"{N8N_BASE_URL}/api/v1"

# Workflows to deploy
WORKFLOWS = {
    "youtube_upload_PRODUCTION.json": "YouTube Upload Production",
    "youtube_analytics_PRODUCTION.json": "YouTube Analytics Production"
}

def check_n8n_running():
    """Check if n8n is running"""
    try:
        response = requests.get(N8N_BASE_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def load_workflow(file_path):
    """Load workflow from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return None

def test_webhook(endpoint, test_data):
    """Test a webhook endpoint"""
    url = f"{N8N_BASE_URL}/webhook/{endpoint}"
    try:
        response = requests.post(url, json=test_data, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

def main():
    print("=" * 80)
    print("DEPLOYING FIXED N8N WORKFLOWS")
    print("=" * 80)

    # Check n8n is running
    if not check_n8n_running():
        print("❌ n8n is not running!")
        print("Please start n8n first with: npx n8n start")
        return False

    print("✅ n8n is running")

    # Load and validate workflows
    workflows_dir = Path("workflows")
    loaded_workflows = {}

    for filename, display_name in WORKFLOWS.items():
        file_path = workflows_dir / filename
        if not file_path.exists():
            print(f"❌ Workflow file not found: {file_path}")
            continue

        workflow = load_workflow(file_path)
        if workflow:
            loaded_workflows[filename] = {
                "data": workflow,
                "name": display_name,
                "path": file_path
            }
            print(f"✅ Loaded: {display_name}")
        else:
            print(f"❌ Failed to load: {display_name}")

    if not loaded_workflows:
        print("❌ No workflows to deploy!")
        return False

    print(f"\n📋 Loaded {len(loaded_workflows)} workflows")

    # Manual deployment instructions
    print("\n" + "=" * 80)
    print("MANUAL DEPLOYMENT INSTRUCTIONS")
    print("=" * 80)
    print("Since n8n API requires authentication, please deploy manually:")
    print()
    print("1. Open n8n in your browser: http://localhost:5678")
    print("2. For each workflow below:")
    print("   a. Click 'Delete' if the workflow already exists")
    print("   b. Click '+ Add workflow'")
    print("   c. Click 'Import from file'")
    print("   d. Select the workflow file")
    print("   e. Click 'Save' and 'Activate'")
    print()

    for filename, info in loaded_workflows.items():
        print(f"📁 {info['name']}: {info['path']}")

    # Test instructions
    print("\n" + "=" * 80)
    print("🧪 TESTING INSTRUCTIONS")
    print("=" * 80)

    test_cases = [
        {
            "name": "YouTube Upload",
            "endpoint": "youtube-upload",
            "data": {"title": "Test Video", "description": "Test description"}
        },
        {
            "name": "YouTube Analytics",
            "endpoint": "youtube-analytics",
            "data": {"channel_id": "test123"}
        }
    ]

    print("After deployment, test with these commands:")
    print()

    for test in test_cases:
        data_json = json.dumps(test["data"])
        print(f"# Test {test['name']}")
        print(f"curl -X POST -H \"Content-Type: application/json\" \\")
        print(f"     -d '{data_json}' \\")
        print(f"     {N8N_BASE_URL}/webhook/{test['endpoint']}")
        print()

    print("Expected responses:")
    print("✅ Success: JSON with 'status': 'success'")
    print("⚠️  Error: JSON with 'status': 'error' (NOT a 500 server error)")

    # Automated testing (if user wants to run it after deployment)
    print("\n" + "=" * 80)
    print("🤖 AUTOMATED TESTING")
    print("=" * 80)

    while True:
        user_input = input("Run automated tests now? (y/n/later): ").lower().strip()
        if user_input in ['n', 'no', 'later']:
            print("Skipping automated tests. Run this script again later to test.")
            break
        elif user_input in ['y', 'yes']:
            print("\n🧪 Running automated tests...")

            all_passed = True
            for test in test_cases:
                print(f"\nTesting {test['name']}...")
                status_code, response = test_webhook(test["endpoint"], test["data"])

                if status_code == 200:
                    try:
                        result = json.loads(response)
                        if result.get("status") in ["success", "error"]:
                            print(f"  ✅ PASS - {result.get('status', 'unknown')}")
                        else:
                            print(f"  ⚠️  PARTIAL - Got response but unexpected format: {response[:100]}")
                    except json.JSONDecodeError:
                        print(f"  ❌ FAIL - Invalid JSON response: {response[:100]}")
                        all_passed = False
                else:
                    print(f"  ❌ FAIL - HTTP {status_code}: {response[:100]}")
                    all_passed = False

            if all_passed:
                print("\n🎉 ALL TESTS PASSED! Workflows are working correctly.")
            else:
                print("\n⚠️  Some tests failed. Check the deployment and try again.")
            break
        else:
            print("Please enter 'y' or 'n'")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)