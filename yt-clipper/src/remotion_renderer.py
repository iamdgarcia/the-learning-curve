"""
Remotion renderer for Pipeline C.
Claude Code writes a React/Remotion component → `npx remotion render` → FFmpeg muxes audio + subs.

Style: animated whiteboard / hand-drawn sketchy cards using Remotion + Rough.js.
Great for software architecture, flow diagrams, and 3Blue1Brown-lite explanations in React.

Remotion rules (from `npx skills add remotion`):
  - Use useCurrentFrame() + interpolate() for all motion — no CSS transitions
  - Spring physics for entrances: spring({ fps, frame, config: { damping: 12 } })
  - Each section = one <Sequence from={...} durationInFrames={...}> block
  - Canvas: 1080×1920 (9:16 portrait), fps=30
  - Rough.js for sketchy shapes; Tailwind or inline styles for colour
"""
from __future__ import annotations
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

_CLAUDE = "claude"
_TIMEOUT_S = 600   # Remotion scaffold + React can be large


def _scaffold_project(work_dir: Path) -> Path:
    """Create a minimal Remotion project if not already present."""
    pkg = work_dir / "package.json"
    if pkg.exists():
        return work_dir
    log.info("[Remotion] Scaffolding project...")
    subprocess.run(["npm", "init", "-y"], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(
        ["npm", "install", "--save-exact",
         "remotion", "@remotion/cli", "react", "react-dom", "roughjs"],
        cwd=work_dir, check=True, capture_output=True,
    )
    # Minimal remotion.config.ts
    (work_dir / "remotion.config.ts").write_text(
        "import { Config } from '@remotion/cli/config';\n"
        "Config.setVideoImageFormat('jpeg');\n"
        "Config.setCodec('h264');\n"
    )
    (work_dir / "tsconfig.json").write_text(
        '{"compilerOptions":{"lib":["dom","esnext"],"jsx":"react",'
        '"moduleResolution":"node","target":"esnext","module":"commonjs",'
        '"esModuleInterop":true,"strict":true,"skipLibCheck":true}}'
    )
    return work_dir


def _build_brief(topic: str, sections: list[dict], channel_handle: str,
                 comp_path: Path, fps: int = 30) -> str:
    section_lines = "\n".join(
        f"  - [{s['start_s']}s–{s['end_s']}s] {s['title']}: {s['text']}"
        for s in sections
    )
    total_frames = int(sections[-1]["end_s"] * fps) if sections else 1650
    return f"""Write a Remotion React animation for a 9:16 vertical YouTube Short about: "{topic}"

Output file: {comp_path}
FPS: {fps}, canvas: 1080×1920, totalFrames: {total_frames}

SECTIONS (match timing):
{section_lines}

REMOTION RULES (follow strictly):
1. Single file exporting a default React component `ExplainerComp` and a `compositionConfig` object.
2. compositionConfig = {{ id: "Explainer", component: ExplainerComp, durationInFrames: {total_frames}, fps: {fps}, width: 1080, height: 1920 }}
3. Use useCurrentFrame() + interpolate() for ALL motion — no CSS transitions or keyframes.
4. Spring physics for entrances: spring({{ fps, frame: f - startFrame, config: {{ damping: 12 }} }}).
5. Each section = <Sequence from={{startFrame}} durationInFrames={{dur}}> wrapper.
6. Rough.js for sketchy/hand-drawn shapes (import rc from 'roughjs/bin/rough').
7. Colour palette: accent=#FF6719 (TLC orange), background=#1C1B1F (near-black), text=white.
8. Channel handle "{channel_handle}" fixed bottom-right, fontSize 22, opacity 0.6.
9. No external images. All shapes via Rough.js SVG or inline React divs.
10. Export: `export default ExplainerComp; export {{ compositionConfig }};`

Write ONLY the TypeScript/TSX file. No explanations."""


def _generate_component(brief: str, comp_path: Path) -> bool:
    """Ask Claude Code to write the Remotion component via stdin+Popen (avoids deadlock)."""
    import tempfile, threading, time
    brief_file = Path(tempfile.mktemp(suffix=".md"))
    brief_file.write_text(f"{brief}\n\nWrite the file to: {comp_path}")
    proc = None
    try:
        with open(brief_file) as stdin_f:
            proc = subprocess.Popen(
                [_CLAUDE, "--print", "--dangerously-skip-permissions", "--allowedTools", "Write"],
                stdin=stdin_f, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                cwd=comp_path.parent,
            )
            threading.Thread(target=lambda: [_ for _ in proc.stdout], daemon=True).start()
            deadline = time.time() + _TIMEOUT_S
            while time.time() < deadline:
                if comp_path.exists() and comp_path.stat().st_size > 500:
                    log.info(f"[Remotion] Component written: {comp_path.stat().st_size // 1024}KB")
                    proc.terminate()
                    return True
                if proc.poll() is not None:
                    break
                time.sleep(2)
        if comp_path.exists() and comp_path.stat().st_size > 500:
            return True
        log.warning("[Remotion] Claude finished but no component file written")
        return False
    except Exception as e:
        log.warning(f"[Remotion] error: {e}")
        return False
    finally:
        brief_file.unlink(missing_ok=True)
        if proc and proc.poll() is None:
            proc.terminate()


def _write_index(work_dir: Path, comp_path: Path):
    """Write the Remotion entry-point index.tsx that registers the composition."""
    (work_dir / "src" / "index.tsx").write_text(
        "import { registerRoot, Composition } from 'remotion';\n"
        "import { compositionConfig, default as Comp } from './ExplainerComp';\n"
        "registerRoot(() => (\n"
        "  <Composition\n"
        "    {...compositionConfig}\n"
        "    component={Comp}\n"
        "  />\n"
        "));\n"
    )


def _render_component(work_dir: Path, output: Path, fps: int = 30) -> Path | None:
    """Run `npx remotion render` and return the output MP4 path."""
    try:
        subprocess.run(
            ["npx", "remotion", "render", "src/index.tsx", "Explainer", str(output),
             f"--fps={fps}", "--codec=h264"],
            check=True, cwd=work_dir, capture_output=True,
        )
        if output.exists():
            log.info(f"[Remotion] Rendered: {output}")
            return output
        log.error("[Remotion] Output file not found after render")
        return None
    except subprocess.CalledProcessError as e:
        log.error(f"[Remotion] render failed: {e.stderr[-500:]}")
        return None
    except FileNotFoundError:
        log.error("[Remotion] `npx` not found — install Node.js")
        return None


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
    """End-to-end: scaffold Remotion → Claude writes component → render → mux audio → MP4."""
    work = work_dir or output_path.parent / "remotion_work"
    work.mkdir(parents=True, exist_ok=True)
    (work / "src").mkdir(exist_ok=True)

    _scaffold_project(work)

    comp_path = work / "src" / "ExplainerComp.tsx"
    content_sections = [s for s in sections if s.get("start_s", 0) < (cta_start_s or audio_duration)]
    brief = _build_brief(topic, content_sections, channel_handle, comp_path)

    ok = _generate_component(brief, comp_path)
    if not ok:
        raise RuntimeError("Claude failed to generate Remotion component")

    _write_index(work, comp_path)

    raw_video = work / "raw_animation.mp4"
    result = _render_component(work, raw_video)
    if not result:
        raise RuntimeError("Remotion render failed — check logs above")

    from src.animation_renderer import compose
    return compose(raw_video, audio_path, output_path, audio_duration,
                   cta_start_s=cta_start_s, word_events=word_events or [], narration=narration)
