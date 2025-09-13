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


# Phase 8 Commands - Monetization & Scale

def _cmd_monetize_affiliates(args: argparse.Namespace) -> int:
    """Handle monetize affiliates command."""
    try:
        import asyncio
        from .monetization.affiliates import inject_affiliate_links

        config = load_enhanced_config()

        # Load existing description
        content_dir = config.directories.content_dir / args.slug
        metadata_path = content_dir / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                # Handle both string and dict description formats
                desc_data = metadata.get("description", "")
                if isinstance(desc_data, dict):
                    description = desc_data.get("text", "")
                else:
                    description = str(desc_data)
                niche = metadata.get("niche")
        else:
            description = ""
            niche = None

        # Inject affiliate links
        result = asyncio.run(inject_affiliate_links(
            config,
            args.slug,
            description,
            niche=niche,
            pin_comment=args.pin_comment,
            dry_run=args.dry_run
        ))

        if args.dry_run:
            print(f"[DRY RUN] Would inject affiliate links for {args.slug}")
            if "placements" in result:
                print(f"Placements: {len(result['placements'])}")
        else:
            # Save updated metadata (maintain dict structure for description)
            if isinstance(metadata.get("description"), dict):
                metadata["description"]["text"] = result["description"]
            else:
                metadata["description"] = {"text": result["description"]}
            if "pinned_comment" in result:
                metadata["pinned_comment"] = result["pinned_comment"]

            # Store structured affiliate links in monetization settings
            if "affiliate_links" in result:
                if "monetization_settings" not in metadata:
                    metadata["monetization_settings"] = {}
                metadata["monetization_settings"]["affiliate_links"] = result["affiliate_links"]

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✅ Injected affiliate links for {args.slug}")
            if "pinned_comment" in result:
                print("📌 Generated pinned comment")

        return 0

    except Exception as e:
        logger.error(f"Affiliate injection failed: {e}")
        print(f"ERROR: {e}")
        return 1


def _cmd_monetize_sponsor(args: argparse.Namespace) -> int:
    """Handle monetize sponsor command."""
    try:
        from .monetization.sponsorships import apply_sponsorship_disclosure

        config = load_enhanced_config()

        # Load existing metadata
        content_dir = config.directories.content_dir / args.slug
        metadata_path = content_dir / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                # Handle both string and dict description formats
                desc_data = metadata.get("description", "")
                if isinstance(desc_data, dict):
                    description = desc_data.get("text", "")
                else:
                    description = str(desc_data)
                niche = metadata.get("niche")
                duration = metadata.get("duration_seconds", 600)
        else:
            description = ""
            niche = None
            duration = 600

        # Apply sponsorship disclosure
        result = apply_sponsorship_disclosure(
            config,
            args.slug,
            description,
            video_duration=duration,
            niche=niche,
            apply_overlay=args.apply_overlay,
            dry_run=args.dry_run
        )

        if args.dry_run:
            print(f"[DRY RUN] Would apply sponsorship for {args.slug}")
            if "deals" in result:
                print(f"Active deals: {len(result['deals'])}")
        else:
            # Save updated metadata (maintain dict structure for description)
            if isinstance(metadata.get("description"), dict):
                metadata["description"]["text"] = result["description"]
            else:
                metadata["description"] = {"text": result["description"]}
            if "overlay_markers" in result:
                metadata["overlay_markers"] = result["overlay_markers"]
            if "monetization_settings" in result:
                metadata["monetization_settings"] = result["monetization_settings"]

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✅ Applied sponsorship disclosure for {args.slug}")
            if "overlay_markers" in result:
                print(f"📊 Added {len(result['overlay_markers'])} overlay markers")

        return 0

    except Exception as e:
        logger.error(f"Sponsorship application failed: {e}")
        print(f"ERROR: {e}")
        return 1


