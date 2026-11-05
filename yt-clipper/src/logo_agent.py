"""
Logo agent — resolves any brand name to a downloadable logo.

Strategy:
  1. Check disk cache (temp/logos/slugs.json) for a known slug
  2. If not cached, ask the LLM for the simple-icons slug (one cheap call)
  3. Download SVG from simple-icons GitHub, render white (or black) via cairosvg
  4. Cache slug + PNG to disk

If simple-icons has no icon for the brand, returns None — caller renders
the brand initial as fallback.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

log = logging.getLogger(__name__)

_LOGO_DIR  = Path("temp/logos")
_SLUG_FILE = _LOGO_DIR / "slugs.json"
_SI_BASE   = "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons"

# Seed cache with known high-frequency brands so we skip the LLM call
_SEED: dict[str, str] = {
    "langchain":        "langchain",
    "anthropic":        "anthropic",
    "openai":           "openai",
    "chatgpt":          "openai",
    "claude":           "anthropic",
    "mcp":              "anthropic",
    "google":           "google",
    "gemini":           "googlegemini",
    "meta":             "meta",
    "llama":            "meta",
    "hugging face":     "huggingface",
    "huggingface":      "huggingface",
    "mistral":          "mistralai",
    "groq":             "none",     # not in simple-icons
    "cohere":           "none",     # not in simple-icons
    "aws":              "amazonwebservices",
    "amazon":           "amazonwebservices",
    "azure":            "microsoftazure",
    "microsoft":        "microsoft",
    "github":           "github",
    "python":           "python",
    "pytorch":          "pytorch",
    "tensorflow":       "tensorflow",
    "docker":           "docker",
    "fastapi":          "fastapi",
    "ollama":           "ollama",
    "cursor":           "cursor",
    "vercel":           "vercel",
    "supabase":         "supabase",
    "pinecone":         "pinecone",
    "weaviate":         "none",     # not in simple-icons
    "qdrant":           "qdrant",
    "redis":            "redis",
    "postgresql":       "postgresql",
    "mongodb":          "mongodb",
    "langsmith":        "langchain",
    "langgraph":        "langchain",
    "crewai":           "none",
    "autogen":          "microsoft",
    "dspy":             "none",
}


def _load_slug_cache() -> dict[str, str]:
    _LOGO_DIR.mkdir(parents=True, exist_ok=True)
    if _SLUG_FILE.exists():
        try:
            return json.loads(_SLUG_FILE.read_text())
        except Exception:
            pass
    return dict(_SEED)


def _save_slug_cache(cache: dict[str, str]) -> None:
    _LOGO_DIR.mkdir(parents=True, exist_ok=True)
    _SLUG_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def _llm_resolve(brand: str) -> str:
    """Ask the LLM for the simple-icons slug. Returns slug or 'none'."""
    from openai import OpenAI
    from src.config import settings

    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{
            "role": "user",
            "content": (
                f"What is the exact slug used in the simple-icons project (simpleicons.org) "
                f"for the brand '{brand}'?\n"
                f"Reply with ONLY the slug (lowercase, no spaces, as it appears in the GitHub URL "
                f"https://github.com/simple-icons/simple-icons/blob/develop/icons/<SLUG>.svg).\n"
                f"If the brand is not in simple-icons, reply: none"
            ),
        }],
        temperature=0,
        max_tokens=20,
    )
    slug = resp.choices[0].message.content.strip().lower().split()[0]
    slug = re.sub(r"[^a-z0-9]", "", slug)   # strip any punctuation
    log.info(f"[LogoAgent] LLM resolved '{brand}' → '{slug}'")
    return slug or "none"


def _try_download(slug: str, icon_color: str, dest: Path) -> bool:
    """Download SVG from simple-icons, render to PNG. Returns True on success."""
    url = f"{_SI_BASE}/{slug}.svg"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            svg = r.read().decode()
        # Inject fill color into every path element
        svg = re.sub(r"(<(?:path|circle|rect|polygon)\b)", f'<path fill="{icon_color}" ', svg)
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=300, output_height=300)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(png)
        return dest.stat().st_size > 200
    except Exception as e:
        log.warning(f"[LogoAgent] download '{slug}': {e}")
        return False


def fetch(brand_name: str, icon_color: str = "white") -> Image.Image | None:
    """
    Main entry point. Returns RGBA PIL image or None.
    brand_name — the human-readable brand name, e.g. "LangChain", "OpenAI"
    icon_color — "white" or "black" depending on card background
    """
    key   = brand_name.strip().lower()
    cache = _load_slug_cache()

    # 1. Check slug cache
    if key not in cache:
        slug = _llm_resolve(brand_name)
        cache[key] = slug
        _save_slug_cache(cache)
    else:
        slug = cache[key]

    if slug == "none" or not slug:
        return None

    # 2. Check PNG cache
    png_path = _LOGO_DIR / f"{slug}_{icon_color}.png"
    if png_path.exists() and png_path.stat().st_size > 200:
        try:
            return Image.open(png_path).convert("RGBA")
        except Exception:
            pass

    # 3. Download + render
    if _try_download(slug, icon_color, png_path):
        try:
            return Image.open(png_path).convert("RGBA")
        except Exception:
            pass

    return None
