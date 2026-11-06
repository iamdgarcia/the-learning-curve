"""
LLM script writer for faceless YouTube Shorts (Spanish).
~140 wpm is a comfortable Spanish narration pace.
"""
import importlib.util
import json
import logging
import pathlib

from openai import OpenAI
from src.config import settings

log = logging.getLogger(__name__)

_WPM = 140  # ponytail: global knob, tune if TTS pace changes
_SKILL_DIR = pathlib.Path(__file__).parent.parent / "skills" / "viral-video-writing"
_SCORE_PY  = _SKILL_DIR / "scripts" / "score.py"

_VOICE = """
Voz: directa, datos concretos, sin relleno. Cada segundo cuenta.
Estilo: divulgación técnica amigable para developers curiosos.
Idioma: español de España (tú, no vosotros; sin latinismos).
Nunca menciones "en este vídeo" ni "hoy os traigo".
"""


def _load_hook_rules() -> str:
    p = _SKILL_DIR / "hook-craft.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _score(text: str) -> tuple[int, list, list]:
    """Score via viral-video-writing skill; (100,[],[]) if skill absent."""
    if not _SCORE_PY.exists():
        return 100, [], []
    spec = importlib.util.spec_from_file_location("vvw_score", _SCORE_PY)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    total, hard, soft, *_ = mod.score(text)
    return total, hard, soft


def write_script(topic: str, hook: str = "", target_duration_s: int = 55) -> dict:
    """
    Generate a complete faceless Short package.

    Returns:
        script         – text to narrate (no stage directions)
        sections       – list of 5 section dicts
        title          – YouTube title <100 chars with emoji
        description    – YouTube description with hashtags
        tags           – list[str] of 10 YouTube tags in Spanish
        thumbnail_text – ≤4 words for thumbnail overlay
        keywords       – list[str] English keywords for Pexels footage search
    """
    word_target = int(target_duration_s * _WPM / 60)
    hook_rules  = _load_hook_rules()

    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)

    base_prompt = (
        f"Escribe un script para un YouTube Short faceless de {target_duration_s}s "
        f"(~{word_target} palabras).\n"
        f"Tema: {topic}\n"
        f"{'Gancho sugerido: ' + hook if hook else ''}\n"
        f"Voz del canal:\n{_VOICE}\n\n"
        + (f"Reglas de gancho (aplícalas al GANCHO del script):\n{hook_rules}\n\n" if hook_rules else "")
        + "Estructura (exactamente 5 secciones):\n"
        "1. GANCHO (5s): pregunta o dato impactante — claridad + curiosidad, sin clichés\n"
        "2. PUNTO 1 (~10s): primer dato/argumento concreto\n"
        "3. PUNTO 2 (~10s): segundo dato/argumento\n"
        "4. PUNTO 3 (~10s): tercer dato/argumento\n"
        "5. CTA (5s): llamada a seguir el canal o comentar\n\n"
        "Devuelve JSON con estos campos exactos:\n"
        "  script: string — texto completo a narrar (todo seguido, sin etiquetas de sección)\n"
        "  sections: array de 5 objetos con:\n"
        "    label: string corto para la pestaña de navegación (1-2 palabras, minúsculas)\n"
        "    title: string título visual en MAYÚSCULAS (máx 3 palabras, ninguna palabra más de 10 letras)\n"
        "    text: el texto de esa sección (fragmento del script)\n"
        "    visual_text: dato, stat o frase impactante (máx 4 palabras) para mostrar en una card central grande\n"
        "    visual_subtitle: contexto breve de visual_text (máx 5 palabras)\n"
        "  title: string — título YouTube con emoji, <100 chars\n"
        "  description: string — descripción YouTube con hashtags al final\n"
        "  tags: array[string] — 10 tags en español\n"
        "  thumbnail_text: string — máximo 4 palabras impactantes\n"
        "  keywords: array[string] — 4 palabras clave en INGLÉS para Pexels\n"
        "JSON puro, sin markdown."
    )

    result: dict = {}
    feedback = ""
    for attempt in range(3):
        prompt = base_prompt if not feedback else (
            base_prompt + f"\n\nProblemas del intento anterior — corrígelos:\n{feedback}"
        )
        resp = client.chat.completions.create(
            model=settings.novita_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        result = json.loads(raw)

        sc, hard, soft = _score(result.get("script", ""))
        log.info(f"[Script] attempt {attempt+1}/3 — score {sc}/100, hard={len(hard)}, soft={len(soft)}")
        if sc >= 90 and not hard:
            break
        feedback = "\n".join([f"HARD: {h}" for h in hard] + [f"soft: {s}" for s in soft])

    log.info(f"[Script] '{result.get('title', '')}' — {len(result.get('script','').split())} words")
    return result
