#!/usr/bin/env python3
"""
Test script to verify the YouTube Analytics workflow fix.
Run this after deploying the fixed workflow to n8n.
"""

import requests
import json
import time
from datetime import datetime

N8N_BASE_URL = "http://localhost:5678"
WEBHOOK_URL = f"{N8N_BASE_URL}/webhook/youtube-analytics"

def test_basic_functionality():
    """Test basic webhook functionality."""
    print("🧪 Testing Basic Functionality")
    print("-" * 40)
    
    test_data = {"channel_id": "test_channel"}
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            if response.text:
                try:
                    data = response.json()
                    print("✅ Received valid JSON response")
                    print(f"Status: {data.get('status', 'unknown')}")
                    print(f"Message: {data.get('message', 'unknown')}")
                    
                    if 'debug_data_keys' in data:
                        print(f"Debug Keys: {data['debug_data_keys']}")
                    
                    if data.get('status') == 'success':
                        print("✅ Workflow executing successfully")
                        return True
                    else:
                        print(f"⚠️  Workflow error: {data.get('message')}")
                        return False
                        
                except json.JSONDecodeError:
                    print("❌ Response is not valid JSON")
                    print(f"Raw response: {response.text[:200]}")
                    return False
            else:
                print("❌ Empty response body - fix not deployed yet")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to n8n - is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_parameters():
    """Test with various parameters to ensure workflow handles different inputs."""
    print("\n🧪 Testing with Different Parameters")
    print("-" * 45)
    
    test_cases = [
        {
            "name": "Minimal data",
            "data": {"channel_id": "UC_test"}
        },
        {
            "name": "With date range",
            "data": {
                "channel_id": "UC_test",
                "date_range": "last_7_days",
                "start_date": "2024-09-07",
                "end_date": "2024-09-14"
            }
        },
        {
            "name": "With demographics enabled",
            "data": {
                "channel_id": "UC_test",
                "include_demographics": True,
                "include_traffic_sources": False
            }
        },
        {
            "name": "Full parameters",
            "data": {
                "channel_id": "UC_test",
                "date_range": "custom",
                "start_date": "2024-08-01",
                "end_date": "2024-09-01",
                "include_demographics": True,
                "include_traffic_sources": True
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=test_case['data'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200 and response.text:
                try:
                    data = response.json()
                    success = data.get('status') == 'success'
                    print(f"  {'✅' if success else '❌'} {test_case['name']}")
                    
                    if success:
                        # Check for expected data structure
                        has_channel = 'channel' in data
                        has_metrics = 'metrics' in data
                        has_insights = 'insights' in data
                        
                        print(f"    Channel data: {'✅' if has_channel else '❌'}")
                        print(f"    Metrics data: {'✅' if has_metrics else '❌'}")
                        print(f"    Insights: {'✅' if has_insights else '❌'}")
                        
                        # Check conditional data
                        if test_case['data'].get('include_demographics', True):
                            has_demo = data.get('demographics') is not None
                            print(f"    Demographics: {'✅' if has_demo else '❌'}")
                        
                        if test_case['data'].get('include_traffic_sources', True):
                            has_traffic = data.get('traffic') is not None
                            print(f"    Traffic data: {'✅' if has_traffic else '❌'}")
                    
                    results.append(success)
                    
                except json.JSONDecodeError:
                    print(f"  ❌ Invalid JSON response")
                    results.append(False)
            else:
                print(f"  ❌ HTTP {response.status_code} or empty response")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append(False)
        
        time.sleep(0.5)  # Brief pause between tests
    
    return all(results)

def test_error_handling():
    """Test error handling with invalid data."""
    print("\n🧪 Testing Error Handling")
    print("-" * 30)
    
    error_test_cases = [
        {
            "name": "Empty request",
            "data": {}
        },
        {
            "name": "Invalid data types",
            "data": {
                "channel_id": 123,  # Should be string
                "include_demographics": "yes"  # Should be boolean
            }
        }
    ]
    
    for test_case in error_test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=test_case['data'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200 and response.text:
                try:
                    data = response.json()
                    print(f"  Status: {data.get('status', 'unknown')}")
                    if data.get('status') == 'error':
                        print("  ✅ Error properly handled")
                    else:
                        print("  ✅ Request processed successfully")
                        
                except json.JSONDecodeError:
                    print("  ❌ Invalid JSON response")
            else:
                print(f"  ❌ HTTP {response.status_code} or empty response")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Run all tests."""
    print("🚀 YouTube Analytics Workflow Fix - Test Suite")
    print("=" * 55)
    print(f"Testing webhook: {WEBHOOK_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test basic functionality
    basic_success = test_basic_functionality()
    
    if not basic_success:
        print("\n❌ Basic functionality test failed!")
        print("Please ensure the fixed workflow is deployed and active in n8n.")
        return False
    
    # Test with parameters
    param_success = test_with_parameters()
    
    # Test error handling
    test_error_handling()
    
    # Summary
    print("\n" + "=" * 55)
    print("TEST SUMMARY")
    print("=" * 55)
    
    if basic_success and param_success:
        print("✅ ALL TESTS PASSED!")
        print("The YouTube Analytics workflow is working correctly.")
        print("\nNext steps:")
        print("- Remove debug_data_keys from production if desired")
        print("- Monitor workflow performance")
        print("- The fix has resolved the empty response issue")
    else:
        print("⚠️  Some tests failed")
        print("Please check the workflow configuration and n8n logs")
    
    return basic_success and param_success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)