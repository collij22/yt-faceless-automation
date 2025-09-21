#!/usr/bin/env python3
"""
Quick script generator for a given slug.

Creates content/{slug}/script.md and metadata.json using the built-in ScriptGenerator.

Usage:
  python scripts/generate_script_for_slug.py \
    --slug new_1 \
    --title "The $50 Investment That Changed My Life" \
    --niche finance \
    --minutes 10
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List

# Ensure local src is importable when run directly
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yt_faceless.core.config import load_config
from yt_faceless.core.schemas import (
    CompetitorAnalysis,
    IdeaScores,
    IdeaValidation,
    Keywords,
    VideoIdea,
    VideoNiche,
)
from yt_faceless.content.scriptwriter import ScriptGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate script + metadata for a slug")
    parser.add_argument("--slug", required=True, help="Content slug (folder name under content/)")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--angle", default="A clear, practical and engaging exploration of the topic.", help="Video angle/summary")
    parser.add_argument("--niche", default="education", choices=[n.value for n in VideoNiche], help="Video niche")
    parser.add_argument("--minutes", type=int, default=10, help="Target duration in minutes (default 10)")
    return parser.parse_args()


def build_keywords_from_title(title: str) -> Keywords:
    words = [w.strip(".,:;!?") for w in title.lower().split() if len(w) > 3]
    primary = words[:2]
    secondary = words[2:6]
    long_tail: List[str] = []
    return Keywords(primary=primary, secondary=secondary, long_tail=long_tail)


def main() -> int:
    args = parse_args()

    cfg = load_config()
    content_dir = cfg.directories.content_dir / args.slug
    content_dir.mkdir(parents=True, exist_ok=True)

    # Compose a minimal, valid VideoIdea
    now = datetime.now()
    scores = IdeaScores(
        rpm=7.5, trend_velocity=7.0, competition_gap=6.5, virality=6.8, monetization=8.0, composite=7.2
    )
    validation = IdeaValidation(
        youtube_safe=True, copyright_clear=True, trend_sustainable=True, monetization_eligible=True
    )
    keywords = build_keywords_from_title(args.title)
    competitors = [
        CompetitorAnalysis(
            channel_name="BenchmarkChannel",
            channel_id=None,
            video_title=f"Similar to: {args.title}",
            video_id=None,
            views=100000,
            likes=5000,
            comments=800,
            duration_seconds=600,
            published_at=now,
            strategy_notes="High engagement via strong hook and clear pacing",
        )
    ]

    idea = VideoIdea(
        title=args.title,
        angle=args.angle,
        niche=VideoNiche(args.niche),
        scores=scores,
        keywords=keywords,
        competitors=competitors,
        sources=["internal"],
        validation=validation,
    )

    generator = ScriptGenerator(cfg)
    target_seconds = max(60, args.minutes * 60)
    script, metadata = generator.generate_script(
        idea=idea,
        template=None,
        target_duration=target_seconds,
        style={"voice": "neutral", "tone": "confident"},
    )

    # Move generated files into content/{slug}/ explicitly if needed (generator should already write there)
    # This is a safety net in case future generator paths change.
    # Files are expected at content/{slug}/script.md and metadata.json
    script_path = content_dir / "script.md"
    meta_path = content_dir / "metadata.json"
    if not script_path.exists():
        script_path.write_text("\n".join(s.text for s in script.sections), encoding="utf-8")
    if not meta_path.exists():
        import json
        def _default(o):
            try:
                # pydantic BaseModel
                if hasattr(o, 'model_dump'):
                    return o.model_dump()
            except Exception:
                pass
            # UUID, datetime, Path, enums
            import datetime
            from pathlib import Path as _Path
            from enum import Enum as _Enum
            if hasattr(o, 'hex') and len(getattr(o, 'hex', '')) in (32,):
                return str(o)
            if isinstance(o, (datetime.datetime, datetime.date)):
                return o.isoformat()
            if isinstance(o, _Path):
                return str(o)
            if isinstance(o, _Enum):
                return o.value
            # Fallback
            return str(o)
        meta_path.write_text(json.dumps(metadata, default=_default, indent=2), encoding="utf-8")

    print(f"✓ Generated script and metadata for slug '{args.slug}' at {content_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


