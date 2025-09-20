#!/usr/bin/env python
"""
Automated YouTube Production Pipeline - No User Input Required
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

class AutomatedYouTubePipeline:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.content_dir = Path(f"content/{self.session_id}")
        self.content_dir.mkdir(parents=True, exist_ok=True)

        # Pre-selected options for automation
        self.selected_niche = 4  # Educational Content
        self.selected_idea = 1   # First idea
        self.auto_upload = False  # Don't auto-upload to YouTube

    def run(self):
        """Run the complete automated pipeline"""
        print("\n" + "="*60)
        print("AUTOMATED YOUTUBE PRODUCTION PIPELINE")
        print("="*60)
        print(f"Session: {self.session_id}")
        print(f"Output: {self.content_dir}")

        try:
            # Phase 1: Environment Check
            print("\n" + "="*60)
            print("PHASE 1: ENVIRONMENT CHECK")
            print("="*60)
            self.check_environment()

            # Phase 2: Research & Idea Generation
            print("\n" + "="*60)
            print("PHASE 2: RESEARCH & NICHE SELECTION")
            print("="*60)
            ideas = self.generate_ideas()

            # Phase 3: Scriptwriting
            print("\n" + "="*60)
            print("PHASE 3: SCRIPTWRITING & SEO")
            print("="*60)
            script, metadata = self.write_script(ideas[0])

            # Phase 4: TTS Production
            print("\n" + "="*60)
            print("PHASE 4: TTS PRODUCTION")
            print("="*60)
            audio_file = self.generate_tts(script)

            # Phase 5: Video Assembly
            print("\n" + "="*60)
            print("PHASE 5: VIDEO ASSEMBLY")
            print("="*60)
            video_file = self.assemble_video(audio_file, metadata)

            # Phase 6: Upload (Optional)
            if self.auto_upload:
                print("\n" + "="*60)
                print("PHASE 6: YOUTUBE UPLOAD")
                print("="*60)
                self.upload_to_youtube(video_file, metadata)
            else:
                print("\n[INFO] Skipping YouTube upload (auto_upload=False)")
                print(f"[INFO] Video saved to: {video_file}")

            print("\n" + "="*60)
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"Session: {self.session_id}")
            print(f"Output: {self.content_dir}")
            print(f"Video: {video_file}")

        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        return True

    def check_environment(self):
        """Check required environment variables and tools"""
        checks = []

        # Python version
        version = sys.version_info
        if version.major >= 3 and version.minor >= 12:
            print("[OK] Python 3.12+")
        else:
            print(f"[WARNING] Python {version.major}.{version.minor} (3.12+ recommended)")

        # FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            print("[OK] FFmpeg")
        except:
            print("[ERROR] FFmpeg not found")
            raise Exception("FFmpeg is required")

        # Environment variables
        if os.getenv("YOUTUBE_API_KEY"):
            print("[OK] YouTube API key")
        else:
            print("[WARNING] YouTube API key not set")

        if os.getenv("ELEVENLABS_API_KEY"):
            print("[OK] ElevenLabs API key")
        else:
            print("[INFO] ElevenLabs API key not set (will use Google TTS)")

    def generate_ideas(self):
        """Generate content ideas for selected niche"""
        niches = {
            1: {
                "name": "Personal Finance & Investing",
                "rpm": "$15-45",
                "ideas": [
                    "5 Money Mistakes That Keep You Poor (Fix Them Today)",
                    "The 50/30/20 Budget Rule Explained in 3 Minutes",
                    "How to Start Investing with Just $100",
                    "Passive Income Ideas That Actually Work in 2025",
                    "Credit Score Hacks Banks Don't Want You to Know"
                ]
            },
            2: {
                "name": "Technology & AI",
                "rpm": "$10-30",
                "ideas": [
                    "10 AI Tools That Will Replace Your Job (And How to Use Them)",
                    "ChatGPT Tricks That Will 10x Your Productivity",
                    "The Future of Work: Skills You Need by 2026",
                    "How to Make Money with AI (Complete Guide)",
                    "Tech Gadgets Under $50 That Changed My Life"
                ]
            },
            3: {
                "name": "Health & Wellness",
                "rpm": "$8-25",
                "ideas": [
                    "The 5-Minute Morning Routine That Changed My Life",
                    "Science-Backed Ways to Fall Asleep in 2 Minutes",
                    "Foods That Boost Brain Power (Backed by Science)",
                    "How to Build Habits That Actually Stick",
                    "The Japanese Secret to Living Past 100"
                ]
            },
            4: {
                "name": "Educational Content",
                "rpm": "$7-20",
                "ideas": [
                    "10 Historical Facts That Will Blow Your Mind",
                    "How to Learn Anything 10x Faster (Feynman Technique)",
                    "5 Skills That Will Be Essential in 2026",
                    "The Science of Getting Lucky (It's Not Random)",
                    "Why School Didn't Teach You This About Money"
                ]
            }
        }

        niche = niches[self.selected_niche]
        print(f"Selected Niche: {niche['name']}")
        print(f"RPM Range: {niche['rpm']}")
        print(f"\nGenerated Ideas:")
        for i, idea in enumerate(niche['ideas'], 1):
            print(f"  {i}. {idea}")

        print(f"\nAuto-selected idea #{self.selected_idea}: {niche['ideas'][self.selected_idea-1]}")

        # Save ideas
        ideas_file = Path("data/ideas") / f"ideas_{self.session_id}.json"
        ideas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ideas_file, "w") as f:
            json.dump({
                "session": self.session_id,
                "niche": niche['name'],
                "ideas": niche['ideas'],
                "selected": self.selected_idea
            }, f, indent=2)
        print(f"[SAVED] Ideas saved to {ideas_file}")

        return niche['ideas']

    def write_script(self, idea):
        """Generate script and metadata for the selected idea"""
        print(f"Generating script for: {idea}")

        # Create a simple script template
        script = f"""# {idea}

