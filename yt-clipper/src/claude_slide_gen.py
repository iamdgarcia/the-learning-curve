"""
Claude CLI → HTML → Playwright PNG slide generator.

For each slide spec the visual planner produced, we:
  1. Build a detailed design prompt (brand + slide content)
  2. Call `claude --print` (Claude on Vertex, no SDK needed)
  3. Playwright screenshots the HTML at 1080×1920 → PNG

Quality is far superior to PIL because Claude produces real CSS:
gradients, shadows, perfect typography, flex layout, brand colors.

Logo SVGs are inlined directly in the prompt so Claude can embed them.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.brand_config import BrandConfig
from src import logo_agent

log = logging.getLogger(__name__)

_CLAUDE_BIN = Path.home() / ".local/bin/claude"
_CLAUDE_TIMEOUT = 150   # seconds per slide (comparison cards take longer)


# ── Prompt builder ────────────────────────────────────────────────────────────

def _svg_for(label: str, text_color: str) -> str:
    """Return inline SVG string for a brand logo, or empty string."""
    color = "white" if text_color.upper() in ("#FFF", "#FFFFFF") else "black"
    img = logo_agent.fetch(label, color)
    if img is None:
        return ""
    # Convert PIL RGBA image → PNG bytes → base64 data URI
    import base64
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{b64}" style="max-width:140px;max-height:140px;object-fit:contain;">'


def _card_html(card: dict, brand: BrandConfig) -> str:
    """Return the inner HTML for the center card section."""
    t = card.get("type", "stat")

    if t == "comparison":
        items = card.get("items", [])[:2]
        parts = []
        for item in items:
            label    = item.get("label", "")
            bg       = item.get("bg_color", "#1A1A1A")
            tc       = item.get("text_color", "#FFFFFF")
            subtitle = item.get("subtitle", "")
            logo_tag = _svg_for(label, tc)
            parts.append(f"""
            <div style="flex:1;background:{bg};border-radius:24px;display:flex;
                        flex-direction:column;align-items:center;justify-content:center;
                        padding:32px 20px;gap:18px;min-height:480px;
                        box-shadow:0 8px 32px rgba(0,0,0,0.18);
                        background:linear-gradient(145deg,{bg},{bg}dd);">
              {logo_tag}
              <div style="color:{tc};font-size:58px;font-weight:900;text-align:center;
                          line-height:1.1;letter-spacing:-1px;">{label}</div>
              {'<div style="color:'+tc+'99;font-size:30px;font-weight:500;">'+subtitle+'</div>' if subtitle else ''}
            </div>""")
        return f"""
        <div style="display:flex;gap:18px;width:100%;padding:0 54px;box-sizing:border-box;">
          {''.join(parts)}
        </div>"""

    if t == "logo_single":
        label    = card.get("label", "")
        bg       = card.get("bg_color", "#1A1A1A")
        tc       = card.get("text_color", "#FFFFFF")
        subtitle = card.get("subtitle", "")
        logo_tag = _svg_for(label, tc)
        return f"""
        <div style="width:calc(100% - 108px);margin:0 54px;background:{bg};border-radius:24px;
                    display:flex;flex-direction:column;align-items:center;justify-content:center;
                    padding:48px 32px;gap:24px;min-height:500px;box-sizing:border-box;">
          {logo_tag}
          <div style="color:{tc};font-size:72px;font-weight:900;text-align:center;">{label}</div>
          {'<div style="color:'+tc+'99;font-size:34px;">'+subtitle+'</div>' if subtitle else ''}
        </div>"""

    # stat (default)
    vt  = card.get("visual_text", "")
    vs  = card.get("visual_subtitle", "")
    bg  = card.get("bg_color", "") or brand.accent_color
    tc  = "#FFFFFF"
    fs  = max(64, 160 - max(0, len(vt) - 8) * 8)
    return f"""
    <div style="width:calc(100% - 108px);margin:0 54px;border-radius:24px;
                display:flex;flex-direction:column;align-items:center;justify-content:center;
                padding:48px 40px;gap:20px;min-height:500px;box-sizing:border-box;
                background:linear-gradient(145deg,{bg},{bg}cc);
                box-shadow:0 12px 40px rgba(0,0,0,0.15);">
      <div style="color:{tc};font-size:{fs}px;font-weight:900;text-align:center;
                  line-height:1.0;letter-spacing:-2px;">{vt}</div>
      {'<div style="color:'+tc+'cc;font-size:38px;font-weight:500;text-align:center;">'+vs+'</div>' if vs else ''}
    </div>"""


def _build_prompt(
    brand: BrandConfig,
    tabs: list[str],
    active_tab: int,
    slide: dict,
    topic_label: str,
) -> str:
    title    = slide.get("title", "")
    card     = slide.get("card", {})
    card_html = _card_html(card, brand)

    tab_items = []
    for i, tab in enumerate(tabs):
        if i == active_tab:
            tab_items.append(
                f'<span style="color:{brand.accent_color};font-weight:700;'
                f'border-bottom:5px solid {brand.accent_color};padding-bottom:4px;">{tab}</span>'
            )
        else:
            tab_items.append(
                f'<span style="color:#999;font-weight:500;">{tab}</span>'
            )

    tab_row = "".join(f'<div style="white-space:nowrap;">{t}</div>' for t in tab_items)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{
  width:1080px;height:1920px;overflow:hidden;
  background:{brand.bg_color};
  font-family:'Inter',sans-serif;
  position:relative;
}}
.grid-bg{{
  position:absolute;inset:0;
  background-image:
    linear-gradient({brand.grid_color} 1px,transparent 1px),
    linear-gradient(90deg,{brand.grid_color} 1px,transparent 1px);
  background-size:{brand.grid_size}px {brand.grid_size}px;
  pointer-events:none;
}}
.content{{position:relative;z-index:1;display:flex;flex-direction:column;height:100%;}}
.topbar{{
  display:flex;justify-content:space-between;align-items:center;
  padding:56px 54px 0;
}}
.niche{{color:{brand.accent_color};font-size:30px;font-weight:700;letter-spacing:0.5px;}}
.handle{{color:{brand.accent_color};font-size:30px;font-weight:700;}}
.tabs{{
  display:flex;gap:28px;padding:28px 54px 0;
  font-size:26px;
}}
.title{{
  padding:36px 54px 0;
  font-size:108px;font-weight:900;
  color:{brand.text_color};
  line-height:1.0;letter-spacing:-2px;
}}
.card-zone{{
  flex:1;display:flex;align-items:center;justify-content:center;
  padding:32px 0;
  max-height:680px;
}}
.subtitle-zone{{height:580px;flex-shrink:0;}}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="content">
  <div class="topbar">
    <div class="niche">{topic_label}</div>
    <div class="handle">{brand.channel_handle}</div>
  </div>
  <div class="tabs">{tab_row}</div>
  <div class="title">{title}</div>
  <div class="card-zone">{card_html}</div>
  <div class="subtitle-zone"></div>
</div>
</body>
</html>"""


