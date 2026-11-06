"""
CTA slide — final slide appended to every video.

Reads all content from BrandConfig (config/faceless_brand.json):
  cta_logo       → logo image at top (optional)
  cta_tagline    → tagline text
  cta_screenshot → screenshot card in the middle (optional)
  cta_button_text / cta_url → CTA button
  accent_color   → background color

If cta_logo or cta_screenshot are empty, those sections are skipped gracefully.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.brand_config import BrandConfig, load as load_brand

log = logging.getLogger(__name__)


def _build_html(brand: BrandConfig) -> str:
    logo_html = ""
    if brand.cta_logo and Path(brand.cta_logo).exists():
        logo_path = Path(brand.cta_logo).resolve()
        logo_html = f'<img class="logo" src="file://{logo_path}" alt="{brand.channel_handle}">'

    screenshot_html = ""
    if brand.cta_screenshot and Path(brand.cta_screenshot).exists():
        ss_path = Path(brand.cta_screenshot).resolve()
        screenshot_html = f"""
  <div class="screenshot-card">
    <img src="file://{ss_path}" alt="{brand.channel_handle}">
  </div>"""

    tagline_html = ""
    if brand.cta_tagline:
        tagline_html = f'<div class="tagline">{brand.cta_tagline}</div>'

    cta_button_html = ""
    if brand.cta_button_text:
        cta_button_html = f'<div class="cta-button">{brand.cta_button_text} →</div>'

    cta_url_html = ""
    if brand.cta_url:
        cta_url_html = f'<div class="cta-url">{brand.cta_url}</div>'

    handle_html = f'<div class="handle">{brand.channel_handle}</div>' if brand.channel_handle else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1080px; height: 1920px;
  background: {brand.accent_color};
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 48px; padding: 80px 64px;
  font-family: 'Inter', sans-serif; color: #fff;
}}
.logo {{ max-width: 480px; max-height: 180px; object-fit: contain; }}
.handle {{ font-size: 36px; font-weight: 700; opacity: 0.85; letter-spacing: 0.02em; }}
.tagline {{
  font-size: 54px; font-weight: 900; text-align: center;
  line-height: 1.15; letter-spacing: -0.5px;
}}
.screenshot-card {{
  width: 100%; border-radius: 28px; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}}
.screenshot-card img {{ width: 100%; display: block; max-height: 500px; object-fit: cover; object-position: top; }}
.cta-button {{
  background: #fff; color: {brand.accent_color};
  font-size: 48px; font-weight: 900;
  padding: 28px 80px; border-radius: 100px;
  letter-spacing: -0.5px;
}}
.cta-url {{ font-size: 32px; font-weight: 500; opacity: 0.8; letter-spacing: 0.02em; }}
</style>
</head>
<body>
  {logo_html}
  {handle_html}
  {tagline_html}
  {screenshot_html}
  {cta_button_html}
  {cta_url_html}
</body>
</html>"""


def _render_png(out_path: Path, brand: BrandConfig) -> None:
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(_build_html(brand))
        tmp = Path(f.name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.goto(f"file://{tmp.resolve()}", wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": 1080, "height": 1920})
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)
    log.info(f"[CTA] PNG rendered: {out_path}")


def _render_mp4(out_path: Path, brand: BrandConfig, duration_s: float = 5.0) -> None:
    png = out_path.with_suffix(".png")
    _render_png(png, brand)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-t", str(duration_s),
        "-vf", "fade=t=in:st=0:d=0.4,scale=1080:1920",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-r", "30", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True, capture_output=True)
    png.unlink(missing_ok=True)
    log.info(f"[CTA] MP4 rendered: {out_path} ({out_path.stat().st_size // 1024} KB, {duration_s:.1f}s)")


def get_png(cache_dir: Path, brand: BrandConfig | None = None) -> Path:
    brand = brand or load_brand()
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / "cta.png"
    if not out.exists():
        _render_png(out, brand)
    return out


def get_mp4(cache_dir: Path, duration_s: float = 5.0, brand: BrandConfig | None = None) -> Path:
    brand = brand or load_brand()
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"cta_{duration_s:.0f}s.mp4"
    if not out.exists():
        _render_mp4(out, brand, duration_s)
    return out
