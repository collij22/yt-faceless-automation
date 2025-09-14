#!/usr/bin/env python3
"""
Comprehensive test suite for all n8n MCP workflows.
Tests all 5 workflows: TTS, YouTube Upload, Analytics, Cross-Platform, and Affiliate Shortener.
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import base64

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBy4nQXiHuslrLgQwnqi0W-GuC1tb4WFTA")

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "workflows": {},
    "summary": {"passed": 0, "failed": 0, "total": 5}
}

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test_result(workflow: str, success: bool, details: str = ""):
    """Print formatted test result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {workflow}: {'PASSED' if success else 'FAILED'}")
    if details:
        print(f"   Details: {details}")

def test_tts_webhook() -> Dict[str, Any]:
    """Test TTS Generation webhook workflow."""
    print_header("Testing TTS Generation Workflow")

    webhook_url = f"{N8N_BASE_URL}/webhook/tts-generation"
    test_data = {
        "text": "Hello, this is a test of the text to speech system. It should handle multiple sentences well. This is the third sentence to ensure we have enough content.",
        "slug": "test_tts_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "provider": "elevenlabs",
        "model_id": "eleven_monolingual_v1",
        "chunk_size": 100  # Small chunk size for testing
    }

    print(f"Webhook URL: {webhook_url}")
    print(f"Test slug: {test_data['slug']}")

    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        success = response.status_code == 200
        result = {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if success else response.text,
            "test_data": test_data
        }

        if success:
            print_test_result("TTS Generation", True, f"Audio chunks processed for slug: {test_data['slug']}")
        else:
            print_test_result("TTS Generation", False, f"Status code: {response.status_code}")

        return result

    except requests.exceptions.ConnectionError:
        print_test_result("TTS Generation", False, "Cannot connect to n8n webhook")
        return {"success": False, "error": "Connection refused"}
    except Exception as e:
        print_test_result("TTS Generation", False, str(e))
        return {"success": False, "error": str(e)}

def test_youtube_upload() -> Dict[str, Any]:
    """Test YouTube Upload webhook workflow."""
    print_header("Testing YouTube Upload Workflow")

    webhook_url = f"{N8N_BASE_URL}/webhook/youtube-upload"
    test_data = {
        "video_path": "C:/AI projects/test_video.mp4",
        "title": "Test Upload - " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "description": "This is an automated test of the YouTube upload workflow via n8n MCP integration.",
        "tags": ["test", "automation", "n8n", "mcp"],
        "category_id": "22",
        "privacy": "private",
        "thumbnail_path": "C:/AI projects/test_thumbnail.jpg",
        "playlist_id": "PLtest123",
        "slug": "test_upload",
        "chapters": [
            {"start": "0:00", "title": "Introduction"},
            {"start": "1:30", "title": "Main Content"},
            {"start": "5:00", "title": "Conclusion"}
        ]
    }

    print(f"Webhook URL: {webhook_url}")
    print(f"Video title: {test_data['title']}")

    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        success = response.status_code == 200
        result = {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if success else response.text,
            "test_data": test_data
        }

        if success:
            video_id = result["response"].get("video_id", "unknown")
            print_test_result("YouTube Upload", True, f"Video ID: {video_id}")
        else:
            print_test_result("YouTube Upload", False, f"Status code: {response.status_code}")

        return result

    except Exception as e:
        print_test_result("YouTube Upload", False, str(e))
        return {"success": False, "error": str(e)}

def test_youtube_analytics() -> Dict[str, Any]:
    """Test YouTube Analytics webhook workflow."""
    print_header("Testing YouTube Analytics Workflow")

    webhook_url = f"{N8N_BASE_URL}/webhook/youtube-analytics"
    test_data = {
        "video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"],  # Famous YouTube videos for testing
        "metrics": ["views", "likes", "comments", "dislikes"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }

    print(f"Webhook URL: {webhook_url}")
    print(f"Analyzing {len(test_data['video_ids'])} videos")

    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": YOUTUBE_API_KEY
            },
            timeout=30
        )

        success = response.status_code == 200
        result = {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if success else response.text,
            "test_data": test_data
        }

        if success:
            metrics = result["response"].get("aggregate_metrics", {})
            print_test_result("YouTube Analytics", True, f"Analyzed {len(test_data['video_ids'])} videos")
        else:
            print_test_result("YouTube Analytics", False, f"Status code: {response.status_code}")

        return result

    except Exception as e:
        print_test_result("YouTube Analytics", False, str(e))
        return {"success": False, "error": str(e)}

def test_cross_platform_distribution() -> Dict[str, Any]:
    """Test Cross-Platform Distribution webhook workflow."""
    print_header("Testing Cross-Platform Distribution Workflow")

    webhook_url = f"{N8N_BASE_URL}/webhook/cross-platform-distribute"
    test_data = {
        "content": {
            "title": "Amazing Content Test - " + datetime.now().strftime("%H:%M"),
            "description": "Check out this incredible test content! Testing cross-platform distribution via n8n MCP workflows.",
            "video_path": "https://example.com/test_video.mp4",
            "thumbnail_path": "https://example.com/test_thumb.jpg",
            "hashtags": ["test", "automation", "viral", "tech"]
        },
        "platforms": ["twitter", "instagram", "linkedin", "tiktok"],
        "schedule_time": None,  # Post immediately
        "custom_messages": {
            "twitter": "🚀 New video alert! Check it out:",
            "instagram": "New content dropping! 🎬",
            "linkedin": "Excited to share my latest work on automation",
            "tiktok": "You won't believe this! #viral"
        }
    }

    print(f"Webhook URL: {webhook_url}")
    print(f"Platforms: {', '.join(test_data['platforms'])}")

    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=45
        )

        success = response.status_code == 200
        result = {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if success else response.text,
            "test_data": test_data
        }

        if success:
            platforms_posted = result["response"].get("successful_platforms", [])
            print_test_result("Cross-Platform Distribution", True,
                            f"Posted to {len(platforms_posted)}/{len(test_data['platforms'])} platforms")
        else:
            print_test_result("Cross-Platform Distribution", False, f"Status code: {response.status_code}")

        return result

    except Exception as e:
        print_test_result("Cross-Platform Distribution", False, str(e))
        return {"success": False, "error": str(e)}

