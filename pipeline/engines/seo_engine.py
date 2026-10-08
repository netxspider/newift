"""
Pipeline B: SEO Engine
Generates focus keywords, semantic secondary keywords, optimized titles, meta descriptions, slugs, canonical URLs, and internal linking suggestions.
"""
import re
from typing import List, Dict, Any, Optional
from pipeline.config import settings
from pipeline.models import StoryCluster, SEOMetadata, ResearchPackage
from pipeline.storage.db import PipelineDB


class SEOEngine:
    def __init__(self, db: Optional[PipelineDB] = None):
        self.db = db or PipelineDB()

    def generate_seo_metadata(self, cluster: StoryCluster, research: ResearchPackage) -> SEOMetadata:
        title = cluster.canonical_title
        category = cluster.category

        # 1. Determine Focus Keyword
        focus_keyword = self._extract_focus_keyword(title, research.key_entities)

        # 2. Extract Secondary Semantic Keywords
        secondary_keywords = self._extract_secondary_keywords(title, category, research.key_entities)

        # 3. Clean Slug
        slug = self._generate_slug(title, focus_keyword)

        # 4. SEO Title (Keep within 60 chars where possible, absolute max 70)
        seo_title = self._generate_seo_title(title, focus_keyword)

        # 5. Meta Description (Keep within 155 chars)
        meta_description = self._generate_meta_description(title, focus_keyword, research.facts)

        # 6. Canonical URL
        base_url = settings.site_url.rstrip("/")
        canonical_url = f"{base_url}/posts/{slug}"

        # 7. Internal Links Suggestions
        internal_links = self._find_internal_links(category, focus_keyword, slug)

        return SEOMetadata(
            focus_keyword=focus_keyword,
            secondary_keywords=secondary_keywords,
            title=seo_title,
            description=meta_description,
            slug=slug,
            canonical_url=canonical_url,
            og_title=seo_title,
            og_description=meta_description,
            schema_type="NewsArticle",
            suggested_internal_links=internal_links,
        )

    def _extract_focus_keyword(self, title: str, entities: List[str]) -> str:
        if entities:
            # Prefer first 2 entities
            return " ".join(entities[:2])
        # Strip common stopwords
        words = [w for w in re.sub(r"[^\w\s]", "", title).split() if len(w) > 3 and w.lower() not in ["what", "this", "after", "with", "from", "over"]]
        return " ".join(words[:3]) or title[:40]

    def _extract_secondary_keywords(self, title: str, category: str, entities: List[str]) -> List[str]:
        keywords = []
        if category:
            keywords.append(f"{category} News")
        for ent in entities:
            keywords.append(f"{ent} Update")
            keywords.append(f"{ent} Explained")
        keywords.append("What It Means")
        keywords.append("Latest Breakdown")
        return list(dict.fromkeys(keywords))[:5]

    def _generate_slug(self, title: str, focus_keyword: str) -> str:
        text = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        slug = re.sub(r"[\s_-]+", "-", text)[:60].rstrip("-")
        return slug or "trending-story"

    def _generate_seo_title(self, title: str, focus_keyword: str) -> str:
        clean_title = title.strip()
        if len(clean_title) <= 60:
            return clean_title
        # Truncate at word boundary
        truncated = clean_title[:57].rsplit(" ", 1)[0] + "..."
        return truncated

    def _generate_meta_description(self, title: str, focus_keyword: str, facts: List[str]) -> str:
        lead_fact = facts[0] if facts else title
        desc = f"{lead_fact}. Here's what changed, why it matters, and what to know right now."
        if len(desc) > 155:
            desc = desc[:152].rsplit(" ", 1)[0] + "..."
        return desc

    def _find_internal_links(self, category: str, focus_keyword: str, current_slug: str) -> List[Dict[str, str]]:
        published = self.db.get_published_articles(limit=30)
        matches = []
        kw_terms = set(focus_keyword.lower().split())

        for art in published:
            if art["slug"] == current_slug:
                continue
            art_title = art["title"].lower()
            score = 0
            if art.get("category") == category:
                score += 1
            if any(term in art_title for term in kw_terms):
                score += 3

            if score > 0:
                matches.append({
                    "title": art["title"],
                    "slug": art["slug"],
                    "url": f"/posts/{art['slug']}",
                    "score": score,
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return [{"title": m["title"], "url": m["url"]} for m in matches[:4]]
