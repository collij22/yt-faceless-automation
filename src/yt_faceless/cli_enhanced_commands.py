"""Enhanced CLI command implementations for visual pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .core.config import load_config as load_enhanced_config
from .logging_setup import get_logger

logger = get_logger(__name__)


def cmd_assets_enhanced(args: argparse.Namespace) -> int:
    """Handle enhanced asset commands (plan, fetch)."""
    try:
        from .production.assets import plan_assets_for_slug, download_assets
        from .production.scene_analyzer import analyze_script_for_scenes
        from .utils.license import check_license_compatibility

        config = load_enhanced_config()
        assets_dir = config.directories.assets_dir / args.slug
        content_dir = config.directories.content_dir / args.slug
        manifest_path = assets_dir / "manifest.json"

        # Handle subcommands
        if args.assets_command == "plan":
            # Analyze script for scenes and keywords
            script_path = content_dir / "script.md"
            metadata_path = content_dir / "metadata.json"

            if not script_path.exists():
                print(f"ERROR: Script not found: {script_path}")
                return 1

            print("🔍 Analyzing script for visual requirements...")
            scenes = analyze_script_for_scenes(
                script_path,
                metadata_path if metadata_path.exists() else None
            )

            print(f"📊 Found {len(scenes)} scenes requiring visuals")
            for scene in scenes[:5]:  # Show first 5
                if scene.search_queries:
                    print(f"  Scene {scene.index + 1}: {', '.join(scene.search_queries[:3])}")

            # Plan assets
            print("\n📋 Planning asset collection...")
            manifest = plan_assets_for_slug(config, args.slug, max_assets=args.max_assets)
            print(f"✅ Planned {len(manifest['assets'])} assets")

            # Check license compatibility
            licenses = [a.get("license", "") for a in manifest["assets"]]
            compat = check_license_compatibility(licenses)

            if not compat["compatible"]:
                print("\n⚠️ WARNING: License compatibility issues:")
                for warning in compat["warnings"]:
                    print(f"  - {warning}")

            if compat["requires_attribution"]:
                print("\n📝 NOTE: Attribution required for some assets")

            # Save summary
            summary_path = assets_dir / "plan_summary.txt"
            assets_dir.mkdir(parents=True, exist_ok=True)
            with open(summary_path, "w") as f:
                f.write(f"Asset Plan for {args.slug}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total assets planned: {len(manifest['assets'])}\n")
                f.write(f"Attribution required: {compat['requires_attribution']}\n")
                f.write(f"Commercial safe: {compat['commercial_safe']}\n")

            print(f"\n💾 Plan saved to: {summary_path}")

            return 0

        elif args.assets_command == "fetch":
            # Check if manifest exists
            if not manifest_path.exists():
                print("📋 No asset manifest found. Running planning first...")
                manifest = plan_assets_for_slug(config, args.slug)
            else:
                with open(manifest_path) as f:
                    manifest = json.load(f)

            # Download assets
            print(f"⬇️ Fetching {len(manifest['assets'])} assets...")

            async def download():
                return await download_assets(
                    config,
                    manifest,
                    parallel=args.parallel,
                    force_download=args.force
                )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                updated_manifest = loop.run_until_complete(download())

                # Show summary
                print(f"\n✅ Downloaded {len(updated_manifest['assets'])} assets successfully")
                print(f"📁 Location: {assets_dir}")

                if updated_manifest.get("attribution_required"):
                    print("\n📝 Attribution file created: ATTRIBUTION.txt")

                # Count by type
                types = {}
                for asset in updated_manifest["assets"]:
                    asset_type = asset.get("type", "unknown")
                    types[asset_type] = types.get(asset_type, 0) + 1

                print("\nAssets by type:")
                for asset_type, count in types.items():
                    print(f"  {asset_type}: {count}")

                return 0
            finally:
                loop.close()

    except Exception as e:
        logger.error(f"Asset command failed: {e}")
        print(f"❌ ERROR: Asset command failed: {e}")
        return 1


def cmd_timeline_enhanced(args: argparse.Namespace) -> int:
    """Handle enhanced timeline commands with visual composition."""
    try:
        from .production.timeline import (
            build_visual_timeline,
            validate_timeline,
            verify_assets_for_timeline,
            write_timeline_for_slug
        )

        config = load_enhanced_config()
        content_dir = config.directories.content_dir / args.slug
        timeline_path = content_dir / "timeline.json"

        if args.timeline_command == "auto":
            # Auto-generate visual timeline
            print("🎬 Building visual timeline with scene analysis...")

            timeline = build_visual_timeline(
                config,
                args.slug,
                use_scene_analysis=not args.no_analysis,
                auto_transitions=not args.no_transitions,
                ken_burns=not args.no_kenburns
            )

            print(f"✅ Generated timeline with {len(timeline['scenes'])} visual shots")

            # Show summary
            if timeline.get("scenes"):
                # Count unique scenes
                unique_scenes = set()
                for scene in timeline["scenes"]:
                    base_id = scene.get("scene_id", "").split("_shot_")[0]
                    if base_id:
                        unique_scenes.add(base_id)

                print(f"\n📊 Timeline Summary:")
                print(f"  • Unique scenes: {len(unique_scenes)}")
                print(f"  • Total shots: {len(timeline['scenes'])}")
                print(f"  • Duration: {timeline.get('total_duration', 0):.1f}s")
                print(f"  • Resolution: {timeline.get('width', 1920)}x{timeline.get('height', 1080)}")
                print(f"  • FPS: {timeline.get('fps', 30)}")

                # Features
                features = []
                if timeline.get("music_track"):
                    features.append("Background Music")
                if timeline.get("burn_subtitles"):
                    features.append("Burned Subtitles")
                if any(s.get("zoom_pan") for s in timeline["scenes"]):
                    features.append("Ken Burns Effects")
                if any(s.get("transition") for s in timeline["scenes"]):
                    features.append("Transitions")
                if any(s.get("overlay_text") for s in timeline["scenes"]):
                    features.append("Text Overlays")

                if features:
                    print(f"\n✨ Features:")
                    for feature in features:
                        print(f"  • {feature}")

            print(f"\n💾 Timeline saved to: {timeline_path}")

            return 0

        elif args.timeline_command == "validate":
            # Validate existing timeline
            if not timeline_path.exists():
                print(f"❌ ERROR: Timeline not found: {timeline_path}")
                return 1

            with open(timeline_path) as f:
                timeline = json.load(f)

            print("🔍 Validating timeline...")

            try:
                validate_timeline(timeline)
                print("✅ Timeline structure validation passed")

                # Verify assets
                missing = verify_assets_for_timeline(config, args.slug, timeline)
                if missing:
                    print("\n⚠️ WARNING: Missing assets:")
                    for item in missing[:10]:  # Show first 10
                        print(f"  • {item}")
                    if len(missing) > 10:
                        print(f"  ... and {len(missing) - 10} more")
                else:
                    print("✅ All assets found")

                # Check timeline consistency
                print("\n📊 Timeline Statistics:")
                print(f"  • Total duration: {timeline.get('total_duration', 0):.1f}s")
                print(f"  • Number of scenes: {len(timeline.get('scenes', []))}")

                # Check for gaps
                scenes = timeline.get("scenes", [])
                if scenes:
                    gaps = []
                    for i in range(1, len(scenes)):
                        gap = scenes[i]["start_time"] - scenes[i-1]["end_time"]
                        if gap > 0.1:
                            gaps.append((i-1, i, gap))

                    if gaps:
                        print(f"\n⚠️ Found {len(gaps)} gaps in timeline:")
                        for prev_idx, next_idx, gap in gaps[:5]:
                            print(f"  • Between scene {prev_idx} and {next_idx}: {gap:.2f}s")

                return 0

            except Exception as e:
                print(f"❌ Timeline validation failed: {e}")
                return 1

        elif args.timeline_command == "preview":
            # Preview timeline composition
            if not timeline_path.exists():
                print(f"❌ ERROR: Timeline not found: {timeline_path}")
                print("Run 'timeline auto' first to generate a timeline")
                return 1

            with open(timeline_path) as f:
                timeline = json.load(f)

            if args.format == "json":
                print(json.dumps(timeline, indent=2))
            elif args.format == "html":
                # Generate HTML preview
                html_path = content_dir / "timeline_preview.html"
                _generate_timeline_html(timeline, html_path, args.slug)
                print(f"📄 HTML preview generated: {html_path}")
            else:
                # Text preview
                print(f"\n🎬 Timeline Preview: {args.slug}")
                print("=" * 70)
                print(f"Duration: {timeline.get('total_duration', 0):.1f}s")
                print(f"Resolution: {timeline.get('width', 1920)}x{timeline.get('height', 1080)} @ {timeline.get('fps', 30)}fps")

                scenes = timeline.get("scenes", [])
                print(f"\n📑 Scenes ({len(scenes)}):\n")

                # Group by base scene
                scene_groups = {}
                for scene in scenes:
                    base_id = scene.get("scene_id", "unknown").split("_shot_")[0]
                    if base_id not in scene_groups:
                        scene_groups[base_id] = []
                    scene_groups[base_id].append(scene)

                for i, (base_id, shots) in enumerate(list(scene_groups.items())[:10], 1):
                    duration = shots[-1]["end_time"] - shots[0]["start_time"]
                    print(f"  {i}. {base_id} [{shots[0]['start_time']:.1f}-{shots[-1]['end_time']:.1f}s] ({duration:.1f}s)")

                    for shot in shots:
                        print(f"     • Shot: {shot['start_time']:.1f}-{shot['end_time']:.1f}s", end="")

                        features = []
                        if shot.get("overlay_text"):
                            features.append(f"Text: \"{shot['overlay_text'][:30]}...\"")
                        if shot.get("transition"):
                            features.append(f"Transition: {shot['transition']}")
                        if shot.get("zoom_pan"):
                            features.append("Ken Burns")

                        if features:
                            print(f" [{', '.join(features)}]")
                        else:
                            print()

                if len(scene_groups) > 10:
                    print(f"\n  ... and {len(scene_groups) - 10} more scenes")

                # Show summary
                print(f"\n📊 Summary:")
                print(f"  • Total unique scenes: {len(scene_groups)}")
                print(f"  • Total shots: {len(scenes)}")
                print(f"  • Average shots per scene: {len(scenes) / len(scene_groups):.1f}")

        return 0

    except Exception as e:
        logger.error(f"Timeline command failed: {e}")
        print(f"❌ ERROR: Timeline command failed: {e}")
        return 1


def _generate_timeline_html(timeline: dict, output_path: Path, slug: str) -> None:
    """Generate an HTML preview of the timeline."""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Timeline Preview - {slug}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
        .header {{ background: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .timeline {{ position: relative; height: 100px; background: #333; border-radius: 4px; margin: 20px 0; }}
        .scene {{ position: absolute; height: 80px; top: 10px; background: #4a90e2; border-radius: 3px;
                  display: flex; align-items: center; justify-content: center; font-size: 12px;
                  cursor: pointer; transition: all 0.3s; }}
        .scene:hover {{ background: #5aa3f0; transform: translateY(-2px); }}
        .details {{ background: #2a2a2a; padding: 15px; border-radius: 8px; margin-top: 20px; }}
        .feature {{ display: inline-block; background: #4a4a4a; padding: 5px 10px;
                    border-radius: 15px; margin: 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Timeline Preview: {slug}</h1>
        <p>Duration: {timeline.get('total_duration', 0):.1f}s |
           Resolution: {timeline.get('width', 1920)}x{timeline.get('height', 1080)} |
           FPS: {timeline.get('fps', 30)}</p>
    </div>

    <div class="timeline">
"""

    # Add scenes to timeline
    total_duration = timeline.get('total_duration', 100)
    for scene in timeline.get('scenes', []):
        left = (scene['start_time'] / total_duration) * 100
        width = ((scene['end_time'] - scene['start_time']) / total_duration) * 100
        html_content += f"""
        <div class="scene" style="left: {left:.1f}%; width: {width:.1f}%;"
             title="{scene.get('scene_id', 'Scene')} ({scene['start_time']:.1f}-{scene['end_time']:.1f}s)">
        </div>
"""

    html_content += """
    </div>

    <div class="details">
        <h2>Features</h2>
"""

    # Add feature badges
    features = []
    if timeline.get("music_track"):
        features.append("🎵 Background Music")
    if timeline.get("burn_subtitles"):
        features.append("📝 Subtitles")
    if any(s.get("zoom_pan") for s in timeline.get("scenes", [])):
        features.append("🎥 Ken Burns")
    if any(s.get("transition") for s in timeline.get("scenes", [])):
        features.append("✨ Transitions")
    if any(s.get("overlay_text") for s in timeline.get("scenes", [])):
        features.append("💬 Text Overlays")

    for feature in features:
        html_content += f'<span class="feature">{feature}</span>'

    html_content += """
    </div>
</body>
</html>
"""

    output_path.write_text(html_content, encoding="utf-8")