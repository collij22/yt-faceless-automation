"""
Dynamic Content Ideas Generator - Full Implementation
This will replace the static idea generation with dynamic, varied content
"""

def generate_content_ideas(self, niche):
    """Generate specific content ideas for a niche with dynamic variety"""
    # Load history to avoid duplicates
    history = self.load_idea_history()

    # Get dynamic variations
    vars = self.generate_dynamic_variations()
    current_year = vars["year"]
    n = vars["numbers"]

    ideas = []

    # Generate fresh ideas based on niche
    if "Finance" in niche['niche']:
        # Dynamic finance templates
        finance_templates = [
            # Money mistakes series
            f"{n['small']} Money Mistakes That Keep You Poor (Fix Them {vars['time_frame']})",
            f"The ${n['money']} Mistake {n['percentage']}% of People Make",
            f"{n['tips_count']} Financial Habits of Millionaires {vars['time_frame']}",
            f"Why {n['percentage']}% of People Never Build Wealth (Harsh Truth)",
            f"The Money Rule That Changed My Life at Age {n['medium']+5}",

            # Budgeting variations
            f"The {n['time_minutes']}-Minute Budget System That Works",
            f"How to Save ${n['money']} in {n['time_days']} Days (Proven Method)",
            f"The Lazy Person's Guide to Saving ${n['large']*10} {vars['time_frame']}",
            f"Budget Like a Millionaire With Only ${n['money']}",

            # Investment topics
            f"{n['small']} Stocks That Pay You Every Month {vars['time_frame']}",
            f"How to Turn ${n['money']} into ${n['money']*10} (No BS)",
            f"The {n['time_minutes']}-Minute Investment Strategy Beating Wall Street",
            f"Why I Stopped Investing in [Popular Stock] {vars['time_frame']}",

            # Passive income variations
            f"{n['tips_count']} Passive Income Ideas That Actually Work {vars['time_frame']}",
            f"How I Make ${n['money']} Per Month While I Sleep",
            f"The ${n['medium']} Per Day Method Nobody Talks About",
            f"Passive Income: Expectation vs Reality {vars['time_frame']}",
        ]

        # Create ideas from templates
        ideas = self.create_ideas_from_templates(finance_templates, history, n, "finance")

    elif "Technology" in niche['niche']:
        tech_templates = [
            # AI tools
            f"{n['tips_count']} AI Tools That Will Change Everything {vars['time_frame']}",
            f"The AI Tool That Saves Me {n['time_minutes']} Hours Per Week",
            f"ChatGPT vs [New AI]: {n['time_days']}-Day Test Results",
            f"{n['percentage']}% of People Don't Know These AI Features",

            # Productivity tech
            f"{n['small']} Apps That 10x Your Productivity {vars['time_frame']}",
            f"The {n['time_minutes']}-Minute Tech Setup That Changed My Life",
            f"Why I Deleted {n['tips_count']} Popular Apps (And What I Use Instead)",

            # Tech tips and tricks
            f"{n['tips_count']} Hidden Features in Your Phone {vars['time_frame']}",
            f"The Computer Trick That Saves ${n['money']} Per Year",
            f"{n['small']} Websites That Feel Illegal to Know",

            # Future tech
            f"The Next Big Thing After AI (It's Already Here)",
            f"{n['small']} Technologies That Will Define {vars['next_year']}",
            f"Why {n['percentage']}% of Tech Jobs Will Disappear by {vars['next_year']+1}",
        ]

        ideas = self.create_ideas_from_templates(tech_templates, history, n, "technology")

    elif "Health" in niche['niche']:
        health_templates = [
            # Morning routines
            f"The {n['time_minutes']}-Minute Morning Routine That Changed Everything",
            f"{n['small']} Morning Habits of Highly Successful People",
            f"I Tried [Celebrity]'s Morning Routine for {n['time_days']} Days",

            # Sleep optimization
            f"How to Fall Asleep in {n['time_minutes']} Minutes (Military Method)",
            f"{n['small']} Sleep Mistakes That Ruin Your Day",
            f"The {n['time_minutes']} PM Rule That Fixed My Insomnia",

            # Fitness and diet
            f"{n['tips_count']} Foods That Boost Brain Power {vars['time_frame']}",
            f"The {n['time_minutes']}-Minute Workout Better Than Running",
            f"I Ate Like [Celebrity] for {n['time_days']} Days (Results)",

            # Mental health
            f"{n['small']} Signs Your Mental Health Needs Attention",
            f"The {n['time_minutes']}-Minute Anxiety Fix That Actually Works",
            f"How I Beat Burnout in {n['time_days']} Days",
        ]

        ideas = self.create_ideas_from_templates(health_templates, history, n, "health")

    else:
        # Educational and general content
        education_templates = [
            # Historical
            f"{n['tips_count']} Historical Facts That Will Blow Your Mind",
            f"The {n['small']} Events That Changed Everything {vars['time_frame']}",
            f"What They Don't Teach You About [Historical Figure]",

            # Science
            f"{n['small']} Scientific Discoveries That Change Everything {vars['time_frame']}",
            f"The Science of [Popular Topic] Explained in {n['time_minutes']} Minutes",
            f"Why {n['percentage']}% of What You Learned in School is Wrong",

            # Psychology
            f"{n['tips_count']} Psychology Tricks That Always Work",
            f"The {n['time_minutes']}-Second Rule That Changes Your Brain",
            f"How Your Mind Tricks You Every Day (And How to Stop It)",

            # Self-improvement
            f"{n['small']} Skills Everyone Should Learn {vars['time_frame']}",
            f"The {n['time_days']}-Day Challenge That Will Transform You",
            f"How to Learn Anything {n['small']}x Faster (Science-Based)",

            # Life hacks
            f"{n['tips_count']} Life Hacks That Actually Work {vars['time_frame']}",
            f"The {n['time_minutes']}-Minute Habit That Solves {n['percentage']}% of Problems",
            f"Things I Wish I Knew at Age {n['medium']}",
        ]

        ideas = self.create_ideas_from_templates(education_templates, history, n, "educational")

    # Save the new ideas to history
    self.save_idea_history(history, ideas)

    return ideas

