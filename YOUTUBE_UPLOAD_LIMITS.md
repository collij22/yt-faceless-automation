# YouTube Upload Limits & Quota Management

## Understanding YouTube Upload Limits

You've hit the "uploadLimitExceeded" error. Here's what you need to know:

### Daily Upload Limits

YouTube has different limits based on your channel status:

1. **New/Unverified Channels**:
   - 10-15 videos per day maximum
   - Must verify phone number to increase

2. **Verified Channels (No Strikes)**:
   - 20-50 videos per day
   - Depends on channel age and history

3. **Established Channels**:
   - 100+ videos per day
   - Based on good standing and history

### API Quota Limits

- **Daily Quota**: 10,000 units per day (resets at midnight Pacific Time)
- **Upload Cost**: 1,600 units per video upload
- **Theoretical Max**: ~6 videos per day via API

## How to Manage Your Limits

### 1. Check Your Current Status
```bash
python youtube_quota_manager.py
```
Select option 1 to see your quota info and limits.

### 2. Delete Unnecessary Videos

Since you're testing, you can delete private/test videos to free up space:

```bash
python youtube_quota_manager.py
```
Select option 3 to delete all private videos.

### 3. Wait for Reset

Upload limits reset daily at:
- **12:00 AM Pacific Time (PT)**
- **3:00 AM Eastern Time (ET)**
- **8:00 AM UTC**

## Best Practices to Avoid Limits

### For Development/Testing

1. **Use a Test Channel**: Create a separate channel for testing
2. **Delete Test Videos**: Remove private test uploads regularly
3. **Batch Uploads**: Plan your uploads for when quota resets
4. **Local Testing**: Test video creation without uploading:
   ```python
   # In run_full_production_pipeline.py, comment out phase 6
   # video_id = self.phase6_upload_to_youtube(video_file, metadata)
   ```

### For Production

1. **Schedule Uploads**: Space them throughout the day
2. **Verify Your Channel**: Increases limits significantly
3. **Build Channel History**: Consistent uploads increase future limits
4. **Use YouTube Studio**: Manual uploads don't count against API quota

## Immediate Solutions

### Option 1: Delete Private Videos
```bash
# Run the quota manager
python youtube_quota_manager.py

# Select option 3 to delete private videos
# This frees up your upload count
```

### Option 2: Skip Upload During Testing
```python
# Modify run_full_production_pipeline.py temporarily
# Change line asking "Proceed with upload?" default to 'no'
```

### Option 3: Wait for Reset
- Check current Pacific Time: https://time.is/PT
- Your quota resets at midnight PT
- Plan uploads accordingly

## Modify Pipeline for Testing

To avoid hitting limits during development, update the pipeline:

```python
# In run_full_production_pipeline.py, add this option:

def phase6_upload_to_youtube(self, video_file, metadata):
    """Phase 6: Upload to YouTube"""

    # Add testing mode check
    if os.getenv('TESTING_MODE', 'false').lower() == 'true':
        print("[TESTING MODE] Skipping upload to avoid quota limits")
        print(f"Video saved locally: {video_file}")
        return None

    # Rest of upload code...
```

Then set environment variable when testing:
```bash
set TESTING_MODE=true
python run_full_production_pipeline.py
```

## Monitor Your Usage

Track your uploads to avoid hitting limits:

1. **Keep a log** of daily uploads
2. **Set up alerts** before reaching limits
3. **Use the quota manager** regularly to check status

## Long-term Solutions

1. **Request Quota Increase**:
   - Go to Google Cloud Console
   - Request higher API quota (requires justification)

2. **Multiple Channels**:
   - Distribute uploads across channels
   - Different content types on different channels

3. **YouTube Partner Program**:
   - Join when eligible
   - Higher limits for partners

Remember: These limits are in place to prevent spam. As your channel grows and maintains good standing, limits automatically increase.