#!/usr/bin/env python
"""Check YouTube upload status and limits"""

from youtube_quota_manager import YouTubeQuotaManager
import sys

def main():
    print("\n" + "="*60)
    print("CHECKING YOUTUBE STATUS")
    print("="*60)

    manager = YouTubeQuotaManager()

    if not manager.youtube:
        print("[ERROR] Failed to connect to YouTube API")
        return

    # Show quota info
    manager.check_quota_info()

    # List videos
    videos = manager.list_my_videos(20)

    if videos:
        private_count = sum(1 for v in videos if v['privacy'] == 'private')
        public_count = sum(1 for v in videos if v['privacy'] == 'public')
        unlisted_count = sum(1 for v in videos if v['privacy'] == 'unlisted')

        print(f"\n" + "="*60)
        print("VIDEO SUMMARY")
        print("="*60)
        print(f"Total videos found: {len(videos)}")
        print(f"- Private: {private_count}")
        print(f"- Public: {public_count}")
        print(f"- Unlisted: {unlisted_count}")

        if private_count > 0:
            print(f"\n[TIP] You have {private_count} private videos")
            print("You can delete these test videos to free up upload capacity")
            print("Run: python youtube_quota_manager.py")
            print("Then select option 3 to delete private videos")

    print("\n" + "="*60)
    print("SOLUTIONS TO UPLOAD LIMIT")
    print("="*60)
    print("1. Wait until midnight PT for quota reset (daily limit resets)")
    print("2. Delete test/private videos to free up space")
    print("3. For testing, skip upload phase:")
    print("   set TESTING_MODE=true")
    print("   python run_full_production_pipeline.py")
    print("4. Verify your channel (increases limits)")
    print("5. Use YouTube Studio for manual upload (no API quota)")

if __name__ == "__main__":
    main()