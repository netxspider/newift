"""
Pipeline Data Models
Strongly-typed Pydantic schemas for each stage of the Newift pipeline.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()


class RawSignal(BaseModel):
    id: str
    source_name: str
    source_type: str  # google_trends, google_news, rss, social
    title: str
    summary: str = ""
    url: str
    published_at: str = Field(default_factory=current_iso_time)
    source_tier: int = 2  # 1 = highest reliability, 3 = social
    reliability_score: float = 80.0
    search_velocity: float = 70.0
    news_velocity: float = 70.0
    social_velocity: float = 50.0
    recency_score: float = 90.0
    category: str = "Tech"
    image_url: Optional[str] = None


class TrendScore(BaseModel):
    search_velocity: float = 0.0
    news_velocity: float = 0.0
    social_velocity: float = 0.0
    recency: float = 0.0
    source_reliability: float = 0.0
    newift_relevance: float = 0.0
    composite_score: float = 0.0
    priority: str = "medium"  # high (>80), medium (60-80), discard (<60)


class StoryCluster(BaseModel):
    cluster_id: str
    canonical_title: str
    canonical_summary: str = ""
    category: str = "Tech"
    trend_score: TrendScore
    signals: List[RawSignal] = Field(default_factory=list)
    signal_count: int = 1
    first_detected_at: str = Field(default_factory=current_iso_time)
    last_updated_at: str = Field(default_factory=current_iso_time)
    content_hash: str = ""
    status: str = "discovered"  # discovered, researching, drafted, verified, published, review, rejected


class SourceItem(BaseModel):
    publisher: str
    title: str
    url: str
    published_at: Optional[str] = None
    is_primary: bool = False
    excerpt: Optional[str] = None


class ResearchPackage(BaseModel):
    cluster_id: str
    topic: str
    primary_sources: List[SourceItem] = Field(default_factory=list)
    secondary_sources: List[SourceItem] = Field(default_factory=list)
    official_statements: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    quotes: List[Dict[str, str]] = Field(default_factory=list)  # {quote, speaker, source}
    timeline: List[Dict[str, str]] = Field(default_factory=list)  # {time, event}
    conflicting_claims: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    key_entities: List[str] = Field(default_factory=list)


class SEOMetadata(BaseModel):
    focus_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    title: str
    description: str
    slug: str
    canonical_url: str
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    schema_type: str = "NewsArticle"
    suggested_internal_links: List[Dict[str, str]] = Field(default_factory=list)


class QualityGateResult(BaseModel):
    passed: bool = False
    composite_score: float = 0.0
    fact_accuracy_score: float = 0.0
    source_quality_score: float = 0.0
    originality_score: float = 0.0
    seo_score: float = 0.0
    readability_score: float = 0.0
    safety_classification: str = "green"  # green (auto), yellow (review), red (never)
    requires_human_review: bool = False
    reasons: List[str] = Field(default_factory=list)
    checked_at: str = Field(default_factory=current_iso_time)


class CoverImageInfo(BaseModel):
    url: Optional[str] = None
    alt: str = ""
    caption: Optional[str] = None
    attribution: Optional[str] = None
    source_url: Optional[str] = None
    is_generated: bool = False
    asset_ref: Optional[str] = None
    image_bytes: Optional[bytes] = None
    mime_type: str = "image/jpeg"


class EditorialArticle(BaseModel):
    headline: str
    dek: str
    slug: str
    category: str
    read_time: int = 4
    key_points: List[str] = Field(default_factory=list)
    what_happened: str = ""
    why_it_matters: str = ""
    what_changed: str = ""
    what_we_know: List[str] = Field(default_factory=list)
    what_we_dont_know: List[str] = Field(default_factory=list)
    timeline: List[Dict[str, str]] = Field(default_factory=list)
    faq: List[Dict[str, str]] = Field(default_factory=list)
    sources: List[SourceItem] = Field(default_factory=list)
    cover_image: Optional[CoverImageInfo] = None
    seo: SEOMetadata
    quality_gate: QualityGateResult
    ai_disclosure: Dict[str, Any] = Field(default_factory=dict)
    story: Dict[str, Any] = Field(default_factory=dict)
    portable_text_body: List[Dict[str, Any]] = Field(default_factory=list)


class PipelineJob(BaseModel):
    job_id: str
    cluster_id: str
    status: str = "pending"  # pending, running, completed, failed, review_required
    current_step: str = "init"
    step_history: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    article_slug: Optional[str] = None
    sanity_id: Optional[str] = None
    created_at: str = Field(default_factory=current_iso_time)
    updated_at: str = Field(default_factory=current_iso_time)
