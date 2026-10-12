# ⚡ Newift — Automated News Intelligence, SEO & Editorial Platform

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=flat&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-blue?style=flat&logo=react)](https://react.dev/)
[![Sanity](https://img.shields.io/badge/Sanity-Studio%20v6-red?style=flat&logo=sanity)](https://www.sanity.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-orange?style=flat&logo=google)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-Proprietary-gray?style=flat)]()

**Newift** is an enterprise-grade automated editorial intelligence, SEO, and publishing platform built to report breaking news and trending developments at internet speed.

Unlike naive "cron → LLM → publish" scripts, Newift is architected from the ground up to comply with **Google's Helpful Content and Information Gain guidelines**:
- Multi-source fact corroboration (≥3 independent outlets) before any story is published.
- Deterministic trend acceleration scoring (combining velocity, breadth, acceleration, and corroboration).
- Original analytical breakdown (*What happened*, *Why it matters*, *What changed*, *Timeline*, *FAQ*).
- Magnetic, high-stakes journalistic headlines (banning raw search queries and passive wire rewrites).
- 100% guaranteed cover image assets (source extraction or automated 1200×675 Pillow editorial briefing banners).
- In-browser interactive **Voice Reader** with Web Speech API audio briefings.
- Google Discover & News ready with structured `NewsArticle` / `FAQPage` JSON-LD schemas, Google News Sitemap, and instant ISR cache revalidation.

---

## 📑 Table of Contents

1. [Architecture Overview](#-architecture-overview)
2. [Project Structure](#-project-structure)
3. [Prerequisites](#-prerequisites)
4. [Step-by-Step Installation & Setup](#-step-by-step-installation--setup)
   - [1. Clone Repository](#1-clone-repository)
   - [2. Configure Environment Variables](#2-configure-environment-variables)
   - [3. Python Intelligence Pipeline Setup](#3-python-intelligence-pipeline-setup)
   - [4. Next.js Web Application Setup](#4-nextjs-web-application-setup)
   - [5. Sanity Studio Setup](#5-sanity-studio-setup)
5. [Running the Intelligence Pipeline](#-running-the-intelligence-pipeline)
   - [Verification Check](#verification-check)
   - [Pipeline A: Trend Discovery & Clustering](#pipeline-a-trend-discovery--clustering)
   - [Pipeline B: Dry-Run Testing](#pipeline-b-dry-run-testing)
   - [Pipeline B: Live Production Publishing](#pipeline-b-live-production-publishing)
   - [Pipeline Status & Quality Gate Review](#pipeline-status--quality-gate-review)
   - [SEO Search Console Feedback Loop](#seo-search-console-feedback-loop)
6. [Background Automation & Schedulers](#-background-automation--schedulers)
   - [Native Background Scheduler](#native-background-scheduler)
   - [FastAPI Microservice (REST API)](#fastapi-microservice-rest-api)
7. [Core Platform Features](#-core-platform-features)
   - [Striking, High-CTR Headlines](#1-striking-high-ctr-headlines)
   - [Mandatory Cover Image Engine](#2-mandatory-cover-image-engine)
   - [Interactive Voice Reader](#3-interactive-voice-reader)
   - [SEO, Schema & Google Discover Readiness](#4-seo-schema--google-discover-readiness)
8. [Production Deployment Guide](#-production-deployment-guide)
9. [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🏛️ Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   NEWIFT SCHEDULER & ORCHESTRATOR                      │
│                (Pipeline A every 6h • Pipeline B every 24h)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 PIPELINE A: TREND DISCOVERY & CLUSTERING               │
│  ├── Trend Discovery Engine: Google Trends, RSS feeds, Google News,    │
│  │   Reddit, and Hacker News signals                                   │
│  ├── Deterministic Trend Scorer: 6 weighted metrics (Velocity,         │
│  │   Acceleration, Source Breadth, Corroboration Factor)               │
│  └── Semantic Clustering: TF-IDF + Cosine similarity deduplication    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Canonical Story Clusters
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 PIPELINE B: EDITORIAL & PUBLISHING ENGINE              │
│  ├── Multi-Source Research Layer: Scrapes & cross-verifies claims      │
│  ├── AI Editorial Engine: Synthesizes striking headline, dek, key      │
│  │   takeaways, What Happened, Why It Matters, What Changed, FAQ,      │
│  │   Timeline, and PortableText blocks (Gemini 2.5 Flash + Failovers)  │
│  ├── SEO Engine: Derives slug, meta description, and keywords          │
│  │   directly from striking headline                                   │
│  ├── Image Engine: Extracts high-res web images or generates a custom  │
│  │   1200×675 Pillow editorial briefing graphic with category styling  │
│  ├── Quality Gate: Multi-point verification check                      │
│  │   (Composite score ≥ 85, Fact confidence ≥ 90, Safety: 🟢 / 🟡 / 🔴) │
│  └── Sanity Publisher: Uploads image asset to Sanity Assets API,       │
│      writes idempotent mutations, and sends signed ISR webhook         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
          Quality ≥ 85 & 🟢               Quality < 85 or 🟡
                    ▼                               ▼
          ┌───────────────────┐           ┌───────────────────┐
          │  Auto-Published   │           │   Human Review    │
          │   to Sanity CMS   │           │   Queue (SQLite)  │
          └─────────┬─────────┘           └───────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │    Next.js Web    │
          │  • NewsArticle LD │
          │  • FAQPage Schema │
          │  • Voice Reader   │
          │  • Fact Badge     │
          │  • /rss.xml       │
          │  • /sitemap-news  │
          └───────────────────┘
```

---

## 📂 Project Structure

```text
newift/
├── requirements.txt            # Python dependencies for the editorial pipeline
├── .env.example                # Template for environment credentials
├── pipeline/                   # Python Editorial & Intelligence Pipeline
│   ├── cli.py                  # Command-line interface (discover, run-daily, status, etc.)
│   ├── orchestrator.py         # End-to-end pipeline coordinator
│   ├── scheduler.py            # Continuous background daemon
│   ├── api.py                  # FastAPI REST endpoints for webhook/cloud triggers
│   ├── config.py               # Settings & environment variable loader
│   ├── models.py               # Pydantic data schemas
│   ├── storage/
│   │   ├── db.py               # SQLite pipeline database interface
│   │   └── pipeline.db         # Persistent storage (jobs, clusters, audit logs)
│   └── engines/
│       ├── trend_discovery.py  # Signal collectors (Google Trends, RSS, Social)
│       ├── trend_scoring.py    # Deterministic scoring algorithms
│       ├── story_clustering.py # TF-IDF semantic deduplication
│       ├── research_layer.py   # Multi-source fact corroboration scraper
│       ├── editorial_engine.py # AI synthesis & magnetic headline generator
│       ├── image_engine.py     # High-res image extractor & Pillow banner renderer
│       ├── seo_engine.py       # Slugs, meta descriptions & schema generator
│       ├── quality_gate.py     # Editorial safety & threshold verification
│       ├── publisher.py        # Sanity CMS mutations & HMAC ISR revalidation
│       └── seo_feedback.py     # Search Console ranking analysis & content optimizer
├── web/                        # Next.js 16 Web Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Homepage (featured stories, trending feed)
│   │   │   ├── posts/[slug]/   # Dynamic article page (Voice reader, JSON-LD, FAQ)
│   │   │   ├── api/revalidate/ # Next.js ISR on-demand cache revalidation route
│   │   │   ├── rss.xml/        # Automated RSS feed
│   │   │   ├── sitemap-news.xml# Google News sitemap
│   │   │   └── globals.css     # Luxury editorial design system & animations
│   │   ├── components/
│   │   │   ├── VoiceReader.tsx # In-browser Web Speech API audio player
│   │   │   ├── SiteShell.tsx   # Header, brandmark & footer navigation
│   │   │   └── UtilityControls.tsx # Search bar & dark/light theme toggle
│   │   ├── sanity/             # Sanity client, queries, and image URL builders
│   │   └── lib/                # Types and fallback content helpers
│   └── package.json
└── studio/                     # Sanity Studio v6 (Content Management)
    ├── schemaTypes/
    │   ├── postType.ts         # Post schema (Key takeaways, timeline, FAQ, sources, etc.)
    │   ├── categoryType.ts     # Category schema with trending metadata
    │   ├── authorType.ts       # Author & editorial profile schema
    │   └── seoType.ts          # Structured SEO schema
    ├── sanity.config.ts        # Sanity Studio workspace configuration
    └── package.json
```

---

## 🛠️ Prerequisites

Make sure the following tools are installed on your machine or server:
- **Node.js**: `v20.x` or `v22.x` (LTS recommended)
- **npm**: `v10.x` or higher
- **Python**: `3.10` or higher (Python 3.12+ recommended)
- **Sanity Account**: A project on [Sanity.io](https://www.sanity.io/) (default project: `kezbsr7k`)
- **Google Gemini API Key**: Free or paid key from [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Step-by-Step Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/netxspider/newift.git
cd newift
```

### 2. Configure Environment Variables

Copy the example environment configuration into `.env` at the root of the workspace:

```bash
cp .env.example .env
```

Open `.env` in your editor and supply your credentials:

```bash
# --- Sanity CMS Configuration ---
NEXT_PUBLIC_SANITY_PROJECT_ID=kezbsr7k
NEXT_PUBLIC_SANITY_DATASET=production
SANITY_PROJECT_ID=kezbsr7k
SANITY_DATASET=production
SANITY_API_VERSION=2026-07-21

# REQUIRED for automated publishing:
# Generate at: https://www.sanity.io/manage/project/kezbsr7k/api#tokens
# Ensure you assign "Editor" permissions!
SANITY_API_WRITE_TOKEN=skYourSanityWriteTokenHere

# OPTIONAL: Webhook secret to trigger Next.js Instant Cache Revalidation (/api/revalidate)
# Generate with: openssl rand -hex 32
SANITY_REVALIDATE_SECRET=your_revalidate_secret_hex

# --- Google Gemini AI Configuration ---
# Generate at: https://aistudio.google.com/
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GEMINI_MODEL=gemini-2.5-flash

# --- Frontend Website URL ---
NEXT_PUBLIC_SITE_URL=https://newift.com

# --- Pipeline Storage ---
PIPELINE_DB_PATH=pipeline/storage/pipeline.db
```

#### Environment Variable Reference

| Variable | Required | Description |
|---|:---:|---|
| `NEXT_PUBLIC_SANITY_PROJECT_ID` | **Yes** | Your Sanity Project ID (`kezbsr7k`) |
| `NEXT_PUBLIC_SANITY_DATASET` | **Yes** | Dataset name (`production`) |
| `SANITY_API_WRITE_TOKEN` | **Yes** (Live) | Sanity API token with **Editor** permissions for publishing articles and uploading cover image assets |
| `SANITY_REVALIDATE_SECRET` | **Recommended** | Secret key for signing HMAC-SHA256 headers to purge Next.js ISR cache on `/api/revalidate` |
| `GEMINI_API_KEY` | **Recommended** | Google Gemini API key for PULITZER-caliber analytical news synthesis |
| `GEMINI_MODEL` | Optional | Primary Gemini model (defaults to fast and reliable `gemini-2.5-flash`) |
| `NEXT_PUBLIC_SITE_URL` | **Yes** | Canonical website URL (e.g. `https://newift.com` or `https://newift.netlify.app`) |
| `PIPELINE_DB_PATH` | Optional | SQLite database location (defaults to `pipeline/storage/pipeline.db`) |

---

### 3. Python Intelligence Pipeline Setup

Set up a dedicated Python virtual environment and install the required packages:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# 3. Install pipeline dependencies
pip install -r requirements.txt
```

Verify your setup:

```bash
python3 -m pipeline.cli verify-setup
```

A properly configured environment will output:
```text
🔍 Checking Newift Pipeline Configuration & Environment...
  • Sanity Project ID: kezbsr7k (Configured: ✓)
  • Sanity Dataset:    production (Configured: ✓)
  • Sanity Write Token: ✓ Configured (Permissions: Editor)
  • Gemini API Key:     ✓ Configured (Model: gemini-2.5-flash)
  • Site URL:           https://newift.com
  • Database Path:      /Users/arnavraj/newift/pipeline/storage/pipeline.db
  • Min Publish Score:  85.0
  • Min Fact Confidence:90.0
  • Min Source Count:   3
```

---

### 4. Next.js Web Application Setup

Navigate to the `web/` directory and install dependencies:

```bash
cd web
npm install
```

Copy the environment variables for local development:
```bash
cp ../.env .env.local
```

Start the Next.js development server:
```bash
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser to view the live frontend.

To verify a production build:
```bash
npm run build
```

---

### 5. Sanity Studio Setup

Navigate to `studio/` and install dependencies:

```bash
cd ../studio
npm install
```

Start Sanity Studio locally:
```bash
npm run dev
```
Open **[http://localhost:3333](http://localhost:3333)** in your browser to inspect schemas, review drafts, or edit published articles.

To deploy Sanity Studio to the cloud:
```bash
npm run deploy
```

---

## ⚡ Running the Intelligence Pipeline

The pipeline is operated via the `pipeline.cli` module.

### Verification Check
Validates your `.env` configuration, database connection, and API tokens:
```bash
python3 -m pipeline.cli verify-setup
```

### Pipeline A: Trend Discovery & Clustering
Scrapes signals across Google Trends, Google News, Tech/World RSS feeds, Reddit, and social signals; deduplicates them with cosine similarity; and computes deterministic trend scores:
```bash
# Discover top 5 clusters
python3 -m pipeline.cli discover --limit 5
```

### Pipeline B: Dry-Run Testing
Runs research, fact extraction, magnetic headline creation, SEO metadata derivation, and image rendering **without modifying your live Sanity dataset**. Complete documents are exported to `pipeline/output/<slug>.json`:
```bash
python3 -m pipeline.cli run-daily --dry-run --max-stories 2
```

### Pipeline B: Live Production Publishing
Executes the full pipeline and publishes verified stories directly into Sanity CMS, uploads 1200×675 cover image assets, and triggers Next.js cache revalidation:
```bash
python3 -m pipeline.cli run-daily --max-stories 3
```

### Pipeline Status & Quality Gate Review
Displays recent jobs, auto-published articles, quality scores, and stories waiting in the human-review queue:
```bash
python3 -m pipeline.cli status
```

### SEO Search Console Feedback Loop
Analyzes query impressions and click rankings to find "striking distance" queries (positions 5–20) and recommends specific section or FAQ optimizations:
```bash
python3 -m pipeline.cli feedback --seed-demo
```

---

## 🕒 Background Automation & Schedulers

### Native Background Scheduler
The pipeline includes a built-in multi-interval daemon that automatically runs **Pipeline A every 6 hours** and **Pipeline B every 24 hours**:

```bash
python3 -m pipeline.scheduler --discovery-hours 6 --publish-hours 24
```

To run this persistently in the background on your machine or a server:
```bash
nohup python3 -m pipeline.scheduler --discovery-hours 6 --publish-hours 24 > pipeline.log 2>&1 &
```

To verify the background process is running:
```bash
ps aux | grep pipeline.scheduler
```

To stop the background process:
```bash
kill $(pgrep -f "pipeline.scheduler")
```

### FastAPI Microservice (REST API)
If you prefer triggering the pipeline from external orchestrators (such as Google Cloud Scheduler, GitHub Actions, AWS EventBridge, Inngest, or Trigger.dev), launch the REST API daemon:

```bash
python3 -m pipeline.api
```
The server runs on `http://localhost:8000`. Available endpoints:
- `POST /pipeline/run`: Triggers full daily editorial and publishing workflow
- `POST /pipeline/discover`: Triggers Trend Discovery (Pipeline A)
- `GET /pipeline/status`: Returns current pipeline status and recent published stories
- `POST /pipeline/process-cluster/{id}`: Processes a specific story cluster

---

## 🌟 Core Platform Features

### 1. Striking, High-CTR Headlines
Raw search queries (such as `"us immigration and customs enforcement"` or `"apple m5 chip"`) are strictly forbidden from publishing. 

The editorial engine (`editorial_engine.py`) enforces Pulitzer-caliber news framing:
- **Generic:** `us immigration and customs enforcement` ❌
- **Striking:** `ICE Unleashes Expanded Operations: New Directives Ignite Federal-Local Clash` ✅

The striking headline automatically dictates:
- The clean URL slug: `/posts/ice-unleashes-expanded-operations-new-directives-ignite-fede`
- The `og:title` and `<title>` tag for social and search crawlers
- The typography on the generated editorial banner

### 2. Mandatory Cover Image Engine
Every published article is **guaranteed** to have a high-resolution cover image asset attached:
1. **Primary Sourcing:** Scrapes and downloads high-resolution `og:image` metadata from verified reporting outlets.
2. **Editorial Fallback (`render_editorial_banner`):** If no external image is available, Pillow renders a **1200×675 (16:9)** high-contrast editorial briefing graphic featuring:
   - Category-tailored color gradients (Navy/Amber for Politics, Electric Indigo for Tech, Emerald for Business, Violet for Culture).
   - Category pill badge and ambient depth lighting.
   - The striking headline rendered in bold typography with subtle drop shadow.
   - Newift brand mark and `✓ VERIFIED REPORT` seal.
3. **Direct Asset Upload:** Uploads image bytes directly to Sanity Assets API (`/assets/images/production`) and attaches the asset reference `_ref` to `coverImage`.

### 3. Interactive Voice Reader
Post pages include a native, in-browser audio player (`VoiceReader.tsx`) powered by the Web Speech API:
- **Zero API costs & zero latency** across modern desktop and mobile browsers.
- Automatically reads the **Headline**, **Dek**, **Key Takeaways**, and **Body Paragraphs** sequentially.
- **Controls:** Play, Pause, Resume, Stop, and Speed Toggle (`1x`, `1.25x`, `1.5x`).
- **Visuals:** Animated sound equalizer waveform pulsing during playback.

### 4. SEO, Schema & Google Discover Readiness
- **Structured Data:** Full `NewsArticle` schema with publisher logos, author attribution, citation sources, and `FAQPage` schema.
- **Google News Sitemap:** Available at `/sitemap-news.xml`.
- **RSS Feed:** Available at `/rss.xml`.
- **Instant Cache Invalidation:** The pipeline signs an HMAC-SHA256 signature (`sanity-webhook-signature`) and posts to `/api/revalidate`, refreshing the Next.js edge cache the instant an article is published.

---

## 🌐 Production Deployment Guide

### Deploying the Web Frontend (Netlify / Vercel)

The Next.js frontend is configured for instant deployment on Netlify or Vercel:

1. Push your repository to GitHub.
2. Link the repository in your Netlify or Vercel dashboard.
3. Set the **Base directory** to `web`.
4. Set the **Build command** to `npm run build`.
5. Set the **Publish directory** to `.next`.
6. Add the following **Environment Variables** in your hosting dashboard:
   - `NEXT_PUBLIC_SANITY_PROJECT_ID`: `kezbsr7k`
   - `NEXT_PUBLIC_SANITY_DATASET`: `production`
   - `NEXT_PUBLIC_SITE_URL`: `https://your-domain.com` (or Netlify URL)
   - `SANITY_REVALIDATE_SECRET`: Same secret configured in `.env`

### Deploying Sanity Studio

Deploy Sanity Studio to Sanity's global CDN:
```bash
cd studio
npx sanity deploy
```
Choose your studio subdomain (e.g. `newift.sanity.studio`).

### Deploying the Python Pipeline on a Server

You can run the Python pipeline on any Linux VM (Ubuntu/Debian, AWS EC2, DigitalOcean Droplet, Hetzner):

```bash
# On your server:
git clone https://github.com/netxspider/newift.git
cd newift
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your production tokens:
nano .env

# Run scheduler as a systemd service or background daemon:
nohup python3 -m pipeline.scheduler --discovery-hours 6 --publish-hours 24 > pipeline.log 2>&1 &
```

---

## ❓ Troubleshooting & FAQs

### Q1: `Sanity Write Token: ✗ Not set`
**Fix:** Ensure your `.env` file exists at the root of the project (`/Users/arnavraj/newift/.env`) and contains `SANITY_API_WRITE_TOKEN`.
- Generate the token in your [Sanity Management Console](https://www.sanity.io/manage/project/kezbsr7k/api#tokens).
- Select **Editor** permissions so the worker can create documents and upload assets.

### Q2: Gemini API returns `503 UNAVAILABLE` / High Demand
**Fix:** The pipeline includes automatic multi-model failover. In `pipeline/config.py` and `pipeline/engines/editorial_engine.py`, the model order prioritizes `gemini-2.5-flash`, which has the highest quota and responds in ~2 seconds. If Gemini is unavailable, the pipeline falls back gracefully to its internal algorithmic synthesis engine.

### Q3: `401 Invalid signature` on `/api/revalidate`
**Fix:** Verify that `SANITY_REVALIDATE_SECRET` matches exactly between `.env` and your Netlify/Vercel environment variables. The pipeline calculates a millisecond-precision HMAC-SHA256 signature (`t=<ms>,v1=<base64url>`) matching the `@sanity/webhook` specification.

### Q4: Checking pipeline background logs
```bash
tail -f pipeline.log
```

---

## 📄 License

Proprietary software for **Newift**. All rights reserved.
