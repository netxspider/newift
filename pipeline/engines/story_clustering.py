"""
Pipeline A: Story Clustering & Deduplication Engine
Uses TF-IDF and Cosine Similarity to group multi-source signals into canonical story clusters.
"""
import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.models import RawSignal, StoryCluster, TrendScore, current_iso_time
from pipeline.engines.trend_scoring import TrendScoringEngine


class StoryClusteringEngine:
    def __init__(self, similarity_threshold: float = 0.58):
        self.similarity_threshold = similarity_threshold
        self.scorer = TrendScoringEngine()

    def cluster_signals(self, signals: List[RawSignal]) -> List[StoryCluster]:
        if not signals:
            return []

        # Prepare corpus from signal titles and summaries
        corpus = [f"{s.title} {s.summary}" for s in signals]

        # Fit TF-IDF matrix
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            sim_matrix = cosine_similarity(tfidf_matrix)
        except Exception:
            # Fallback for tiny or unvectorizable corpus
            sim_matrix = np.eye(len(signals))

        n = len(signals)
        visited = set()
        clusters: List[StoryCluster] = []

        for i in range(n):
            if i in visited:
                continue

            cluster_indices = [i]
            visited.add(i)

            for j in range(i + 1, n):
                if j not in visited and sim_matrix[i, j] >= self.similarity_threshold:
                    cluster_indices.append(j)
                    visited.add(j)

            cluster_signals = [signals[idx] for idx in cluster_indices]

            # Pick canonical anchor signal: highest reliability & clarity
            anchor = max(
                cluster_signals,
                key=lambda s: (s.reliability_score * 1.5) + (s.search_velocity) - (len(s.title) < 20) * 20,
            )

            # Compute aggregate cluster trend score
            cluster_score = self.scorer.score_cluster_signals(cluster_signals)

            # Determine dominant category
            categories = [s.category for s in cluster_signals]
            dominant_category = max(set(categories), key=categories.count) if categories else anchor.category

            # Generate deterministic cluster ID and content hash
            content_hash = self._generate_cluster_hash(anchor.title, cluster_signals)
            cluster_id = f"cluster_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{content_hash[:8]}"

            cluster = StoryCluster(
                cluster_id=cluster_id,
                canonical_title=anchor.title,
                canonical_summary=anchor.summary,
                category=dominant_category,
                trend_score=cluster_score,
                signals=cluster_signals,
                signal_count=len(cluster_signals),
                first_detected_at=min((s.published_at for s in cluster_signals), default=current_iso_time()),
                last_updated_at=max((s.published_at for s in cluster_signals), default=current_iso_time()),
                content_hash=content_hash,
                status="discovered",
            )
            clusters.append(cluster)

        # Sort clusters by composite trend score descending
        clusters.sort(key=lambda c: c.trend_score.composite_score, reverse=True)
        return clusters

    def _generate_cluster_hash(self, canonical_title: str, signals: List[RawSignal]) -> str:
        # Normalize anchor terms
        cleaned = re.sub(r"[^\w\s]", "", canonical_title.lower()).split()
        top_terms = sorted(list(set([w for w in cleaned if len(w) > 3])))[:6]
        seed = f"{'-'.join(top_terms)}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()
