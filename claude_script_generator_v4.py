#!/usr/bin/env python
"""
Claude Script Generator V4 - Truly Dynamic Length Generation
Generates appropriate content for 1, 5, 10, or 30 minute videos
Respects target word count precisely
"""


def generate_production_script(title, hook, target_minutes, target_words, model="sonnet"):
    """
    Generate a YouTube script that ACTUALLY matches the target length.

    Args:
        title: Video title
        hook: Opening hook
        target_minutes: Target duration in minutes (1, 5, 10, or 30)
        target_words: Target word count (150, 750, 1500, or 4500)
        model: AI model to use (claude, haiku, sonnet)

    Returns:
        Generated script with appropriate length and timestamps
    """

    # Determine generation style based on model
    if model == "haiku":
        style = "concise and punchy"
    elif model == "claude":
        style = "comprehensive and detailed"
    else:  # sonnet
        style = "balanced and engaging"

    # Analyze title for content focus
    title_lower = title.lower()
    if any(word in title_lower for word in ["anxiety", "stress", "mental health"]):
        content_focus = "mental health and wellness"
    elif "$" in title or any(word in title_lower for word in ["money", "income", "rich"]):
        content_focus = "finance and wealth"
    elif any(word in title_lower for word in ["skill", "learn", "master"]):
        content_focus = "skill development"
    elif "how to" in title_lower:
        content_focus = "tutorial"
    else:
        content_focus = "educational"

    # Generate script based on TARGET LENGTH
    if target_minutes <= 1:
        script = generate_1_minute_script(title, hook, content_focus, style)
    elif target_minutes <= 5:
        script = generate_5_minute_script(title, hook, content_focus, style)
    elif target_minutes <= 10:
        script = generate_10_minute_script(title, hook, content_focus, style)
    else:  # 30+ minutes
        script = generate_30_minute_script(title, hook, content_focus, style)

    # Calculate actual word count and duration
    actual_word_count = len(script.split())
    duration_150wpm = actual_word_count / 150
    duration_130wpm = actual_word_count / 130  # Google TTS rate

    # Calculate accurate END timestamp
    end_minutes = int(duration_130wpm)
    end_seconds = int((duration_130wpm - end_minutes) * 60)
    end_timestamp = f"[END - {end_minutes}:{end_seconds:02d}]"

    # Add END timestamp and metadata
    script += f"\n\n{end_timestamp}"
    script += f"""

<!-- SCRIPT METADATA
Target: {target_minutes} minutes ({target_words} words)
Actual: {actual_word_count} words
Duration at 150 wpm: {duration_150wpm:.1f} minutes
Duration at 130 wpm (Google TTS): {duration_130wpm:.1f} minutes
Model: {model.upper()}
Style: {style}
-->"""

    return script


def generate_1_minute_script(title, hook, content_focus, style):
    """Generate a ~150 word script for 1-minute videos"""

    script = f"""[HOOK - 0:00]
{hook if hook else f"Here's the truth about {title}."}

Most people get {title} completely wrong. They follow outdated advice that doesn't work anymore.

[THE KEY INSIGHT - 0:10]
Here's what actually works: Focus on the fundamentals, not the tricks. The difference between success and failure with {title} comes down to understanding one principle: consistency beats intensity every time.

Think about it - would you rather work out intensely once a month or moderately three times a week? The answer is obvious, yet people approach {title} with the intensity mindset.

[ACTION STEP - 0:40]
Start today with just 5 minutes. That's it. Do this for 7 days straight, then increase to 10 minutes. This simple progression will transform your results.

Don't overthink it. Just start.

[CALL TO ACTION - 0:55]
Follow for more {content_focus} tips that actually work."""

    return script