def _cmd_shorts_generate(args: argparse.Namespace) -> int:
    """Handle shorts generate command."""
    try:
        from .production.shorts import generate_shorts

        config = load_enhanced_config()

        # Parse segments if provided
        segments = None
        if args.segments:
            segments = []
            for seg in args.segments.split(','):
                start, end = seg.split('-')
                # Convert MM:SS to seconds
                def to_seconds(time_str):
                    parts = time_str.split(':')
                    if len(parts) == 2:
                        return int(parts[0]) * 60 + int(parts[1])
                    return int(parts[0])

                segments.append((to_seconds(start), to_seconds(end)))

        # Generate Shorts
        shorts = generate_shorts(
            config,
            args.slug,
            count=args.count,
            segments=segments,
            burn_captions=args.burn_captions,
            dry_run=args.dry_run
        )

        if args.dry_run:
            print(f"[DRY RUN] Would generate {len(shorts)} Shorts for {args.slug}")
        else:
            print(f"✅ Generated {len(shorts)} Shorts for {args.slug}")
            for short in shorts:
                print(f"  - {short.segment_id}: {short.hook_type} ({short.start_sec:.0f}s-{short.end_sec:.0f}s)")

        return 0

    except Exception as e:
        logger.error(f"Shorts generation failed: {e}")
        print(f"ERROR: {e}")
        return 1


def _cmd_revenue_report(args: argparse.Namespace) -> int:
    """Handle revenue report command."""
    try:
        from .monetization.revenue import generate_revenue_report

        config = load_enhanced_config()

        # Generate revenue report
        report = generate_revenue_report(
            config,
            month=args.month,
            output_json=args.json
        )

        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print(f"📊 Revenue Report - {report['month']}")
            print(f"Total Revenue: {report['total_revenue']}")
            print(f"Average RPM: {report['rpm']}")
            if report['top_video']:
                print(f"Top Video: {report['top_video']['slug']} (${report['top_video']['revenue']:.2f})")
            print(f"\nFull report: {report['report_path']}")

        return 0

    except Exception as e:
        logger.error(f"Revenue report generation failed: {e}")
        print(f"ERROR: {e}")
        return 1


def _cmd_distribute_post(args: argparse.Namespace) -> int:
    """Handle distribute post command."""
    try:
        import asyncio
        from .distribution.cross_platform import distribute_content

        config = load_enhanced_config()

        # Parse platforms
        platforms = args.platforms.split(',') if args.platforms else ["tiktok", "instagram", "x"]

        # Distribute content
        result = asyncio.run(distribute_content(
            config,
            args.slug,
            platforms=platforms,
            schedule=False,
            dry_run=args.dry_run
        ))

        if args.dry_run:
            print(f"[DRY RUN] Would distribute {args.slug}")
            for platform, details in result.items():
                if platform != "status":
                    print(f"  {platform}: {details}")
        else:
            print(f"✅ Distributed {args.slug}")
            for platform, details in result.items():
                if platform != "status":
                    print(f"  {platform}: {details.get('status', 'unknown')}")

        return 0

    except Exception as e:
        logger.error(f"Failed to distribute content: {e}")
        return 1


def _cmd_distribute_schedule(args: argparse.Namespace) -> int:
    """Handle distribute schedule command."""
    try:
        import asyncio
        from datetime import datetime
        from .distribution.cross_platform import distribute_content

        config = load_enhanced_config()

        # Parse platforms
        platforms = args.platforms.split(',') if args.platforms else ["tiktok", "instagram", "x"]

        # Parse base time if provided
        schedule_time = None
        if args.base_time:
            schedule_time = datetime.fromisoformat(args.base_time)

        # Schedule distribution
        result = asyncio.run(distribute_content(
            config,
            args.slug,
            platforms=platforms,
            schedule=True,
            schedule_time=schedule_time,
            dry_run=False
        ))

        print(f"📅 Scheduled distribution for {args.slug}")
        for platform, time_info in result.items():
            if platform != "status":
                print(f"  {platform}: {time_info}")

        return 0

    except Exception as e:
        logger.error(f"Failed to schedule distribution: {e}")
        return 1


def _cmd_distribute(args: argparse.Namespace) -> int:
    """Legacy distribute command handler - kept for compatibility."""
    # This function is kept for backward compatibility
    # The new subcommands handle the actual functionality
    return _cmd_distribute_post(args) if not hasattr(args, 'schedule') or not args.schedule else _cmd_distribute_schedule(args)


