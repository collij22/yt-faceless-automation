#!/usr/bin/env python3
"""Simple test for YouTube Analytics workflow without Unicode."""

import requests
import json

N8N_BASE_URL = "http://localhost:5678"
WEBHOOK_URL = f"{N8N_BASE_URL}/webhook/youtube-analytics"

def test_analytics_workflow():
    """Test the analytics workflow."""
    print("Testing YouTube Analytics Workflow")
    print("-" * 40)
    
    test_data = {"channel_id": "test"}
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.text:
            print(f"Raw Response (first 500 chars): {response.text[:500]}")
            try:
                data = response.json()
                print("JSON Response parsed successfully")
                print(f"Response status: {data.get('status', 'unknown')}")
                return True
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                print(f"Raw response: {repr(response.text)}")
                return False
        else:
            print("EMPTY RESPONSE BODY - This is the issue!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to n8n - is it running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_analytics_workflow()