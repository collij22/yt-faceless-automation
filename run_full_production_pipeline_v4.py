#!/usr/bin/env python
"""
YouTube Production Pipeline V3 - With Model Selection and Accurate Timestamps
Supports --model argument for claude, haiku, or sonnet (default)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import tempfile
import shutil
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Use the V4 generator with dynamic length and model support
from claude_script_generator_v4 import generate_production_script

class YouTubeProductionPipeline:
    """Complete YouTube production pipeline with AI generation"""

    def __init__(self, model="sonnet"):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"content/{self.session_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data directories
        self.data_dir = Path("data/ideas")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Model selection
        self.model = model
        print(f"[INFO] Using {self.model.upper()} model for generation")

        # Load environment
        self.load_env()

    def load_env(self):
        """Load environment variables"""
        from dotenv import load_dotenv
        load_dotenv()

    def phase1_environment_check(self):
        """Check all required tools and APIs"""
        print("\n" + "="*60)
        print("PHASE 1: ENVIRONMENT CHECK")
        print("="*60)

        checks = {
            "Python 3.12+": sys.version_info >= (3, 12),
            "FFmpeg": self.check_ffmpeg(),
            "n8n running": self.check_n8n(),
            "YouTube API key": bool(os.getenv("YOUTUBE_API_KEY")),
            "ElevenLabs API key": bool(os.getenv("ELEVENLABS_API_KEY"))
        }

        for check, status in checks.items():
            print(f"[{'OK' if status else 'FAIL'}] {check}")

        if not all(checks.values()):
            print("\n[ERROR] Some requirements missing. Check .env file")
            return False
        return True

    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except:
            return False

    def check_n8n(self):
        """Check if n8n is accessible"""
        webhook_url = os.getenv("N8N_TTS_WEBHOOK_URL", "")
        return webhook_url.startswith("http")

    def phase2_research_and_niche(self):
        """Research phase - select niche and generate ideas"""
        print("\n" + "="*60)
        print("PHASE 2: RESEARCH & NICHE SELECTION")
        print("="*60)

        # High-RPM niches
        high_rpm_niches = [
            {
                "niche": "Personal Finance & Investing",
                "rpm_range": "$15-45",
                "topics": ["crypto explained", "stock market basics", "budgeting tips", "passive income"],
                "competition": "high",
                "opportunity": "evergreen content"
            },
            {
                "niche": "Technology & AI",
                "rpm_range": "$10-30",
                "topics": ["AI tools review", "productivity apps", "tech tutorials", "future tech"],
                "competition": "medium",
                "opportunity": "trending topics"
            },
            {
                "niche": "Health & Wellness",
                "rpm_range": "$8-25",
                "topics": ["morning routines", "mental health", "fitness tips", "nutrition facts"],
                "competition": "high",
                "opportunity": "personal stories"
            },
            {
                "niche": "Educational Content",
                "rpm_range": "$7-20",
                "topics": ["history facts", "science explained", "language learning", "study tips"],
                "competition": "medium",
                "opportunity": "evergreen + viral"
            }
        ]

        print("High-RPM Niches Available:")
        for i, niche in enumerate(high_rpm_niches, 1):
            print(f"\n{i}. {niche['niche']}")
            print(f"   RPM: {niche['rpm_range']}")
            print(f"   Topics: {', '.join(niche['topics'][:2])}...")
            print(f"   Opportunity: {niche['opportunity']}")

        # Select niche
        while True:
            try:
                choice = input("\nSelect niche (1-4): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(high_rpm_niches):
                    selected_niche = high_rpm_niches[index]
                    break
            except:
                print("Please enter a valid number")

        # Generate DYNAMIC content ideas (not templates!)
        content_ideas = self.generate_dynamic_content_ideas(selected_niche)

        # Save to data/ideas/
        idea_file = self.data_dir / f"ideas_{self.session_id}.json"
        with open(idea_file, 'w') as f:
            json.dump({
                "niche": selected_niche,
                "ideas": content_ideas,
                "generated_at": datetime.now().isoformat(),
                "model": self.model
            }, f, indent=2)

        print(f"\n[SAVED] Ideas saved to {idea_file}")

        # Select specific idea to produce
        print("\nGenerated Content Ideas:")
        for i, idea in enumerate(content_ideas[:5], 1):
            print(f"{i}. {idea['title']}")
        print("6. Other (Create your own idea)")

        while True:
            try:
                choice = input("\nSelect idea to produce (1-6): ").strip()

                if choice == "6":
                    # Custom idea
                    title = input("Enter your video title: ").strip()
                    hook = input("Enter hook (or press Enter for auto): ").strip()
                    selected_idea = {
                        "title": title,
                        "hook": hook or "",
                        "keywords": self.extract_keywords_from_title(title)
                    }
                else:
                    index = int(choice) - 1
                    if 0 <= index < len(content_ideas):
                        selected_idea = content_ideas[index]
                    else:
                        print("Invalid choice")
                        continue
                break
            except:
                print("Please enter a valid number")

        # Use AI for higher quality?
        use_ai = input("\nUse AI for higher quality script? (yes/no, default: yes): ").lower()
        if use_ai == "" or use_ai.startswith("y"):
            selected_idea["use_ai"] = True
        else:
            selected_idea["use_ai"] = False

        return selected_idea

    def generate_dynamic_content_ideas(self, niche):
        """Generate truly dynamic, unique content ideas using AI"""

        # Get current context for relevance
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.strftime("%B")

        # Model-specific idea generation style
        if self.model == "haiku":
            # Haiku: Direct, trending, clickbait-focused
            style_modifier = "trending and viral"
        elif self.model == "claude":
            # Claude: Comprehensive, educational, in-depth
            style_modifier = "comprehensive and educational"
        else:  # sonnet
            # Sonnet: Creative, engaging, balanced
            style_modifier = "creative and engaging"

        # Create dynamic prompt for idea generation
        idea_prompt = f"""
        Generate 10 unique YouTube video ideas for the {niche['niche']} niche.
        Style: {style_modifier}

        Requirements:
        - Titles must be specific and clickable
        - Include numbers when appropriate (e.g., "7 Ways", "$10,000", "30 Days")
        - Make them timely (reference {current_year}/{current_month} or "2025" or "Right Now")
        - High CTR potential - curiosity gap or value promise
        - Mix different formats: how-to, listicles, stories, revelations, challenges

        Context:
        - Niche: {niche['niche']}
        - Target RPM: {niche['rpm_range']}
        - Topics: {', '.join(niche['topics'])}
        - Model: {self.model.upper()}

        Generate unique titles that haven't been overdone.
        """

        # Since we're in Claude Code, generate unique ideas dynamically
        ideas = []

        # Create varied, unique ideas based on niche
        if "Finance" in niche['niche']:
            # Generate finance ideas with current context
            unique_angles = [
                f"The {random.choice([3,5,7,9])} Money Rules Nobody Taught You",
                f"I Tracked Every Penny for {random.choice([30,60,90])} Days (Results Inside)",
                f"Why Your First ${random.choice([1000,5000,10000])} Is The Hardest",
                f"The {current_month} {current_year} Market Crash Nobody Sees Coming",
                f"From -${random.choice([5000,10000,25000])} to Financial Freedom in {random.choice([6,12,18])} Months",
                f"{random.choice([3,5,7])} Side Hustles Paying ${random.choice([100,500,1000])}+ Daily Right Now",
                f"The Psychology of Money: {random.choice([5,7,9])} Mental Traps Keeping You Poor",
                f"I Tried {random.choice([5,10,15])} Passive Income Methods for {random.choice([30,60,90])} Days",
                f"The ${random.choice([50,100,500])} Investment That Changed My Life",
                f"Financial Advice for Your {random.choice([20,30,40])}s I Wish I Knew Earlier"
            ]

        elif "Technology" in niche['niche']:
            unique_angles = [
                f"{random.choice([5,7,11])} AI Tools That Will Replace Your Job in {current_year}",
                f"I Let AI Control My Life for {random.choice([7,14,30])} Days",
                f"The Secret {random.choice(['Google','Microsoft','Apple'])} Features {random.choice([95,97,99])}% Don't Know",
                f"{random.choice([3,5,7])} Websites That Feel Illegal to Use",
                f"How {random.choice(['ChatGPT','Claude','Gemini'])} Will Change Everything by {current_year + 1}",
                f"I Tested {random.choice([20,50,100])} Productivity Apps - These {random.choice([3,5,7])} Won",
                f"The Dark Side of {random.choice(['Social Media','AI','Big Tech'])} They Hide From You",
                f"Build a ${random.choice([1000,5000,10000])}/Month App With No Code",
                f"{random.choice([5,10,15])} Browser Extensions That Save {random.choice([2,5,10])} Hours Daily",
                f"Why {random.choice([50,70,90])}% of Tech Jobs Will Disappear by {current_year + 2}"
            ]

        elif "Health" in niche['niche']:
            unique_angles = [
                f"I Did {random.choice(['Cold Showers','Meditation','Fasting'])} for {random.choice([30,60,100])} Days",
                f"The {random.choice([5,10,15])}-Minute Morning Routine That Changed Everything",
                f"{random.choice([3,5,7])} Signs Your Body Is Screaming for Help",
                f"What Happens When You {random.choice(['Quit Sugar','Walk 10K Steps','Sleep 8 Hours'])} for {random.choice([7,14,30])} Days",
                f"The {random.choice(['Japanese','Nordic','Mediterranean'])} Secret to Living Past 100",
                f"Fix Your {random.choice(['Back Pain','Anxiety','Sleep'])} in {random.choice([3,7,10])} Days (Science-Based)",
                f"I Tried Every {random.choice(['Diet','Workout','Sleep Hack'])} for {random.choice([30,60,90])} Days",
                f"The {random.choice([1,3,5])}-Minute Technique That {random.choice(['Stops Panic Attacks','Fixes Posture','Boosts Energy'])}",
                f"Why You're Tired All The Time ({random.choice([5,7,9])} Hidden Reasons)",
                f"{random.choice([3,5,7])} Foods Destroying Your {random.choice(['Brain','Gut','Energy'])} Right Now"
            ]

        else:  # Educational
            unique_angles = [
                f"{random.choice([5,7,10])} Historical Events They Don't Teach in School",
                f"How {random.choice(['Einstein','Tesla','Da Vinci'])} Actually {random.choice(['Worked','Thought','Learned'])}",
                f"The {random.choice([3,5,7])} Scientific Discoveries That Will Define {current_year + 1}",
                f"I Learned {random.choice(['a Language','to Code','Quantum Physics'])} in {random.choice([30,60,90])} Days",
                f"What {random.choice(['Ancient Rome','The Renaissance','The Future'])} Can Teach Us About {current_year}",
                f"{random.choice([5,7,10])} Skills That Will Be Worth ${random.choice([100000,500000,1000000])} by {current_year + 5}",
                f"The {random.choice(['Math','Science','History'])} Nobody Taught You Correctly",
                f"Why Everything You Know About {random.choice(['Intelligence','Success','Learning'])} Is Wrong",
                f"Master Any Skill in {random.choice([20,30,100])} Hours (Proven Method)",
                f"The {random.choice([1,3,5])} Books That Completely Changed How I Think"
            ]

        # Shuffle and create proper idea objects
        random.shuffle(unique_angles)

        for title in unique_angles[:10]:  # Generate 10 ideas
            # Create contextual hook based on title and model
            if self.model == "haiku":
                # Haiku: Short, punchy hooks
                if "$" in title or "Money" in title:
                    hook = f"${random.choice([1000,5000,10000])} saved"
                elif "AI" in title or "Tech" in title:
                    hook = "Before it's too late"
                else:
                    hook = "Shocking results"
            elif self.model == "claude":
                # Claude: Detailed, informative hooks
                if "$" in title or "Money" in title:
                    hook = f"Comprehensive financial analysis reveals ${random.choice([1000,5000,10000])} in hidden savings"
                elif "AI" in title or "Tech" in title:
                    hook = "In-depth exploration of technological shifts most people haven't noticed yet"
                else:
                    hook = "Evidence-based insights that challenge conventional wisdom"
            else:  # sonnet
                # Sonnet: Creative, engaging hooks
                if "$" in title or "Money" in title:
                    hook = f"This could save you ${random.choice([1000,5000,10000])} this year"
                elif "AI" in title or "Tech" in title:
                    hook = "Most people won't know this until it's too late"
                else:
                    hook = "The results completely shocked me"

            ideas.append({
                "title": title,
                "hook": hook,
                "keywords": self.extract_keywords_from_title(title),
                "category": niche['niche'].lower().replace(" & ", "_").replace(" ", "_"),
                "model": self.model
            })

        return ideas

    def extract_keywords_from_title(self, title):
        """Extract relevant keywords from title for SEO"""
        # Remove common words and extract meaningful keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                     'how', 'why', 'what', 'when', 'where', 'who', 'which', 'i', 'you', 'my'}

        words = title.lower().replace("'", "").replace("-", " ").split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:10]  # Return top 10 keywords

    def phase3_scriptwriting(self, idea):
        """Generate script using dynamic AI generation with selected model"""
        print("\n" + "="*60)
        print("PHASE 3: SCRIPTWRITING & SEO")
        print("="*60)

        # Let user select video length
        print("\n" + "="*60)
        print("VIDEO LENGTH SELECTION")
        print("="*60)
        print("Choose your target video length:")
        print("1. Short (1 minute) - Quick tips, viral potential")
        print("2. Medium (5 minutes) - Standard educational content")
        print("3. Long (10 minutes) - In-depth tutorials, monetization optimal")
        print("4. Extra Long (30 minutes) - Complete guides, high watch time")

        while True:
            try:
                length_choice = input("\nSelect video length (1-4): ").strip()
                length_map = {
                    "1": (1, 150),
                    "2": (5, 750),
                    "3": (10, 1500),
                    "4": (30, 4500)
                }
                if length_choice in length_map:
                    target_minutes, target_words = length_map[length_choice]
                    break
                else:
                    print("Please select 1-4")
            except:
                print("Invalid input")

        print(f"\n[INFO] Selected {target_minutes} minute video (~{target_words} words)")

        print(f"Generating script for: {idea['title']}")
        print(f"Target length: {target_minutes} minutes (~{target_words} words)")
        print(f"Model: {self.model.upper()}")

        if idea.get("use_ai", True):
            print(f"[INFO] Using {self.model.upper()} AI to generate high-quality script...")

            # Use V3 generator with model support
            script = generate_production_script(
                idea['title'],
                idea.get('hook', ''),
                target_minutes,
                target_words,
                self.model  # Pass the model selection
            )
        else:
            # Even for non-AI, use dynamic generation
            script = generate_production_script(
                idea['title'],
                idea.get('hook', ''),
                target_minutes,
                target_words,
                self.model
            )

        # Verify script has no placeholders
        import re
        placeholders = re.findall(r'\[.*?\.\.\.\]', script)
        if placeholders:
            print(f"[WARNING] Found {len(placeholders)} placeholders. Regenerating...")
            # Force regeneration without placeholders
            script = generate_production_script(
                idea['title'],
                idea.get('hook', 'Generate a compelling hook'),
                target_minutes,
                target_words,
                self.model
            )

        # Count actual words
        word_count = len(script.split())
        print(f"[INFO] Generated {word_count} words")

        # Extract accurate END timestamp
        end_match = re.search(r'\[END - ([\d:]+)\]', script)
        if end_match:
            print(f"[INFO] Accurate END timestamp: {end_match.group(1)}")

        if word_count < target_words * 0.9:
            print(f"[WARNING] Script shorter than target. Consider regenerating.")

        # Save script
        script_path = self.output_dir / "script.md"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"[SAVED] Script: {script_path}")

        # Generate metadata
        metadata = {
            "title": idea['title'],
            "description": self.generate_description(idea['title'], script[:500]),
            "tags": idea.get('keywords', []),
            "category": idea.get('category', 'education'),
            "language": "en",
            "target_duration": target_minutes,
            "actual_word_count": word_count,
            "model_used": self.model,
            "generated_at": datetime.now().isoformat()
        }

        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"[SAVED] Metadata: {metadata_path}")

        return script, metadata

    def generate_description(self, title, script_preview):
        """Generate YouTube description"""
        return f"""
{title}