# ── Claude CLI call ───────────────────────────────────────────────────────────

def _claude_polish(html: str, slide: dict) -> str:
    """
    Ask Claude to improve the generated HTML visually.
    Returns improved HTML or the original if Claude fails/times out.
    """
    prompt = f"""You are a UI designer. Improve this YouTube Short slide HTML (1080x1920px) visually.

Current HTML:
{html}

Slide content: title="{slide.get('title','')}", card type={slide.get('card',{}).get('type','stat')}

Rules:
- Keep EXACT same structure (topbar, tabs, title, card-zone, subtitle-zone)
- subtitle-zone MUST stay empty (580px at bottom) — karaoke subtitles added by ffmpeg
- Improve: card visual impact, typography, spacing, shadows, gradients on cards
- Cards should feel bold and premium (box-shadow, slight gradient overlay is fine)
- Keep all colors, font choices, and layout positions
- Output ONLY the complete improved HTML. No markdown. No explanation."""

    try:
        result = subprocess.run(
            [str(_CLAUDE_BIN), "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=_CLAUDE_TIMEOUT,
        )
        out = result.stdout.strip()
        if out.startswith("```"):
            out = out.split("```")[1]
            if out.startswith("html"):
                out = out[4:]
            out = out.rsplit("```", 1)[0].strip()
        if "<!DOCTYPE" in out or "<html" in out:
            return out
    except subprocess.TimeoutExpired:
        log.warning(f"[Claude] timeout on '{slide.get('title','')}' — using base HTML")
    except Exception as e:
        log.warning(f"[Claude] error: {e}")
    return html


# ── Playwright renderer ───────────────────────────────────────────────────────

def _render_html(html: str, out_path: Path, playwright_ctx) -> None:
    """Screenshot HTML at 1080×1920 → PNG."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html)
        tmp = Path(f.name)
    page = playwright_ctx.new_page()
    page.set_viewport_size({"width": 1080, "height": 1920})
    page.goto(f"file://{tmp}", wait_until="networkidle", timeout=15000)
    page.screenshot(path=str(out_path), full_page=False)
    page.close()
    tmp.unlink(missing_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_frames(
    brand: BrandConfig,
    topic_label: str,
    tabs: list[str],
    slides: list[dict],
    out_dir: Path,
) -> list[Path]:
    """
    Generate one PNG per slide using Claude HTML + Playwright.
    Returns list of PNG paths in slide order.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        for i, slide in enumerate(slides):
            log.info(f"[Slide {i}] '{slide.get('title','')}' [{slide.get('card',{}).get('type','?')}]")

            # 1. Generate base HTML (deterministic, no LLM, fast)
            base_html = _build_prompt(brand, tabs, i, slide, topic_label)

            # 2. Claude polishes it (better gradients, shadows, visual impact)
            html = _claude_polish(base_html, slide)

            # 3. Playwright → PNG
            out_path = out_dir / f"section_{i:02d}.png"
            _render_html(html, out_path, browser)

            # Save HTML alongside PNG for debugging
            (out_dir / f"section_{i:02d}.html").write_text(html)

            log.info(f"  → {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            paths.append(out_path)

        browser.close()

    return paths
