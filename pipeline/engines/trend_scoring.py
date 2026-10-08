"""
Deterministic Trend Scoring Engine
Calculates weighted trend score based on search velocity, news velocity, social velocity, recency, reliability, and relevance.
"""
from typing import List, Dict, Any
from pipeline.config import settings
from pipeline.models import RawSignal, TrendScore


class TrendScoringEngine:
    def __init__(self):
        self.w_search = settings.weight_search_velocity / 100.0
        self.w_news = settings.weight_news_velocity / 100.0
        self.w_social = settings.weight_social_velocity / 100.0
        self.w_recency = settings.weight_recency / 100.0
        self.w_reliability = settings.weight_source_reliability / 100.0
        self.w_relevance = settings.weight_newift_relevance / 100.0

    def score_signal(self, signal: RawSignal) -> TrendScore:
        relevance = self._calculate_relevance(signal)
        composite = (
            (signal.search_velocity * self.w_search)
            + (signal.news_velocity * self.w_news)
            + (signal.social_velocity * self.w_social)
            + (signal.recency_score * self.w_recency)
            + (signal.reliability_score * self.w_reliability)
            + (relevance * self.w_relevance)
        )
        composite = round(min(100.0, max(0.0, composite)), 2)

        priority = "discard"
        if composite >= 80.0:
            priority = "high"
        elif composite >= 60.0:
            priority = "medium"

        return TrendScore(
            search_velocity=round(signal.search_velocity, 1),
            news_velocity=round(signal.news_velocity, 1),
            social_velocity=round(signal.social_velocity, 1),
            recency=round(signal.recency_score, 1),
            source_reliability=round(signal.reliability_score, 1),
            newift_relevance=round(relevance, 1),
            composite_score=composite,
            priority=priority,
        )

    def score_cluster_signals(self, signals: List[RawSignal]) -> TrendScore:
        """
        Aggregate scoring across multiple signals reporting on the same story.
        More independent sources significantly boosts news velocity and reliability!
        """
        if not signals:
            return TrendScore()

        source_count = len(signals)
        avg_search = sum(s.search_velocity for s in signals) / source_count
        avg_social = max(s.social_velocity for s in signals)
        avg_recency = max(s.recency_score for s in signals)
        best_reliability = max(s.reliability_score for s in signals)

        # Multi-source news velocity booster (1 source = base, 3+ sources = high, 6+ sources = max velocity)
        news_velocity = min(98.0, 70.0 + (source_count * 5.0))

        # Diversity bonus for source reliability
        composite_reliability = min(98.0, best_reliability + (source_count * 1.5))

        # Overall cluster relevance
        avg_relevance = sum(self._calculate_relevance(s) for s in signals) / source_count

        composite = (
            (avg_search * self.w_search)
            + (news_velocity * self.w_news)
            + (avg_social * self.w_social)
            + (avg_recency * self.w_recency)
            + (composite_reliability * self.w_reliability)
            + (avg_relevance * self.w_relevance)
        )
        composite = round(min(100.0, max(0.0, composite)), 2)

        priority = "discard"
        if composite >= 80.0:
            priority = "high"
        elif composite >= 60.0:
            priority = "medium"

        return TrendScore(
            search_velocity=round(avg_search, 1),
            news_velocity=round(news_velocity, 1),
            social_velocity=round(avg_social, 1),
            recency=round(avg_recency, 1),
            source_reliability=round(composite_reliability, 1),
            newift_relevance=round(avg_relevance, 1),
            composite_score=composite,
            priority=priority,
        )

    def _calculate_relevance(self, signal: RawSignal) -> float:
        text = f"{signal.title} {signal.summary}".lower()

        # Hard stop penalty for sensitive topics
        if any(w in text for w in settings.hard_stop_keywords):
            return 30.0

        # Core editorial pillars: high engagement on modern web
        high_relevance_keywords = [
            "ai", "artificial intelligence", "openai", "google", "apple", "microsoft",
            "nvidia", "meta", "breakthrough", "launch", "announced", "features",
            "release", "space", "quantum", "iphone", "robot", "streaming", "game",
        ]
        if any(w in text for w in high_relevance_keywords):
            return 95.0

        if signal.category in ["Tech", "Entertainment", "Science"]:
            return 88.0
        if signal.category in ["Business", "Global"]:
            return 75.0
        return 65.0
