"""
Manim renderer for Pipeline C.
Claude Code writes a Manim Python scene → `manim -qh` renders it → FFmpeg muxes audio + subtitles.

Style: 3Blue1Brown / mathematical, clean dark background, animated arrows and diagrams.
Manim visual rules (from manim-skill / manim-video):
  - Opacity layering: fade out previous objects before introducing new ones (avoid clutter)
  - Monospace font for code/labels (prevents Pango kerning bugs)
  - Each logical beat = one Scene subclass; use construct() with self.play() / self.wait()
  - Colour palette: TLC orange #FF6719 as accent, WHITE text, BLACK background
"""
from __future__ import annotations
import logging
import os
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

_CLAUDE = "claude"
_TIMEOUT_S = 480


def _build_brief(topic: str, sections: list[dict], channel_handle: str, out_path: Path) -> str:
    section_lines = "\n".join(
        f"  - [{s['start_s']}s–{s['end_s']}s] {s['title']}: {s['text']}"
        for s in sections
    )
    return f"""Write a Manim Python animation for a 9:16 vertical YouTube Short about: "{topic}"

Output file: {out_path}

SECTIONS (match timing exactly):
{section_lines}

MANIM RULES (follow strictly):
1. Single file, single Scene class named `ExplainerScene`.
2. Canvas: config.frame_width=9, config.frame_height=16 (portrait 9:16).
3. Colour palette: accent=#FF6719 (TLC orange), text=WHITE, bg=BLACK.
4. Opacity discipline: FadeOut previous objects before next section — never stack clutter.
5. Monospace font (Courier New or Consolas) for any code or technical labels.
6. Use self.play(Write(title)), self.wait(section_duration), self.play(FadeOut(...)).
7. Each section = one visual beat with its own objects; reuse as little as possible.
8. No external images or assets — pure Manim primitives (Text, MathTex, Arrow, Rectangle, Circle, VGroup).
9. Channel handle "{channel_handle}" in small text bottom-right, opacity 0.6, stays for the whole animation.
10. Total duration must match the sum of section durations.

Write ONLY the Python file. No explanations. Start with `from manim import *`."""


def _generate_scene(brief: str, scene_path: Path) -> bool:
    """Ask Claude Code to write the Manim scene via stdin+Popen (avoids deadlock on large output)."""
    import tempfile, threading, time
    brief_file = Path(tempfile.mktemp(suffix=".md"))
    brief_file.write_text(f"{brief}\n\nWrite the file to: {scene_path}")
    proc = None
    try:
        with open(brief_file) as stdin_f:
            proc = subprocess.Popen(
                [_CLAUDE, "--print", "--dangerously-skip-permissions", "--allowedTools", "Write"],
                stdin=stdin_f, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                cwd=scene_path.parent,
            )
            threading.Thread(target=lambda: [_ for _ in proc.stdout], daemon=True).start()
            deadline = time.time() + _TIMEOUT_S
            while time.time() < deadline:
                if scene_path.exists() and scene_path.stat().st_size > 500:
                    log.info(f"[Manim] Scene written: {scene_path.stat().st_size // 1024}KB")
                    proc.terminate()
                    return True
                if proc.poll() is not None:
                    break
                time.sleep(2)
        if scene_path.exists() and scene_path.stat().st_size > 500:
            return True
        log.warning("[Manim] Claude finished but no scene file written")
        return False
    except Exception as e:
        log.warning(f"[Manim] error: {e}")
        return False
    finally:
        brief_file.unlink(missing_ok=True)
        if proc and proc.poll() is None:
            proc.terminate()


def _render_scene(scene_path: Path, work_dir: Path) -> Path | None:
    """Run `manim -qh scene.py ExplainerScene` and return the output MP4 path."""
    try:
        subprocess.run(
            ["manim", "-qh", "--media_dir", "media",
             scene_path.name, "ExplainerScene"],
            check=True, capture_output=True, cwd=work_dir,
        )
        # Manim outputs to media/videos/<stem>/1080p60/<ClassName>.mp4
        matches = list((work_dir.resolve() / "media").rglob("ExplainerScene.mp4"))
        if matches:
            log.info(f"[Manim] Rendered: {matches[0]}")
            return matches[0]
        log.error("[Manim] Rendered file not found after manim run")
        return None
    except subprocess.CalledProcessError as e:
        log.error(f"[Manim] manim failed: {e.stderr[-500:]}")
        return None
    except FileNotFoundError:
        log.error("[Manim] `manim` not installed — run: pip install manim")
        return None


def _mux(video: Path, audio: Path, output: Path, duration: float,
         cta_start_s: float | None, word_events: list[dict], narration: str = "") -> Path:
    """Mux Manim video + audio, trim at cta_start_s, burn karaoke subtitles via FFmpeg."""
    from src.animation_renderer import compose
    return compose(video, audio, output, duration,
                   cta_start_s=cta_start_s, word_events=word_events, narration=narration)


def render(
    topic: str,
    sections: list[dict],
    audio_path: Path,
    audio_duration: float,
    output_path: Path,
    channel_handle: str = "",
    work_dir: Path | None = None,
    cta_start_s: float | None = None,
    word_events: list[dict] | None = None,
    narration: str = "",
) -> Path:
    """End-to-end: generate Manim scene → render → mux audio → MP4."""
    work = work_dir or output_path.parent / "manim_work"
    work.mkdir(parents=True, exist_ok=True)
    scene_path = work / "scene.py"

    content_sections = [s for s in sections if s.get("start_s", 0) < (cta_start_s or audio_duration)]
    brief = _build_brief(topic, content_sections, channel_handle, scene_path)

    ok = _generate_scene(brief, scene_path)
    if not ok:
        raise RuntimeError("Claude failed to generate Manim scene")

    raw_video = _render_scene(scene_path, work)
    if not raw_video:
        raise RuntimeError("manim render failed — check logs above")

    return _mux(raw_video, audio_path, output_path, audio_duration,
                cta_start_s, word_events or [], narration=narration)
