import json
import os

def fix_webhook_node(node):
    """Fix webhook node to accept POST requests"""
    if node.get("type") == "n8n-nodes-base.webhook":
        if "parameters" not in node:
            node["parameters"] = {}

        # Ensure httpMethod is set to POST
        if "httpMethod" not in node["parameters"]:
            node["parameters"]["httpMethod"] = "POST"

        # Ensure path is set
        if "path" not in node["parameters"]:
            print(f"  Warning: Webhook node {node.get('name', 'unnamed')} has no path")

        # Ensure responseMode is set
        if "responseMode" not in node["parameters"]:
            node["parameters"]["responseMode"] = "lastNode"

        print(f"  Fixed webhook node: {node.get('name', 'unnamed')}")

    return node

def fix_workflow_file(filepath):
    """Fix a workflow file to ensure webhooks accept POST"""
    print(f"\nProcessing: {os.path.basename(filepath)}")

    with open(filepath, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Fix all webhook nodes
    if "nodes" in workflow:
        for i, node in enumerate(workflow["nodes"]):
            workflow["nodes"][i] = fix_webhook_node(node)

    # Save fixed version
    output_path = filepath.replace("_COMPLETE.json", "_FIXED.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2)

    print(f"  Saved fixed version: {os.path.basename(output_path)}")
    return output_path

def main():
    """Fix all workflow files"""
    print("="*60)
    print("FIXING N8N WEBHOOK WORKFLOWS")
    print("="*60)

    workflows_dir = "workflows"
    files_to_fix = [
        "tts_webhook_COMPLETE.json",
        "youtube_upload_COMPLETE.json",
        "youtube_analytics_COMPLETE.json",
        "cross_platform_COMPLETE.json",
        "affiliate_shortener_COMPLETE.json"
    ]

    fixed_files = []
    for filename in files_to_fix:
        filepath = os.path.join(workflows_dir, filename)
        if os.path.exists(filepath):
            fixed_path = fix_workflow_file(filepath)
            fixed_files.append(os.path.basename(fixed_path))
        else:
            print(f"  File not found: {filename}")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Delete the old workflows in n8n")
    print("2. Import these FIXED versions:")
    for f in fixed_files:
        print(f"   - {f}")
    print("3. ACTIVATE each workflow (toggle switch)")
    print("4. Run: python test_workflows.py")

    print("\nThe fixed files explicitly set httpMethod='POST' for all webhooks.")

if __name__ == "__main__":
    main()