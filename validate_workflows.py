#!/usr/bin/env python3
"""
n8n Workflow Validation Script

This script validates the MCP workflow files for correctness before deployment.
It checks JSON structure, required fields, and node configurations.

Usage:
    python validate_workflows.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class WorkflowValidator:
    """Validates n8n workflow files."""

    def __init__(self):
        """Initialize the validator."""
        self.workflow_files = [
            "workflows/tts_webhook_mcp.json",
            "workflows/youtube_upload_mcp.json",
            "workflows/youtube_analytics_mcp.json",
            "workflows/cross_platform_mcp.json",
            "workflows/affiliate_shortener_mcp.json"
        ]

    def validate_workflow_structure(self, workflow_data: Dict) -> List[str]:
        """Validate the basic structure of a workflow."""
        errors = []

        # Required top-level fields
        required_fields = ["name", "nodes", "connections"]
        for field in required_fields:
            if field not in workflow_data:
                errors.append(f"Missing required field: {field}")

        # Validate name
        if "name" in workflow_data:
            if not isinstance(workflow_data["name"], str) or not workflow_data["name"].strip():
                errors.append("Workflow name must be a non-empty string")

        # Validate nodes
        if "nodes" in workflow_data:
            if not isinstance(workflow_data["nodes"], list):
                errors.append("Nodes must be a list")
            elif len(workflow_data["nodes"]) == 0:
                errors.append("Workflow must have at least one node")
            else:
                # Validate each node
                node_ids = set()
                for i, node in enumerate(workflow_data["nodes"]):
                    if not isinstance(node, dict):
                        errors.append(f"Node {i} must be an object")
                        continue

                    # Required node fields
                    node_required = ["id", "name", "type", "position"]
                    for field in node_required:
                        if field not in node:
                            errors.append(f"Node {i} missing required field: {field}")

                    # Check for duplicate node IDs
                    node_id = node.get("id")
                    if node_id:
                        if node_id in node_ids:
                            errors.append(f"Duplicate node ID: {node_id}")
                        node_ids.add(node_id)

        # Validate connections
        if "connections" in workflow_data:
            if not isinstance(workflow_data["connections"], dict):
                errors.append("Connections must be an object")
            else:
                # Validate connection structure
                for node_name, connections in workflow_data["connections"].items():
                    if not isinstance(connections, dict):
                        errors.append(f"Connections for '{node_name}' must be an object")
                        continue

                    for output_type, outputs in connections.items():
                        if not isinstance(outputs, list):
                            errors.append(f"Connection outputs for '{node_name}.{output_type}' must be a list")
                            continue

                        for output_group in outputs:
                            if not isinstance(output_group, list):
                                errors.append(f"Output group in '{node_name}.{output_type}' must be a list")
                                continue

                            for connection in output_group:
                                if not isinstance(connection, dict):
                                    errors.append(f"Connection in '{node_name}.{output_type}' must be an object")
                                    continue

                                conn_required = ["node", "type", "index"]
                                for field in conn_required:
                                    if field not in connection:
                                        errors.append(f"Connection missing required field: {field}")

        return errors

    def validate_webhook_nodes(self, workflow_data: Dict) -> List[str]:
        """Validate webhook-specific node configurations."""
        errors = []
        webhook_nodes = []

        # Find webhook nodes
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                webhook_nodes.append(node)

        if len(webhook_nodes) == 0:
            errors.append("No webhook trigger node found")
        elif len(webhook_nodes) > 1:
            errors.append("Multiple webhook trigger nodes found (should have only one)")
        else:
            # Validate webhook node configuration
            webhook_node = webhook_nodes[0]
            params = webhook_node.get("parameters", {})

            if "path" not in params:
                errors.append("Webhook node missing 'path' parameter")
            elif not params["path"]:
                errors.append("Webhook path cannot be empty")

            if params.get("httpMethod") != "POST":
                errors.append("Webhook should use POST method")

            if params.get("responseMode") != "responseNode":
                errors.append("Webhook should use responseNode mode")

        return errors

    def validate_response_nodes(self, workflow_data: Dict) -> List[str]:
        """Validate that workflows have proper response nodes."""
        errors = []
        response_nodes = []

        # Find response nodes
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.respondToWebhook":
                response_nodes.append(node)

        if len(response_nodes) == 0:
            errors.append("No 'Respond to Webhook' node found")
        elif len(response_nodes) > 1:
            errors.append("Multiple response nodes found (should have only one)")

        return errors

    def validate_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """Validate a single workflow file."""
        errors = []

        # Check file exists
        if not os.path.exists(filepath):
            return False, [f"File not found: {filepath}"]

        try:
            # Load and parse JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            # Validate structure
            errors.extend(self.validate_workflow_structure(workflow_data))

            # Validate webhook-specific requirements
            errors.extend(self.validate_webhook_nodes(workflow_data))

            # Validate response nodes
            errors.extend(self.validate_response_nodes(workflow_data))

            # Check for common issues
            workflow_name = workflow_data.get("name", "")
            if "MCP" not in workflow_name:
                errors.append("Workflow name should contain 'MCP' to indicate MCP version")

            if not workflow_data.get("active", True):
                errors.append("Workflow should be set to active by default")

            return len(errors) == 0, errors

        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def validate_all_workflows(self) -> bool:
        """Validate all workflow files."""
        print("Validating n8n workflow files...")
        print("=" * 50)

        total_files = len(self.workflow_files)
        valid_files = 0
        all_errors = []

        for filepath in self.workflow_files:
            print(f"\nValidating: {filepath}")

            is_valid, errors = self.validate_file(filepath)

            if is_valid:
                print("[VALID]")
                valid_files += 1
            else:
                print("[INVALID]")
                for error in errors:
                    print(f"   * {error}")
                all_errors.extend(errors)

        # Summary
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Total files: {total_files}")
        print(f"Valid files: {valid_files}")
        print(f"Invalid files: {total_files - valid_files}")
        print(f"Total errors: {len(all_errors)}")

        if valid_files == total_files:
            print("\nAll workflow files are valid!")
            print("Ready for deployment to n8n")
            return True
        else:
            print(f"\n{total_files - valid_files} files have validation errors")
            print("Fix errors before deployment")
            return False

    def check_workflow_files_exist(self) -> bool:
        """Check if all required workflow files exist."""
        print("Checking for workflow files...")

        missing_files = []
        existing_files = []

        for filepath in self.workflow_files:
            if os.path.exists(filepath):
                existing_files.append(filepath)
                print(f"[FOUND] {filepath}")
            else:
                missing_files.append(filepath)
                print(f"[MISSING] {filepath}")

        if missing_files:
            print(f"\n{len(missing_files)} workflow files are missing:")
            for filepath in missing_files:
                print(f"   * {filepath}")
            print("\nMake sure all MCP workflow files are present before validation.")
            return False

        print(f"\nAll {len(existing_files)} workflow files found")
        return True


def main():
    """Main entry point."""
    try:
        validator = WorkflowValidator()

        # First check if files exist
        if not validator.check_workflow_files_exist():
            sys.exit(1)

        # Then validate the files
        success = validator.validate_all_workflows()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nValidation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()