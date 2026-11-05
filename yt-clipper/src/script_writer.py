"""
LLM script writer for faceless YouTube Shorts (Spanish).
~140 wpm is a comfortable Spanish narration pace.
"""
import json
import logging

from openai import OpenAI
from src.config import settings

log = logging.getLogger(__name__)

_WPM = 140  # ponytail: global knob, tune if TTS pace changes

_VOICE = """
Voz: directa, datos concretos, sin relleno. Cada segundo cuenta.
Estilo: divulgación técnica amigable para developers curiosos.
Idioma: español de España (tú, no vosotros; sin latinismos).
Nunca menciones "en este vídeo" ni "hoy os traigo".
"""


def write_script(topic: str, hook: str = "", target_duration_s: int = 55) -> dict:
    """
    Generate a complete faceless Short package.

    Returns:
        script       – text to narrate (no stage directions)
        title        – YouTube title <100 chars with emoji
        description  – YouTube description with hashtags
        tags         – list[str] of 10 YouTube tags in Spanish
        thumbnail_text – ≤4 words for thumbnail overlay
        keywords     – list[str] English keywords for Pexels footage search
    """
    word_target = int(target_duration_s * _WPM / 60)

    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{
            "role": "user",
            "content": (
                f"Escribe un script para un YouTube Short faceless de {target_duration_s}s "
                f"(~{word_target} palabras).\n"
                f"Tema: {topic}\n"
                f"{'Gancho sugerido: ' + hook if hook else ''}\n"
                f"Voz del canal:\n{_VOICE}\n\n"
                f"Estructura (exactamente 5 secciones):\n"
                f"1. GANCHO (5s): pregunta o dato impactante\n"
                f"2. PUNTO 1 (~10s): primer dato/argumento concreto\n"
                f"3. PUNTO 2 (~10s): segundo dato/argumento\n"
                f"4. PUNTO 3 (~10s): tercer dato/argumento\n"
                f"5. CTA (5s): llamada a seguir el canal o comentar\n\n"
                f"Devuelve JSON con estos campos exactos:\n"
                f"  script: string — texto completo a narrar (todo seguido, sin etiquetas de sección)\n"
                f"  sections: array de 5 objetos con:\n"
                f"    label: string corto para la pestaña de navegación (1-2 palabras, minúsculas)\n"
                f"    title: string título visual en MAYÚSCULAS (máx 3 palabras, ninguna palabra más de 10 letras)\n"
                f"    text: el texto de esa sección (fragmento del script)\n"
                f"    visual_text: dato, stat o frase impactante (máx 4 palabras) para mostrar en una card central grande\n"
                f"    visual_subtitle: contexto breve de visual_text (máx 5 palabras)\n"
                f"  title: string — título YouTube con emoji, <100 chars\n"
                f"  description: string — descripción YouTube con hashtags al final\n"
                f"  tags: array[string] — 10 tags en español\n"
                f"  thumbnail_text: string — máximo 4 palabras impactantes\n"
                f"  keywords: array[string] — 4 palabras clave en INGLÉS para Pexels\n"
                f"JSON puro, sin markdown."
            )
        }],
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    result: dict = json.loads(raw)

    word_count = len(result.get("script", "").split())
    log.info(f"[Script] '{result.get('title', '')}' — {word_count} words")
    return result
