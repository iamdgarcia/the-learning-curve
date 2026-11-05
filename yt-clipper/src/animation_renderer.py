"""
Animation renderer:
  1. Claude Code (--print --allowedTools Write) generates animated HTML
  2. Playwright records the HTML as a WebM video
  3. FFmpeg converts WebM → MP4 and merges TTS audio
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from src.brand_assets import inject_logo
from src.cta_slide import get_mp4 as get_cta_mp4
from src.subtitle_generator import generate as generate_subs, CaptionStyle

log = logging.getLogger(__name__)

_CLAUDE = Path.home() / ".local/bin/claude"
_TIMEOUT = 600  # Claude generation timeout per animation (can take up to 500s)


# ── Brief builder ─────────────────────────────────────────────────────────────

_STYLE = """
VISUAL STYLE — Substack brand palette, clean and premium:
  Background: #FAFAF9 (warm white) with 54px CSS grid lines #E8E4DC
  Primary accent: #FF6719 (Substack orange) — headers, highlights, CTA cards, arrows
  Text: #1C1B1F (near black) — titles and diagram labels
  Secondary text: #6B6B6B (gray) — subtitles, annotations
  Diagram nodes: white boxes with #1C1B1F border and #FF6719 accent glow on active
  Code/mono labels: 'Fira Code' monospace, #1C1B1F text
  UI font: 'Inter' from Google Fonts — weights 400, 600, 800, 900
  Success: #16a34a (green) — for positive results
  Error: #dc2626 (red) — for negative results
  Progress bar: thin #FF6719 strip at very bottom (y=1910-1920)
  Feel: Bloomberg Terminal meets Substack — data-dense but beautifully typeset
"""

_ANIMATION_RULES = """
ANIMATION RULES:
  - All elements start invisible (opacity:0 or display:none)
  - Use CSS transitions (opacity, transform) for reveals
  - JS setTimeout drives the timeline — every cue is a function call
  - Arrows: SVG <line> or <path> with stroke-dasharray + stroke-dashoffset animation
  - Cells/bits: flash effect when value changes (box-shadow glow)
  - Text: slide-in from left or fade-in
  - Build up: each section ADDS to previous — nothing disappears until scene change
  - Scene change: fade out old content, fade in new section header
  - Canvas: 1080×1920px, all content fits within 50px margins
  - DO NOT overflow below y=1900 (progress bar at 1910)