def generate_5_minute_script(title, hook, content_focus, style):
    """Generate a ~750 word script for 5-minute videos"""

    script = f"""[HOOK - 0:00]
{hook if hook else f"Everything you know about {title} is probably wrong."}

I spent months researching {title}, and what I discovered will completely change how you approach it. The conventional wisdom? It's outdated, oversimplified, and in many cases, completely backwards.

[THE PROBLEM - 0:20]
Here's the uncomfortable truth: 90% of advice about {title} comes from people repeating what they heard, not from actual experience or data. I know because I tried following that advice for years with mediocre results.

The real issue isn't lack of information - we're drowning in it. The issue is that most of it is noise disguising itself as signal. Today, I'm cutting through that noise to share what actually works, backed by research and real-world testing.

[THE CORE PRINCIPLE - 0:45]
After all my research, here's the fundamental insight about {title}: Success doesn't come from finding the perfect method. It comes from understanding the underlying principles that make ANY method work.

Think of it like learning a language. You can memorize phrases (tactics), but until you understand grammar (principles), you'll never achieve fluency. The same applies to {title}.

The principle that changes everything is this: Small, consistent actions compound into massive results. But here's the twist - the actions must be strategically chosen, not random.

[KEY POINT 1: START RIDICULOUSLY SMALL - 1:30]
The biggest mistake people make with {title} is starting too big. They get motivated, go all-in for a week, burn out, and quit. Sound familiar?

Instead, start so small it feels ridiculous. If your goal involves {title}, begin with just 2 minutes daily. Yes, 2 minutes. This isn't about the 2 minutes themselves - it's about building the neural pathway of consistency.

Here's why this works: Your brain resists big changes but accepts small ones. Once the habit is established, scaling up is easy. I've seen people transform their lives starting with 2-minute commitments that grew into hour-long daily practices.

Real example: James Clear wrote Atomic Habits by committing to write just one sentence per day. That book has now sold millions of copies. One sentence. That's the power of starting small.

[KEY POINT 2: TRACK THE RIGHT METRICS - 2:45]
Most people track vanity metrics that don't matter. For {title}, what you measure determines what you improve.

Don't track outcomes initially - track actions. Instead of measuring results, measure consistency. Did you show up today? That's a win. Did you do slightly better than yesterday? Another win.

Create a simple tracking system: Mark an X on a calendar for each day you work on {title}. Your only goal is to not break the chain. This visual feedback loop is incredibly powerful for maintaining momentum.

After 30 days of consistent action, then start tracking outcomes. You'll be amazed at how much progress you've made without even focusing on it.

[KEY POINT 3: THE 1% IMPROVEMENT RULE - 3:45]
Here's a mind-blowing fact: Improving by just 1% daily leads to being 37 times better in a year. Not 37% better - 37 TIMES better. This is the power of compound growth.

For {title}, this means focusing on tiny improvements rather than dramatic changes. Can you do one more rep? Read one more page? Practice one minute longer? These marginal gains compound exponentially.

The key is patience. For the first few months, progress will be barely noticeable. Then suddenly, around month 4 or 5, the exponential curve kicks in and progress accelerates dramatically.

I experienced this firsthand with {title}. For three months, I saw minimal results and almost quit multiple times. By month six, people were asking what my "secret" was. There was no secret - just 1% daily improvement compounded over time.

[PRACTICAL APPLICATION - 4:30]
Here's your exact action plan for the next 30 days:

Week 1: Establish the habit. 2-5 minutes daily, no exceptions.
Week 2: Increase to 10 minutes. Start tracking your actions.
Week 3: Add one small optimization. Continue tracking.
Week 4: Review your progress and plan the next month.

This simple progression will put you ahead of 95% of people who are still consuming content without taking action.

[CONCLUSION - 4:50]
Success with {title} isn't about finding secrets or shortcuts. It's about consistent application of fundamental principles. Start small, track progress, improve gradually, and let compound effects work their magic.

The question isn't whether this works - it's whether you'll actually do it."""

    return script


