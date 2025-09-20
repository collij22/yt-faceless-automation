import requests
import json

url = "http://localhost:5678/webhook/youtube-analytics"
data = {"channel_id": "test"}

print("Testing YouTube Analytics webhook...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

response = requests.post(url, json=data)

print(f"\n--- Response Details ---")
print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
print(f"Content Length: {len(response.content)} bytes")
print(f"Raw Content: {repr(response.content)}")

if response.content:
    try:
        json_data = response.json()
        print(f"\n--- JSON Response ---")
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError as e:
        print(f"\n--- JSON Parse Error ---")
        print(f"Error: {e}")
        print(f"Response text: '{response.text}'")
else:
    print("\n--- Empty Response ---")
    print("The server returned an empty response body")

print("\n--- Diagnosis ---")
if response.status_code == 200 and not response.content:
    print("✗ The workflow is returning HTTP 200 but with empty body")
    print("  This means the workflow in n8n is not properly configured")
    print("  The webhook_response node is likely not receiving data")
    print("\nSOLUTION:")
    print("1. Delete the YouTube Analytics Production workflow in n8n")
    print("2. Import workflows/youtube_analytics_PRODUCTION.json")
    print("3. Activate the workflow")
    print("4. Test again")