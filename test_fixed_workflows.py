#!/usr/bin/env python3
"""Test script to validate fixed n8n production workflows."""

import json
import requests
import time
from typing import Dict, Any

# Test data for each workflow
TEST_DATA = {
    "tts-generation": {
        "text": "Hello world",
        "slug": "test"
    },
    "youtube-upload": {
        "title": "Test",
        "description": "Test video"
    },
    "youtube-analytics": {
        "channel_id": "test"
    },
    "cross-platform-distribute": {
        "title": "Test content"
    },
    "affiliate-shorten": {
        "original_url": "https://example.com"
    }
}

# n8n webhook base URL (adjust based on your n8n instance)
BASE_URL = "http://localhost:5678/webhook"

def test_webhook(webhook_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single webhook endpoint."""
    url = f"{BASE_URL}/{webhook_path}"

    try:
        print(f"\n🧪 Testing {webhook_path}...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(data, indent=2)}")

        response = requests.post(
            url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return {
                "success": True,
                "status_code": response.status_code,
                "response": result
            }
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ Connection failed - n8n may not be running")
        return {
            "success": False,
            "error": "Connection failed - n8n not running"
        }
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Run all webhook tests."""
    print("=" * 60)
    print("TESTING FIXED N8N PRODUCTION WORKFLOWS")
    print("=" * 60)

    results = {}

    for webhook_path, test_data in TEST_DATA.items():
        results[webhook_path] = test_webhook(webhook_path, test_data)
        time.sleep(1)  # Small delay between tests

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    successful = [path for path, result in results.items() if result.get("success")]
    failed = [path for path, result in results.items() if not result.get("success")]

    print(f"\n✅ Successful: {len(successful)}/{len(TEST_DATA)}")
    for path in successful:
        print(f"   • {path}")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(TEST_DATA)}")
        for path in failed:
            error = results[path].get("error", "Unknown error")
            print(f"   • {path}: {error}")

    print(f"\n🎯 Overall success rate: {len(successful)/len(TEST_DATA)*100:.1f}%")

    if len(successful) == len(TEST_DATA):
        print("\n🚀 ALL WORKFLOWS ARE WORKING CORRECTLY!")
    else:
        print(f"\n⚠️ {len(failed)} workflow(s) still need attention")

    return len(successful) == len(TEST_DATA)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)