"""
Interview/explainer script writer.
Generates: narration text + section timing + animation spec for Claude.
"""
from __future__ import annotations
import json, logging
from openai import OpenAI
from src.config import settings

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
    word_target = int(duration_s * _WPM / 60)
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{"role": "user", "content": f"""
Escribe un script para un YouTube Short educativo de {duration_s}s (~{word_target} palabras).
Tema: {topic}
Idioma: español de España. Voz: directa, técnica pero accesible.
Canal: @TheLearningCurveAI (Daniel García) — nicho IA/LLMs/Agentes para developers hispanohablantes.
Formato: pregunta de entrevista IA explicada con diagrama animado.

Estructura (exactamente 5 secciones):
1. INTRO (5s): título impactante, qué es y por qué importa para IA
2. PROBLEMA (10s): el caso de uso real en IA/LLMs que lo motiva
3. CÓMO FUNCIONA (15s): mecanismo paso a paso, lo más visual posible
4. RESULTADO (10s): qué gana un dev de IA usándolo
5. CTA (5s): suscríbete + un concepto de IA por semana

Devuelve JSON puro:
{{
  "narration": "texto completo a narrar seguido, sin etiquetas",
  "sections": [
    {{"title": "BLOOM FILTER", "text": "fragmento de esa sección", "start_s": 0, "end_s": 5}},
    ...
  ],
  "yt_title": "título YouTube <100 chars con emoji",
  "description": "descripción con hashtags",
  "tags": ["tag1", "tag2"]
}}
"""}], temperature=0.6)
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"): raw = raw.split("```")[1].lstrip("json").strip().rsplit("```",1)[0]
    data = json.loads(raw)
    log.info(f"[InterviewWriter] '{data.get('yt_title','')}' — {len(data.get('narration','').split())} words")
    return data
