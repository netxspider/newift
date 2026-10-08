"""
Pipeline: Google Search Console Performance & SEO Feedback Engine
Identifies striking distance queries (positions 5-20) and recommends content expansions to boost search rankings.
"""
from typing import List, Dict, Any, Optional
from pipeline.storage.db import PipelineDB
from pipeline.config import settings


class FeedbackLoopEngine:
    def __init__(self, db: Optional[PipelineDB] = None):
        self.db = db or PipelineDB()

    def record_performance_data(self, metrics: List[Dict[str, Any]]) -> int:
        """
        Ingests Google Search Console query metrics into the feedback database.
        Each item has: {query, page, clicks, impressions, ctr, position}
        """
        return self.db.record_gsc_metrics(metrics)

    def analyze_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identifies queries ranking in striking distance (positions 5 - 20) with high impressions.
        Generates actionable content enhancement proposals for existing articles.
        """
        candidates = self.db.get_striking_distance_queries(min_pos=5.0, max_pos=20.0)
        recommendations = []

        for item in candidates:
            query = item["query"]
            page = item["page"]
            pos = round(item["position"], 1)
            impr = item["impressions"]

            # Recommend section or FAQ addition
            if any(w in query.lower() for w in ["what is", "how does", "why did", "when will", "who is", "features"]):
                action_type = "add_faq_or_explainer"
                proposal = f"Add dedicated FAQ item answering '{query}' to improve position from {pos} to top 3."
            elif any(w in query.lower() for w in ["vs", "difference", "compare"]):
                action_type = "add_comparison_section"
                proposal = f"Add structured comparison breakdown addressing '{query}'."
            else:
                action_type = "improve_h2_and_meta"
                proposal = f"Include secondary keyword '{query}' into article H2 and meta tags."

            recommendations.append({
                "page": page,
                "target_query": query,
                "current_position": pos,
                "impressions": impr,
                "action_type": action_type,
                "proposal": proposal,
            })

        return recommendations
