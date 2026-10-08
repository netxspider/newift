"""
Pipeline B: Image Engine
Sources high-resolution licensed/primary images, creates editorial vector hero fallbacks,
generates alt text, caption, and attribution. Guaranteed to provide valid image data.
"""
import io
import os
import re
import textwrap
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from pipeline.models import StoryCluster, ResearchPackage, CoverImageInfo, SourceItem

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*;q=0.8",
}


def render_editorial_banner(headline: str, category: str = "General", dek: str = "") -> bytes:
    """
    Renders a premium 1200x675 (16:9) editorial briefing banner with high-contrast typography,
    category badges, ambient lighting, and Newift brand identity.
    """
    W, H = 1200, 675
    cat_lower = category.lower()

    if any(k in cat_lower for k in ["tech", "ai", "cyber", "gadget", "software"]):
        top_color, bot_color, accent_color = (10, 15, 29), (23, 37, 84), (99, 102, 241)
    elif any(k in cat_lower for k in ["business", "finance", "market", "econ", "trade"]):
        top_color, bot_color, accent_color = (9, 13, 22), (6, 78, 59), (16, 185, 129)
    elif any(k in cat_lower for k in ["politic", "gov", "world", "us", "policy", "law"]):
        top_color, bot_color, accent_color = (11, 15, 25), (49, 46, 129), (245, 158, 11)
    elif any(k in cat_lower for k in ["entertain", "media", "celebrity", "film", "music"]):
        top_color, bot_color, accent_color = (15, 10, 28), (46, 16, 101), (236, 72, 153)
    elif any(k in cat_lower for k in ["sport", "game", "match", "cup"]):
        top_color, bot_color, accent_color = (11, 17, 32), (30, 41, 59), (249, 115, 22)
    elif any(k in cat_lower for k in ["science", "health", "climate", "space"]):
        top_color, bot_color, accent_color = (8, 23, 38), (17, 94, 89), (20, 184, 166)
    else:
        top_color, bot_color, accent_color = (11, 15, 26), (26, 33, 61), (129, 140, 248)

    img = Image.new("RGB", (W, H), color=top_color)
    draw = ImageDraw.Draw(img)

    # Smooth vertical dark gradient
    for y in range(H):
        ratio = y / H
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Ambient radial rings for subtle editorial depth
    for rad in range(400, 0, -30):
        draw.ellipse(
            [W - 200 - rad, 120 - rad, W - 200 + rad, 120 + rad],
            outline=(accent_color[0] // 3, accent_color[1] // 3, accent_color[2] // 3),
        )

    font_bold_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_reg_candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    def load_font(candidates: List[str], size: int) -> ImageFont.ImageFont:
        for c in candidates:
            if os.path.exists(c):
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    badge_font = load_font(font_bold_candidates, 20)
    title_font = load_font(font_bold_candidates, 44)
    sub_font = load_font(font_reg_candidates, 22)
    brand_font = load_font(font_bold_candidates, 22)
    seal_font = load_font(font_bold_candidates, 18)

    # Category badge
    pill_text = f"  {category.upper()}  "
    draw.rounded_rectangle(
        [80, 65, 80 + len(pill_text) * 15, 110],
        radius=6,
        fill=(15, 23, 42),
        outline=accent_color,
        width=2,
    )
    draw.text((95, 75), pill_text.strip(), font=badge_font, fill=accent_color)

    # Wrap title
    lines = textwrap.wrap(headline, width=38)
    curr_y = 155
    for line in lines[:4]:
        # Drop shadow
        draw.text((82, curr_y + 2), line, font=title_font, fill=(0, 0, 0))
        draw.text((80, curr_y), line, font=title_font, fill=(248, 250, 252))
        curr_y += 58

    # Dek / Subtitle if space permits
    if dek and curr_y < H - 180:
        dek_lines = textwrap.wrap(dek, width=65)
        for d_line in dek_lines[:2]:
            draw.text((80, curr_y + 12), d_line, font=sub_font, fill=(148, 163, 184))
            curr_y += 32

    # Bottom rule
    draw.line([(80, H - 95), (W - 80, H - 95)], fill=(51, 65, 85), width=2)

    # Brand + Verification
    draw.text((80, H - 72), "NEWIFT", font=brand_font, fill=(255, 255, 255))
    draw.text((185, H - 70), "EDITORIAL INTELLIGENCE", font=sub_font, fill=(148, 163, 184))
    draw.text((W - 280, H - 70), "✓ VERIFIED REPORT", font=seal_font, fill=(52, 211, 153))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


class ImageEngine:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(headers=HEADERS, timeout=12.0, follow_redirects=True)

    def process_cover_image(
        self,
        cluster: StoryCluster,
        research: ResearchPackage,
        headline: Optional[str] = None,
        dek: Optional[str] = None,
    ) -> CoverImageInfo:
        """
        Slices primary web images or generates a custom 1200x675 editorial graphic.
        GUARANTEES that a valid image (URL or binary image_bytes) is returned.
        """
        display_title = headline or cluster.canonical_title
        summary = dek or cluster.canonical_summary

        # 1. Attempt to extract high-resolution OG image from primary sources
        source_image = self._find_source_og_image(research.primary_sources, display_title)
        if source_image and (source_image.image_bytes or source_image.url):
            return source_image

        # 2. Check cluster raw signals for thumbnail / enclosure image
        for s in cluster.signals:
            if s.image_url and s.image_url.startswith("http") and not s.image_url.endswith(".ico"):
                try:
                    resp = self.client.get(s.image_url)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        content_type = resp.headers.get("content-type", "image/jpeg")
                        return CoverImageInfo(
                            url=s.image_url,
                            image_bytes=resp.content,
                            mime_type=content_type,
                            alt=f"Editorial coverage regarding {display_title}",
                            caption=f"News coverage for {display_title}.",
                            attribution=s.source_name,
                            source_url=s.url,
                            is_generated=False,
                        )
                except Exception:
                    continue

        # 3. Fallback: Guaranteed High-Res Editorial Graphic
        banner_bytes = render_editorial_banner(
            headline=display_title,
            category=cluster.category,
            dek=summary,
        )

        return CoverImageInfo(
            url=None,
            image_bytes=banner_bytes,
            mime_type="image/jpeg",
            alt=f"Newift visual briefing: {display_title}",
            caption=f"Newift news analysis: {display_title}.",
            attribution="Newift Editorial Studio",
            source_url=None,
            is_generated=True,
        )

    def _find_source_og_image(
        self, sources: list[SourceItem], display_title: str
    ) -> Optional[CoverImageInfo]:
        for s in sources[:4]:
            if not s.url or "google.com" in s.url or "reddit.com" in s.url:
                continue
            try:
                resp = self.client.get(s.url, timeout=4.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_img = soup.find("meta", property="og:image") or soup.find(
                        "meta", attrs={"name": "og:image"}
                    )
                    if og_img and og_img.get("content"):
                        img_url = og_img["content"]
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        if img_url.startswith("http"):
                            # Validate and fetch bytes
                            img_resp = self.client.get(img_url, timeout=5.0)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                ctype = img_resp.headers.get("content-type", "image/jpeg")
                                return CoverImageInfo(
                                    url=img_url,
                                    image_bytes=img_resp.content,
                                    mime_type=ctype,
                                    alt=f"Coverage of {display_title} via {s.publisher}",
                                    caption=f"Reporting from {s.publisher} on {display_title}.",
                                    attribution=f"{s.publisher} / Source reporting",
                                    source_url=s.url,
                                    is_generated=False,
                                )
            except Exception:
                continue
        return None
