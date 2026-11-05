"""
Generates ASS subtitle files in multiple TikTok-inspired styles.

Styles:
  karaoke  (default) — 3 words shown at a time, active word in yellow
  wordbox  — each active word gets a solid colour box background
  clean    — white text, no highlight, no box (minimal)
  emoji    — karaoke + emoji injected after keyword matches

Word timestamps must come from Whisper (word_timestamps=True) or are
approximated by distributing segment text linearly.
"""
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

log = logging.getLogger(__name__)

WORDS_PER_PHRASE = 3

# ── colour palette ─────────────────────────────────────────────────────────────
# ASS &HAABBGGRR  (AA=alpha, BGR colour)
WHITE   = "&H00FFFFFF"
YELLOW  = "&H0000FFFF"
BLACK   = "&H00000000"
SHADOW  = "&HAA000000"
CYAN    = "&H00FFFF00"   # wordbox background (teal)
ORANGE  = "&H000080FF"   # wordbox active word

# ── emoji keyword map ──────────────────────────────────────────────────────────
_EMOJI_MAP = {
    # ES
    "gratis": "🎁", "dinero": "💰", "error": "❌", "funciona": "✅",
    "rápido": "⚡", "fácil": "🙌", "problema": "⚠️", "solución": "💡",
    "importante": "‼️", "atención": "👀", "nuevo": "🆕", "secreto": "🤫",
    "modelo": "🤖", "ia": "🤖", "inteligencia": "🧠", "código": "💻",
    "python": "🐍", "api": "🔌", "datos": "📊", "probabilidad": "📈",
    # EN
    "free": "🎁", "money": "💰", "error": "❌", "works": "✅",
    "fast": "⚡", "easy": "🙌", "problem": "⚠️", "solution": "💡",
    "important": "‼️", "attention": "👀", "new": "🆕", "secret": "🤫",
    "model": "🤖", "ai": "🤖", "intelligence": "🧠", "code": "💻",
}


class CaptionStyle(str, Enum):
    karaoke = "karaoke"   # word-by-word yellow highlight
    wordbox = "wordbox"   # solid colour box per active word
    clean   = "clean"     # white text, no highlight
    emoji   = "emoji"     # karaoke + emoji keywords


# ── ASS header builders ────────────────────────────────────────────────────────

def _header(style: CaptionStyle) -> str:
    base = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,"
        "ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
    )
    if style == CaptionStyle.wordbox:
        # BorderStyle=4 → box background; outline colour = box fill
        style_line = (
            f"Style: TikTok,Arial,85,{WHITE},{ORANGE},{CYAN},{SHADOW},"
            "1,0,0,0,100,100,0,0,4,12,2,2,80,80,400,1\n"
        )
    elif style == CaptionStyle.clean:
        style_line = (
            f"Style: TikTok,Arial,80,{WHITE},{WHITE},{BLACK},{SHADOW},"
            "1,0,0,0,100,100,0,0,1,4,2,2,80,80,400,1\n"
        )
    else:  # karaoke / emoji (same visual base)
        style_line = (
            f"Style: TikTok,Arial,85,{WHITE},{YELLOW},{BLACK},{SHADOW},"
            "1,0,0,0,100,100,0,0,1,5,2,2,80,80,400,1\n"
        )
    return base + style_line + "\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"


# ── data ───────────────────────────────────────────────────────────────────────

@dataclass
class Word:
    text: str
    start: float
    end: float


def _ts(s: float) -> str:
    s = max(0.0, s)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    cs = s % 60
    return f"{h}:{m:02d}:{cs:05.2f}"


def _clean(t: str) -> str:
    return t.strip().replace("{", "").replace("}", "")


def _emoji_for(word: str) -> str:
    return _EMOJI_MAP.get(word.lower().strip(".,!?:;"), "")


# ── word extraction ────────────────────────────────────────────────────────────

def _from_whisper(segs: list, clip_start: float) -> list[Word]:
    words = []
    for seg in segs:
        for w in seg.get("words", []):
            s = w["start"] - clip_start
            e = w["end"]   - clip_start
            if e > 0:
                words.append(Word(_clean(w["word"]), max(0, s), max(0, e)))
    return words


