#!/usr/bin/env python
"""Delete test videos to free up upload capacity"""

from youtube_quota_manager import YouTubeQuotaManager

def main():
    print("\n" + "="*60)
    print("DELETE TEST VIDEOS")
    print("="*60)

    manager = YouTubeQuotaManager()

    if not manager.youtube:
        print("[ERROR] Failed to connect to YouTube API")
        return

    # Get all videos
    videos = manager.list_my_videos(50)
    private_videos = [v for v in videos if v['privacy'] == 'private']

    if not private_videos:
        print("No private videos found to delete")
        return

    print(f"\nFound {len(private_videos)} private test videos:")
    for i, video in enumerate(private_videos, 1):
        print(f"{i}. {video['title'][:60]}...")
        print(f"   Uploaded: {video['published'][:10]}")

    print("\n" + "="*60)
    print("OPTIONS:")
    print("1. Delete ALL private videos")
    print("2. Delete only today's videos")
    print("3. Keep newest 2, delete rest")
    print("4. Cancel")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == '1':
        print(f"\nDeleting all {len(private_videos)} private videos...")
        for video in private_videos:
            manager.delete_video(video['id'])
        print(f"\n[SUCCESS] Deleted {len(private_videos)} videos")
        print("You can now upload new videos!")

    elif choice == '2':
        from datetime import datetime
        today = datetime.now().strftime('%Y-%09-%20')
        todays_videos = [v for v in private_videos if v['published'].startswith(today)]
        if todays_videos:
            print(f"\nDeleting {len(todays_videos)} videos from today...")
            for video in todays_videos:
                manager.delete_video(video['id'])
            print(f"\n[SUCCESS] Deleted {len(todays_videos)} videos")
        else:
            print("No videos from today found")

    elif choice == '3':
        if len(private_videos) > 2:
            to_delete = private_videos[2:]  # Keep first 2 (newest)
            print(f"\nDeleting {len(to_delete)} older videos...")
            for video in to_delete:
                manager.delete_video(video['id'])
            print(f"\n[SUCCESS] Deleted {len(to_delete)} videos")
            print(f"Kept the 2 newest videos")
        else:
            print("You have 2 or fewer videos, nothing to delete")

    else:
        print("Cancelled - no videos deleted")

if __name__ == "__main__":
    main()