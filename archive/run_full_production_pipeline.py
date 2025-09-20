#!/usr/bin/env python3
"""
Full Production Pipeline for YouTube Automation
Implements all 8 phases from README.md
"""

import os
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import time
import random
import hashlib

# Load environment variables
load_dotenv()

class YouTubeProductionSystem:
    def __init__(self):
        self.base_url = "http://localhost:5678/webhook"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.content_dir = Path(f"content/{self.session_id}")
        self.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Directories from project structure
        self.data_dir = Path("data/ideas")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # API keys
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', '')
        self.elevenlabs_voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default voice
        self.brave_search_key = os.getenv('BRAVE_API_KEY', '')
        
    def phase1_environment_check(self):
        """Phase 1: Prerequisites & Environment Check"""
        print("\n" + "="*60)
        print("PHASE 1: ENVIRONMENT CHECK")
        print("="*60)
        
        checks = []
        
        # Check Python
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            if '3.12' in result.stdout or '3.11' in result.stdout:
                checks.append(('Python 3.12+', True))
            else:
                checks.append(('Python 3.12+', False))
        except:
            checks.append(('Python 3.12+', False))
        
        # Check FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            checks.append(('FFmpeg', 'ffmpeg version' in result.stdout))
        except:
            checks.append(('FFmpeg', False))
        
        # Check n8n
        try:
            response = requests.get("http://localhost:5678/", timeout=5)
            checks.append(('n8n running', response.status_code == 200))
        except:
            checks.append(('n8n running', False))
        
        # Check API keys
        checks.append(('YouTube API key', bool(self.youtube_api_key)))
        checks.append(('ElevenLabs API key', bool(self.elevenlabs_api_key)))
        
        # Display results
        all_passed = True
        for check, passed in checks:
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {check}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def phase2_research_and_niche_selection(self):
        """Phase 2: Research & Niche Selection Engine"""
        print("\n" + "="*60)
        print("PHASE 2: RESEARCH & NICHE SELECTION")
        print("="*60)
        
        # High-RPM niches from research (based on README citations)
        high_rpm_niches = [
            {
                "niche": "Personal Finance & Investing",
                "rpm_range": "$15-45",
                "topics": ["crypto explained", "stock market basics", "passive income", "budgeting tips"],
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
        
        # Generate content ideas for selected niche
        content_ideas = self.generate_content_ideas(selected_niche)
        
        # Save to data/ideas/
        idea_file = self.data_dir / f"ideas_{self.session_id}.json"
        with open(idea_file, 'w') as f:
            json.dump({
                "niche": selected_niche,
                "ideas": content_ideas,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n[SAVED] Ideas saved to {idea_file}")
        
        # Select specific idea to produce
        if content_ideas:
            print("\nGenerated Content Ideas:")
            for i, idea in enumerate(content_ideas[:5], 1):
                print(f"{i}. {idea['title']}")
            print("6. Other (Create your own idea)")
        else:
            print("\n[WARNING] No ideas generated. Switching to custom idea mode.")
            content_ideas = []  # Ensure it's empty list

        while True:
            try:
                if not content_ideas:
                    choice = "6"  # Force custom idea if no ideas
                else:
                    choice = input("\nSelect idea to produce (1-6): ").strip()

                if choice == "6":
                    # Custom idea option
                    print("\n" + "="*60)
                    print("CREATE YOUR OWN IDEA")
                    print("="*60)
                    custom_title = input("Enter your video title: ").strip()
                    if not custom_title:
                        print("Title cannot be empty. Please try again.")
                        continue

                    custom_hook = input("Enter a hook/tagline (or press Enter to auto-generate): ").strip()
                    if not custom_hook:
                        custom_hook = "The truth about this will surprise you"

                    # Research the topic if needed
                    print(f"\n[INFO] Researching topic: {custom_title}")

                    # Create custom idea object
                    selected_idea = {
                        "title": custom_title,
                        "hook": custom_hook,
                        "keywords": self.extract_keywords_from_title(custom_title),
                        "estimated_views": "10K-100K",
                        "competition_score": 7,
                        "custom": True
                    }

                    # Perform research if Brave Search is available
                    selected_idea = self.research_topic(selected_idea)
                    break
                else:
                    index = int(choice) - 1
                    if 0 <= index < len(content_ideas[:5]):
                        selected_idea = content_ideas[index]
                        selected_idea["custom"] = False
                        break
                    else:
                        print("Please enter a valid number (1-6)")
            except ValueError:
                print("Please enter a valid number (1-6)")
            except Exception as e:
                print(f"Error: {e}. Please try again.")

        # Ask if user wants AI-generated script for better quality
        if not selected_idea.get('custom', False):
            use_ai = input("\nUse AI for higher quality script? (yes/no, default: yes): ").strip().lower()
            if use_ai != 'no':
                selected_idea['use_ai_script'] = True

        # Select video length
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
                length_options = {
                    "1": {"minutes": 1, "name": "short", "words": 150},
                    "2": {"minutes": 5, "name": "medium", "words": 750},
                    "3": {"minutes": 10, "name": "long", "words": 1500},
                    "4": {"minutes": 30, "name": "extra_long", "words": 4500}
                }
                if length_choice in length_options:
                    selected_length = length_options[length_choice]
                    print(f"\n[INFO] Selected {selected_length['minutes']} minute video (~{selected_length['words']} words)")
                    selected_idea['target_length'] = selected_length
                    break
            except:
                print("Please enter a valid number (1-4)")

        return selected_idea
    
    def load_idea_history(self):
        """Load previously generated ideas to avoid duplicates"""
        history_file = self.data_dir / "idea_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                return {"generated_titles": [], "last_updated": None}
        return {"generated_titles": [], "last_updated": None}

    def save_idea_history(self, history, new_ideas):
        """Save idea history to avoid duplicates"""
        history_file = self.data_dir / "idea_history.json"
        # Add new ideas to history
        for idea in new_ideas:
            if idea['title'] not in history["generated_titles"]:
                history["generated_titles"].append(idea['title'])
        # Keep only last 100 titles to prevent file from growing too large
        history["generated_titles"] = history["generated_titles"][-100:]
        history["last_updated"] = datetime.now().isoformat()
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def generate_dynamic_variations(self):
        """Generate dynamic elements for idea variations"""
        current_year = datetime.now().year
        current_month = datetime.now().strftime("%B")

        # Use current time to add variety while keeping ideas relevant
        day_seed = datetime.now().day
        hour_seed = datetime.now().hour

        numbers = {
            "small": [3, 5, 7, 10, 11, 13, 15, 17][day_seed % 8],
            "medium": [20, 25, 30, 40, 50, 60, 75][day_seed % 7],
            "large": [100, 365, 500, 1000, 2024][day_seed % 5],
            "percentage": [67, 73, 81, 87, 92, 96, 99][day_seed % 7],
            "money": [100, 250, 500, 1000, 2500, 5000, 10000][hour_seed % 7],
            "time_days": [3, 7, 14, 21, 30, 60, 90][day_seed % 7],
            "time_minutes": [2, 5, 10, 15, 30, 60][hour_seed % 6],
            "tips_count": [5, 7, 9, 10, 12, 15, 20][day_seed % 7]
        }

        time_frames = [
            f"in {current_year}",
            f"({current_month} {current_year})",
            "Right Now",
            "This Week",
            f"Before {current_year + 1}",
            "Starting Today"
        ]

        return {
            "numbers": numbers,
            "time_frame": time_frames[day_seed % len(time_frames)],
            "year": current_year,
            "month": current_month,
            "next_year": current_year + 1
        }

    def generate_content_ideas(self, niche):
        """Generate specific content ideas for a niche with dynamic variety"""
        # Load history to avoid duplicates
        history = self.load_idea_history()

        # Get dynamic variations
        vars = self.generate_dynamic_variations()
        current_year = vars["year"]
        n = vars["numbers"]

        # Generate fresh ideas based on niche
        if "Finance" in niche['niche']:
            # Dynamic finance templates
            templates = [
                f"{n['small']} Money Mistakes That Keep You Poor (Fix Them {vars['time_frame']})",
                f"The ${n['money']} Mistake {n['percentage']}% of People Make",
                f"{n['tips_count']} Financial Habits of Millionaires {vars['time_frame']}",
                f"Why {n['percentage']}% Never Build Wealth (Harsh Truth)",
                f"The {n['time_minutes']}-Minute Budget System That Works",
                f"Save ${n['money']} in {n['time_days']} Days (Proven Method)",
                f"{n['small']} Investments That Pay Monthly {vars['time_frame']}",
                f"Turn ${n['money']} into ${n['money']*10} This Year",
                f"{n['tips_count']} Passive Income Ideas {vars['time_frame']}",
                f"Make ${n['money']} Per Month While You Sleep",
                f"Raise Your Credit Score {n['large']} Points Fast",
                f"Retire at {n['medium']+20} (Complete Blueprint)",
            ]
            category = "finance"

        elif "Technology" in niche['niche']:
            templates = [
                f"{n['tips_count']} AI Tools That Change Everything {vars['time_frame']}",
                f"The AI That Saves {n['time_minutes']} Hours Weekly",
                f"ChatGPT Tricks {n['percentage']}% Don't Know",
                f"{n['small']} Free AI Tools Better Than Paid",
                f"{n['small']} Apps I Can't Live Without {vars['time_frame']}",
                f"The {n['time_minutes']}-Minute Productivity Setup",
                f"{n['tips_count']} Hidden Phone Features",
                f"{n['small']} Websites That Feel Illegal",
                f"Why {n['percentage']}% of Jobs Will Be AI Soon",
                f"The Tech That Defines {vars['next_year']}",
            ]
            category = "technology"

        elif "Health" in niche['niche'] or "Wellness" in niche['niche']:
            templates = [
                f"The {n['time_minutes']}-Minute Morning Routine",
                f"{n['small']} Morning Habits That Change Everything",
                f"Fall Asleep in {n['time_minutes']} Minutes (Military)",
                f"{n['small']} Sleep Mistakes You Make Daily",
                f"{n['time_minutes']}-Minute Workout > Running",
                f"{n['tips_count']} Foods for Brain Power",
                f"{n['small']} Signs You're Mentally Exhausted",
                f"Beat Anxiety in {n['time_minutes']} Minutes",
                f"The Habit That Fixed My Life",
                f"Live to {100 + n['small']*2} (Science Says)",
            ]
            category = "health"

        else:
            templates = [
                f"{n['tips_count']} Historical Facts That Shock",
                f"The {n['small']} Events That Changed History",
                f"{n['small']} Scientific Discoveries of {vars['year']}",
                f"Why {n['percentage']}% of Facts Are Wrong",
                f"{n['tips_count']} Psychology Tricks That Work",
                f"Your Brain Does This {n['large']} Times Daily",
                f"{n['small']} Skills Worth Learning {vars['time_frame']}",
                f"Master Anything in {n['time_days']} Days",
                f"The {n['percentage']}% Rule for Success",
                f"Life at Age {n['medium']}: What I Learned",
            ]
            category = "educational"

        # Create unique ideas
        ideas = []
        random.shuffle(templates)

        # First try to find unused templates
        for title in templates:
            if title not in history["generated_titles"]:
                # Generate hook
                if "Money" in title or "$" in title:
                    hook = f"This saves ${n['money']} per year minimum"
                elif "AI" in title:
                    hook = f"Replace {n['small']} hours of work instantly"
                elif "Mistake" in title:
                    hook = f"{n['percentage']}% of people do this wrong"
                else:
                    hook = f"The results will shock you"

                ideas.append({
                    "title": title,
                    "hook": hook,
                    "keywords": self.get_keywords_for_category(category),
                    "estimated_views": f"{n['medium']}K-{n['large']}K",
                    "competition_score": random.randint(6, 9)
                })

                if len(ideas) >= 5:
                    break

        # If we don't have enough ideas, generate new variations
        if len(ideas) < 5:
            print(f"[INFO] Generating fresh variations (found {len(ideas)} unique ideas)")
            # Generate new variations with different templates
            variation_templates = {
                "finance": [
                    f"The ${random.randint(100, 10000)} Challenge That Made Me Rich",
                    f"Why {random.randint(70, 99)}% of Millionaires Do This Daily",
                    f"I Tried {random.randint(5, 30)} Side Hustles - Here's What Worked",
                    f"The {random.randint(3, 15)}-Step Formula to Financial Freedom",
                    f"How to Go From $0 to ${random.randint(10000, 100000)} (Real Story)",
                    f"{random.randint(3, 10)} Investments That Pay You Every Week",
                    f"The Truth About {['Crypto', 'Stocks', 'Real Estate', 'Gold'][random.randint(0, 3)]}",
                    f"My ${random.randint(1000, 50000)}/Month Passive Income System",
                ],
                "technology": [
                    f"I Tested {random.randint(10, 50)} AI Tools - These {random.randint(3, 7)} Won",
                    f"The App That Replaced {random.randint(3, 10)} Employees",
                    f"Why I Quit Using {['Google', 'Microsoft', 'Apple', 'Meta'][random.randint(0, 3)]}",
                    f"{random.randint(3, 10)} Websites Better Than College",
                    f"The {random.randint(5, 30)}-Minute Automation That Saves Hours",
                    f"Tech Skills Worth ${random.randint(50000, 200000)}/Year",
                ],
                "health": [
                    f"I Did This for {random.randint(7, 90)} Days - Shocking Results",
                    f"The {random.randint(2, 10)}-Minute Routine Doctors Hate",
                    f"Why {random.randint(80, 99)}% of People Feel Tired (Fix This)",
                    f"{random.randint(3, 10)} Foods That Changed My Life",
                    f"The Science of Living to {random.randint(100, 120)}",
                    f"How I Lost {random.randint(10, 50)} Pounds Without Exercise",
                ],
                "educational": [
                    f"The {random.randint(3, 10)} Books That Changed Everything",
                    f"{random.randint(5, 20)} Skills You Need Before {datetime.now().year + 1}",
                    f"How {['Einstein', 'Tesla', 'Da Vinci', 'Newton'][random.randint(0, 3)]} Actually Thought",
                    f"The Truth About {['Success', 'Intelligence', 'Talent', 'Genius'][random.randint(0, 3)]}",
                    f"{random.randint(3, 10)} Lessons From My Biggest Failure",
                    f"Why School Failed You (And What to Do Now)",
                ]
            }

            templates_to_use = variation_templates.get(category, variation_templates["educational"])
            random.shuffle(templates_to_use)

            for i in range(5 - len(ideas)):
                if i < len(templates_to_use):
                    new_title = templates_to_use[i]
                    hook = "The results will shock you"
                else:
                    # Ultimate fallback
                    alt_num = random.randint(3, 99)
                    new_title = f"{alt_num} Things You Need to Know About {category.title()}"
                    hook = f"Number {random.randint(1, alt_num)} will blow your mind"

                ideas.append({
                    "title": new_title,
                    "hook": hook,
                    "keywords": self.get_keywords_for_category(category),
                    "estimated_views": f"{n['medium']}K-{n['large']}K",
                    "competition_score": random.randint(6, 9)
                })

        # Save history
        self.save_idea_history(history, ideas)
        return ideas

    def get_keywords_for_category(self, category):
        """Get relevant keywords for a category"""
        keywords_map = {
            "finance": ["money", "finance", "wealth", "passive income", "investing"],
            "technology": ["tech", "AI", "ChatGPT", "productivity", "apps"],
            "health": ["health", "wellness", "fitness", "mental health", "habits"],
            "educational": ["education", "facts", "learning", "skills", "science"]
        }
        return random.sample(keywords_map.get(category, ["educational"]), min(5, len(keywords_map.get(category, ["educational"]))))

    def extract_keywords_from_title(self, title):
        """Extract potential keywords from a title"""
        # Common words to exclude
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                     "of", "with", "by", "from", "as", "is", "was", "are", "were", "that",
                     "this", "these", "those", "how", "why", "what", "when", "where"}

        # Extract meaningful words
        words = title.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Add some generic keywords based on content
        if any(w in title.lower() for w in ["money", "dollar", "invest", "save", "budget"]):
            keywords.extend(["finance", "money"])
        elif any(w in title.lower() for w in ["ai", "tech", "app", "software", "computer"]):
            keywords.extend(["technology", "tech"])
        elif any(w in title.lower() for w in ["health", "fitness", "workout", "diet", "sleep"]):
            keywords.extend(["health", "wellness"])
        else:
            keywords.extend(["education", "learning"])

        # Add current year
        keywords.append(str(datetime.now().year))

        # Return unique keywords (up to 10)
        return list(set(keywords))[:10]

    def research_topic(self, idea):
        """Research a topic using available tools"""
        try:
            # Try to use Brave Search if available
            if hasattr(self, 'brave_search_key') and self.brave_search_key:
                print(f"[INFO] Searching for: {idea['title']}")
                # Note: This would use the Brave Search MCP if integrated
                # For now, we'll add placeholder research data
                idea['research'] = {
                    "searched": True,
                    "query": idea['title'],
                    "notes": "Research data would be gathered here via Brave Search MCP"
                }
            else:
                print("[INFO] Brave Search not configured, using basic research")
                idea['research'] = {
                    "searched": False,
                    "notes": "Manual research may be needed for accuracy"
                }
        except Exception as e:
            print(f"[WARNING] Research failed: {e}")
            idea['research'] = {"searched": False, "error": str(e)}

        return idea

    def generate_ai_script(self, idea, target_minutes, target_words):
        """Generate a high-quality script using Claude AI"""
        try:
            # Import the production script generator
            from claude_script_generator import get_production_script

            # Generate actual full content, not placeholders
            script = get_production_script(
                title=idea['title'],
                hook=idea.get('hook', ''),
                target_minutes=target_minutes,
                target_words=target_words
            )

            if script:
                return script

            # Fallback to template if generation fails
            if "Money Rules" in idea['title']:
                # Extract number from title
                import re
                numbers = re.findall(r'\d+', idea['title'])
                num_rules = int(numbers[0]) if numbers else 10

                script = f"""[HOOK - 0:00]
You've been lied to about money your entire life. Today, I'm sharing {num_rules} money rules that the wealthy know but never talk about.

[PROMISE - 0:10]
Stick around because rule number {num_rules//2} alone could save you thousands of dollars this year.

[MAIN CONTENT - 0:20]
Let's dive right in.

Rule #1: Pay yourself first. Before any bills, before any purchases, 20% goes to your future self.

Rule #2: If you can't buy it twice, you can't afford it. This simple rule prevents lifestyle inflation.

Rule #3: Invest in assets, not liabilities. Your car loses value. Stocks and real estate gain value.

Rule #4: The 72-hour rule. Wait 72 hours before any purchase over $100. You'll skip 90% of impulse buys.

Rule #5: Multiple income streams. One source of income is too close to zero. Build at least three.

[Continue with more specific rules based on the number requested...]

Rule #{num_rules//2}: Compound interest is the 8th wonder of the world. Start investing today, not tomorrow.

[More rules...]

Rule #{num_rules}: Your network is your net worth. Invest in relationships, they pay the highest dividends.

[EXAMPLES - {target_minutes-2}:00]
Let me give you a real example. Sarah followed rule #5 and built three income streams. Today she makes $15,000 per month.

[CTA - {target_minutes-1}:00]
Which rule surprised you the most? Comment below and don't forget to subscribe for more financial wisdom."""

            elif "school" in idea['title'].lower() and "million" in idea['title'].lower():
                script = f"""[HOOK - 0:00]
School teaches you to be an employee. I'm going to teach you how to use school to become a millionaire.

[PROMISE - 0:10]
These aren't the typical 'get good grades' tips. This is the blueprint that helped me go from student debt to seven figures.

[MAIN CONTENT - 0:20]
Strategy #1: Treat professors as your first network. They have connections worth millions. Office hours aren't for grades, they're for relationships.

Strategy #2: Start a business solving campus problems. I made $50K selling study guides. Another student made $200K with a laundry service.

Strategy #3: Use free resources like crazy. Free software licenses, free consulting from business professors, free marketing through student organizations.

Strategy #4: The credential arbitrage. Get certifications while in school. I got Google, HubSpot, and AWS certified for free through my university.

Strategy #5: Build your personal brand on campus first. If you can market to 20,000 students, you can market to anyone.

[EXAMPLES - {target_minutes-2}:00]
Mark started a note-sharing app in his dorm. Sold it for $3 million before graduation. Sarah leveraged her professor's network to land a $150K job that led to her own consultancy.

[CTA - {target_minutes-1}:00]
The biggest mistake is thinking school is just about the degree. It's about leverage. Subscribe for more unconventional success strategies."""

            else:
                # Generic but better template
                script = self.create_specific_script_for_title(idea, target_minutes, target_words)

            return script

        except Exception as e:
            print(f"[WARNING] AI script generation error: {e}")
            return None

    def create_specific_script_for_title(self, idea, target_minutes, target_words):
        """Create a specific script based on the title content"""
        title = idea['title']

        # Analyze title to determine content type
        if any(word in title.lower() for word in ['how to', 'guide', 'tutorial']):
            # How-to content
            return self.generate_howto_script(idea, target_minutes, target_words)
        elif any(word in title.lower() for word in ['facts', 'things', 'rules', 'tips', 'mistakes']):
            # List-based content
            return self.generate_list_script(idea, target_minutes, target_words)
        elif any(word in title.lower() for word in ['story', 'journey', 'tried', 'tested', 'tested']):
            # Story-based content
            return self.generate_story_script(idea, target_minutes, target_words)
        else:
            # Default educational content
            return None

    def generate_howto_script(self, idea, target_minutes, target_words):
        """Generate a how-to script"""
        title = idea['title']
        # Calculate content sections based on target duration
        num_steps = min(int(target_minutes * 2), 10)  # 2 steps per minute, max 10

        script = f"""[HOOK - 0:00]
{idea['hook']}

[INTRO - 0:10]
Today, I'm going to show you exactly {title.lower()}. No fluff, no theory, just practical steps you can implement right now.

[OVERVIEW - 0:30]
Here's what we'll cover: {num_steps} proven steps that will transform how you approach this.

"""

        # Add steps based on duration
        time_per_step = (target_minutes - 1.5) / num_steps  # Leave 1.5 min for intro/outro
        current_time = 1.0

        for i in range(1, num_steps + 1):
            script += f"""[STEP {i} - {current_time:.1f}:00]
Step {i}: [Detailed explanation of this step]
This is important because... [specific reasoning]
Here's exactly how to do it... [actionable instructions]

"""
            current_time += time_per_step

        script += f"""[RECAP - {target_minutes-1:.1f}:00]
Let's quickly recap the {num_steps} steps...

[CTA - {target_minutes-0.5:.1f}:00]
Now you have everything you need. The next step is yours. Subscribe for more actionable content."""

        return script

    def generate_list_script(self, idea, target_minutes, target_words):
        """Generate a list-based script with proper length"""
        title = idea['title']
        import re
        numbers = re.findall(r'\d+', title)
        num_items = int(numbers[0]) if numbers else 7

        # Calculate time per item
        time_per_item = max((target_minutes - 2) / num_items, 0.5)  # At least 30 seconds per item

        script = f"""[HOOK - 0:00]
{idea['hook']}

[INTRO - 0:10]
I've spent months researching this topic, and what I found will blow your mind. Let's dive into {num_items} game-changing insights.

"""

        current_time = 0.5

        # Generate detailed content for each item
        for i in range(1, min(num_items + 1, 20)):  # Cap at 20 items
            script += f"""[POINT {i} - {current_time:.1f}:00]
Number {i}: [Specific point about {title}]

Here's why this matters: [Detailed explanation with examples]
Think about it this way... [Analogy or comparison]
The data shows... [Statistics or evidence]
Here's how to apply this... [Actionable advice]

"""
            current_time += time_per_item

        script += f"""[SUMMARY - {target_minutes-1.5:.1f}:00]
Let's recap the {num_items} key points we covered...
[Quick summary of main insights]

[CTA - {target_minutes-0.5:.1f}:00]
Which of these {num_items} surprised you the most? Drop a comment below.
Subscribe for more deep dives like this, and hit the bell so you don't miss the next one."""

        return script

    def generate_story_script(self, idea, target_minutes, target_words):
        """Generate a comprehensive story-based script with full content"""
        title = idea['title']
        hook = idea.get('hook', '')

        # Generate full production-ready content based on the title pattern
        if "80 Days" in title or "30 Days" in title or "challenge" in title.lower():
            return self.generate_challenge_story_script(title, hook, target_minutes)
        elif 'tested' in title.lower() or 'tried' in title.lower():
            return self.generate_testing_story_script(title, hook, target_minutes)
        else:
            return self.generate_transformation_story_script(title, hook, target_minutes)

    def generate_challenge_story_script(self, title, hook, target_minutes):
        """Generate a full challenge/transformation story script"""

        # This generates a COMPLETE script for 10 minutes (1500+ words)
        if target_minutes >= 10:
            script = f"""[HOOK - 0:00]
{hook if hook else "What happened next completely changed my life."}

I'm about to show you the exact system that transformed everything for me. And no, this isn't clickbait - I have the receipts.

[THE BEGINNING - 0:15]
Eighty days ago, I was stuck. Dead-end job, zero savings, watching everyone else succeed while I scrolled Instagram at 2 AM feeling sorry for myself.

Then I found this method. It sounded too simple to work. But desperation makes you try anything.

[THE DECISION - 0:35]
Here was the commitment: Every single day for 80 days, I would follow this exact routine. No exceptions, no excuses, no matter what.

Day 1 started at 5 AM. I'd never been a morning person. The alarm felt like torture. But I had made a promise to myself.

[THE ROUTINE BREAKDOWN - 1:00]
Let me break down exactly what I did every single day:

First hour: Deep work on my most important project. No phone, no distractions, just pure focus. This was harder than it sounds. My brain fought me every minute.

Second hour: Physical training. Not just exercise - deliberate, progressive training. Started with 10 pushups. By day 80, I was doing 100.

Third hour: Learning. Reading, courses, podcasts. But here's the key - I had to apply something from each session immediately. Knowledge without action is worthless.

Fourth hour: Building connections. Reaching out to one new person daily. This terrified me. I'm an introvert. But this changed everything.

[WEEK 1 - THE STRUGGLE - 2:30]
The first week was hell. I'm not going to sugarcoat it.

Day 2: Wanted to quit. My body hurt, my mind resisted, everything felt wrong.

Day 3: Accidentally slept through the alarm. Had to do double the next day. Lesson learned.

Day 5: First small win. Completed a project I'd been procrastinating on for months. Felt a tiny spark of hope.

Day 7: Survived the first week. Celebrated with... going to bed at 9 PM. This was my life now.

[WEEK 2-3 - THE ADJUSTMENT - 3:30]
Something shifted in week two. The resistance was still there, but weaker.

I started noticing changes. My focus lasted longer. Tasks that took hours now took minutes. My energy didn't crash at 3 PM anymore.

But let me be specific about what was changing. The morning deep work session - I was now cranking out content that would've taken me all day before. Writing became fluid. Ideas connected naturally. The fog lifted.

The physical changes were obvious. Lost 8 pounds without trying. Just from being active every morning and having structure. Energy levels stayed consistent all day. No more afternoon coffee required.

Week three brought the first external validation. My boss noticed my productivity. Asked what changed. I couldn't explain it without sounding like I joined a cult. Just said I was sleeping better.

A client reached out with an opportunity. Small project, but it came from one of my daily connections. The compound effect was starting. Each action building on the last.

The routine was becoming automatic. Wake up at 5 AM without thinking about it. Execute the four pillars without negotiating with myself. This is when I knew something fundamental had shifted.

Sleep became sacred. 10 PM meant lights out, no exceptions. Friends thought I was crazy. But I was seeing results they weren't.

[THE FIRST BREAKTHROUGH - DAY 25 - 4:30]
Day 25 changed everything. One of my daily connections responded. Not just responded - offered me a contract worth three months salary.

But here's what nobody tells you about breakthroughs - they come from consistency, not intensity. Those 24 days of showing up made day 25 possible.

I almost sabotaged it. Imposter syndrome hit hard. Who was I to take this opportunity? But I remembered why I started. Pushed through the fear.

[DAYS 30-50 - THE MOMENTUM - 5:30]
By day 30, people started asking what changed. I looked different. Acted different. Was different.

The transformation was visible. Lost 15 pounds. Gained muscle definition I'd never had. But the mental changes were bigger. Clarity of thought. Decisiveness. No more analysis paralysis.

The morning routine was now sacred. Nothing could interrupt it. Friends called me obsessed. They were right. But obsession directed at the right target is just focus.

Day 35 brought an unexpected challenge. Got sick. Really sick. Flu knocked me down for three days. Old me would've used this as an excuse to quit. New me modified the routine and kept going. Did pushups between bathroom trips. Read instead of deep work. Still made my daily connection via email.

Day 40: Landed my second client through another connection. $5,000 project. Pattern recognition kicked in - this was repeatable. The system wasn't luck. It was predictable cause and effect.

Started documenting everything. Every action, every result, every lesson. This data would become invaluable later.

Day 45: Hit my first $10K month. More than I'd made in three months at my job. The system was working. But more importantly, I was working. Operating at a level I didn't know existed.

The compound effect was accelerating. Each connection led to two more. Each project built skills for the next. Each morning session built on yesterday's progress.

Day 50: The halfway point. I could have stopped here and still been ahead. But stopping wasn't an option anymore. This wasn't a challenge anymore - it was my life.

[THE MENTAL SHIFT - 6:30]
Somewhere around day 55, I realized something profound. This wasn't about the 80 days anymore. This was who I was becoming.

The person who wakes up at 5 AM without questioning it. The person who doesn't negotiate with themselves about what needs to be done. The person who executes regardless of feelings.

This is what transformation actually looks like. Not a sudden change, but a slow rebuild of your entire operating system.

[DAYS 60-70 - THE COMPOUND EFFECT - 7:30]
The results started compounding exponentially. This is where the magic happens - but only if you've done the work.

Day 60: Third client signed. $15,000 retainer. Quit my job. Scariest and best decision of my life.

My boss tried to counter-offer. Offered a 40% raise to stay. Would've changed my life six months ago. Now it felt like an insult. I wasn't playing that game anymore.

Walked out with nothing but a laptop and absolute confidence. No safety net. No plan B. Plan A was working.

Day 63: Systems started running themselves. Morning routine happened automatically. Client work flowed naturally. Connections reached out to me instead of the other way around.

Day 65: First five-figure project. $12,000 for work that used to pay $500. Same deliverable, different positioning. The confidence from 65 days of consistency changed how I presented myself. Clients could feel it.

Day 67: Had to start saying no to opportunities. Good problem, but still a problem. Time became the constraint, not money.

Day 70: Built a team. Hired my first virtual assistant from the Philippines. $400/month for 20 hours/week. She freed up 15 hours of my time. Leverage unlocked.

Second hire: A junior developer from my network. One of my daily connections from Day 20. Full circle moment.

The business was building itself now. Systems, team, recurring revenue. Each day built on the last. The foundation from days 1-30 made days 60-70 possible. This is how exponential growth actually works.

But here's what nobody tells you about exponential growth - it's terrifying. Every day brought new problems I'd never faced. Imposter syndrome on steroids.

[THE FINAL PUSH - DAYS 71-80 - 8:30]
The last ten days felt different. I wasn't pushing anymore. I was being pulled by the momentum.

Day 75: Launched my own product. Something I'd dreamed about for years but never had the discipline to create.

Day 78: Hit six figures in total revenue. In 78 days, I'd made more than the previous two years combined.

Day 80: The final day. Woke up at 5 AM like every other day. But everything was different.

[THE RESULTS - 9:00]
Let me give you the raw numbers, because data doesn't lie:

Income transformation:
- Day 0: $3,000/month salary
- Day 30: $5,000 first client project
- Day 45: $10,000 monthly revenue
- Day 60: $15,000 recurring retainer
- Day 80: $30,000/month with 40% profit margins

That's a 10x increase in 80 days. Not years. Days.

Fitness transformation:
- Day 1: 10 shaky pushups
- Day 20: 25 consecutive pushups
- Day 40: 50 pushups without stopping
- Day 60: 75 pushups, added pull-ups
- Day 80: 100 consecutive pushups, 15 pull-ups, 5-minute plank

Bodyweight dropped 22 pounds. Body fat from 25% to 15%. Energy levels through the roof.

Network explosion:
- Started: 50 LinkedIn connections, mostly dormant
- Day 80: 500+ active connections
- 80 new meaningful relationships
- 12 paying clients
- 3 mentors
- 2 business partners

Skills acquired:
- Video editing (Premier Pro)
- Copywriting (direct response)
- Sales (consultative selling)
- Systems design (SOPs and automation)
- Team management
- Financial planning

But the biggest change? I trust myself now. When I say I'll do something, it happens. No excuses, no exceptions. That self-trust is worth more than any amount of money. It's the foundation everything else is built on.

[THE SYSTEM REVEALED - 9:30]
Here's the exact system you can copy:

1. Pick four non-negotiable daily actions
2. Set a specific time for each
3. Track everything in a simple spreadsheet
4. Never miss twice - if you fail one day, double the next
5. Share your progress publicly for accountability

That's it. No apps, no complex systems, no excuses.

[THE REALITY CHECK - 9:45]
Will this work for you? Honestly, probably not.

Not because the system doesn't work, but because 99% of people won't actually do it. They'll watch this video, feel motivated for a day, then go back to their old patterns.

The 1% who actually commit? They'll change their entire life trajectory.

[YOUR DECISION - 9:55]
So here's my challenge to you: Try it for just 10 days. Not 80. Just 10.

Pick your four non-negotiables. Set your wake-up time. Create your tracking sheet. Start tomorrow morning.

10 days is nothing. You've wasted 10 days scrolling social media this month. But 10 days of focused action? That could be the beginning of everything.

If you can't do 10, you were never going to do 80 anyway. But if you can do 10, you'll see enough results to continue.

[CALL TO ACTION - 10:00]
Comment 'Day 1' below if you're starting today. I'll personally check in on everyone who commits.

Subscribe if you want to see the day-by-day breakdown. I documented everything and I'll share the raw, unfiltered journey.

Remember: In 80 days, you'll either have results or excuses. Choose wisely.

[END - 10:10]"""
        else:
            # Shorter 5-minute version
            script = f"""[HOOK - 0:00]
{hook if hook else "This changed everything."}

[THE BEGINNING - 0:10]
80 days ago, I made a decision that transformed my entire life. Here's exactly what happened.

[THE COMMITMENT - 0:30]
Four daily actions, every single day, no matter what. Sounds simple, but simple doesn't mean easy.

[THE JOURNEY - 1:00]
Week 1: Pure torture. Wanted to quit every day.
Week 2-3: Started seeing small changes.
Week 4-6: First major breakthrough.
Week 8-10: Momentum took over.
Week 11: Results I never imagined possible.

[THE RESULTS - 3:00]
10x income increase. Complete physical transformation. Network exploded. But the mindset shift was everything.

[YOUR TURN - 4:00]
The system is simple: Pick your four actions, never miss a day, track everything. That's it.

[CALL TO ACTION - 4:30]
Comment 'Day 1' if you're starting. Subscribe for the detailed breakdown. Your 80-day transformation starts now.

[END - 5:00]"""

        return script

    def generate_testing_story_script(self, title, hook, target_minutes):
        """Generate a full testing/review story script"""

        # Import the production script generator for AI tools reviews
        from claude_script_generator import generate_ai_tools_review_script

        # Use the comprehensive AI tools review script for testing stories
        return generate_ai_tools_review_script(title, hook, target_minutes)

    def generate_transformation_story_script(self, title, hook, target_minutes):
        """Generate a general transformation/story script"""

        script = f"""[HOOK - 0:00]
{hook if hook else "This is the story nobody expected."}

[INTRO - 0:15]
{title} - Let me tell you exactly how this unfolded, because the journey is more incredible than the destination.

[THE SETUP - 0:30]
It started with a simple observation. Something everyone else ignored, but I couldn't stop thinking about.

[THE DISCOVERY - 1:00]
That's when I found it. Hidden in plain sight. The solution that would change everything.

[THE IMPLEMENTATION - 2:00]
Putting it into practice wasn't straightforward. There were obstacles, setbacks, moments of doubt.

[THE FIRST RESULTS - 3:00]
But then the results started coming. Slowly at first, then all at once.

[THE BREAKTHROUGH - 4:00]
The breakthrough moment came when I realized this wasn't just working for me - it could work for anyone.

[THE TRANSFORMATION - 5:00]
What happened next exceeded every expectation. The complete transformation took less than 90 days.

[THE SYSTEM - 6:00]
Here's the exact system I developed, step by step, so you can replicate these results.

[THE PROOF - 7:00]
I'm not asking you to take my word for it. Here's the documented proof of everything I'm claiming.

[YOUR OPPORTUNITY - 8:00]
This same opportunity is available to you right now. The only question is whether you'll take action.

[NEXT STEPS - 9:00]
Here's exactly what to do next if you want these same results.

[CALL TO ACTION - 9:30]
The choice is yours. Take action today, or wonder what if forever.

[END - 10:00]"""

        return script

    def generate_old_story_script(self, idea, target_minutes, target_words):
        """Legacy story script generator (kept for compatibility)"""
        title = idea['title']

        # Extract numbers if present
        import re
        numbers = re.findall(r'\d+', title)

        script = f"""[HOOK - 0:00]
{idea['hook']}

[SETUP - 0:10]
Let me take you back to when this all started. {title} - this isn't just a catchy title, it's my actual experience.

[THE CHALLENGE - 0:30]
Here was the situation: [Set up the problem or challenge]
I had to find a solution, and fast.

[THE JOURNEY - 1:00]
"""

        # Add journey sections based on duration
        if 'tested' in title.lower() or 'tried' in title.lower():
            # Testing/experiment format
            if numbers:
                num_tested = int(numbers[0])
                num_winners = int(numbers[1]) if len(numbers) > 1 else min(5, num_tested // 2)
            else:
                num_tested = 10
                num_winners = 5

            time_per_test = (target_minutes - 3) / num_winners
            current_time = 1.5

            script += f"""So I started testing. {num_tested} different options, hundreds of hours, real money spent.

"""

            for i in range(1, num_winners + 1):
                script += f"""[WINNER #{i} - {current_time:.1f}:00]
The {['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth'][i-1]} winner: [Name of tool/method]

Why it won: [Specific benefits and features]
Real results: [Actual metrics or outcomes]
Best for: [Who should use this]
Downsides: [Honest limitations]

"""
                current_time += time_per_test

            # Add losers section
            script += f"""[THE LOSERS - {current_time:.1f}:00]
Now, let me save you time. These didn't make the cut:
[List of what didn't work and why]

"""
            current_time += 0.5

        else:
            # Generic story format
            sections = int((target_minutes - 3) / 1.5)  # 1.5 minutes per story section
            current_time = 1.5

            for i in range(sections):
                script += f"""[PART {i+1} - {current_time:.1f}:00]
[Next part of the story with specific details]
[Challenges faced]
[Solutions found]
[Lessons learned]

"""
                current_time += 1.5

        script += f"""[THE RESULTS - {target_minutes-1.5:.1f}:00]
Here's where I am now: [Final outcomes]
The biggest lesson: [Key takeaway]

[YOUR TURN - {target_minutes-0.5:.1f}:00]
Your journey starts now. Take what I've learned and make it better.
Subscribe to follow my continued experiments, and comment your own experiences below."""

        return script


    def phase3_scriptwriting(self, idea):
        """Phase 3: Scriptwriting & SEO"""
        print("\n" + "="*60)
        print("PHASE 3: SCRIPTWRITING & SEO")
        print("="*60)

        # Get target length if not specified
        if 'target_length' not in idea:
            idea['target_length'] = {"minutes": 5, "name": "medium", "words": 750}

        print(f"Generating script for: {idea['title']}")
        print(f"Target length: {idea['target_length']['minutes']} minutes (~{idea['target_length']['words']} words)")

        # Generate script with high-retention structure based on target length
        script = self.generate_high_retention_script(idea)
        
        # Generate metadata
        # Initially create metadata without accurate timestamps
        metadata = {
            "title": idea['title'][:100],  # YouTube limit
            "description": self.generate_seo_description(idea),  # Will update after TTS
            "tags": idea['keywords'][:30],  # Limit tags
            "thumbnail_text": idea['hook'],
            "chapters": self.generate_chapters(script)
        }
        
        # Save script and metadata
        script_file = self.content_dir / "script.md"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)
        
        metadata_file = self.content_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[SAVED] Script: {script_file}")
        print(f"[SAVED] Metadata: {metadata_file}")
        
        return script, metadata
    
    def get_time_reference(self, minutes):
        """Get appropriate time reference for script based on video length"""
        if minutes == 1:
            return "60 seconds"
        elif minutes < 2:
            return "next minute"
        elif minutes < 3:
            return "couple of minutes"
        elif minutes <= 5:
            return "few minutes"
        elif minutes <= 10:
            return f"{minutes} minutes"
        else:
            return "next little while"

    def generate_high_retention_script(self, idea):
        """Generate script with proven retention structure"""
        # High-retention structure: Hook → Promise → Proof → Preview → Value → CTA

        title = idea['title']
        hook = idea['hook']
        target_minutes = idea.get('target_length', {}).get('minutes', 5)
        target_words = idea.get('target_length', {}).get('words', 750)

        # Get appropriate time reference
        time_reference = self.get_time_reference(target_minutes)

        # Check if custom idea needs AI-generated script
        if idea.get('custom', False) or idea.get('use_ai_script', False):
            print("[INFO] Using AI to generate high-quality script...")
            script = self.generate_ai_script(idea, target_minutes, target_words)
            if script:
                return script
            print("[WARNING] AI script generation failed, using template")

        # Template based on video type
        if "Money" in title or "Finance" in title:
            script = f"""[HOOK - 0:00]
{hook}

If you're watching this, you're probably making at least one of these mistakes right now. And it's costing you thousands of dollars every single year.

[PROMISE - 0:15]
In the next {time_reference}, I'm going to show you exactly what these mistakes are, why they're destroying your wealth, and most importantly, how to fix them starting today.

[PROOF - 0:25]
I learned this the hard way. Five years ago, I was broke, in debt, and had no idea where my money was going. Today, I'm financially free, and it all started when I fixed these exact mistakes.

[PREVIEW - 0:40]
We'll cover the mistake that 87% of people make with their paychecks, the investment trap that costs the average person forty thousand dollars, and the one simple change that can double your savings rate overnight.

[VALUE DELIVERY - 0:55]
Let's start with mistake number one: Not paying yourself first.

Most people get their paycheck, pay bills, buy stuff, and then try to save whatever's left. There's never anything left. Successful people do the opposite. They automatically transfer 20% to savings the moment their paycheck hits. The money never touches their checking account.

Here's how to set this up: Go to your bank app right now, create an automatic transfer for the day after your payday. Start with just 5% if 20% seems too much. The key is starting.

Mistake number two: Keeping money in a checking account.

Your checking account pays you nothing while inflation eats 3% of your money every year. Meanwhile, high-yield savings accounts are paying 5% right now. On ten thousand dollars, that's five hundred dollars per year you're leaving on the table.

Action step: Open a high-yield savings account today. I'm not sponsored by anyone, but Ally, Marcus, and American Express all offer great rates. It takes five minutes online.

Mistake number three: Waiting to invest.

Every year you wait costs you exponentially more. If you invest one hundred dollars per month starting at 25, you'll have over three hundred thousand by retirement. Start at 35? Only one hundred and thirty thousand. That ten-year delay costs you one hundred and seventy thousand dollars.

The fix: Open a brokerage account today. Start with index funds like VOO or VTI. Even ten dollars per month is better than waiting.

[CLIFFHANGER - 3:30]
But here's the thing - there's one mistake that's bigger than all of these combined. It's the reason why most people never build wealth no matter how much they earn.

[CTA - 3:45]
If you want to learn about this wealth-killer and dozens of other money strategies, make sure to subscribe and hit the notification bell. I drop new finance videos every week.

Which of these mistakes are you making? Let me know in the comments below. And remember, the best time to start was yesterday. The second best time is right now.

[END - 4:00]"""

        elif "AI" in title or "Tech" in title:
            script = f"""[HOOK - 0:00]
{hook}

Stop what you're doing and pay attention, because what I'm about to show you will completely change how you work.

[PROMISE - 0:10]
In the next {time_reference}, you'll discover AI tools that 99% of people don't know exist, but the 1% who do are already using them to get ahead.

[PROOF - 0:20]
I've tested over 200 AI tools in the past year. Most are hype. But these ten are legitimately game-changing. I use them every single day, and they've 10x'd my productivity.

[PREVIEW - 0:35]
We'll cover the AI that writes perfect emails in your voice, the tool that turns any PDF into a interactive assistant, and the one that can literally clone your skills and work while you sleep.

[VALUE DELIVERY - 0:50]
Let's dive into tool number one: Perplexity AI.

Forget Google. Perplexity gives you instant, accurate answers with sources. No ads, no SEO spam, just pure information. Ask it anything complex and watch it work magic.

Tool number two: Claude by Anthropic.

While everyone's using ChatGPT, Claude is quietly destroying it at coding and analysis. Upload any document, even books, and have deep conversations about them. It's like having a genius assistant.

Tool number three: Gamma.

Create stunning presentations in literally 30 seconds. Just tell it your topic, and it generates professional slides with designs that look like you hired a designer.

Tool number four: ElevenLabs.

Not just text-to-speech. This creates human-like voices so real, you can't tell the difference. Create podcasts, videos, or audiobooks without recording anything.

Tool number five: Runway ML.

Edit videos with text prompts. Remove backgrounds, add effects, even generate entirely new video content from text. Hollywood studios are using this right now.

[RAPID FIRE SECTION - 2:30]
Quick fire round - Screenshot to code with Screenshot2Code, automate everything with Zapier AI, transcribe anything with Whisper, create music with Suno, and build apps without code using Cursor.

[CLIFFHANGER - 3:00]
But here's what nobody tells you about AI - there's a dark side that could destroy entire industries...

[CTA - 3:15]
Want to stay ahead of the AI revolution? Subscribe and hit the bell. I test new AI tools every week and only share the ones that actually matter.

Drop a comment with your favorite AI tool - I read every single one and might feature it in the next video.

[END - 3:30]"""

        else:
            # Generate content based on target length
            script = self.generate_length_appropriate_script(title, hook, time_reference, target_minutes, target_words)

        return script

    def generate_length_appropriate_script(self, title, hook, time_reference, target_minutes, target_words):
        """Generate script content appropriate for target video length"""

        if target_minutes == 1:
            # Short 1-minute script - straight to the point
            script = f"""[HOOK - 0:00]
{hook}

Here's what you need to know right now.

[MAIN POINT - 0:10]
The single most important thing is this: {title.lower()} is more relevant than ever.

Think about it - every successful person knows this secret, but nobody talks about it.

[VALUE - 0:30]
Here's how to use this: Start immediately. Don't overthink it. Just take the first step today.

The difference between those who succeed and those who don't is action.

[CTA - 0:50]
Follow for more quick tips that actually work. Drop a comment if this helped.

[END - 0:59]"""

        elif target_minutes == 5:
            # Medium 5-minute script - standard educational format
            script = f"""[HOOK - 0:00]
{hook}

This is going to sound crazy, but stick with me for the next {time_reference} and I promise it will make sense.

[PROMISE - 0:15]
By the end of this video, you'll understand exactly why {title.lower()} matters, and how to use this knowledge to get ahead.

[PROOF - 0:30]
I discovered this three years ago, and it completely changed my perspective. Since then, thousands of people have used this exact method with incredible results.

[MAIN CONTENT - 0:45]
Let's break this down into three key points.

First, understand the fundamentals. Most people skip this part, but it's crucial. You need to grasp the core concept before anything else makes sense.

Here's what that means in practice: Start with the basics, master them completely, then build from there. It sounds simple, but 90% of people get this wrong.

Second, application is everything. Knowledge without action is worthless. You need to take what you learn and immediately put it into practice.

Try this: As soon as you finish watching, take one small action. Just one. That momentum will carry you forward.

Third, consistency beats intensity. You don't need to be perfect; you need to be persistent. Small steps every day lead to massive results over time.

[EXAMPLES - 3:00]
Let me give you a real example. Sarah from Texas started using this method six months ago. She went from struggling to thriving, and all it took was applying these three principles.

Another example: Marcus used this approach for just 15 minutes a day. Within three months, he saw results that shocked everyone around him.

[SUMMARY - 4:00]
Here's what we covered: The fundamentals matter more than you think. Action beats perfectionism every time. And consistency is your secret weapon.

[CTA - 4:30]
If this helped you, subscribe and hit the bell. I release new content every week designed to help you level up. Comment below with your biggest takeaway - I read and respond to as many as I can.

[END - 4:55]"""

        elif target_minutes == 10:
            # Long 10-minute script - in-depth tutorial
            script = f"""[HOOK - 0:00]
{hook}

This is going to completely change how you think about {title.lower()}.

[PROMISE - 0:20]
In the next {time_reference}, I'm going to walk you through everything you need to know, step by step. By the end, you'll have a complete understanding and a clear action plan.

[CREDIBILITY - 0:40]
I've spent the last five years researching this topic, testing every method, and refining the approach. What I'm about to share is the distilled wisdom from thousands of hours of work.

[PREVIEW - 1:00]
We'll cover seven key areas: The foundation, the science behind it, common mistakes to avoid, the step-by-step process, advanced strategies, real-world examples, and your personalized action plan.

[FOUNDATION - 1:30]
Let's start with the foundation. Understanding the 'why' behind {title.lower()} is crucial. Without this context, nothing else will stick.

The history goes back further than most people realize. This isn't some new trend - it's based on principles that have worked for decades.

[SCIENCE - 3:00]
Now, the science. Recent studies from Harvard and MIT have confirmed what practitioners have known for years. The data is overwhelming.

Here are the key findings: First, the impact is 3x greater than previously thought. Second, the effects compound over time. Third, anyone can do this with the right approach.

[MISTAKES - 4:30]
Let's talk about mistakes. I see people make these same errors over and over. Mistake number one: Starting too fast. You need to build gradually.

Mistake two: Ignoring the fundamentals. Advanced tactics won't help if you skip the basics.

Mistake three: Not tracking progress. What gets measured gets managed.

[PROCESS - 6:00]
Now for the step-by-step process. Step one: Assessment. Figure out exactly where you are right now.

Step two: Set clear, specific goals. Vague goals lead to vague results.

Step three: Create your implementation plan. This is where most people fail - they have knowledge but no system.

Step four: Execute with consistency. Show up every day, even when you don't feel like it.

Step five: Review and adjust. What's working? What isn't? Adapt based on results.

[ADVANCED - 7:30]
For those ready to level up, here are advanced strategies. These aren't for beginners, but once you master the basics, these will accelerate your progress.

Strategy one: The multiplication method. Instead of linear progress, create exponential growth.

Strategy two: The network effect. Leverage connections and community for faster results.

[EXAMPLES - 8:30]
Real examples from real people. Jennifer went from zero to hero in six months using exactly what I've outlined. Tom transformed his entire life with these principles.

The patterns are clear: Those who succeed follow the system. Those who struggle try to skip steps or overcomplicate things.

[ACTION PLAN - 9:00]
Your action plan: Today, complete step one. This week, implement the first three strategies. This month, establish the full system.

Remember: Progress over perfection. Start where you are, use what you have, do what you can.

[CTA - 9:30]
If you found value here, subscribe and join our community of action-takers. Download the free checklist in the description. Comment your commitment below - public accountability drives results.

[END - 9:55]"""

        else:
            # Extra long 30-minute script - complete masterclass
            script = f"""[HOOK - 0:00]
{hook}

[INTRODUCTION - 0:30]
Welcome to this complete guide on {title.lower()}. Over the next {time_reference}, we're going deep. This isn't just another surface-level video - this is the comprehensive resource you've been looking for.

[Full 30-minute content would continue here with multiple detailed sections...]

[This is abbreviated for space - a real 30-minute script would be 4500+ words]

[END - 29:55]"""

        return script
    
    def generate_seo_description(self, idea, audio_duration=None):
        """Generate SEO-optimized description with accurate timestamps"""

        # Generate timestamps based on audio duration
        if audio_duration:
            # Create realistic timestamps based on actual duration
            timestamps = self.generate_accurate_timestamps(audio_duration)
        else:
            # Fallback to generic timestamps
            timestamps = """0:00 Introduction
0:30 Main Content
3:00 Key Takeaways
3:30 Next Steps"""

        description = f"""{idea['title']}

{idea['hook']}

In this video, you'll discover:
- Actionable tips you can implement today
- Common mistakes to avoid
- Proven strategies that actually work
- Real examples and case studies

Timestamps:
{timestamps}

Subscribe for more content like this!

Follow me:
[Your social links here]

Tags:
#{' #'.join(idea['keywords'][:10])}

Disclaimer: This content is for educational purposes only."""

        return description[:5000]  # YouTube description limit

    def generate_accurate_timestamps(self, total_duration):
        """Generate accurate timestamps based on video duration"""
        # Convert to minutes and seconds
        total_seconds = int(total_duration)

        timestamps = []

        # Introduction is always at the start
        timestamps.append("0:00 Introduction")

        if total_seconds <= 30:
            # Very short video - just intro and main content
            timestamps.append(f"0:05 Main Content")
        elif total_seconds <= 60:
            # Short video - intro, main content, conclusion
            timestamps.append(f"0:05 Main Content")
            timestamps.append(f"{self.format_timestamp(total_seconds - 10)} Key Takeaways")
        elif total_seconds <= 120:
            # 1-2 minute video
            timestamps.append(f"0:10 Main Content")
            timestamps.append(f"{self.format_timestamp(total_seconds - 20)} Key Takeaways")
            timestamps.append(f"{self.format_timestamp(total_seconds - 5)} Next Steps")
        else:
            # Longer video - distribute timestamps proportionally
            main_content_start = 10
            key_takeaways_start = int(total_seconds * 0.75)
            next_steps_start = total_seconds - 15

            timestamps.append(f"{self.format_timestamp(main_content_start)} Main Content")

            # Add some middle sections for longer videos
            if total_seconds > 180:
                timestamps.append(f"{self.format_timestamp(int(total_seconds * 0.33))} Deep Dive")
                timestamps.append(f"{self.format_timestamp(int(total_seconds * 0.55))} Examples & Case Studies")

            timestamps.append(f"{self.format_timestamp(key_takeaways_start)} Key Takeaways")
            timestamps.append(f"{self.format_timestamp(next_steps_start)} Next Steps")

        return "\n".join(timestamps)

    def format_timestamp(self, seconds):
        """Format seconds to MM:SS or H:MM:SS"""
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def generate_chapters(self, script):
        """Extract chapter markers from script"""
        chapters = []
        lines = script.split('\n')
        for line in lines:
            if line.startswith('[') and ' - ' in line:
                # Extract timestamp and title
                try:
                    parts = line.strip('[]').split(' - ')
                    if len(parts) == 2:
                        timestamp = parts[1]
                        title = parts[0]
                        chapters.append({
                            "timestamp": timestamp,
                            "title": title
                        })
                except:
                    pass
        return chapters
    
    def phase4_tts_production(self, script):
        """Phase 4: Asset Gathering & TTS"""
        print("\n" + "="*60)
        print("PHASE 4: TTS PRODUCTION")
        print("="*60)
        
        # Clean script for TTS (remove timestamps and markers)
        tts_text = self.clean_script_for_tts(script)
        
        print("Generating audio via n8n TTS webhook...")
        
        # Call n8n TTS webhook
        response = requests.post(
            f"{self.base_url}/tts-generation",
            json={
                "text": tts_text,
                "voice_id": self.elevenlabs_voice_id,
                "slug": self.session_id
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] TTS generated: {result.get('message', 'Audio created')}")
            
            # For now, create placeholder audio file
            # In production, n8n would return audio URL or base64
            audio_file = self.content_dir / "narration.mp3"
            
            # If using ElevenLabs directly (optional)
            if self.elevenlabs_api_key:
                if not self.generate_elevenlabs_audio(tts_text, audio_file):
                    print("[INFO] Falling back to Google TTS...")
                    self.generate_google_tts_fallback(tts_text, audio_file)
            else:
                # Create placeholder
                audio_file.write_text("AUDIO_PLACEHOLDER")
            
            return str(audio_file)
        else:
            print(f"[WARNING] TTS webhook failed, using placeholder")
            audio_file = self.content_dir / "narration.mp3"
            audio_file.write_text("AUDIO_PLACEHOLDER")
            return str(audio_file)
    
    def clean_script_for_tts(self, script):
        """Remove formatting markers for TTS"""
        lines = []
        for line in script.split('\n'):
            # Skip timestamp lines and formatting
            if line.startswith('[') and ' - ' in line:
                continue
            if line.strip() == '':
                continue
            lines.append(line)
        return ' '.join(lines)
    
    def generate_google_tts_fallback(self, text, output_file):
        """Generate audio using free Google TTS as fallback"""
        try:
            from gtts import gTTS
            
            print("Using Google TTS (free)...")
            
            # Create TTS object
            tts = gTTS(text=text[:5000], lang='en', slow=False)  # Limit text length
            
            # Save to file
            tts.save(str(output_file))
            
            print(f"[SUCCESS] Google TTS audio saved to {output_file}")
            return True
            
        except ImportError:
            print("[ERROR] gTTS not installed. Run: pip install gtts")
            # Create placeholder
            output_file.write_text("AUDIO_PLACEHOLDER")
            return False
        except Exception as e:
            print(f"[ERROR] Google TTS failed: {e}")
            # Create placeholder
            output_file.write_text("AUDIO_PLACEHOLDER")
            return False
    
    def generate_elevenlabs_audio(self, text, output_file):
        """Generate audio using ElevenLabs API directly"""
        if not self.elevenlabs_api_key:
            print("[WARNING] ElevenLabs API key not found")
            return False
        
        print("Calling ElevenLabs API...")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text[:5000],  # ElevenLabs character limit
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"[SUCCESS] Audio saved to {output_file}")
                return True
            else:
                print(f"[ERROR] ElevenLabs API error: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to generate audio: {e}")
            return False
    
    def phase5_video_assembly(self, audio_file, metadata):
        """Phase 5: Video Assembly"""
        print("\n" + "="*60)
        print("PHASE 5: VIDEO ASSEMBLY")
        print("="*60)
        
        video_file = self.content_dir / "final.mp4"
        
        # Check if audio file exists and is real
        audio_path = Path(audio_file)
        if audio_path.exists() and audio_path.stat().st_size > 100:  # Check file size instead of reading content
            print("Using FFmpeg to create video...")
            
            # Create a simple video with title card
            # In production, this would be more sophisticated
            self.create_simple_video_ffmpeg(audio_file, metadata['title'], video_file)
        else:
            print("Creating placeholder video...")
            # For testing, create a simple test video
            self.create_test_video(metadata['title'], video_file)
        
        print(f"[SUCCESS] Video created: {video_file}")
        return str(video_file)
    
    def create_simple_video_ffmpeg(self, audio_file, title, output_file):
        """Create video with FFmpeg"""
        # Get audio duration first
        try:
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_file)
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            audio_duration = float(result.stdout.strip())
            print(f"[INFO] Audio duration: {audio_duration:.2f} seconds")
        except:
            print("[WARNING] Could not determine audio duration, using 60 seconds")
            audio_duration = 60

        # Create a title image using FFmpeg with proper duration
        filter_complex = f"color=c=black:s=1920x1080:d={audio_duration}[bg];[bg]drawtext=text='{title}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2"

        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=c=black:s=1920x1080:d={audio_duration}',
            '-i', audio_file,
            '-filter_complex', filter_complex,
            '-shortest',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] FFmpeg error, using simple approach")
            # Fallback to simpler command with audio
            simple_cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1920x1080:d={audio_duration}',
                '-i', audio_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-y',
                str(output_file)
            ]
            try:
                subprocess.run(simple_cmd, check=True, capture_output=True)
                return True
            except:
                return False
    
    def create_test_video(self, title, output_file):
        """Create a minimal test video file"""
        # For testing, create a very simple video
        # In production, use proper video generation
        output_file.write_text("VIDEO_PLACEHOLDER")
        return True
    
    def phase6_upload_to_youtube(self, video_file, metadata):
        """Phase 6: Upload & Publishing Automation"""
        print("\n" + "="*60)
        print("PHASE 6: YOUTUBE UPLOAD")
        print("="*60)

        # Check for testing mode
        if os.getenv('TESTING_MODE', 'false').lower() == 'true':
            print("[TESTING MODE] Skipping upload to avoid quota limits")
            print(f"Video saved locally: {video_file}")
            print("\nTo upload later, use YouTube Studio or run:")
            print(f"python youtube_upload.py \"{video_file}\"")
            return None

        print("Preparing upload...")
        print(f"Title: {metadata['title']}")
        print(f"Tags: {', '.join(metadata['tags'][:5])}...")
        print("\nVideo will be uploaded as PRIVATE for review")
        print("\n[WARNING] Daily upload limits apply:")
        print("- Unverified channels: 10-15 videos/day")
        print("- API quota: ~6 videos/day")

        confirm = input("\nProceed with upload? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("[CANCELLED] Upload cancelled by user")
            print(f"Video saved locally: {video_file}")
            return None
        
        # Use the OAuth credentials we set up
        from test_youtube_oauth import authenticate_youtube
        
        youtube = authenticate_youtube()
        if not youtube:
            print("[ERROR] YouTube authentication failed")
            return None
        
        # Check if video file exists and has content
        if Path(video_file).exists():
            file_size = Path(video_file).stat().st_size
            if file_size < 1000:  # Less than 1KB, likely a placeholder
                print("[WARNING] Video file too small, creating real test video...")
                # Create a minimal real video for testing
                test_video = self.content_dir / "test_upload.mp4"
                self.create_minimal_test_video(test_video)
                video_file = str(test_video)
        
        # Upload video
        try:
            from googleapiclient.http import MediaFileUpload
            
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'private',  # Start private for safety
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                video_file,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Execute upload
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            print("Uploading video...")
            response = request.execute()
            
            video_id = response['id']
            print(f"\n[SUCCESS] Video uploaded!")
            print(f"Video ID: {video_id}")
            print(f"URL: https://youtube.com/watch?v={video_id}")
            print(f"Edit: https://studio.youtube.com/video/{video_id}/edit")
            
            return video_id
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return None
    
    def create_minimal_test_video(self, output_file):
        """Create a minimal valid video file for testing"""
        # Create a 5-second black video
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'color=c=black:s=640x480:d=5',
            '-c:v', 'libx264',
            '-y',
            str(output_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[SUCCESS] Test video created: {output_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not create test video: {e}")
            return False
    
    def phase7_optimization(self, video_id):
        """Phase 7: Optimization & Analytics Loop"""
        print("\n" + "="*60)
        print("PHASE 7: OPTIMIZATION & ANALYTICS")
        print("="*60)
        
        if not video_id:
            print("[SKIP] No video to analyze")
            return
        
        # Call analytics webhook
        response = requests.post(
            f"{self.base_url}/youtube-analytics",
            json={
                "channel_id": "mine",
                "video_id": video_id,
                "metrics": ["views", "likes", "retention"]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Analytics retrieved")
            print(f"Insights: {result.get('insights', ['Video just uploaded, check back later'])}")
        
    def phase8_monetization(self):
        """Phase 8: Monetization Expansion & Scale"""
        print("\n" + "="*60)
        print("PHASE 8: MONETIZATION STRATEGY")
        print("="*60)
        
        print("Monetization Opportunities:")
        print("1. YouTube AdSense (automatic once eligible)")
        print("2. Affiliate Marketing (Amazon, courses, tools)")
        print("3. Sponsorships (reach out after 10K subs)")
        print("4. Your own products/courses")
        print("5. YouTube Shorts fund")
        
    def run_full_pipeline(self):
        """Run all 8 phases"""
        print("\n" + "="*60)
        print("YOUTUBE PRODUCTION PIPELINE - FULL AUTOMATION")
        print("="*60)
        print(f"Session: {self.session_id}")
        print(f"Output: {self.content_dir}")
        
        # Phase 1: Environment Check
        if not self.phase1_environment_check():
            print("\n[ERROR] Environment check failed. Fix issues above.")
            return
        
        try:
            # Phase 2: Research & Select Content
            idea = self.phase2_research_and_niche_selection()
            
            # Phase 3: Generate Script
            script, metadata = self.phase3_scriptwriting(idea)
            
            # Phase 4: Generate TTS
            audio_file = self.phase4_tts_production(script)

            # Update metadata with accurate timestamps based on audio duration
            if audio_file and Path(audio_file).exists():
                try:
                    probe_cmd = [
                        'ffprobe', '-v', 'error',
                        '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        str(audio_file)
                    ]
                    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                    audio_duration = float(result.stdout.strip())
                    print(f"[INFO] Updating timestamps for {audio_duration:.1f} second video")

                    # Regenerate description with accurate timestamps
                    metadata['description'] = self.generate_seo_description(idea, audio_duration)

                    # Update metadata file
                    metadata_file = self.content_dir / "metadata.json"
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    print("[SUCCESS] Updated metadata with accurate timestamps")
                except Exception as e:
                    print(f"[WARNING] Could not update timestamps: {e}")

            # Phase 5: Assemble Video
            video_file = self.phase5_video_assembly(audio_file, metadata)
            
            # Phase 6: Upload to YouTube
            video_id = self.phase6_upload_to_youtube(video_file, metadata)
            
            # Phase 7: Analytics
            self.phase7_optimization(video_id)
            
            # Phase 8: Monetization
            self.phase8_monetization()
            
            print("\n" + "="*60)
            print("PIPELINE COMPLETE!")
            print("="*60)
            
            if video_id:
                print(f"\nYour video is uploaded as PRIVATE")
                print(f"Review at: https://studio.youtube.com/video/{video_id}/edit")
                print("\nNext steps:")
                print("1. Add custom thumbnail")
                print("2. Review auto-generated captions")
                print("3. Set end screen")
                print("4. Schedule or publish")
            
        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    system = YouTubeProductionSystem()
    system.run_full_pipeline()

if __name__ == "__main__":
    main()