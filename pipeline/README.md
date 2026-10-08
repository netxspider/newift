# Newift Automated News Intelligence, SEO & Fact Verification Pipeline

An enterprise-grade editorial automation pipeline engineered specifically for **Newift**, designed to comply with Google's helpful content guidelines by avoiding generic AI paraphrasing in favor of multi-source corroboration, deterministic trend scoring, differentiated reporting ("What happened", "Why it matters", "What changed", "Timeline", "FAQ"), and strict quality gates.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────┐
│             SCHEDULER / ORCHESTRATOR                   │
│        (Runs Pipeline A 6h, Pipeline B 24h)            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        PIPELINE A: TREND & STORY INTELLIGENCE          │
│  ├── Trend Discovery Engine (Google Trends, RSS, News, │
│  │   Reddit, Hacker News)                              │
│  ├── Deterministic Trend Scoring (6 Weighted Metrics)  │
│  └── Semantic Clustering & Deduplication (TF-IDF + Cos)│
└──────────────────────────┬─────────────────────────────┘
                           │ Canonical Story Clusters
                           ▼
┌────────────────────────────────────────────────────────┐
│        PIPELINE B: EDITORIAL & PUBLISHING ENGINE       │
│  ├── Multi-Source Research Layer (Extract claims & facts)
│  ├── SEO Engine (Keywords, slugs, schemas, cross-links)│
│  ├── Image Engine (Licensed sourcing & editorial fallbacks)
│  ├── AI Editorial Engine (What happened, Why it matters,
│  │   What changed, Timeline, FAQ, PortableText)        │
│  └── Quality Gate (Multi-dimensional verification &    │
│      safety routing: 🟢 Auto / 🟡 Review / 🔴 Hard Gate)│
└──────────────────────────┬─────────────────────────────┘
                           │
                ┌──────────┴──────────┐
      Score ≥ 85 & 🟢               Score < 85 or 🟡
                ▼                                 ▼
      ┌──────────────────┐              ┌──────────────────┐
      │  Auto-Publish    │              │  Human Review    │
      │  to Sanity CMS   │              │  Queue in DB     │
      └─────────┬────────┘              └──────────────────┘
                ▼
      ┌──────────────────┐
      │  Next.js Web     │
      │  • NewsArticle   │
      │  • FAQPage LD    │
      │  • Fact Badge    │
      │  • /rss.xml      │
      │  • /sitemap-news │
      └─────────┬────────┘
                ▼
      ┌──────────────────────────────────────────────────┐
      │  Search Console Feedback & Optimization Loop     │
      └──────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### 1. Verification & Configuration Check
```bash
python3 -m pipeline.cli verify-setup
```

### 2. Run Pipeline A: Discover Trends & Story Clusters
Scrapes Google Trends, Google News, Tech & World RSS feeds, and Reddit, clusters them, and scores them deterministically:
```bash
python3 -m pipeline.cli discover --limit 5
```

### 3. Run End-to-End Pipeline (Dry Run)
Runs the full pipeline without modifying your live Sanity dataset. Generates full JSON payloads, runs research, SEO, editorial synthesis, and quality gate evaluations, and saves output to `pipeline/output/<slug>.json`:
```bash
python3 -m pipeline.cli run-daily --dry-run --max-stories 2
```

### 4. Run Live Publishing into Sanity
Once `SANITY_API_WRITE_TOKEN` is set in `.env`:
```bash
python3 -m pipeline.cli run-daily --max-stories 3
```

### 5. Check Pipeline Status & Review Queue
```bash
python3 -m pipeline.cli status
```

### 6. SEO Feedback Loop
Analyzes Google Search Console query rankings to identify striking-distance opportunities (positions 5–20) and recommends specific section or FAQ additions:
```bash
python3 -m pipeline.cli feedback --seed-demo
```

---

## 🕒 Background Daemon & Schedulers

### Built-in Native Scheduler
Runs discovery every 6 hours and publishing every 24 hours:
```bash
python3 -m pipeline.scheduler --discovery-hours 6 --publish-hours 24
```

### FastAPI REST Service
Exposes HTTP endpoints for external schedulers (Cron, Cloud Scheduler, Inngest, Trigger.dev):
```bash
python3 -m pipeline.api
```
Key endpoints:
- `POST /pipeline/run`: trigger daily run
- `POST /pipeline/discover`: trigger trend discovery
- `GET /pipeline/status`: check job status
- `POST /pipeline/process-cluster/{id}`: process specific cluster

---

## 📋 What You Need to Set Up Explicitly

To enable 100% automated live publishing and multimodal AI, add these keys to `/Users/arnavraj/newift/.env`:

1. **`SANITY_API_WRITE_TOKEN`**:
   - Go to [Sanity Management Console](https://www.sanity.io/manage/project/kezbsr7k/api#tokens)
   - Click **Add API token**
   - Give it a name like `Newift Pipeline Worker` and select **Editor** permissions.
   - Paste the token into `SANITY_API_WRITE_TOKEN`.

2. **`GEMINI_API_KEY`**:
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Click **Get API key**
   - Paste into `GEMINI_API_KEY`.
   *(Note: The pipeline has an intelligent deterministic synthesis engine that runs cleanly even before adding this key!)*

3. **`SANITY_REVALIDATE_SECRET`** (Optional):
   - Any secret string shared between `web/.env.local` and `.env` to trigger immediate Next.js ISR cache purges on publish.
