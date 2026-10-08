"""
Pipeline Database Storage Engine
Handles persistence for raw signals, story clusters, pipeline jobs, published articles, and SEO performance feedback.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pipeline.config import settings
from pipeline.models import RawSignal, StoryCluster, PipelineJob, current_iso_time


class PipelineDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovered_signals (
                id TEXT PRIMARY KEY,
                source_name TEXT,
                source_type TEXT,
                title TEXT,
                summary TEXT,
                url TEXT UNIQUE,
                published_at TEXT,
                reliability_score REAL,
                search_velocity REAL,
                social_velocity REAL,
                recency_score REAL,
                category TEXT,
                image_url TEXT,
                created_at TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_clusters (
                cluster_id TEXT PRIMARY KEY,
                canonical_title TEXT,
                canonical_summary TEXT,
                category TEXT,
                composite_score REAL,
                priority TEXT,
                signal_count INTEGER,
                first_detected_at TEXT,
                last_updated_at TEXT,
                content_hash TEXT,
                status TEXT,
                raw_json TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_jobs (
                job_id TEXT PRIMARY KEY,
                cluster_id TEXT,
                status TEXT,
                current_step TEXT,
                step_history_json TEXT,
                error_message TEXT,
                article_slug TEXT,
                sanity_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS published_articles (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE,
                title TEXT,
                category TEXT,
                sanity_id TEXT,
                cluster_id TEXT,
                quality_score REAL,
                fact_confidence REAL,
                status TEXT,
                canonical_url TEXT,
                raw_json TEXT,
                published_at TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS gsc_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                page TEXT,
                clicks INTEGER,
                impressions INTEGER,
                ctr REAL,
                position REAL,
                recorded_at TEXT
            );
            """)

            # Create Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_url ON discovered_signals(url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clusters_score ON story_clusters(composite_score DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clusters_hash ON story_clusters(content_hash);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON pipeline_jobs(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_slug ON published_articles(slug);")
            conn.commit()

    # --- Signals ---
    def save_signals(self, signals: List[RawSignal]) -> int:
        inserted = 0
        now = current_iso_time()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for s in signals:
                try:
                    cursor.execute("""
                    INSERT INTO discovered_signals (
                        id, source_name, source_type, title, summary, url, published_at,
                        reliability_score, search_velocity, social_velocity, recency_score, category, image_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        search_velocity = excluded.search_velocity,
                        social_velocity = excluded.social_velocity,
                        recency_score = excluded.recency_score;
                    """, (
                        s.id, s.source_name, s.source_type, s.title, s.summary, s.url, s.published_at,
                        s.reliability_score, s.search_velocity, s.social_velocity, s.recency_score, s.category, s.image_url, now
                    ))
                    inserted += 1
                except Exception:
                    continue
            conn.commit()
        return inserted

    # --- Story Clusters ---
    def save_cluster(self, cluster: StoryCluster):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO story_clusters (
                cluster_id, canonical_title, canonical_summary, category,
                composite_score, priority, signal_count, first_detected_at,
                last_updated_at, content_hash, status, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cluster_id) DO UPDATE SET
                canonical_title = excluded.canonical_title,
                composite_score = excluded.composite_score,
                priority = excluded.priority,
                signal_count = excluded.signal_count,
                last_updated_at = excluded.last_updated_at,
                raw_json = excluded.raw_json,
                status = excluded.status;
            """, (
                cluster.cluster_id,
                cluster.canonical_title,
                cluster.canonical_summary,
                cluster.category,
                cluster.trend_score.composite_score,
                cluster.trend_score.priority,
                cluster.signal_count,
                cluster.first_detected_at,
                cluster.last_updated_at,
                cluster.content_hash,
                cluster.status,
                cluster.model_dump_json(),
            ))
            conn.commit()

    def get_cluster(self, cluster_id: str) -> Optional[StoryCluster]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM story_clusters WHERE cluster_id = ?", (cluster_id,))
            row = cursor.fetchone()
            if row:
                return StoryCluster.model_validate_json(row["raw_json"])
        return None

    def find_cluster_by_hash(self, content_hash: str) -> Optional[StoryCluster]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM story_clusters WHERE content_hash = ?", (content_hash,))
            row = cursor.fetchone()
            if row:
                return StoryCluster.model_validate_json(row["raw_json"])
        return None

    def get_top_clusters(self, limit: int = 10, min_score: float = 60.0) -> List[StoryCluster]:
        clusters = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT raw_json FROM story_clusters
            WHERE composite_score >= ? AND status != 'rejected'
            ORDER BY composite_score DESC, last_updated_at DESC
            LIMIT ?;
            """, (min_score, limit))
            for row in cursor.fetchall():
                try:
                    clusters.append(StoryCluster.model_validate_json(row["raw_json"]))
                except Exception:
                    continue
        return clusters

    # --- Jobs & State Machine ---
    def create_job(self, cluster_id: str) -> PipelineJob:
        now = current_iso_time()
        job_id = f"JOB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{cluster_id[-6:]}"
        job = PipelineJob(
            job_id=job_id,
            cluster_id=cluster_id,
            status="running",
            current_step="init",
            step_history=[{"step": "init", "status": "started", "timestamp": now}],
            created_at=now,
            updated_at=now,
        )
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO pipeline_jobs (
                job_id, cluster_id, status, current_step, step_history_json,
                error_message, article_slug, sanity_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                job.job_id, job.cluster_id, job.status, job.current_step,
                json.dumps(job.step_history), None, None, None, job.created_at, job.updated_at
            ))
            conn.commit()
        return job

    def update_job(
        self,
        job_id: str,
        status: str,
        current_step: str,
        step_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        article_slug: Optional[str] = None,
        sanity_id: Optional[str] = None,
    ):
        now = current_iso_time()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT step_history_json FROM pipeline_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            history = json.loads(row["step_history_json"]) if row and row["step_history_json"] else []

            step_entry = {"step": current_step, "status": status, "timestamp": now}
            if step_data:
                step_entry["data"] = step_data
            if error:
                step_entry["error"] = error
            history.append(step_entry)

            cursor.execute("""
            UPDATE pipeline_jobs SET
                status = ?,
                current_step = ?,
                step_history_json = ?,
                error_message = coalesce(?, error_message),
                article_slug = coalesce(?, article_slug),
                sanity_id = coalesce(?, sanity_id),
                updated_at = ?
            WHERE job_id = ?;
            """, (
                status, current_step, json.dumps(history), error, article_slug, sanity_id, now, job_id
            ))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return PipelineJob(
                    job_id=row["job_id"],
                    cluster_id=row["cluster_id"],
                    status=row["status"],
                    current_step=row["current_step"],
                    step_history=json.loads(row["step_history_json"]) if row["step_history_json"] else [],
                    error_message=row["error_message"],
                    article_slug=row["article_slug"],
                    sanity_id=row["sanity_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        return None

    def get_jobs(self, limit: int = 20, status: Optional[str] = None) -> List[PipelineJob]:
        jobs = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                SELECT * FROM pipeline_jobs WHERE status = ?
                ORDER BY updated_at DESC LIMIT ?;
                """, (status, limit))
            else:
                cursor.execute("""
                SELECT * FROM pipeline_jobs
                ORDER BY updated_at DESC LIMIT ?;
                """, (limit,))
            for row in cursor.fetchall():
                jobs.append(PipelineJob(
                    job_id=row["job_id"],
                    cluster_id=row["cluster_id"],
                    status=row["status"],
                    current_step=row["current_step"],
                    step_history=json.loads(row["step_history_json"]) if row["step_history_json"] else [],
                    error_message=row["error_message"],
                    article_slug=row["article_slug"],
                    sanity_id=row["sanity_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                ))
        return jobs

    # --- Published Articles ---
    def save_published_article(
        self,
        slug: str,
        title: str,
        category: str,
        sanity_id: str,
        cluster_id: str,
        quality_score: float,
        fact_confidence: float,
        status: str,
        canonical_url: str,
        raw_json: str,
    ):
        now = current_iso_time()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO published_articles (
                id, slug, title, category, sanity_id, cluster_id,
                quality_score, fact_confidence, status, canonical_url, raw_json, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                quality_score = excluded.quality_score,
                status = excluded.status,
                raw_json = excluded.raw_json;
            """, (
                f"art_{slug}", slug, title, category, sanity_id, cluster_id,
                quality_score, fact_confidence, status, canonical_url, raw_json, now
            ))
            # Also update cluster status
            cursor.execute("UPDATE story_clusters SET status = ? WHERE cluster_id = ?", (status, cluster_id))
            conn.commit()

    def get_published_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        articles = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, slug, title, category, sanity_id, cluster_id, quality_score, fact_confidence, status, canonical_url, published_at
            FROM published_articles
            ORDER BY published_at DESC LIMIT ?;
            """, (limit,))
            for row in cursor.fetchall():
                articles.append(dict(row))
        return articles

    def find_published_by_cluster(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM published_articles WHERE cluster_id = ?", (cluster_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    # --- Search Console Performance Feedback ---
    def record_gsc_metrics(self, rows: List[Dict[str, Any]]) -> int:
        now = current_iso_time()
        inserted = 0
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for r in rows:
                cursor.execute("""
                INSERT INTO gsc_feedback (query, page, clicks, impressions, ctr, position, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    r.get("query", ""),
                    r.get("page", ""),
                    r.get("clicks", 0),
                    r.get("impressions", 0),
                    r.get("ctr", 0.0),
                    r.get("position", 0.0),
                    now,
                ))
                inserted += 1
            conn.commit()
        return inserted

    def get_striking_distance_queries(self, min_pos: float = 5.0, max_pos: float = 20.0) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT query, page, clicks, impressions, ctr, position
            FROM gsc_feedback
            WHERE position >= ? AND position <= ? AND impressions > 50
            ORDER BY impressions DESC
            LIMIT 50;
            """, (min_pos, max_pos))
            return [dict(r) for r in cursor.fetchall()]
