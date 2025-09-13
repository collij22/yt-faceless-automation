"""Research analyzer for video idea generation and validation."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core.config import AppConfig
from ..core.errors import ResearchError
from ..core.schemas import (
    CompetitorAnalysis,
    IdeaScores,
    IdeaValidation,
    Keywords,
    VideoIdea,
    VideoNiche,
)

logger = logging.getLogger(__name__)


class ResearchAnalyzer:
    """Main research and idea generation engine."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.cache_dir = config.directories.cache_dir / "research"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ideas_dir = config.directories.data_dir / "ideas"
        self.ideas_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize source adapters
        self.sources = []
        self._init_sources()
    
    def _init_sources(self) -> None:
        """Initialize research source adapters."""
        # These will be implemented as we add integrations
        if self.config.apis.brave_search_key:
            logger.info("Brave Search API configured")
        if self.config.apis.firecrawl_key:
            logger.info("Firecrawl API configured")
        if self.config.apis.youtube_api_key:
            logger.info("YouTube API configured")
    
    def generate_ideas(
        self,
        count: int = 20,
        niches: Optional[List[VideoNiche]] = None,
        force_refresh: bool = False
    ) -> List[VideoIdea]:
        """Generate validated video ideas with scoring.
        
        Args:
            count: Number of ideas to generate
            niches: Specific niches to focus on (None for all)
            force_refresh: Bypass cache and fetch fresh data
        
        Returns:
            List of scored and validated video ideas
        """
        ideas = []
        
        # Check cache unless forced refresh
        if not force_refresh:
            cached_ideas = self._load_cached_ideas()
            if cached_ideas and len(cached_ideas) >= count:
                logger.info(f"Returning {count} ideas from cache")
                return cached_ideas[:count]
        
        # Gather raw ideas from multiple sources
        raw_ideas = self._gather_raw_ideas(niches)
        
        # Score and validate each idea
        for raw_idea in raw_ideas:
            try:
                idea = self._process_raw_idea(raw_idea)
                if idea and idea.validation.youtube_safe:
                    ideas.append(idea)
                    if len(ideas) >= count:
                        break
            except Exception as e:
                logger.warning(f"Failed to process idea: {e}")
                continue
        
        # Cache the results
        self._cache_ideas(ideas)
        
        # Export to individual files as per plan
        self._export_ideas(ideas)
        
        # Sort by composite score
        ideas.sort(key=lambda x: x.scores.composite, reverse=True)
        
        return ideas[:count]
    
    def _gather_raw_ideas(
        self,
        niches: Optional[List[VideoNiche]] = None
    ) -> List[Dict[str, Any]]:
        """Gather raw idea data from various sources.
        
        This is a placeholder that will integrate with:
        - Zebracat formats
        - TastyEdits RPM data
        - Exploding Topics trends
        - YouTube competitor analysis
        - Reddit trending topics
        """
        raw_ideas = []
        
        # Target niches
        target_niches = niches or list(VideoNiche)
        
        # Generate sample ideas for now
        for niche in target_niches[:5]:  # Limit for demo
            raw_ideas.extend(self._generate_sample_ideas(niche))
        
        return raw_ideas
    
    def _generate_sample_ideas(self, niche: VideoNiche) -> List[Dict[str, Any]]:
        """Generate sample ideas for demonstration."""
        templates = {
            VideoNiche.AI_NEWS: [
                {
                    "title": "OpenAI's Secret Project That Changes Everything",
                    "angle": "Exclusive analysis of leaked documents revealing OpenAI's next breakthrough that could revolutionize AI accessibility for everyone",
                    "keywords": ["OpenAI", "AI breakthrough", "GPT-5", "artificial intelligence news"],
                },
                {
                    "title": "The $1 Billion AI Tool Nobody's Talking About",
                    "angle": "Deep dive into a stealth AI startup that just secured massive funding and could disrupt the entire tech industry",
                    "keywords": ["AI startup", "tech investment", "AI tools", "billion dollar company"],
                },
            ],
            VideoNiche.FINANCE: [
                {
                    "title": "Why 97% of People Will Never Be Rich (And How to Be the 3%)",
                    "angle": "Data-driven analysis of wealth accumulation patterns and the specific habits that separate the wealthy from everyone else",
                    "keywords": ["wealth building", "financial freedom", "rich habits", "personal finance"],
                },
                {
                    "title": "The Hidden Tax That's Stealing 40% of Your Money",
                    "angle": "Exposing the invisible costs and fees that drain your wealth, with actionable strategies to reclaim thousands per year",
                    "keywords": ["hidden taxes", "save money", "financial tips", "wealth preservation"],
                },
            ],
            VideoNiche.PSYCHOLOGY: [
                {
                    "title": "The Dark Psychology Trick Used by Every Successful Person",
                    "angle": "Scientific breakdown of the psychological frameworks that high achievers use to manipulate their own minds for success",
                    "keywords": ["dark psychology", "success mindset", "psychological tricks", "high achievers"],
                },
                {
                    "title": "Why Your Brain Sabotages You at 3 PM Every Day",
                    "angle": "Neuroscience explanation of afternoon energy crashes and evidence-based techniques to maintain peak performance",
                    "keywords": ["brain science", "productivity", "energy management", "neuroscience"],
                },
            ],
        }
        
        ideas = templates.get(niche, [])
        for idea in ideas:
            idea["niche"] = niche
            idea["sources"] = ["https://example.com/research"]
        
        return ideas
    
    def _process_raw_idea(self, raw_idea: Dict[str, Any]) -> Optional[VideoIdea]:
        """Process and score a raw idea."""
        try:
            # Calculate scores
            scores = self._calculate_scores(raw_idea)
            
            # Extract keywords
            keywords = self._extract_keywords(raw_idea)
            
            # Validate content
            validation = self._validate_idea(raw_idea)
            
            # Get competitor data (placeholder)
            competitors = self._analyze_competitors(raw_idea)
            
            # Create VideoIdea object
            idea = VideoIdea(
                idea_id=uuid4(),
                timestamp=datetime.now(),
                title=raw_idea["title"],
                angle=raw_idea["angle"],
                niche=raw_idea["niche"],
                scores=scores,
                keywords=keywords,
                competitors=competitors,
                sources=raw_idea.get("sources", []),
                validation=validation,
                notes=raw_idea.get("notes"),
            )
            
            return idea
            
        except Exception as e:
            logger.error(f"Error processing idea: {e}")
            return None
    
    def _calculate_scores(self, raw_idea: Dict[str, Any]) -> IdeaScores:
        """Calculate comprehensive scores for an idea."""
        # This is a simplified scoring algorithm
        # In production, this would use ML models and real data
        
        niche = raw_idea.get("niche", VideoNiche.EDUCATION)
        
        # Base scores by niche (based on RPM data)
        niche_rpm_scores = {
            VideoNiche.FINANCE: 8.5,
            VideoNiche.CRYPTO: 7.8,
            VideoNiche.AI_NEWS: 7.5,
            VideoNiche.TECH_REVIEWS: 7.2,
            VideoNiche.BUSINESS: 7.0,
            VideoNiche.PSYCHOLOGY: 6.8,
            VideoNiche.SCIENCE: 6.5,
            VideoNiche.EDUCATION: 6.2,
            VideoNiche.HEALTH: 6.0,
            VideoNiche.TRUE_CRIME: 5.8,
            VideoNiche.HISTORY: 5.5,
            VideoNiche.MOTIVATION: 5.2,
            VideoNiche.LIFESTYLE: 5.0,
            VideoNiche.PRODUCTIVITY: 4.8,
        }
        
        rpm_score = niche_rpm_scores.get(niche, 5.0)
        
        # Simulate other scores (would use real data in production)
        import random
        random.seed(raw_idea["title"].__hash__())  # Consistent scores for same title
        
        trend_velocity = random.uniform(5.0, 9.0)
        competition_gap = random.uniform(4.0, 8.5)
        virality = random.uniform(3.0, 8.0)
        monetization = random.uniform(7.0, 9.5)
        
        # Calculate composite score using configured weights
        composite = (
            rpm_score * self.config.research.score_weight_rpm +
            trend_velocity * self.config.research.score_weight_trend +
            competition_gap * self.config.research.score_weight_competition +
            virality * self.config.research.score_weight_virality +
            monetization * self.config.research.score_weight_monetization
        )
        
        return IdeaScores(
            rpm=round(rpm_score, 1),
            trend_velocity=round(trend_velocity, 1),
            competition_gap=round(competition_gap, 1),
            virality=round(virality, 1),
            monetization=round(monetization, 1),
            composite=round(composite, 1),
        )
    
    def _extract_keywords(self, raw_idea: Dict[str, Any]) -> Keywords:
        """Extract and categorize keywords."""
        # Use provided keywords or extract from title/angle
        provided_keywords = raw_idea.get("keywords", [])
        
        # Split into categories (simplified)
        primary = provided_keywords[:2] if provided_keywords else []
        secondary = provided_keywords[2:5] if len(provided_keywords) > 2 else []
        long_tail = provided_keywords[5:] if len(provided_keywords) > 5 else []
        
        # Add niche-specific keywords
        niche = raw_idea.get("niche")
        if niche:
            secondary.append(niche.value.replace("_", " "))
        
        return Keywords(
            primary=primary,
            secondary=secondary,
            long_tail=long_tail,
        )
    
    def _validate_idea(self, raw_idea: Dict[str, Any]) -> IdeaValidation:
        """Validate idea for policy compliance."""
        # Simplified validation - would use actual YouTube policy checks
        title = raw_idea.get("title", "").lower()
        angle = raw_idea.get("angle", "").lower()
        
        # Check for problematic content
        problematic_terms = [
            "illegal", "hack", "exploit", "leaked", "stolen",
            "violence", "adult", "gambling", "drugs"
        ]
        
        youtube_safe = not any(term in title or term in angle for term in problematic_terms)
        
        return IdeaValidation(
            youtube_safe=youtube_safe,
            copyright_clear=True,  # Would check against copyright database
            trend_sustainable=True,  # Would analyze trend longevity
            monetization_eligible=youtube_safe,
        )
    
    def _analyze_competitors(self, raw_idea: Dict[str, Any]) -> List[CompetitorAnalysis]:
        """Analyze competitor videos for the idea."""
        # Placeholder - would use YouTube API
        competitors = []
        
        # Generate sample competitor data
        sample_channels = [
            ("TechExplained", "UC_tech_123"),
            ("FinanceGuru", "UC_finance_456"),
            ("MindMatters", "UC_psych_789"),
        ]
        
        import random
        for channel_name, channel_id in sample_channels[:2]:
            competitors.append(
                CompetitorAnalysis(
                    channel_name=channel_name,
                    channel_id=channel_id,
                    video_title=f"Similar: {raw_idea.get('title', 'Video')}",
                    video_id=f"vid_{random.randint(1000, 9999)}",
                    views=random.randint(10000, 1000000),
                    likes=random.randint(100, 10000),
                    comments=random.randint(10, 1000),
                    duration_seconds=random.randint(300, 900),
                    published_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                    strategy_notes="High engagement through controversy hook",
                )
            )
        
        return competitors
    
    def _load_cached_ideas(self) -> Optional[List[VideoIdea]]:
        """Load ideas from cache if fresh."""
        cache_file = self.cache_dir / "ideas_cache.json"
        
        if not cache_file.exists():
            return None
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age > timedelta(days=self.config.research.cache_days):
            logger.info("Cache expired, will fetch fresh data")
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            ideas = []
            for item in data:
                # Reconstruct VideoIdea objects
                # This is simplified - would use proper serialization
                idea_dict = {
                    "idea_id": item["idea_id"],
                    "timestamp": datetime.fromisoformat(item["timestamp"]),
                    "title": item["title"],
                    "angle": item["angle"],
                    "niche": VideoNiche(item["niche"]),
                    "scores": IdeaScores(**item["scores"]),
                    "keywords": Keywords(**item["keywords"]),
                    "competitors": [CompetitorAnalysis(**c) for c in item["competitors"]],
                    "sources": item["sources"],
                    "validation": IdeaValidation(**item["validation"]),
                    "notes": item.get("notes"),
                }
                ideas.append(VideoIdea(**idea_dict))
            
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None
    
    def _cache_ideas(self, ideas: List[VideoIdea]) -> None:
        """Cache ideas to disk."""
        cache_file = self.cache_dir / "ideas_cache.json"
        
        try:
            # Convert to JSON-serializable format
            data = []
            for idea in ideas:
                item = {
                    "idea_id": str(idea.idea_id),
                    "timestamp": idea.timestamp.isoformat(),
                    "title": idea.title,
                    "angle": idea.angle,
                    "niche": idea.niche.value,
                    "scores": {
                        "rpm": idea.scores.rpm,
                        "trend_velocity": idea.scores.trend_velocity,
                        "competition_gap": idea.scores.competition_gap,
                        "virality": idea.scores.virality,
                        "monetization": idea.scores.monetization,
                        "composite": idea.scores.composite,
                    },
                    "keywords": {
                        "primary": idea.keywords.primary,
                        "secondary": idea.keywords.secondary,
                        "long_tail": idea.keywords.long_tail,
                    },
                    "competitors": [
                        {
                            "channel_name": c.channel_name,
                            "channel_id": c.channel_id,
                            "video_title": c.video_title,
                            "video_id": c.video_id,
                            "views": c.views,
                            "likes": c.likes,
                            "comments": c.comments,
                            "duration_seconds": c.duration_seconds,
                            "published_at": c.published_at.isoformat(),
                            "strategy_notes": c.strategy_notes,
                        }
                        for c in idea.competitors
                    ],
                    "sources": idea.sources,
                    "validation": {
                        "youtube_safe": idea.validation.youtube_safe,
                        "copyright_clear": idea.validation.copyright_clear,
                        "trend_sustainable": idea.validation.trend_sustainable,
                        "monetization_eligible": idea.validation.monetization_eligible,
                    },
                    "notes": idea.notes,
                }
                data.append(item)
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached {len(ideas)} ideas to {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to cache ideas: {e}")
    
    def _export_ideas(self, ideas: List[VideoIdea]) -> None:
        """Export ideas to individual files in data/ideas/ directory."""
        try:
            for idea in ideas:
                # Create filename from title (sanitized)
                safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in idea.title)
                safe_title = safe_title.replace(" ", "_").lower()[:50]
                filename = f"{safe_title}_{str(idea.idea_id)[:8]}.json"
                filepath = self.ideas_dir / filename
                
                # Convert idea to JSON-serializable format
                idea_data = {
                    "idea_id": str(idea.idea_id),
                    "timestamp": idea.timestamp.isoformat(),
                    "title": idea.title,
                    "angle": idea.angle,
                    "niche": idea.niche.value,
                    "scores": {
                        "rpm": idea.scores.rpm,
                        "trend_velocity": idea.scores.trend_velocity,
                        "competition_gap": idea.scores.competition_gap,
                        "virality": idea.scores.virality,
                        "monetization": idea.scores.monetization,
                        "composite": idea.scores.composite,
                    },
                    "keywords": {
                        "primary": idea.keywords.primary,
                        "secondary": idea.keywords.secondary,
                        "long_tail": idea.keywords.long_tail,
                    },
                    "competitors": [
                        {
                            "channel_name": c.channel_name,
                            "channel_id": c.channel_id,
                            "video_title": c.video_title,
                            "video_id": c.video_id,
                            "views": c.views,
                            "likes": c.likes,
                            "comments": c.comments,
                            "duration_seconds": c.duration_seconds,
                            "published_at": c.published_at.isoformat(),
                            "strategy_notes": c.strategy_notes,
                        }
                        for c in idea.competitors
                    ],
                    "sources": idea.sources,
                    "validation": {
                        "youtube_safe": idea.validation.youtube_safe,
                        "copyright_clear": idea.validation.copyright_clear,
                        "trend_sustainable": idea.validation.trend_sustainable,
                        "monetization_eligible": idea.validation.monetization_eligible,
                    },
                    "notes": idea.notes,
                }
                
                # Write to file
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(idea_data, f, indent=2)
                
                logger.debug(f"Exported idea to {filepath}")
            
            logger.info(f"Exported {len(ideas)} ideas to {self.ideas_dir}")
            
        except Exception as e:
            logger.error(f"Failed to export ideas: {e}")