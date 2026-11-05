"""
Download a clip segment via yt-dlp, convert to 9:16 vertical,
detect silence (reject dead segments), transcribe clip audio with Whisper
for frame-accurate subtitles, then burn TikTok-style captions.
"""
import re
import subprocess
import logging
import shutil
import tempfile
from pathlib import Path

from src import frame_analyzer
from src.subtitle_generator import CaptionStyle
import src.subtitle_generator as subtitle_generator
from src import speaker_diarizer, hook_overlay, audio_enhancer, broll_inserter

log = logging.getLogger(__name__)

PADDING      = 10     # seconds padded on each side for precise trim
TARGET_W     = 1080
TARGET_H     = 1920
FACE_RATIO   = 0.38   # fraction of height for face panel

# Silence rejection: if >40% of clip is silent (≥-35dB for ≥1.5s stretches), reject
SILENCE_DB   = -35
SILENCE_DUR  = 1.5    # minimum silence stretch (seconds)
SILENCE_MAX  = 0.40   # max fraction of clip allowed to be silent

_YTDLP = shutil.which("yt-dlp") or None
_NODE  = shutil.which("node") or ""


# ── helpers ────────────────────────────────────────────────────────────────────

def _ytdlp_cmd() -> list[str]:
    base = [_YTDLP] if _YTDLP else ["python", "-m", "yt_dlp"]
    return base + [
        "--no-update",
        "--cookies-from-browser", "firefox",
        "--no-js-runtimes",
        *(["--js-runtimes", f"node:{_NODE}"] if _NODE else []),
    ]


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed:\n{result.stderr[-2000:]}")
    return result.stderr  # ffmpeg writes info to stderr


def _check_silence(tmp: Path, trim_offset: int, duration: int) -> None:
    """Raise RuntimeError if the clip contains too much silence."""
    result = subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(trim_offset), "-t", str(duration),
        "-i", str(tmp),
        "-af", f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_DUR}",
        "-f", "null", "-",
    ], capture_output=True, text=True)

    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", result.stderr)]
    ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", result.stderr)]

    # If a silence_start has no matching end, the silence extends to clip end
    total_silence = 0.0
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration
        total_silence += max(0.0, e - s)

    ratio = total_silence / duration
    if ratio > SILENCE_MAX:
        raise RuntimeError(
            f"Clip contains {ratio:.0%} silence ({total_silence:.1f}s / {duration}s) — "
            "likely dead air or stream exit. Skipping."
        )
    if total_silence > 0:
        log.info(f"Silence check OK: {total_silence:.1f}s silent ({ratio:.0%})")


def _transcribe_clip(tmp: Path, trim_offset: int, duration: int, language: str | None) -> list[dict]:
    """
    Extract clip audio from tmp and run Whisper on it.
    Returns Whisper segments with timestamps relative to clip start (0..duration).
    """
    import whisper
    audio = tmp.with_suffix(".clip_audio.mp3")
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(trim_offset), "-t", str(duration),
        "-i", str(tmp),
        "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "libmp3lame", "-q:a", "5",
        str(audio),
    ], check=True, capture_output=True)

    log.info("Transcribing clip audio for subtitles...")
    model = whisper.load_model("small")
    lang  = language.split("-")[0] if language else None
    res   = model.transcribe(str(audio), language=lang, word_timestamps=True, verbose=False)
    audio.unlink(missing_ok=True)
    return res["segments"]


# ── ffmpeg filters ─────────────────────────────────────────────────────────────