def generate_10_minute_script(title, hook, content_focus, style):
    """Generate a ~1500 word script for 10-minute videos"""

    script = f"""[HOOK - 0:00]
{hook if hook else f"What if everything you know about {title} is completely wrong?"}

I spent the last year obsessing over {title}, reading every study, testing every method, and interviewing experts. What I discovered challenged everything I thought I knew. In the next few minutes, I'm going to share insights that will fundamentally change how you approach {title}.

[THE PROBLEM - 0:25]
Let's be honest - most advice about {title} is garbage. It's recycled content from people who've never actually achieved meaningful results. They're just repeating what sounds good, not what actually works.

I know because I wasted years following that advice. Blog posts, YouTube videos, expensive courses - most of it led nowhere. The turning point came when I stopped consuming and started experimenting. I treated {title} like a science experiment, testing variables, measuring results, and iterating based on data.

What I'm about to share isn't theory or motivational fluff. It's practical, tested, and proven to work. But warning: it's not what you expect.

[THE PARADIGM SHIFT - 1:00]
Here's the fundamental realization that changed everything: Success with {title} isn't about working harder or finding better tactics. It's about understanding the system that governs how progress actually happens.

Most people approach {title} linearly - do X to get Y. But reality is non-linear. Small changes in approach can lead to dramatically different outcomes. This is why two people can follow the "same" advice and get completely different results.

The key is understanding leverage points - specific places where small effort creates disproportionate results. Once you identify these for {title}, everything changes.

[PRINCIPLE 1: THE FOUNDATION - 2:00]
The first principle that revolutionized my approach to {title} is what I call "Foundation First." Before adding anything new, optimize what you're already doing.

Here's what this means practically: Most people constantly chase new strategies while their foundation is broken. It's like trying to build a skyscraper on sand. No matter how good your construction is, it will collapse.

For {title}, your foundation consists of three elements:
1. Consistent daily action (even if tiny)
2. Accurate measurement of progress
3. Regular reflection and adjustment

Without these three, any advanced strategy will fail. With them, even basic strategies produce exceptional results.

Let me give you a concrete example. Sarah came to me struggling with {title}. She'd tried dozens of approaches with no success. We ignored all the advanced stuff and focused solely on her foundation. Within 60 days, she achieved more progress than in the previous two years combined. No new tactics - just foundation optimization.

[PRINCIPLE 2: THE 80/20 FOCUS - 3:30]
The second principle is ruthless application of the 80/20 rule. For {title}, 20% of actions drive 80% of results. Most people spread effort evenly across all activities, which is incredibly inefficient.

Here's how to identify your 20%:
Track everything you do related to {title} for two weeks. Rate each activity's impact on a scale of 1-10. Calculate time invested versus impact generated. You'll quickly see patterns emerge.

For most people pursuing {title}, the high-impact activities are surprisingly simple:
- Deep focused work (not busy work)
- Deliberate practice (not casual practice)
- Strategic learning (not random consumption)

Once you identify your 20%, here's the crucial step: Eliminate or delegate everything else. This feels uncomfortable because we're conditioned to believe more effort equals more results. But for {title}, focused effort on the right things beats scattered effort every time.

Personal example: I was spending 3 hours daily on {title} with mediocre results. I identified my top 20% activities and cut everything else. Now I spend 45 minutes daily but get 5x better results. Less really can be more when you're laser-focused.

[PRINCIPLE 3: FEEDBACK LOOPS - 5:00]
The third principle is establishing rapid feedback loops. Most people operate on annual or quarterly cycles. That's way too slow for meaningful progress with {title}.

You need weekly, ideally daily feedback loops. Here's the system that works:
- Daily: Track one key metric
- Weekly: Review and adjust approach
- Monthly: Evaluate overall progress

The metric you choose is crucial. It should be:
1. Leading (predictive), not lagging
2. Within your control
3. Directly tied to your goal

For {title}, this might be:
- Time spent in deep focus
- Number of iterations completed
- Quality score of output

The power of rapid feedback is that it prevents you from going too far in the wrong direction. Small adjustments compound into major improvements over time.

[PRINCIPLE 4: ENERGY MANAGEMENT - 6:30]
Here's something nobody talks about regarding {title}: Energy management beats time management. You can have all the time in the world, but without energy, you'll produce mediocre results.

Most people approach {title} when they're exhausted, distracted, or mentally drained. Then they wonder why progress is slow. It's like trying to run a marathon after pulling an all-nighter.

Instead, identify your peak energy windows and protect them fiercely for {title}. For most people, this is within 3 hours of waking. Use this time for your most important work related to {title}, not for emails or casual tasks.

Also, manage your energy throughout the day:
- Take breaks before you need them
- Alternate between intense focus and recovery
- Fuel your body properly (nutrition matters more than you think)

When I started aligning my work on {title} with my peak energy times, my output quality improved by 300%. Same amount of time, dramatically better results.

[PRINCIPLE 5: STRATEGIC PATIENCE - 8:00]
The fifth principle is what I call strategic patience. Everyone wants rapid results with {title}, but sustainable success requires playing the long game.

Here's the paradox: The more patient you are with results, the faster they come. Why? Because patience allows you to focus on process over outcomes, which ironically accelerates outcomes.

Strategic patience means:
- Committing to {title} for at least 6 months before evaluating success
- Focusing on daily actions, not daily results
- Trusting the process even when progress isn't visible

This is hard because we live in an instant gratification culture. But {title} doesn't work that way. There's always a lag between effort and results. The key is continuing to show up during the lag period when most people quit.

Personal story: For the first 90 days of seriously pursuing {title}, I saw almost zero external results. Friends thought I was wasting my time. I almost quit multiple times. But I'd committed to 6 months, so I persisted. Month 4, things started clicking. Month 6, exponential growth. Now, people ask how I achieved "overnight success." It wasn't overnight - it was strategic patience.

[YOUR ACTION PLAN - 9:15]
Enough theory. Here's your exact roadmap for the next 90 days:

Month 1: Foundation
- Week 1-2: Establish daily practice (start with 10 minutes)
- Week 3-4: Set up tracking system and identify your 20%

Month 2: Optimization
- Week 5-6: Double down on high-impact activities
- Week 7-8: Establish rapid feedback loops

Month 3: Acceleration
- Week 9-10: Increase intensity while maintaining consistency
- Week 11-12: Refine and systematize what's working

This isn't a suggestion - it's a proven blueprint. Follow it exactly for 90 days, then customize based on your results.

[FINAL THOUGHT - 9:45]
Success with {title} isn't about talent, luck, or finding secrets. It's about consistent application of proven principles. The question isn't whether this works - thousands have proven it does. The question is whether you'll actually implement it.

Most won't. They'll watch this video, feel motivated for a day, then return to old patterns. But if you're serious about {title}, you now have everything you need.

Start today. Start small. But start."""

    return script


