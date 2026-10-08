"""
Pipeline A: Trend Discovery Engine
Discovers trending news and viral topics across Google Trends, RSS feeds, News APIs, and Social signals.
"""
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from pipeline.config import settings
from pipeline.models import RawSignal, current_iso_time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
}


class TrendDiscoveryEngine:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(headers=HEADERS, timeout=10.0, follow_redirects=True)

    def discover_all_signals(self) -> List[RawSignal]:
        all_signals: List[RawSignal] = []

        # 1. Google Trends Feeds
        for feed in settings.feed_sources.get("google_trends", []):
            signals = self._fetch_google_trends(feed["url"], feed["name"])
            all_signals.extend(signals)

        # 2. Google News Feeds
        for feed in settings.feed_sources.get("google_news", []):
            signals = self._fetch_rss_feed(feed["url"], feed["name"], "google_news", feed.get("tier", 1))
            all_signals.extend(signals)

        # 3. Major Tech Outlets
        for feed in settings.feed_sources.get("tech_rss", []):
            signals = self._fetch_rss_feed(feed["url"], feed["name"], "tech_rss", feed.get("tier", 2))
            all_signals.extend(signals)

        # 4. Major World Outlets
        for feed in settings.feed_sources.get("world_rss", []):
            signals = self._fetch_rss_feed(feed["url"], feed["name"], "world_rss", feed.get("tier", 1))
            all_signals.extend(signals)

        # 5. Social & Community Signals (Reddit & Hacker News)
        social_signals = self._fetch_social_signals()
        all_signals.extend(social_signals)

        # Deduplicate signals by normalized URL / Title
        unique_signals: Dict[str, RawSignal] = {}
        for s in all_signals:
            key = self._normalize_title(s.title)
            if key not in unique_signals or s.source_tier < unique_signals[key].source_tier:
                unique_signals[key] = s

        return list(unique_signals.values())

    def _fetch_rss_feed(self, url: str, source_name: str, source_type: str, tier: int) -> List[RawSignal]:
        signals: List[RawSignal] = []
        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return signals

            root = ET.fromstring(resp.content)
            # Find all item tags (RSS) or entry tags (Atom)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items[:25]:
                title = self._get_xml_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
                link = self._get_xml_text(item, ["link", "{http://www.w3.org/2005/Atom}link"])
                if not link:
                    link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                    if link_elem is not None and "href" in link_elem.attrib:
                        link = link_elem.attrib["href"]

                description = self._get_xml_text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])
                pub_date = self._get_xml_text(item, ["pubDate", "published", "{http://www.w3.org/2005/Atom}published"])

                if not title or not link:
                    continue

                clean_desc = self._clean_html(description)
                recency_score = self._compute_recency(pub_date)
                category = self._infer_category(title, clean_desc, source_name)

                # Extract potential enclosure / image
                image_url = None
                enclosure = item.find("enclosure")
                if enclosure is not None and "image" in enclosure.attrib.get("type", ""):
                    image_url = enclosure.attrib.get("url")

                signal = RawSignal(
                    id=self._hash_id(link or title),
                    source_name=source_name,
                    source_type=source_type,
                    title=title.strip(),
                    summary=clean_desc[:300],
                    url=link.strip(),
                    published_at=pub_date or current_iso_time(),
                    source_tier=tier,
                    reliability_score=95.0 if tier == 1 else 85.0 if tier == 2 else 70.0,
                    search_velocity=75.0,
                    news_velocity=80.0,
                    social_velocity=50.0,
                    recency_score=recency_score,
                    category=category,
                    image_url=image_url,
                )
                signals.append(signal)
        except Exception:
            # Resilient: individual feed failure should not interrupt pipeline
            pass
        return signals

    def _fetch_google_trends(self, url: str, source_name: str) -> List[RawSignal]:
        signals: List[RawSignal] = []
        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return signals

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for item in items[:20]:
                title = self._get_xml_text(item, ["title"])
                link = self._get_xml_text(item, ["link"])
                description = self._get_xml_text(item, ["description"])
                approx_traffic = self._get_xml_text(item, ["{https://trends.google.com/trending/rss}approx_traffic"])
                pub_date = self._get_xml_text(item, ["pubDate"])

                if not title:
                    continue

                # Traffic velocity estimation (e.g., "100K+", "50K+", "20K+")
                search_vel = 80.0
                if approx_traffic:
                    digits = re.sub(r"[^\d]", "", approx_traffic)
                    if digits:
                        num = int(digits)
                        if num >= 100:
                            search_vel = 96.0
                        elif num >= 50:
                            search_vel = 90.0
                        elif num >= 20:
                            search_vel = 82.0

                clean_desc = self._clean_html(description)
                category = self._infer_category(title, clean_desc, "Google Trends")

                signal = RawSignal(
                    id=self._hash_id(f"gt_{title}"),
                    source_name=source_name,
                    source_type="google_trends",
                    title=title.strip(),
                    summary=clean_desc[:300] or f"Trending search on Google with {approx_traffic or 'surging'} search interest.",
                    url=link or f"https://www.google.com/search?q={title.replace(' ', '+')}",
                    published_at=pub_date or current_iso_time(),
                    source_tier=1,
                    reliability_score=92.0,
                    search_velocity=search_vel,
                    news_velocity=85.0,
                    social_velocity=75.0,
                    recency_score=95.0,
                    category=category,
                )
                signals.append(signal)
        except Exception:
            pass
        return signals

    def _fetch_social_signals(self) -> List[RawSignal]:
        signals: List[RawSignal] = []
        # Reddit Hot Topics
        reddit_endpoints = [
            ("Reddit Tech", "https://www.reddit.com/r/technology/hot.json?limit=15", "Tech"),
            ("Reddit News", "https://www.reddit.com/r/worldnews/hot.json?limit=15", "World"),
        ]
        for name, url, default_cat in reddit_endpoints:
            try:
                resp = self.client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        d = child.get("data", {})
                        if d.get("stickied"):
                            continue
                        title = d.get("title", "")
                        post_url = d.get("url", "")
                        permalink = f"https://reddit.com{d.get('permalink', '')}"
                        score = d.get("score", 0)
                        num_comments = d.get("num_comments", 0)

                        if not title:
                            continue

                        # Social velocity scaled by upvotes and comment density
                        social_vel = min(98.0, 50.0 + (score / 200.0) + (num_comments / 50.0))

                        signals.append(RawSignal(
                            id=self._hash_id(permalink),
                            source_name=name,
                            source_type="social",
                            title=title.strip(),
                            summary=d.get("selftext", "")[:300] or f"Viral discussion on {name} with {score} points and {num_comments} comments.",
                            url=post_url if post_url.startswith("http") and "reddit.com" not in post_url else permalink,
                            published_at=datetime.fromtimestamp(d.get("created_utc", 0), timezone.utc).isoformat() if d.get("created_utc") else current_iso_time(),
                            source_tier=3,
                            reliability_score=72.0,
                            search_velocity=65.0,
                            news_velocity=70.0,
                            social_velocity=social_vel,
                            recency_score=88.0,
                            category=default_cat,
                            image_url=d.get("thumbnail") if d.get("thumbnail", "").startswith("http") else None,
                        ))
            except Exception:
                pass

        # Hacker News Top Stories
        try:
            hn_resp = self.client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            if hn_resp.status_code == 200:
                top_ids = hn_resp.json()[:15]
                for item_id in top_ids:
                    try:
                        item_resp = self.client.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
                        if item_resp.status_code == 200:
                            d = item_resp.json()
                            title = d.get("title", "")
                            url = d.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
                            score = d.get("score", 0)
                            descendants = d.get("descendants", 0)
                            social_vel = min(95.0, 55.0 + (score / 15.0) + (descendants / 10.0))

                            signals.append(RawSignal(
                                id=self._hash_id(f"hn_{item_id}"),
                                source_name="Hacker News",
                                source_type="social",
                                title=title.strip(),
                                summary=f"Trending technology discussion on Hacker News ({score} points, {descendants} comments).",
                                url=url,
                                published_at=datetime.fromtimestamp(d.get("time", 0), timezone.utc).isoformat() if d.get("time") else current_iso_time(),
                                source_tier=2,
                                reliability_score=85.0,
                                search_velocity=72.0,
                                news_velocity=75.0,
                                social_velocity=social_vel,
                                recency_score=90.0,
                                category="Tech",
                            ))
                    except Exception:
                        pass
        except Exception:
            pass

        return signals

    def _get_xml_text(self, element: ET.Element, tags: List[str]) -> str:
        for tag in tags:
            found = element.find(tag)
            if found is not None and found.text:
                return found.text
        return ""

    def _clean_html(self, html_text: str) -> str:
        if not html_text:
            return ""
        try:
            soup = BeautifulSoup(html_text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return re.sub(r"<[^>]+>", " ", html_text).strip()

    def _compute_recency(self, date_str: str) -> float:
        if not date_str:
            return 80.0
        try:
            # Parse RFC 2822 or ISO
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            now = datetime.now(timezone.utc)
            hours_old = max(0.0, (now - dt.astimezone(timezone.utc)).total_seconds() / 3600.0)
            if hours_old < 2:
                return 98.0
            elif hours_old < 6:
                return 90.0
            elif hours_old < 12:
                return 80.0
            elif hours_old < 24:
                return 65.0
            return 45.0
        except Exception:
            return 80.0

    def _infer_category(self, title: str, summary: str, source_name: str) -> str:
        text = f"{title} {summary} {source_name}".lower()
        if any(w in text for w in ["ai", "apple", "google", "microsoft", "nvidia", "chip", "software", "iphone", "android", "tech", "gadget", "cyber", "robot"]):
            return "Tech"
        if any(w in text for w in ["movie", "trailer", "box office", "actor", "hollywood", "netflix", "music", "album", "gaming", "game", "nintendo", "playstation", "celebrity"]):
            return "Entertainment"
        if any(w in text for w in ["market", "stock", "nasdaq", "fed", "inflation", "economy", "ceo", "revenue", "quarter", "bank", "crypto", "bitcoin"]):
            return "Business"
        if any(w in text for w in ["space", "nasa", "physics", "climate", "mars", "telescope", "biology", "dna"]):
            return "Science"
        if any(w in text for w in ["president", "congress", "senate", "election", "parliament", "vote", "bill", "court", "supreme court"]):
            return "Politics"
        if any(w in text for w in ["nba", "nfl", "premier league", "champions league", "football", "tennis", "formula 1", "olympic"]):
            return "Sports"
        return "Global"

    def _normalize_title(self, title: str) -> str:
        return re.sub(r"[^\w\s]", "", title.lower()).strip()

    def _hash_id(self, val: str) -> str:
        return hashlib.md5(val.encode("utf-8")).hexdigest()[:16]
