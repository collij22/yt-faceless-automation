#!/usr/bin/env python
"""Apply the complete dynamic ideas fix to run_full_production_pipeline.py"""

import sys

# Read the current file
with open('run_full_production_pipeline.py', 'r') as f:
    content = f.read()

# Find the generate_content_ideas function and replace it entirely
import_index = content.find('import hashlib')
if import_index == -1:
    # Add the import if not there
    import_section = content.find('import time')
    if import_section != -1:
        content = content[:import_section + len('import time')] + '\nimport random\nimport hashlib' + content[import_section + len('import time'):]

# Find and replace the entire generate_content_ideas function
start_marker = '    def generate_content_ideas(self, niche):'
end_marker = '                }\n            ]\n        else:\n            # Educational and other ideas\n            return ['

start_index = content.find(start_marker)
if start_index == -1:
    print("ERROR: Could not find generate_content_ideas function")
    sys.exit(1)

# Find the end of the function (look for the last return statement)
search_from = start_index
end_index = -1
indent_count = 0
lines = content[start_index:].split('\n')
for i, line in enumerate(lines):
    if i == 0:
        continue
    # Check if we're at the start of a new method (same indentation as def)
    if line.startswith('    def ') and i > 1:
        end_index = start_index + len('\n'.join(lines[:i]))
        break

if end_index == -1:
    print("ERROR: Could not find end of function")
    sys.exit(1)

# New implementation
new_implementation = '''    def generate_content_ideas(self, niche):
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

        for title in templates[:10]:
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
        return random.sample(keywords_map.get(category, ["educational"]), 5)
'''

# Replace the old function
content = content[:start_index] + new_implementation + '\n' + content[end_index:]

# Write back
with open('run_full_production_pipeline.py', 'w') as f:
    f.write(content)

print("Successfully applied dynamic ideas fix!")
print("The generate_content_ideas function now creates unique, varied content each time.")