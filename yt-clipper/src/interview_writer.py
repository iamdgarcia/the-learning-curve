"""
Interview/explainer script writer.
Generates: narration text + section timing + animation spec for Claude.
"""
from __future__ import annotations
import importlib.util
import json
import logging
import pathlib
from openai import OpenAI
from src.config import settings
from src import brand_config

_SKILL_DIR = pathlib.Path(__file__).parent.parent / "skills" / "viral-video-writing"
_SCORE_PY  = _SKILL_DIR / "scripts" / "score.py"


def _score(text: str) -> tuple[int, list, list]:
    if not _SCORE_PY.exists():
        return 100, [], []
    spec = importlib.util.spec_from_file_location("vvw_score", _SCORE_PY)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    total, hard, soft, *_ = mod.score(text)
    return total, hard, soft

log = logging.getLogger(__name__)
_WPM = 130  # Spanish narration pace

def write(topic: str, duration_s: int = 55) -> dict:
    """
    Returns:
      narration   — plain text to TTS
      sections    — [{title, text, start_s, end_s}]  (for animation timeline)
      yt_title    — YouTube title
      description — YouTube description
      tags        — list[str]
    """
    brand = brand_config.load()
    word_target = int(duration_s * _WPM / 60)
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    _base = (
        f"Escribe un script para un YouTube Short educativo de {duration_s}s (~{word_target} palabras).\n"
        f"Tema: {topic}\n"
        "Idioma: espa\u00f1ol de Espa\u00f1a. Voz: directa, t\u00e9cnica pero accesible.\n"
        f"Canal: {brand.channel_handle}" + (f" ({brand.channel_owner})" if brand.channel_owner else "") + ".\n"
        "Formato: pregunta de entrevista IA explicada con diagrama animado.\n\n"
        "Estructura (exactamente 5 secciones):\n"
        "1. INTRO (5s): t\u00edtulo impactante, qu\u00e9 es y por qu\u00e9 importa para IA\n"
        "2. PROBLEMA (10s): el caso de uso real en IA/LLMs que lo motiva\n"
        "3. C\u00d3MO FUNCIONA (15s): mecanismo paso a paso, lo m\u00e1s visual posible\n"
        "4. RESULTADO (10s): qu\u00e9 gana un dev de IA us\u00e1ndolo\n"
        "5. CTA (5s): suscr\u00edbete + un concepto de IA por semana\n\n"
        'Devuelve JSON puro:\n'
        '{{\n'
        '  "narration": "texto completo a narrar seguido, sin etiquetas",\n'
        '  "sections": [\n'
        '    {{"title": "BLOOM FILTER", "text": "fragmento de esa secci\u00f3n", "start_s": 0, "end_s": 5}},\n'
        '    ...\n'
        '  ],\n'
        '  "yt_title": "t\u00edtulo YouTube <100 chars con emoji",\n'
        '  "description": "descripci\u00f3n con hashtags",\n'
        '  "tags": ["tag1", "tag2"]\n'
        '}}'
    )
    data: dict = {}
    feedback = ""
    for attempt in range(3):
        content = _base if not feedback else _base + f"\n\nProblemas del intento anterior \u2014 corr\u00edgelos:\n{feedback}"
        resp = client.chat.completions.create(
            model=settings.novita_model,
            messages=[{"role": "user", "content": content}],
            temperature=0.6,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"): raw = raw.split("```")[1].lstrip("json").strip().rsplit("```", 1)[0]
        data = json.loads(raw)

        sc, hard, soft = _score(data.get("narration", ""))
        log.info(f"[InterviewWriter] attempt {attempt+1}/3 — score {sc}/100, hard={len(hard)}, soft={len(soft)}")
        if sc >= 90 and not hard:
            break
        feedback = "\n".join([f"HARD: {h}" for h in hard] + [f"soft: {s}" for s in soft])

    log.info(f"[InterviewWriter] '{data.get('yt_title','')}' — {len(data.get('narration','').split())} words")
    return data
