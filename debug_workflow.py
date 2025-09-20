"""
Debug n8n workflow issues
"""

import requests
import json

def test_workflow(endpoint, data, name):
    """Test a single workflow with detailed output"""
    url = f"http://localhost:5678/webhook/{endpoint}"
    print(f"\nTesting: {name}")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 40)

    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    print("N8N Workflow Debugger")
    print("=" * 60)

    # Test each workflow with minimal data
    tests = [
        # 1. Test TTS with minimal data
        ("tts-generation", {
            "text": "Hello world",
            "slug": "test"
        }, "TTS Generation - Minimal"),

        # 2. Test TTS with full data
        ("tts-generation", {
            "text": "This is a test",
            "slug": "test123",
            "provider": "mock",
            "voice_id": "test",
            "language": "en"
        }, "TTS Generation - Full"),

        # 3. Test Upload
        ("youtube-upload", {
            "title": "Test Video",
            "description": "Test Description"
        }, "YouTube Upload"),

        # 4. Test Analytics (no required fields)
        ("youtube-analytics", {}, "YouTube Analytics - Empty"),

        # 5. Test Analytics with data
        ("youtube-analytics", {
            "channel_id": "test_channel"
        }, "YouTube Analytics - With Channel"),

        # 6. Test Cross-Platform
        ("cross-platform-distribute", {
            "title": "Test Content"
        }, "Cross-Platform Distribution"),

        # 7. Test Affiliate
        ("affiliate-shorten", {
            "original_url": "https://example.com"
        }, "Affiliate Shortener")
    ]

    results = []
    for endpoint, data, name in tests:
        success = test_workflow(endpoint, data, name)
        results.append((name, success))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"{status} {name}")

    success_count = sum(1 for _, s in results if s)
    print(f"\nPassed: {success_count}/{len(results)}")

if __name__ == "__main__":
    main()