def _cmd_localize_run(args: argparse.Namespace) -> int:
    """Handle localize run command."""
    try:
        import asyncio
        from .localization.translator import translate_content

        config = load_enhanced_config()

        # Parse languages
        languages = args.languages.split(',') if args.languages else []

        # Localize content
        result = asyncio.run(translate_content(
            config,
            args.slug,
            target_languages=languages,
            generate_audio=args.audio,
            generate_subtitles=args.subtitles,
            dry_run=args.dry_run
        ))

        if args.dry_run:
            print(f"[DRY RUN] Would localize {args.slug} to: {', '.join(languages)}")
        else:
            print(f"✅ Localized {args.slug}")
            for lang, details in result.get("languages", {}).items():
                status = details.get("status", "unknown")
                print(f"  {lang}: {status}")
                if status == "success":
                    if "metadata" in details:
                        print(f"    Metadata: {details['metadata']}")
                    if "subtitles" in details:
                        print(f"    Subtitles: {details['subtitles']}")
                    if "audio" in details:
                        print(f"    Audio: {details['audio']}")

        return 0

    except Exception as e:
        logger.error(f"Failed to localize content: {e}")
        return 1


def _cmd_localize(args: argparse.Namespace) -> int:
    """Legacy localize command handler - kept for compatibility."""
    # Convert old format to new format
    if hasattr(args, 'languages') and isinstance(args.languages, list):
        args.languages = ','.join(args.languages)
    return _cmd_localize_run(args)


