"""
Compose a faceless 1080×1920 Short — brand-styled white grid aesthetic.

Pipeline:
  1. Whisper → word timestamps
  2. Match script sections to Whisper timestamps
  3. frame_generator → one PNG per section
  4. FFmpeg timed concat → background video
  5. Merge TTS audio
  6. Burn karaoke subtitles → final MP4

ponytail: section-timestamp matching uses first-word search in Whisper output.
          Falls back to proportional split if a section's first word isn't found.
"""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path

import whisper

import src.subtitle_generator as subtitle_generator
from src.brand_config import BrandConfig, load as load_brand
from src.cta_slide import get_png as get_cta_png
from src.slide_agent import generate_frames
from src.slide_reviewer import validate_frame
from src.subtitle_generator import CaptionStyle

log = logging.getLogger(__name__)

W, H = 1080, 1920
_WHISPER_MODEL = "small"


# ── Timestamp helpers ──────────────────────────────────────────────────────────

def _all_words(segments: list[dict]) -> list[dict]:
    """Flatten Whisper segments → list of {word, start, end}."""
    words = []
    for seg in segments:
        for w in seg.get("words", []):
            words.append({"word": w["word"].strip().lower(), "start": w["start"], "end": w["end"]})
    return words


def _section_starts(
    sections: list[dict],
    whisper_words: list[dict],
    total_duration: float,
) -> list[float]:
    """
    Estimate the start timestamp of each section.
    Strategy: proportional by word count (reliable baseline), then
    snap each boundary to the nearest real Whisper word timestamp.
    ponytail: word-search matching is fragile (repeated terms, stopwords);
              proportional split is boring and correct.
    """
    word_counts = [max(1, len(s["text"].split())) for s in sections]
    total_words = sum(word_counts)
    starts: list[float] = [0.0]
    cumulative = 0
    for wc in word_counts[:-1]:
        cumulative += wc
        t = total_duration * cumulative / total_words
        # snap to nearest Whisper word within ±2s
        best = t
        best_dist = 2.0
        for w in whisper_words:
            dist = abs(w["start"] - t)
            if dist < best_dist:
                best, best_dist = w["start"], dist
        starts.append(best)
    return starts


def _build_bg_video(
    brand: BrandConfig,
    topic_label: str,
    tabs: list[str],
    slides: list[dict],
    section_starts: list[float],
    total_duration: float,
    tmp: Path,
) -> Path:
    """
    Generate one PNG per section, concat them at the right timestamps
    into a background video.
    """
    png_paths = generate_frames(brand, topic_label, tabs, slides, tmp)

    # Build FFmpeg concat script with per-section durations
    durations: list[float] = []
    for i, start in enumerate(section_starts):
        if i + 1 < len(section_starts):
            durations.append(section_starts[i + 1] - start)
        else:
            durations.append(total_duration - start + 0.5)

    # FFmpeg concat: each PNG shown for its section duration
    # Using image2pipe + concat filter for precise timing
    filter_parts: list[str] = []
    inputs: list[str] = []
    for i, (png, dur) in enumerate(zip(png_paths, durations)):
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(png)]
        filter_parts.append(f"[{i}:v]scale={W}:{H},setsar=1[v{i}]")

    concat_filter = (
        "".join(f"[v{i}]" for i in range(len(png_paths)))
        + f"concat=n={len(png_paths)}:v=1:a=0[vout]"
    )
    full_filter = ";".join(filter_parts + [concat_filter])

    bg_out = tmp / "bg.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", full_filter,
            "-map", "[vout]",
            "-t", str(total_duration + 0.5),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-r", "30",
            str(bg_out),
        ],
        capture_output=True,
        check=True,
    )
    return bg_out


# ── Public API ────────────────────────────────────────────────────────────────

