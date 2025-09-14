#!/usr/bin/env python3
"""
n8n Workflow Deployment Script

This script deploys the MCP workflow files to n8n using the REST API.
It handles validation, deployment, activation, and testing of workflows.

Usage:
    python deploy_n8n_workflows.py

Requirements:
    - n8n instance running with API access
    - N8N_API_KEY and N8N_API_URL configured in .env
    - Workflow files in workflows/ directory
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class WorkflowDeployment:
    """Represents a workflow deployment result."""
    filename: str
    workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None


class N8nDeployer:
    """Handles deployment of workflows to n8n via REST API."""

    def __init__(self):
        """Initialize the deployer with environment configuration."""
        self.api_url = os.getenv("N8N_API_URL", "https://your-n8n-instance.com/api/v1")
        self.api_key = os.getenv("N8N_API_KEY")
        self.base_webhook_url = self.api_url.replace("/api/v1", "/webhook")

        if not self.api_key:
            raise ValueError("N8N_API_KEY environment variable is required")

        self.session = requests.Session()
        self.session.headers.update({
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        # Workflow files to deploy
        self.workflow_files = [
            "workflows/tts_webhook_mcp.json",
            "workflows/youtube_upload_mcp.json",
            "workflows/youtube_analytics_mcp.json",
            "workflows/cross_platform_mcp.json",
            "workflows/affiliate_shortener_mcp.json"
        ]

        self.deployments: List[WorkflowDeployment] = []

    def validate_api_connection(self) -> bool:
        """Validate connection to n8n API."""
        try:
            response = self.session.get(f"{self.api_url}/workflows")
            if response.status_code == 200:
                print("✅ Successfully connected to n8n API")
                return True
            else:
                print(f"❌ API connection failed: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            print(f"❌ API connection error: {e}")
            return False

    def list_existing_workflows(self) -> List[Dict]:
        """List all existing workflows in n8n."""
        try:
            response = self.session.get(f"{self.api_url}/workflows")
            response.raise_for_status()
            workflows = response.json().get("data", [])
            print(f"📋 Found {len(workflows)} existing workflows in n8n:")
            for wf in workflows:
                status = "Active" if wf.get("active", False) else "Inactive"
                print(f"  - {wf.get('name', 'Unnamed')} (ID: {wf.get('id')}) [{status}]")
            return workflows
        except requests.RequestException as e:
            print(f"❌ Failed to list workflows: {e}")
            return []

    def validate_workflow_file(self, filepath: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Validate a workflow file and return parsed JSON."""
        if not os.path.exists(filepath):
            return False, None, f"File not found: {filepath}"

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            # Basic validation
            required_fields = ["name", "nodes", "connections"]
            missing_fields = [field for field in required_fields if field not in workflow_data]
            if missing_fields:
                return False, None, f"Missing required fields: {', '.join(missing_fields)}"

            # Validate nodes structure
            if not isinstance(workflow_data["nodes"], list) or len(workflow_data["nodes"]) == 0:
                return False, None, "Workflow must have at least one node"

            # Check for webhook nodes and extract webhook info
            webhook_nodes = [node for node in workflow_data["nodes"]
                           if node.get("type") == "n8n-nodes-base.webhook"]

            if webhook_nodes:
                webhook_path = webhook_nodes[0].get("parameters", {}).get("path")
                if webhook_path:
                    webhook_url = f"{self.base_webhook_url}/{webhook_path}"
                    workflow_data["_webhook_url"] = webhook_url

            print(f"✅ Validated workflow: {workflow_data['name']}")
            return True, workflow_data, None

        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {e}"
        except Exception as e:
            return False, None, f"Validation error: {e}"

    def check_existing_workflow(self, workflow_name: str) -> Optional[str]:
        """Check if a workflow with the given name already exists."""
        try:
            response = self.session.get(f"{self.api_url}/workflows")
            response.raise_for_status()
            workflows = response.json().get("data", [])

            for workflow in workflows:
                if workflow.get("name") == workflow_name:
                    return workflow.get("id")
            return None
        except requests.RequestException as e:
            print(f"❌ Error checking existing workflows: {e}")
            return None

    def deploy_workflow(self, workflow_data: Dict, filepath: str) -> WorkflowDeployment:
        """Deploy a single workflow to n8n."""
        deployment = WorkflowDeployment(filename=filepath)
        workflow_name = workflow_data.get("name", "Unnamed Workflow")

        try:
            # Check if workflow already exists
            existing_id = self.check_existing_workflow(workflow_name)

            if existing_id:
                print(f"⚠️  Workflow '{workflow_name}' already exists (ID: {existing_id})")
                print("   Updating existing workflow...")

                # Update existing workflow
                response = self.session.patch(
                    f"{self.api_url}/workflows/{existing_id}",
                    json=workflow_data
                )
                deployment.workflow_id = existing_id
            else:
                print(f"📤 Creating new workflow: {workflow_name}")

                # Create new workflow
                response = self.session.post(
                    f"{self.api_url}/workflows",
                    json=workflow_data
                )

            response.raise_for_status()
            result = response.json()

            if not deployment.workflow_id:
                deployment.workflow_id = result.get("data", {}).get("id") or result.get("id")

            deployment.status = "deployed"
            deployment.webhook_url = workflow_data.get("_webhook_url")

            print(f"✅ Successfully deployed: {workflow_name} (ID: {deployment.workflow_id})")

        except requests.RequestException as e:
            deployment.status = "failed"
            deployment.error = f"Deployment failed: {e}"
            print(f"❌ Failed to deploy {workflow_name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response: {e.response.text}")

        return deployment

    def activate_workflow(self, workflow_id: str, workflow_name: str) -> bool:
        """Activate a workflow in n8n."""
        try:
            response = self.session.patch(
                f"{self.api_url}/workflows/{workflow_id}",
                json={"active": True}
            )
            response.raise_for_status()
            print(f"✅ Activated workflow: {workflow_name}")
            return True
        except requests.RequestException as e:
            print(f"❌ Failed to activate {workflow_name}: {e}")
            return False

    def test_webhook(self, webhook_url: str, workflow_name: str) -> bool:
        """Test a webhook endpoint with a simple GET request."""
        if not webhook_url:
            print(f"⚠️  No webhook URL found for {workflow_name}")
            return False

        try:
            # Test with GET request first (should return method not allowed but prove endpoint exists)
            response = requests.get(webhook_url, timeout=10)

            # For webhooks, we expect either 200 (if GET is supported) or 405 (method not allowed)
            if response.status_code in [200, 405]:
                print(f"✅ Webhook endpoint active: {webhook_url}")
                return True
            else:
                print(f"⚠️  Webhook test returned {response.status_code}: {webhook_url}")
                return False

        except requests.RequestException as e:
            print(f"❌ Webhook test failed for {workflow_name}: {e}")
            return False

    def deploy_all_workflows(self) -> bool:
        """Deploy all workflow files."""
        print("🚀 Starting n8n workflow deployment...")
        print("=" * 60)

        # Validate API connection
        if not self.validate_api_connection():
            return False

        # List existing workflows
        print("\n📋 Current workflows in n8n:")
        self.list_existing_workflows()

        print(f"\n📦 Deploying {len(self.workflow_files)} workflows...")
        print("-" * 60)

        success_count = 0

        for filepath in self.workflow_files:
            print(f"\n🔄 Processing: {filepath}")

            # Validate workflow file
            is_valid, workflow_data, error = self.validate_workflow_file(filepath)
            if not is_valid:
                deployment = WorkflowDeployment(
                    filename=filepath,
                    status="validation_failed",
                    error=error
                )
                self.deployments.append(deployment)
                print(f"❌ Validation failed: {error}")
                continue

            # Deploy workflow
            deployment = self.deploy_workflow(workflow_data, filepath)
            self.deployments.append(deployment)

            if deployment.status == "deployed" and deployment.workflow_id:
                # Activate workflow
                if self.activate_workflow(deployment.workflow_id, workflow_data["name"]):
                    success_count += 1

                    # Test webhook if available
                    if deployment.webhook_url:
                        self.test_webhook(deployment.webhook_url, workflow_data["name"])

        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT SUMMARY")
        print("=" * 60)

        for deployment in self.deployments:
            status_emoji = "✅" if deployment.status == "deployed" else "❌"
            print(f"{status_emoji} {deployment.filename}")
            if deployment.workflow_id:
                print(f"   ID: {deployment.workflow_id}")
            if deployment.webhook_url:
                print(f"   Webhook: {deployment.webhook_url}")
            if deployment.error:
                print(f"   Error: {deployment.error}")
            print()

        print(f"Successfully deployed: {success_count}/{len(self.workflow_files)} workflows")

        if success_count == len(self.workflow_files):
            print("\n🎉 All workflows deployed successfully!")
            self.print_webhook_urls()
            return True
        else:
            print(f"\n⚠️  {len(self.workflow_files) - success_count} workflows failed to deploy")
            return False

    def print_webhook_urls(self):
        """Print all webhook URLs for easy reference."""
        webhook_deployments = [d for d in self.deployments if d.webhook_url]

        if webhook_deployments:
            print("\n🔗 WEBHOOK ENDPOINTS")
            print("-" * 40)
            for deployment in webhook_deployments:
                workflow_name = deployment.filename.replace("workflows/", "").replace("_mcp.json", "")
                print(f"{workflow_name.upper()}_WEBHOOK_URL={deployment.webhook_url}")

        print("\n💡 TIP: Add these URLs to your .env file to use with the Python orchestrator")


def main():
    """Main entry point."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        if os.path.exists(".env"):
            load_dotenv()
            print("📁 Loaded configuration from .env file")
        else:
            print("⚠️  No .env file found. Make sure N8N_API_KEY and N8N_API_URL are set.")

        # Initialize deployer
        deployer = N8nDeployer()

        # Deploy all workflows
        success = deployer.deploy_all_workflows()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()