def _cmd_safety_check(args: argparse.Namespace) -> int:
    """Handle safety check command."""
    try:
        import asyncio
        from .guardrails.safety_checker import check_content_safety, validate_compliance

        config = load_enhanced_config()

        if args.fix:
            # Validate and fix
            result = asyncio.run(validate_compliance(
                config,
                args.slug,
                fix_issues=True
            ))
            print(f"✅ Compliance check for {args.slug}")
            print(f"  Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"  Score: {result['score']}/100")
            if result.get('fixed'):
                print(f"  Fixed issues: Yes")
        else:
            # Just check
            result = asyncio.run(check_content_safety(
                config,
                args.slug,
                platforms=["youtube"],  # Default to YouTube
                run_ai_check=args.ai
            ))
            print(f"🔍 Safety check for {args.slug}")
            print(f"  Status: {'PASS' if result.passed else 'FAIL'}")
            print(f"  Score: {result.score}/100")

            if result.violations:
                print("\n  Violations:")
                for v in result.violations[:5]:  # Show first 5
                    print(f"    - {v.get('type')}: {v.get('issue', v.get('term', 'unknown'))}")

            if result.warnings:
                print("\n  Warnings:")
                for w in result.warnings[:3]:  # Show first 3
                    if isinstance(w, dict):
                        print(f"    - {w.get('type')}: {w.get('topic', 'unknown')}")
                    else:
                        print(f"    - {w}")

        return 0

    except Exception as e:
        logger.error(f"Failed to check content safety: {e}")
        return 1


def _cmd_safety(args: argparse.Namespace) -> int:
    """Legacy safety command handler - kept for compatibility."""
    # Convert old format to new format
    if not hasattr(args, 'ai'):
        args.ai = getattr(args, 'ai_check', False)
    return _cmd_safety_check(args)


def _cmd_calendar_schedule(args: argparse.Namespace) -> int:
    """Handle calendar schedule command."""
    try:
        import asyncio
        from datetime import datetime
        from .schedule.calendar import schedule_content

        config = load_enhanced_config()

        # Parse date if provided
        publish_date = None
        if args.date:
            publish_date = datetime.strptime(args.date, "%Y-%m-%d %H:%M")

        # Schedule content
        result = asyncio.run(schedule_content(
            config,
            args.slug,
            publish_date=publish_date,
            template=args.template,
            dry_run=args.dry_run
        ))

        if args.dry_run:
            print(f"[DRY RUN] Would schedule {args.slug}")
            if "would_schedule" in result:
                print(f"  Date: {result['would_schedule']['scheduled_time']}")
        else:
            print(f"📅 Scheduled {args.slug}")
            print(f"  Date: {result['scheduled_time']}")
            if result.get('conflicts_resolved'):
                print(f"  Note: Conflicts were resolved automatically")

        return 0

    except Exception as e:
        logger.error(f"Failed to schedule content: {e}")
        return 1


def _cmd_calendar_view(args: argparse.Namespace) -> int:
    """Handle calendar view command."""
    try:
        from .schedule.calendar import get_publishing_schedule

        config = load_enhanced_config()

        # Get schedule
        result = get_publishing_schedule(
            config,
            days_ahead=args.days,
            analyze=args.analyze
        )

        print(f"📅 Content Schedule (next {args.days} days)")
        print("-" * 40)

        if result['upcoming']:
            for item in result['upcoming']:
                time = item.get('scheduled_time', item.get('published_time'))
                status = item.get('status', 'scheduled')
                print(f"  {time[:16]} - {item['slug']} [{status}]")
        else:
            print("  No scheduled content")

        if args.analyze and 'analytics' in result:
            analytics = result['analytics']
            print("\n📊 Publishing Analytics")
            print("-" * 40)

            if analytics.get('status') != 'no_data':
                print(f"  Total published: {analytics.get('total_published', 0)}")
                print(f"  Avg views (24h): {analytics.get('average_views_24h', 0):.0f}")

                if analytics.get('best_days'):
                    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    best = analytics['best_days'][0]
                    print(f"  Best day: {days[best[0]]} ({best[1]:.0f} avg views)")

                if analytics.get('recommendations'):
                    print("\n  Recommendations:")
                    for rec in analytics['recommendations']:
                        print(f"    - {rec}")

        return 0

    except Exception as e:
        logger.error(f"Failed to view calendar: {e}")
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

    # Phase 8 Commands - Monetization & Scale

    # Monetize command group
    p_monetize = sub.add_parser("monetize", help="Monetization commands")
    p_monetize_sub = p_monetize.add_subparsers(dest="monetize_command", required=True)

    # Monetize affiliates subcommand
    p_monetize_affiliates = p_monetize_sub.add_parser(
        "affiliates",
        help="Inject affiliate links into video metadata"
    )
    p_monetize_affiliates.add_argument("--slug", required=True, help="Content slug")
    p_monetize_affiliates.add_argument("--pin-comment", action="store_true",
                                       help="Generate pinned comment with affiliate links")
    p_monetize_affiliates.add_argument("--dry-run", action="store_true",
                                       help="Preview changes without applying")
    p_monetize_affiliates.set_defaults(func=_cmd_monetize_affiliates)

    # Monetize sponsor subcommand
    p_monetize_sponsor = p_monetize_sub.add_parser(
        "sponsor",
        help="Apply sponsorship disclosure and markers"
    )
    p_monetize_sponsor.add_argument("--slug", required=True, help="Content slug")
    p_monetize_sponsor.add_argument("--apply-overlay", action="store_true",
                                    help="Add overlay markers to timeline")
    p_monetize_sponsor.add_argument("--dry-run", action="store_true",
                                    help="Preview changes without applying")
    p_monetize_sponsor.set_defaults(func=_cmd_monetize_sponsor)

    # Shorts command
    p_shorts = sub.add_parser("shorts", help="YouTube Shorts commands")
    p_shorts_sub = p_shorts.add_subparsers(dest="shorts_command", required=True)

    # Shorts generate subcommand
    p_shorts_generate = p_shorts_sub.add_parser(
        "generate",
        help="Generate Shorts from long-form video"
    )
    p_shorts_generate.add_argument("--slug", required=True, help="Content slug")
    p_shorts_generate.add_argument("--count", type=int, default=3,
                                   help="Number of Shorts to generate (default: 3)")
    p_shorts_generate.add_argument("--segments",
                                   help="Specific segments (format: MM:SS-MM:SS,MM:SS-MM:SS)")
    p_shorts_generate.add_argument("--burn-captions", action="store_true", default=True,
                                   help="Burn captions into video (default: True)")
    p_shorts_generate.add_argument("--dry-run", action="store_true",
                                   help="Preview without generating files")
    p_shorts_generate.set_defaults(func=_cmd_shorts_generate)

    # Revenue command
    p_revenue = sub.add_parser("revenue", help="Revenue tracking and reporting")
    p_revenue_sub = p_revenue.add_subparsers(dest="revenue_command", required=True)

    # Revenue report subcommand
    p_revenue_report = p_revenue_sub.add_parser(
        "report",
        help="Generate monthly revenue report"
    )
    p_revenue_report.add_argument("--month",
                                  help="Report month (YYYY-MM format, default: current month)")
    p_revenue_report.add_argument("--json", action="store_true",
                                  help="Output report as JSON")
    p_revenue_report.set_defaults(func=_cmd_revenue_report)

    # DISTRIBUTE command with subparsers
    p_distribute = sub.add_parser("distribute", help="Cross-platform distribution")
    distrib_sub = p_distribute.add_subparsers(dest="distribute_command", required=True)

    p_distribute_post = distrib_sub.add_parser("post", help="Post immediately")
    p_distribute_post.add_argument("--slug", required=True, help="Video slug to distribute")
    p_distribute_post.add_argument("--platforms", default="tiktok,instagram,x",
                                  help="Comma-separated platforms")
    p_distribute_post.add_argument("--dry-run", action="store_true",
                                  help="Simulate without distributing")
    p_distribute_post.set_defaults(func=_cmd_distribute_post)

    p_distribute_schedule = distrib_sub.add_parser("schedule", help="Schedule distribution")
    p_distribute_schedule.add_argument("--slug", required=True, help="Video slug to schedule")
    p_distribute_schedule.add_argument("--platforms", default="tiktok,instagram,x",
                                      help="Comma-separated platforms")
    p_distribute_schedule.add_argument("--base-time", help="ISO time (UTC)")
    p_distribute_schedule.set_defaults(func=_cmd_distribute_schedule)

    # LOCALIZE command with subparsers
    p_localize = sub.add_parser("localize", help="Localization")
    localize_sub = p_localize.add_subparsers(dest="localize_command", required=True)

    p_localize_run = localize_sub.add_parser("run", help="Translate content")
    p_localize_run.add_argument("--slug", required=True, help="Video slug to localize")
    p_localize_run.add_argument("--languages", required=True,
                               help="Comma-separated languages (e.g., es,de,fr)")
    p_localize_run.add_argument("--audio", action="store_true",
                               help="Generate voice-overs")
    p_localize_run.add_argument("--subtitles", action="store_true", default=True,
                               help="Generate subtitles")
    p_localize_run.add_argument("--dry-run", action="store_true",
                               help="Simulate without localizing")
    p_localize_run.set_defaults(func=_cmd_localize_run)

    # SAFETY command with subparsers
    p_safety = sub.add_parser("safety", help="Brand safety checks")
    safety_sub = p_safety.add_subparsers(dest="safety_command", required=True)

    p_safety_check = safety_sub.add_parser("check", help="Run safety checks")
    p_safety_check.add_argument("--slug", required=True, help="Video slug to check")
    p_safety_check.add_argument("--ai", action="store_true",
                               help="Run AI-powered moderation")
    p_safety_check.add_argument("--fix", action="store_true",
                               help="Attempt to fix issues")
    p_safety_check.set_defaults(func=_cmd_safety_check)

    # Calendar command
    p_calendar = sub.add_parser("calendar", help="Content calendar management")
    p_calendar_sub = p_calendar.add_subparsers(dest="calendar_command", required=True)

    # Calendar schedule subcommand
    p_calendar_schedule = p_calendar_sub.add_parser(
        "schedule",
        help="Schedule content for publishing"
    )
    p_calendar_schedule.add_argument("slug", help="Video slug to schedule")
    p_calendar_schedule.add_argument("--date",
                                    help="Publish date (YYYY-MM-DD HH:MM format)")
    p_calendar_schedule.add_argument("--template",
                                    choices=["daily", "weekday", "weekend", "optimal"],
                                    help="Use scheduling template")
    p_calendar_schedule.add_argument("--dry-run", action="store_true",
                                    help="Simulate without scheduling")
    p_calendar_schedule.set_defaults(func=_cmd_calendar_schedule)

    # Calendar view subcommand
    p_calendar_view = p_calendar_sub.add_parser(
        "view",
        help="View upcoming schedule"
    )
    p_calendar_view.add_argument("--days", type=int, default=7,
                                help="Days ahead to show")
    p_calendar_view.add_argument("--analyze", action="store_true",
                                help="Include analytics")
    p_calendar_view.set_defaults(func=_cmd_calendar_view)

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