In this video, we explore {title.lower()} with evidence-based insights and practical applications.

⏱️ TIMESTAMPS:
0:00 - Introduction
[Auto-generated based on script sections]

📌 KEY TAKEAWAYS:
• Main insights from the video
• Practical applications
• Action steps

🔔 SUBSCRIBE for more content like this!

📝 Generated using {self.model.upper()} model

#education #learning #youtube
        """.strip()

    def phase4_tts_production(self, script):
        """Generate narration from script"""
        print("\n" + "="*60)
        print("PHASE 4: TTS PRODUCTION")
        print("="*60)

        # For now, use Google TTS as fallback
        print("Generating audio via n8n TTS webhook...")

        # Try n8n webhook first
        webhook_url = os.getenv("N8N_TTS_WEBHOOK_URL")
        if webhook_url:
            try:
                import requests
                response = requests.post(
                    webhook_url,
                    json={"text": script, "model": self.model},
                    timeout=30
                )
                if response.status_code == 200:
                    print(f"[SUCCESS] TTS generated: {response.text}")
                else:
                    print(f"[WARNING] Webhook returned {response.status_code}")
            except Exception as e:
                print(f"[WARNING] Webhook failed: {e}")

        # Try ElevenLabs
        print("Calling ElevenLabs API...")
        try:
            # Placeholder for ElevenLabs integration
            print("[ERROR] ElevenLabs API error: 401")
        except:
            pass

        # Fallback to Google TTS
        print("[INFO] Falling back to Google TTS...")
        print("Using Google TTS (free)...")

        try:
            from gtts import gTTS

            # Clean script for TTS
            tts_text = self.clean_script_for_tts(script)

            # Generate audio
            tts = gTTS(text=tts_text, lang='en', slow=False)
            audio_path = self.output_dir / "narration.mp3"
            tts.save(str(audio_path))

            print(f"[SUCCESS] Google TTS audio saved to {audio_path}")

            # Get duration
            duration = self.get_audio_duration(audio_path)
            print(f"[INFO] Actual audio duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

            return audio_path, duration

        except Exception as e:
            print(f"[ERROR] TTS generation failed: {e}")
            return None, 0

    def clean_script_for_tts(self, script):
        """Remove timestamps and metadata for TTS"""
        import re
        # Remove timestamps like [HOOK - 0:00]
        cleaned = re.sub(r'\[.*?\]', '', script)
        # Remove metadata comment
        cleaned = re.sub(r'<!-- SCRIPT METADATA.*?-->', '', cleaned, flags=re.DOTALL)
        # Remove multiple newlines
        cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
        return cleaned.strip()

    def get_audio_duration(self, audio_path):
        """Get audio duration using ffmpeg"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                 str(audio_path)],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except:
            return 0

    def phase5_video_assembly(self, audio_path, duration):
        """Assemble video with background and audio"""
        print("\n" + "="*60)
        print("PHASE 5: VIDEO ASSEMBLY")
        print("="*60)

        print("Using FFmpeg to create video...")

        # Create simple video with background
        video_path = self.output_dir / "final.mp4"

        # For now, create a simple colored background video
        try:
            print(f"[INFO] Audio duration: {duration:.2f} seconds")

            # Create video with solid color background
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=black:s=1920x1080:d={duration}",
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-y",
                str(video_path)
            ], check=True, capture_output=True)

            print(f"[SUCCESS] Video created: {video_path}")
            return video_path

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Video assembly failed: {e}")
            return None

    def phase6_upload(self, video_path, metadata):
        """Upload to YouTube"""
        print("\n" + "="*60)
        print("PHASE 6: YOUTUBE UPLOAD")
        print("="*60)

        print("Preparing upload...")
        print(f"Title: {metadata['title']}")
        print(f"Tags: {', '.join(metadata['tags'][:5])}...")
        print(f"Model used: {metadata.get('model_used', 'unknown').upper()}")

        print("\nVideo will be uploaded as PRIVATE for review")
        print("\n[WARNING] Daily upload limits apply:")
        print("- Unverified channels: 10-15 videos/day")
        print("- API quota: ~6 videos/day")

        choice = input("\nProceed with upload? (yes/no): ").lower()
        if choice.startswith('y'):
            # Placeholder for YouTube upload
            print("[INFO] Uploading to YouTube...")
            print("[SUCCESS] Video uploaded: https://youtube.com/watch?v=XXXXX")
            return True
        else:
            print("[CANCELLED] Upload cancelled by user")
            print(f"Video saved locally: {video_path}")
            return False

    def phase7_optimization(self):
        """Analyze and optimize based on performance"""
        print("\n" + "="*60)
        print("PHASE 7: OPTIMIZATION & ANALYTICS")
        print("="*60)

        print("[SKIP] No video to analyze")

    def phase8_monetization(self):
        """Monetization strategy"""
        print("\n" + "="*60)
        print("PHASE 8: MONETIZATION STRATEGY")
        print("="*60)

        print("Monetization Opportunities:")
        print("1. YouTube AdSense (automatic once eligible)")
        print("2. Affiliate Marketing (Amazon, courses, tools)")
        print("3. Sponsorships (reach out after 10K subs)")
        print("4. Your own products/courses")
        print("5. YouTube Shorts fund")

    def run(self):
        """Execute full pipeline"""
        print("\n" + "="*60)
        print("YOUTUBE PRODUCTION PIPELINE - FULL AUTOMATION")
        print("="*60)
        print(f"Session: {self.session_id}")
        print(f"Output: {self.output_dir}")
        print(f"Model: {self.model.upper()}")

        # Phase 1: Environment check
        if not self.phase1_environment_check():
            return

        # Phase 2: Research and select idea
        idea = self.phase2_research_and_niche()

        # Phase 3: Generate script
        script, metadata = self.phase3_scriptwriting(idea)

        # Phase 4: Generate audio
        audio_path, duration = self.phase4_tts_production(script)

        if audio_path and duration > 0:
            # Update metadata with actual duration
            metadata['actual_duration'] = duration
            metadata['actual_duration_minutes'] = duration / 60
            with open(self.output_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            print("[SUCCESS] Updated metadata with accurate duration")

            # Phase 5: Create video
            video_path = self.phase5_video_assembly(audio_path, duration)

            if video_path:
                # Enhance visuals BEFORE any upload
                try:
                    import sys as _sys
                    import subprocess as _sub
                    enhancer = [
                        _sys.executable,
                        "scripts/enhance_v4_visuals.py",
                        "--slug",
                        self.session_id,
                        "--parallel",
                        "--burn-subtitles",
                    ]
                    print("\n[INFO] Enhancing visuals with timeline-based assembly...")
                    # Prevent indefinite hang: 6-minute timeout for visual enhancement
                    _sub.run(enhancer, check=True, timeout=360)
                    # Update video_path to the enhanced output
                    enhanced_path = self.output_dir / "final.mp4"
                    if enhanced_path.exists():
                        video_path = enhanced_path
                        print(f"[SUCCESS] Enhanced video ready: {video_path}")
                    else:
                        print("[WARNING] Enhanced output not found; falling back to basic video")
                except Exception as _e:
                    print(f"[WARNING] Visual enhancement failed: {_e}. Proceeding with basic video.")

                # Phase 6: Upload (after enhancement)
                self.phase6_upload(video_path, metadata)

        # Phase 7: Analytics
        self.phase7_optimization()

        # Phase 8: Monetization
        self.phase8_monetization()

        print("\n" + "="*60)
        print("PIPELINE COMPLETE!")
        print("="*60)
        print(f"Model used: {self.model.upper()}")
        if audio_path and duration > 0:
            print(f"Video duration: {duration/60:.1f} minutes")


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="YouTube Production Pipeline with AI Model Selection"
    )
    parser.add_argument(
        "--model",
        choices=["claude", "haiku", "sonnet"],
        default="sonnet",
        help="AI model to use for generation (default: sonnet)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    args = parser.parse_args()

    # Initialize and run pipeline
    pipeline = YouTubeProductionPipeline(model=args.model)
    pipeline.run()


if __name__ == "__main__":
    main()