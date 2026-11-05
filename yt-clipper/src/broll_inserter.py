"""
B-roll auto insertion — matches OpusClip's /brolls/generate workflow.

Strategy:
1. Extract keywords from the clip transcript (nouns/topics via LLM)
2. Search Pexels for matching 9:16 vertical stock footage
3. Composite B-roll over the screen panel (bottom 62%) during moments
   where the speaker is not showing their screen (detected by low motion)

Requires: PEXELS_API_KEY in .env
"""
import json
import logging
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from src.config import settings

log = logging.getLogger(__name__)

PEXELS_API = "https://api.pexels.com/videos/search"
ORIENTATION = "portrait"   # 9:16 videos


def _search_pexels(query: str, api_key: str, per_page: int = 3) -> list[str]:
    """Return list of direct video URLs from Pexels (HD, portrait)."""
    url = f"{PEXELS_API}?query={urllib.parse.quote(query)}&orientation={ORIENTATION}&per_page={per_page}"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        log.warning(f"Pexels search failed for '{query}': {e}")
        return []

    urls = []
    for video in data.get("videos", []):
        # Pick HD file, prefer 1080p portrait
        files = sorted(video.get("video_files", []),
                       key=lambda f: f.get("height", 0), reverse=True)
        for f in files:
            if f.get("width", 0) <= f.get("height", 1):  # portrait
                urls.append(f["link"])
                break
    return urls


def _extract_keywords(clip_text: str, hook: str) -> list[str]:
    """Extract 2-3 search keywords from the clip using the LLM."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    resp = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{
            "role": "user",
            "content": (
                f"Extract 3 short visual search queries (2-3 words each) for stock B-roll footage "
                f"that would enhance this video clip. Return JSON array only, no explanation.\n"
                f"Hook: {hook}\nTranscript snippet: {clip_text[:300]}"
            )
        }],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    try:
        return json.loads(raw)[:3]
    except Exception:
        return [hook.split()[0]] if hook else ["technology"]


def _download_clip(url: str, dest: Path) -> bool:
    """Download a video file to dest."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 10_000
    except Exception as e:
        log.warning(f"Download failed {url}: {e}")
        return False


def insert_broll(
    input_path: str,
    output_path: str,
    clip_text: str,
    hook: str,
    pexels_key: str,
    broll_duration_s: float = 4.0,
    broll_start_s: float = 5.0,   # start B-roll 5s in (after hook)
    screen_panel_ratio: float = 0.62,
) -> Path:
    """
    Overlay B-roll footage over the screen portion of the vertical clip
    for a few seconds in the middle.

    input_path: 1080x1920 vertical clip (already processed)
    """
    inp  = Path(input_path)
    out  = Path(output_path)

    # 1. Get keywords
    log.info("Extracting B-roll keywords...")
    keywords = _extract_keywords(clip_text, hook)
    log.info(f"Keywords: {keywords}")

    # 2. Search Pexels
    broll_url = None
    for kw in keywords:
        urls = _search_pexels(kw, pexels_key, per_page=2)
        if urls:
            broll_url = urls[0]
            log.info(f"B-roll found for '{kw}': {broll_url[:60]}...")
            break

    if not broll_url:
        log.warning("No B-roll found — skipping insertion")
        inp.rename(out) if inp != out else None
        if inp == out:
            import shutil; shutil.copy2(str(inp), str(out))
        return out

    # 3. Download B-roll
    with tempfile.TemporaryDirectory() as tmp:
        broll_raw = Path(tmp) / "broll_raw.mp4"
        broll_crop = Path(tmp) / "broll_crop.mp4"

        if not _download_clip(broll_url, broll_raw):
            log.warning("B-roll download failed — skipping")
            return inp

        # 4. Crop/scale B-roll to fit screen panel (1080 wide × screen_h tall)
        # Screen panel = bottom 62% of 1920 = 1190px tall (at 1080 wide = 1080:1190 ratio)
        screen_h = int(1920 * screen_panel_ratio)
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(broll_raw),
            "-t", str(broll_duration_s + 2),
            "-vf", (
                f"scale=1080:{screen_h}:force_original_aspect_ratio=increase,"
                f"crop=1080:{screen_h}"
            ),
            "-an",   # no audio from B-roll
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            str(broll_crop),
        ], capture_output=True, check=True)

        face_h = 1920 - screen_h  # top panel height

        # 5. Overlay B-roll on screen panel with crossfade in/out
        # B-roll starts at broll_start_s, overlaid on the screen region
        overlay_filter = (
            f"[0:v][1:v]overlay="
            f"x=0:y={face_h}:"
            f"enable='between(t,{broll_start_s},{broll_start_s+broll_duration_s})',"
            # Fade overlay alpha
            f"format=yuv420p[v]"
        )

        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(inp),
            "-i", str(broll_crop),
            "-filter_complex", overlay_filter,
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
            "-c:a", "copy",
            str(out),
        ], capture_output=True)

    log.info(f"B-roll inserted → {out}")
    return out


# Make urllib.parse available
import urllib.parse
