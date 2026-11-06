"""
Visual orchestration agent — runs BEFORE the frame generator.

Given the topic + script sections it decides:
  - Meaningful tab labels (no "gancho / punto 1 / cta")
  - Card type per slide: comparison | stat | logo_single | plain
  - Logo domains (Clearbit) + brand bg_color per item

Card specs
----------
comparison  : two side-by-side branded cards with logos
              items: [{label, domain, bg_color, text_color}]
stat        : accent-colored card with big visual_text + visual_subtitle
logo_single : one branded card with logo centered
plain       : no card (title only)

The agent deliberately does NOT generate the script — it only plans visuals.
"""
from __future__ import annotations

import json
import logging

from openai import OpenAI
from src.config import settings

log = logging.getLogger(__name__)

_SYSTEM = """
Eres un director de arte para YouTube Shorts de contenido técnico en español.
Tu trabajo: dado un tema y secciones de script, diseñar el layout visual de cada slide.

Reglas de negocio:
- Los tabs deben ser palabras CORTAS y DESCRIPTIVAS del contenido (no "gancho", "punto 1", "cta")
  Ejemplos buenos: "intro", "qué es", "diferencia", "costes", "veredicto", "sígueme"
  Max 2 palabras por tab, 10 caracteres total por tab.
- Los section titles deben ser MUY CORTOS: max 3 palabras, max 10 letras por palabra.
  Si una palabra clave es larga (>10 letras), abrevia: "INTEROPERABILIDAD" → "INTER-OP" o "PORTABILIDAD"
- Card types (SIEMPRE elige uno, NUNCA dejes un slide sin card):
    comparison  → cuando el slide compara DOS productos/empresas concretas
    stat        → cuando hay un dato, afirmación impactante, o conclusión (veredicto, CTA, gancho)
    logo_single → cuando el slide trata de UN producto/empresa específica
  REGLA: para slides de intro/gancho/CTA/veredicto usa siempre stat con visual_text impactante.
  NUNCA uses 'plain' — siempre hay algo que mostrar.
- domains: usa dominios reales de Clearbit (ej: langchain.com, anthropic.com, openai.com)
  Si no conoces el dominio exacto, usa el más probable.
- bg_color: usa el color de marca real del producto (ej: LangChain #1C3C3C, Anthropic #CC785C)
  text_color: "#FFFFFF" para fondos oscuros, "#000000" para fondos claros
"""

_USER_TMPL = """
Tema del Short: {topic}

Secciones del script (5 slides):
{sections_json}

Devuelve JSON con esta estructura exacta (sin markdown):
{{
  "tabs": ["tab0", "tab1", "tab2", "tab3", "tab4"],
  "slides": [
    {{
      "title": "TÍTULO CORTO",
      "card": {{
        "type": "comparison",
        "items": [
          {{"label": "LangChain", "domain": "langchain.com", "bg_color": "#1C3C3C", "text_color": "#FFFFFF"}},
          {{"label": "MCP", "domain": "anthropic.com", "bg_color": "#CC785C", "text_color": "#FFFFFF"}}
        ]
      }}
    }},
    {{
      "title": "DATO CLAVE",
      "card": {{"type": "stat", "visual_text": "CERO CÓDIGO", "visual_subtitle": "con MCP"}}
    }},
    {{
      "title": "LANGCHAIN",
      "card": {{"type": "logo_single", "label": "LangChain", "domain": "langchain.com", "bg_color": "#1C3C3C", "text_color": "#FFFFFF"}}
    }},
    {{
      "title": "VEREDICTO",
      "card": {{"type": "stat", "visual_text": "DEPENDE", "visual_subtitle": "del caso de uso"}}
    }},
    {{
      "title": "SÍGUEME",
      "card": {{"type": "stat", "visual_text": "SÍGUEME", "visual_subtitle": "" + brand.channel_handle + ""}}
    }}
  ]
}}
"""


def plan(topic: str, sections: list[dict]) -> dict:
    """
    Run the visual orchestration agent.
    Returns: {tabs: [...], slides: [{title, card: {...}}, ...]}
    Slides and tabs have the same length as sections.
    """
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)

    sections_json = json.dumps(
        [{"label": s.get("label", ""), "text": s.get("text", "")[:120]} for s in sections],
        ensure_ascii=False,
        indent=2,
    )

    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _USER_TMPL.format(
                topic=topic,
                sections_json=sections_json,
            )},
        ],
        temperature=0.4,  # low temp for consistent JSON
    )

    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    plan_data: dict = json.loads(raw)

    # Validate + fallback
    tabs   = plan_data.get("tabs", [s.get("label", f"s{i}") for i, s in enumerate(sections)])
    slides = plan_data.get("slides", [{"title": s.get("title", ""), "card": {"type": "plain"}} for s in sections])

    # Align lengths
    while len(tabs)   < len(sections): tabs.append(f"s{len(tabs)}")
    while len(slides) < len(sections): slides.append({"title": "", "card": {"type": "plain"}})

    log.info(f"[VisualPlanner] tabs={tabs}")
    for i, sl in enumerate(slides):
        log.info(f"  slide {i}: '{sl.get('title','')}' → {sl.get('card',{}).get('type','?')}")

    return {"tabs": tabs[:len(sections)], "slides": slides[:len(sections)]}
