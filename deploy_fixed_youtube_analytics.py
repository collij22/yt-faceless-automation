#!/usr/bin/env python3
"""
Deploy the fixed YouTube Analytics workflow to n8n.
This script will update the existing workflow with the corrected version.
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

def load_workflow():
    """Load the corrected workflow from file."""
    workflow_file = Path("workflows/youtube_analytics_PRODUCTION.json")
    with open(workflow_file, 'r') as f:
        return json.load(f)

def find_existing_workflow():
    """Find the existing YouTube Analytics workflow in n8n."""
    try:
        headers = {"X-N8N-API-KEY": N8N_API_KEY} if N8N_API_KEY else {}
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows", headers=headers)
        
        if response.status_code == 200:
            workflows = response.json()
            for workflow in workflows:
                if workflow.get("name") == "YouTube Analytics Production":
                    return workflow["id"]
        
        return None
    except Exception as e:
        print(f"Error finding workflow: {e}")
        return None

def update_workflow(workflow_id, workflow_data):
    """Update the existing workflow in n8n."""
    try:
        headers = {
            "Content-Type": "application/json",
            "X-N8N-API-KEY": N8N_API_KEY
        } if N8N_API_KEY else {"Content-Type": "application/json"}
        
        response = requests.put(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
            json=workflow_data,
            headers=headers
        )
        
        return response.status_code == 200, response
    except Exception as e:
        print(f"Error updating workflow: {e}")
        return False, None

def create_workflow(workflow_data):
    """Create a new workflow in n8n."""
    try:
        headers = {
            "Content-Type": "application/json",
            "X-N8N-API-KEY": N8N_API_KEY
        } if N8N_API_KEY else {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows",
            json=workflow_data,
            headers=headers
        )
        
        return response.status_code == 201, response
    except Exception as e:
        print(f"Error creating workflow: {e}")
        return False, None

def activate_workflow(workflow_id):
    """Activate the workflow in n8n."""
    try:
        headers = {"X-N8N-API-KEY": N8N_API_KEY} if N8N_API_KEY else {}
        response = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/activate",
            headers=headers
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error activating workflow: {e}")
        return False

def test_webhook():
    """Test the webhook to see if it's working."""
    try:
        test_data = {"channel_id": "test"}
        response = requests.post(
            f"{N8N_BASE_URL}/webhook/youtube-analytics",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Webhook Test Results:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Length: {len(response.text)}")
        
        if response.text:
            try:
                json_resp = response.json()
                print(f"  Status: {json_resp.get('status', 'unknown')}")
                print(f"  Message: {json_resp.get('message', 'unknown')}")
                if 'debug_data_keys' in json_resp:
                    print(f"  Debug Data Keys: {json_resp['debug_data_keys']}")
                return True
            except:
                print(f"  Response: {response.text[:100]}...")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing webhook: {e}")
        return False

def main():
    """Deploy the fixed workflow."""
    print("🔧 YouTube Analytics Workflow - Fix Deployment")
    print("=" * 55)
    
    # Load corrected workflow
    print("📂 Loading corrected workflow...")
    workflow = load_workflow()
    print(f"✅ Loaded workflow with {len(workflow['nodes'])} nodes")
    
    # Check n8n connectivity
    print(f"\n🌐 Checking n8n connectivity ({N8N_BASE_URL})...")
    try:
        response = requests.get(f"{N8N_BASE_URL}/", timeout=5)
        print("✅ n8n is reachable")
    except:
        print("❌ Cannot reach n8n - make sure it's running")
        return False
    
    # Find existing workflow
    print("\n🔍 Looking for existing workflow...")
    existing_id = find_existing_workflow()
    
    if existing_id:
        print(f"✅ Found existing workflow (ID: {existing_id})")
        print("🔄 Updating workflow...")
        success, response = update_workflow(existing_id, workflow)
        
        if success:
            print("✅ Workflow updated successfully")
            workflow_id = existing_id
        else:
            print(f"❌ Failed to update workflow: {response.status_code if response else 'Unknown'}")
            return False
    else:
        print("⚠️  No existing workflow found, creating new one...")
        success, response = create_workflow(workflow)
        
        if success:
            workflow_id = response.json()["id"]
            print(f"✅ Workflow created successfully (ID: {workflow_id})")
        else:
            print(f"❌ Failed to create workflow: {response.status_code if response else 'Unknown'}")
            return False
    
    # Activate workflow
    print("\n🚀 Activating workflow...")
    if activate_workflow(workflow_id):
        print("✅ Workflow activated successfully")
    else:
        print("⚠️  Could not activate workflow - please check n8n UI")
    
    # Test the webhook
    print("\n🧪 Testing webhook functionality...")
    if test_webhook():
        print("✅ Webhook test passed - workflow is working!")
    else:
        print("⚠️  Webhook test had issues - check logs")
    
    print(f"\n📋 Next Steps:")
    print(f"  1. Visit {N8N_BASE_URL} to verify the workflow is active")
    print(f"  2. Test webhook: {N8N_BASE_URL}/webhook/youtube-analytics")
    print(f"  3. Check execution logs if issues persist")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)