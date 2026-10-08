"""
Pipeline Configuration & Settings
Loads environment variables with robust defaults for development and production.
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Base Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PIPELINE_DIR / "storage" / "pipeline.db"

# Load local .env if present
def load_env_file():
    env_paths = [
        BASE_DIR / ".env",
        BASE_DIR / ".env.local",
        PIPELINE_DIR / ".env",
        BASE_DIR / "web" / ".env.local",
    ]
    for p in env_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

load_env_file()


class Settings(BaseModel):
    # Sanity CMS Settings
    sanity_project_id: str = Field(default_factory=lambda: os.getenv("SANITY_PROJECT_ID", "kezbsr7k"))
    sanity_dataset: str = Field(default_factory=lambda: os.getenv("SANITY_DATASET", "production"))
    sanity_api_version: str = Field(default_factory=lambda: os.getenv("SANITY_API_VERSION", "2026-07-21"))
    sanity_api_write_token: str = Field(default_factory=lambda: os.getenv("SANITY_API_WRITE_TOKEN", ""))
    sanity_revalidate_secret: str = Field(default_factory=lambda: os.getenv("SANITY_REVALIDATE_SECRET", ""))

    # LLM & AI Settings
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    # Web & Hosting Settings
    site_url: str = Field(default_factory=lambda: os.getenv("NEXT_PUBLIC_SITE_URL", "https://newift.com"))
    api_revalidate_url: str = Field(default_factory=lambda: os.getenv("API_REVALIDATE_URL", "http://localhost:3000/api/revalidate"))

    # Database Path
    database_path: str = Field(default_factory=lambda: os.getenv("PIPELINE_DB_PATH", str(DEFAULT_DB_PATH)))

    # Quality Gate Thresholds
    min_cluster_score: float = 65.0
    min_publish_score: float = 85.0
    min_fact_confidence: float = 90.0
    min_source_count: int = 3
    max_stories_per_run: int = 5

    # Trend Scoring Weights (Must sum to 100)
    weight_search_velocity: float = 30.0
    weight_news_velocity: float = 20.0
    weight_social_velocity: float = 15.0
    weight_recency: float = 15.0
    weight_source_reliability: float = 10.0
    weight_newift_relevance: float = 10.0

    # Editorial Categorization & Safety Routing
    auto_publish_categories: List[str] = [
        "Tech",
        "Entertainment",
        "Gadgets",
        "Gaming",
        "Sports",
        "General",
    ]
    human_review_categories: List[str] = [
        "Business",
        "Finance",
        "Politics",
        "World",
        "Global",
    ]
    hard_stop_keywords: List[str] = [
        "fatal", "killed", "casualty", "massacre", "suicide", "terror",
        "lawsuit", "criminal charge", "indicted", "allegation", "sexual assault",
        "fraud investigation", "plane crash", "disaster", "election fraud",
        "medical cure", "vaccine danger", "experimental drug",
    ]

    # Discovery Source Feeds
    feed_sources: Dict[str, List[Dict[str, Any]]] = {
        "google_trends": [
            {"name": "Google Trends (US Daily)", "url": "https://trends.google.com/trending/rss?geo=US", "tier": 1},
            {"name": "Google Trends (Global Daily)", "url": "https://trends.google.com/trending/rss?geo=GLOBAL", "tier": 1},
        ],
        "google_news": [
            {"name": "Google News Tech", "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en", "tier": 1},
            {"name": "Google News Business", "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en", "tier": 1},
            {"name": "Google News Entertainment", "url": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en", "tier": 1},
            {"name": "Google News Science", "url": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en", "tier": 1},
        ],
        "tech_rss": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "tier": 2},
            {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "tier": 2},
            {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "tier": 2},
            {"name": "Wired", "url": "https://www.wired.com/feed/rss", "tier": 2},
        ],
        "world_rss": [
            {"name": "BBC Top Stories", "url": "https://feeds.bbci.co.uk/news/rss.xml", "tier": 1},
            {"name": "BBC Technology", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "tier": 1},
            {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml", "tier": 1},
        ],
        "social": [
            {"name": "Reddit Technology", "url": "https://www.reddit.com/r/technology/hot.json?limit=25", "tier": 3},
            {"name": "Reddit World News", "url": "https://www.reddit.com/r/worldnews/hot.json?limit=25", "tier": 3},
            {"name": "Hacker News Top", "url": "https://hacker-news.firebaseio.com/v0/topstories.json", "tier": 2},
        ],
    }

settings = Settings()
