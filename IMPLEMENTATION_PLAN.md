# YouTube Automation Implementation Plan

## 🎯 Objective
Get the YouTube automation system working end-to-end, from content generation to upload and distribution.

## 📋 Current Status
- ✅ 5 production n8n workflows created and tested
- ✅ Python orchestrator framework in place
- ✅ Integration scripts ready
- ⏳ Using mock responses (need real API integration)
- ⏳ Manual video assembly (need FFmpeg automation)

## 🚀 Immediate Actions (Do Now)

### 1. Test the Pipeline (5 minutes)
```bash
# Ensure n8n is running with workflows active
python run_youtube_pipeline.py
```

This will:
- Generate a sample productivity video script
- Call all 5 n8n workflows in sequence
- Create session folder with all outputs
- Generate analytics and reports

### 2. Review Pipeline Output
Check `content/[session_id]/` for:
- `script.json` - Generated video script
- `tts_result.json` - TTS generation response
- `upload_result.json` - YouTube upload details
- `distribution_result.json` - Social media posts
- `affiliate_links.json` - Shortened links with QR codes
- `analytics_result.json` - Channel performance
- `pipeline_report.json` - Complete execution summary

## 📦 Integration Architecture

```
┌─────────────────┐
│  Python CLI     │ ─── run_youtube_pipeline.py
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  n8n Webhooks   │ ─── 5 Production Workflows
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mock/Real APIs │ ─── ElevenLabs, YouTube, etc.
└─────────────────┘
```

## 🔧 Next Steps for Production

### Phase 1: Replace Mock with Real APIs (Priority)

#### 1.1 ElevenLabs TTS Integration
```python
# In n8n workflow: Edit ElevenLabs_API node
# Change from Mock to actual HTTP Request
# Add header: xi-api-key: {{$env.ELEVENLABS_API_KEY}}
```

**Prerequisites:**
- ✅ ElevenLabs API key in .env
- Set voice_id to your preferred voice
- Test with small text first (API costs)

#### 1.2 YouTube Upload Integration
```python
# Requires OAuth2 setup in n8n
# Or use youtube_backend_api.py as bridge
```

**Human Action Required:**
1. Set up YouTube OAuth2 in Google Cloud Console
2. Configure OAuth2 credentials in n8n
3. Or run `youtube_backend_api.py` as middleware

### Phase 2: Video Assembly Automation

#### 2.1 FFmpeg Integration
```python
# Already have src/yt_faceless/assembly.py
# Need to connect with pipeline

from src.yt_faceless.assembly import VideoAssembler

assembler = VideoAssembler(config)
video_path = assembler.create_video(
    audio_file=tts_audio,
    clips=video_clips,
    output=output_path
)
```

#### 2.2 Stock Footage Integration
- Use Pexels API for free stock videos
- Or Pixabay API for images/videos
- Store in `assets/` folder

### Phase 3: Content Generation

#### 3.1 Script Generation with AI
```python
# Use Claude API or OpenAI for script writing
# Template in src/yt_faceless/scriptwriter.py
```

#### 3.2 Research Integration
```python
# Use research-analyst agent
# Or brave_search_api for trending topics
```

## 🎬 Running Your First Real Video

### Step 1: Prepare Content
```python
# Create a simple test script
script = {
    "title": "Your First Automated Video",
    "script": "This is a test of the automation system.",
    "tags": ["test", "automation"]
}
```

### Step 2: Generate Audio (with real TTS)
1. Update n8n TTS workflow to use ElevenLabs
2. Run: `python run_youtube_pipeline.py`
3. Audio will be saved as MP3

### Step 3: Create Video
```bash
# Use existing assembly.py
python -c "
from src.yt_faceless.assembly import create_simple_video
create_simple_video(
    audio='content/session/audio.mp3',
    background='assets/background.mp4',
    output='final.mp4'
)
"
```

### Step 4: Upload (Manual First)
1. Use YouTube Studio to upload `final.mp4`
2. Copy metadata from `upload_result.json`
3. Monitor performance

## 🔄 Automation Schedule

### Daily Tasks (Cron/Task Scheduler)
```bash
# Morning: Research trending topics
python -m yt_faceless research --trending

# Afternoon: Generate and upload video
python run_youtube_pipeline.py --auto

# Evening: Check analytics
python -m yt_faceless analytics --report
```

### Weekly Tasks
- Review performance metrics
- Optimize underperforming videos
- Update content strategy

## 🚨 Prerequisites Checklist

### Required (Do Now):
- [x] n8n running with workflows active
- [x] Python environment activated
- [ ] API keys in .env file:
  ```
  YOUTUBE_API_KEY=your_key
  ELEVENLABS_API_KEY=your_key  # For TTS
  N8N_API_KEY=your_key  # If using n8n API
  ```

### Optional (For Full Automation):
- [ ] FFmpeg installed for video processing
- [ ] YouTube OAuth2 credentials
- [ ] Claude/OpenAI API key for content generation
- [ ] Brave Search API for research

## 📊 Monitoring & Optimization

### Key Metrics to Track:
1. **Upload Success Rate**: Check `logs/pipeline_*.json`
2. **View Performance**: Use analytics workflow weekly
3. **Engagement**: CTR, watch time from YouTube Analytics
4. **Revenue**: Track affiliate clicks and AdSense

### Optimization Loop:
```python
# Weekly optimization script
python -c "
from analytics import analyze_performance
insights = analyze_performance()
for video in insights['underperforming']:
    # Update title/thumbnail
    # Adjust tags
    # Modify description
"
```

## 🎯 Quick Start Commands

```bash
# 1. Test pipeline with mock data
python run_youtube_pipeline.py

# 2. Generate real content (needs API keys)
python run_youtube_pipeline.py --real

# 3. Check last run status
python -c "import json; print(json.load(open('content/latest/pipeline_report.json')))"

# 4. Run analytics
curl -X POST http://localhost:5678/webhook/youtube-analytics \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "your_channel"}'
```

## 📝 Today's Action Items

1. **Run the test pipeline** to see everything working
2. **Add your API keys** to .env file
3. **Choose one workflow** to make real (suggest TTS first)
4. **Generate one piece of content** manually
5. **Review the outputs** and iterate

## 🆘 Troubleshooting

### "Webhook not found"
- Ensure workflows are imported AND activated in n8n
- Check webhook paths match exactly

### "API key invalid"
- Verify keys in .env file
- Check API quota/billing

### "Video assembly failed"
- Install FFmpeg: `winget install ffmpeg`
- Check file paths are correct

## 🎉 Success Criteria

You'll know it's working when:
1. Pipeline completes without errors
2. Content folder has all expected files
3. Mock upload shows success
4. Analytics provides insights
5. Affiliate links are shortened with QR codes

---

**Next Step:** Run `python run_youtube_pipeline.py` and watch the magic happen!