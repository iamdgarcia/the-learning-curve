"""
Trending AI topic discovery for the Spanish market.
Uses the LLM (which knows current AI landscape) to propose high-virality ideas.

ponytail: LLM-as-oracle is enough for MVP. Add pytrends/YouTube Trending when
          real-time signal measurably improves CTR vs LLM baseline.
"""
import json
import logging

from openai import OpenAI
from src.config import settings

log = logging.getLogger(__name__)

_CHANNEL_CONTEXT = """
Canal: TheLearningCurveAI (Daniel García, España).
Nicho: LLMs, agentes IA, Python, herramientas de IA, tutoriales prácticos.
Audiencia: desarrolladores y makers hispanohablantes.
Formato: Short faceless 45-60s, en español de España.
"""

_FORMATS = [
    "X vs Y — cuál elegir y por qué",
    "Los N errores más comunes con X",
    "Cómo funciona X en 60 segundos",
    "El secreto que nadie te cuenta sobre X",
    "X cambió todo lo que sabíamos de Y",
    "Por qué X ya no sirve (y qué usar en su lugar)",
    "Qué es X y por qué deberías aprenderlo ya",
    "El truco de X que usan los pros",
]


def get_trending_topics(n: int = 5) -> list[dict]:
    """
    Return n topic ideas sorted by virality score (desc).
    Each item: {topic, format, hook, score, keywords}
    """
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{
            "role": "user",
            "content": (
                f"Eres un estratega de contenido para YouTube Shorts en español.\n"
                f"Contexto del canal:\n{_CHANNEL_CONTEXT}\n"
                f"Formatos efectivos: {json.dumps(_FORMATS, ensure_ascii=False)}\n\n"
                f"Genera {n} ideas de Short sobre tendencias actuales en IA/LLMs/agentes "
                f"(últimos 30 días). Prioriza temas con debate, comparaciones o datos sorprendentes.\n\n"
                f"Devuelve JSON array. Cada item:\n"
                f"  topic: tema concreto (ej: 'Claude 3.5 Sonnet vs GPT-4o')\n"
                f"  format: formato elegido de la lista\n"
                f"  hook: primera frase de gancho (<15 palabras, impacto inmediato)\n"
                f"  score: viralidad estimada 1-10\n"
                f"  keywords: array 3-5 palabras clave en inglés para buscar stock footage\n"
                f"JSON puro, sin markdown, sin texto extra."
            )
        }],
        temperature=0.85,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    ideas: list[dict] = json.loads(raw)
    ideas.sort(key=lambda x: x.get("score", 0), reverse=True)
    log.info(f"[Trends] {len(ideas)} ideas generated, top: {ideas[0].get('topic','')}")
    return ideas[:n]
