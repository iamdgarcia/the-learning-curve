"""
Slide Agent — Claude Code writes HTML files autonomously, Playwright renders them.

Architecture:
  For each slide, we send Claude a complete design brief via stdin.
  Claude uses its Write tool to output the HTML file directly to disk.
  Playwright then screenshots each HTML → PNG at 1080×1920.

No Python HTML scaffold. Claude owns the design from scratch.
"""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.brand_assets import inject_logo
from src.brand_config import BrandConfig
from src import logo_agent

log = logging.getLogger(__name__)

_CLAUDE = Path.home() / ".local/bin/claude"
_TIMEOUT = 160   # seconds per slide


# ── Logo embedding ────────────────────────────────────────────────────────────

def _logo_b64(label: str, on_dark: bool = True) -> str:
    """Return a base64 data-URI PNG for the brand logo, or empty string."""
    import base64
    from io import BytesIO
    color = "white" if on_dark else "black"
    img = logo_agent.fetch(label, color)
    if img is None:
        return ""
    buf = BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── Brief builder ─────────────────────────────────────────────────────────────

_BRAND_GUIDE = """
BRAND GUIDE:
  Background: #FAFAF9 (warm white)
  Grid: 54px CSS grid with #E8E4DC 1px lines — subtle, not distracting
  Accent color: #FF6719 (Substack orange)
  Text: #1C1B1F (near black)
  Font: Inter from Google Fonts (weights 400, 600, 700, 800, 900)
  Handle: @TheLearningCurveAI

LAYOUT ZONES (pixel-exact, 1080×1920):
  y=0   – 100 : TOP BAR — niche label bold orange LEFT, @handle bold orange RIGHT
  y=100 – 170 : TABS ROW — small text, gray inactive, orange+underline active tab
  y=170 – 460 : TITLE — Inter Black 900, left-aligned, very large (fits in 3 lines max)
  y=460 – 1350: CARD ZONE — the main visual (see card types below)
  y=1350– 1920: ⚠️  COMPLETELY EMPTY — ffmpeg burns karaoke subtitles here. NOTHING here.

AESTHETIC REFERENCE (@underthehoodai):
  - Cards dominate the slide — they should feel substantial and premium
  - Layered box-shadows: 0 20px 60px rgba(0,0,0,0.25), 0 4px 16px rgba(0,0,0,0.12)
  - Rounded corners: 24-32px
  - For comparison cards: each card ~480px tall, separated by a floating "vs" badge
  - For stat cards: full-width, centered content, large gradient background
  - Subtle decorative elements inside cards are encouraged (faded large number, diagonal stripe, noise)
  - NO content below y=1350 — not even a pixel
"""

_CARD_TYPES = {
    "stat": """
CARD TYPE: STAT (full-width accent card)
  - Full width (54px margin each side), ~700px tall, border-radius 28px
  - Background: gradient of the accent color (or bg_color if provided)
  - Main text: VISUAL_TEXT in white, Inter Black 900, very large (auto-size: longer text = smaller font)
  - Sub text: VISUAL_SUBTITLE in white 70% opacity, medium weight, below main text
  - Decorative: optional faded large version of key word in background
  - Box-shadow layered and dramatic
""",
    "comparison": """
CARD TYPE: COMPARISON (two side-by-side product cards)
  - Two cards with 16px gap between them, each ~480px tall, border-radius 28px
  - Left card: bg ITEM0_BG, text ITEM0_LABEL (white, large, bold), subtitle ITEM0_SUBTITLE
  - Right card: bg ITEM1_BG, text ITEM1_LABEL (white, large, bold), subtitle ITEM1_SUBTITLE
  - Floating "vs" badge centered between cards (white circle, gray text)
  - Each card can have: logo image (base64 PNG if provided), gradient, inner shadow, accent strip at top
  - Logos sized max 100×100px, centered in upper portion
  - Include the VISUAL_TEXT as a stat/number in each card if provided (e.g. "72%" under the label)
  - Dramatic shadows, feel premium not flat
""",
    "logo_single": """
CARD TYPE: LOGO SINGLE (one brand card, full width)
  - Full width (54px margin), ~600px tall, border-radius 28px
  - Background: brand color (ITEM0_BG)
  - Logo image (base64 PNG if provided) centered in upper 50%
  - Brand name below logo, white, Inter Black 900, large
  - Subtitle if provided, smaller, white 70%
  - Dramatic shadows, feel premium
""",
}


