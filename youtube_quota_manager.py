#!/usr/bin/env python
"""YouTube Quota Manager - Check limits and manage uploads"""

import os
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

class YouTubeQuotaManager:
    def __init__(self):
        self.youtube = self.get_youtube_client()

    def get_youtube_client(self):
        """Initialize YouTube API client"""
        creds = None

        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("[ERROR] credentials.json not found!")
                    print("Please set up YouTube API credentials first")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('youtube', 'v3', credentials=creds)

    def list_my_videos(self, max_results=50):
        """List uploaded videos"""
        try:
            request = self.youtube.channels().list(
                part="contentDetails",
                mine=True
            )
            response = request.execute()

            if not response['items']:
                print("No channel found")
                return []

            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get videos from uploads playlist
            videos = []
            next_page = None

            while True:
                playlist_request = self.youtube.playlistItems().list(
                    part="snippet,status",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page
                )
                playlist_response = playlist_request.execute()

                for item in playlist_response['items']:
                    videos.append({
                        'id': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title'],
                        'published': item['snippet']['publishedAt'],
                        'privacy': item.get('status', {}).get('privacyStatus', 'unknown')
                    })

                next_page = playlist_response.get('nextPageToken')
                if not next_page or len(videos) >= max_results:
                    break

            return videos[:max_results]
        except Exception as e:
            print(f"[ERROR] Failed to list videos: {e}")
            return []

    def delete_video(self, video_id):
        """Delete a video by ID"""
        try:
            request = self.youtube.videos().delete(id=video_id)
            request.execute()
            print(f"[SUCCESS] Deleted video: {video_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete video {video_id}: {e}")
            return False

    def delete_private_videos(self):
        """Delete all private videos to free up quota"""
        videos = self.list_my_videos()
        private_videos = [v for v in videos if v['privacy'] == 'private']

        if not private_videos:
            print("No private videos found")
            return

        print(f"\nFound {len(private_videos)} private videos:")
        for i, video in enumerate(private_videos, 1):
            print(f"{i}. {video['title'][:50]}... ({video['published'][:10]})")

        confirm = input(f"\nDelete all {len(private_videos)} private videos? (yes/no): ").lower()
        if confirm == 'yes':
            for video in private_videos:
                self.delete_video(video['id'])
            print(f"\n[COMPLETE] Deleted {len(private_videos)} private videos")
        else:
            print("Deletion cancelled")

    def check_quota_info(self):
        """Display quota information and limits"""
        print("\n" + "="*60)
        print("YOUTUBE API QUOTA INFORMATION")
        print("="*60)

        print("\nYouTube API Daily Quotas:")
        print("- Default quota: 10,000 units per day")
        print("- Video upload: 1,600 units per upload")
        print("- Video delete: 50 units per deletion")
        print("- List videos: 1 unit per request")

        print("\nUpload Limits by Channel Status:")
        print("- Unverified: 10-15 videos per day")
        print("- Verified (no strikes): 20-50 videos per day")
        print("- Verified (with history): 100+ videos per day")

        print("\nVideo Length Limits:")
        print("- Default: 15 minutes")
        print("- Verified account: 12 hours")
        print("- Live streaming: 12 hours")

        # Try to get channel info
        try:
            request = self.youtube.channels().list(
                part="statistics,status",
                mine=True
            )
            response = request.execute()

            if response['items']:
                stats = response['items'][0]['statistics']
                print(f"\nYour Channel Statistics:")
                print(f"- Total videos: {stats.get('videoCount', 'N/A')}")
                print(f"- Subscribers: {stats.get('subscriberCount', 'hidden')}")
                print(f"- Total views: {stats.get('viewCount', 'N/A')}")
        except Exception as e:
            print(f"\n[WARNING] Could not fetch channel statistics: {e}")

        videos = self.list_my_videos()
        if videos:
            print(f"\nRecent Uploads (Total: {len(videos)}):")
            for video in videos[:5]:
                print(f"- {video['title'][:50]}... ({video['privacy']}) - {video['published'][:10]}")

    def interactive_menu(self):
        """Interactive menu for quota management"""
        while True:
            print("\n" + "="*60)
            print("YOUTUBE QUOTA MANAGER")
            print("="*60)
            print("1. Check quota info and limits")
            print("2. List my uploaded videos")
            print("3. Delete all private videos")
            print("4. Delete specific video by ID")
            print("5. Exit")

            choice = input("\nSelect option (1-5): ").strip()

            if choice == '1':
                self.check_quota_info()
            elif choice == '2':
                videos = self.list_my_videos()
                print(f"\nFound {len(videos)} videos:")
                for i, video in enumerate(videos, 1):
                    print(f"{i}. [{video['privacy']}] {video['title'][:60]}...")
                    print(f"   ID: {video['id']}")
                    print(f"   Published: {video['published']}")
            elif choice == '3':
                self.delete_private_videos()
            elif choice == '4':
                video_id = input("Enter video ID to delete: ").strip()
                if video_id:
                    confirm = input(f"Delete video {video_id}? (yes/no): ").lower()
                    if confirm == 'yes':
                        self.delete_video(video_id)
            elif choice == '5':
                print("Exiting...")
                break
            else:
                print("Invalid option")

def main():
    manager = YouTubeQuotaManager()
    if manager.youtube:
        manager.interactive_menu()
    else:
        print("[ERROR] Failed to initialize YouTube client")
        print("\nTo set up YouTube API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable YouTube Data API v3")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download as 'credentials.json'")

if __name__ == "__main__":
    main()