def _from_segments(segs: list, clip_start: float) -> list[Word]:
    words = []
    for seg in segs:
        s = (seg["start"] if isinstance(seg, dict) else seg.start) - clip_start
        e = (seg.get("end", seg["start"] + 3.0) if isinstance(seg, dict)
             else seg.start + 3.0) - clip_start
        text = (seg.get("text", "") if isinstance(seg, dict) else seg.text)
        tokens = text.split()
        if not tokens or e <= 0:
            continue
        dur = (e - s) / len(tokens)
        for i, t in enumerate(tokens):
            words.append(Word(_clean(t), max(0, s + i * dur), max(0, s + (i + 1) * dur)))
    return words


# ── speaker-aware event builders ─────────────────────────────────────────────────

def _events_with_speakers(words: list[Word], style: CaptionStyle,
                          speaker_segments: list) -> list[str]:
    """Like _events but colours the active word with the speaker's colour."""
    from src.speaker_diarizer import speaker_for_time
    events = []
    for start in range(0, len(words), WORDS_PER_PHRASE):
        phrase = words[start:start + WORDS_PER_PHRASE]
        for i, w in enumerate(phrase):
            seg = speaker_for_time(speaker_segments, w.start)
            speaker_color = seg.color_ass if seg else YELLOW

            parts = []
            for j, pw in enumerate(phrase):
                t = pw.text
                emj = _emoji_for(t) if style == CaptionStyle.emoji else ""
                suffix = f" {emj}" if emj else ""
                if j == i:
                    parts.append(f"{{\\c{speaker_color}}}{t}{suffix}{{\\c{WHITE}}}")
                else:
                    parts.append(t + suffix)
            text = " ".join(parts)
            events.append(
                f"Dialogue: 0,{_ts(w.start)},{_ts(w.end)},"
                f"TikTok,,0,0,0,,{text}"
            )
    return events


# ── event builders ─────────────────────────────────────────────────────────────

def _line_karaoke(phrase: list[Word], hi: int, style: CaptionStyle) -> str:
    parts = []
    for i, w in enumerate(phrase):
        t = w.text
        emj = _emoji_for(t) if style == CaptionStyle.emoji else ""
        suffix = f" {emj}" if emj else ""
        if i == hi:
            parts.append(f"{{\\c{YELLOW}}}{t}{suffix}{{\\c{WHITE}}}")
        else:
            parts.append(t + suffix)
    return " ".join(parts)


def _line_wordbox(phrase: list[Word], hi: int) -> str:
    """Each word normal; active word uses secondary colour override."""
    parts = []
    for i, w in enumerate(phrase):
        t = w.text
        if i == hi:
            # highlight box: toggle BorderStyle to box for just this word
            parts.append(f"{{\\c{ORANGE}}}{t}{{\\c{WHITE}}}")
        else:
            parts.append(t)
    return " ".join(parts)


def _line_clean(phrase: list[Word]) -> str:
    return " ".join(w.text for w in phrase)


def _events(words: list[Word], style: CaptionStyle) -> list[str]:
    events = []
    for start in range(0, len(words), WORDS_PER_PHRASE):
        phrase = words[start:start + WORDS_PER_PHRASE]
        for i, w in enumerate(phrase):
            if style == CaptionStyle.clean:
                text = _line_clean(phrase)
            elif style == CaptionStyle.wordbox:
                text = _line_wordbox(phrase, i)
            else:  # karaoke / emoji
                text = _line_karaoke(phrase, i, style)
            events.append(
                f"Dialogue: 0,{_ts(w.start)},{_ts(w.end)},"
                f"TikTok,,0,0,0,,{text}"
            )
    return events


# ── public API ─────────────────────────────────────────────────────────────────

def generate(
    segments: list,
    clip_start: float,
    clip_duration: float,
    output_path: str,
    has_word_timestamps: bool = False,
    style: CaptionStyle = CaptionStyle.karaoke,
    speaker_segments: list | None = None,   # from speaker_diarizer.diarize()
) -> Path:
    out = Path(output_path)

    words = (_from_whisper(segments, clip_start) if has_word_timestamps
             else _from_segments(segments, clip_start))
    words = [w for w in words if w.start < clip_duration and w.end > 0]
    for w in words:
        w.end = min(w.end, clip_duration)

    # Apply speaker colors if diarization data available
    if speaker_segments:
        events = _events_with_speakers(words, style, speaker_segments)
    else:
        events = _events(words, style)
    log.info(f"Generated {len(events)} subtitle events (style={style.value}) from {len(words)} words")

    out.write_text(_header(style) + "\n".join(events) + "\n", encoding="utf-8")
    return out
