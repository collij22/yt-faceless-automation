"""Trend analysis and monitoring for content ideas."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import AppConfig
from ..core.schemas import VideoNiche

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trends across multiple platforms for content opportunities."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.cache_dir = config.directories.cache_dir / "trends"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_trending_topics(
        self,
        niche: Optional[VideoNiche] = None,
        lookback_days: Optional[int] = None,
        min_velocity: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Get currently trending topics with growth metrics.
        
        Args:
            niche: Filter by specific niche
            lookback_days: Days to analyze (default from config)
            min_velocity: Minimum trend velocity score
        
        Returns:
            List of trending topics with metrics
        """
        lookback_days = lookback_days or self.config.research.trend_lookback_days
        
        # Aggregate trends from multiple sources
        trends = []
        
        # Get trends from each source
        trends.extend(self._get_exploding_topics(niche))
        trends.extend(self._get_google_trends(niche))
        trends.extend(self._get_reddit_trends(niche))
        trends.extend(self._get_youtube_trends(niche))
        
        # Calculate velocity scores
        for trend in trends:
            trend["velocity_score"] = self._calculate_velocity(trend)
        
        # Filter by minimum velocity
        trends = [t for t in trends if t["velocity_score"] >= min_velocity]
        
        # Sort by velocity
        trends.sort(key=lambda x: x["velocity_score"], reverse=True)
        
        return trends
    
    def analyze_trend_sustainability(
        self,
        topic: str,
        historical_days: int = 90
    ) -> Dict[str, Any]:
        """Analyze if a trend is sustainable or just a spike.
        
        Args:
            topic: The topic to analyze
            historical_days: Days of historical data to analyze
        
        Returns:
            Sustainability analysis with predictions
        """
        analysis = {
            "topic": topic,
            "sustainability_score": 0.0,
            "peak_detected": False,
            "growth_phase": "unknown",
            "predicted_duration_days": 0,
            "confidence": 0.0,
        }
        
        # Get historical data (placeholder)
        historical_data = self._get_historical_data(topic, historical_days)
        
        if not historical_data:
            return analysis
        
        # Analyze trend pattern
        pattern = self._analyze_pattern(historical_data)
        
        # Calculate sustainability score
        sustainability = self._calculate_sustainability(pattern)
        
        analysis.update({
            "sustainability_score": sustainability["score"],
            "peak_detected": pattern["has_peaked"],
            "growth_phase": pattern["phase"],
            "predicted_duration_days": sustainability["predicted_duration"],
            "confidence": sustainability["confidence"],
        })
        
        return analysis
    
    def get_seasonal_trends(
        self,
        niche: VideoNiche,
        target_month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get seasonal trends for planning ahead.
        
        Args:
            niche: Video niche to analyze
            target_month: Month to target (1-12), None for next month
        
        Returns:
            List of seasonal trends with timing
        """
        if target_month is None:
            target_month = (datetime.now().month % 12) + 1
        
        seasonal_trends = []
        
        # Niche-specific seasonal patterns
        seasonal_patterns = {
            VideoNiche.FINANCE: {
                1: ["tax preparation", "new year budget", "investment planning"],
                4: ["tax filing", "quarterly earnings", "spring cleaning finances"],
                9: ["back to school budgeting", "Q4 planning"],
                11: ["black friday deals", "holiday budgeting"],
            },
            VideoNiche.HEALTH: {
                1: ["new year fitness", "diet resolutions", "gym memberships"],
                3: ["spring fitness", "allergy season"],
                6: ["summer body", "outdoor workouts"],
                10: ["flu season prep", "immune boosting"],
            },
            VideoNiche.TECH_REVIEWS: {
                1: ["CES coverage", "new year tech"],
                6: ["WWDC coverage", "summer gadgets"],
                9: ["iPhone launch", "back to school tech"],
                11: ["black friday tech deals", "holiday gift guides"],
            },
        }
        
        patterns = seasonal_patterns.get(niche, {})
        topics = patterns.get(target_month, [])
        
        for topic in topics:
            seasonal_trends.append({
                "topic": topic,
                "niche": niche.value,
                "target_month": target_month,
                "seasonality_score": 8.5,  # Placeholder
                "historical_performance": "high",
                "recommended_publish_date": self._calculate_publish_date(target_month),
            })
        
        return seasonal_trends
    
    def _get_exploding_topics(self, niche: Optional[VideoNiche] = None) -> List[Dict[str, Any]]:
        """Get trends from Exploding Topics (placeholder)."""
        trends = []
        
        # Sample trending topics
        sample_topics = [
            {
                "topic": "AI Agents",
                "category": "technology",
                "growth": 850,
                "search_volume": 45000,
                "competition": "medium",
            },
            {
                "topic": "Vision Pro Apps",
                "category": "technology",
                "growth": 1200,
                "search_volume": 28000,
                "competition": "low",
            },
            {
                "topic": "GLP-1 Drugs",
                "category": "health",
                "growth": 650,
                "search_volume": 82000,
                "competition": "high",
            },
        ]
        
        for topic_data in sample_topics:
            if niche and not self._matches_niche(topic_data["category"], niche):
                continue
            
            trends.append({
                "source": "exploding_topics",
                "topic": topic_data["topic"],
                "category": topic_data["category"],
                "growth_percentage": topic_data["growth"],
                "search_volume": topic_data["search_volume"],
                "competition": topic_data["competition"],
                "timestamp": datetime.now().isoformat(),
            })
        
        return trends
    
    def _get_google_trends(self, niche: Optional[VideoNiche] = None) -> List[Dict[str, Any]]:
        """Get trends from Google Trends (placeholder)."""
        trends = []
        
        # Would integrate with pytrends or Google Trends API
        sample_trends = [
            ("chatgpt plugins", 95, "technology"),
            ("recession 2024", 88, "finance"),
            ("ozempic alternatives", 76, "health"),
        ]
        
        for topic, interest, category in sample_trends:
            if niche and not self._matches_niche(category, niche):
                continue
            
            trends.append({
                "source": "google_trends",
                "topic": topic,
                "category": category,
                "interest_score": interest,
                "timestamp": datetime.now().isoformat(),
            })
        
        return trends
    
    def _get_reddit_trends(self, niche: Optional[VideoNiche] = None) -> List[Dict[str, Any]]:
        """Get trends from Reddit (placeholder)."""
        trends = []
        
        # Would integrate with Reddit API
        subreddit_map = {
            VideoNiche.AI_NEWS: ["r/artificial", "r/singularity"],
            VideoNiche.FINANCE: ["r/personalfinance", "r/investing"],
            VideoNiche.CRYPTO: ["r/cryptocurrency", "r/bitcoin"],
            VideoNiche.PSYCHOLOGY: ["r/psychology", "r/getmotivated"],
        }
        
        # Sample trending posts
        sample_posts = [
            {
                "title": "New AI model beats GPT-4 on benchmarks",
                "subreddit": "r/artificial",
                "upvotes": 15000,
                "comments": 850,
                "category": "technology",
            },
            {
                "title": "How I saved $50k in 2 years",
                "subreddit": "r/personalfinance",
                "upvotes": 8500,
                "comments": 420,
                "category": "finance",
            },
        ]
        
        for post in sample_posts:
            if niche and not self._matches_niche(post["category"], niche):
                continue
            
            trends.append({
                "source": "reddit",
                "topic": post["title"],
                "subreddit": post["subreddit"],
                "engagement_score": (post["upvotes"] + post["comments"] * 10) / 1000,
                "category": post["category"],
                "timestamp": datetime.now().isoformat(),
            })
        
        return trends
    
    def _get_youtube_trends(self, niche: Optional[VideoNiche] = None) -> List[Dict[str, Any]]:
        """Get trends from YouTube (placeholder)."""
        trends = []
        
        # Would use YouTube API
        sample_youtube_trends = [
            {
                "title": "AI News This Week",
                "views_velocity": 150000,  # views per day
                "category": "technology",
            },
            {
                "title": "Market Crash Incoming?",
                "views_velocity": 85000,
                "category": "finance",
            },
        ]
        
        for trend in sample_youtube_trends:
            if niche and not self._matches_niche(trend["category"], niche):
                continue
            
            trends.append({
                "source": "youtube",
                "topic": trend["title"],
                "category": trend["category"],
                "views_velocity": trend["views_velocity"],
                "timestamp": datetime.now().isoformat(),
            })
        
        return trends
    
    def _calculate_velocity(self, trend: Dict[str, Any]) -> float:
        """Calculate trend velocity score (0-10)."""
        source = trend.get("source", "")
        
        if source == "exploding_topics":
            # Based on growth percentage
            growth = trend.get("growth_percentage", 0)
            if growth > 1000:
                return 10.0
            elif growth > 500:
                return 8.5
            elif growth > 200:
                return 7.0
            elif growth > 100:
                return 5.5
            else:
                return 4.0
        
        elif source == "google_trends":
            # Based on interest score
            interest = trend.get("interest_score", 0)
            return min(10.0, interest / 10)
        
        elif source == "reddit":
            # Based on engagement
            engagement = trend.get("engagement_score", 0)
            return min(10.0, engagement / 10)
        
        elif source == "youtube":
            # Based on views velocity
            velocity = trend.get("views_velocity", 0)
            if velocity > 100000:
                return 9.0
            elif velocity > 50000:
                return 7.5
            elif velocity > 20000:
                return 6.0
            else:
                return 4.5
        
        return 5.0  # Default
    
    def _matches_niche(self, category: str, niche: VideoNiche) -> bool:
        """Check if a category matches a niche."""
        category_map = {
            "technology": [VideoNiche.AI_NEWS, VideoNiche.TECH_REVIEWS],
            "finance": [VideoNiche.FINANCE, VideoNiche.CRYPTO, VideoNiche.BUSINESS],
            "health": [VideoNiche.HEALTH, VideoNiche.PSYCHOLOGY],
            "education": [VideoNiche.EDUCATION, VideoNiche.SCIENCE],
            "entertainment": [VideoNiche.TRUE_CRIME, VideoNiche.HISTORY],
            "lifestyle": [VideoNiche.LIFESTYLE, VideoNiche.MOTIVATION, VideoNiche.PRODUCTIVITY],
        }
        
        for cat, niches in category_map.items():
            if category.lower() == cat and niche in niches:
                return True
        
        return False
    
    def _get_historical_data(
        self,
        topic: str,
        days: int
    ) -> List[Tuple[datetime, float]]:
        """Get historical data points for a topic."""
        # Placeholder - would query actual data sources
        data_points = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            # Simulate growth pattern
            value = 100 * (1 + i/days) * (1 + 0.1 * (i % 7))
            data_points.append((date, value))
        
        return data_points
    
    def _analyze_pattern(
        self,
        data_points: List[Tuple[datetime, float]]
    ) -> Dict[str, Any]:
        """Analyze trend pattern from historical data."""
        if not data_points:
            return {"phase": "unknown", "has_peaked": False}
        
        values = [v for _, v in data_points]
        
        # Simple pattern detection
        recent_avg = sum(values[-7:]) / 7 if len(values) >= 7 else sum(values) / len(values)
        historical_avg = sum(values) / len(values)
        
        if recent_avg > historical_avg * 1.5:
            phase = "explosive_growth"
        elif recent_avg > historical_avg * 1.2:
            phase = "steady_growth"
        elif recent_avg > historical_avg * 0.8:
            phase = "plateau"
        else:
            phase = "declining"
        
        # Peak detection
        max_value = max(values)
        has_peaked = values[-1] < max_value * 0.8
        
        return {
            "phase": phase,
            "has_peaked": has_peaked,
            "recent_avg": recent_avg,
            "historical_avg": historical_avg,
        }
    
    def _calculate_sustainability(
        self,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate trend sustainability metrics."""
        phase = pattern.get("phase", "unknown")
        has_peaked = pattern.get("has_peaked", False)
        
        if phase == "explosive_growth" and not has_peaked:
            score = 8.5
            predicted_duration = 30
            confidence = 0.7
        elif phase == "steady_growth":
            score = 7.0
            predicted_duration = 60
            confidence = 0.8
        elif phase == "plateau":
            score = 5.0
            predicted_duration = 45
            confidence = 0.6
        else:
            score = 3.0
            predicted_duration = 15
            confidence = 0.5
        
        return {
            "score": score,
            "predicted_duration": predicted_duration,
            "confidence": confidence,
        }
    
    def _calculate_publish_date(self, target_month: int) -> str:
        """Calculate optimal publish date for seasonal content."""
        current_date = datetime.now()
        target_year = current_date.year
        
        if target_month < current_date.month:
            target_year += 1
        
        # Publish 2 weeks before peak season
        target_date = datetime(target_year, target_month, 1) - timedelta(days=14)
        
        return target_date.isoformat()