def _make_brief(
    brand: BrandConfig,
    topic_label: str,
    tabs: list[str],
    active_tab: int,
    slide: dict,
    html_path: Path,
) -> str:
    card = slide.get("card", {})
    ctype = card.get("type", "stat")
    items = card.get("items", [])
    vt = card.get("visual_text", slide.get("title", ""))
    vs = card.get("visual_subtitle", "")

    # Build logo data URIs for comparison/logo cards
    logo_lines = []
    for i, item in enumerate(items[:2]):
        label = item.get("label", "")
        on_dark = item.get("text_color", "#FFFFFF").upper() in ("#FFF", "#FFFFFF", "#FFFFFF")
        b64 = _logo_b64(label, on_dark)
        if b64:
            logo_lines.append(f"  ITEM{i}_LOGO_B64: {b64[:80]}... (full base64 PNG, use as img src)")

    # Substitute card template variables
    card_desc = _CARD_TYPES.get(ctype, _CARD_TYPES["stat"])
    card_desc = card_desc.replace("VISUAL_TEXT", vt or slide.get("title", ""))
    card_desc = card_desc.replace("VISUAL_SUBTITLE", vs)
    for i, item in enumerate(items[:2]):
        card_desc = card_desc.replace(f"ITEM{i}_LABEL", item.get("label", ""))
        card_desc = card_desc.replace(f"ITEM{i}_BG", item.get("bg_color", "#1A1A1A"))
        card_desc = card_desc.replace(f"ITEM{i}_SUBTITLE", item.get("subtitle", item.get("label", "")))

    tab_html = " | ".join(
        f"[{t}]" if i == active_tab else t
        for i, t in enumerate(tabs)
    )

    logo_section = "\n".join(logo_lines) if logo_lines else "  (no logos available)"

    return f"""You are a world-class UI designer creating YouTube Shorts slides.

{_BRAND_GUIDE}

SLIDE CONTENT:
  Topic label (top bar): {topic_label}
  Tabs (active in brackets): {tab_html}
  Title: {slide.get('title', '')}
  {card_desc}

LOGO ASSETS (use as <img> src if relevant):
{logo_section}

OUTPUT:
Write a complete, self-contained 1080×1920px HTML file to:
  {html_path}

Requirements:
  1. Load Inter from Google Fonts
  2. body: width=1080px, height=1920px, overflow=hidden
  3. CSS grid background (54px, color #E8E4DC, 1px lines)
  4. Exact layout zones as specified
  5. y=1350 to y=1920: ABSOLUTELY NOTHING — not a pixel, not a shadow, not padding
  6. Make it look PREMIUM. This is the quality bar: think Stripe product cards, Linear.app aesthetics, Vercel marketing
  7. If logo b64 is provided, embed it as <img src="data:image/png;base64,...">

Write the HTML file now.
"""


# ── Claude agent call ─────────────────────────────────────────────────────────

