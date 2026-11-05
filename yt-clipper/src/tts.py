"""
Text-to-speech — Google Cloud Neural2 (primary) + edge-tts fallback.

Priority:
  1. Google Cloud TTS Neural2 (es-ES-Neural2-B male, es-ES-Neural2-F female)
     Requires: google-cloud-texttospeech + API enabled in GCP project.
     Word timestamps via SSML <mark> tags → perfect subtitle sync.
  2. edge-tts (Microsoft Neural, free) — used if GCP TTS is unavailable.
     Word timestamps via WordBoundary events.

Usage:
  generate(text, path)                    → MP3
  generate_with_timestamps(text, path)    → (MP3, word_events)

word_events: [{"word": "Un", "start": 0.10, "end": 0.31}, ...]

to_whisper_segments(word_events) → Whisper-compatible segment dicts
    for subtitle_generator.generate(has_word_timestamps=True)
"""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

GCP_VOICE_MALE   = "es-ES-Neural2-B"
GCP_VOICE_FEMALE = "es-ES-Neural2-F"
GCP_LANGUAGE     = "es-ES"
GCP_RATE         = 0.95   # slightly slower than 1.0 — more natural for explainers

EDGE_VOICE_MALE   = "es-ES-AlvaroNeural"
EDGE_VOICE_FEMALE = "es-ES-ElviraNeural"
EDGE_RATE         = "+0%"

DEFAULT_VOICE = "es-ES-Neural2-B"   # GCP Neural2 male (Spain)


# ── GCP TTS ───────────────────────────────────────────────────────────────────

def _gcp_available() -> bool:
    try:
        from google.cloud import texttospeech  # noqa: F401
        return True
    except ImportError:
        return False


def _build_ssml_with_marks(text: str) -> tuple[str, list[str]]:
    """
    Wrap each word in an SSML <mark> so GCP returns per-word timestamps.
    Returns (ssml_string, ordered_mark_names).
    """
    words = text.split()
    marks: list[str] = []
    parts = ["<speak>"]
    for i, w in enumerate(words):
        mark = f"w{i}"
        marks.append(mark)
        parts.append(f'<mark name="{mark}"/>{w}')
    parts.append("</speak>")
    return " ".join(parts), marks


_TTS_SCOPES   = ["https://www.googleapis.com/auth/cloud-platform"]
_SECRETS_FILE = Path(__file__).parent.parent / "config" / "client_secrets.json"
_TTS_TOKEN    = Path(__file__).parent.parent / "config" / "tts_token.json"


def _gcp_credentials():
    """OAuth2 credentials for GCP TTS, using client_secrets.json."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if _TTS_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(_TTS_TOKEN), _TTS_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_SECRETS_FILE), _TTS_SCOPES)
            creds = flow.run_local_server(port=0)
        _TTS_TOKEN.write_text(creds.to_json())
    return creds


def _gcp_synthesize(text: str, out: Path, voice_name: str) -> list[dict]:
    """
    Call GCP TTS via REST API using OAuth2 from client_secrets.json,
    save MP3, return word_events from SSML mark timepoints.
    """
    import base64, json as _json, subprocess, urllib.request

    creds = _gcp_credentials()

    ssml, _ = _build_ssml_with_marks(text)
    words = text.split()

    body = _json.dumps({
        "input": {"ssml": ssml},
        "voice": {"languageCode": GCP_LANGUAGE, "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": GCP_RATE},
        "enableTimePointing": ["SSML_MARK"],
    }).encode()

    from google.auth.transport.requests import Request as _Req
    creds.refresh(_Req())

    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1beta1/text:synthesize",
        data=body,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
    )
    resp = _json.loads(urllib.request.urlopen(req, timeout=30).read())

    audio_bytes = base64.b64decode(resp["audioContent"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio_bytes)

    # Build word_events from SSML mark timepoints
    timepoints = sorted(
        [(tp["markName"], tp["timeSeconds"]) for tp in resp.get("timepoints", [])],
        key=lambda x: x[1],
    )

    # Total duration from ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(out)],
        capture_output=True, text=True,
    )
    total_dur = float(_json.loads(probe.stdout)["streams"][0]["duration"])

    word_events: list[dict] = []
    for idx, (mark_name, start_s) in enumerate(timepoints):
        word_idx = int(mark_name[1:])  # "w3" → 3
        if word_idx >= len(words):
            continue
        end_s = timepoints[idx + 1][1] if idx + 1 < len(timepoints) else total_dur
        word_events.append({
            "word":  words[word_idx],
            "start": round(start_s, 3),
            "end":   round(end_s, 3),
        })

    log.info(f"[TTS/GCP] {out.name} ({out.stat().st_size // 1024}KB) "
             f"voice={voice_name} words={len(word_events)}")
    return word_events


# ── edge-tts fallback ─────────────────────────────────────────────────────────

async def _edge_synth(text: str, out: Path, voice: str, rate: str) -> list[dict]:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    word_events: list[dict] = []
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            word_events.append({
                "word":  chunk["text"],
                "start": round(chunk["offset"] / 1e7, 3),
                "end":   round((chunk["offset"] + chunk["duration"]) / 1e7, 3),
            })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio_bytes)
    log.info(f"[TTS/edge] {out.name} ({out.stat().st_size // 1024}KB) "
             f"voice={voice} words={len(word_events)}")
    return word_events


def _edge_voice_for(gcp_voice: str) -> str:
    """Map a GCP voice name to the nearest edge-tts equivalent."""
    female = "Female" in gcp_voice or gcp_voice.endswith(("-A", "-C", "-D", "-E", "-F"))
    return EDGE_VOICE_FEMALE if female else EDGE_VOICE_MALE


# ── Public API ────────────────────────────────────────────────────────────────

def generate_with_timestamps(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = EDGE_RATE,
) -> tuple[Path, list[dict]]:
    """
    Generate MP3 + exact word timestamps.
    Uses GCP Neural2 if available, otherwise falls back to edge-tts.
    Returns (path, word_events).
    """
    out = Path(output_path)

    # Try GCP first
    if _gcp_available() and voice.startswith("es-ES-Neural2"):
        try:
            word_events = _gcp_synthesize(text, out, voice)
            return out, word_events
        except Exception as e:
            log.warning(f"[TTS] GCP failed ({e}) — falling back to edge-tts")

    # edge-tts fallback (also used for non-Neural2 voices)
    edge_voice = _edge_voice_for(voice) if voice.startswith("es-ES-Neural2") else voice
    word_events = asyncio.run(_edge_synth(text, out, edge_voice, rate))
    return out, word_events


def generate(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = EDGE_RATE,
) -> Path:
    """Generate MP3. Returns the output Path."""
    path, _ = generate_with_timestamps(text, output_path, voice, rate)
    return path


# ── Word events → Whisper segment format ─────────────────────────────────────

def to_whisper_segments(word_events: list[dict], pause_s: float = 0.45) -> list[dict]:
    """
    Group word_events into sentence-like segments split on pauses ≥ pause_s.
    Returns Whisper-compatible dicts with word-level timestamps.
    """
    if not word_events:
        return []

    segments: list[dict] = []
    current: list[dict] = []

    for i, w in enumerate(word_events):
        current.append({"word": " " + w["word"], "start": w["start"], "end": w["end"]})
        is_last   = i == len(word_events) - 1
        long_pause = not is_last and (word_events[i + 1]["start"] - w["end"]) >= pause_s

        if is_last or long_pause:
            segments.append({
                "start": current[0]["start"],
                "end":   current[-1]["end"],
                "text":  "".join(cw["word"] for cw in current),
                "words": current,
            })
            current = []

    return segments
