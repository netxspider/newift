"""
Pipeline B: Quality Gate & Fact Verification Engine
Performs multi-dimensional verification (fact corroboration, source count, originality, SEO, sensitivity routing).
"""
import re
from typing import Dict, Any, List
from pipeline.config import settings
from pipeline.models import StoryCluster, ResearchPackage, SEOMetadata, QualityGateResult, current_iso_time


class QualityGateEngine:
    def __init__(self):
        self.min_publish_score = settings.min_publish_score
        self.min_fact_confidence = settings.min_fact_confidence
        self.min_source_count = settings.min_source_count

    def evaluate(
        self,
        cluster: StoryCluster,
        research: ResearchPackage,
        article_data: Dict[str, Any],
        seo_meta: SEOMetadata,
    ) -> QualityGateResult:
        reasons: List[str] = []

        # 1. Fact Accuracy & Corroboration Score
        fact_accuracy_score = self._evaluate_fact_accuracy(research, reasons)

        # 2. Source Quality Score
        source_quality_score = self._evaluate_sources(research, reasons)

        # 3. Originality Score
        originality_score = self._evaluate_originality(article_data, research, reasons)

        # 4. SEO Compliance Score
        seo_score = self._evaluate_seo(seo_meta, reasons)

        # 5. Readability & Structure Score
        readability_score = self._evaluate_readability(article_data, reasons)

        # 6. Safety & Sensitivity Classification
        safety_class = self._check_safety(cluster, article_data, reasons)

        # Composite score
        composite = (
            (fact_accuracy_score * 0.30)
            + (source_quality_score * 0.20)
            + (originality_score * 0.15)
            + (seo_score * 0.15)
            + (readability_score * 0.20)
        )
        composite = round(min(100.0, max(0.0, composite)), 1)

        # Pass / Fail Decision
        source_count = len(research.primary_sources) + len(research.secondary_sources)
        passed = (
            composite >= self.min_publish_score
            and fact_accuracy_score >= self.min_fact_confidence
            and source_count >= self.min_source_count
            and safety_class == "green"
        )

        requires_human_review = not passed or safety_class in ["yellow", "red"]

        return QualityGateResult(
            passed=passed,
            composite_score=composite,
            fact_accuracy_score=round(fact_accuracy_score, 1),
            source_quality_score=round(source_quality_score, 1),
            originality_score=round(originality_score, 1),
            seo_score=round(seo_score, 1),
            readability_score=round(readability_score, 1),
            safety_classification=safety_class,
            requires_human_review=requires_human_review,
            reasons=reasons,
            checked_at=current_iso_time(),
        )

    def _evaluate_fact_accuracy(self, research: ResearchPackage, reasons: List[str]) -> float:
        score = 85.0
        # Check source count
        total_sources = len(research.primary_sources) + len(research.secondary_sources)
        if total_sources >= 4:
            score += 10.0
        elif total_sources >= 3:
            score += 5.0
        else:
            score -= 15.0
            reasons.append(f"Fewer than 3 independent sources ({total_sources} found).")

        # Check for confirmed facts vs conflicting claims
        if research.conflicting_claims:
            score -= 10.0
            reasons.append("Conflicting claims detected between sources.")
        if len(research.facts) >= 4:
            score += 5.0

        return min(100.0, max(40.0, score))

    def _evaluate_sources(self, research: ResearchPackage, reasons: List[str]) -> float:
        score = 80.0
        primary_count = len(research.primary_sources)
        if primary_count >= 1:
            score += 15.0
        else:
            reasons.append("No Tier 1 primary wire or official source identified.")

        # Bonus for presence of official statements
        if research.official_statements:
            score += 5.0
        return min(100.0, max(50.0, score))

    def _evaluate_originality(self, article_data: Dict[str, Any], research: ResearchPackage, reasons: List[str]) -> float:
        score = 90.0
        # Verify analytical components are present
        if article_data.get("why_it_matters") and article_data.get("what_changed"):
            score += 5.0
        else:
            score -= 15.0
            reasons.append("Missing core analytical sections (Why it matters / What changed).")

        # N-gram overlap penalty against raw snippets
        body_str = " ".join([b.get("children", [{}])[0].get("text", "") for b in article_data.get("portable_text_body", [])])
        for s in research.primary_sources:
            if s.excerpt and len(s.excerpt) > 100:
                words = s.excerpt.lower().split()[:20]
                chunk = " ".join(words)
                if chunk and chunk in body_str.lower():
                    score -= 10.0
                    reasons.append(f"Direct verbatim block detected from source {s.publisher}.")
                    break

        return min(100.0, max(50.0, score))

    def _evaluate_seo(self, seo: SEOMetadata, reasons: List[str]) -> float:
        score = 95.0
        if len(seo.title) > 70:
            score -= 10.0
            reasons.append(f"SEO title exceeds 70 characters ({len(seo.title)} chars).")
        if len(seo.description) > 165:
            score -= 5.0
            reasons.append(f"Meta description exceeds 165 characters ({len(seo.description)} chars).")
        if not seo.focus_keyword:
            score -= 15.0
            reasons.append("Missing focus keyword.")
        return min(100.0, max(50.0, score))

    def _evaluate_readability(self, article_data: Dict[str, Any], reasons: List[str]) -> float:
        score = 90.0
        if not article_data.get("key_points"):
            score -= 10.0
            reasons.append("Missing key takeaways / key points.")
        if not article_data.get("faq"):
            score -= 5.0
        if not article_data.get("timeline"):
            score -= 5.0
        return min(100.0, max(50.0, score))

    def _check_safety(self, cluster: StoryCluster, article_data: Dict[str, Any], reasons: List[str]) -> str:
        text = f"{cluster.canonical_title} {cluster.canonical_summary} {article_data.get('what_happened', '')}".lower()

        # Hard Red: Tragedies, crimes, medical claims, election disputes
        for kw in settings.hard_stop_keywords:
            if kw in text:
                reasons.append(f"Hard safety gate triggered by sensitive keyword: '{kw}'.")
                return "red"

        # Yellow: Politics, Finance, Controversies
        if cluster.category in settings.human_review_categories:
            reasons.append(f"Category '{cluster.category}' requires human editorial sign-off.")
            return "yellow"

        # Green: Auto-publishable
        return "green"
