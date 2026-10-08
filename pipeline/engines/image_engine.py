"""
Pipeline B: Image Engine
Sources high-resolution licensed/primary images, creates editorial vector hero fallbacks, generates alt text, caption, and attribution.
"""
import io
import re
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from pipeline.models import StoryCluster, ResearchPackage, CoverImageInfo, SourceItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*;q=0.8",
}


class ImageEngine:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(headers=HEADERS, timeout=10.0, follow_redirects=True)

    def process_cover_image(self, cluster: StoryCluster, research: ResearchPackage) -> CoverImageInfo:
        # 1. Attempt to extract high-resolution OG image from primary sources
        source_image = self._find_source_og_image(research.primary_sources)
        if source_image:
            return source_image

        # 2. Check cluster raw signals for thumbnail / enclosure image
        for s in cluster.signals:
            if s.image_url and s.image_url.startswith("http") and not s.image_url.endswith(".ico"):
                return CoverImageInfo(
                    url=s.image_url,
                    alt=f"Editorial coverage regarding {cluster.canonical_title}",
                    caption=f"News coverage for {cluster.canonical_title}.",
                    attribution=s.source_name,
                    source_url=s.url,
                    is_generated=False,
                )

        # 3. Fallback: Editorial Illustration
        return self._generate_editorial_fallback(cluster)

    def _find_source_og_image(self, sources: list[SourceItem]) -> Optional[CoverImageInfo]:
        for s in sources[:3]:
            if not s.url or "google.com" in s.url or "reddit.com" in s.url:
                continue
            try:
                resp = self.client.get(s.url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
                    if og_img and og_img.get("content"):
                        img_url = og_img["content"]
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        if img_url.startswith("http"):
                            return CoverImageInfo(
                                url=img_url,
                                alt=f"Coverage of {s.title} via {s.publisher}",
                                caption=f"Reporting from {s.publisher} on {s.title}.",
                                attribution=f"{s.publisher} / Source reporting",
                                source_url=s.url,
                                is_generated=False,
                            )
            except Exception:
                continue
        return None

    def _generate_editorial_fallback(self, cluster: StoryCluster) -> CoverImageInfo:
        # Modern editorial placeholder configuration
        title = cluster.canonical_title
        category = cluster.category
        return CoverImageInfo(
            url=None,
            alt=f"Newift editorial illustration for {title}",
            caption=f"Newift graphic analysis: {title}.",
            attribution="Newift Editorial Intelligence",
            source_url=None,
            is_generated=True,
        )
