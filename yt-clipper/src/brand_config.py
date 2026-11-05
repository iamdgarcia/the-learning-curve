"""Brand config loader — reads config/faceless_brand.json."""
import json
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT = Path(__file__).parent.parent / "config" / "faceless_brand.json"


@dataclass
class BrandConfig:
    channel_handle: str = "@YourChannel"
    channel_niche: str = "IA · LLMs · Python"
    accent_color: str = "#0047FF"
    bg_color: str = "#FFFFFF"
    grid_color: str = "#E5E5E5"
    grid_size: int = 54
    text_color: str = "#0D0D0D"
    card_text_color: str = "#FFFFFF"
    font_bold: str = "assets/fonts/InterDisplay-Bold.ttf"
    font_regular: str = "assets/fonts/Inter-Medium.ttf"
    tts_voice: str = "es-ES-AlvaroNeural"
    tts_rate: str = "+5%"
    default_privacy: str = "unlisted"
    tiktok_enabled: bool = False
    youtube_channel_url: str = ""

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
