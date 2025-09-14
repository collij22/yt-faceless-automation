import requests
import json
import time

BASE_URL = "http://localhost:5678"

def test_webhook_get(endpoint, name):
    """Test if webhook exists with GET request"""
    print(f"\nTesting GET: {name}")
    try:
        response = requests.get(f"{BASE_URL}/webhook/{endpoint}")
        print(f"  GET Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}")
        return response.status_code != 404
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

def test_webhook_post(endpoint, data, name):
    """Test webhook with POST request"""
    print(f"\nTesting POST: {name}")
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/{endpoint}",
            json=data,
            timeout=30
        )
        print(f"  POST Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

def test_webhook_test_mode(endpoint, data, name):
    """Test webhook in test mode"""
    print(f"\nTesting Test Mode: {name}")
    try:
        response = requests.post(
            f"{BASE_URL}/webhook-test/{endpoint}",
            json=data,
            timeout=30
        )
        print(f"  Test Mode Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False

def diagnose_webhooks():
    """Diagnose webhook issues"""

    print("="*60)
    print("N8N WEBHOOK DIAGNOSTICS")
    print("="*60)

    # Check n8n is running
    try:
        response = requests.get(BASE_URL)
        print(f"[OK] n8n is running at {BASE_URL}")
    except:
        print(f"[ERROR] n8n is NOT running at {BASE_URL}")
        return

    webhooks = [
        ("tts-generation", {"text": "test", "slug": "test"}, "TTS Generation"),
        ("youtube-upload", {"title": "Test", "description": "Test", "video_url": "https://example.com/test.mp4"}, "YouTube Upload"),
        ("youtube-analytics", {"channel_id": "test"}, "YouTube Analytics"),
        ("cross-platform-distribute", {"title": "Test", "video_url": "https://example.com/test.mp4"}, "Cross-Platform"),
        ("affiliate-shorten", {"original_url": "https://amazon.com/test"}, "Affiliate Shortener")
    ]

    print("\n" + "="*60)
    print("CHECKING WEBHOOK ENDPOINTS")
    print("="*60)

    for endpoint, data, name in webhooks:
        print(f"\n--- {name} ---")

        # Test GET
        get_exists = test_webhook_get(endpoint, name)

        # Test POST
        if get_exists:
            post_works = test_webhook_post(endpoint, data, name)
        else:
            print("  Skipping POST test (webhook not found)")
            post_works = False

        # Test test mode
        test_mode_works = test_webhook_test_mode(endpoint, data, name)

        # Summary for this webhook
        if post_works:
            print(f"  [SUCCESS] {name} webhook is WORKING")
        elif get_exists:
            print(f"  [WARNING] {name} webhook EXISTS but has errors")
        else:
            print(f"  [FAIL] {name} webhook NOT FOUND")

    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)

    print("""
    If webhooks exist but return errors:
    1. Open each workflow in n8n
    2. Check for red error indicators on nodes
    3. Click on the webhook node and check its settings
    4. Make sure the workflow is ACTIVE (toggle in top right)
    5. Try executing the workflow manually once

    If webhooks are not found (404):
    1. Re-import the workflow files
    2. Make sure to ACTIVATE each workflow
    3. Check the webhook path in the webhook node matches the test

    To test in n8n UI:
    1. Open the workflow
    2. Click 'Execute Workflow' button
    3. For webhook node, you'll see the actual URL
    4. Copy that URL and test with curl
    """)

if __name__ == "__main__":
    diagnose_webhooks()