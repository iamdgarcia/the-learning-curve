"""
PIL frame generator — 1080×1920 brand-styled frames.

Layout zones (px):
  0   –  70  : top padding
  70  – 130  : top bar  (topic label left · @handle right)
  130 – 170  : gap
  170 – 220  : section tabs row
  220 – 260  : gap
  260 – 530  : section title  (Inter Display Bold, auto-size, single line)
  530 – 580  : gap
  580 – 1190 : center card zone
  1190– 1920 : subtitle zone  (left clear — karaoke subtitles burned by ffmpeg)

Card types (center zone):
  comparison  — two side-by-side branded cards with logos
  stat        — accent-bg rounded card with big visual_text
  logo_single — one centered branded card with logo
  plain       — no card
"""
from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src import logo_agent
from src.brand_config import BrandConfig

log = logging.getLogger(__name__)

W, H = 1080, 1920

# ── Layout ────────────────────────────────────────────────────────────────────
_TOP_Y          = 70
_BAR_SIZE       = 32
_TAB_Y          = 178
_TAB_SIZE       = 28
_TAB_UNDERLINE  = 6
_TITLE_Y        = 264
_TITLE_MAX_PX   = 110
_TITLE_MIN_PX   = 32          # low floor — single long word will still fit
_CARD_TOP       = 568
_CARD_BOT       = 1185
_CARD_MARGIN    = 54
_CARD_RADIUS    = 28
_GRID_ALPHA     = 200
_LOGO_CACHE     = Path("temp/logos")


# ── Font / color helpers ──────────────────────────────────────────────────────

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    p = Path(path)
    return ImageFont.truetype(str(p), size) if p.exists() else ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _th(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ── Logo fetching ─────────────────────────────────────────────────────────────

def _fetch_logo(label: str, icon_color: str = "white") -> Image.Image | None:
    """Delegate to logo_agent which handles LLM slug resolution + caching."""
    return logo_agent.fetch(label, icon_color)


def _place_logo(
    canvas: Image.Image,
    logo: Image.Image,
    cx: int, cy: int,
    max_w: int, max_h: int,
) -> None:
    """Paste logo centered at (cx, cy), scaled to fit max_w×max_h."""
    lw, lh = logo.size
    scale = min(max_w / lw, max_h / lh, 1.0)
    nw, nh = max(1, int(lw * scale)), max(1, int(lh * scale))
    resized = logo.resize((nw, nh), Image.LANCZOS)
    x = cx - nw // 2
    y = cy - nh // 2
    canvas.paste(resized, (x, y), resized)


# ── Grid / top bar / tabs ─────────────────────────────────────────────────────

def _draw_grid(draw: ImageDraw.ImageDraw, brand: BrandConfig) -> None:
    r, g, b = brand.grid_rgb()
    color = (r, g, b, _GRID_ALPHA)
    step  = brand.grid_size
    for x in range(0, W + step, step):
        draw.line([(x, 0), (x, H)], fill=color, width=1)
    for y in range(0, H + step, step):
        draw.line([(0, y), (W, y)], fill=color, width=1)


def _draw_top_bar(
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    topic_label: str,
) -> None:
    acc  = brand.accent_rgb()
    font = _font(brand.font_bold, _BAR_SIZE)
    # handle right-anchored first
    hw   = _tw(draw, brand.channel_handle, font)
    draw.text((W - _CARD_MARGIN - hw, _TOP_Y), brand.channel_handle, font=font, fill=acc)
    # topic label — truncate so it never overlaps handle
    max_w = W - _CARD_MARGIN - hw - 64
    label = topic_label.upper()
    while label and _tw(draw, label, font) > max_w:
        parts = label.rsplit(" ", 1)
        label = parts[0] if len(parts) > 1 else label[:-1]
    if label:
        draw.text((_CARD_MARGIN, _TOP_Y), label, font=font, fill=acc)


def _draw_tabs(
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    labels: list[str],
    active: int,
) -> None:
    acc  = brand.accent_rgb()
    gray = (150, 150, 150)
    font = _font(brand.font_regular, _TAB_SIZE)
    x    = _CARD_MARGIN
    for i, label in enumerate(labels):
        color = acc if i == active else gray
        draw.text((x, _TAB_Y), label, font=font, fill=color)
        tw = _tw(draw, label, font)
        th = _th(draw, label, font)
        if i == active:
            y_ul = _TAB_Y + th + 5
            draw.rectangle([x, y_ul, x + tw, y_ul + _TAB_UNDERLINE], fill=acc)
        x += tw + 32


def _draw_title(
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    title: str,
) -> None:
    """
    Single-line bold title. Auto-shrinks until the longest word fits.
    Never overflows the right edge.
    """
    max_w = W - _CARD_MARGIN * 2
    text  = title.upper()

    # Find a font size where no word is wider than max_w
    size = _TITLE_MAX_PX
    while size >= _TITLE_MIN_PX:
        f = _font(brand.font_bold, size)
        if all(_tw(draw, w, f) <= max_w for w in text.split()):
            break
        size -= 4

    f = _font(brand.font_bold, max(_TITLE_MIN_PX, size))

    # Word-wrap at max_w
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if _tw(draw, test, f) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)

    y = _TITLE_Y
    for line in lines[:3]:   # never more than 3 lines
        draw.text((_CARD_MARGIN, y), line, font=f, fill=brand.text_rgb())
        y += _th(draw, line, f) + 8


