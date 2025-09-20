#!/usr/bin/env python3
"""Deploy the fixed YouTube Analytics workflow to n8n."""

import json
import requests
import time
import sys
import os

N8N_BASE_URL = "http://localhost:5678"
WORKFLOW_FILE = "workflows/youtube_analytics_PRODUCTION.json"

def get_n8n_workflows():
    """Get all workflows from n8n."""
    try:
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows")
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Failed to get workflows: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting workflows: {e}")
        return []

def find_analytics_workflow(workflows):
    """Find the YouTube Analytics workflow."""
    for workflow in workflows:
        if 'analytics' in workflow.get('name', '').lower():
            return workflow
    return None

def update_workflow(workflow_id, workflow_data):
    """Update an existing workflow."""
    try:
        # Make sure the workflow is inactive before updating
        deactivate_response = requests.patch(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
            json={"active": False}
        )
        
        # Update the workflow
        response = requests.put(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
            json=workflow_data
        )
        
        if response.status_code == 200:
            print("Workflow updated successfully")
            
            # Activate the workflow
            activate_response = requests.patch(
                f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
                json={"active": True}
            )
            
            if activate_response.status_code == 200:
                print("Workflow activated successfully")
                return True
            else:
                print(f"Failed to activate workflow: {activate_response.status_code}")
                print(activate_response.text)
                return False
        else:
            print(f"Failed to update workflow: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error updating workflow: {e}")
        return False

def create_workflow(workflow_data):
    """Create a new workflow."""
    try:
        # Set active to false initially
        workflow_data['active'] = False
        
        response = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows",
            json=workflow_data
        )
        
        if response.status_code == 201:
            workflow_id = response.json()['data']['id']
            print(f"Workflow created with ID: {workflow_id}")
            
            # Activate the workflow
            activate_response = requests.patch(
                f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}",
                json={"active": True}
            )
            
            if activate_response.status_code == 200:
                print("Workflow activated successfully")
                return True
            else:
                print(f"Failed to activate workflow: {activate_response.status_code}")
                return False
        else:
            print(f"Failed to create workflow: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error creating workflow: {e}")
        return False

def main():
    """Main deployment function."""
    print("=" * 60)
    print("DEPLOYING FIXED YOUTUBE ANALYTICS WORKFLOW")
    print("=" * 60)
    
    # Check if n8n is running
    try:
        response = requests.get(N8N_BASE_URL)
        print(f"n8n is running at {N8N_BASE_URL}")
    except:
        print(f"ERROR: n8n is not running at {N8N_BASE_URL}")
        print("Please start n8n first: npx n8n")
        return False
    
    # Load the fixed workflow
    if not os.path.exists(WORKFLOW_FILE):
        print(f"ERROR: Workflow file not found: {WORKFLOW_FILE}")
        return False
    
    try:
        with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        print(f"Loaded workflow: {workflow_data['name']}")
    except Exception as e:
        print(f"ERROR: Failed to load workflow file: {e}")
        return False
    
    # Get existing workflows
    workflows = get_n8n_workflows()
    analytics_workflow = find_analytics_workflow(workflows)
    
    if analytics_workflow:
        print(f"Found existing workflow: {analytics_workflow['name']} (ID: {analytics_workflow['id']})")
        success = update_workflow(analytics_workflow['id'], workflow_data)
    else:
        print("No existing analytics workflow found, creating new one")
        success = create_workflow(workflow_data)
    
    if success:
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"Webhook URL: {N8N_BASE_URL}/webhook/youtube-analytics")
        print("You can now test the webhook")
        return True
    else:
        print("\n" + "=" * 60)
        print("DEPLOYMENT FAILED!")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)