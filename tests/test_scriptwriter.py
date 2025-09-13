"""Tests for scriptwriter module."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from yt_faceless.content.scriptwriter import ScriptGenerator
from yt_faceless.core.config import load_config as load_enhanced_config
from yt_faceless.core.schemas import (
    IdeaScores,
    IdeaValidation,
    Keywords,
    VideoIdea,
    VideoNiche,
)


class MockProcess:
    """Mock subprocess result."""
    
    def __init__(self, returncode: int = 0, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr


@pytest.fixture
def mock_config(monkeypatch, tmp_path):
    """Create a mock configuration with temp directories."""
    import yt_faceless.core.config as core_cfg
    
    # Mock FFmpeg check
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: MockProcess(0, "")
    )
    
    # Set environment variables
    monkeypatch.setenv("N8N_TTS_WEBHOOK_URL", "https://n8n.example/tts")
    monkeypatch.setenv("N8N_UPLOAD_WEBHOOK_URL", "https://n8n.example/upload")
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test_key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test_voice")
    monkeypatch.setenv("CONTENT_DIR", str(tmp_path / "content"))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / ".cache"))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    
    config = load_enhanced_config()
    config.directories.create_all()
    return config


@pytest.fixture
def sample_idea():
    """Create a sample video idea for testing."""
    return VideoIdea(
        idea_id=uuid4(),
        timestamp=datetime.now(),
        title="How AI Changes Everything in 2024",
        angle="Discover the revolutionary AI breakthroughs that are transforming industries and daily life",
        niche=VideoNiche.AI_NEWS,
        scores=IdeaScores(
            rpm=8.5,
            trend_velocity=9.0,
            competition_gap=7.5,
            virality=8.0,
            monetization=9.0,
            composite=8.4,
        ),
        keywords=Keywords(
            primary=["AI breakthrough", "artificial intelligence", "GPT-5"],
            secondary=["machine learning", "deep learning", "neural networks", "AI tools", "automation"],
            long_tail=["how AI works", "future of AI", "AI for beginners"],
        ),
        competitors=[],
        sources=["https://example.com/ai-news"],
        validation=IdeaValidation(
            youtube_safe=True,
            copyright_clear=True,
            trend_sustainable=True,
            monetization_eligible=True,
        ),
        notes="High-potential video idea",
    )


def test_script_generation_basic(mock_config, sample_idea):
    """Test basic script generation."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Verify script properties
    assert script.script_id is not None
    assert script.idea_id == sample_idea.idea_id
    assert script.title == sample_idea.title
    assert script.duration_seconds == 600  # Default 10 minutes
    assert script.word_count > 0
    assert len(script.sections) > 0
    assert script.hook_text != ""
    assert script.cta_text != ""
    
    # Verify metadata properties
    assert metadata.video_id is not None
    assert metadata.script_id == script.script_id
    assert len(metadata.titles) > 0
    assert metadata.description is not None
    assert metadata.tags is not None
    assert len(metadata.chapters) > 0


def test_title_variants_max_length(mock_config, sample_idea):
    """Test that all title variants are max 60 characters."""
    generator = ScriptGenerator(mock_config)
    
    # Create an idea with a very long title (between 60-100 chars)
    long_title_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "This is a very long title that exceeds YouTube's 60 character limit for titles",  # 79 chars
        }
    )
    
    script, metadata = generator.generate_script(long_title_idea)
    
    # Check all title variants
    for variant in metadata.titles:
        assert len(variant.text) <= 60, f"Title too long: {variant.text} ({len(variant.text)} chars)"
        assert variant.ctr_prediction >= 0 and variant.ctr_prediction <= 1
        assert variant.keyword_density >= 0


def test_description_length_cap(mock_config, sample_idea):
    """Test that description respects YouTube's 5000 char limit."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Check description length
    assert len(metadata.description.text) <= 5000
    assert len(metadata.description.text) >= 100  # Should have meaningful content
    assert len(metadata.description.keywords_included) > 0
    assert len(metadata.description.timestamps) > 0
    assert len(metadata.description.hashtags) > 0


def test_chapter_generation(mock_config, sample_idea):
    """Test that chapters are generated from script sections."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Check chapters
    assert len(metadata.chapters) > 0
    
    for time, title in metadata.chapters:
        assert time >= 0
        assert len(title) > 0
        assert "cold_open" not in title.lower()  # Should skip cold open
    
    # Chapters should be in chronological order
    times = [time for time, _ in metadata.chapters]
    assert times == sorted(times)


def test_ssml_generation_and_escaping(mock_config, sample_idea):
    """Test SSML generation and XML escaping."""
    generator = ScriptGenerator(mock_config)
    
    # Create idea with special characters that need escaping
    special_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "AI & Machine Learning: <Advanced> Topics",
            "angle": "Learn about 'cutting-edge' AI & ML with \"expert\" insights",
        }
    )
    
    script, metadata = generator.generate_script(special_idea)
    
    # Check SSML in sections
    for section in script.sections:
        if section.ssml_text:
            # Check for proper XML structure
            assert section.ssml_text.startswith("<speak>")
            assert section.ssml_text.endswith("</speak>")
            
            # Check that special characters are escaped
            if "&" in section.text and "&" not in ["&amp;", "&lt;", "&gt;", "&quot;", "&apos;"]:
                assert "&amp;" in section.ssml_text
            if "<" in section.text:
                assert "&lt;" in section.ssml_text
            if ">" in section.text:
                assert "&gt;" in section.ssml_text


