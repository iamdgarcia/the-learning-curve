"""
Auto Hook overlay — burns an animated hook text into the first 3 seconds
of a vertical clip, just like OpusClip's hook templates.

Templates (matching OpusClip naming):
  hook-01  White bold, bottom-center, black outline (default TikTok)
  hook-02  Yellow highlight box, centered
  hook-03  ALL CAPS white, top banner with dark background
  hook-04  Gradient accent color, mid-screen bold
  hook-05  Word-by-word fade-in, white on black bar

Uses ffmpeg drawtext filter — no external deps.
"""
import subprocess
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# OpusClip accent color from their JS: "#F1C329" (gold)
ACCENT = "F1C329"

TEMPLATES = {
    "hook-01": dict(
        # Classic TikTok: white bold bottom-center
        fontsize=72, fontcolor="white", borderw=4, bordercolor="black",
        x="(w-text_w)/2", y="h*0.72",
        box=0,
    ),
    "hook-02": dict(
        # Yellow box
        fontsize=68, fontcolor="black", borderw=0,
        x="(w-text_w)/2", y="h*0.70",
        box=1, boxcolor=f"#{ACCENT}@0.95", boxborderw=20,
    ),
    "hook-03": dict(
        # Top banner
        fontsize=60, fontcolor="white", borderw=3, bordercolor="black",
        x="(w-text_w)/2", y="h*0.08",
        box=1, boxcolor="black@0.65", boxborderw=18,
    ),
    "hook-04": dict(
        # Gold accent mid-screen
        fontsize=74, fontcolor=f"#{ACCENT}", borderw=4, bordercolor="black",
        x="(w-text_w)/2", y="h*0.65",
        box=0,
    ),
    "hook-05": dict(
        # White on dark bar
        fontsize=66, fontcolor="white", borderw=0,
        x="(w-text_w)/2", y="h*0.75",
        box=1, boxcolor="black@0.75", boxborderw=22,
    ),
}


def _escape(text: str) -> str:
    """Escape text for ffmpeg drawtext."""
    return text.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")


def _wrap(text: str, max_chars: int = 28) -> str:
    """Wrap long hook text to max_chars per line."""
    words = text.split()
    lines, line = [], []
    for w in words:
        if sum(len(x) for x in line) + len(w) + len(line) > max_chars and line:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))
    return "\n".join(lines)


def burn_hook(
    input_path: str,
    output_path: str,
    hook_text: str,
    template: str = "hook-01",
    duration_s: float = 3.0,
    font_path: str | None = None,
) -> Path:
    """
    Burn hook overlay onto the first `duration_s` seconds of the clip.
    Returns output_path as Path.
    """
    cfg = TEMPLATES.get(template, TEMPLATES["hook-01"])
    text = _wrap(hook_text.upper() if template == "hook-03" else hook_text)
    escaped = _escape(text)

    # Base drawtext options
    dt_opts = [
        f"text='{escaped}'",
        f"fontsize={cfg['fontsize']}",
        f"fontcolor={cfg['fontcolor']}",
        f"x={cfg['x']}",
        f"y={cfg['y']}",
        f"borderw={cfg.get('borderw', 0)}",
        f"bordercolor={cfg.get('bordercolor', 'black')}",
        # Fade in over 0.3s, fade out over 0.3s near duration_s
        f"alpha='if(lt(t,0.3),t/0.3,if(lt(t,{duration_s-0.3}),1,({duration_s}-t)/0.3))'",
    ]
    if font_path:
        dt_opts.append(f"fontfile='{font_path}'")
    if cfg.get("box"):
        dt_opts.append("box=1")
        dt_opts.append(f"boxcolor={cfg['boxcolor']}")
        dt_opts.append(f"boxborderw={cfg['boxborderw']}")

    drawtext = "drawtext=" + ":".join(dt_opts)

    out = Path(output_path)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", drawtext,
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
        "-c:a", "copy",
        str(out),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Hook overlay failed:\n{result.stderr[-1000:]}")

    log.info(f"Hook overlay applied ({template}): {out}")
    return out
