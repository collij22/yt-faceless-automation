#!/usr/bin/env python3
"""
Debug script to test the YouTube Analytics workflow webhook.
"""

import json
import requests
import sys
from typing import Dict, Any

def test_youtube_analytics_webhook(webhook_url: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test the YouTube Analytics webhook with test data."""
    
    print(f"Testing webhook: {webhook_url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make POST request to webhook
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Get response text first
        response_text = response.text
        print(f"Raw response text: {repr(response_text)}")
        print(f"Response text length: {len(response_text)}")
        
        if not response_text or response_text.strip() == "":
            return {
                "status": "error", 
                "message": "Empty response body",
                "http_status": response.status_code,
                "raw_response": response_text
            }
        
        try:
            # Try to parse as JSON
            response_data = response.json()
            return {
                "status": "success",
                "http_status": response.status_code,
                "data": response_data
            }
        except json.JSONDecodeError as e:
            return {
                "status": "json_decode_error",
                "message": f"Failed to decode JSON: {str(e)}",
                "http_status": response.status_code,
                "raw_response": response_text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "request_error",
            "message": f"Request failed: {str(e)}"
        }

def main():
    """Main test function."""
    
    # Test data - same as mentioned in the issue
    test_data = {"channel_id": "test"}
    
    # You'll need to replace this with your actual n8n webhook URL
    # The URL should look like: http://localhost:5678/webhook/youtube-analytics
    webhook_url = input("Enter the YouTube Analytics webhook URL: ").strip()
    
    if not webhook_url:
        print("No webhook URL provided. Exiting.")
        return
    
    print("=" * 60)
    print("YouTube Analytics Webhook Debug Test")
    print("=" * 60)
    
    result = test_youtube_analytics_webhook(webhook_url, test_data)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    
    # Analyze the results
    if result["status"] == "success":
        print("\n✅ Test PASSED - Webhook returned valid JSON")
        data = result["data"]
        if isinstance(data, dict) and "status" in data:
            print(f"Response status: {data.get('status')}")
            print(f"Response message: {data.get('message', 'N/A')}")
        else:
            print("⚠️  Response format is unexpected")
    else:
        print(f"\n❌ Test FAILED - {result['status']}")
        print(f"Issue: {result.get('message', 'Unknown error')}")
        
        if result.get("raw_response"):
            print("\nDebugging info:")
            raw = result["raw_response"]
            if raw == "":
                print("- Response is completely empty")
            elif raw.isspace():
                print("- Response contains only whitespace")
            else:
                print(f"- Response contains: {repr(raw)}")

if __name__ == "__main__":
    main()