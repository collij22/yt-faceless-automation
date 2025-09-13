---
description: Prime Claude with essential project context for faceless YouTube automation
allowed-tools: Read, Glob, Grep
---

## Project Overview: Faceless YouTube Automation System

**Tech Stack**: Python 3.12, FFmpeg, Claude subagents, MCP servers (Firecrawl, n8n, Ref), n8n workflows

**Purpose**: Automated content creation for high-RPM faceless YouTube channels with profit optimization focus

## 8-Phase Content Pipeline

1. **Research** → `research-analyst` → High-RPM niche discovery, validated ideas → `data/ideas/*.json`
2. **Script** → `scriptwriter` → High-retention scripts with SSML, SEO metadata → `content/{slug}/script.md`
3. **Assets & TTS** → `asset-curator`, `voiceover-producer` → B-roll, audio → `assets/`, `audio.wav`
4. **Assembly** → `video-assembler` → FFmpeg video compilation → `final.mp4`
5. **Upload** → `uploader` → YouTube publishing via n8n → Scheduled video
6. **Optimize** → `optimizer` → Analytics-driven A/B testing → `reports/*.md`
7. **Monetize** → `revenue-analyst` → Revenue expansion strategies
8. **Scale** → Cross-platform distribution, automation improvements

## Core Components

**Subagents** (`.claude/agents/`):
- `research-analyst`: Trend validation, competitor analysis
- `scriptwriter`: Hook-first structure, SSML markers, SEO
- `asset-curator`: Firecrawl MCP for web assets
- `voiceover-producer`: TTS via n8n webhook
- `video-assembler`: FFmpeg orchestration
- `uploader`: YouTube API via n8n
- `optimizer`: CTR/retention analysis
- `revenue-analyst`: Affiliate/sponsorship strategies

**Python Module** (`src/yt_faceless/`):
- `cli.py`: Entry point, `ytfaceless` command
- `orchestrator.py`: Pipeline coordination
- `assembly.py`: FFmpeg video assembly
- `config.py`: Environment management
- `youtube_metadata.py`: Metadata handling

## CLI Commands

```bash
# Setup
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# Initialize project
ytfaceless init

# Health check
ytfaceless health [--json]

# Video assembly
ytfaceless assemble --clips clip1.mp4 clip2.mp4 --audio narration.mp3 --output final.mp4

# Testing & quality
pytest
black src/ tests/
mypy src/
```

## Configuration

**Required**: `.env` file with:
- n8n webhook URLs (TTS, upload)
- API keys (Firecrawl, YouTube, TTS provider)
- FFmpeg path
- Directory paths (assets, output, content, data)

**MCP Servers**: Configure in Claude Code settings:
- Firecrawl MCP for web scraping
- n8n MCP for workflow automation
- Ref MCP for documentation

## Key Conventions

- **Python 3.12+** with type hints
- **Black formatter** (88 char lines)
- **Conventional Commits**
- **Batch TTS** requests for cost optimization
- **Firecrawl summaries** over full scraping
- **Windows-compatible** paths and commands

## Current Focus Areas

1. High-RPM niches: Finance, tech, health, business
2. Retention optimization: Hook within 5s, scene changes every 6-12s
3. SEO: Titles ≤60 chars, descriptions 500-1500 chars, 20-30 tags
4. Monetization: AdSense optimization, affiliate integration ready
5. Analytics: CTR, APV, retention curves for continuous improvement

## Testing

```bash
pytest                           # Run all tests
pytest tests/test_config.py -v  # Specific test
pytest -q                        # Quiet mode
```

Ready to assist with any phase of the YouTube automation pipeline. Use `@README.md` for full documentation.