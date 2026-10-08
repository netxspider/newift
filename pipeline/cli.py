"""
Newift Pipeline Command Line Interface (CLI)
Provides comprehensive commands to run, inspect, and manage the automated news pipeline.
"""
import sys
import argparse
import json
from pipeline.config import settings
from pipeline.storage.db import PipelineDB
from pipeline.orchestrator import NewiftOrchestrator
from pipeline.engines.feedback_loop import FeedbackLoopEngine


def cmd_verify_setup(args):
    print("\n🔍 Checking Newift Pipeline Configuration & Environment...")
    print(f"  • Sanity Project ID: {settings.sanity_project_id} (Configured: {'✓' if settings.sanity_project_id else '✗'})")
    print(f"  • Sanity Dataset:    {settings.sanity_dataset} (Configured: {'✓' if settings.sanity_dataset else '✗'})")
    print(f"  • Sanity Write Token: {'✓ Present' if settings.sanity_api_write_token else '✗ Not set (Required for live Sanity publishing)'}")
    print(f"  • Gemini API Key:     {'✓ Present' if settings.gemini_api_key else '✗ Not set (Using algorithmic news synthesis fallback)'}")
    print(f"  • Site URL:           {settings.site_url}")
    print(f"  • Database Path:      {settings.database_path}")
    print(f"  • Min Publish Score:  {settings.min_publish_score}")
    print(f"  • Min Fact Confidence:{settings.min_fact_confidence}")
    print(f"  • Min Source Count:   {settings.min_source_count}")

    if not settings.sanity_api_write_token:
        print("\n💡 NOTE: To publish live articles into Sanity Studio, set SANITY_API_WRITE_TOKEN in .env.")
        print("   In the meantime, the pipeline can run in full dry-run mode and export complete JSON payloads!")
    if not settings.gemini_api_key:
        print("💡 NOTE: To enable Google Gemini AI generation, set GEMINI_API_KEY in .env.")
    print()


def cmd_discover(args):
    orchestrator = NewiftOrchestrator()
    clusters = orchestrator.run_pipeline_a(save_to_db=True)
    print(f"\n🔥 Top Trending Clusters ({len(clusters)} total discovered):\n")
    for idx, c in enumerate(clusters[: args.limit], 1):
        score = c.trend_score
        print(f"  {idx}. [{c.category.upper()}] {c.canonical_title}")
        print(f"     Cluster ID: {c.cluster_id}")
        print(f"     Score: {score.composite_score}/100 ({score.priority.upper()}) | Sources: {len(c.signals)}")
        print(f"     Velocities: Search={score.search_velocity} | News={score.news_velocity} | Social={score.social_velocity} | Recency={score.recency}")
        print()


def cmd_run_daily(args):
    orchestrator = NewiftOrchestrator()
    results = orchestrator.run_daily_pipeline(max_stories=args.max_stories, dry_run=args.dry_run)
    print(f"\nFinished. Processed {len(results)} stories.")


def cmd_process_cluster(args):
    orchestrator = NewiftOrchestrator()
    db = PipelineDB()
    cluster = db.get_cluster(args.cluster_id)
    if not cluster:
        print(f"❌ Cluster not found with ID: {args.cluster_id}")
        sys.exit(1)
    res = orchestrator.run_pipeline_b_for_cluster(cluster, dry_run=args.dry_run)
    print(json.dumps(res, indent=2))


def cmd_status(args):
    db = PipelineDB()
    jobs = db.get_jobs(limit=15)
    articles = db.get_published_articles(limit=15)
    print(f"\n📊 Pipeline System Status:")
    print(f"  • Total Published Articles Recorded: {len(articles)}")
    print(f"  • Recent Jobs ({len(jobs)}):")
    for j in jobs:
        status_icon = "✓" if j.status == "completed" else "⏳" if j.status == "running" else "⚠️" if j.status == "review_required" else "✗"
        print(f"    {status_icon} [{j.job_id}] Status: {j.status.upper()} | Step: {j.current_step} | Cluster: {j.cluster_id} | Slug: {j.article_slug or 'N/A'}")
    print()


def cmd_feedback(args):
    db = PipelineDB()
    engine = FeedbackLoopEngine(db)

    # If demo option is passed, populate sample GSC performance metrics
    if args.seed_demo:
        sample_metrics = [
            {"query": "what is apple m5 chip features", "page": "/posts/apple-m5-chip-launch", "clicks": 140, "impressions": 2800, "ctr": 0.05, "position": 8.4},
            {"query": "openai gpt 5 announcement timeline", "page": "/posts/openai-gpt-5-announcement", "clicks": 290, "impressions": 5400, "ctr": 0.053, "position": 6.2},
            {"query": "why did nvidia announce new ai model", "page": "/posts/nvidia-ai-breakthrough", "clicks": 90, "impressions": 1900, "ctr": 0.047, "position": 14.1},
        ]
        inserted = engine.record_performance_data(sample_metrics)
        print(f"✓ Inserted {inserted} sample Search Console records.")

    recommendations = engine.analyze_optimization_opportunities()
    print(f"\n📈 SEO Striking-Distance Optimization Recommendations ({len(recommendations)} found):\n")
    for r in recommendations:
        print(f"  • Page: {r['page']}")
        print(f"    Query: \"{r['target_query']}\" (Pos: {r['current_position']}, Impr: {r['impressions']})")
        print(f"    Action: [{r['action_type']}] {r['proposal']}\n")


def main():
    parser = argparse.ArgumentParser(description="Newift Automated Editorial & SEO Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # verify-setup
    subparsers.add_parser("verify-setup", help="Verify environment variables, tokens, and configuration")

    # discover
    p_disc = subparsers.add_parser("discover", help="Run Pipeline A: Trend Discovery & Story Clustering")
    p_disc.add_argument("--limit", type=int, default=10, help="Number of top clusters to display")

    # run-daily
    p_daily = subparsers.add_parser("run-daily", help="Run end-to-end daily pipeline")
    p_daily.add_argument("--max-stories", type=int, default=3, help="Maximum number of stories to process")
    p_daily.add_argument("--dry-run", action="store_true", help="Run in dry-run mode without modifying Sanity")

    # process-cluster
    p_proc = subparsers.add_parser("process-cluster", help="Run Pipeline B for a specific story cluster")
    p_proc.add_argument("cluster_id", type=str, help="Story Cluster ID")
    p_proc.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")

    # status
    subparsers.add_parser("status", help="View pipeline jobs and published articles")

    # feedback
    p_feed = subparsers.add_parser("feedback", help="Analyze Search Console queries and optimization feedback")
    p_feed.add_argument("--seed-demo", action="store_true", help="Seed sample GSC metrics for testing")

    args = parser.parse_args()

    if args.command == "verify-setup":
        cmd_verify_setup(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "run-daily":
        cmd_run_daily(args)
    elif args.command == "process-cluster":
        cmd_process_cluster(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "feedback":
        cmd_feedback(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