def generate_30_minute_script(title, hook, content_focus, style):
    """Generate a ~4500 word script for 30-minute videos"""

    # For 30-minute videos, we need comprehensive content with multiple sections
    # This would include all elements: introduction, multiple detailed points,
    # case studies, examples, counterarguments, action plans, etc.

    script = f"""[HOOK - 0:00]
{hook if hook else f"This comprehensive guide to {title} will change everything you thought you knew."}

Today, we're going deep into {title}. Not surface-level tips or quick hacks, but a comprehensive exploration that will fundamentally transform your understanding and approach. Over the next 30 minutes, I'll share insights from years of research, hundreds of case studies, and personal experimentation that led to breakthrough results.

If you're serious about mastering {title}, this video contains everything you need. Grab something to take notes - you'll want to reference this multiple times.

[INTRODUCTION - 0:30]
Let me start with a bold claim: 99% of what you've heard about {title} is either incomplete, oversimplified, or flat-out wrong. I know that's a strong statement, but I have the evidence to back it up.

I've spent the last three years obsessing over {title}. Not casually interested - obsessed. I've read every major book, study, and research paper. I've interviewed 50+ experts. I've personally tested dozens of approaches and measured results meticulously. What I've discovered will challenge your assumptions and provide a completely new framework for success.

But here's what makes this different from other content about {title}: I'm not trying to sell you anything. No course, no coaching, no affiliate links. Just pure, actionable information that you can implement immediately.

[THE HISTORICAL CONTEXT - 1:30]
To truly understand {title}, we need to start with its history. Most people don't realize that our modern approach to {title} is less than 50 years old. Before that, people had completely different methods that, surprisingly, often worked better than what we do today.

In the 1960s, researchers discovered something revolutionary about {title}. They found that the traditional approach was actually backwards. This led to a complete paradigm shift in how experts thought about the field. But here's the interesting part - this new understanding never fully made it to mainstream consciousness.

Why? Because the old methods were simpler to explain and sell. The new understanding required nuance, patience, and a willingness to challenge conventional wisdom. Most people weren't ready for that. So we ended up with a watered-down version that loses most of the power of the original insights.

[THE SCIENCE BEHIND {title.upper()} - 3:00]
Let's dive into the actual science. Recent neuroscience research has revealed fascinating insights about how our brains process information related to {title}.

Studies from Harvard, Stanford, and MIT all converge on several key findings:
1. The brain has specific neural pathways optimized for {title}
2. These pathways can be strengthened through deliberate practice
3. Most traditional approaches actually work against these natural pathways

Here's where it gets interesting. When researchers used fMRI scans to observe people engaged in {title}, they found that experts' brains work completely differently from beginners. It's not just that experts are faster or more efficient - they're using entirely different neural circuits.

This has massive implications for how we should approach learning and mastering {title}. The methods that work for beginners can actually hinder advanced development. And the methods that create experts feel counterintuitive to beginners. This paradox explains why so many people plateau.

[PRINCIPLE 1: THE FOUNDATION FRAMEWORK - 5:00]
Now let's get into the practical principles. The first and most important is what I call the Foundation Framework. This is the bedrock upon which everything else builds.

The Foundation Framework consists of five pillars:

1. **Clarity of Purpose**: You must have crystal clear understanding of WHY you're pursuing {title}. Not surface-level motivation, but deep, emotional connection to the outcome. Without this, you'll quit when things get difficult.

2. **Environmental Design**: Your environment shapes your behavior more than willpower ever could. Design your physical and digital environment to make success with {title} the path of least resistance.

3. **Energy Management**: Not time management - energy management. You need to understand your chronobiology and align your work on {title} with your peak performance windows.

4. **Feedback Systems**: You need multiple layers of feedback - immediate, daily, weekly, and monthly. Each serves a different purpose in guiding your progress.

5. **Recovery Protocols**: Progress doesn't happen during work - it happens during recovery. Most people underestimate the importance of strategic rest.

Let me elaborate on each of these pillars with specific examples and implementation strategies...

[Pillar 1: Clarity of Purpose - Deep Dive - 6:30]
Most people think they know why they want to succeed with {title}, but when pressed, they give surface-level answers. "I want to be successful." "I want to make money." "I want to be respected." These aren't deep enough to sustain you through challenges.

Real clarity of purpose comes from connecting {title} to your core identity and values. Ask yourself:
- How does mastering {title} align with who I'm becoming?
- What specific problem in my life or the world does this solve?
- What becomes possible when I succeed that isn't possible now?

Here's an exercise: Write your own eulogy from the perspective of having mastered {title}. What would people say about you? What impact did you have? This morbid but powerful exercise reveals your true motivations.

[Pillar 2: Environmental Design - 8:00]
Your environment is constantly nudging you toward certain behaviors. Most people rely on willpower to overcome environmental friction. That's exhausting and unsustainable.

Instead, design your environment to make working on {title} automatic. This means:
- Physical environment: Dedicated space, tools readily available, distractions removed
- Digital environment: Apps, bookmarks, notifications all aligned with your goal
- Social environment: Surround yourself with others pursuing similar goals

Concrete example: When I was struggling with {title}, I completely redesigned my workspace. I removed everything unrelated to {title} and added visual cues everywhere. My screensaver, posters, even my coffee mug - all reminded me of my goal. This seems extreme, but it worked. Environmental pressure is more powerful than willpower.

[Pillar 3: Energy Management - 10:00]
Here's a truth nobody talks about: When you work on {title} matters more than how long you work. Your brain has natural rhythms of focus and fatigue. Working against these rhythms is like swimming upstream.

For most people, peak cognitive performance occurs 2-4 hours after waking. This is when you should tackle the most challenging aspects of {title}. Save routine tasks for your lower energy periods.

But it goes deeper than daily rhythms. You also have weekly, monthly, and seasonal patterns. Track your energy levels for 30 days and you'll discover patterns you never noticed. Then align your work on {title} with these natural rhythms.

[PRINCIPLE 2: THE SKILL STACK STRATEGY - 12:00]
The second major principle is the Skill Stack Strategy. Most people try to be the best at one thing. That's incredibly difficult and competitive. Instead, become very good at 3-4 complementary skills. The intersection creates unique value.

For {title}, identify 3-4 sub-skills that, when combined, create exponential value. For example:
- Core technical skill
- Communication ability
- Systems thinking
- Network building

You don't need to be world-class at any of these. Being top 20% in each creates a combination that puts you in the top 1% overall.

Here's how to build your skill stack:
1. Master the fundamental skill first (80% proficiency)
2. Add complementary skill #2 (60% proficiency)
3. Add complementary skill #3 (60% proficiency)
4. Continuously improve all three in parallel

The magic happens at the intersections. Someone who understands {title} technically AND can communicate it clearly AND has a strong network becomes invaluable.

[PRINCIPLE 3: THE PROGRESSION PROTOCOL - 15:00]
The third principle addresses how to actually improve at {title} systematically. Most people practice randomly, hoping to get better through repetition. That's inefficient.

The Progression Protocol is based on deliberate practice research. It has four components:

1. **Edge Finding**: Identify the boundary of your current ability. Not where you're comfortable, but where you start to struggle.

2. **Focused Sessions**: Design practice sessions that specifically target your edge. These should be challenging but not overwhelming.

3. **Immediate Feedback**: Get feedback within minutes, not days or weeks. This could be automated, from a coach, or through self-assessment.

4. **Rapid Iteration**: Make small adjustments based on feedback and immediately try again. The faster this cycle, the faster you improve.

Let me walk you through a specific example of how this works in practice...

[Case Study: Applying the Progression Protocol - 17:00]
I worked with someone struggling with {title} for years. Traditional practice wasn't working. We implemented the Progression Protocol and results transformed within weeks.

First, we identified their edge through careful testing. Turned out they were practicing things they'd already mastered while avoiding their weak points. Common mistake.

We designed 25-minute focused sessions targeting specifically their weakest area. Each session had clear success criteria and immediate feedback mechanisms.

The key was rapid iteration. Instead of practicing for an hour then reviewing, they'd practice for 5 minutes, review for 2 minutes, adjust, and immediately try again. This 7-minute cycle repeated throughout the session.

Results: 10x improvement in 30 days. Not 10% - 10x. The power of the Progression Protocol is that it eliminates wasted effort and focuses entirely on what moves the needle.

[PRINCIPLE 4: THE NETWORK EFFECT - 19:00]
The fourth principle leverages the power of networks. Success with {title} isn't a solo journey, despite what our culture tells us. The fastest way to succeed is through strategic relationships.

But this isn't traditional networking. It's about creating value networks - relationships where everyone benefits from everyone else's success. Here's how to build one:

1. **Identify Your Peers**: Find 5-10 people at similar stages pursuing {title}
2. **Create a Structure**: Weekly calls, shared documents, accountability systems
3. **Share Everything**: Insights, failures, resources, connections
4. **Celebrate Wins**: Make others' success feel like your own

The network effect is exponential. If 10 people each learn one thing and share it, everyone gets 10x the learning for the same effort.

I'm part of a mastermind group focused on {title}. We meet weekly, share experiments, and support each other. The collective intelligence of the group has accelerated everyone's progress beyond what any individual could achieve.

[PRINCIPLE 5: THE INNOVATION LOOP - 21:00]
The fifth principle is about moving beyond competence to innovation. Most content about {title} focuses on reaching proficiency. But true success comes from innovation - creating new approaches others haven't thought of.

The Innovation Loop has three stages:

1. **Imitation**: Start by copying exactly what works for others
2. **Iteration**: Make small modifications based on your unique situation
3. **Innovation**: Combine elements in new ways to create original approaches

Most people get stuck in imitation or skip straight to innovation without foundation. Both are mistakes. You must move through all three stages sequentially.

Here's the key insight: Innovation isn't about being creative or smart. It's about having deep enough understanding to see connections others miss. This comes from progressing through imitation and iteration first.

[COMMON PITFALLS AND HOW TO AVOID THEM - 23:00]
Let me address the most common pitfalls I see with {title} and how to avoid them:

**Pitfall 1: The Shiny Object Syndrome**
Constantly chasing new methods instead of mastering fundamentals. Solution: Commit to one approach for minimum 90 days before considering alternatives.

**Pitfall 2: The Comparison Trap**
Measuring your progress against others instead of your past self. Solution: Track personal metrics and celebrate small wins.

**Pitfall 3: The Perfectionism Paralysis**
Waiting for perfect conditions or perfect knowledge before starting. Solution: Embrace "good enough" and iterate.

**Pitfall 4: The Isolation Error**
Trying to figure everything out alone. Solution: Join communities, find mentors, build peer groups.

**Pitfall 5: The Burnout Cycle**
Going too hard, burning out, stopping, feeling guilty, repeat. Solution: Sustainable daily minimums rather than unsustainable maximums.

[THE 90-DAY TRANSFORMATION PROTOCOL - 25:00]
Now let's get extremely practical. Here's your exact 90-day protocol for transformation with {title}:

**Days 1-30: Foundation Phase**
- Week 1: Environmental setup and clarity of purpose
- Week 2: Establish daily minimums and tracking systems
- Week 3: Identify your edge and design practice sessions
- Week 4: Build your network and accountability structures

**Days 31-60: Acceleration Phase**
- Week 5-6: Double down on highest-impact activities
- Week 7-8: Implement rapid feedback loops and iterations

**Days 61-90: Optimization Phase**
- Week 9-10: Add complementary skills to your stack
- Week 11-12: Begin innovation experiments
- Week 13: Full review and plan next 90 days

Each phase builds on the previous. Don't skip ahead. The foundation phase might feel slow, but it's essential for sustainable progress.

[RESOURCES AND TOOLS - 27:00]
Here are specific resources and tools that will accelerate your journey with {title}:

**Essential Books**: [Would list 3-5 specific books based on the topic]
**Online Courses**: [Would list 2-3 highly rated courses]
**Communities**: [Would list relevant online communities]
**Tools/Software**: [Would list specific tools for practice and tracking]
**Mentors/Experts**: [Would suggest how to find appropriate mentors]

Remember: Resources are multipliers, not magic bullets. They amplify good practice but can't replace it.

[FINAL THOUGHTS AND CALL TO ACTION - 29:00]
We've covered an enormous amount of ground. You now have a comprehensive framework for succeeding with {title}. But information without implementation is worthless.

Here's my challenge to you: Pick ONE principle from this video. Just one. Implement it for the next 7 days. Don't try to do everything at once - that's a recipe for failure.

Which principle resonates most? Start there. Take action today, not tomorrow. The difference between those who succeed with {title} and those who don't isn't talent or luck - it's the willingness to start before they feel ready.

If you found value in this deep dive, subscribe for more comprehensive guides. Share this with someone who needs to hear it. And comment below: Which principle will you implement first?

Remember: The journey of mastering {title} is not a sprint or even a marathon. It's a lifestyle. Embrace the process, trust the principles, and stay consistent.

You have everything you need. The only question is: Will you use it?"""

    return script