"""


def _build_brief(
    topic: str,
    sections: list[dict],
    channel_handle: str,
    html_path: Path,
) -> str:
    """Minimal brief — shorter = faster Claude generation (~100s vs 360s+)."""
    total = sections[-1]["end_s"] if sections else 55
    timeline = "\n".join(
        f"{s['start_s']}s-{s['end_s']}s: {s['title']} — {s['text'][:80]}"
        for s in sections
    )
    return (
        f"Create a 1080x1920px animated HTML explainer (YouTube Short, {total}s) in Spanish about: {topic}\n"
        f"Style: warm white bg #FAFAF9, 54px grid lines #E8E4DC, orange accent #FF6719, dark text #1C1B1F.\n"
        f"Inter + Fira Code fonts from Google. Diagram nodes: white boxes #1C1B1F border, orange glow on active.\n"
        f"SVG arrows in #FF6719, JS setTimeout timeline, stroke-dashoffset animations, orange flash on state changes.\n"
        f"Orange #FF6719 progress bar at y=1910-1920. {channel_handle} watermark top-right (small, #FF6719).\n"
        f"Nothing below y=1900 except progress bar.\n\n"
        f"TIMELINE:\n{timeline}\n\n"
        f"The animation ends at {total}s. Do NOT include a CTA or subscribe slide — that is added separately.\n"
        f"Write ONLY the complete self-contained HTML to: {html_path.resolve()}"
    )



# ── Claude generation ─────────────────────────────────────────────────────────

def generate_html(brief: str, html_path: Path) -> bool:
    """
    Run Claude to generate the animation HTML. Returns True on success.

    Uses Popen + file polling instead of subprocess.run() because Claude
    writes the HTML file via the Write tool and THEN prints a summary to
    stdout. subprocess.run(capture_output=True) deadlocks waiting for stdout
    while Claude's internal buffer fills. Polling for the output file avoids
    this entirely.
    """
    import tempfile as _tf, time
    brief_file = Path(_tf.mktemp(suffix=".md"))
    brief_file.write_text(brief)
    proc = None
    try:
        import threading
        with open(brief_file) as stdin_f:
            proc = subprocess.Popen(
                [str(_CLAUDE), "--print", "--dangerously-skip-permissions", "--allowedTools", "Write"],
                stdin=stdin_f,
                stdout=subprocess.PIPE,   # must be PIPE, not DEVNULL — Claude stalls on DEVNULL
                stderr=subprocess.DEVNULL,
            )
            # Drain stdout in background so the pipe buffer never fills
            threading.Thread(target=lambda: [_ for _ in proc.stdout], daemon=True).start()

            # Poll for the output file — Claude writes it before printing summary
            deadline = time.time() + _TIMEOUT
            while time.time() < deadline:
                if html_path.exists() and html_path.stat().st_size > 2000:
                    elapsed = time.time() - (deadline - _TIMEOUT)
                    log.info(f"[Anim] wrote {html_path.stat().st_size // 1024} KB in {elapsed:.0f}s")
                    proc.terminate()
                    return True
                if proc.poll() is not None:
                    break   # process exited
                time.sleep(2)

        if html_path.exists() and html_path.stat().st_size > 2000:
            log.info(f"[Anim] wrote {html_path.stat().st_size // 1024} KB")
            return True

        log.warning(f"[Anim] Claude finished but no HTML file written")
        return False

    except Exception as e:
        log.warning(f"[Anim] error: {e}")
        return False
    finally:
        brief_file.unlink(missing_ok=True)
        if proc and proc.poll() is None:
            proc.kill()


# ── Playwright recorder ───────────────────────────────────────────────────────

def record_animation(html_path: Path, duration_s: float, out_dir: Path) -> Path:
    """Record the HTML animation as WebM using Playwright. Returns WebM path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    webm_dest = out_dir / "animation.webm"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_video_dir = Path(tmp)
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            ctx = browser.new_context(
                viewport={"width": 1080, "height": 1920},
                record_video_dir=str(tmp_video_dir),
                record_video_size={"width": 1080, "height": 1920},
            )
            page = ctx.new_page()
            page.goto(
                f"file://{html_path.resolve()}",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            inject_logo(page)
            log.info(f"[Anim] Recording {duration_s:.0f}s animation...")
            page.wait_for_timeout(int(duration_s * 1000) + 500)
            ctx.close()
            browser.close()

        videos = list(tmp_video_dir.glob("*.webm"))
        if not videos:
            raise RuntimeError("Playwright produced no video file")
        shutil.move(str(videos[0]), str(webm_dest))

    log.info(f"[Anim] Recorded: {webm_dest} ({webm_dest.stat().st_size // 1024} KB)")
    return webm_dest


# ── Final assembly ────────────────────────────────────────────────────────────

def compose(
    webm_path: Path,
    audio_path: Path,
    output_path: Path,
    audio_duration: float,
    cta_start_s: float | None = None,
    word_events: list[dict] | None = None,
) -> Path:
    """
    Merge animation video + TTS audio into final MP4.
    If cta_start_s is given, trims animation there and appends the fixed CTA clip.
    """
    work = output_path.parent
    cta_duration = audio_duration - cta_start_s if cta_start_s else 0
    anim_duration = cta_start_s if cta_start_s else audio_duration
    # Use output stem as prefix so concurrent runs don't clobber each other's temp files
    pfx = output_path.stem

    # 1. Render animation part (trimmed at cta_start_s)
    anim_mp4 = work / f"{pfx}_anim_part.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(webm_path),
        "-i", str(audio_path),
        "-map", "0:v", "-map", "1:a",
        "-t", str(anim_duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        str(anim_mp4),
    ], check=True, capture_output=True)

    if not cta_start_s:
        anim_mp4.rename(output_path)
        log.info(f"[Anim] Final: {output_path} ({output_path.stat().st_size // 1024} KB)")
        return output_path

    # 2. Fixed CTA clip with matching audio tail
    cta_clip = get_cta_mp4(work, duration_s=max(3.0, cta_duration))

    # Extract audio tail for CTA
    cta_audio = work / f"{pfx}_cta_audio.aac"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(audio_path),
        "-ss", str(cta_start_s), "-t", str(cta_duration),
        "-c:a", "aac", "-b:a", "192k",
        str(cta_audio),
    ], check=True, capture_output=True)

    # Mux CTA video + CTA audio
    cta_with_audio = work / f"{pfx}_cta_with_audio.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(cta_clip), "-i", str(cta_audio),
        "-map", "0:v", "-map", "1:a",
        "-t", str(cta_duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        str(cta_with_audio),
    ], check=True, capture_output=True)

    # 3. Concat animation + CTA
    concat_list = work / f"{pfx}_concat.txt"
    concat_list.write_text(f"file '{anim_mp4.resolve()}'\nfile '{cta_with_audio.resolve()}'")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(output_path),
    ], check=True, capture_output=True)

    # Cleanup temp files
    for f in [anim_mp4, cta_audio, cta_with_audio, concat_list]:
        f.unlink(missing_ok=True)

    # ── Subtitles: use TTS word events (exact) or fall back to Whisper ──
    from src.tts import to_whisper_segments
    sub_dur = cta_start_s if cta_start_s else audio_duration
    ass     = output_path.with_suffix(".ass")

    if word_events:
        log.info(f"[Anim] Subtitles from TTS word events ({len(word_events)} words)")
        segments = to_whisper_segments(word_events)
    else:
        log.info("[Anim] Transcribing for subtitles (Whisper fallback)...")
        import whisper as _whisper
        model    = _whisper.load_model("small")
        result   = model.transcribe(str(audio_path), language="es", word_timestamps=True, verbose=False)
        segments = result["segments"]

    generate_subs(
        segments            = segments,
        clip_start          = 0.0,
        clip_duration       = sub_dur,
        output_path         = str(ass),
        has_word_timestamps = True,
        style               = CaptionStyle.karaoke,
    )
    subbed = output_path.with_suffix(".subbed.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(output_path),
        "-vf", f"ass={ass}",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
        "-c:a", "copy",
        str(subbed),
    ], check=True, capture_output=True)
    output_path.unlink()
    subbed.rename(output_path)
    ass.unlink(missing_ok=True)
    log.info(f"[Anim] Final: {output_path} ({output_path.stat().st_size // 1024} KB)")
    return output_path


# ── Public API ────────────────────────────────────────────────────────────────

def render(
    topic: str,
    sections: list[dict],
    audio_path: Path,
    audio_duration: float,
    output_path: Path,
    channel_handle: str = "@TheLearningCurveAI",
    work_dir: Path | None = None,
    cta_start_s: float | None = None,
    word_events: list[dict] | None = None,
) -> Path:
    """End-to-end: generate HTML → record → merge audio → MP4."""
    work = work_dir or output_path.parent / "anim_work"
    work.mkdir(parents=True, exist_ok=True)
    html_path = work / "animation.html"

    # Build brief using only the non-CTA sections
    content_sections = [s for s in sections if s.get("start_s", 0) < (cta_start_s or audio_duration)]
    brief = _build_brief(topic, content_sections, channel_handle, html_path)
    ok = generate_html(brief, html_path)
    if not ok:
        raise RuntimeError("Claude failed to generate animation HTML")

    webm = record_animation(html_path, (cta_start_s or audio_duration) + 1, work)
    return compose(webm, audio_path, output_path, audio_duration,
                   cta_start_s=cta_start_s, word_events=word_events)
