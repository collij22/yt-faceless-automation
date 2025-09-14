# n8n MCP Workflows - Deployment & Fix Guide

## 🚨 DIAGNOSIS SUMMARY

After comprehensive testing, the root cause of workflow failures has been identified:

### Issues Found:
1. ✅ **FIXED**: All MCP workflows had `"active": false` - now set to `"active": true`
2. ✅ **FIXED**: JSON syntax error in `youtube_upload_mcp.json` - extra braces removed
3. ❌ **REQUIRES MANUAL ACTION**: Workflows exist as files but are NOT imported into n8n instance
4. ❌ **REQUIRES MANUAL ACTION**: n8n is returning empty responses because workflows aren't loaded

### Current Status:
- **n8n Server**: ✅ Running on http://localhost:5678
- **Webhook Endpoints**: ✅ Responding (but empty - workflows not loaded)
- **Workflow Files**: ✅ All 5 MCP workflows are valid JSON with correct structure
- **Workflow Import**: ❌ Manual import required

---

## 📋 AVAILABLE WORKFLOWS

The following MCP workflows are ready for import:

### 1. TTS Generation Webhook (MCP)
- **File**: `workflows/tts_webhook_mcp.json`
- **Webhook Path**: `/webhook/tts-generation`
- **Status**: Ready for import
- **Features**: ElevenLabs & Google TTS, chunking, file saving

### 2. YouTube Upload Webhook (MCP)
- **File**: `workflows/youtube_upload_mcp.json`
- **Webhook Path**: `/webhook/youtube-upload`
- **Status**: Ready for import
- **Features**: Metadata validation, upload simulation

### 3. YouTube Analytics MCP
- **File**: `workflows/youtube_analytics_mcp.json`
- **Webhook Path**: `/webhook/youtube-analytics`
- **Status**: Ready for import
- **Features**: Analytics data retrieval and processing

### 4. Cross Platform Distribution MCP
- **File**: `workflows/cross_platform_mcp.json`
- **Webhook Path**: `/webhook/cross-platform-distribute`
- **Status**: Ready for import
- **Features**: Multi-platform content distribution

### 5. Affiliate Link Shortener MCP
- **File**: `workflows/affiliate_shortener_mcp.json`
- **Webhook Path**: `/webhook/affiliate-shorten`
- **Status**: Ready for import
- **Features**: URL shortening with tracking

---

## 🛠️ DEPLOYMENT INSTRUCTIONS

### Option 1: Manual Import via n8n Web Interface (RECOMMENDED)

1. **Open n8n Web Interface**:
   ```
   http://localhost:5678
   ```

2. **Import Each Workflow**:
   - Click "+" to create new workflow
   - Click the "..." menu → "Import from file"
   - Select workflow file (e.g., `workflows/tts_webhook_mcp.json`)
   - Click "Import"

3. **Activate Each Workflow**:
   - After import, click the "Inactive" toggle in top-right
   - Toggle should change to "Active"
   - Save the workflow

4. **Repeat for all 5 workflows**

### Option 2: Using n8n CLI (if available)

```bash
# If n8n CLI is installed
n8n import:workflow --input=workflows/tts_webhook_mcp.json
n8n import:workflow --input=workflows/youtube_upload_mcp.json
n8n import:workflow --input=workflows/youtube_analytics_mcp.json
n8n import:workflow --input=workflows/cross_platform_mcp.json
n8n import:workflow --input=workflows/affiliate_shortener_mcp.json
```

### Option 3: Docker Volume Mount (if using Docker)

```bash
# Mount workflows directory and import
docker cp workflows/ n8n_container:/home/node/workflows/
# Then import via web interface
```

---

## ✅ VERIFICATION STEPS

After importing and activating workflows:

### 1. Check Workflow Status
```bash
python import_workflows.py
```
Should show "Status: READY FOR USE" for all 5 workflows.

### 2. Run Individual Tests
```bash
# Test TTS workflow
python test_all_mcp_workflows.py tts

# Test YouTube upload
python test_all_mcp_workflows.py upload

# Test all workflows
python test_all_mcp_workflows.py
```

### 3. Manual Webhook Test
```bash
# Should return JSON response (not empty)
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "slug": "test123"}' \
  http://localhost:5678/webhook/tts-generation
```

---

## 🔧 TROUBLESHOOTING

### Issue: Empty Responses
**Cause**: Workflows not imported/activated in n8n
**Solution**: Import workflows via n8n web interface

### Issue: 404 Not Found
**Cause**: Webhook path not registered
**Solution**: Ensure workflow is active (green toggle in n8n)

### Issue: 500 Internal Server Error
**Cause**: Missing environment variables or API keys
**Solution**: Check `.env` file has required API keys:
- `ELEVENLABS_API_KEY`
- `YOUTUBE_API_KEY`
- `FIRECRAWL_API_KEY`

### Issue: JSON Errors in Workflows
**Cause**: Invalid JSON syntax
**Solution**: All JSON syntax errors have been fixed in MCP workflows

---

## 📊 EXPECTED TEST RESULTS

After proper deployment, you should see:

```
n8n MCP Workflow Import & Activation Tool
==================================================
Found 5 MCP workflow files:

[WORKFLOW] TTS Generation Webhook (MCP)
   Status: READY FOR USE
   Webhook: Returning JSON responses

[WORKFLOW] YouTube Upload Webhook (MCP)
   Status: READY FOR USE
   Webhook: Returning JSON responses

[... and so on for all 5 workflows]

SUCCESS RATE: 100%
```

---

## 🚀 NEXT STEPS

1. **Import workflows** via n8n web interface (required)
2. **Activate all workflows** (toggle to green/active)
3. **Run verification tests** to confirm functionality
4. **Set up environment variables** if any API calls fail
5. **Check n8n execution logs** for detailed debugging

The workflow files are now properly formatted and ready for use. The only remaining step is the manual import into the n8n instance.