def test_file_creation(mock_config, sample_idea):
    """Test that script and metadata files are created correctly."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Construct expected directory path
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in sample_idea.title)
    safe_title = safe_title.replace(" ", "_").lower()[:50]
    slug = f"{safe_title}_{str(script.script_id)[:8]}"
    
    video_dir = mock_config.directories.content_dir / slug
    
    # Check directory exists
    assert video_dir.exists()
    
    # Check script.md exists and has content
    script_file = video_dir / "script.md"
    assert script_file.exists()
    
    script_content = script_file.read_text(encoding="utf-8")
    assert sample_idea.title in script_content
    assert "## " in script_content  # Has section headers
    assert "SSML" in script_content  # Has SSML sections
    
    # Check metadata.json exists and is valid JSON
    metadata_file = video_dir / "metadata.json"
    assert metadata_file.exists()
    
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata_dict = json.load(f)
    
    assert "video_id" in metadata_dict
    assert "script_id" in metadata_dict
    assert "titles" in metadata_dict
    assert "description" in metadata_dict
    assert "tags" in metadata_dict
    assert "chapters" in metadata_dict


def test_template_selection(mock_config, sample_idea):
    """Test that different templates are selected based on title."""
    generator = ScriptGenerator(mock_config)
    
    # Test story arc template
    story_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "The Story of How AI Was Born",
        }
    )
    template = generator._select_template(story_idea)
    assert template == "story_arc"
    
    # Test listicle template
    list_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "Top 10 AI Tools You Need",
        }
    )
    template = generator._select_template(list_idea)
    assert template == "listicle"
    
    # Test educational template
    edu_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "How Does AI Actually Work",
        }
    )
    template = generator._select_template(edu_idea)
    assert template == "educational"
    
    # Test comparison template
    compare_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "GPT-4 vs Claude: Which is Better",
        }
    )
    template = generator._select_template(compare_idea)
    assert template == "comparison"
    
    # Test news template
    news_idea = VideoIdea(
        **{
            **sample_idea.__dict__,
            "title": "Breaking: New AI Model Just Released",
        }
    )
    template = generator._select_template(news_idea)
    assert template == "news_analysis"


def test_dynamic_year_in_titles(mock_config, sample_idea):
    """Test that title variants use the current year dynamically."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    current_year = datetime.now().year
    
    # Find the time-sensitive variant (should have "(YYYY Update)" format)
    year_variant = None
    for variant in metadata.titles:
        if f"({current_year} Update)" in variant.text:
            year_variant = variant
            break
    
    assert year_variant is not None, f"Should have a year-based title variant with ({current_year} Update)"
    assert f"({current_year} Update)" in year_variant.text


def test_tags_generation(mock_config, sample_idea):
    """Test that tags are properly categorized."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Check tag categories
    assert len(metadata.tags.primary) > 0
    assert len(metadata.tags.primary) <= 10
    
    assert len(metadata.tags.competitive) > 0
    for tag in metadata.tags.competitive:
        assert str(datetime.now().year) in tag  # Should have current year
    
    assert len(metadata.tags.trending) > 0
    for tag in metadata.tags.trending:
        assert "explained" in tag  # Should have "explained" suffix
    
    assert len(metadata.tags.long_tail) > 0


def test_youtube_category_mapping(mock_config, sample_idea):
    """Test that YouTube categories are correctly mapped."""
    generator = ScriptGenerator(mock_config)
    
    # Test different niches
    test_cases = [
        (VideoNiche.AI_NEWS, 28),  # Science & Technology
        (VideoNiche.FINANCE, 22),  # People & Blogs
        (VideoNiche.PSYCHOLOGY, 27),  # Education
        (VideoNiche.HEALTH, 26),  # Howto & Style
    ]
    
    for niche, expected_category in test_cases:
        idea = VideoIdea(
            **{
                **sample_idea.__dict__,
                "niche": niche,
            }
        )
        category_id = generator._get_youtube_category(idea)
        assert category_id == expected_category


def test_script_word_count(mock_config, sample_idea):
    """Test that script respects target word count."""
    generator = ScriptGenerator(mock_config)
    
    # Test with custom duration
    target_duration = 300  # 5 minutes
    expected_words = (target_duration / 60) * generator.words_per_minute
    
    script, metadata = generator.generate_script(
        sample_idea,
        target_duration=target_duration
    )
    
    assert script.duration_seconds == target_duration
    # Allow 20% variance in word count
    assert abs(script.word_count - expected_words) / expected_words < 0.2


def test_section_timing(mock_config, sample_idea):
    """Test that section timings are properly calculated."""
    generator = ScriptGenerator(mock_config)
    
    script, metadata = generator.generate_script(sample_idea)
    
    # Check section timings
    for i, section in enumerate(script.sections):
        assert section.start_time >= 0
        assert section.end_time > section.start_time
        
        # Check continuity
        if i > 0:
            prev_section = script.sections[i - 1]
            assert abs(section.start_time - prev_section.end_time) < 0.1  # Allow small rounding difference
    
    # Last section should end around total duration
    last_section = script.sections[-1]
    assert abs(last_section.end_time - script.duration_seconds) < 10  # Within 10 seconds