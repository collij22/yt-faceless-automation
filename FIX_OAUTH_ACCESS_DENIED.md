# Fix OAuth "Access Blocked" Error

## The Issue
Your OAuth app is in testing mode (which is normal) but your email isn't added as a test user.

## Quick Fix Steps

### 1. Go to Google Cloud Console
- Open: https://console.cloud.google.com/
- Make sure you're in your "YouTube-Automation" project

### 2. Navigate to OAuth Consent Screen
- Click "APIs & Services" in the left menu
- Click "OAuth consent screen"

### 3. Add Test Users
- Scroll down to "Test users" section
- Click "+ ADD USERS"
- Enter your email: jon.l.collins@gmail.com
- Click "ADD"
- Click "SAVE" at the bottom

### 4. Verify Settings
While you're there, also check:
- Publishing status: Should show "Testing"
- User type: External
- Test users: Should list jon.l.collins@gmail.com

### 5. Important Note About Scopes
Make sure these scopes are added:
- ../auth/youtube.upload
- ../auth/youtube
- ../auth/youtubepartner (optional)

### 6. Try Again
After adding yourself as a test user:
```bash
python test_youtube_oauth.py
```

## Alternative: If Still Having Issues

### Option 1: Create New OAuth Client (Desktop Type)
Sometimes "Web application" OAuth clients have redirect issues. Try:
1. Go to "Credentials"
2. Create new OAuth client ID
3. Choose "Desktop app" (not Web application)
4. Download the JSON
5. Save as credentials.json

### Option 2: Check App Publishing Status
- If your app shows "In production" instead of "Testing", you need Google verification
- For personal use, keep it in "Testing" mode
- Testing mode allows up to 100 test users

## Why This Happens
Google requires explicit permission for testing OAuth apps to prevent abuse. Apps in testing mode can only be used by:
- The developer (owner of the project)
- Explicitly added test users
- Up to 100 users total

## No Verification Needed
For personal YouTube automation:
- Keep the app in "Testing" mode
- No need for Google verification (that's for public apps)
- Testing mode works perfectly for personal use
- Refresh tokens don't expire in testing mode (they do in production without verification)