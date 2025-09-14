#!/usr/bin/env python3
"""Quick verification that n8n workflows are properly set up."""

import requests
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("N8N WORKFLOW VERIFICATION")
print("=" * 50)

# Test simple webhook
test_url = "http://localhost:5678/webhook/tts-generation"
test_data = {"text": "test", "slug": "test"}

try:
    response = requests.post(test_url, json=test_data, timeout=5)

    if response.status_code == 200:
        if response.text and response.text.strip():
            try:
                data = response.json()
                print("✅ SUCCESS! Workflows are responding with data")
                print(f"Sample response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print("⚠️ Response received but not valid JSON")
        else:
            print("❌ EMPTY RESPONSE - Workflows need to be re-imported")
            print("\nACTION REQUIRED:")
            print("1. Delete old workflows from n8n")
            print("2. Import the fixed workflow files")
            print("3. Activate each workflow")
    else:
        print(f"❌ Error: Status code {response.status_code}")

except Exception as e:
    print(f"❌ Connection error: {e}")

print("\nFor detailed instructions, see above.")