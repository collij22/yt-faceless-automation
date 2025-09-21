#!/usr/bin/env python3
"""
Enhance a V4-produced run with full visuals (assets, timeline, assembly).

Usage:
  python scripts/enhance_v4_visuals.py --slug SLUG [--parallel] [--burn-subtitles]

Assumptions:
  - V4 has written content/{slug}/script.md and narration (narration.mp3 or audio.wav)
  - This script converts MP3 to WAV if needed, fetches free assets, builds a timeline,
    and assembles the final video at content/{slug}/final.mp4
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from pathlib import Path
import json
from typing import Optional

# Make local src importable when running as a standalone script
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(SRC_DIR))

from yt_faceless.core.config import AppConfig
from yt_faceless.core.config import load_config as load_app_config
from yt_faceless.production.assets import plan_assets_for_slug, download_assets
from yt_faceless.production.timeline import infer_timeline_from_script
from yt_faceless.core.errors import TimelineError
from yt_faceless.assembly import assemble_from_timeline


def _ensure_wav_audio(cfg: AppConfig, content_dir: Path) -> Path:
    """Ensure content/{slug}/audio.wav exists (convert from narration.mp3 if needed)."""
    wav_path = content_dir / "audio.wav"
    if wav_path.exists():
        return wav_path
    mp3_path = content_dir / "narration.mp3"
    if not mp3_path.exists():
        raise FileNotFoundError(f"Missing audio: {wav_path} and {mp3_path} not found")
    # Convert MP3 → WAV for downstream consistency
    subprocess.run([
        cfg.video.ffmpeg_bin,
        "-y",
        "-i",
        str(mp3_path),
        "-ar",
        "44100",
        "-ac",
        "1",
        str(wav_path),
    ], check=True, capture_output=True)
    return wav_path


async def _fetch_assets_async(cfg: AppConfig, manifest: dict, parallel: bool) -> dict:
    return await download_assets(cfg, manifest, parallel=parallel, force_download=False)


def enhance_from_v4(slug: str, parallel: bool, burn_subtitles: bool) -> Path:
    cfg = load_app_config()
    content_dir = cfg.directories.content_dir / slug
    script_path = content_dir / "script.md"
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script: {script_path}")

    # Ensure WAV present
    _ensure_wav_audio(cfg, content_dir)

    # Plan and fetch assets
    manifest = plan_assets_for_slug(cfg, slug)
    # If no assets planned (e.g., API failures), generate gradient-card fallbacks (images written to cache)
    if not manifest.get("assets"):
        from yt_faceless.production.fallbacks import ensure_minimum_assets
        print("[WARN] No assets planned; generating visual fallbacks...")
        _ = ensure_minimum_assets([], 12, scene_type=None)
    else:
        # Try to download assets; if this fails due to 403/429, timeline will still use thumbnails/fallbacks
        try:
            asyncio.run(_fetch_assets_async(cfg, manifest, parallel=parallel))
        except Exception as e:
            print(f"[WARN] Asset fetch failed, proceeding with planned/thumbnail/fallbacks: {e}")

    # Build timeline from script with transitions and Ken Burns (force scene analysis)
    # Some scripts lack metadata sections; scene analysis ensures segments are produced.
    from yt_faceless.production.timeline import infer_timeline_from_script as _infer
    # Use the version that supports scene analysis if available; on failure, fall back to manual analysis
    try:
        _infer(cfg, slug, auto_transitions=True, ken_burns=True)
    except (TypeError, TimelineError, Exception):
        # Older signature: call the advanced path explicitly
        from yt_faceless.production.timeline import TimelineBuilder, _build_scene_specs
        from yt_faceless.production.scene_analyzer import SceneAnalyzer
        content_dir = cfg.directories.content_dir / slug
        script_text = (content_dir / "script.md").read_text()
        metadata = json.loads((content_dir / "metadata.json").read_text())
        analyzer = SceneAnalyzer()
        # Estimate audio duration if needed
        audio_path = content_dir / "audio.wav"
        audio_duration = None
        if audio_path.exists():
            try:
                import subprocess, json as _json
                r = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format',str(audio_path)], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    d = _json.loads(r.stdout)
                    audio_duration = float(d.get('format',{}).get('duration',0)) or None
            except Exception:
                pass
        segments = analyzer.analyze_script(script_text, metadata, audio_duration)
        builder = TimelineBuilder(cfg)
        scene_specs = _build_scene_specs(segments, [], True, True, cfg.video.fps)  # assets may be empty; fallbacks kick in
        builder.build_advanced_timeline(
            slug=slug,
            scene_specs=scene_specs,
            narration_track=str(audio_path) if audio_path.exists() else None,
            burn_subtitles=cfg.features.get('auto_subtitles', True),
            subtitle_path=str(content_dir / 'subtitles.srt') if (content_dir / 'subtitles.srt').exists() else None,
            width=cfg.video.width,
            height=cfg.video.height,
            fps=cfg.video.fps
        )

    # Assemble final video. If timeline.json wasn't written by _infer (rare), build an in-memory
    # minimal timeline from synthesized scenes to avoid "timeline not found" errors.
    try:
        out_path = assemble_from_timeline(
            cfg,
            slug,
            burn_subtitles=burn_subtitles,
            music_gain_db=-16.0,
            output_path=None,
        )
    except Exception as e:
        # Last‑resort: build a basic timeline with gradient fallbacks covering narration duration
        print(f"[WARN] assemble_from_timeline failed: {e}; building minimal timeline in memory")
        from yt_faceless.production.fallbacks import ensure_minimum_assets
        content_dir = cfg.directories.content_dir / slug
        # Determine duration
        audio_path = content_dir / "audio.wav"
        total_dur = 300.0
        if audio_path.exists():
            try:
                import subprocess, json as _json
                r = subprocess.run(['ffprobe','-v','quiet','-print_format','json','-show_format',str(audio_path)], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    d = _json.loads(r.stdout)
                    total_dur = float(d.get('format',{}).get('duration', total_dur))
            except Exception:
                pass
        # Generate a handful of fallback cards
        fallbacks = ensure_minimum_assets([], max(6, int(total_dur // 8)), scene_type=None)
        scenes = []
        t = 0.0
        per = max(6.0, min(12.0, total_dur / max(1, len(fallbacks))))
        idx = 0
        while t < total_dur and idx < len(fallbacks):
            fa = fallbacks[idx]
            scenes.append({
                "scene_id": f"fb_{idx}",
                "clip_path": str(fa.path),
                "start_time": t,
                "end_time": min(total_dur, t + per),
                "source_start": 0,
                "source_end": min(per, total_dur - t),
                "transition": None,
                "transition_duration": 0.0,
                "zoom_pan": None,
                "overlay_text": None,
                "overlay_position": None,
                "audio_duck": False,
                "effects": []
            })
            t += per
            idx += 1
        timeline = {
            "version": 1,
            "slug": slug,
            "width": cfg.video.width,
            "height": cfg.video.height,
            "fps": cfg.video.fps,
            "total_duration": total_dur,
            "scenes": scenes,
            "music_track": None,
            "music_volume": 0.2,
            "narration_track": str(audio_path) if audio_path.exists() else "",
            "burn_subtitles": burn_subtitles,
            "subtitle_path": str(content_dir / 'subtitles.srt') if (content_dir / 'subtitles.srt').exists() else None,
            "loudness_target": -14,
            "output_format": "mp4",
        }
        out_path = assemble_from_timeline(
            cfg,
            slug,
            timeline=timeline,
            burn_subtitles=burn_subtitles,
            music_gain_db=-16.0,
            output_path=None,
        )
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Enhance V4 output with visuals")
    parser.add_argument("--slug", required=True, help="Content slug (content/{slug})")
    parser.add_argument("--parallel", action="store_true", help="Parallel asset downloads")
    parser.add_argument("--burn-subtitles", action="store_true", help="Burn subtitles in final video")
    args = parser.parse_args()

    try:
        out = enhance_from_v4(args.slug, args.parallel, args.burn_subtitles)
        print(f"\u2713 Visual enhancement complete: {out}")
        return 0
    except Exception as exc:
        print(f"ERROR: Visual enhancement failed: {exc}")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


