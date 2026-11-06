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

from src.brand_config import load as load_brand

log = logging.getLogger(__name__)


def _channel_context() -> str:
    b = load_brand()
    parts = [f"Channel: {b.channel_handle}"]
    if b.channel_owner:      parts.append(f"Owner: {b.channel_owner}")
    if b.channel_niche:      parts.append(f"Niche: {b.channel_niche}")
    if b.channel_description: parts.append(b.channel_description)
    if b.channel_topics:     parts.append(f"Topic areas: {b.channel_topics}")
    if b.channel_language:   parts.append(f"Language: {b.channel_language}")
    parts.append("Format: faceless Short 45-60s")
    return "\n".join(parts)

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
                f"You are a content strategist for YouTube Shorts.\n"
                f"Channel context:\n{_channel_context()}\n"
                f"Effective formats: {json.dumps(_FORMATS, ensure_ascii=False)}\n\n"
                f"Generate {n} Short ideas about current trending topics for this channel "
                f"(last 30 days). Prioritise debate, comparisons or surprising data.\n\n"
                f"Return a JSON array. Each item:\n"
                f"  topic: specific topic (e.g. 'Claude 3.5 Sonnet vs GPT-4o')\n"
                f"  format: chosen format from the list\n"
                f"  hook: opening hook sentence (<15 words, immediate impact)\n"
                f"  score: estimated virality 1-10\n"
                f"  keywords: array of 3-5 English keywords for stock footage search\n"
                f"Pure JSON, no markdown, no extra text."
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
