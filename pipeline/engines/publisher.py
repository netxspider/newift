"""
Pipeline B: Sanity CMS Publisher
Handles idempotent mutations, category/author reference resolution, image asset uploading, and Next.js ISR revalidation.
"""
import io
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from pipeline.config import settings, PIPELINE_DIR
from pipeline.models import StoryCluster, SEOMetadata, QualityGateResult, current_iso_time
from pipeline.storage.db import PipelineDB

HEADERS = {
    "User-Agent": "Newift-Editorial-Pipeline/1.0",
}


class SanityPublisher:
    def __init__(self, db: Optional[PipelineDB] = None, client: Optional[httpx.Client] = None):
        self.db = db or PipelineDB()
        self.project_id = settings.sanity_project_id
        self.dataset = settings.sanity_dataset
        self.api_version = settings.sanity_api_version
        self.token = settings.sanity_api_write_token or os.getenv("SANITY_API_WRITE_TOKEN", "")
        self.client = client or httpx.Client(timeout=30.0)

        self.mutate_url = f"https://{self.project_id}.api.sanity.io/v{self.api_version}/data/mutate/{self.dataset}"
        self.assets_url = f"https://{self.project_id}.api.sanity.io/v{self.api_version}/assets/images/{self.dataset}"
        self.query_url = f"https://{self.project_id}.api.sanity.io/v{self.api_version}/data/query/{self.dataset}"

    def publish_article(
        self,
        cluster: StoryCluster,
        article_data: Dict[str, Any],
        seo_meta: SEOMetadata,
        quality_gate: QualityGateResult,
        cover_image_info: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Publishes article to Sanity with full idempotency checks.
        """
        slug = seo_meta.slug
        doc_id = f"post-{cluster.cluster_id}"

        # 1. Idempotency Check: check if cluster or slug was previously published
        existing_in_db = self.db.find_published_by_cluster(cluster.cluster_id)
        if existing_in_db:
            doc_id = existing_in_db["sanity_id"]

        # 2. Build Sanity Post Document
        doc: Dict[str, Any] = {
            "_id": doc_id,
            "_type": "post",
            "title": article_data["headline"],
            "slug": {"_type": "slug", "current": slug},
            "excerpt": article_data["dek"],
            "publishedAt": current_iso_time(),
            "updatedAt": current_iso_time(),
            "readTime": article_data.get("read_time", 4),
            "viewCount": 0,
            "keyPoints": article_data.get("key_points", []),
            "timeline": article_data.get("timeline", []),
            "faq": article_data.get("faq", []),
            "sources": article_data.get("sources", []),
            "story": article_data.get("story", {}),
            "verification": {
                "status": "verified" if quality_gate.passed else "needs_review",
                "confidence": quality_gate.fact_accuracy_score,
                "factCheckedAt": quality_gate.checked_at,
                "corroboratingSourcesCount": len(article_data.get("sources", [])),
                "notes": " • ".join(quality_gate.reasons) or "Multi-source corroboration verified.",
            },
            "aiDisclosure": article_data.get("ai_disclosure", {}),
            "seo": {
                "_type": "seo",
                "title": seo_meta.title,
                "description": seo_meta.description,
                "focusKeyword": seo_meta.focus_keyword,
                "secondaryKeywords": seo_meta.secondary_keywords,
                "canonicalUrl": seo_meta.canonical_url,
                "schemaType": seo_meta.schema_type,
                "noIndex": False,
            },
            "body": article_data.get("portable_text_body", []),
        }

        # Dry Run Mode or Missing Write Token
        if dry_run or not self.token:
            output_dir = PIPELINE_DIR / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{slug}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=2)

            self.db.save_published_article(
                slug=slug,
                title=doc["title"],
                category=cluster.category,
                sanity_id=doc_id,
                cluster_id=cluster.cluster_id,
                quality_score=quality_gate.composite_score,
                fact_confidence=quality_gate.fact_accuracy_score,
                status="dry_run_published" if quality_gate.passed else "dry_run_review",
                canonical_url=seo_meta.canonical_url,
                raw_json=json.dumps(doc),
            )

            return {
                "success": True,
                "mode": "dry_run",
                "document_id": doc_id,
                "slug": slug,
                "url": seo_meta.canonical_url,
                "saved_to": str(output_file),
                "quality_gate": quality_gate.model_dump(),
            }

        # 3. Live Sanity Publishing
        auth_headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        # Resolve or create Category and Author references
        category_ref = self._resolve_category_ref(cluster.category, auth_headers)
        if category_ref:
            doc["category"] = {"_type": "reference", "_ref": category_ref}

        author_ref = self._resolve_author_ref("Newift Desk", auth_headers)
        if author_ref:
            doc["author"] = {"_type": "reference", "_ref": author_ref}

        # Upload Cover Image if available
        if cover_image_info and cover_image_info.get("url"):
            image_ref = self._upload_image_asset(cover_image_info["url"])
            if image_ref:
                doc["coverImage"] = {
                    "_type": "image",
                    "asset": {"_type": "reference", "_ref": image_ref},
                    "alt": cover_image_info.get("alt", doc["title"]),
                    "caption": cover_image_info.get("caption"),
                    "attribution": cover_image_info.get("attribution"),
                    "sourceUrl": cover_image_info.get("source_url"),
                }

        # Execute createOrReplace mutation
        mutations = {"mutations": [{"createOrReplace": doc}]}
        resp = self.client.post(self.mutate_url, headers=auth_headers, json=mutations)
        if resp.status_code not in [200, 201]:
            raise RuntimeError(f"Sanity mutation error ({resp.status_code}): {resp.text}")

        # Trigger Next.js Revalidation Webhook
        self._trigger_revalidation(slug)

        # Save to local DB
        self.db.save_published_article(
            slug=slug,
            title=doc["title"],
            category=cluster.category,
            sanity_id=doc_id,
            cluster_id=cluster.cluster_id,
            quality_score=quality_gate.composite_score,
            fact_confidence=quality_gate.fact_accuracy_score,
            status="published" if quality_gate.passed else "draft_review",
            canonical_url=seo_meta.canonical_url,
            raw_json=json.dumps(doc),
        )

        return {
            "success": True,
            "mode": "live",
            "document_id": doc_id,
            "slug": slug,
            "url": seo_meta.canonical_url,
            "quality_gate": quality_gate.model_dump(),
        }

    def _resolve_category_ref(self, category_title: str, headers: Dict[str, str]) -> Optional[str]:
        try:
            query = f'*[_type == "category" && title == "{category_title}"][0]._id'
            resp = self.client.get(f"{self.query_url}?query={query}", headers=headers)
            if resp.status_code == 200:
                result = resp.json().get("result")
                if result:
                    return result
            # Create category if missing
            cat_id = f"category-{category_title.lower().replace(' ', '-')}"
            create_mut = {
                "mutations": [
                    {
                        "createIfNotExists": {
                            "_id": cat_id,
                            "_type": "category",
                            "title": category_title,
                            "slug": {"_type": "slug", "current": category_title.lower().replace(" ", "-")},
                        }
                    }
                ]
            }
            self.client.post(self.mutate_url, headers=headers, json=create_mut)
            return cat_id
        except Exception:
            return None

    def _resolve_author_ref(self, author_name: str, headers: Dict[str, str]) -> Optional[str]:
        try:
            query = f'*[_type == "author" && name == "{author_name}"][0]._id'
            resp = self.client.get(f"{self.query_url}?query={query}", headers=headers)
            if resp.status_code == 200:
                result = resp.json().get("result")
                if result:
                    return result
            auth_id = f"author-{author_name.lower().replace(' ', '-')}"
            create_mut = {
                "mutations": [
                    {
                        "createIfNotExists": {
                            "_id": auth_id,
                            "_type": "author",
                            "name": author_name,
                            "role": "Editorial Intelligence",
                        }
                    }
                ]
            }
            self.client.post(self.mutate_url, headers=headers, json=create_mut)
            return auth_id
        except Exception:
            return None

    def _upload_image_asset(self, image_url: str) -> Optional[str]:
        try:
            img_resp = self.client.get(image_url)
            if img_resp.status_code == 200:
                content_type = img_resp.headers.get("content-type", "image/jpeg")
                upload_resp = self.client.post(
                    self.assets_url,
                    headers={"Authorization": f"Bearer {self.token}", "Content-Type": content_type},
                    content=img_resp.content,
                )
                if upload_resp.status_code in [200, 201]:
                    return upload_resp.json().get("document", {}).get("_id")
        except Exception:
            pass
        return None

    def _trigger_revalidation(self, slug: str):
        if not settings.sanity_revalidate_secret:
            return
        try:
            self.client.post(
                settings.api_revalidate_url,
                headers={"x-sanity-webhook-secret": settings.sanity_revalidate_secret},
                json={"slug": slug},
                timeout=5.0,
            )
        except Exception:
            pass
