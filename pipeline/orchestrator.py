"""
Newift Pipeline Orchestrator
Coordinates Pipeline A (News Intelligence & Clustering) and Pipeline B (Editorial & Publishing)
with state machine persistence, idempotency, and retryable steps.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from pipeline.config import settings
from pipeline.models import StoryCluster, PipelineJob, RawSignal
from pipeline.storage.db import PipelineDB
from pipeline.engines.trend_discovery import TrendDiscoveryEngine
from pipeline.engines.story_clustering import StoryClusteringEngine
from pipeline.engines.research_layer import ResearchLayerEngine
from pipeline.engines.editorial_engine import EditorialEngine
from pipeline.engines.seo_engine import SEOEngine
from pipeline.engines.image_engine import ImageEngine
from pipeline.engines.quality_gate import QualityGateEngine
from pipeline.engines.publisher import SanityPublisher


class NewiftOrchestrator:
    def __init__(self, db: Optional[PipelineDB] = None):
        self.db = db or PipelineDB()
        self.discovery_engine = TrendDiscoveryEngine()
        self.clustering_engine = StoryClusteringEngine()
        self.research_engine = ResearchLayerEngine()
        self.seo_engine = SEOEngine(self.db)
        self.editorial_engine = EditorialEngine()
        self.image_engine = ImageEngine()
        self.quality_gate_engine = QualityGateEngine()
        self.publisher = SanityPublisher(self.db)

    # -------------------------------------------------------------
    # Pipeline A: News & Trend Intelligence
    # -------------------------------------------------------------
    def run_pipeline_a(self, save_to_db: bool = True) -> List[StoryCluster]:
        """
        Discovers raw signals, clusters them, calculates deterministic trend scores,
        and saves top clusters to the database.
        """
        print("🔍 [Pipeline A] Collecting signals across Google Trends, RSS, News, and Social feeds...")
        raw_signals = self.discovery_engine.discover_all_signals()
        print(f"   ✓ Collected {len(raw_signals)} unique signals.")

        if save_to_db:
            saved_count = self.db.save_signals(raw_signals)
            print(f"   ✓ Stored {saved_count} signals in pipeline database.")

        print("🧬 [Pipeline A] Performing semantic clustering & deduplication...")
        clusters = self.clustering_engine.cluster_signals(raw_signals)
        print(f"   ✓ Formed {len(clusters)} canonical story clusters.")

        if save_to_db:
            for c in clusters:
                self.db.save_cluster(c)

        return clusters

    # -------------------------------------------------------------
    # Pipeline B: Editorial & Publishing Pipeline
    # -------------------------------------------------------------
    def run_pipeline_b_for_cluster(
        self,
        cluster: StoryCluster,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end editorial pipeline for a single story cluster:
        Research -> SEO -> AI Editorial -> Image -> Quality Gate -> Publishing.
        """
        # Create or resume pipeline job
        job = self.db.create_job(cluster.cluster_id)
        job_id = job.job_id
        print(f"\n🚀 [Pipeline B] Processing Story Cluster: {cluster.cluster_id} (Job: {job_id})")
        print(f"   Headline: \"{cluster.canonical_title}\"")
        print(f"   Trend Score: {cluster.trend_score.composite_score}/100 ({cluster.trend_score.priority.upper()})")

        try:
            # 1. Research & Fact Extraction
            self.db.update_job(job_id, status="running", current_step="research")
            print("   📚 Step 1: Conducting multi-source research & claim corroboration...")
            research_package = self.research_engine.conduct_research(cluster)
            print(f"      ✓ Extracted {len(research_package.facts)} facts, {len(research_package.quotes)} quotes, {len(research_package.primary_sources)} primary sources.")
            self.db.update_job(job_id, status="running", current_step="research", step_data={"facts_count": len(research_package.facts)})

            # 2. Editorial Engine (Synthesize striking, eye-catching headline & original analysis)
            self.db.update_job(job_id, status="running", current_step="editorial")
            print("   ✍️  Step 2: Synthesizing original analytical article & magnetic headline...")
            article_data = self.editorial_engine.generate_article(cluster, research_package)
            striking_headline = article_data["headline"]
            print(f"      ✨ Striking Headline: \"{striking_headline}\"")
            print(f"      ✓ Generated {len(article_data['key_points'])} key takeaways, {len(article_data.get('faq', []))} FAQs, {len(article_data['portable_text_body'])} PortableText blocks.")
            self.db.update_job(job_id, status="running", current_step="editorial", step_data={"headline": striking_headline, "key_points": len(article_data['key_points'])})

            # 3. SEO Optimization (Derives slug and tags directly from striking headline)
            self.db.update_job(job_id, status="running", current_step="seo")
            print("   🔎 Step 3: Generating SEO metadata, schema tags, and high-CTR slug...")
            seo_meta = self.seo_engine.generate_seo_metadata(
                cluster=cluster,
                research=research_package,
                headline=striking_headline,
                dek=article_data.get("dek"),
            )
            print(f"      ✓ Slug: /posts/{seo_meta.slug}")
            print(f"      ✓ Focus Keyword: \"{seo_meta.focus_keyword}\"")
            self.db.update_job(job_id, status="running", current_step="seo", step_data={"slug": seo_meta.slug, "keyword": seo_meta.focus_keyword})

            # 4. Mandatory Cover Image Processing (Source web image or high-res branded editorial banner)
            self.db.update_job(job_id, status="running", current_step="image")
            print("   🖼️  Step 4: Processing mandatory cover image asset...")
            cover_image = self.image_engine.process_cover_image(
                cluster=cluster,
                research=research_package,
                headline=striking_headline,
                dek=article_data.get("dek"),
            )
            cover_dict = cover_image.model_dump()
            print(f"      ✓ Image source: {cover_image.attribution or 'Newift Editorial Studio'}")
            print(f"      ✓ Image bytes ready: {len(cover_image.image_bytes) if cover_image.image_bytes else 'URL provided'}")
            self.db.update_job(job_id, status="running", current_step="image", step_data={"attribution": cover_image.attribution})

            # 5. Quality Gate & Safety Verification
            self.db.update_job(job_id, status="running", current_step="quality_gate")
            print("   ⚖️  Step 5: Evaluating Quality Gate & verification thresholds...")
            quality_result = self.quality_gate_engine.evaluate(cluster, research_package, article_data, seo_meta)
            print(f"      ✓ Quality Score: {quality_result.composite_score}/100")
            print(f"      ✓ Fact Accuracy: {quality_result.fact_accuracy_score}/100")
            print(f"      ✓ Safety Gate: {quality_result.safety_classification.upper()}")
            print(f"      ✓ Auto-publish: {'APPROVED' if quality_result.passed else 'REQUIRES HUMAN REVIEW'}")
            self.db.update_job(job_id, status="running", current_step="quality_gate", step_data=quality_result.model_dump())

            # 6. Publishing to Sanity CMS with Guaranteed Cover Image Asset
            self.db.update_job(job_id, status="running", current_step="publishing")
            print("   📡 Step 6: Syncing document & cover image asset to Sanity CMS...")
            publish_result = self.publisher.publish_article(
                cluster=cluster,
                article_data=article_data,
                seo_meta=seo_meta,
                quality_gate=quality_result,
                cover_image_info=cover_dict,
                dry_run=dry_run,
            )

            final_status = "completed" if quality_result.passed else "review_required"
            self.db.update_job(
                job_id,
                status=final_status,
                current_step="completed",
                article_slug=seo_meta.slug,
                sanity_id=publish_result.get("document_id"),
                step_data=publish_result,
            )

            print(f"   🎉 Done! Status: {final_status.upper()} | URL: {seo_meta.canonical_url}\n")
            return {
                "job_id": job_id,
                "status": final_status,
                "cluster_id": cluster.cluster_id,
                "slug": seo_meta.slug,
                "url": seo_meta.canonical_url,
                "quality_score": quality_result.composite_score,
                "publish_result": publish_result,
            }

        except Exception as e:
            err_msg = str(e)
            print(f"   ❌ Error in Pipeline B: {err_msg}")
            self.db.update_job(job_id, status="failed", current_step="failed", error=err_msg)
            return {"job_id": job_id, "status": "failed", "error": err_msg}

    # -------------------------------------------------------------
    # End-to-End Daily Runner
    # -------------------------------------------------------------
    def run_daily_pipeline(self, max_stories: int = 3, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Runs the complete 24h automation cycle:
        1. Run Pipeline A (Trend Discovery + Scoring + Clustering)
        2. Pick top 1-N high scoring stories
        3. Run Pipeline B for each selected story
        """
        print("===================================================================")
        print(f"  Newift Daily Editorial & Publishing Pipeline (Dry Run: {dry_run})")
        print("===================================================================")

        clusters = self.run_pipeline_a()
        if not clusters:
            print("⚠️ No story clusters identified.")
            return []

        # Filter high priority or highest scoring clusters
        top_clusters = [c for c in clusters if c.trend_score.composite_score >= settings.min_cluster_score][:max_stories]
        if not top_clusters:
            top_clusters = clusters[:max_stories]

        print(f"\n📋 Selected top {len(top_clusters)} stories for full editorial coverage:")
        for idx, c in enumerate(top_clusters, 1):
            print(f"   {idx}. [{c.category}] {c.canonical_title} (Score: {c.trend_score.composite_score})")

        results = []
        for c in top_clusters:
            res = self.run_pipeline_b_for_cluster(c, dry_run=dry_run)
            results.append(res)

        print("===================================================================")
        print(f"  Pipeline Run Complete! Processed {len(results)} stories.")
        print("===================================================================")
        return results
