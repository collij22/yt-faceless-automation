#!/usr/bin/env python3
"""
YouTube Production Upload Script
Handles the complete pipeline from content selection to upload
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeProductionPipeline:
    def __init__(self):
        self.base_url = "http://localhost:5678/webhook"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.content_dir = Path(f"content/{self.session_id}")
        self.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Load API keys from .env
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', '')
        
    def select_content_topic(self):
        """Let user select what type of content to create"""
        print("\n" + "="*60)
        print("CONTENT SELECTION")
        print("="*60)
        
        topics = [
            {
                "id": "tech_tutorial",
                "name": "Tech Tutorial",
                "title": "5 Hidden Windows Features You Never Knew Existed",
                "description": "Discover powerful Windows features that will boost your productivity",
                "script": """Welcome to today's tech tip video! Did you know that Windows has dozens of hidden features that most people never discover? Today, I'm going to show you 5 amazing features that will completely change how you use your computer.

First up, Virtual Desktops. Press Windows plus Tab to open Task View, then click New Desktop at the top. You can create multiple desktops for different tasks - one for work, one for personal use. Switch between them with Windows plus Control plus arrow keys.

Second, the hidden God Mode. Create a new folder and rename it to GodMode followed by a special code. This gives you access to every single Windows setting in one place. It's like having admin superpowers!

Third, clipboard history. Press Windows plus V instead of Control V. Windows keeps a history of everything you've copied, so you can paste items from hours ago. Never lose copied text again!

Fourth, built-in screen recording. Press Windows plus G to open the Game Bar. Despite its name, it can record any application, perfect for creating tutorials or saving important video calls.

Finally, PowerToys. This free Microsoft tool adds incredible features like FancyZones for window management, PowerRename for bulk file renaming, and a color picker that works anywhere on your screen.

That's it for today's tech tips! If you found this helpful, make sure to like and subscribe for more productivity boosters. See you in the next video!""",
                "tags": ["windows tips", "productivity", "tech tutorial", "computer tricks", "hidden features"],
                "category": "Science & Technology"
            },
            {
                "id": "motivation",
                "name": "Motivational Content",
                "title": "The 5-Minute Morning Routine That Changed My Life",
                "description": "Transform your mornings and supercharge your day with this simple routine",
                "script": """What if I told you that just 5 minutes each morning could completely transform your life? I'm not exaggerating. Six months ago, I discovered a simple morning routine that changed everything for me, and today I'm sharing it with you.

Here's the thing - most of us wake up and immediately reach for our phones. We're flooding our brains with other people's priorities before we've even set our own. This routine breaks that cycle.

Minute one: Gratitude breathing. Before you even open your eyes, take three deep breaths and think of three things you're grateful for. They can be tiny things - your warm bed, your morning coffee, the fact that you woke up today.

Minute two: Stretch and affirm. Stand up, stretch your arms above your head, and say three affirmations out loud. I am capable. I am worthy. Today will be amazing. Say them like you mean them.

Minute three: Hydrate and visualize. Drink a full glass of water while visualizing your perfect day. See yourself accomplishing your goals, feeling confident, spreading positivity.

Minutes four and five: Write your top three. Grab a notebook and write down the three most important things you'll accomplish today. Not ten things, not your entire to-do list. Just three things that will make today a win.

That's it. Five minutes. No phone, no email, no social media. Just you, setting the tone for an incredible day. Try this for one week and watch how your life begins to shift. 