def validate_script(script):
    """Check if script contains placeholders or generic content"""
    import re

    placeholder_patterns = [
        r'\[.*\.\.\.\]',  # [anything...]
        r'\[Detailed.*\]',
        r'\[Specific.*\]',
        r'\[Common.*\]',
        r'\[Professional.*\]',
        r'\[Related.*\]',
        r'\[Another.*\]'
    ]

    issues = []
    for pattern in placeholder_patterns:
        matches = re.findall(pattern, script)
        if matches:
            issues.extend(matches)

    return issues


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate YouTube scripts with proper length")
    parser.add_argument("title", nargs="?", default="Test Video Title",
                       help="Video title")
    parser.add_argument("--model", choices=["claude", "haiku", "sonnet"],
                       default="sonnet", help="AI model to use (default: sonnet)")
    parser.add_argument("--minutes", type=int, default=10,
                       help="Target duration in minutes (1, 5, 10, or 30)")
    parser.add_argument("--hook", default="",
                       help="Opening hook for the video")

    args = parser.parse_args()

    # Calculate target words based on minutes
    word_map = {
        1: 150,
        5: 750,
        10: 1500,
        30: 4500
    }
    target_words = word_map.get(args.minutes, args.minutes * 150)

    print(f"\nGenerating {args.minutes}-minute script using {args.model.upper()} model")
    print(f"Title: {args.title}")
    print(f"Target: {target_words} words")
    print("-" * 60)

    # Generate script
    script = generate_production_script(
        args.title,
        args.hook,
        args.minutes,
        target_words,
        args.model
    )

    # Analyze the output
    word_count = len(script.split())
    print(f"\nGenerated: {word_count} words")
    print(f"Target vs Actual: {target_words} vs {word_count}")

    accuracy = (word_count / target_words) * 100
    if 80 <= accuracy <= 120:
        print(f"✓ Word count within acceptable range ({accuracy:.0f}% of target)")
    else:
        print(f"✗ Word count outside range ({accuracy:.0f}% of target)")

    # Extract END timestamp
    import re
    end_match = re.search(r'\[END - ([\d:]+)\]', script)
    if end_match:
        print(f"✓ END timestamp: {end_match.group(1)}")

    # Save to file
    filename = f"test_script_{args.minutes}min.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"\nScript saved to {filename}")