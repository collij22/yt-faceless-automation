---
description: Prime Claude with complete YouTube faceless automation system context - V4 PIPELINE DEPLOYED WITH BULLETPROOF VIDEO PRODUCTION
allowed-tools: Read, Glob, Grep
---

## 🚀 Production-Ready YouTube Automation System - V4 Bulletproof Edition

**Status**: ✅ V4 PIPELINE COMPLETE WITH DYNAMIC LENGTH, MODEL SELECTION & BULLETPROOF PRODUCTION
**Tech Stack**: Python 3.12, FFmpeg, Claude subagents (V4), MCP (Firecrawl, n8n, Ref), n8n workflows
**Purpose**: Enterprise-grade automated content creation for high-RPM faceless YouTube channels with bulletproof production

## Complete 8-Phase Implementation

### Phase 1-2: Research & Scripting ✅
- **Research** → Dynamic idea generation (no recycling) → High-RPM niches → `data/ideas/*.json`
- **Script** → V4 generator (1/5/10/30 min) → No placeholders → `content/{slug}/script.md`

### Phase 3-5: Production & Assembly ✅
- **TTS** → `ytfaceless tts --slug SLUG` → Multi-provider audio generation
- **Assets** → `ytfaceless assets --slug SLUG` → B-roll & image curation
- **Timeline** → `ytfaceless timeline --slug SLUG` → Scene-by-scene composition
- **Assembly** → `ytfaceless produce --slug SLUG` → FFmpeg video → `final.mp4`

### Phase 6-7: Publishing & Optimization ✅
- **Upload** → `ytfaceless publish --slug SLUG` → YouTube via n8n webhook
- **Analytics** → `ytfaceless analytics fetch --slug SLUG` → Performance metrics
- **Optimize** → `ytfaceless optimize propose --slug SLUG` → A/B experiments

### Phase 8: Monetization & Scale ✅
- **Affiliates** → `ytfaceless monetize affiliates --slug SLUG` → Link injection
- **Sponsors** → `ytfaceless monetize sponsor --slug SLUG` → Disclosure automation
- **Shorts** → `ytfaceless shorts generate --slug SLUG` → 9:16 format conversion
- **Distribute** → `ytfaceless distribute post --slug SLUG` → Cross-platform
- **Localize** → `ytfaceless localize run --slug SLUG --languages es,de,fr`
- **Safety** → `ytfaceless safety check --slug SLUG` → Brand compliance
- **Calendar** → `ytfaceless calendar schedule SLUG --date YYYY-MM-DD`
- **Revenue** → `ytfaceless revenue report --month YYYY-MM`

## Architecture Overview

```
src/yt_faceless/
├── cli.py                    # 1,472-line CLI interface (30+ commands)
├── orchestrator.py           # 612-line pipeline coordinator
├── assembly.py              # FFmpeg video assembly engine
├── config.py                # 255+ environment variables
├── core/                    # Enhanced modules (analytics, experiments)
├── content/                 # Script generation, metadata
├── production/             # TTS, assets, timeline, subtitles
├── monetization/           # Affiliates, sponsorships, revenue
├── distribution/           # YouTube, TikTok, Instagram, X
├── localization/           # Multi-language translation
├── guardrails/             # Safety, compliance, moderation
├── integrations/           # n8n client, webhook handlers
├── scheduling/             # Content calendar, optimal timing
└── utils/                  # Validators, formatters, helpers
```

## Complete n8n Workflow Suite

- `tts_webhook_full.json` - Multi-provider TTS with chunking (300 lines)
- `youtube_upload_full.json` - Complete YouTube publishing
- `youtube_upload_working.json` - Battle-tested upload flow
- `youtube_analytics.json` - Performance data collection
- `cross_platform_distribution.json` - Multi-platform publishing
- `affiliate_shortener.json` - URL tracking & management
- `translation_webhook.json` - Multi-language processing

## Key Production Commands

```bash
# Setup (Windows)
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env  # Configure your settings

# V4 Production Pipeline (RECOMMENDED)
python run_full_production_pipeline_v4.py --model sonnet  # Balanced
python run_full_production_pipeline_v4.py --model claude  # Comprehensive
python run_full_production_pipeline_v4.py --model haiku   # Concise

# Legacy Commands (still available)
ytfaceless produce --slug my-video  # Complete video generation

# Publishing & Monetization
ytfaceless publish --slug my-video
ytfaceless monetize affiliates --slug my-video
ytfaceless shorts generate --slug my-video
ytfaceless distribute post --slug my-video

# Analytics & Optimization
ytfaceless analytics fetch --slug my-video
ytfaceless optimize propose --slug my-video
ytfaceless revenue report --month 2025-01
```

## Environment Configuration

**Required in `.env`**:
- `N8N_TTS_WEBHOOK_URL` - TTS generation endpoint
- `N8N_UPLOAD_WEBHOOK_URL` - YouTube upload endpoint
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` - Premium TTS
- `YOUTUBE_API_KEY` - Publishing access
- `FIRECRAWL_API_KEY` - Web scraping
- `FFMPEG_PATH` - Video processing
- 250+ other configurable options

## Advanced Features

### Monetization System
- **Affiliate Programs**: Amazon, Skillshare, NordVPN pre-configured
- **UTM Tracking**: Full analytics integration
- **Sponsorship Overlays**: FTC-compliant disclosures
- **Revenue Tracking**: Multi-tier monetization analytics

### Content Intelligence
- **Niche Scoring**: RPM validation, competition analysis
- **Hook Optimization**: 5-second retention focus
- **Scene Pacing**: 6-12 second transitions
- **SEO Automation**: Title variants, tag research, descriptions

### Safety & Compliance
- **Brand Safety**: Score-based content validation
- **Policy Checks**: YouTube monetization compliance
- **Moderation Gates**: Pre-publish safety verification
- **Violation Tracking**: Automated issue resolution

### Cross-Platform Scale
- **YouTube Shorts**: Automatic 9:16 conversion
- **TikTok/Reels**: Platform-optimized exports
- **Scheduling**: Analytics-driven timing
- **Localization**: 10+ language support

## Subagent Capabilities

All subagents have MCP access for:
- **Firecrawl**: Web scraping, research, asset discovery
- **n8n**: Workflow automation, webhook triggers
- **Ref**: Documentation, API references

## Production Status

✅ **V4 Script Generator** - Dynamic 1/5/10/30 min videos (no placeholders)
✅ **Model Selection** - claude/haiku/sonnet for different content styles
✅ **Accurate Timestamps** - END timestamps match actual duration
✅ **Bulletproof Video Assembly** - 6 critical production fixes verified
✅ **API Resilience** - Exponential backoff retry logic on all asset sources
✅ **Smart Deduplication** - Perceptual hashing with URL-based fallback
✅ **License Compliance** - Commercial validation & attribution
✅ **42 Python modules** implemented
✅ **8 n8n workflows** production-ready
✅ **Windows compatibility** complete
✅ **YouTube quota management** tools included

**V4 BULLETPROOF IMPROVEMENTS DEPLOYED & TESTED**

System generates accurate video lengths with resilient production:
- 5-min selection → 6-min video (was 17 min in V3)
- Automatic asset fallbacks prevent failures
- YouTube-safe description lengths
- Perfect audio/video sync via FFprobe
- All transitions properly mapped for FFmpeg