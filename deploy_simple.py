#!/usr/bin/env python3
"""
Simple deployment guide for fixed n8n workflows
"""

import requests
import json

# Check if n8n is running
def check_n8n():
    try:
        response = requests.get("http://localhost:5678", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_endpoint(endpoint, data):
    """Test a webhook endpoint"""
    url = f"http://localhost:5678/webhook/{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

def main():
    print("=" * 80)
    print("N8N WORKFLOW DEPLOYMENT GUIDE")
    print("=" * 80)

    # Check n8n
    if check_n8n():
        print("SUCCESS: n8n is running at http://localhost:5678")
    else:
        print("ERROR: n8n is not running!")
        print("Please start n8n with: npx n8n start")
        return

    print("\nMANUAL DEPLOYMENT STEPS:")
    print("1. Open http://localhost:5678 in browser")
    print("2. Delete existing workflows if they exist:")
    print("   - YouTube Upload Production")
    print("   - YouTube Analytics Production")
    print("3. Import these fixed files:")
    print("   - workflows/youtube_upload_PRODUCTION.json")
    print("   - workflows/youtube_analytics_PRODUCTION.json")
    print("4. Activate both workflows")
    print("5. Run tests below")

    print("\n" + "=" * 80)
    print("TESTING COMMANDS")
    print("=" * 80)

    tests = [
        ("youtube-upload", {"title": "Test", "description": "Test video"}),
        ("youtube-analytics", {"channel_id": "test123"})
    ]

    for endpoint, data in tests:
        print(f"\n# Test {endpoint}")
        print("curl -X POST -H \"Content-Type: application/json\" \\")
        print(f"     -d '{json.dumps(data)}' \\")
        print(f"     http://localhost:5678/webhook/{endpoint}")

    print("\nEXPECTED RESULTS:")
    print("- Should return JSON with 'status': 'success' or 'status': 'error'")
    print("- Should NOT return 'Error in workflow' or 'No item to return'")

    # Offer to run tests
    test_now = input("\nRun tests now? (y/n): ").lower()
    if test_now == 'y':
        print("\nRunning tests...")
        for endpoint, data in tests:
            print(f"\nTesting {endpoint}...")
            status, response = test_endpoint(endpoint, data)
            if status == 200:
                try:
                    result = json.loads(response)
                    if "status" in result:
                        print(f"  PASS: {result['status']}")
                    else:
                        print(f"  PARTIAL: Got response but no status field")
                except:
                    print(f"  FAIL: Invalid JSON - {response[:100]}")
            else:
                print(f"  FAIL: HTTP {status} - {response[:100]}")

if __name__ == "__main__":
    main()