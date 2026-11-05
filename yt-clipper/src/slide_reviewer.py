"""
Slide reviewer agent — validates and improves the full visual plan BEFORE rendering.

Runs in at most MAX_ROUNDS batch passes (1 LLM call per pass, all slides at once).
No per-slide calls → stays well under 10 RPM rate limit.

Also provides a post-render pixel sanity check (code-based):
  - frame is not blank
  - card zone (y 580-1190) has non-background pixels
  - title zone has text pixels
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import OpenAI
from PIL import Image

from src.config import settings

log = logging.getLogger(__name__)

MAX_ROUNDS = 2   # 1 review + 1 fix pass at most → max 2 LLM calls total

_SYSTEM = """
Eres un director de arte y revisor de contenido visual para YouTube Shorts técnicos en español.
Recibes TODOS los slides de un Short y los revisas de una vez.

Criterios (aplica a CADA slide):
1. TITLE: máx 3 palabras, ninguna palabra >10 letras. Si supera, abrevia.
   "INTEROPERABILIDAD" → "INTER-OP" | "PORTABILIDAD" → "PORTABLE" | "RESISTENCIA" → "RESISTE"
2. visual_text (cards stat): el dato o afirmación más impactante de esa sección.
   Máx 4 palabras. Debe ser autónomo (entendible sin escuchar el audio).
3. visual_subtitle: máx 5 palabras, complementa visual_text sin repetirlo ni repetir el title.
4. card type coherente con el contenido:
   - comparison  → exactamente 2 productos/empresas enfrentados
   - stat        → dato, conclusión, gancho o CTA (también para intro y veredicto)
   - logo_single → slide centrado en 1 producto/empresa
   NUNCA dejes un slide sin card: si dudas, usa stat.
5. Tab label: máx 2 palabras, máx 10 chars, descriptivo del contenido real.
   Prohibido: "gancho", "punto 1", "punto 2", "punto 3", "cta", "intro".
6. Coherencia: el visual debe transmitir la esencia del fragmento de script de esa sección.

Devuelve JSON (sin markdown):
{
  "slides": [
    {"index": 0, "approved": true, "issues": [], "slide": null},
    {"index": 1, "approved": false, "issues": ["visual_text no es el dato clave"],
     "slide": { /* spec corregida completa: title + card */ }}
  ]
}
Si approved=true → slide=null. Si approved=false → slide DEBE tener la spec completa corregida.
"""

_USER_TMPL = """
Tema del Short: {topic}

Slides a revisar ({n} slides):
{payload_json}

Devuelve el JSON con la revisión de los {n} slides.
"""


def _call(slides: list[dict], tabs: list[str], sections: list[dict], topic: str) -> list[dict]:
    """One LLM call reviewing all slides. Returns list of result dicts."""
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)

    payload = [
        {
            "index": i,
            "tab": tabs[i] if i < len(tabs) else f"s{i}",
            "section_text": (sections[i].get("text", "") if i < len(sections) else "")[:150],
            "slide": slide,
        }
        for i, slide in enumerate(slides)
    ]

    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _USER_TMPL.format(
                topic=topic,
                payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
                n=len(slides),
            )},
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    try:
        return json.loads(raw).get("slides", [])
    except Exception:
        log.warning("[Reviewer] JSON parse failed — skipping this pass")
        return []


def review_plan(plan: dict, sections: list[dict], topic: str) -> dict:
    """
    Review all slides in at most MAX_ROUNDS batch passes.
    Returns the improved plan (mutated in-place).
    """
    tabs   = plan["tabs"]
    slides = plan["slides"]

    for round_n in range(MAX_ROUNDS):
        log.info(f"[Reviewer] pass {round_n + 1}/{MAX_ROUNDS} — {len(slides)} slides")
        results = _call(slides, tabs, sections, topic)
        if not results:
            break

        any_fix = False
        for r in results:
            idx      = r.get("index", -1)
            approved = r.get("approved", True)
            issues   = r.get("issues", [])
            revised  = r.get("slide")

            if not (0 <= idx < len(slides)):
                continue

            title = slides[idx].get("title", "")
            if approved:
                log.info(f"  [{idx}] '{title}' ✓")
            else:
                short_issues = "; ".join(str(x)[:80] for x in issues[:2])
                log.info(f"  [{idx}] '{title}' ✗ — {short_issues}")
                if revised:
                    new_title = revised.get("title", "")
                    new_type  = revised.get("card", {}).get("type", "")
                    log.info(f"       → '{new_title}' [{new_type}]")
                    slides[idx] = revised
                    any_fix = True

        if not any_fix:
            log.info("[Reviewer] all slides approved ✓")
            break

    plan["slides"] = slides
    return plan


# ── Post-render pixel sanity check ────────────────────────────────────────────

_BG_TOL = 15   # channel tolerance vs background


def _is_bg(pixel: tuple, bg: tuple) -> bool:
    return all(abs(int(p) - int(b)) < _BG_TOL for p, b in zip(pixel[:3], bg[:3]))


def validate_frame(png_path: Path, bg_color: tuple = (250, 250, 249)) -> dict:
    """Pixel-level sanity check on a rendered PNG. Returns {ok, issues}."""
    issues: list[str] = []
    try:
        img     = Image.open(png_path).convert("RGB")
        w, h    = img.size
        pixels  = img.load()

        # 1. Frame not completely blank
        if all(_is_bg(pixels[w // 2, y], bg_color) for y in range(0, h, h // 10)):
            issues.append("frame blank")

        # 2. Card zone has non-background pixels
        cy0, cy1 = int(h * 580 / 1920), int(h * 1190 / 1920)
        if all(_is_bg(pixels[w // 2, y], bg_color) for y in range(cy0, cy1, 20)):
            issues.append("card zone empty")

        # 3. Title zone has text pixels
        ty = int(h * 380 / 1920)
        if all(_is_bg(pixels[x, ty], bg_color) for x in range(54, w - 54, 40)):
            issues.append("title zone blank")

    except Exception as e:
        issues.append(f"read error: {e}")

    return {"ok": not issues, "issues": issues}