def test_affiliate_shortener() -> Dict[str, Any]:
    """Test Affiliate Link Shortener webhook workflow."""
    print_header("Testing Affiliate Link Shortener Workflow")

    webhook_url = f"{N8N_BASE_URL}/webhook/affiliate-shorten"
    test_data = {
        "original_url": "https://www.amazon.com/dp/B08N5WRWNW?tag=test-20",
        "campaign": "youtube_test_" + datetime.now().strftime("%Y%m%d"),
        "source": "youtube",
        "medium": "video_description",
        "content": "product_link",
        "custom_domain": "bit.ly",
        "title": "Echo Dot (4th Gen) - Test Link",
        "tags": ["amazon", "affiliate", "smart-home"],
        "track_clicks": True,
        "generate_qr": True
    }

    print(f"Webhook URL: {webhook_url}")
    print(f"Original URL: {test_data['original_url'][:50]}...")

    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )

        success = response.status_code == 200
        result = {
            "success": success,
            "status_code": response.status_code,
            "response": response.json() if success else response.text,
            "test_data": test_data
        }

        if success:
            short_url = result["response"].get("short_url", "N/A")
            print_test_result("Affiliate Shortener", True, f"Shortened URL: {short_url}")
        else:
            print_test_result("Affiliate Shortener", False, f"Status code: {response.status_code}")

        return result

    except Exception as e:
        print_test_result("Affiliate Shortener", False, str(e))
        return {"success": False, "error": str(e)}

def run_all_tests():
    """Run all workflow tests and generate report."""
    print("\n" + "🚀" * 35)
    print("     N8N MCP WORKFLOWS - COMPREHENSIVE TEST SUITE")
    print("🚀" * 35)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"n8n URL: {N8N_BASE_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Key: {YOUTUBE_API_KEY[:10]}..." if YOUTUBE_API_KEY else "API Key: Not set")

    # Run all tests
    tests = [
        ("TTS Generation", test_tts_webhook),
        ("YouTube Upload", test_youtube_upload),
        ("YouTube Analytics", test_youtube_analytics),
        ("Cross-Platform Distribution", test_cross_platform_distribution),
        ("Affiliate Shortener", test_affiliate_shortener)
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            test_results["workflows"][name] = result
            if result.get("success"):
                test_results["summary"]["passed"] += 1
            else:
                test_results["summary"]["failed"] += 1
        except Exception as e:
            print(f"❌ Failed to run {name} test: {e}")
            test_results["workflows"][name] = {"success": False, "error": str(e)}
            test_results["summary"]["failed"] += 1

        time.sleep(1)  # Small delay between tests

    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total Tests: {test_results['summary']['total']}")
    print(f"✅ Passed: {test_results['summary']['passed']}")
    print(f"❌ Failed: {test_results['summary']['failed']}")
    print(f"Success Rate: {(test_results['summary']['passed'] / test_results['summary']['total'] * 100):.1f}%")

    # Save detailed results
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n📄 Detailed results saved to: {results_file}")

    # Print workflow-specific notes
    print("\n📝 NOTES:")
    print("1. TTS workflow requires ElevenLabs API or Google TTS configured")
    print("2. YouTube workflows need backend API running (python youtube_backend_api.py)")
    print("3. Cross-platform needs social media API credentials")
    print("4. Affiliate shortener needs Bitly/TinyURL access")
    print("5. Make sure all workflows are ACTIVE in n8n")

    return test_results["summary"]["passed"] == test_results["summary"]["total"]

def quick_connectivity_check():
    """Quick check to ensure n8n is reachable."""
    print("\n🔍 Quick Connectivity Check...")

    try:
        # Try to reach n8n
        response = requests.get(f"{N8N_BASE_URL}/", timeout=5)
        print(f"✅ n8n is reachable at {N8N_BASE_URL}")
        return True
    except:
        print(f"❌ Cannot reach n8n at {N8N_BASE_URL}")
        print("   Make sure n8n is running and accessible")
        return False

if __name__ == "__main__":
    import sys

    # Check for specific test argument
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()

        if test_name == "tts":
            test_tts_webhook()
        elif test_name == "upload":
            test_youtube_upload()
        elif test_name == "analytics":
            test_youtube_analytics()
        elif test_name == "distribute":
            test_cross_platform_distribution()
        elif test_name == "affiliate":
            test_affiliate_shortener()
        elif test_name == "check":
            quick_connectivity_check()
        else:
            print(f"Unknown test: {test_name}")
            print("\nAvailable tests:")
            print("  python test_all_mcp_workflows.py         # Run all tests")
            print("  python test_all_mcp_workflows.py tts     # Test TTS only")
            print("  python test_all_mcp_workflows.py upload  # Test YouTube upload only")
            print("  python test_all_mcp_workflows.py analytics # Test analytics only")
            print("  python test_all_mcp_workflows.py distribute # Test distribution only")
            print("  python test_all_mcp_workflows.py affiliate # Test affiliate only")
            print("  python test_all_mcp_workflows.py check   # Quick connectivity check")
    else:
        # Run all tests
        if quick_connectivity_check():
            success = run_all_tests()
            sys.exit(0 if success else 1)
        else:
            print("\n⚠️  Fix connectivity issues before running tests")
            sys.exit(1)