import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

log = logging.getLogger(__name__)

_YTDLP = shutil.which("yt-dlp") or None
_NODE  = shutil.which("node") or ""


def parse_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    qs = parse_qs(parsed.query)
    if "v" in qs:
        return qs["v"][0]
    raise ValueError(f"Cannot parse video ID from URL: {url}")


def _detect_language(url: str) -> str | None:
    """Ask yt-dlp for the video's declared language tag (e.g. 'es-US', 'en')."""
    cmd = [_YTDLP] if _YTDLP else ["python", "-m", "yt_dlp"]
    cmd += [
        "--no-download", "--no-update",
        "--cookies-from-browser", "firefox",
        "--no-js-runtimes",
        *(["--js-runtimes", f"node:{_NODE}"] if _NODE else []),
        "--print", "%(language)s",
        url,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
        # language tag may be "es-US", "es", "en", etc. — take the base
        return out.split("-")[0] if out and out != "None" else None
    except Exception:
        return None


def fetch_transcript(video_id: str, preferred_lang: str | None = None) -> tuple[list, str]:
    """
    Returns (snippets, language_code).
    Tries preferred_lang first, then manual transcripts, then all auto-generated.
    """
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except TranscriptsDisabled:
        raise RuntimeError(f"Transcripts are disabled for video {video_id}.")

    all_transcripts = list(transcript_list)
    if not all_transcripts:
        raise RuntimeError(f"No transcripts available for video {video_id}.")

    # 1. Preferred language (original video language) — any kind
    if preferred_lang:
        matches = [t for t in all_transcripts if t.language_code.startswith(preferred_lang)]
        if matches:
            t = matches[0]
            log.info(f"Using transcript: {t.language_code} ({t.language})")
            return t.fetch().snippets, t.language_code

    # 2. Manual transcripts in any language
    manual = [t for t in all_transcripts if not t.is_generated]
    if manual:
        t = manual[0]
        log.info(f"Using manual transcript: {t.language_code} ({t.language})")
        return t.fetch().snippets, t.language_code

    # 3. Fallback: first auto-generated
    t = all_transcripts[0]
    log.warning(f"Falling back to first available: {t.language_code} ({t.language})")
    return t.fetch().snippets, t.language_code


def format_transcript(raw: list) -> str:
    lines = []
    for entry in raw:
        secs = int(entry["start"] if isinstance(entry, dict) else entry.start)
        text = (entry["text"] if isinstance(entry, dict) else entry.text).strip()
        ts = f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


def _whisper_transcribe(url: str, lang: str | None) -> tuple[list, str]:
    """Download audio and transcribe with local Whisper. Returns (snippets, language_code)."""
    import whisper
    log.info("No subtitles found — falling back to Whisper transcription...")

    ytdlp = shutil.which("yt-dlp") or None
    node  = shutil.which("node") or ""
    base  = [ytdlp] if ytdlp else ["python", "-m", "yt_dlp"]

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / "audio.mp3"
        dl_lang = lang or "es"
        cmd = base + [
            "--no-update",
            "--cookies-from-browser", "firefox",
            "--no-js-runtimes",
            *([ "--js-runtimes", f"node:{node}"] if node else []),
            # HLS audio avoids HTTPS 403; prefer original language, fall back to any
            "-f", f"bestaudio[protocol^=m3u8][language^={dl_lang}]/bestaudio[protocol^=m3u8]/bestaudio",
            "--extract-audio", "--audio-format", "mp3", "--audio-quality", "5",
            "-o", str(audio_path),
            "--no-playlist",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not audio_path.exists():
            raise RuntimeError(f"Audio download failed:\n{result.stderr}")

        log.info(f"Transcribing with Whisper (small model)...")
        model = whisper.load_model("small")
        whisper_lang = lang.split("-")[0] if lang else None
        result = model.transcribe(
            str(audio_path), language=whisper_lang,
            word_timestamps=True, verbose=False,
        )

        # Keep full segment dicts (with 'words' key for word-level timestamps)
        snippets = result["segments"]
        detected_lang = result.get("language", lang or "es")
        log.info(f"Whisper detected language: {detected_lang}, {len(snippets)} segments")
        return snippets, detected_lang, True   # True = has word timestamps


def extract(url: str) -> dict:
    log.info("Fetching transcript...")
    video_id = parse_video_id(url)
    lang = _detect_language(url)
    if lang and lang.lower() in ("na", "none", "und"):
        lang = None
    log.info(f"Detected video language: {lang or 'unknown'}")

    has_word_timestamps = False
    try:
        raw, language_code = fetch_transcript(video_id, preferred_lang=lang)
    except RuntimeError:
        raw, language_code, has_word_timestamps = _whisper_transcribe(url, lang)

    return {
        "video_id": video_id,
        "language_code": language_code,
        "raw": raw,
        "has_word_timestamps": has_word_timestamps,
        "text": format_transcript(raw),
    }