def _screen_zoom_crop(screen: "frame_analyzer.Region", screen_h_out: int,
                       act_cx: int, act_cy: int) -> "frame_analyzer.Region":
    """
    Compute a zoom crop of the screen region centered on (act_cx, act_cy).
    Output aspect ratio must match TARGET_W : screen_h_out.
    Crop is in ABSOLUTE frame coordinates. All dimensions forced even for libx264.
    """
    crop_h = screen.h & ~1
    crop_w = int(crop_h * TARGET_W / screen_h_out) & ~1
    crop_w = min(crop_w, screen.w & ~1)

    if crop_w == (screen.w & ~1):
        crop_h = int(crop_w * screen_h_out / TARGET_W) & ~1
        crop_h = min(crop_h, screen.h & ~1)

    zoom = screen.w / crop_w
    log.info(f"Screen zoom: {zoom:.2f}x ({crop_w}x{crop_h} crop → {TARGET_W}x{screen_h_out})")

    # Center crop on activity, clamped to screen bounds
    cx_abs = screen.x + act_cx
    cy_abs = screen.y + act_cy
    x = max(screen.x, min(screen.x + screen.w - crop_w, cx_abs - crop_w // 2))
    y = max(screen.y, min(screen.y + screen.h - crop_h, cy_abs - crop_h // 2))

    from src.frame_analyzer import Region
    return Region(x=x, y=y, w=crop_w, h=crop_h)


def _build_vf(layout: "frame_analyzer.LayoutResult", trim_offset: int, duration: int,
              aspect: str = "9:16") -> tuple[str, list[str]]:
    face   = layout.face
    screen = layout.screen
    trim   = f"trim=start={trim_offset}:duration={duration},setpts=PTS-STARTPTS"

    # ── Aspect ratio helpers ────────────────────────────────────────────────
    if aspect == "1:1":
        # Square: 1080×1080, center-crop on face or activity
        OUT_W = OUT_H = 1080
        fw, fh = layout.frame_w, layout.frame_h
        cx = (layout.screen.x + (layout.activity_cx if layout.activity_cx >= 0 else layout.screen.w // 2))
        cy = fh // 2
        crop_sz = min(fw, fh) & ~1
        crop_x  = max(0, min(fw - crop_sz, cx - crop_sz // 2)) & ~1
        crop_y  = max(0, min(fh - crop_sz, cy - crop_sz // 2)) & ~1
        vf = (
            f"[0:v]{trim},"
            f"crop={crop_sz}:{crop_sz}:{crop_x}:{crop_y},"
            f"scale={OUT_W}:{OUT_H}[v]"
        )
        return vf, ["-map", "[v]", "-map", "0:a"]

    if aspect == "16:9":
        # Keep landscape, just trim precisely — no reframing needed
        fw, fh = layout.frame_w, layout.frame_h
        vf = f"[0:v]{trim},scale={fw & ~1}:{fh & ~1}[v]"
        return vf, ["-map", "[v]", "-map", "0:a"]

    # ── Default: 9:16 vertical split ────────────────────────────────────────
    if face:
        face_h   = int(TARGET_H * FACE_RATIO) & ~1
        screen_h = TARGET_H - face_h
        f = face

        act_cx = layout.activity_cx if layout.activity_cx >= 0 else screen.w // 2
        act_cy = layout.activity_cy if layout.activity_cy >= 0 else screen.h // 2
        zoom = _screen_zoom_crop(screen, screen_h, act_cx, act_cy)

        vf = (
            f"[0:v]{trim},"
            f"crop={f.w}:{f.h}:{f.x}:{f.y},"
            f"scale={TARGET_W}:{TARGET_W},"
            f"crop={TARGET_W}:{face_h}:0:(ih-{face_h})/2[top];"

            f"[0:v]{trim},"
            f"crop={zoom.w}:{zoom.h}:{zoom.x}:{zoom.y},"
            f"scale={TARGET_W}:{screen_h}"
            f"[bottom];"

            f"[top][bottom]vstack=inputs=2[v]"
        )
        map_args = ["-map", "[v]", "-map", "0:a"]
    else:
        fw, fh = layout.frame_w, layout.frame_h
        crop_w = int(fh * TARGET_W / TARGET_H) & ~1
        crop_x = max(0, (fw - crop_w) // 2) & ~1
        vf = (
            f"[0:v]{trim},"
            f"crop={crop_w}:{fh & ~1}:{crop_x}:0,"
            f"scale={TARGET_W}:{TARGET_H}[v]"
        )
        map_args = ["-map", "[v]", "-map", "0:a"]

    return vf, map_args


# ── public API ─────────────────────────────────────────────────────────────────

def cut(
    video_url: str,
    start_seconds: int,
    end_seconds: int,
    output_path: str,
    language: str = "es",
    transcript_segments: list | None = None,
    has_word_timestamps: bool = False,
    caption_style: CaptionStyle = CaptionStyle.karaoke,
    aspect: str = "9:16",
    # New OpusClip-equivalent features
    enhance_audio: bool = False,
    hook_text: str = "",
    hook_template: str = "hook-01",
    diarize: bool = False,
    broll: bool = False,
    clip_transcript_text: str = "",
    pexels_key: str = "",
) -> Path:
    duration     = end_seconds - start_seconds
    padded_start = max(0, start_seconds - PADDING)
    padded_end   = end_seconds + PADDING
    trim_offset  = start_seconds - padded_start

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.mp4")

    log.info(f"Cutting {start_seconds}s–{end_seconds}s ({duration}s) → {output_path}")

    # 1. Download — HTTPS first (best quality), HLS fallback
    lang = language.split("-")[0]
    https_fmt = (
        f"bestvideo[ext=mp4]+bestaudio[language^={lang}][ext=m4a]"
        f"/bestvideo[ext=mp4]+bestaudio[ext=m4a]"
        f"/bestvideo[ext=mp4]+bestaudio"
    )
    hls_fmt = (
        f"bestvideo[protocol^=m3u8]+bestaudio[language^={lang}][protocol^=m3u8]"
        f"/bestvideo[protocol^=m3u8]+bestaudio[language^={lang}]"
        f"/bestvideo[protocol^=m3u8]+bestaudio/best"
    )
    dl_base = _ytdlp_cmd() + [
        "--download-sections", f"*{padded_start}-{padded_end}",
        "--force-keyframes-at-cuts",
        "--merge-output-format", "mp4",
        "-o", str(tmp), "--no-playlist", "--no-warnings",
    ]
    try:
        _run(dl_base + ["-f", https_fmt, video_url])
        log.info("Downloaded via HTTPS")
    except RuntimeError:
        log.warning("HTTPS failed — retrying with HLS")
        tmp.unlink(missing_ok=True)
        _run(dl_base + ["-f", hls_fmt, video_url])
        log.info("Downloaded via HLS")

    if not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file missing or empty: {tmp}")

    # 2. Silence check — reject dead air / stream exits
    _check_silence(tmp, trim_offset, duration)

    # 3. Detect face/screen layout
    log.info("Analyzing frame layout...")
    layout = frame_analyzer.analyze(str(tmp), offset_s=trim_offset)

    # 4a. Audio enhancement (noise reduction)
    if enhance_audio:
        try:
            enhanced_tmp = tmp.with_suffix(".enh.mp4")
            audio_enhancer.enhance(str(tmp), str(enhanced_tmp))
            tmp.unlink(missing_ok=True)
            tmp = enhanced_tmp
            log.info("Audio enhanced")
        except Exception as e:
            log.warning(f"Audio enhancement failed ({e}) — continuing without")

    # 4b. Convert to target aspect ratio
    vertical_tmp = out.with_suffix(".v.mp4")
    vf, map_args = _build_vf(layout, trim_offset, duration, aspect=aspect)
    _run([
        "ffmpeg", "-y", "-i", str(tmp),
        "-filter_complex", vf, *map_args,
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),   # truncate ALL streams to exact clip duration
        str(vertical_tmp),
    ])
    tmp.unlink(missing_ok=True)

    # 5. Speaker diarization
    speaker_segs = []
    if diarize:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as af:
                audio_tmp = Path(af.name)
            subprocess.run([
                "ffmpeg", "-y", "-i", str(vertical_tmp),
                "-vn", "-c:a", "libmp3lame", "-q:a", "5", str(audio_tmp)
            ], capture_output=True)
            speaker_segs = speaker_diarizer.diarize(str(audio_tmp))
            audio_tmp.unlink(missing_ok=True)
        except Exception as e:
            log.warning(f"Diarization failed ({e})")

    # 6. Whisper on clip audio → frame-accurate subtitles
    try:
        clip_segs = _transcribe_clip(vertical_tmp, 0, duration, language)
        ass_path  = out.with_suffix(".ass")
        subtitle_generator.generate(
            segments=clip_segs,
            clip_start=0.0,
            clip_duration=float(duration),
            output_path=str(ass_path),
            has_word_timestamps=True,
            style=caption_style,
            speaker_segments=speaker_segs if speaker_segs else None,
        )
        log.info("Burning subtitles...")
        sub_out = out.with_suffix(".sub.mp4")
        _run([
            "ffmpeg", "-y", "-i", str(vertical_tmp),
            "-vf", f"ass={ass_path}",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-b:v", "4M", "-maxrate", "6M", "-bufsize", "8M",
            "-c:a", "copy", str(sub_out),
        ])
        vertical_tmp.unlink(missing_ok=True)
        ass_path.unlink(missing_ok=True)
        vertical_tmp = sub_out
    except Exception as e:
        log.warning(f"Subtitle generation failed ({e}) — continuing without")

    # 7. Auto hook overlay (first 3s)
    if hook_text:
        try:
            hook_out = out.with_suffix(".hook.mp4")
            hook_overlay.burn_hook(
                str(vertical_tmp), str(hook_out),
                hook_text=hook_text,
                template=hook_template,
                duration_s=3.0,
            )
            vertical_tmp.unlink(missing_ok=True)
            vertical_tmp = hook_out
            log.info(f"Hook overlay applied: {hook_template}")
        except Exception as e:
            log.warning(f"Hook overlay failed ({e})")

    # 8. B-roll insertion
    if broll and pexels_key and clip_transcript_text:
        try:
            broll_out = out.with_suffix(".broll.mp4")
            broll_inserter.insert_broll(
                str(vertical_tmp), str(broll_out),
                clip_text=clip_transcript_text,
                hook=hook_text,
                pexels_key=pexels_key,
            )
            vertical_tmp.unlink(missing_ok=True)
            vertical_tmp = broll_out
            log.info("B-roll inserted")
        except Exception as e:
            log.warning(f"B-roll insertion failed ({e})")

    # Final output
    vertical_tmp.rename(out)

    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"Output file missing or empty: {out}")

    log.info(f"Vertical clip saved: {out} ({out.stat().st_size // 1024} KB)")
    return out
