#!/usr/bin/env python3
"""
n8n Webhook Testing Script

This script tests the deployed n8n webhooks with sample data to ensure they're working correctly.

Usage:
    python test_n8n_webhooks.py

Requirements:
    - Webhooks deployed and active in n8n
    - Webhook URLs configured in environment variables
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional
import requests


class WebhookTester:
    """Tests n8n webhook endpoints."""

    def __init__(self):
        """Initialize the tester with environment configuration."""
        # Load webhook URLs from environment
        self.webhook_urls = {
            "tts": os.getenv("N8N_TTS_WEBHOOK_URL"),
            "upload": os.getenv("N8N_UPLOAD_WEBHOOK_URL"),
            "analytics": os.getenv("N8N_ANALYTICS_WEBHOOK_URL"),
            "cross_platform": os.getenv("N8N_CROSS_PLATFORM_WEBHOOK_URL"),
            "affiliate": os.getenv("N8N_AFFILIATE_WEBHOOK_URL")
        }

        # Filter out None values
        self.webhook_urls = {k: v for k, v in self.webhook_urls.items() if v}

        if not self.webhook_urls:
            print("⚠️  No webhook URLs found in environment variables")
            print("   Make sure the following are set in your .env file:")
            print("   - N8N_TTS_WEBHOOK_URL")
            print("   - N8N_UPLOAD_WEBHOOK_URL")
            print("   - N8N_ANALYTICS_WEBHOOK_URL")
            print("   - N8N_CROSS_PLATFORM_WEBHOOK_URL")
            print("   - N8N_AFFILIATE_WEBHOOK_URL")

    def test_tts_webhook(self, webhook_url: str) -> bool:
        """Test the TTS generation webhook."""
        test_data = {
            "text": "This is a test of the TTS generation webhook. If you can hear this, it means the webhook is working correctly.",
            "slug": "webhook_test",
            "voice_id": "UgBBYS2sOqTuMpoF3BR0",
            "provider": "elevenlabs",
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        return self._send_webhook_request(webhook_url, test_data, "TTS Generation")

    def test_upload_webhook(self, webhook_url: str) -> bool:
        """Test the YouTube upload webhook."""
        test_data = {
            "video_path": "/content/webhook_test/final.mp4",
            "title": "Test Video - Webhook Validation",
            "description": "This is a test video uploaded via the n8n webhook to validate the deployment.",
            "tags": ["test", "webhook", "n8n", "automation"],
            "privacy": "private",
            "category_id": "22",
            "slug": "webhook_test",
            "thumbnail_path": "/content/webhook_test/thumbnail.jpg"
        }

        return self._send_webhook_request(webhook_url, test_data, "YouTube Upload")

    def test_analytics_webhook(self, webhook_url: str) -> bool:
        """Test the YouTube analytics webhook."""
        test_data = {
            "video_id": "test_video_id_123",
            "slug": "webhook_test",
            "metrics": ["views", "likes", "comments", "shares"],
            "date_range": {
                "start_date": "2025-09-01",
                "end_date": "2025-09-14"
            }
        }

        return self._send_webhook_request(webhook_url, test_data, "YouTube Analytics")

    def test_cross_platform_webhook(self, webhook_url: str) -> bool:
        """Test the cross-platform distribution webhook."""
        test_data = {
            "content_slug": "webhook_test",
            "platforms": ["tiktok", "instagram", "twitter"],
            "video_path": "/content/webhook_test/final.mp4",
            "title": "Test Content - Cross Platform",
            "description": "Test cross-platform distribution",
            "tags": ["test", "multiplatform"]
        }

        return self._send_webhook_request(webhook_url, test_data, "Cross Platform Distribution")

    def test_affiliate_webhook(self, webhook_url: str) -> bool:
        """Test the affiliate link shortener webhook."""
        test_data = {
            "original_url": "https://example.com/affiliate-link?ref=test123",
            "campaign": "webhook_test",
            "slug": "test_affiliate",
            "description": "Test affiliate link shortening"
        }

        return self._send_webhook_request(webhook_url, test_data, "Affiliate Link Shortener")

    def _send_webhook_request(self, webhook_url: str, data: Dict[str, Any], webhook_name: str) -> bool:
        """Send a test request to a webhook endpoint."""
        print(f"🧪 Testing {webhook_name} webhook...")
        print(f"   URL: {webhook_url}")

        try:
            response = requests.post(
                webhook_url,
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "n8n-webhook-tester/1.0"
                },
                timeout=30
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success - Response received")
                    if "status" in result:
                        print(f"      Status: {result['status']}")
                    if "message" in result:
                        print(f"      Message: {result['message']}")
                    return True
                except json.JSONDecodeError:
                    print(f"   ✅ Success - Non-JSON response (length: {len(response.text)})")
                    return True
            else:
                print(f"   ❌ Failed - HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        print(f"      Error: {error_data['message']}")
                except:
                    print(f"      Response: {response.text[:200]}...")
                return False

        except requests.exceptions.Timeout:
            print(f"   ❌ Failed - Request timeout (>30s)")
            return False
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Failed - Connection error (webhook may not be active)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed - Request error: {e}")
            return False

    def test_all_webhooks(self) -> bool:
        """Test all configured webhooks."""
        print("🧪 Testing n8n webhook endpoints...")
        print("=" * 60)

        if not self.webhook_urls:
            return False

        test_functions = {
            "tts": self.test_tts_webhook,
            "upload": self.test_upload_webhook,
            "analytics": self.test_analytics_webhook,
            "cross_platform": self.test_cross_platform_webhook,
            "affiliate": self.test_affiliate_webhook
        }

        total_tests = len(self.webhook_urls)
        passed_tests = 0

        for webhook_name, webhook_url in self.webhook_urls.items():
            print(f"\n📡 Testing {webhook_name.upper()} webhook")
            print("-" * 40)

            test_function = test_functions.get(webhook_name)
            if test_function:
                if test_function(webhook_url):
                    passed_tests += 1
            else:
                print(f"⚠️  No test function available for {webhook_name}")

            # Small delay between tests
            if webhook_name != list(self.webhook_urls.keys())[-1]:
                time.sleep(1)

        # Summary
        print("\n" + "=" * 60)
        print("📊 WEBHOOK TEST SUMMARY")
        print("=" * 60)
        print(f"Total webhooks tested: {total_tests}")
        print(f"Tests passed: {passed_tests}")
        print(f"Tests failed: {total_tests - passed_tests}")

        if passed_tests == total_tests:
            print("\n🎉 All webhook tests passed!")
            print("✅ n8n workflows are properly deployed and functional")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} webhook tests failed")
            print("❌ Check n8n workflow deployment and activation")
            return False

    def check_webhook_availability(self) -> None:
        """Check which webhooks are configured and potentially available."""
        print("🔍 Checking webhook configuration...")
        print("-" * 40)

        all_possible_webhooks = {
            "N8N_TTS_WEBHOOK_URL": "TTS Generation",
            "N8N_UPLOAD_WEBHOOK_URL": "YouTube Upload",
            "N8N_ANALYTICS_WEBHOOK_URL": "YouTube Analytics",
            "N8N_CROSS_PLATFORM_WEBHOOK_URL": "Cross Platform Distribution",
            "N8N_AFFILIATE_WEBHOOK_URL": "Affiliate Link Shortener"
        }

        configured = []
        missing = []

        for env_var, description in all_possible_webhooks.items():
            value = os.getenv(env_var)
            if value:
                configured.append(f"{description}: {value}")
            else:
                missing.append(f"{description} ({env_var})")

        if configured:
            print("✅ Configured webhooks:")
            for webhook in configured:
                print(f"   • {webhook}")

        if missing:
            print(f"\n⚠️  Missing webhook URLs:")
            for webhook in missing:
                print(f"   • {webhook}")

        print(f"\nTotal configured: {len(configured)}/{len(all_possible_webhooks)}")


def main():
    """Main entry point."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        if os.path.exists(".env"):
            load_dotenv()
            print("📁 Loaded configuration from .env file")

        # Initialize tester
        tester = WebhookTester()

        # Check webhook configuration
        tester.check_webhook_availability()

        if not tester.webhook_urls:
            print("\n❌ No webhooks configured for testing")
            sys.exit(1)

        # Test all webhooks
        print("\n")
        success = tester.test_all_webhooks()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()