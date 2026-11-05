"""
Fixed CTA slide — identical across every video.

Renders a hardcoded 1080×1920 HTML to:
  - PNG  → used as last slide in faceless videos
  - MP4  → appended as last clip in interview animated videos

Content (always the same):
  - Orange #FF6719 full background
  - "The Learning Curve" logo (wordmark)
  - Tagline: "Aprende IA como un ingeniero"
  - Rounded card with Substack page screenshot
  - "Suscríbete gratis" + URL
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

_LOGO       = Path(__file__).parent.parent / "assets" / "logos"       / "tlc_logo.png"
_SCREENSHOT = Path(__file__).parent.parent / "assets" / "substack_screenshot.png"
_CTA_URL    = "iamdgarcia.substack.com"

_HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  width: 1080px;
  height: 1920px;
  overflow: hidden;
  background: #FF6719;
  font-family: 'Inter', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 64px;
  gap: 0;
}}

.eyebrow {{
  font-size: 28px;
  font-weight: 600;
  color: rgba(255,255,255,0.75);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 32px;
}}

.logo {{
  width: 420px;
  object-fit: contain;
  filter: brightness(0) invert(1);
  margin-bottom: 28px;
}}

.tagline {{
  font-size: 38px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  text-align: center;
  line-height: 1.3;
  margin-bottom: 64px;
}}

.screenshot-card {{
  width: 100%;
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.25);
  margin-bottom: 64px;
  position: relative;
}}

.screenshot-card img {{
  width: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
  max-height: 480px;
}}

.screenshot-label {{
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
  color: #fff;
  font-size: 26px;
  font-weight: 600;
  padding: 40px 32px 24px;
}}

.cta-row {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}}

.cta-button {{
  background: #fff;
  color: #FF6719;
  font-size: 48px;
  font-weight: 900;
  padding: 28px 80px;
  border-radius: 100px;
  letter-spacing: -0.5px;
}}

.cta-url {{
  font-size: 32px;
  font-weight: 500;
  color: rgba(255,255,255,0.8);
  letter-spacing: 0.02em;
}}
</style>
</head>
<body>
  <div class="eyebrow">Un concepto de IA por semana</div>

  <img class="logo" src="file://{_LOGO.resolve()}" alt="The Learning Curve">

  <div class="tagline">
    Aprende IA como un ingeniero,<br>no como un gurú de YouTube.
  </div>

  <div class="screenshot-card">
    <img src="file://{_SCREENSHOT.resolve()}" alt="The Learning Curve en Substack">
    <div class="screenshot-label">Newsletter · Podcast · Comunidad</div>
  </div>

  <div class="cta-row">
    <div class="cta-button">Suscríbete gratis →</div>
    <div class="cta-url">{_CTA_URL}</div>
  </div>
</body>
</html>"""


def _render_png(out_path: Path) -> None:
    """Render the CTA HTML to a 1080×1920 PNG."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(_HTML)
        tmp = Path(f.name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1080, "height": 1920})
            page.goto(f"file://{tmp.resolve()}", wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)


def _render_mp4(out_path: Path, duration_s: float = 5.0) -> None:
    """Render the CTA as a static MP4 (PNG held for duration_s, with fade-in)."""
    png = out_path.with_suffix(".png")
    _render_png(png)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(png),
        "-t", str(duration_s),
        "-vf", f"fade=t=in:st=0:d=0.4,scale=1080:1920",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-r", "30", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True, capture_output=True)
    png.unlink(missing_ok=True)
    log.info(f"[CTA] {out_path} ({out_path.stat().st_size // 1024} KB, {duration_s:.1f}s)")


def get_png(cache_dir: Path) -> Path:
    """Return the CTA PNG, rendering only if not cached."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / "cta.png"
    if not out.exists():
        log.info("[CTA] Rendering PNG...")
        _render_png(out)
    return out


def get_mp4(cache_dir: Path, duration_s: float = 5.0) -> Path:
    """Return the CTA MP4 clip, rendering only if not cached."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"cta_{duration_s:.0f}s.mp4"
    if not out.exists():
        log.info("[CTA] Rendering MP4 clip...")
        _render_mp4(out, duration_s)
    return out
