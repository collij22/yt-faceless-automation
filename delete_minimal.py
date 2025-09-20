import os
import glob

minimal_files = glob.glob("workflows/*_MINIMAL.json")
for file in minimal_files:
    os.remove(file)
    print(f"Deleted: {file}")

print("\nRemaining workflow files:")
for file in glob.glob("workflows/*.json"):
    print(f"  {file}")