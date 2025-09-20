# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 Current Version: V4 Pipeline

**IMPORTANT**: Always use the V4 pipeline for production. Previous versions had critical issues:
- V1-V2: Placeholder content like `[Detailed explanation...]`
- V3: All videos generated at 17 minutes regardless of selection
- **V4: Fixed all issues - dynamic length, no placeholders, model selection**

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

### Production Commands
```bash
# Run the V4 production pipeline (RECOMMENDED)
python run_full_production_pipeline_v4.py              # Default: sonnet model
python run_full_production_pipeline_v4.py --model claude   # Comprehensive content
python run_full_production_pipeline_v4.py --model haiku    # Concise, viral content
python run_full_production_pipeline_v4.py --model sonnet   # Balanced (default)

# Legacy commands (DO NOT USE)
# python run_full_production_pipeline.py    # V1 - has placeholders
# python run_full_production_pipeline_v3.py # V3 - wrong video lengths

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

## V4 Pipeline Improvements

### Script Generation (`claude_script_generator_v4.py`)
- **Dynamic Length**: Generates appropriate content for 1, 5, 10, or 30 minute videos
- **No Placeholders**: All content is unique and specific, no `[insert example]` or `[...]`
- **Model Support**: Choose between claude (comprehensive), haiku (concise), or sonnet (balanced)
- **Accurate Timestamps**: END timestamps match actual video duration (e.g., `[END - 6:15]` for 6.25 min video)

### Word Count Targets
| Duration | Target Words | Actual Output | Result |
|----------|-------------|---------------|---------|
| 1 minute | 150 | ~180 | 1.4 minutes |
| 5 minutes | 750 | ~800 | 6.2 minutes |
| 10 minutes | 1500 | ~1500 | 11 minutes |
| 30 minutes | 4500 | ~2500-4500 | 20-30 minutes |

### Idea Generation
- **Dynamic Ideas**: No more recycled templates
- **Context-Aware**: Uses current date, trends, and niche-specific angles
- **Model-Specific**: Different idea styles based on selected model

### Usage Examples
```bash
# Generate a 5-minute educational video
python run_full_production_pipeline_v4.py
# Select: Educational Content → Choose idea → Video length: 2 (5 minutes)
# Result: ~800 word script, ~6 minute video

# Generate a 10-minute finance video with comprehensive content
python run_full_production_pipeline_v4.py --model claude
# Select: Personal Finance → Choose idea → Video length: 3 (10 minutes)
# Result: ~1500 word script, ~11 minute video
```