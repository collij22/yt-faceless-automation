#!/usr/bin/env python3
"""
Deploy the FIXED YouTube Analytics workflow to n8n.
This version uses responseMode: "lastNode" instead of "responseNode".
"""

import requests
import json
import sys
import time

N8N_BASE_URL = "http://localhost:5678"
N8N_API_URL = f"{N8N_BASE_URL}/api/v1"

def load_workflow():
    """Load the fixed workflow from file."""
    try:
        with open('workflows/youtube_analytics_FIXED.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading workflow: {e}")
        return None

def deploy_workflow():
    """Deploy the fixed workflow to n8n."""
    workflow_data = load_workflow()
    if not workflow_data:
        return False
    
    print("Deploying FIXED YouTube Analytics workflow...")
    print("Fix Applied: Changed responseMode from 'responseNode' to 'lastNode'")
    print("-" * 60)
    
    try:
        # First, check if workflow exists by name
        existing_workflows = requests.get(f"{N8N_API_URL}/workflows")
        if existing_workflows.status_code == 200:
            workflows = existing_workflows.json()
            for workflow in workflows.get('data', []):
                if workflow['name'] in ['YouTube Analytics Fixed', 'YouTube Analytics Production']:
                    print(f"Found existing workflow: {workflow['name']} (ID: {workflow['id']})")
                    
                    # Update existing workflow
                    update_url = f"{N8N_API_URL}/workflows/{workflow['id']}"
                    response = requests.put(
                        update_url,
                        json=workflow_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        print(f"Successfully updated workflow '{workflow['name']}'")
                        
                        # Activate the workflow
                        activate_url = f"{N8N_API_URL}/workflows/{workflow['id']}/activate"
                        activate_response = requests.post(activate_url)
                        
                        if activate_response.status_code == 200:
                            print("Workflow activated successfully")
                            return True
                        else:
                            print(f"Warning: Failed to activate workflow: {activate_response.status_code}")
                            return True  # Still count as success
                    else:
                        print(f"Failed to update workflow: {response.status_code}")
                        print(response.text)
                        continue
        
        # If no existing workflow, create new one
        response = requests.post(
            f"{N8N_API_URL}/workflows",
            json=workflow_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            workflow_info = response.json()
            workflow_id = workflow_info['id']
            print(f"Successfully created new workflow (ID: {workflow_id})")
            
            # Activate the new workflow
            activate_url = f"{N8N_API_URL}/workflows/{workflow_id}/activate"
            activate_response = requests.post(activate_url)
            
            if activate_response.status_code == 200:
                print("Workflow activated successfully")
            else:
                print(f"Warning: Failed to activate workflow: {activate_response.status_code}")
            
            return True
        else:
            print(f"Failed to create workflow: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to n8n. Is n8n running on localhost:5678?")
        return False
    except Exception as e:
        print(f"Error deploying workflow: {e}")
        return False

def test_fixed_webhook():
    """Test the fixed webhook endpoint."""
    print("\nTesting the FIXED webhook endpoint...")
    print("-" * 40)
    
    webhook_url = f"{N8N_BASE_URL}/webhook/youtube-analytics-fixed"
    test_data = {"channel_id": "test_fixed"}
    
    try:
        response = requests.post(
            webhook_url,
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
                    print("SUCCESS: Received valid JSON response!")
                    print(f"Status: {data.get('status')}")
                    print(f"Message: {data.get('message')}")
                    
                    if 'debug_info' in data:
                        print(f"Fix Applied: {data['debug_info']['fix_applied']}")
                    
                    print("FIX CONFIRMED: The empty response issue is resolved!")
                    return True
                except json.JSONDecodeError:
                    print("ERROR: Response is not valid JSON")
                    print(f"Raw response: {response.text[:200]}")
                    return False
            else:
                print("ERROR: Still getting empty response")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing webhook: {e}")
        return False

def main():
    """Main deployment function."""
    print("=== YouTube Analytics Workflow FIX DEPLOYMENT ===")
    print("Problem: HTTP 200 but empty response body (0 bytes)")
    print("Solution: Change responseMode from 'responseNode' to 'lastNode'")
    print("=" * 55)
    
    # Deploy the fixed workflow
    if not deploy_workflow():
        print("Deployment failed!")
        return False
    
    # Wait a moment for n8n to process
    print("Waiting 3 seconds for n8n to process...")
    time.sleep(3)
    
    # Test the fix
    if test_fixed_webhook():
        print("\n" + "=" * 55)
        print("SUCCESS: YOUTUBE ANALYTICS WORKFLOW IS NOW FIXED!")
        print("=" * 55)
        print("The empty response issue has been resolved.")
        print("New webhook URL: http://localhost:5678/webhook/youtube-analytics-fixed")
        print("\nRoot cause was: responseMode 'responseNode' not working properly")
        print("Solution applied: Changed to responseMode 'lastNode'")
        return True
    else:
        print("\n" + "=" * 55)
        print("DEPLOYMENT SUCCEEDED BUT TEST FAILED")
        print("=" * 55)
        print("Please check n8n logs and workflow configuration manually.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)