Remember, you don't need more hours in your day. You need more intention in your mornings. Start tomorrow. Your future self will thank you.""",
                "tags": ["morning routine", "productivity", "self improvement", "motivation", "life hacks"],
                "category": "People & Blogs"
            },
            {
                "id": "finance",
                "name": "Finance Tips",
                "title": "3 Money Mistakes I Made in My 20s (So You Don't Have To)",
                "description": "Learn from my financial failures and build wealth faster",
                "script": """Let's talk about money - specifically, the expensive mistakes I made in my twenties that cost me thousands of dollars. I'm sharing these so you can learn from my failures and build wealth faster than I did.

Mistake number one: I thought budgeting was for broke people. I had a decent job, money was coming in, so why track it, right? Wrong. I was hemorrhaging money on subscriptions I forgot about, eating out constantly, and had no idea where my paycheck went each month. It wasn't until I started tracking every dollar that I realized I was wasting 40 percent of my income on things that didn't matter.

Mistake number two: I waited to invest because I thought I needed thousands of dollars to start. This one hurts the most. I missed out on seven years of compound interest because I thought investing was only for rich people. The truth? You can start with as little as one dollar using apps like Robinhood or Acorns. Those seven years of waiting cost me potentially hundreds of thousands in retirement.

Mistake number three: I used credit cards like free money. I racked up eight thousand dollars in credit card debt buying things to impress people I didn't even like. It took me three years to pay it off, and with interest, I paid almost twelve thousand total. Credit cards aren't evil, but treating them like free money will destroy your financial future.

Here's what I want you to do: Start today, not tomorrow. Track your spending for just one week. Open an investment account with whatever you can afford, even if it's five dollars. And if you have credit card debt, make a plan to crush it.

Your twenties are for making mistakes, but they don't have to be financial ones. Learn from mine, and you'll be miles ahead. What money mistake do you wish you could take back? Let me know in the comments below.""",
                "tags": ["personal finance", "money tips", "investing", "budgeting", "financial mistakes"],
                "category": "Education"
            },
            {
                "id": "custom",
                "name": "Custom Topic",
                "title": "",
                "description": "",
                "script": "",
                "tags": [],
                "category": "People & Blogs"
            }
        ]
        
        print("\nChoose a content topic:")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic['name']}")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(topics):
                    selected = topics[index]
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Please enter a valid number.")
        
        # If custom, get user input
        if selected['id'] == 'custom':
            print("\n" + "="*60)
            print("CUSTOM CONTENT SETUP")
            print("="*60)
            
            selected['title'] = input("Enter video title: ").strip()
            selected['description'] = input("Enter video description: ").strip()
            
            print("\nEnter your script (type 'END' on a new line when done):")
            script_lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                script_lines.append(line)
            selected['script'] = '\n'.join(script_lines)
            
            tags_input = input("\nEnter tags (comma-separated): ").strip()
            selected['tags'] = [tag.strip() for tag in tags_input.split(',')]
            
            print("\nCategories: Education, Entertainment, Gaming, Music, News, People & Blogs, Science & Technology")
            selected['category'] = input("Enter category: ").strip()
        
        return selected
    
    def generate_tts(self, script, voice_id=None):
        """Generate TTS audio from script"""
        print("\n[TTS] Generating audio from script...")
        
        # For testing, we'll use the n8n webhook
        response = requests.post(
            f"{self.base_url}/tts-generation",
            json={
                "text": script,
                "slug": self.session_id,
                "voice_id": voice_id or "default",
                "format": "mp3"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[TTS] Audio generated: {result.get('message', 'Success')}")
            
            # Save audio file path
            audio_path = self.content_dir / "narration.mp3"
            # In production, the TTS webhook would return a URL or base64 audio
            # For now, we'll create a placeholder
            audio_path.write_text("PLACEHOLDER_AUDIO")
            
            return str(audio_path)
        else:
            print(f"[TTS] Failed: {response.status_code}")
            return None
    
    def create_simple_video(self, audio_path, title):
        """Create a simple video with audio and title card"""
        print("\n[VIDEO] Creating video...")
        
        # For testing, we'll create a placeholder video
        video_path = self.content_dir / "video.mp4"
        
        # In production, this would use FFmpeg to create a real video
        # For now, we'll create a placeholder
        video_path.write_text("PLACEHOLDER_VIDEO")
        
        print(f"[VIDEO] Video created: {video_path}")
        return str(video_path)
    
    def prepare_upload_metadata(self, content):
        """Prepare metadata for YouTube upload"""
        metadata = {
            "title": content['title'][:100],  # YouTube title limit
            "description": f"{content['description']}\n\n" + 
                          "Created with AI-powered content automation.\n\n" +
                          "#" + " #".join(content['tags'][:5]),
            "tags": content['tags'][:500],  # YouTube tag limit
            "category": content['category'],
            "privacy": "private",  # Start with private for safety
            "thumbnail": None
        }
        
        # Save metadata
        metadata_path = self.content_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dumps(metadata, f, indent=2)
        
        return metadata
    
    def upload_to_youtube(self, video_path, metadata):
        """Upload video to YouTube"""
        print("\n[UPLOAD] Preparing YouTube upload...")
        
        # Show what will be uploaded
        print(f"\nTitle: {metadata['title']}")
        print(f"Category: {metadata['category']}")
        print(f"Privacy: {metadata['privacy']}")
        print(f"Tags: {', '.join(metadata['tags'][:5])}...")
        
        confirm = input("\nProceed with upload? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("[UPLOAD] Cancelled by user")
            return None
        
        # Call n8n webhook for upload
        response = requests.post(
            f"{self.base_url}/youtube-upload",
            json={
                "video_path": video_path,
                "title": metadata['title'],
                "description": metadata['description'],
                "tags": metadata['tags'],
                "category": metadata['category'],
                "privacy": metadata['privacy']
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                video_id = result.get('video_id', 'unknown')
                print(f"\n[SUCCESS] Video uploaded!")
                print(f"Video ID: {video_id}")
                print(f"URL: https://youtube.com/watch?v={video_id}")
                return video_id
            else:
                print(f"\n[ERROR] Upload failed: {result.get('message')}")
                return None
        else:
            print(f"\n[ERROR] Upload failed with status {response.status_code}")
            return None
    
    def run(self):
        """Run the complete production pipeline"""
        print("\n" + "="*60)
        print("YOUTUBE PRODUCTION UPLOAD PIPELINE")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Content Directory: {self.content_dir}")
        
        # Check API keys
        if not self.youtube_api_key:
            print("\n[ERROR] YOUTUBE_API_KEY not found in .env file")
            return
        
        if not self.elevenlabs_api_key:
            print("\n[WARNING] ELEVENLABS_API_KEY not found - TTS will use default voice")
        
        try:
            # Step 1: Select content
            content = self.select_content_topic()
            
            # Step 2: Generate TTS
            audio_path = self.generate_tts(content['script'])
            if not audio_path:
                print("[ERROR] TTS generation failed")
                return
            
            # Step 3: Create video
            video_path = self.create_simple_video(audio_path, content['title'])
            
            # Step 4: Prepare metadata
            metadata = self.prepare_upload_metadata(content)
            
            # Step 5: Upload to YouTube
            video_id = self.upload_to_youtube(video_path, metadata)
            
            if video_id:
                # Step 6: Generate affiliate links
                print("\n[AFFILIATE] Generating tracking links...")
                response = requests.post(
                    f"{self.base_url}/affiliate-shorten",
                    json={
                        "original_url": f"https://youtube.com/watch?v={video_id}",
                        "campaign": "launch",
                        "source": "direct"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[AFFILIATE] Short URL: {result.get('short_url', 'N/A')}")
                
                print("\n" + "="*60)
                print("PIPELINE COMPLETE!")
                print("="*60)
                print(f"Video uploaded successfully as PRIVATE")
                print(f"Review and make public at: https://studio.youtube.com")
            
        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    # Check n8n is running
    try:
        response = requests.get("http://localhost:5678/", timeout=5)
        if response.status_code != 200:
            print("[ERROR] n8n is not running. Please start n8n first.")
            return
    except:
        print("[ERROR] Cannot connect to n8n at localhost:5678")
        return
    
    pipeline = YouTubeProductionPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()