def create_ideas_from_templates(self, templates, history, n, category):
    """Helper function to create ideas from templates"""
    available_ideas = []
    random.shuffle(templates)  # Randomize order

    for title in templates[:15]:  # Process more than needed
        if title not in history["generated_titles"]:
            # Generate appropriate hook based on title content
            if "AI" in title or "Tech" in title:
                hook = f"This changes everything about how we work"
            elif "Money" in title or "$" in title:
                hook = f"The math behind this will shock you"
            elif "Minute" in title or "Hour" in title:
                hook = f"Saves {n['time_minutes']} hours per week minimum"
            elif "Mistake" in title:
                hook = f"{n['percentage']}% of people make this exact mistake"
            elif "Hack" in title or "Trick" in title:
                hook = f"Once you know this, you can't unknow it"
            elif "Science" in title or "Scientific" in title:
                hook = f"The research on this is mind-blowing"
            elif "Historical" in title or "History" in title:
                hook = f"This fact changes how you see everything"
            else:
                hook = f"What happens next will surprise you"

            # Generate keywords based on category
            if category == "finance":
                keywords = ["money", "finance", "investing", "wealth", "savings"]
            elif category == "technology":
                keywords = ["tech", "AI", "apps", "productivity", "future"]
            elif category == "health":
                keywords = ["health", "wellness", "fitness", "lifestyle", "habits"]
            else:
                keywords = ["education", "learning", "facts", "knowledge", "skills"]

            available_ideas.append({
                "title": title,
                "hook": hook,
                "keywords": keywords + [str(self.generate_dynamic_variations()["year"])],
                "estimated_views": f"{n['medium']}K-{n['large']}K",
                "competition_score": random.randint(6, 9)
            })

    return available_ideas[:5]  # Return top 5 unique ideas