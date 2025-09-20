# Faceless YouTube Automation — Claude Subagents + MCP + n8n (Python 3.12)

This repository provides a cutting-edge, profitability-focused automation system for faceless YouTube channels. It combines Claude Code subagents, Model Context Protocol (MCP) servers (Firecrawl, n8n MCP, Ref MCP), n8n workflows, and a lightweight Python 3.12 orchestration layer with FFmpeg-based video assembly.

> Citations used to derive strategy and implementation targets:
> - Faceless channel ideas and formats: [Zebracat — 13 Best Faceless YouTube Channel Ideas (2025)](https://www.zebracat.ai/post/13-best-faceless-youtube-channel-ideas)
> - High-RPM niches: [TastyEdits — Most Profitable YouTube Niches in 2024](https://www.tastyedits.com/most-profitable-youtube-niches/) and [TubeBuddy — CPM & RPM expectations](https://www.tubebuddy.com/blog/youtube-cpm-rpm-how-much-can-creators-make-with-adsense-in-2024/), plus community insight: [r/PartneredYoutube: Highest RPMs](https://www.reddit.com/r/PartneredYoutube/comments/1b2y6v5/which_niches_have_highest_rpm_in_2024/)
> - Trend sources: [Exploding Topics — AI Trends](https://explodingtopics.com/ai-topics)
> - Upload automation: [n8n YouTube node docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.youtube/)
> - Web research/scraping automation: [Firecrawl + n8n](https://www.firecrawl.dev/blog/firecrawl-n8n-web-automation) and [Firecrawl MCP Server (GitHub)](https://github.com/firecrawl/firecrawl-mcp-server)
> - n8n MCP server: [LobeHub — n8n MCP Server](https://lobehub.com/mcp/illuminaresolutions-n8n-mcp-server)
> - Optional search API: [Brave Search API](https://api-dashboard.search.brave.com/app/plans) and [What sets Brave apart](https://brave.com/search/api/guides/what-sets-brave-search-api-apart/)

---

## 8-Phase Plan (Profit-Optimized)

Each phase lists prerequisites and outputs, aligned with Claude Subagents best practices ([Anthropic docs — Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)).

### Phase 1 — Prerequisites & Environment
- Install: Python 3.12+, FFmpeg, Git.
- Set up Claude Code with MCP servers:
  - Firecrawl MCP (scrape/search) — see `docs/mcp-setup.md`.
  - n8n MCP (or direct webhooks) — see `docs/mcp-setup.md`.
  - Ref MCP (latest docs retrieval; configure per your Ref MCP instructions) to keep all tool usage current.
- n8n instance: cloud or self-host; import workflows from `workflows/`.
- Create `.env` from `.env.example`.

Outputs:
- Working dev environment, MCP servers connected, n8n workflows deployed.

### Phase 2 — Research & Niche Selection Engine
- Goal: pick niches with high RPM and strong demand, then generate a validated idea backlog.
- Inputs: Zebracat ideas, TastyEdits RPM niches, TubeBuddy RPM data, Exploding Topics trends, Brave API (optional).
- Subagents: `research-analyst` (uses Firecrawl MCP, optional Brave API). Produces 10–20 validated ideas with sources, keyword lists, and competitor notes.

Outputs:
- `data/ideas/*.json` backlog with priority scores; SEO keyword sets per idea.

### Phase 3 — Scriptwriting & SEO
- Subagent: `scriptwriter` applies high-retention structure (hook → promise → proof → preview → CTA → value → cliffhanger). Generates: script (with SSML markers for TTS), title variants, 500–1500 char description, tags, and chapter markers.
- Validates against monetization and policy guardrails.

Outputs:
- `content/{slug}/script.md`, `metadata.json` with titles/descriptions/tags/chapters.

### Phase 4 — Asset Gathering & TTS
- Subagent: `asset-curator` fetches B‑roll and background using Firecrawl and stock sources. `voiceover-producer` compiles TTS via n8n webhook.
- You can connect any TTS provider via n8n; keep costs low by batching and caching.

Outputs:
- `content/{slug}/audio.wav` or `.mp3`, `assets/` with B‑roll lists and downloads, `subtitles.srt` (if generated).

### Phase 5 — Video Assembly (Bulletproof Production)
- Python + FFmpeg assembly provided in `yt_faceless.assembly` with CLI `ytfaceless assemble`.
- Subagent: `video-assembler` orchestrates assembly, transitions, background music, and subtitles.
- **Bulletproof Features:**
  - Resilient API calls with exponential backoff retry logic
  - Smart asset deduplication (perceptual hashing with URL fallback)
  - Automatic fallback generation for missing assets
  - FFprobe-based audio duration sync
  - Configurable FPS for Ken Burns effects
  - Commercial license validation and attribution

Outputs:
- Final `content/{slug}/final.mp4` with correct codecs and loudness.

### Phase 6 — Upload & Publishing Automation
- Use n8n YouTube node to upload, schedule, set thumbnails, tags, chapters, and end screens.
- Trigger via webhook from CLI `ytfaceless publish` or via `uploader` subagent.

Outputs:
- Scheduled YouTube video with SEO-optimized metadata.

### Phase 7 — Optimization & Analytics Loop
- Subagent: `optimizer` pulls analytics (CTR, APV, AVPV, retention curves) via n8n and proposes experiments (A/B titles/thumbnails, timestamps, descriptions).
- Implement small weekly iteration cycles.

Outputs:
- `reports/*.md` with experiments and next actions.

### Phase 8 — Monetization Expansion & Scale
- Subagent: `revenue-analyst` proposes affiliate integrations, sponsorship targets, Shorts repurposing, and content calendars.
- Optional cross-posting flows (Reddit/Twitter/LinkedIn) per automation patterns ([r/automation autopost](https://www.reddit.com/r/automation/comments/1ltwvzg/autopost_about_trending_topics_with_your_ai_clone/)).

Outputs:
- Monetization tracker, affiliate link management, sponsorship outreach list.

---

## Quickstart (Windows-friendly)

### Prerequisites
```bash
python --version          # 3.12+
ffmpeg -version
```

### Setup
```bash
# Create and activate venv
py -3.12 -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -e .[dev]

# Configure environment
copy .env.example .env    # Edit with your API keys
```

### Usage - Production Pipeline V4

The latest V4 pipeline generates properly sized videos with dynamic content:

```bash
# Run the full production pipeline (default: sonnet model)
python run_full_production_pipeline_v4.py

# Run with different AI models
python run_full_production_pipeline_v4.py --model claude   # Comprehensive content
python run_full_production_pipeline_v4.py --model haiku    # Concise, viral-focused
python run_full_production_pipeline_v4.py --model sonnet   # Balanced (default)
```

**Key V4 Features:**
- ✅ Dynamic script length (1, 5, 10, or 30 minute videos)
- ✅ No placeholders - all unique AI-generated content
- ✅ Accurate timestamps matching actual video duration
- ✅ Model selection for different content styles
- ✅ Fresh idea generation (no recycling)
- ✅ Bulletproof video assembly with automatic fallbacks
- ✅ Smart asset deduplication (perceptual or URL-based)
- ✅ Commercial license compliance with attribution
- ✅ YouTube-safe description length limits
- ✅ Resilient API integration with retry logic

When prompted:
- Select video length (1/5/10/30 minutes) - script adjusts automatically
- Choose niche (Finance/Tech/Health/Education)
- Pick or create custom idea
- Video generates at correct length (e.g., 5 min selection = 6 min video)

### Initialize the project
```
ytfaceless init
```
This will:
- Create all required directories
- Copy .env.example to .env (if needed)
- Set up logging
- Run initial health check

4) Configure environment
```
# Edit .env with your API keys and webhook URLs
notepad .env
```

5) Configure MCP servers in Claude Code (see `docs/mcp-setup.md`).

6) Import n8n workflows from `workflows/` and set credentials (YouTube node per docs).

7) Verify configuration
```
ytfaceless health          # Run health check
ytfaceless health --json   # Get JSON output
```

8) Available CLI commands
```
ytfaceless --help          # Show all commands
ytfaceless init            # Initialize project
ytfaceless health          # Run health check
ytfaceless assemble        # Assemble video from clips
```

---

## Directory layout
```
.
├─ src/yt_faceless/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ config.py
│  ├─ logging_setup.py
│  ├─ assembly.py
│  ├─ youtube_metadata.py
│  └─ orchestrator.py
├─ tests/
│  ├─ test_assembly.py
│  └─ test_config.py
├─ .claude/agents/
│  ├─ research-analyst.md
│  ├─ scriptwriter.md
│  ├─ asset-curator.md
│  ├─ voiceover-producer.md
│  ├─ video-assembler.md
│  ├─ uploader.md
│  ├─ optimizer.md
│  └─ revenue-analyst.md
├─ workflows/
│  ├─ tts_webhook_PRODUCTION.json
│  ├─ youtube_upload_PRODUCTION.json
│  ├─ youtube_analytics_PRODUCTION.json
│  ├─ cross_platform_PRODUCTION.json
│  └─ affiliate_shortener_PRODUCTION.json
├─ docs/
│  └─ mcp-setup.md
├─ archive/
│  ├─ run_full_production_pipeline.py
│  ├─ run_full_production_pipeline_v2.py
│  ├─ run_full_production_pipeline_v3.py
│  ├─ claude_script_generator.py
│  ├─ claude_script_generator_v2.py
│  ├─ claude_script_generator_v3.py
│  └─ assorted legacy tests/docs
├─ .env.example
├─ pyproject.toml
├─ README.md
└─ .gitignore
```

### Archived content

Legacy V1–V3 pipelines, generators, and ad‑hoc tests have been moved to `archive/`. They are kept for reference only and should not be used in production. Use `run_full_production_pipeline_v4.py` exclusively.

---

## Notes
- Follow Conventional Commits for your commits.
- Keep costs low by batching TTS and preferring efficient providers. Use Firecrawl to compile research summaries instead of scraping full pages when possible.
- Always consult Ref MCP for latest docs before changing tool usage or APIs.
