#!/usr/bin/env python3
"""
Test YouTube OAuth2 Setup
Verifies that OAuth2 is properly configured for YouTube uploads
"""

import os
import json
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube']

def authenticate_youtube():
    """Authenticate and return YouTube service object"""
    creds = None
    token_file = 'token.json'
    
    # Check if token.json exists (stored credentials)
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for credentials.json (downloaded from Google Cloud Console)
            if not os.path.exists('credentials.json'):
                print("\n" + "="*60)
                print("OAUTH2 SETUP REQUIRED")
                print("="*60)
                print("\n1. You need to download OAuth2 credentials from Google Cloud Console")
                print("2. Save the file as 'credentials.json' in this directory")
                print("3. Follow the setup guide in YOUTUBE_OAUTH2_SETUP_GUIDE.md")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    return build('youtube', 'v3', credentials=creds)

def test_youtube_connection(youtube):
    """Test the YouTube API connection"""
    try:
        # Get channel information
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            channel = response['items'][0]
            print("\n" + "="*60)
            print("YOUTUBE CHANNEL CONNECTED")
            print("="*60)
            print(f"Channel Name: {channel['snippet']['title']}")
            print(f"Channel ID: {channel['id']}")
            print(f"Subscribers: {channel['statistics'].get('subscriberCount', 'Hidden')}")
            print(f"Total Videos: {channel['statistics']['videoCount']}")
            print(f"Total Views: {channel['statistics']['viewCount']}")
            return True
        else:
            print("\n[ERROR] No channel found for this account")
            return False
            
    except HttpError as e:
        print(f"\n[ERROR] YouTube API error: {e}")
        return False

def check_upload_capability(youtube):
    """Check if we can upload videos"""
    try:
        # Check quota and permissions
        print("\n" + "="*60)
        print("UPLOAD CAPABILITY CHECK")
        print("="*60)
        
        # Get channel status
        request = youtube.channels().list(
            part="status",
            mine=True
        )
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            status = response['items'][0].get('status', {})
            
            # Check various upload-related statuses
            is_linked = status.get('isLinked', False)
            privacy_status = status.get('privacyStatus', 'private')
            
            print(f"Channel Linked: {is_linked}")
            print(f"Privacy Status: {privacy_status}")
            
            if not is_linked:
                print("\n[WARNING] Channel might not be properly linked")
                print("You may need to verify your YouTube account")
            
            print("\n[SUCCESS] Your account appears ready for uploads!")
            print("\nNote: YouTube has daily upload limits:")
            print("- Unverified accounts: Limited uploads")
            print("- Verified accounts: Higher limits")
            print("- API Quota: 10,000 units per day (each upload uses ~1600 units)")
            
            return True
        
    except HttpError as e:
        error_reason = json.loads(e.content).get('error', {}).get('message', str(e))
        print(f"\n[ERROR] Cannot check upload capability: {error_reason}")
        return False

def main():
    print("\n" + "="*60)
    print("YOUTUBE OAUTH2 TEST")
    print("="*60)
    
    # Check for API key in .env
    api_key = os.getenv('YOUTUBE_API_KEY')
    if api_key:
        print("[OK] YouTube API key found in .env")
    else:
        print("[WARNING] YOUTUBE_API_KEY not found in .env")
    
    # Authenticate with OAuth2
    print("\n[1/3] Authenticating with YouTube...")
    youtube = authenticate_youtube()
    
    if not youtube:
        print("\n[FAILED] Authentication failed")
        print("\nPlease follow these steps:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth2 credentials")
        print("3. Download as 'credentials.json'")
        print("4. Run this script again")
        return
    
    print("[OK] Authentication successful")
    
    # Test connection
    print("\n[2/3] Testing YouTube connection...")
    if not test_youtube_connection(youtube):
        print("[FAILED] Connection test failed")
        return
    
    # Check upload capability
    print("\n[3/3] Checking upload capability...")
    if not check_upload_capability(youtube):
        print("[WARNING] Upload capability check had issues")
    
    print("\n" + "="*60)
    print("OAUTH2 SETUP COMPLETE!")
    print("="*60)
    print("\nYou're ready to upload videos to YouTube!")
    print("\nNext steps:")
    print("1. Run: python youtube_production_upload.py")
    print("2. Select or create content")
    print("3. The video will be uploaded as PRIVATE initially")
    print("4. Review and publish from YouTube Studio")

if __name__ == "__main__":
    main()