import requests
import json
import time

BASE_URL = "http://localhost:5678/webhook"

def test_workflow(endpoint, data, name):
    """Test a single workflow endpoint"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"{'='*50}")

    try:
        response = requests.post(
            f"{BASE_URL}/{endpoint}",
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            print(f"✅ SUCCESS - Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

    time.sleep(1)  # Rate limiting

def run_all_tests():
    """Run all workflow tests"""

    # TTS Test
    test_workflow(
        "tts-generation",
        {
            "text": "Testing TTS workflow",
            "slug": "test_001",
            "provider": "elevenlabs"
        },
        "TTS Generation"
    )

    # YouTube Upload Test
    test_workflow(
        "youtube-upload",
        {
            "title": "Test Upload",
            "description": "Testing upload workflow",
            "video_url": "https://example.com/test.mp4",
            "tags": ["test"],
            "privacy": "private"
        },
        "YouTube Upload"
    )

    # Analytics Test
    test_workflow(
        "youtube-analytics",
        {
            "channel_id": "UC_test",
            "date_range": "last_7_days"
        },
        "YouTube Analytics"
    )

    # Cross-Platform Test
    test_workflow(
        "cross-platform-distribute",
        {
            "title": "Cross-Platform Test",
            "video_url": "https://example.com/test.mp4",
            "platforms": ["tiktok", "instagram"]
        },
        "Cross-Platform Distribution"
    )

    # Affiliate Shortener Test
    test_workflow(
        "affiliate-shorten",
        {
            "original_url": "https://amazon.com/dp/TEST123",
            "title": "Test Product",
            "utm_source": "youtube"
        },
        "Affiliate Link Shortener"
    )

if __name__ == "__main__":
    print("Starting n8n Workflow Tests...")
    run_all_tests()
    print("\n✅ All tests completed!")