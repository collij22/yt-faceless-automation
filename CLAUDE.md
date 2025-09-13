# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Windows: Create and activate venv
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# Configure environment
copy .env.example .env  # Edit with your directories and n8n webhook URLs
```

### Common Commands
```bash
# Run the CLI
ytfaceless --help
ytfaceless assemble --clips clip1.mp4 clip2.mp4 --audio narration.mp3 --output final.mp4

# Testing
pytest
pytest tests/test_assembly.py -v  # Run specific test

# Code quality
black src/ tests/
isort src/ tests/
mypy src/
```

## Architecture Overview

This is a faceless YouTube automation system combining Claude subagents, MCP servers, n8n workflows, and Python orchestration.

### Core Components

1. **Subagents** (`.claude/agents/`): Specialized Claude agents for each phase
   - `research-analyst`: High-RPM niche discovery, trend validation, idea generation
   - `scriptwriter`: High-retention script generation with SSML markers, SEO metadata
   - `asset-curator`: B-roll and asset gathering via Firecrawl MCP
   - `voiceover-producer`: TTS production via n8n webhook
   - `video-assembler`: FFmpeg-based video assembly orchestration
   - `uploader`: YouTube upload via n8n
   - `optimizer`: Analytics-driven A/B testing and improvements
   - `revenue-analyst`: Monetization expansion strategies

2. **MCP Integration**: 
   - Firecrawl MCP for web scraping/search
   - n8n MCP for workflow automation
   - Ref MCP for latest documentation retrieval
   - Configuration in `docs/mcp-setup.md`

3. **Python Orchestrator** (`src/yt_faceless/`):
   - `cli.py`: Entry point with `ytfaceless` command
   - `orchestrator.py`: Main coordination logic
   - `assembly.py`: FFmpeg video assembly
   - `config.py`: Environment and configuration management
   - `youtube_metadata.py`: Metadata handling

4. **n8n Workflows** (`workflows/`):
   - `tts_webhook.json`: TTS processing webhook
   - `youtube_upload.json`: YouTube upload automation

### Content Pipeline

Phase 1 → Research (research-analyst) → `data/ideas/*.json`
Phase 2 → Script (scriptwriter) → `content/{slug}/script.md`, `metadata.json`  
Phase 3 → Assets + TTS (asset-curator, voiceover-producer) → `audio.wav`, `assets/`
Phase 4 → Assembly (video-assembler) → `final.mp4`
Phase 5 → Upload (uploader) → YouTube with SEO metadata
Phase 6 → Optimize (optimizer) → `reports/*.md` with experiments
Phase 7 → Monetize (revenue-analyst) → Revenue tracking and expansion

### Key Conventions

- Python 3.12+ required
- Black formatter (88 char line length)
- Conventional Commits for version control
- All subagents can access MCP tools unless explicitly restricted
- Batch TTS requests to minimize costs
- Use Firecrawl for summaries instead of full page scraping when possible