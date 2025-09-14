#!/usr/bin/env python3
"""Check which webhooks are actually available in n8n."""

import requests

base_url = "http://localhost:5678"

# Test all possible webhook paths
webhooks_to_test = [
    "/webhook/tts-generation",
    "/webhook/youtube-upload",
    "/webhook/youtube-analytics",
    "/webhook/cross-platform-distribute",
    "/webhook/affiliate-shorten",
    "/webhook-test/tts-generation",
    "/webhook-test/youtube-upload",
    "/webhook-test/youtube-analytics",
    "/webhook-test/cross-platform-distribute",
    "/webhook-test/affiliate-shorten"
]

print("CHECKING N8N WEBHOOK ENDPOINTS")
print("=" * 50)

found_count = 0
for path in webhooks_to_test:
    url = base_url + path
    try:
        # Try both GET and POST
        post_response = requests.post(url, json={"test": True}, timeout=2)
        get_response = requests.get(url, timeout=2)

        if post_response.status_code != 404:
            print(f"FOUND: {path} (POST: {post_response.status_code})")
            found_count += 1
        elif get_response.status_code != 404:
            print(f"FOUND: {path} (GET: {get_response.status_code})")
            found_count += 1
        else:
            print(f"NOT FOUND: {path}")
    except Exception as e:
        print(f"ERROR: {path} - {str(e)[:50]}")

print("\n" + "=" * 50)
print(f"Total webhooks found: {found_count}")

if found_count == 0:
    print("\nNo webhooks found. Possible issues:")
    print("1. Workflows not activated")
    print("2. Workflows have import errors")
    print("3. Webhook nodes misconfigured")
    print("\nCheck the n8n UI for error messages in the workflows.")