## Hook (0-5 seconds)
Did you know that {idea.lower()}? In the next 60 seconds, I'm going to reveal something that will completely change your perspective.

## Main Content (5-50 seconds)
Let me share with you the most incredible facts about this topic.

First, consider this amazing discovery...
[Content continues with engaging facts and insights]

Second, scientists have recently found that...
[More compelling information]

Finally, and this is the most mind-blowing part...
[Dramatic revelation]

## Call to Action (50-60 seconds)
If you found this valuable, make sure to subscribe for more amazing content.
And remember, knowledge is power - share this with someone who needs to hear it today!

What fact surprised you the most? Let me know in the comments below!
"""

        # Save script
        script_file = self.content_dir / "script.md"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"[SAVED] Script: {script_file}")

        # Generate metadata
        metadata = {
            "title": idea,
            "description": f"Discover {idea.lower()}. This video reveals fascinating insights that will change how you think. Perfect for curious minds!",
            "tags": [
                "educational", "facts", "learning", "knowledge", "amazing facts",
                "mind blowing", "science", "history", "discovery", "2025"
            ],
            "category": "Education",
            "language": "en",
            "duration": "60",
            "thumbnail_text": idea.split("(")[0].strip()
        }

        # Save metadata
        metadata_file = self.content_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"[SAVED] Metadata: {metadata_file}")

        return script, metadata

    def generate_tts(self, script):
        """Generate TTS audio from script"""
        # Extract text from script (remove markdown headers)
        lines = script.split("\n")
        text_lines = [line for line in lines if not line.startswith("#") and line.strip()]
        text = " ".join(text_lines)

        audio_file = self.content_dir / "narration.mp3"

        # Try ElevenLabs first
        if os.getenv("ELEVENLABS_API_KEY"):
            print("Attempting ElevenLabs TTS...")
            try:
                from test_elevenlabs_api import test_elevenlabs_tts
                if test_elevenlabs_tts(text, str(audio_file)):
                    print(f"[SUCCESS] ElevenLabs TTS saved to {audio_file}")
                    return audio_file
            except Exception as e:
                print(f"[WARNING] ElevenLabs failed: {e}")

        # Fallback to Google TTS
        print("Using Google TTS (free)...")
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(audio_file))
            print(f"[SUCCESS] Google TTS saved to {audio_file}")
            return audio_file
        except ImportError:
            print("[INFO] Installing gTTS...")
            subprocess.run([sys.executable, "-m", "pip", "install", "gtts"], check=True)
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(audio_file))
            print(f"[SUCCESS] Google TTS saved to {audio_file}")
            return audio_file

    def assemble_video(self, audio_file, metadata):
        """Create video from audio and metadata"""
        print("Using FFmpeg to create video...")

        video_file = self.content_dir / "final.mp4"

        # Get audio duration
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())

        # Create a simple video with colored background and text overlay
        title_text = metadata['title'].replace("'", "\\'")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=blue:s=1920x1080:d={duration}",
            "-i", str(audio_file),
            "-vf", f"drawtext=text='{title_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            str(video_file)
        ]

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] Video created: {video_file}")
            return video_file
        else:
            print(f"[ERROR] FFmpeg failed: {result.stderr}")
            raise Exception("Video assembly failed")

    def upload_to_youtube(self, video_file, metadata):
        """Upload video to YouTube (requires authentication)"""
        print("Preparing upload...")
        print(f"Title: {metadata['title']}")
        print(f"Tags: {', '.join(metadata['tags'][:5])}...")

        # Check if video file exists and is valid
        if not Path(video_file).exists():
            print("[ERROR] Video file not found")
            return None

        file_size = Path(video_file).stat().st_size
        print(f"Video size: {file_size / 1024 / 1024:.2f} MB")

        if file_size < 1000:
            print("[ERROR] Video file too small, likely corrupted")
            return None

        print("\n[INFO] YouTube upload requires OAuth authentication")
        print("[INFO] Video saved locally - manual upload recommended")
        print(f"[INFO] Video location: {video_file}")

        return None

if __name__ == "__main__":
    pipeline = AutomatedYouTubePipeline()
    pipeline.run()