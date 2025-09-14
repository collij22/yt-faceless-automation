#!/usr/bin/env python3
"""
Test script for n8n YouTube upload workflow.
"""

import requests
import json
import time
from pathlib import Path

def test_youtube_upload_workflow(n8n_url="http://localhost:5678"):
    """Test the YouTube upload workflow in n8n."""

    # Webhook endpoint
    webhook_url = f"{n8n_url}/webhook/youtube-upload"

    # Test data
    test_data = {
        "video_path": "C:/AI projects/0000000000000000_yt1/content/test_video/final.mp4",
        "title": "Test Video Upload from n8n",
        "description": "This is a test upload to verify n8n workflow is working correctly.",
        "tags": ["test", "n8n", "automation"],
        "category_id": "22",
        "privacy": "private",
        "slug": "test_video"
    }

    print("=" * 60)
    print("N8N YOUTUBE UPLOAD WORKFLOW TEST")
    print("=" * 60)
    print()
    print(f"Testing webhook: {webhook_url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    print()

    try:
        # Send request
        print("Sending request to n8n workflow...")
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(result, indent=2)}")

            # Check key fields
            if result.get("success"):
                print("\n✅ All checks passed:")
                print(f"  - Video ID: {result.get('video_id')}")
                print(f"  - Video URL: {result.get('video_url')}")
                print(f"  - Studio URL: {result.get('studio_url')}")
            else:
                print("\n⚠️ Upload reported failure")
                print(f"  - Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach n8n")
        print("Make sure n8n is running and the webhook is active")
        print("\nTroubleshooting:")
        print("1. Check if n8n is running")
        print("2. Check if the workflow is active")
        print("3. Verify the webhook URL is correct")

    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
        print("The workflow might be taking longer than expected")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_backend_directly(backend_url="http://localhost:8000"):
    """Test the backend API directly (bypassing n8n)."""

    upload_url = f"{backend_url}/api/youtube/upload"

    test_data = {
        "video_path": "test.mp4",
        "title": "Direct Backend Test",
        "description": "Testing backend API directly"
    }

    print("\n" + "=" * 60)
    print("BACKEND API DIRECT TEST")
    print("=" * 60)
    print()
    print(f"Testing backend: {upload_url}")

    try:
        response = requests.post(
            upload_url,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "test_key"
            },
            timeout=10
        )

        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is responding")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Backend error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Backend not running")
        print("Start the backend with: python youtube_backend_api.py")

    except Exception as e:
        print(f"❌ Error: {e}")

def check_environment():
    """Check environment setup."""
    print("=" * 60)
    print("ENVIRONMENT CHECK")
    print("=" * 60)
    print()

    # Check for required files
    files_to_check = [
        "workflows/youtube_upload_no_oauth.json",
        ".env",
        "youtube_backend_api.py"
    ]

    for file in files_to_check:
        path = Path(file)
        if path.exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} not found")

    # Check environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv()

    env_vars = [
        "YOUTUBE_API_KEY",
        "BACKEND_URL",
        "N8N_UPLOAD_WEBHOOK_URL"
    ]

    print("\nEnvironment variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} is set ({value[:20]}...)")
        else:
            print(f"⚠️ {var} not set")

if __name__ == "__main__":
    import sys

    print("N8N YOUTUBE WORKFLOW TEST SUITE")
    print("================================\n")

    # Check environment first
    check_environment()

    # Test based on arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "backend":
            test_backend_directly()
        elif sys.argv[1] == "n8n":
            test_youtube_upload_workflow()
        else:
            print(f"\nUnknown option: {sys.argv[1]}")
            print("Usage: python test_n8n_workflow.py [backend|n8n]")
    else:
        # Test both
        print("\n" + "=" * 60)
        print("Run specific tests with:")
        print("  python test_n8n_workflow.py backend  - Test backend only")
        print("  python test_n8n_workflow.py n8n      - Test n8n workflow")
        print("=" * 60)

        # Default: test n8n workflow
        print("\nTesting n8n workflow by default...")
        time.sleep(2)
        test_youtube_upload_workflow()