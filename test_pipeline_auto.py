"""
Automated test of YouTube pipeline (no user input required)
"""

from run_youtube_pipeline import YouTubePipeline
import requests

def test_pipeline():
    """Run pipeline test automatically"""
    print("YouTube Automation Pipeline - Automated Test")
    print("=" * 60)

    # Check n8n
    try:
        response = requests.get("http://localhost:5678", timeout=5)
        print("[OK] n8n is running")
    except:
        print("[ERROR] n8n is not running")
        print("Please start n8n with: npx n8n start")
        return

    print("\nStarting automated pipeline test...")
    print("-" * 60)

    # Run pipeline
    pipeline = YouTubePipeline()
    result = pipeline.run_full_pipeline()

    if result:
        print("\n[SUCCESS] Pipeline test completed!")
        print(f"Results saved to: {pipeline.content_dir}")
        print("\nGenerated files:")
        for file in result["files_created"]:
            print(f"  - {file}")
    else:
        print("\n[FAILED] Pipeline test failed")
        print("Check logs for details")

if __name__ == "__main__":
    test_pipeline()