def _run_claude(brief: str, html_path: Path) -> bool:
    """Ask Claude to write the HTML file. Returns True if file was created."""
    try:
        result = subprocess.run(
            [str(_CLAUDE), "--print", "--allowedTools", "Write"],
            input=brief,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        if html_path.exists() and html_path.stat().st_size > 1000:
            return True
        # Claude might have output the HTML as text instead of using Write tool
        out = result.stdout.strip()
        if "<!DOCTYPE" in out or "<html" in out:
            html = out
            if html.startswith("```"):
                html = html.split("```")[1].lstrip("html").strip()
                html = html.rsplit("```", 1)[0].strip()
            html_path.write_text(html)
            return html_path.stat().st_size > 1000
        return False
    except subprocess.TimeoutExpired:
        log.warning(f"[SlideAgent] timeout — {html_path.name}")
        return False
    except Exception as e:
        log.warning(f"[SlideAgent] error: {e}")
        return False


# ── Playwright render ─────────────────────────────────────────────────────────

def _render(html_path: Path, png_path: Path, browser) -> None:
    page = browser.new_page()
    page.set_viewport_size({"width": 1080, "height": 1920})
    page.goto(f"file://{html_path.resolve()}", wait_until="networkidle", timeout=20000)
    inject_logo(page)
    page.screenshot(path=str(png_path), full_page=False)
    page.close()


# ── Fallback HTML ─────────────────────────────────────────────────────────────

def _fallback_html(brand: BrandConfig, slide: dict, topic_label: str,
                   tabs: list[str], active_tab: int) -> str:
    """Minimal but clean slide when Claude fails."""
    card = slide.get("card", {})
    vt = card.get("visual_text", slide.get("title", ""))
    vs = card.get("visual_subtitle", "")
    tab_items = "".join(
        f'<span style="color:{brand.accent_color};font-weight:700;border-bottom:4px solid {brand.accent_color};padding-bottom:3px;">{t}</span>'
        if i == active_tab else
        f'<span style="color:#999;">{t}</span>'
        for i, t in enumerate(tabs)
    )
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;overflow:hidden;background:{brand.bg_color};font-family:Inter,sans-serif;
  background-image:linear-gradient({brand.grid_color} 1px,transparent 1px),linear-gradient(90deg,{brand.grid_color} 1px,transparent 1px);
  background-size:54px 54px;}}
</style></head><body>
<div style="padding:56px 54px 0;display:flex;justify-content:space-between;">
  <span style="color:{brand.accent_color};font-weight:700;font-size:28px;">{topic_label}</span>
  <span style="color:{brand.accent_color};font-weight:700;font-size:28px;">{brand.channel_handle}</span>
</div>
<div style="padding:24px 54px 0;display:flex;gap:28px;font-size:24px;">{tab_items}</div>
<div style="padding:32px 54px 0;font-size:104px;font-weight:900;color:{brand.text_color};line-height:1;">{slide.get('title','')}</div>
<div style="margin:32px 54px 0;background:{brand.accent_color};border-radius:28px;padding:60px 48px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:580px;
  box-shadow:0 20px 60px rgba(255,103,25,0.35);">
  <div style="color:#fff;font-size:120px;font-weight:900;text-align:center;line-height:1;">{vt}</div>
  {'<div style="color:#ffffffcc;font-size:40px;margin-top:16px;text-align:center;">'+vs+'</div>' if vs else ''}
</div>
</body></html>"""


# ── Public API ────────────────────────────────────────────────────────────────

def generate_frames(
    brand: BrandConfig,
    topic_label: str,
    tabs: list[str],
    slides: list[dict],
    out_dir: Path,
) -> list[Path]:
    """
    Generate one PNG per slide. Claude writes the HTML, Playwright renders.
    Falls back to a clean minimal HTML if Claude fails/times out.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    png_paths: list[Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        for i, slide in enumerate(slides):
            title = slide.get("title", "")
            ctype = slide.get("card", {}).get("type", "stat")
            log.info(f"[SlideAgent {i}] '{title}' [{ctype}]")

            html_path = out_dir / f"section_{i:02d}.html"
            png_path  = out_dir / f"section_{i:02d}.png"

            brief = _make_brief(brand, topic_label, tabs, i, slide, html_path)

            ok = _run_claude(brief, html_path)
            if not ok:
                log.warning(f"  Claude failed — using fallback")
                html_path.write_text(
                    _fallback_html(brand, slide, topic_label, tabs, i)
                )

            _render(html_path, png_path, browser)
            size_kb = png_path.stat().st_size // 1024
            log.info(f"  → {png_path.name} ({size_kb} KB)")
            png_paths.append(png_path)

        browser.close()

    return png_paths
