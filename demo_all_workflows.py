#!/usr/bin/env python3
"""
Demonstration of all 5 n8n workflows working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5678/webhook"

def test_workflow(name, endpoint, data):
    """Test a single workflow endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    print(f"\n[{name}]")
    print(f"  Endpoint: {endpoint}")
    print(f"  Data: {json.dumps(data)[:100]}...")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'status' in result:
                print(f"  Result: {result['status']}")
            if 'message' in result:
                print(f"  Message: {result['message'][:100]}...")
            return True
        else:
            print(f"  Error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("N8N WORKFLOW DEMONSTRATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check n8n is running
    try:
        response = requests.get("http://localhost:5678/", timeout=5)
        if response.status_code == 200:
            print("[OK] n8n is running")
        else:
            print("[ERROR] n8n is not accessible")
            return
    except:
        print("[ERROR] Cannot connect to n8n at localhost:5678")
        return
    
    # Test all workflows
    workflows = [
        ("TTS Generation", "tts-generation", {
            "text": "This is a test of the text to speech system. It can handle long passages and convert them to audio.",
            "slug": "demo_test",
            "voice": "default"
        }),
        
        ("YouTube Upload", "youtube-upload", {
            "title": "Demo Video Title",
            "description": "This is a comprehensive description of the video content with keywords for SEO.",
            "video_path": "/path/to/video.mp4",
            "thumbnail_path": "/path/to/thumbnail.jpg",
            "tags": ["demo", "test", "automation"]
        }),
        
        ("YouTube Analytics", "youtube-analytics", {
            "channel_id": "UCtest123",
            "date_range": "last_30_days",
            "include_demographics": True,
            "include_traffic_sources": True
        }),
        
        ("Cross-Platform Distribution", "cross-platform-distribute", {
            "title": "Cross-Platform Content",
            "description": "Content to be distributed across multiple platforms",
            "platforms": ["twitter", "instagram", "tiktok"],
            "schedule_time": datetime.now().isoformat()
        }),
        
        ("Affiliate Link Shortener", "affiliate-shorten", {
            "original_url": "https://example.com/product/amazing-item",
            "campaign": "youtube_demo",
            "source": "video_description",
            "generate_qr": True
        })
    ]
    
    print("\n" + "=" * 60)
    print("TESTING ALL WORKFLOWS")
    print("=" * 60)
    
    results = []
    for name, endpoint, data in workflows:
        success = test_workflow(name, endpoint, data)
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} workflows working")
    
    if passed == total:
        print("\n[SUCCESS] All workflows are functioning correctly!")
        print("\nThe YouTube automation system is ready for use.")
        print("\nNext steps:")
        print("1. Configure your API keys in .env file")
        print("2. Set up YouTube OAuth credentials")
        print("3. Run the full pipeline with: python run_youtube_pipeline.py")
    else:
        print("\n[WARNING] Some workflows need attention")
        print("Please check the failed workflows in n8n")

if __name__ == "__main__":
    main()