def compose(
    audio_path: str,
    output_path: str,
    sections: list[dict],         # from script_writer: [{label, title, text}]
    visual_plan: dict | None = None,  # from visual_planner: {tabs, slides}
    topic_label: str = "",
    brand: BrandConfig | None = None,
    caption_style: CaptionStyle = CaptionStyle.karaoke,
    word_events: list[dict] | None = None,  # from tts.generate_with_timestamps()
) -> Path:
    """
    Build the final 1080×1920 faceless Short.
    sections — script sections from script_writer (must have label, title, text)
    """
    if brand is None:
        brand = load_brand()
    if not topic_label:
        topic_label = brand.channel_niche

    audio = Path(audio_path)
    out   = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Audio duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(audio)],
        capture_output=True, text=True, check=True,
    )
    duration = float(json.loads(probe.stdout)["streams"][0]["duration"])
    log.info(f"[Composer] Audio: {duration:.1f}s, {len(sections)} sections")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # 1. Word timestamps: TTS events (exact) or Whisper fallback
        from src.tts import to_whisper_segments as _to_segs
        if word_events:
            log.info(f"[Composer] Using TTS word events ({len(word_events)} words)")
            whisper_segments = _to_segs(word_events)
            flat_words = _all_words(whisper_segments)
            result = {"segments": whisper_segments}
        else:
            log.info("[Composer] Transcribing audio (Whisper fallback)...")
            model  = whisper.load_model(_WHISPER_MODEL)
            result = model.transcribe(
                str(audio), language="es", word_timestamps=True, verbose=False
            )
            flat_words = _all_words(result["segments"])

        # 2. Find section start timestamps
        starts = _section_starts(sections, flat_words, duration)
        tabs   = visual_plan.get("tabs", [s.get("label", "") for s in sections]) if visual_plan else [s.get("label", "") for s in sections]
        slides = visual_plan.get("slides", [{"title": s.get("title", ""), "card": {"type": "plain"}} for s in sections]) if visual_plan else [{"title": s.get("title", ""), "card": {"type": "plain"}} for s in sections]
        for i, (tab, t) in enumerate(zip(tabs, starts)):
            log.info(f"  section {i} '{tab}' starts at {t:.1f}s")

        # 3. Background video (brand frames timed to sections)
        log.info("[Composer] Generating brand frames...")
        bg = _build_bg_video(brand, topic_label, tabs, slides, starts, duration, tmp)


        # 3b. Replace last slide with the fixed CTA PNG
        import shutil as _sh
        last_idx = len(slides) - 1
        cta_src  = get_cta_png(tmp)
        _sh.copy2(cta_src, tmp / f"section_{last_idx:02d}.png")
        log.info(f"[Composer] Fixed CTA → slide {last_idx}")

        # 3c. Pixel sanity check on content slides only
        bg_rgb = brand.bg_rgb()
        for idx in range(last_idx):
            png = tmp / f"section_{idx:02d}.png"
            if png.exists():
                check = validate_frame(png, bg_rgb)
                if not check["ok"]:
                    log.warning(f"[Validator] slide {idx}: {check['issues']}")
                else:
                    log.info(f"[Validator] slide {idx}: ✓")
        # 4. Merge background + TTS audio
        av_tmp = tmp / "av.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(bg), "-i", str(audio),
                "-map", "0:v", "-map", "1:a",
                "-t", str(duration),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                str(av_tmp),
            ],
            capture_output=True,
            check=True,
        )

        # 5. Generate ASS subtitles from Whisper output
        ass_path = tmp / "subs.ass"
        subtitle_generator.generate(
            segments=result["segments"],
            clip_start=0.0,
            clip_duration=duration,
            output_path=str(ass_path),
            has_word_timestamps=True,
            style=caption_style,
        )

        # 6. Burn subtitles → final output
        log.info("[Composer] Burning subtitles...")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(av_tmp),
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
                "-c:a", "copy",
                str(out),
            ],
            capture_output=True,
            check=True,
        )

    size_mb = out.stat().st_size / 1_048_576
    log.info(f"[Composer] → {out.name} ({size_mb:.1f} MB)")
    return out
