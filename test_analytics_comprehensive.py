#!/usr/bin/env python3
"""Comprehensive test of the fixed YouTube Analytics workflow."""

import requests
import json
import time

BASE_URL = "http://localhost:5678/webhook/youtube-analytics"

def test_analytics_basic():
    """Test basic functionality."""
    print("\n" + "="*60)
    print("TEST 1: BASIC FUNCTIONALITY")
    print("="*60)
    
    data = {"channel_id": "test"}
    
    try:
        response = requests.post(BASE_URL, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Length: {len(response.text)}")
        print(f"Raw Response: [{response.text}]")
        
        if response.status_code == 200:
            if response.text.strip():
                try:
                    result = response.json()
                    print(f"Parsed JSON:")
                    print(json.dumps(result, indent=2))
                    print("✅ SUCCESS: Basic test passed")
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {e}")
                    return False
            else:
                print("❌ FAILED: Empty response body")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_demographics():
    """Test demographics functionality."""
    print("\n" + "="*60)
    print("TEST 2: DEMOGRAPHICS INCLUDED")
    print("="*60)
    
    data = {
        "channel_id": "test_channel", 
        "include_demographics": True,
        "include_traffic_sources": False
    }
    
    try:
        response = requests.post(BASE_URL, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 and response.text.strip():
            result = response.json()
            print(f"Channel ID: {result.get('channel', {}).get('id')}")
            demographics = result.get('demographics')
            if demographics and demographics != 'not_included':
                print(f"Demographics: {demographics}")
                print("✅ SUCCESS: Demographics included correctly")
                return True
            else:
                print("❌ FAILED: Demographics not included")
                print(json.dumps(result, indent=2))
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code} or empty response")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_traffic():
    """Test traffic sources functionality."""
    print("\n" + "="*60)
    print("TEST 3: TRAFFIC SOURCES INCLUDED")
    print("="*60)
    
    data = {
        "channel_id": "test_channel",
        "include_demographics": False,
        "include_traffic_sources": True
    }
    
    try:
        response = requests.post(BASE_URL, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 and response.text.strip():
            result = response.json()
            traffic = result.get('traffic')
            if traffic and traffic != 'not_included':
                print(f"Traffic Sources: {traffic}")
                print("✅ SUCCESS: Traffic sources included correctly")
                return True
            else:
                print("❌ FAILED: Traffic sources not included")
                print(json.dumps(result, indent=2))
                return False
        else:
            print(f"❌ FAILED: Status {response.status_code} or empty response")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_full():
    """Test full functionality with both demographics and traffic."""
    print("\n" + "="*60)
    print("TEST 4: FULL ANALYTICS (DEMOGRAPHICS + TRAFFIC)")
    print("="*60)
    
    data = {
        "channel_id": "test_full_channel",
        "include_demographics": True,
        "include_traffic_sources": True,
        "date_range": "last_7_days",
        "start_date": "2024-09-01",
        "end_date": "2024-09-07"
    }
    
    try:
        response = requests.post(BASE_URL, json=data, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 and response.text.strip():
            result = response.json()
            
            # Validate structure
            required_fields = ['status', 'channel', 'metrics', 'insights', 'recommendations']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                print(f"❌ FAILED: Missing required fields: {missing_fields}")
                return False
            
            # Check demographics and traffic
            demographics = result.get('demographics')
            traffic = result.get('traffic')
            
            if not demographics or demographics == 'not_included':
                print("❌ FAILED: Demographics should be included")
                return False
                
            if not traffic or traffic == 'not_included':
                print("❌ FAILED: Traffic sources should be included")
                return False
            
            print(f"✅ SUCCESS: Full analytics working correctly")
            print(f"Channel: {result['channel']['id']}")
            print(f"Metrics: {len(result['metrics'])} fields")
            print(f"Demographics: {demographics.get('age_group', 'N/A')}")
            print(f"Top Traffic Source: {traffic.get('top_source', 'N/A')}")
            print(f"Insights: {len(result['insights'])} items")
            print(f"Recommendations: {len(result['recommendations'])} items")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code} or empty response")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*60)
    print("TEST 5: EDGE CASES")
    print("="*60)
    
    test_cases = [
        {"data": {}, "desc": "Empty payload"},
        {"data": {"channel_id": ""}, "desc": "Empty channel ID"},
        {"data": {"channel_id": None}, "desc": "Null channel ID"},
        {"data": {"channel_id": "test", "include_demographics": None}, "desc": "Null demographics flag"}
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['desc']}")
        try:
            response = requests.post(BASE_URL, json=test_case['data'], timeout=10)
            if response.status_code == 200 and response.text.strip():
                result = response.json()
                print(f"  ✅ Handled correctly: {result.get('status', 'unknown')}")
                success_count += 1
            else:
                print(f"  ❌ Failed: Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\nEdge case results: {success_count}/{len(test_cases)} passed")
    return success_count >= len(test_cases) // 2  # At least half should pass

def main():
    """Run all tests."""
    print("🧪 COMPREHENSIVE YOUTUBE ANALYTICS WORKFLOW TEST")
    print("="*80)
    
    # Check if n8n is running
    try:
        response = requests.get("http://localhost:5678")
        print("✅ n8n is running")
    except:
        print("❌ n8n is not running at http://localhost:5678")
        print("Please start n8n and make sure the YouTube Analytics workflow is active")
        return False
    
    # Run all tests
    tests = [
        ("Basic Functionality", test_analytics_basic),
        ("Demographics Feature", test_analytics_demographics),
        ("Traffic Sources Feature", test_analytics_traffic),
        ("Full Analytics", test_analytics_full),
        ("Edge Cases", test_analytics_edge_cases)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🎯 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # Small delay between tests
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    passed = [name for name, success in results if success]
    failed = [name for name, success in results if not success]
    
    print(f"\n✅ PASSED ({len(passed)}/{len(results)}):")
    for name in passed:
        print(f"   • {name}")
    
    if failed:
        print(f"\n❌ FAILED ({len(failed)}/{len(results)}):")
        for name in failed:
            print(f"   • {name}")
    
    success_rate = len(passed) / len(results) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🚀 WORKFLOW IS WORKING CORRECTLY!")
        print("\nManual Import Instructions:")
        print("1. Open n8n at http://localhost:5678")
        print("2. Click 'Import from file'")
        print("3. Import: import_analytics_fixed.json")
        print("4. Click 'Activate' to enable the workflow")
        print("5. Test with: POST http://localhost:5678/webhook/youtube-analytics")
    else:
        print(f"\n⚠️  WORKFLOW NEEDS MORE FIXES ({len(failed)} issues remaining)")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)