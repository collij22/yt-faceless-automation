from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .core.config import load_config as load_enhanced_config
from .config import load_config
from .logging_setup import get_logger, setup_logging
from .orchestrator import Orchestrator


logger = get_logger(__name__)


def _cmd_assemble(args: argparse.Namespace) -> int:
    cfg = load_config()
    orch = Orchestrator(cfg)
    clip_paths = [Path(p) for p in args.clips]
    audio = Path(args.audio)
    output = Path(args.output)
    orch.assemble(clip_paths=clip_paths, audio_path=audio, output_path=output)
    return 0


def _cmd_health(args: argparse.Namespace) -> int:
    """Run comprehensive health check on the system configuration."""
    try:
        # Load enhanced configuration
        config = load_enhanced_config()
        
        # Run health check
        health_status = config.health_check()
        
        # Format output based on requested format
        if args.json:
            print(json.dumps(health_status, indent=2))
        else:
            # Pretty print health status
            print("\n" + "="*60)
            print("FACELESS YOUTUBE AUTOMATION - HEALTH CHECK")
            print("="*60 + "\n")
            
            # Overall status
            status_label = {
                "healthy": "[OK]",
                "degraded": "[WARNING]",
                "unhealthy": "[ERROR]"
            }.get(health_status["status"], "[UNKNOWN]")
            
            print(f"Overall Status: {status_label} {health_status['status'].upper()}")
            print()
            
            # Errors
            if health_status.get("errors"):
                print("ERRORS:")
                for error in health_status["errors"]:
                    print(f"  - {error}")
                print()
            
            # Warnings
            if health_status.get("warnings"):
                print("WARNINGS:")
                for warning in health_status["warnings"]:
                    print(f"  - {warning}")
                print()
            
            # Component checks
            if health_status.get("checks"):
                print("COMPONENT CHECKS:")
                
                # Directories
                if "directories" in health_status["checks"]:
                    print("\n  Directories:")
                    for dir_name, exists in health_status["checks"]["directories"].items():
                        status = "[OK]" if exists else "[MISSING]"
                        print(f"    {status} {dir_name}")
                
                # APIs
                if "apis" in health_status["checks"]:
                    print("\n  API Keys:")
                    for api_name, value in health_status["checks"]["apis"].items():
                        if value and value != "Not set":
                            print(f"    [OK] {api_name}: {value}")
                        else:
                            print(f"    [MISSING] {api_name}: Not configured")
                
                # FFmpeg
                if "ffmpeg" in health_status["checks"]:
                    ffmpeg = health_status["checks"]["ffmpeg"]
                    status = "[OK]" if ffmpeg["available"] else "[ERROR]"
                    print(f"\n  FFmpeg:")
                    print(f"    {status} Available: {ffmpeg['available']}")
                    print(f"    Path: {ffmpeg['path']}")
            
            print("\n" + "="*60)
            
            # Return appropriate exit code
            if health_status["status"] == "unhealthy":
                return 1
            elif health_status["status"] == "degraded":
                return 2
            else:
                return 0
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        if args.json:
            print(json.dumps({"status": "error", "error": str(e)}))
        else:
            print(f"ERROR: Health check failed: {e}")
        return 1


# Phase 4 Commands - TTS and Assets

def _cmd_tts(args: argparse.Namespace) -> int:
    """Generate TTS voiceover for a content slug."""
    try:
        from .production.tts import voiceover_for_slug

        config = load_enhanced_config()
        audio_path = voiceover_for_slug(
            config,
            args.slug,
            overwrite=args.overwrite
        )

        print(f"✓ Generated voiceover: {audio_path}")
        return 0

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        print(f"ERROR: TTS generation failed: {e}")
        return 1


def _cmd_subtitles(args: argparse.Namespace) -> int:
    """Generate subtitles for a content slug."""
    try:
        from .production.subtitles import write_subtitles_for_slug, extract_sections_from_script

        config = load_enhanced_config()
        content_dir = config.directories.content_dir / args.slug
        script_path = content_dir / "script.md"

        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            return 1

        # Extract sections from script
        sections = extract_sections_from_script(script_path)

        # Generate subtitles
        subtitle_path = write_subtitles_for_slug(
            config,
            args.slug,
            sections,
            format=args.format
        )

        print(f"✓ Generated subtitles: {subtitle_path}")
        return 0

    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        print(f"ERROR: Subtitle generation failed: {e}")
        return 1


