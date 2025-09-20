"""
Fix boolean values in workflow JSON files
"""

import json
import os
from pathlib import Path

def fix_workflow_file(filepath):
    """Fix boolean values in a workflow file"""
    print(f"Fixing: {filepath.name}")

    # Read the file as text
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace Python booleans with JSON booleans
    content = content.replace(': false', ': false')
    content = content.replace(': true', ': true')
    content = content.replace(': False', ': false')
    content = content.replace(': True', ': true')

    # Parse to validate JSON
    try:
        workflow = json.loads(content)
        # Save back with proper JSON formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        print(f"  [OK] Fixed and validated")
        return True
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Invalid JSON: {e}")
        return False

def main():
    print("Fixing Boolean Values in Workflow Files")
    print("="*60)

    workflows_dir = Path("workflows")
    production_files = list(workflows_dir.glob("*_PRODUCTION.json"))

    if not production_files:
        print("No PRODUCTION workflow files found!")
        return

    print(f"Found {len(production_files)} production workflow files\n")

    success_count = 0
    for filepath in production_files:
        if fix_workflow_file(filepath):
            success_count += 1

    print("\n" + "="*60)
    print(f"Result: {success_count}/{len(production_files)} files fixed")

    if success_count == len(production_files):
        print("\n[SUCCESS] All workflow files fixed!")
        print("\nNext steps:")
        print("1. Delete all workflows in n8n")
        print("2. Re-import the PRODUCTION workflows")
        print("3. Activate each workflow")
        print("4. Run: python test_workflows_final.py")
    else:
        print("\n[WARNING] Some files had issues. Check the errors above.")

if __name__ == "__main__":
    main()