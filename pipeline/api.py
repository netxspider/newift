"""
Newift Pipeline REST API (FastAPI)
Provides webhook and HTTP endpoints for orchestrating the pipeline, inspecting jobs, and integrating with external schedulers.
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from pipeline.orchestrator import NewiftOrchestrator
from pipeline.storage.db import PipelineDB
from pipeline.engines.feedback_loop import FeedbackLoopEngine
from pipeline.config import settings

app = FastAPI(
    title="Newift Editorial Intelligence API",
    description="Automated News Editorial, SEO, and Fact Verification Pipeline",
    version="1.0.0",
)

db = PipelineDB()
orchestrator = NewiftOrchestrator(db)
feedback_engine = FeedbackLoopEngine(db)


class RunRequest(BaseModel):
    max_stories: int = 3
    dry_run: bool = False
    background: bool = True


class GSCMetricItem(BaseModel):
    query: str
    page: str
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "newift-pipeline",
        "sanity_project_id": settings.sanity_project_id,
        "database": settings.database_path,
    }


@app.get("/pipeline/status")
def get_status():
    jobs = db.get_jobs(limit=10)
    articles = db.get_published_articles(limit=10)
    return {
        "published_articles_count": len(articles),
        "recent_jobs": [j.model_dump() for j in jobs],
    }


@app.post("/pipeline/discover")
def trigger_discover(limit: int = 10):
    clusters = orchestrator.run_pipeline_a(save_to_db=True)
    return {
        "count": len(clusters),
        "top_clusters": [c.model_dump() for c in clusters[:limit]],
    }


@app.get("/pipeline/clusters")
def list_clusters(limit: int = 20, min_score: float = 60.0):
    clusters = db.get_top_clusters(limit=limit, min_score=min_score)
    return {"clusters": [c.model_dump() for c in clusters]}


@app.get("/pipeline/jobs")
def list_jobs(limit: int = 20, status: Optional[str] = None):
    jobs = db.get_jobs(limit=limit, status=status)
    return {"jobs": [j.model_dump() for j in jobs]}


@app.post("/pipeline/run")
def trigger_pipeline(req: RunRequest, background_tasks: BackgroundTasks):
    if req.background:
        background_tasks.add_task(orchestrator.run_daily_pipeline, max_stories=req.max_stories, dry_run=req.dry_run)
        return {"status": "started", "message": f"Daily pipeline started in background (max_stories={req.max_stories}, dry_run={req.dry_run})"}
    else:
        results = orchestrator.run_daily_pipeline(max_stories=req.max_stories, dry_run=req.dry_run)
        return {"status": "completed", "results": results}


@app.post("/pipeline/process-cluster/{cluster_id}")
def process_single_cluster(cluster_id: str, dry_run: bool = False):
    cluster = db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Story cluster not found")
    result = orchestrator.run_pipeline_b_for_cluster(cluster, dry_run=dry_run)
    return result


@app.post("/pipeline/feedback/ingest")
def ingest_gsc_metrics(metrics: List[GSCMetricItem]):
    rows = [m.model_dump() for m in metrics]
    inserted = feedback_engine.record_performance_data(rows)
    return {"inserted": inserted}


@app.get("/pipeline/feedback/opportunities")
def get_seo_opportunities():
    recommendations = feedback_engine.analyze_optimization_opportunities()
    return {"opportunities": recommendations}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pipeline.api:app", host="0.0.0.0", port=8000, reload=True)