def _cmd_assets(args: argparse.Namespace) -> int:
    """Download assets for a content slug."""
    try:
        from .production.assets import plan_assets_for_slug, download_assets

        config = load_enhanced_config()

        # Plan assets if manifest doesn't exist
        manifest_path = config.directories.assets_dir / args.slug / "manifest.json"

        if not manifest_path.exists():
            print("Planning assets...")
            manifest = plan_assets_for_slug(config, args.slug)
        else:
            # Load existing manifest
            with open(manifest_path) as f:
                manifest = json.load(f)

        # Download assets
        print(f"Downloading {len(manifest['assets'])} assets...")

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
        finally:
            loop.close()

        print(f"✓ Downloaded assets to: assets/{args.slug}/")
        if updated_manifest["attribution_required"]:
            print("  Note: Attribution required - see ATTRIBUTION.txt")

        return 0

    except Exception as e:
        logger.error(f"Asset download failed: {e}")
        print(f"ERROR: Asset download failed: {e}")
        return 1


def _cmd_timeline(args: argparse.Namespace) -> int:
    """Generate or validate timeline for a content slug."""
    try:
        from .production.timeline import (
            infer_timeline_from_script,
            validate_timeline,
            verify_assets_for_timeline,
            write_timeline_for_slug
        )

        config = load_enhanced_config()
        content_dir = config.directories.content_dir / args.slug
        timeline_path = content_dir / "timeline.json"

        if args.validate:
            # Validate existing timeline
            if not timeline_path.exists():
                print(f"ERROR: Timeline not found: {timeline_path}")
                return 1

            with open(timeline_path) as f:
                timeline = json.load(f)

            try:
                validate_timeline(timeline)
                print("✓ Timeline validation passed")

                # Verify assets
                missing = verify_assets_for_timeline(config, args.slug, timeline)
                if missing:
                    print("WARNING: Missing assets:")
                    for asset in missing:
                        print(f"  - {asset}")

                return 0

            except Exception as e:
                print(f"✗ Timeline validation failed: {e}")
                return 1

        else:
            # Generate timeline
            if args.auto or not timeline_path.exists():
                print("Generating timeline from script...")
                timeline = infer_timeline_from_script(
                    config,
                    args.slug,
                    auto_transitions=True,
                    ken_burns=True
                )
                print(f"✓ Generated timeline: {timeline_path}")
            else:
                print(f"Timeline already exists: {timeline_path}")
                print("Use --auto to regenerate")

            return 0

    except Exception as e:
        logger.error(f"Timeline operation failed: {e}")
        print(f"ERROR: Timeline operation failed: {e}")
        return 1


def _cmd_produce(args: argparse.Namespace) -> int:
    """Run complete production pipeline (TTS + Assets + Timeline)."""
    try:
        print(f"Running production pipeline for: {args.slug}")
        print("-" * 50)

        # Generate TTS
        print("\n[1/3] Generating voiceover...")
        args.overwrite = args.overwrite if hasattr(args, 'overwrite') else False
        if _cmd_tts(args) != 0:
            return 1

        # Generate subtitles
        print("\n[2/3] Generating subtitles...")
        args.format = "srt"
        if _cmd_subtitles(args) != 0:
            return 1

        # Download assets
        print("\n[3/3] Downloading assets...")
        args.force = False
        if _cmd_assets(args) != 0:
            return 1

        # Generate timeline
        print("\n[4/4] Generating timeline...")
        args.auto = True
        args.validate = False
        if _cmd_timeline(args) != 0:
            return 1

        print("\n" + "="*50)
        print("✓ Production complete!")
        print(f"  Ready for assembly: ytfaceless assemble --slug {args.slug}")

        return 0

    except Exception as e:
        logger.error(f"Production failed: {e}")
        print(f"ERROR: Production failed: {e}")
        return 1


# Phase 5 Commands - Assembly

