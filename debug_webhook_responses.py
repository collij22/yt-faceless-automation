#!/usr/bin/env python3
"""
Debug n8n webhook responses to understand why tests are failing.
"""

import requests
import json
from datetime import datetime

N8N_URL = "http://localhost:5678"

def test_webhook_detailed(path, name, test_data):
    """Test a webhook and show detailed response."""
    url = f"{N8N_URL}/webhook{path}"
    print(f"\nTesting: {name}")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        # Try to parse response
        try:
            json_response = response.json()
            print(f"JSON Response: {json.dumps(json_response, indent=2)}")
        except:
            print(f"Text Response: {response.text[:500]}")

        return response

    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=" * 70)
    print("N8N WEBHOOK DEBUG TEST")
    print("=" * 70)

    # Test each webhook with appropriate data
    tests = [
        {
            "path": "/tts-generation",
            "name": "TTS Generation",
            "data": {
                "text": "Test text for TTS",
                "slug": "test_" + datetime.now().strftime("%H%M%S"),
                "provider": "elevenlabs"
            }
        },
        {
            "path": "/youtube-upload",
            "name": "YouTube Upload",
            "data": {
                "video_path": "test.mp4",
                "title": "Test Video",
                "description": "Test description"
            }
        },
        {
            "path": "/youtube-analytics",
            "name": "YouTube Analytics",
            "data": {
                "video_ids": ["test123"],
                "metrics": ["views", "likes"]
            }
        },
        {
            "path": "/cross-platform-distribute",
            "name": "Cross-Platform Distribution",
            "data": {
                "content": {
                    "title": "Test Content",
                    "description": "Test description"
                },
                "platforms": ["twitter"]
            }
        },
        {
            "path": "/affiliate-shorten",
            "name": "Affiliate Shortener",
            "data": {
                "original_url": "https://example.com/product",
                "campaign": "test"
            }
        }
    ]

    results = []
    for test in tests:
        response = test_webhook_detailed(test["path"], test["name"], test["data"])
        results.append({
            "name": test["name"],
            "success": response is not None and response.status_code == 200
        })

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for result in results:
        status = "OK" if result["success"] else "FAILED"
        print(f"{result['name']}: {status}")

    # Check if workflows might be inactive
    print("\n" + "=" * 70)
    print("POSSIBLE ISSUES:")
    print("=" * 70)
    print("1. Workflows might be INACTIVE in n8n (check toggle switches)")
    print("2. Workflows might have execution errors")
    print("3. Response nodes might not be configured correctly")
    print("4. Environment variables might be missing")
    print("\nTo check workflow status:")
    print("1. Open http://localhost:5678")
    print("2. Go to Workflows")
    print("3. Check if workflows are ACTIVE (green toggle)")
    print("4. Check Executions tab for error details")

if __name__ == "__main__":
    main()