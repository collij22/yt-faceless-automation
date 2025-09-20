#!/usr/bin/env python3
"""Test the FIXED YouTube Analytics workflow."""

import requests
import json

def test_original_vs_fixed():
    """Test both original and fixed endpoints to compare."""
    
    print("=" * 60)
    print("TESTING ORIGINAL vs FIXED YOUTUBE ANALYTICS WORKFLOW")
    print("=" * 60)
    
    endpoints = [
        {
            "name": "ORIGINAL (Broken)",
            "url": "http://localhost:5678/webhook/youtube-analytics",
            "expected": "Empty response (0 bytes)"
        },
        {
            "name": "FIXED VERSION", 
            "url": "http://localhost:5678/webhook/youtube-analytics-fixed",
            "expected": "Valid JSON response"
        }
    ]
    
    test_data = {"channel_id": "test_comparison"}
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']}")
        print("-" * 40)
        print(f"URL: {endpoint['url']}")
        print(f"Expected: {endpoint['expected']}")
        
        try:
            response = requests.post(
                endpoint['url'],
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)} bytes")
            
            if response.status_code == 200:
                if response.text:
                    try:
                        data = response.json()
                        print("Result: SUCCESS - Valid JSON response received!")
                        print(f"Status: {data.get('status')}")
                        print(f"Message: {data.get('message', '')[:80]}...")
                        
                        # Show fix confirmation if available
                        if 'debug_info' in data:
                            fix_applied = data['debug_info'].get('fix_applied')
                            if fix_applied:
                                print(f"Fix Applied: {fix_applied}")
                                
                    except json.JSONDecodeError:
                        print("Result: FAILED - Invalid JSON response")
                        print(f"Raw: {response.text[:100]}...")
                else:
                    print("Result: FAILED - Empty response body (this is the bug!)")
            else:
                print(f"Result: FAILED - HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("Result: ERROR - Cannot connect (workflow not deployed?)")
        except Exception as e:
            print(f"Result: ERROR - {e}")

def test_comprehensive_fixed():
    """Comprehensive test of the fixed workflow."""
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST OF FIXED WORKFLOW")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Basic Test",
            "data": {"channel_id": "test_basic"}
        },
        {
            "name": "With Demographics",
            "data": {
                "channel_id": "test_demo",
                "include_demographics": True,
                "include_traffic_sources": False
            }
        },
        {
            "name": "Full Parameters",
            "data": {
                "channel_id": "test_full",
                "date_range": "custom",
                "start_date": "2024-08-01",
                "end_date": "2024-09-01",
                "include_demographics": True,
                "include_traffic_sources": True
            }
        }
    ]
    
    fixed_url = "http://localhost:5678/webhook/youtube-analytics-fixed"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                fixed_url,
                json=test_case['data'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200 and response.text:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        print("✓ SUCCESS")
                        
                        # Verify expected data structure
                        checks = [
                            ('channel', 'channel' in data),
                            ('metrics', 'metrics' in data),
                            ('insights', 'insights' in data),
                        ]
                        
                        if test_case['data'].get('include_demographics', True):
                            checks.append(('demographics', data.get('demographics') is not None))
                        
                        if test_case['data'].get('include_traffic_sources', True):
                            checks.append(('traffic', data.get('traffic') is not None))
                        
                        for check_name, result in checks:
                            status = "✓" if result else "✗"
                            print(f"  {status} {check_name}")
                            
                    else:
                        print(f"✗ FAILED: {data.get('message', 'Unknown error')}")
                        
                except json.JSONDecodeError:
                    print("✗ FAILED: Invalid JSON")
            else:
                print(f"✗ FAILED: HTTP {response.status_code} or empty response")
                
        except Exception as e:
            print(f"✗ ERROR: {e}")

def main():
    """Run all tests."""
    print("YOUTUBE ANALYTICS WORKFLOW - FIX VERIFICATION")
    print("Testing both original (broken) and fixed versions")
    
    # Compare original vs fixed
    test_original_vs_fixed()
    
    # Comprehensive test of fixed version
    test_comprehensive_fixed()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("If the FIXED VERSION shows 'SUCCESS - Valid JSON response received!'")
    print("then the empty response bug has been resolved.")
    print("\nThe fix changes webhook responseMode from 'responseNode' to 'lastNode'")
    print("which is more reliable in n8n version 1.110.1")

if __name__ == "__main__":
    main()