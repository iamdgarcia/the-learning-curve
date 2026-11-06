"""Brand config loader — reads config/faceless_brand.json."""
import json
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT = Path(__file__).parent.parent / "config" / "faceless_brand.json"


@dataclass
class BrandConfig:
    # ── Identity ──────────────────────────────────────────────────────────────
    channel_handle: str = "@YourChannel"       # e.g. "@TheLearningCurveAI"
    channel_owner: str = ""                    # e.g. "Daniel García" (used in LLM prompts)
    channel_niche: str = "tech education"       # short label shown on slides
    channel_description: str = ""              # 1-2 sentences for LLM context
    channel_topics: str = ""                   # comma-separated topic hints for auto topic picker
    channel_language: str = "en"               # BCP-47 language code for scripts + TTS
    youtube_channel_url: str = ""

    # ── Visual brand ──────────────────────────────────────────────────────────
    accent_color: str = "#0047FF"
    bg_color: str = "#FFFFFF"
    grid_color: str = "#E5E5E5"
    grid_size: int = 54
    text_color: str = "#0D0D0D"
    card_text_color: str = "#FFFFFF"
    font_bold: str = "assets/fonts/InterDisplay-Bold.ttf"
    font_regular: str = "assets/fonts/Inter-Medium.ttf"
    logo_path: str = ""                        # path to channel logo PNG

    # ── TTS ───────────────────────────────────────────────────────────────────
    tts_voice: str = "es-ES-AlvaroNeural"      # legacy fallback; prefer config/tts.json
    tts_rate: str = "+0%"

    # ── CTA slide ─────────────────────────────────────────────────────────────
    cta_url: str = ""                          # e.g. "yoursubstack.com"
    cta_button_text: str = "Subscribe"         # text on the CTA button
    cta_tagline: str = ""                      # e.g. "One AI concept a week"
    cta_logo: str = ""                         # path to logo shown on CTA slide
    cta_screenshot: str = ""                   # optional: path to screenshot shown on CTA card

    # ── Pipeline defaults ─────────────────────────────────────────────────────
    default_privacy: str = "unlisted"
    tiktok_enabled: bool = False

    def accent_rgb(self) -> tuple[int, int, int]:
        h = self.accent_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    def bg_rgb(self) -> tuple[int, int, int]:
        h = self.bg_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    def grid_rgb(self) -> tuple[int, int, int]:
        h = self.grid_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    def text_rgb(self) -> tuple[int, int, int]:
        h = self.text_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore

    def card_text_rgb(self) -> tuple[int, int, int]:
        h = self.card_text_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def load(path: str | Path = _DEFAULT) -> BrandConfig:
    p = Path(path)
    if not p.exists():
        return BrandConfig()
    data = json.loads(p.read_text())
    return BrandConfig(**{k: v for k, v in data.items() if hasattr(BrandConfig, k)})
