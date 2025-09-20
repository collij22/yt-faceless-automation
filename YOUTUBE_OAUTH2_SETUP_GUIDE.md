# YouTube OAuth2 Setup Guide - Complete Steps

## Part 1: Google Cloud Console Setup (10-15 minutes)

### Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with the Google account that owns your YouTube channel
3. Click the project dropdown at the top
4. Click "New Project" or select an existing one
5. Name it something like "YouTube-Automation"

### Step 2: Enable YouTube Data API v3

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "ENABLE"
4. Wait for it to activate (usually instant)

### Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" (unless you have Google Workspace)
   - Fill in required fields:
     - App name: "YouTube Automation"
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes:
     - Click "ADD OR REMOVE SCOPES"
     - Search and add: 
       - `https://www.googleapis.com/auth/youtube.upload`
       - `https://www.googleapis.com/auth/youtube`
       - `https://www.googleapis.com/auth/youtubepartner`
   - Add your email as a test user
   - Save and continue

4. Now create the OAuth client:
   - Application type: "Web application"
   - Name: "n8n YouTube Integration"
   - Authorized redirect URIs - ADD THIS EXACTLY:
     ```
     http://localhost:5678/rest/oauth2-credential/callback
     ```
   - Click "CREATE"

5. **SAVE YOUR CREDENTIALS:**
   - Client ID: `YOUR_CLIENT_ID.apps.googleusercontent.com`
   - Client Secret: `YOUR_CLIENT_SECRET`
   - Download the JSON file for backup

## Part 2: n8n OAuth2 Configuration (5 minutes)

### Step 1: Open n8n Credentials

1. Open n8n at http://localhost:5678
2. Go to "Credentials" (left sidebar)
3. Click "Add Credential"
4. Search for "Google OAuth2 API"
5. Click to create new credential

### Step 2: Configure Google OAuth2 in n8n

Fill in these fields:
- **Credential Name**: "YouTube OAuth2"
- **Client ID**: (paste from Google Cloud Console)
- **Client Secret**: (paste from Google Cloud Console)
- **Scopes**: 
  ```
  https://www.googleapis.com/auth/youtube.upload
  https://www.googleapis.com/auth/youtube
  ```
- **Auth URI**: Leave default
- **Access Token URL**: Leave default
- **Authentication**: OAuth2

### Step 3: Authorize the Connection

1. Click "Sign in with Google" button in n8n
2. Choose your Google account
3. Review permissions and click "Continue"
4. You'll see "Account connected"
5. Click "Save" to save the credential

## Part 3: Update YouTube Upload Workflow

Since our workflow removes OAuth nodes, we need a different approach. The YouTube upload will be handled via the Python script using the API key for metadata and OAuth for actual upload.

## Part 4: Test Upload Setup

Let me create a test script to verify everything is configured correctly.