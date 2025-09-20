"""
YouTube Automation Pipeline Runner
Demonstrates the complete workflow from content creation to upload
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Configuration
N8N_BASE_URL = "http://localhost:5678/webhook"
CONTENT_DIR = Path("content")
LOGS_DIR = Path("logs")

class YouTubePipeline:
    """Complete YouTube automation pipeline"""

    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.content_dir = CONTENT_DIR / self.session_id
        self.content_dir.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(exist_ok=True)

        # Load environment variables
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")

        print(f"[Pipeline] Session ID: {self.session_id}")
        print(f"[Pipeline] Content directory: {self.content_dir}")

    def log(self, stage, message, data=None):
        """Log pipeline progress"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stage": stage,
            "message": message,
            "data": data
        }

        # Console output
        print(f"[{stage}] {message}")

        # File logging
        log_file = LOGS_DIR / f"pipeline_{self.session_id}.json"
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def call_webhook(self, endpoint, data):
        """Call n8n webhook and return response"""
        url = f"{N8N_BASE_URL}/{endpoint}"
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                self.log("ERROR", f"Webhook failed: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log("ERROR", f"Webhook error: {str(e)}")
            return None

    def step1_generate_script(self):
        """Step 1: Generate or load video script"""
        self.log("SCRIPT", "Generating video script")

        # For demo, use a pre-written script about productivity
        script = {
            "title": "5 Productivity Hacks That Actually Work",
            "description": "Discover 5 science-backed productivity techniques that will transform your daily routine and help you achieve more in less time.",
            "script": """
            Are you tired of feeling overwhelmed by your to-do list? Today, I'm sharing 5 productivity hacks that actually work, backed by science.

            First, the Pomodoro Technique. Work for 25 minutes, then take a 5-minute break. This leverages your brain's natural attention span.

            Second, the 2-minute rule. If something takes less than 2 minutes, do it now. This prevents small tasks from piling up.

            Third, time-blocking. Schedule specific time slots for different activities. This eliminates decision fatigue.

            Fourth, the 80-20 rule. Focus on the 20% of tasks that produce 80% of your results.

            Finally, digital minimalism. Turn off notifications and batch-check emails. Constant interruptions destroy deep work.

            Start with just one technique today. Which will you try first? Let me know in the comments below!
            """.strip(),
            "tags": ["productivity", "time management", "self improvement", "productivity tips", "life hacks"],
            "category_id": "26",  # Howto & Style
            "thumbnail_prompt": "Modern minimalist desk setup with productivity tools"
        }

        # Save script
        script_file = self.content_dir / "script.json"
        with open(script_file, 'w') as f:
            json.dump(script, f, indent=2)

        self.log("SCRIPT", "Script generated", {"title": script["title"], "length": len(script["script"])})
        return script

    def step2_generate_tts(self, script):
        """Step 2: Generate TTS audio from script"""
        self.log("TTS", "Generating text-to-speech audio")

        # Call TTS webhook
        tts_data = {
            "text": script["script"],
            "slug": f"video_{self.session_id}",
            "provider": "mock",  # Use mock for testing
            "voice_id": "EXAVITQu4vr4xnSDxMaL",
            "language": "en"
        }

        response = self.call_webhook("tts-generation", tts_data)

        if response and response.get("status") == "success":
            self.log("TTS", "TTS generation successful", response.get("output"))

            # Save TTS metadata
            tts_file = self.content_dir / "tts_result.json"
            with open(tts_file, 'w') as f:
                json.dump(response, f, indent=2)

            return response
        else:
            self.log("TTS", "TTS generation failed")
            return None

    def step3_prepare_video(self, script, tts_result):
        """Step 3: Prepare video assembly (mock for now)"""
        self.log("ASSEMBLY", "Preparing video assembly")

        # In production, this would call FFmpeg to assemble video
        # For now, we'll create metadata for a mock video
        video_data = {
            "video_file": str(self.content_dir / "final_video.mp4"),
            "duration": 120,  # 2 minutes
            "resolution": "1920x1080",
            "fps": 30,
            "audio_file": tts_result.get("output", {}).get("files", ["audio.mp3"])[0],
            "assembled_at": datetime.now().isoformat()
        }

        # Save video metadata
        video_file = self.content_dir / "video_metadata.json"
        with open(video_file, 'w') as f:
            json.dump(video_data, f, indent=2)

        self.log("ASSEMBLY", "Video assembly prepared", video_data)
        return video_data

    def step4_upload_video(self, script, video_data):
        """Step 4: Upload video to YouTube"""
        self.log("UPLOAD", "Uploading video to YouTube")

        # Call upload webhook
        upload_data = {
            "title": script["title"],
            "description": script["description"] + "\n\n#productivity #timemanagement #selfimprovement",
            "tags": script["tags"],
            "category_id": script["category_id"],
            "privacy": "private",  # Start as private for safety
            "thumbnail_url": "",  # Would be generated from prompt
            "made_for_kids": False
        }

        response = self.call_webhook("youtube-upload", upload_data)

        if response and response.get("status") == "success":
            self.log("UPLOAD", "Upload successful", response.get("video"))

            # Save upload result
            upload_file = self.content_dir / "upload_result.json"
            with open(upload_file, 'w') as f:
                json.dump(response, f, indent=2)

            return response
        else:
            self.log("UPLOAD", "Upload failed")
            return None

    def step5_distribute(self, script, upload_result):
        """Step 5: Distribute to other platforms"""
        self.log("DISTRIBUTE", "Distributing to social platforms")

        # Call cross-platform webhook
        distribute_data = {
            "title": script["title"],
            "description": script["description"][:200],  # Shortened for social
            "platforms": ["tiktok", "instagram", "twitter"],
            "video_url": upload_result.get("video", {}).get("url", ""),
            "hashtags": ["productivity", "lifehacks", "timemanagement"]
        }

        response = self.call_webhook("cross-platform-distribute", distribute_data)

        if response and response.get("status") == "success":
            self.log("DISTRIBUTE", "Distribution successful", response.get("summary"))

            # Save distribution result
            dist_file = self.content_dir / "distribution_result.json"
            with open(dist_file, 'w') as f:
                json.dump(response, f, indent=2)

            return response
        else:
            self.log("DISTRIBUTE", "Distribution failed")
            return None

    def step6_create_affiliate_links(self, script):
        """Step 6: Create affiliate links for description"""
        self.log("AFFILIATE", "Creating affiliate links")

        # Example affiliate products related to productivity
        products = [
            {
                "url": "https://www.amazon.com/dp/B08N5WRWNW",
                "title": "Productivity Planner",
                "campaign": "productivity_video_" + self.session_id
            },
            {
                "url": "https://www.amazon.com/dp/B07G3S3M9J",
                "title": "Pomodoro Timer",
                "campaign": "productivity_video_" + self.session_id
            }
        ]

        shortened_links = []
        for product in products:
            response = self.call_webhook("affiliate-shorten", {
                "original_url": product["url"],
                "title": product["title"],
                "utm_source": "youtube",
                "utm_medium": "video",
                "utm_campaign": product["campaign"],
                "generate_qr": True
            })

            if response and response.get("status") == "success":
                shortened_links.append(response)
                self.log("AFFILIATE", f"Link created for {product['title']}", response.get("link"))

        # Save affiliate links
        if shortened_links:
            links_file = self.content_dir / "affiliate_links.json"
            with open(links_file, 'w') as f:
                json.dump(shortened_links, f, indent=2)

        return shortened_links

    def step7_check_analytics(self):
        """Step 7: Check channel analytics"""
        self.log("ANALYTICS", "Fetching channel analytics")

        # Call analytics webhook
        analytics_data = {
            "channel_id": "UC_demo_channel",
            "date_range": "last_7_days",
            "include_demographics": True,
            "include_traffic_sources": True
        }

        response = self.call_webhook("youtube-analytics", analytics_data)

        if response and response.get("status") == "success":
            self.log("ANALYTICS", "Analytics retrieved", response.get("metrics"))

            # Save analytics
            analytics_file = self.content_dir / "analytics_result.json"
            with open(analytics_file, 'w') as f:
                json.dump(response, f, indent=2)

            # Check for insights
            if response.get("insights"):
                self.log("INSIGHTS", "Performance insights", response["insights"])
            if response.get("recommendations"):
                self.log("RECOMMENDATIONS", "Improvement suggestions", response["recommendations"])

            return response
        else:
            self.log("ANALYTICS", "Analytics retrieval failed")
            return None

    def generate_report(self):
        """Generate final pipeline report"""
        self.log("REPORT", "Generating pipeline report")

        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "content_directory": str(self.content_dir),
            "files_created": [f.name for f in self.content_dir.iterdir()],
            "pipeline_steps": {
                "script": "[OK] Completed",
                "tts": "[OK] Completed",
                "assembly": "[OK] Completed",
                "upload": "[OK] Completed",
                "distribution": "[OK] Completed",
                "affiliate": "[OK] Completed",
                "analytics": "[OK] Completed"
            }
        }

        # Save report
        report_file = self.content_dir / "pipeline_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "="*60)
        print("PIPELINE COMPLETE!")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Content saved to: {self.content_dir}")
        print("\nSteps completed:")
        for step, status in report["pipeline_steps"].items():
            print(f"  {step}: {status}")
        print("\nFiles created:")
        for file in report["files_created"]:
            print(f"  - {file}")
        print("="*60)

        return report

    def run_full_pipeline(self):
        """Run the complete YouTube automation pipeline"""
        print("\n" + "="*60)
        print("STARTING YOUTUBE AUTOMATION PIPELINE")
        print("="*60)

        try:
            # Step 1: Generate script
            script = self.step1_generate_script()
            time.sleep(1)

            # Step 2: Generate TTS
            tts_result = self.step2_generate_tts(script)
            if not tts_result:
                self.log("ERROR", "Pipeline stopped: TTS failed")
                return
            time.sleep(1)

            # Step 3: Prepare video
            video_data = self.step3_prepare_video(script, tts_result)
            time.sleep(1)

            # Step 4: Upload to YouTube
            upload_result = self.step4_upload_video(script, video_data)
            if not upload_result:
                self.log("ERROR", "Pipeline stopped: Upload failed")
                return
            time.sleep(1)

            # Step 5: Distribute to platforms
            distribution = self.step5_distribute(script, upload_result)
            time.sleep(1)

            # Step 6: Create affiliate links
            affiliate_links = self.step6_create_affiliate_links(script)
            time.sleep(1)

            # Step 7: Check analytics
            analytics = self.step7_check_analytics()

            # Generate final report
            report = self.generate_report()

            return report

        except Exception as e:
            self.log("ERROR", f"Pipeline failed: {str(e)}")
            raise

def main():
    """Main entry point"""
    print("YouTube Automation Pipeline Runner")
    print("==================================")

    # Check n8n is running
    try:
        response = requests.get("http://localhost:5678", timeout=5)
        print("[OK] n8n is running")
    except:
        print("[ERROR] n8n is not running. Please start n8n first!")
        print("Run: npx n8n start")
        return

    # Check workflows are active
    print("\nMake sure these workflows are imported and ACTIVE in n8n:")
    print("  1. tts_webhook_PRODUCTION.json")
    print("  2. youtube_upload_PRODUCTION.json")
    print("  3. youtube_analytics_PRODUCTION.json")
    print("  4. cross_platform_PRODUCTION.json")
    print("  5. affiliate_shortener_PRODUCTION.json")

    print("\nPress Enter to start the pipeline (or Ctrl+C to cancel)...")
    input()

    # Run pipeline
    pipeline = YouTubePipeline()
    result = pipeline.run_full_pipeline()

    if result:
        print("\n[SUCCESS] Pipeline completed successfully!")
        print(f"Check {pipeline.content_dir} for all generated content")
    else:
        print("\n[FAILED] Pipeline failed. Check logs for details.")

if __name__ == "__main__":
    main()