def _cmd_assemble_timeline(args: argparse.Namespace) -> int:
    """Assemble video from timeline."""
    try:
        from .assembly import assemble_from_timeline, validate_output

        config = load_config()

        # Assemble video
        output_path = assemble_from_timeline(
            config,
            args.slug,
            burn_subtitles=args.burn_subtitles,
            music_gain_db=args.music_gain,
            output_path=Path(args.output) if args.output else None
        )

        print(f"✓ Assembled video: {output_path}")

        # Validate if requested
        if args.validate:
            # Get expected duration from timeline
            content_dir = Path("content") / args.slug
            timeline_path = content_dir / "timeline.json"

            if timeline_path.exists():
                with open(timeline_path) as f:
                    timeline = json.load(f)
                    expected_duration = timeline.get("total_duration", 0)

                if validate_output(output_path, expected_duration):
                    print("✓ Output validation passed")
                else:
                    print("✗ Output validation failed")
                    return 1

        return 0

    except Exception as e:
        logger.error(f"Assembly failed: {e}")
        print(f"ERROR: Assembly failed: {e}")
        return 1


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate video output."""
    try:
        from .assembly import validate_output

        output_path = Path(args.file)

        if not output_path.exists():
            print(f"ERROR: File not found: {output_path}")
            return 1

        # Get expected duration if slug provided
        expected_duration = args.duration

        if args.slug and not expected_duration:
            content_dir = Path("content") / args.slug
            timeline_path = content_dir / "timeline.json"

            if timeline_path.exists():
                with open(timeline_path) as f:
                    timeline = json.load(f)
                    expected_duration = timeline.get("total_duration", 0)

        if not expected_duration:
            print("ERROR: Expected duration not provided (use --duration or --slug)")
            return 1

        if validate_output(output_path, expected_duration, tolerance=args.tolerance):
            print("✓ Video validation passed")
            return 0
        else:
            print("✗ Video validation failed")
            return 1

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"ERROR: Validation failed: {e}")
        return 1


def _cmd_init(args: argparse.Namespace) -> int:
    """Initialize the project with required directories and configuration."""
    try:
        print("Initializing Faceless YouTube Automation Project...")
        
        # Load configuration to create directories
        config = load_enhanced_config()
        config.directories.create_all()
        
        # Setup logging
        setup_logging(
            logs_dir=config.directories.logs_dir,
            debug=config.debug,
            json_format=args.json
        )
        
        # Check if .env exists
        env_file = Path(".env")
        if not env_file.exists():
            env_example = Path(".env.example")
            if env_example.exists():
                print("Creating .env from .env.example...")
                import shutil
                shutil.copy(env_example, env_file)
                print("WARNING: Please edit .env and add your API keys and configuration")
            else:
                print("WARNING: No .env.example found. Please create .env manually")
        
        # Run health check
        health_status = config.health_check()
        
        print("\nInitialization complete!")
        print(f"   Status: {health_status['status']}")
        
        if health_status.get("errors"):
            print("\nERRORS - Please fix these errors:")
            for error in health_status["errors"]:
                print(f"  - {error}")
        
        if health_status.get("warnings"):
            print("\nWARNINGS - Optional improvements:")
            for warning in health_status["warnings"]:
                print(f"  - {warning}")
        
        print("\nNext steps:")
        print("  1. Edit .env with your API keys")
        print("  2. Set up n8n workflows")
        print("  3. Run 'ytfaceless health' to verify configuration")
        print("  4. Start generating content!")
        
        return 0
    
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        print(f"ERROR: Initialization failed: {e}")
        return 1


def _cmd_publish(args: argparse.Namespace) -> int:
    """Handle publish command."""
    try:
        cfg = load_config()
        orch = Orchestrator(cfg)

        # Build override paths if provided
        override_paths = {}
        if args.video:
            override_paths["video"] = args.video
        if args.thumbnail:
            override_paths["thumbnail"] = args.thumbnail

        # Call publish with parameters
        response = orch.publish(
            slug=args.slug,
            override_paths=override_paths if override_paths else None,
            schedule_iso=args.schedule,
            privacy=args.privacy,
            dry_run=args.dry_run,
            force=args.force,
            verify=not args.no_verify,  # Honor the --no-verify flag
        )

        # Output results
        if args.json:
            print(json.dumps(response.model_dump() if hasattr(response, 'model_dump') else response.__dict__, indent=2, default=str))
        else:
            print(f"✅ Upload successful!")
            print(f"Video ID: {response.video_id}")
            print(f"Status: {response.status}")
            print(f"Transaction: {response.transaction_id}")
            if response.publish_at_iso:
                print(f"Scheduled for: {response.publish_at_iso}")

        return 0

    except Exception as e:
        logger.error(f"Publish failed: {e}")
        print(f"❌ Upload failed: {e}")
        return 1


def _cmd_analytics_fetch(args: argparse.Namespace) -> int:
    """Handle analytics fetch command."""
    try:
        cfg = load_config()
        orch = Orchestrator(cfg)

        # Require either slug or video ID
        if not args.slug and not args.video_id:
            print("Error: Either --slug or --video-id is required")
            return 1

        # Fetch analytics
        slug_or_id = args.slug if args.slug else args.video_id
        snapshot = orch.analytics(slug_or_id, args.lookback_days)

        # Generate report if requested
        if args.report:
            # Get proposals for the report
            proposals = orch.propose_experiments(snapshot)
            report_path = orch.write_report(args.slug or args.video_id, snapshot, proposals)
            print(f"📊 Report generated: {report_path}")

        # Output results
        if args.json:
            print(json.dumps(snapshot.model_dump() if hasattr(snapshot, 'model_dump') else snapshot.__dict__, indent=2, default=str))
        else:
            print(f"📊 Analytics for {slug_or_id}")
            print(f"Performance Score: {snapshot.performance_score:.0f}/100")
            print(f"Views: {snapshot.kpis.views:,}")
            print(f"CTR: {snapshot.kpis.ctr:.1f}%")
            print(f"Avg View Duration: {snapshot.kpis.avg_view_duration_sec:.0f}s")
            print(f"Avg % Viewed: {snapshot.kpis.avg_percentage_viewed:.1f}%")

            if snapshot.anomalies:
                print("\n⚠️ Anomalies Detected:")
                for anomaly in snapshot.anomalies:
                    print(f"  - {anomaly.metric}: {anomaly.probable_cause}")

            if snapshot.predictions:
                print(f"\n📈 Predictions (confidence: {snapshot.predictions.confidence:.0%}):")
                print(f"  - 7-day views: {snapshot.predictions.views_7d:,}")
                print(f"  - 30-day views: {snapshot.predictions.views_30d:,}")
                print(f"  - 30-day revenue: ${snapshot.predictions.revenue_30d:.2f}")

        return 0

    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
        print(f"❌ Analytics failed: {e}")
        return 1


def _cmd_optimize_propose(args: argparse.Namespace) -> int:
    """Handle optimize propose command."""
    try:
        cfg = load_config()
        orch = Orchestrator(cfg)

        # Require either slug or video ID
        if not args.slug and not args.video_id:
            print("Error: Either --slug or --video-id is required")
            return 1

        # Load baselines if provided
        baselines = None
        if args.baselines:
            with open(args.baselines) as f:
                baselines = json.load(f)

        # Fetch analytics and propose experiments
        slug_or_id = args.slug if args.slug else args.video_id
        snapshot = orch.analytics(slug_or_id, args.lookback_days)
        proposals = orch.propose_experiments(snapshot, baselines)

        # Output results
        if args.json:
            print(json.dumps(proposals, indent=2))
        else:
            print(f"🔬 Optimization Proposals for {slug_or_id}\n")

            if not proposals:
                print("✅ No optimizations needed - video performing well!")
            else:
                for i, proposal in enumerate(proposals, 1):
                    print(f"{i}. {proposal['hypothesis']}")
                    print(f"   Type: {proposal['type']}")
                    print(f"   Priority: {proposal['priority']}")
                    print(f"   Target KPI: {proposal['kpi']}")
                    print(f"   Target improvement: {proposal['target_delta_pct']:.0f}%")
                    print()

        return 0

    except Exception as e:
        logger.error(f"Optimize propose failed: {e}")
        print(f"❌ Optimization proposal failed: {e}")
        return 1


def _cmd_optimize_create(args: argparse.Namespace) -> int:
    """Handle optimize create experiment command."""
    try:
        cfg = load_config()
        orch = Orchestrator(cfg)

        # Parse variants
        variants = []
        for variant_str in args.variant:
            # Format: "name:type=value,type2=value2"
            parts = variant_str.split(":", 1)
            name = parts[0]
            changes = {}

            if len(parts) > 1:
                for change in parts[1].split(","):
                    if "=" in change:
                        key, value = change.split("=", 1)
                        changes[key] = value

            variants.append({"name": name, "changes": changes})

        # Create experiment
        experiment = orch.create_experiment(
            video_id=args.video_id,
            hypothesis=args.hypothesis,
            variants=variants,
            kpi=args.kpi,
        )

        # Output results
        if args.json:
            print(json.dumps(experiment.model_dump() if hasattr(experiment, 'model_dump') else experiment.__dict__, indent=2, default=str))
        else:
            print(f"✅ Experiment created: {experiment.id}")
            print(f"Video: {experiment.video_id}")
            print(f"Hypothesis: {experiment.hypothesis}")
            print(f"KPI: {experiment.kpi}")
            print(f"Variants: {len(experiment.variants)}")
            for variant in experiment.variants:
                print(f"  - {variant.name}: {variant.changes}")

        return 0

    except Exception as e:
        logger.error(f"Create experiment failed: {e}")
        print(f"❌ Experiment creation failed: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ytfaceless", description="Faceless YouTube automation CLI"
    )
    
    # Global arguments
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    sub = parser.add_subparsers(dest="command", required=True)

    # Assemble command
    p_assemble = sub.add_parser("assemble", help="Assemble video from clips and audio")
    p_assemble.add_argument("--clips", nargs="+", help="Input clip paths", required=True)
    p_assemble.add_argument("--audio", help="Narration audio path", required=True)
    p_assemble.add_argument("--output", help="Output mp4 path", required=True)
    p_assemble.set_defaults(func=_cmd_assemble)
    
    # Health check command
    p_health = sub.add_parser(
        "health",
        help="Run system health check"
    )
    p_health.set_defaults(func=_cmd_health)
    
    # Init command
    p_init = sub.add_parser(
        "init",
        help="Initialize project with required directories and configuration"
    )
    p_init.set_defaults(func=_cmd_init)

    # Phase 4 Commands - Production

    # TTS command
    p_tts = sub.add_parser("tts", help="Generate TTS voiceover for content")
    p_tts.add_argument("--slug", required=True, help="Content slug identifier")
    p_tts.add_argument("--overwrite", action="store_true", help="Overwrite existing audio")
    p_tts.add_argument("--voice-id", help="Override voice ID")
    p_tts.set_defaults(func=_cmd_tts)

    # Subtitles command
    p_subtitles = sub.add_parser("subtitles", help="Generate subtitles from script")
    p_subtitles.add_argument("--slug", required=True, help="Content slug identifier")
    p_subtitles.add_argument("--format", choices=["srt", "vtt"], default="srt", help="Subtitle format")
    p_subtitles.set_defaults(func=_cmd_subtitles)

    # Assets command
    p_assets = sub.add_parser("assets", help="Download assets for content")
    p_assets.add_argument("--slug", required=True, help="Content slug identifier")
    p_assets.add_argument("--parallel", action="store_true", help="Download in parallel")
    p_assets.add_argument("--force", action="store_true", help="Force re-download")
    p_assets.add_argument("--license-filter", nargs="+", default=["CC0", "PD", "CC-BY"],
                         help="Allowed licenses")
    p_assets.set_defaults(func=_cmd_assets)

    # Timeline command
    p_timeline = sub.add_parser("timeline", help="Generate or validate timeline")
    p_timeline.add_argument("--slug", required=True, help="Content slug identifier")
    p_timeline.add_argument("--auto", action="store_true", help="Auto-generate timeline")
    p_timeline.add_argument("--validate", action="store_true", help="Validate existing timeline")
    p_timeline.set_defaults(func=_cmd_timeline)

    # Produce command (runs TTS + Assets + Timeline)
    p_produce = sub.add_parser("produce", help="Run complete production pipeline")
    p_produce.add_argument("--slug", required=True, help="Content slug identifier")
    p_produce.add_argument("--parallel", action="store_true", help="Parallel processing")
    p_produce.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    p_produce.set_defaults(func=_cmd_produce)

    # Phase 5 Commands - Assembly

    # Enhanced assemble command (timeline-based)
    p_assemble_new = sub.add_parser("assemble-timeline", help="Assemble video from timeline")
    p_assemble_new.add_argument("--slug", required=True, help="Content slug identifier")
    p_assemble_new.add_argument("--burn-subtitles", action="store_true", help="Burn subtitles into video")
    p_assemble_new.add_argument("--music-gain", type=float, default=-16.0, help="Music gain in dB")
    p_assemble_new.add_argument("--output", help="Output path (default: content/{slug}/final.mp4)")
    p_assemble_new.add_argument("--validate", action="store_true", help="Validate output after assembly")
    p_assemble_new.set_defaults(func=_cmd_assemble_timeline)

    # Validate command
    p_validate = sub.add_parser("validate", help="Validate video output")
    p_validate.add_argument("--file", required=True, help="Video file to validate")
    p_validate.add_argument("--slug", help="Content slug (to get expected duration)")
    p_validate.add_argument("--duration", type=float, help="Expected duration in seconds")
    p_validate.add_argument("--tolerance", type=float, default=2.0, help="Duration tolerance in seconds")
    p_validate.set_defaults(func=_cmd_validate)

    # Phase 6 Commands - Upload & Publishing

    # Publish command
    p_publish = sub.add_parser("publish", help="Upload video to YouTube with metadata")
    p_publish.add_argument("--slug", required=True, help="Content slug identifier")
    p_publish.add_argument("--video", help="Override video file path")
    p_publish.add_argument("--thumbnail", help="Override thumbnail file path")
    p_publish.add_argument("--privacy", choices=["public", "unlisted", "private"],
                          default="private", help="Privacy status")
    p_publish.add_argument("--schedule", help="Schedule time (RFC3339/ISO format)")
    p_publish.add_argument("--dry-run", action="store_true", help="Simulate upload without execution")
    p_publish.add_argument("--force", action="store_true", help="Force upload even if exists")
    p_publish.add_argument("--no-verify", action="store_true", help="Skip post-upload verification")
    p_publish.set_defaults(func=_cmd_publish)

    # Phase 7 Commands - Analytics & Optimization

    # Analytics fetch command
    p_analytics = sub.add_parser("analytics", help="Fetch and analyze video performance")
    p_analytics_sub = p_analytics.add_subparsers(dest="analytics_command", required=True)

    # Analytics fetch subcommand
    p_analytics_fetch = p_analytics_sub.add_parser("fetch", help="Fetch analytics data")
    p_analytics_fetch.add_argument("--slug", help="Content slug identifier")
    p_analytics_fetch.add_argument("--video-id", help="YouTube video ID")
    p_analytics_fetch.add_argument("--lookback-days", type=int, default=28, help="Days to look back")
    p_analytics_fetch.add_argument("--report", action="store_true", help="Generate full report")
    p_analytics_fetch.set_defaults(func=_cmd_analytics_fetch)

    # Optimize propose command
    p_optimize = sub.add_parser("optimize", help="Optimization and experiments")
    p_optimize_sub = p_optimize.add_subparsers(dest="optimize_command", required=True)

    # Propose experiments subcommand
    p_optimize_propose = p_optimize_sub.add_parser("propose", help="Propose optimization experiments")
    p_optimize_propose.add_argument("--slug", help="Content slug identifier")
    p_optimize_propose.add_argument("--video-id", help="YouTube video ID")
    p_optimize_propose.add_argument("--lookback-days", type=int, default=28, help="Days to look back")
    p_optimize_propose.add_argument("--baselines", help="Path to baselines JSON file")
    p_optimize_propose.set_defaults(func=_cmd_optimize_propose)

    # Create experiment subcommand
    p_optimize_create = p_optimize_sub.add_parser("create", help="Create an experiment")
    p_optimize_create.add_argument("--video-id", required=True, help="YouTube video ID")
    p_optimize_create.add_argument("--hypothesis", required=True, help="Experiment hypothesis")
    p_optimize_create.add_argument("--variant", action="append", required=True,
                                   help="Variant definition (format: name:type=value)")
    p_optimize_create.add_argument("--kpi", default="ctr", help="Primary KPI to optimize")
    p_optimize_create.set_defaults(func=_cmd_optimize_create)

    args = parser.parse_args(argv)
    
    # Setup logging if debug flag is set
    if args.debug:
        setup_logging(debug=True)
    
    try:
        return int(args.func(args))
    except Exception as exc:  # narrow top-level exception for CLI reporting
        logger.exception("Command failed: %s", exc)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