# ── Center card renderers ─────────────────────────────────────────────────────

def _card_rect(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
               color: tuple) -> None:
    draw.rounded_rectangle([x0, y0, x1, y1], radius=_CARD_RADIUS, fill=color)


def _draw_stat_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    visual_text: str,
    visual_subtitle: str,
    bg_color: str = "",
) -> None:
    """Accent-colored card with big centered text."""
    if not visual_text:
        return
    bg = _hex(bg_color) if bg_color else brand.accent_rgb()
    x0, y0 = _CARD_MARGIN, _CARD_TOP
    x1, y1 = W - _CARD_MARGIN, _CARD_BOT
    _card_rect(draw, x0, y0, x1, y1, bg)

    ct     = brand.card_text_rgb()
    cw, ch = x1 - x0, y1 - y0

    # visual_text — auto-size to fit
    vt_size = 160
    while vt_size > 48:
        vf = _font(brand.font_bold, vt_size)
        if _tw(draw, visual_text, vf) <= cw - 80:
            break
        vt_size -= 8
    vf   = _font(brand.font_bold, vt_size)
    vf_w = _tw(draw, visual_text, vf)
    vf_h = _th(draw, visual_text, vf)

    sf    = _font(brand.font_regular, 44)
    sf_h  = _th(draw, visual_subtitle, sf) if visual_subtitle else 0
    gap   = 20
    total = vf_h + (gap + sf_h if visual_subtitle else 0)
    vt_y  = y0 + (ch - total) // 2

    draw.text((x0 + (cw - vf_w) // 2, vt_y), visual_text, font=vf, fill=ct)
    if visual_subtitle:
        sf_w = _tw(draw, visual_subtitle, sf)
        draw.text((x0 + (cw - sf_w) // 2, vt_y + vf_h + gap),
                  visual_subtitle, font=sf, fill=ct)


def _draw_comparison_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    items: list[dict],
) -> None:
    """Two branded sub-cards side by side with logos."""
    if not items:
        return
    items = items[:2]   # max 2

    total_w  = W - _CARD_MARGIN * 2
    gap      = 18
    sub_w    = (total_w - gap * (len(items) - 1)) // len(items)
    sub_h    = _CARD_BOT - _CARD_TOP
    font_lbl = _font(brand.font_bold, 48)
    font_sub = _font(brand.font_regular, 32)

    for i, item in enumerate(items):
        x0 = _CARD_MARGIN + i * (sub_w + gap)
        y0 = _CARD_TOP
        x1 = x0 + sub_w
        y1 = _CARD_BOT
        bg = _hex(item.get("bg_color", "#1A1A1A"))
        tc = _hex(item.get("text_color", "#FFFFFF"))
        _card_rect(draw, x0, y0, x1, y1, bg)

        cx = x0 + sub_w // 2
        # Logo zone: upper 55% of card
        logo_zone_h = int(sub_h * 0.55)
        logo_cy     = y0 + logo_zone_h // 2

        icon_color = "white" if item.get("text_color", "#FFFFFF").upper() in ("#FFF", "#FFFFFF") else "black"
        logo = _fetch_logo(item.get("label", item.get("domain", "")), icon_color)
        if logo:
            _place_logo(canvas, logo, cx, logo_cy,
                        max_w=sub_w - 40, max_h=logo_zone_h - 40)
        else:
            # Fallback: brand initial in large text
            initial = item.get("label", "?")[0].upper()
            if_size = 120
            if_font = _font(brand.font_bold, if_size)
            draw.text((cx - _tw(draw, initial, if_font) // 2,
                       logo_cy - _th(draw, initial, if_font) // 2),
                      initial, font=if_font, fill=tc)

        # Label zone: lower 40%
        lbl_y = y0 + logo_zone_h + 16
        label = item.get("label", "")
        lw    = _tw(draw, label, font_lbl)
        draw.text((cx - lw // 2, lbl_y), label, font=font_lbl, fill=tc)

        subtitle = item.get("subtitle", "")
        if subtitle:
            sw = _tw(draw, subtitle, font_sub)
            draw.text((cx - sw // 2, lbl_y + _th(draw, label, font_lbl) + 8),
                      subtitle, font=font_sub, fill=tc)


def _draw_logo_single_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    item: dict,
) -> None:
    """One full-width branded card with centered logo."""
    x0, y0 = _CARD_MARGIN, _CARD_TOP
    x1, y1 = W - _CARD_MARGIN, _CARD_BOT
    bg = _hex(item.get("bg_color", "#1A1A1A"))
    tc = _hex(item.get("text_color", "#FFFFFF"))
    _card_rect(draw, x0, y0, x1, y1, bg)

    cw, ch = x1 - x0, y1 - y0
    cx      = x0 + cw // 2
    font_lbl = _font(brand.font_bold, 64)

    icon_color = "white" if item.get("text_color", "#FFFFFF").upper() in ("#FFF", "#FFFFFF") else "black"
    logo = _fetch_logo(item.get("label", item.get("domain", "")), icon_color)
    if logo:
        logo_cy = y0 + int(ch * 0.42)
        _place_logo(canvas, logo, cx, logo_cy, max_w=cw - 80, max_h=int(ch * 0.55))
        label = item.get("label", "")
        lbl_y = y0 + int(ch * 0.72)
        draw.text((cx - _tw(draw, label, font_lbl) // 2, lbl_y),
                  label, font=font_lbl, fill=tc)
    else:
        label = item.get("label", "?")
        draw.text((cx - _tw(draw, label, font_lbl) // 2,
                   y0 + (ch - _th(draw, label, font_lbl)) // 2),
                  label, font=font_lbl, fill=tc)


def _draw_center_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    brand: BrandConfig,
    card: dict,
) -> None:
    """Dispatch to the right card renderer based on card['type']."""
    t = card.get("type", "stat")
    if t == "stat" or t == "plain":   # plain is a fallback to stat
        vt = card.get("visual_text") or card.get("title", "")
        _draw_stat_card(canvas, draw, brand,
                        vt,
                        card.get("visual_subtitle", ""),
                        card.get("bg_color", ""))
    elif t == "comparison":
        _draw_comparison_card(canvas, draw, brand, card.get("items", []))
    elif t == "logo_single":
        _draw_logo_single_card(canvas, draw, brand, card)


# ── Public API ────────────────────────────────────────────────────────────────

def make_frame(
    brand: BrandConfig,
    topic_label: str,
    section_title: str,
    section_tabs: list[str],
    active_tab: int,
    card: dict | None = None,
) -> Image.Image:
    img  = Image.new("RGBA", (W, H), brand.bg_rgb() + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    _draw_grid(draw, brand)
    _draw_top_bar(draw, brand, topic_label)
    _draw_tabs(draw, brand, section_tabs, active_tab)
    _draw_title(draw, brand, section_title)
    if card:
        _draw_center_card(img, draw, brand, card)

    return img


def save_section_frames(
    brand: BrandConfig,
    topic_label: str,
    tabs: list[str],
    slides: list[dict],    # [{title, card}] from visual_planner
    out_dir: Path,
) -> list[Path]:
    """Generate one PNG per slide. Returns paths in order."""
    paths: list[Path] = []
    for i, slide in enumerate(slides):
        img  = make_frame(brand, topic_label, slide.get("title", ""),
                          tabs, active_tab=i, card=slide.get("card"))
        dest = out_dir / f"section_{i:02d}.png"
        img.convert("RGB").save(str(dest), "PNG")
        card_t = slide.get("card", {}).get("type", "plain")
        log.info(f"[Frame] {i}: '{slide.get('title','')}' [{card_t}] → {dest.name}")
        paths.append(dest)
    return paths
