# Setup n8n Workflows

## Step 1: Import Workflows

1. Open n8n in your browser: http://localhost:5678
2. Click on "Workflows" in the left sidebar
3. Click the "+" button or "Add workflow"
4. Click the three dots menu (⋮) in the top right
5. Select "Import from File"
6. Import each file from the `workflows` folder:
   - `tts_webhook_COMPLETE.json`
   - `youtube_upload_COMPLETE.json`
   - `youtube_analytics_COMPLETE.json`
   - `cross_platform_COMPLETE.json`
   - `affiliate_shortener_COMPLETE.json`

## Step 2: Activate Each Workflow

For EACH imported workflow:

1. Open the workflow
2. Click the toggle switch in the top right to **ACTIVATE** it (should turn green/blue)
3. You should see "Active" status
4. The webhook URL will be displayed - something like:
   - `http://localhost:5678/webhook/tts-generation`
   - `http://localhost:5678/webhook/youtube-upload`
   - etc.

## Step 3: Verify Webhooks Are Active

Run this test to check if webhooks are responding:

```bash
# Test if webhooks are registered (should not return 404)
curl http://localhost:5678/webhook/tts-generation
curl http://localhost:5678/webhook/youtube-upload
curl http://localhost:5678/webhook/youtube-analytics
curl http://localhost:5678/webhook/cross-platform-distribute
curl http://localhost:5678/webhook/affiliate-shorten
```

## Step 4: Run Tests

Once all workflows are ACTIVE, run:

```bash
python test_workflows.py
```

## Troubleshooting

### "Webhook not registered" Error
- Workflow is not activated - toggle the activation switch
- Workflow didn't import correctly - try re-importing
- n8n needs restart after importing workflows

### Check Active Workflows
In n8n, go to Workflows page and look for:
- Green/Blue status indicator = Active
- Gray status indicator = Inactive

### Manual Test Single Webhook
Test TTS webhook manually:
```bash
curl -X POST http://localhost:5678/webhook/tts-generation \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "slug": "test"}'
```

If this works, the workflow is active and ready.

## Alternative: Test in n8n UI

1. Open any workflow in n8n
2. Click "Execute Workflow" button
3. For webhook node, click "Listen for Test Event"
4. Send a test request using curl or the test script
5. You'll see the data flow through the workflow in real-time