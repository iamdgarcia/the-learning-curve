"""
Text-to-speech with configurable GCP provider.

Provider priority (resolved from config/tts.json):
  gcp_studio   — GCP Studio voices, highest quality WITH native timestamps. Default.
  gcp_chirp3   — GCP Chirp3-HD, most natural. No native timestamps → Whisper in compose.
  gcp_chirp    — GCP Chirp-HD, very natural. No native timestamps → Whisper in compose.
  gcp_neural2  — GCP Neural2, previous default. Native timestamps.
  edge_tts     — Microsoft Neural (free). Native timestamps via WordBoundary.

Config: config/tts.json  (copy from config/tts.example.json)
  { "provider": "gcp_studio", "speaking_rate": 0.95, "gender": "male", "voices": {...} }

Providers with native timestamps (SSML marks): gcp_studio, gcp_neural2
Providers without (Whisper fallback in compose): gcp_chirp3, gcp_chirp

Usage:
  generate(text, path)                 → MP3
  generate_with_timestamps(text, path) → (MP3, word_events)
    word_events = [] for chirp providers → compose uses Whisper automatically

word_events: [{"word": "Un", "start": 0.10, "end": 0.31}, ...]
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

GCP_LANGUAGE = "es-ES"
EDGE_RATE    = "+0%"

_CONFIG_FILE = Path(__file__).parent.parent / "config" / "tts.json"
_TTS_SCOPES  = ["https://www.googleapis.com/auth/cloud-platform"]
_SECRETS_FILE = Path(__file__).parent.parent / "config" / "client_secrets.json"
_TTS_TOKEN    = Path(__file__).parent.parent / "config" / "tts_token.json"

# Providers that support SSML mark timepoints
_SSML_MARK_PROVIDERS = {"gcp_studio", "gcp_neural2"}


# ── Config loader ─────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if _CONFIG_FILE.exists():
        return json.loads(_CONFIG_FILE.read_text())
    # Legacy fallback: Neural2 behaviour before tts.json existed
    return {
        "provider": "gcp_neural2",
        "speaking_rate": 0.95,
        "gender": "male",
        "voices": {
            "gcp_neural2": {"male": "es-ES-Neural2-G", "female": "es-ES-Neural2-A"},
            "edge_tts":    {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
        },
    }


def _resolve_voice(cfg: dict) -> tuple[str, str]:
    """Return (provider, voice_name) from config."""
    provider = cfg.get("provider", "gcp_neural2")
    gender   = cfg.get("gender", "male")
    voices   = cfg.get("voices", {})
    voice    = voices.get(provider, {}).get(gender, "es-ES-Neural2-G")
    return provider, voice


# ── GCP helpers ───────────────────────────────────────────────────────────────

def _gcp_available() -> bool:
    try:
        from google.cloud import texttospeech  # noqa: F401
        return True
    except ImportError:
        return False


def _gcp_credentials():
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


def _build_ssml_with_marks(text: str) -> str:
    parts = ["<speak>"]
    for i, w in enumerate(text.split()):
        parts.append(f'<mark name="w{i}"/>{w}')
    parts.append("</speak>")
    return " ".join(parts)


def _gcp_synthesize_with_marks(text: str, out: Path, voice_name: str, rate: float) -> list[dict]:
    """GCP TTS with SSML marks → native word timestamps. For Studio and Neural2."""
    import base64, json as _json, subprocess, urllib.request
    from google.auth.transport.requests import Request as _Req

    creds = _gcp_credentials()
    words = text.split()
    ssml  = _build_ssml_with_marks(text)

    body = _json.dumps({
        "input": {"ssml": ssml},
        "voice": {"languageCode": GCP_LANGUAGE, "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate},
        "enableTimePointing": ["SSML_MARK"],
    }).encode()

    creds.refresh(_Req())
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1beta1/text:synthesize",
        data=body,
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
    )
    resp = _json.loads(urllib.request.urlopen(req, timeout=30).read())

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(resp["audioContent"]))

    timepoints = sorted(
        [(tp["markName"], tp["timeSeconds"]) for tp in resp.get("timepoints", [])],
        key=lambda x: x[1],
    )
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(out)],
        capture_output=True, text=True,
    )
    total_dur = float(_json.loads(probe.stdout)["streams"][0]["duration"])

    word_events: list[dict] = []
    for idx, (mark_name, start_s) in enumerate(timepoints):
        word_idx = int(mark_name[1:])
        if word_idx >= len(words):
            continue
        end_s = timepoints[idx + 1][1] if idx + 1 < len(timepoints) else total_dur
        word_events.append({"word": words[word_idx], "start": round(start_s, 3), "end": round(end_s, 3)})

    log.info(f"[TTS/GCP] {out.name} ({out.stat().st_size // 1024}KB) voice={voice_name} words={len(word_events)}")
    return word_events


def _gcp_synthesize_simple(text: str, out: Path, voice_name: str, rate: float) -> list[dict]:
    """GCP TTS without SSML marks. For Chirp/Chirp3 voices (no timepoint support).
    Returns [] — compose step uses Whisper for subtitle timestamps automatically."""
    import base64, json as _json, urllib.request
    from google.auth.transport.requests import Request as _Req

    creds = _gcp_credentials()
    body  = _json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": GCP_LANGUAGE, "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": rate},
    }).encode()

    creds.refresh(_Req())
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=body,
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
    )
    resp = _json.loads(urllib.request.urlopen(req, timeout=30).read())

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(resp["audioContent"]))

    log.info(f"[TTS/GCP] {out.name} ({out.stat().st_size // 1024}KB) voice={voice_name} (no timestamps → Whisper)")
    return []  # compose will run Whisper


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
    log.info(f"[TTS/edge] {out.name} ({out.stat().st_size // 1024}KB) voice={voice} words={len(word_events)}")
    return word_events


# ── Public API ────────────────────────────────────────────────────────────────

def generate_with_timestamps(
    text: str,
    output_path: str,
    voice: str | None = None,   # None → read from config/tts.json
    rate: str = EDGE_RATE,
) -> tuple[Path, list[dict]]:
    """
    Generate MP3 + word timestamps. Provider and voice resolved from config/tts.json.
    voice= overrides the config voice (legacy callers passing a GCP voice name still work).
    Returns (path, word_events).  word_events=[] for chirp providers → Whisper in compose.
    """
    cfg              = _load_config()
    provider, cfg_voice = _resolve_voice(cfg)
    speaking_rate    = float(cfg.get("speaking_rate", 0.95))
    resolved_voice   = voice or cfg_voice  # explicit override wins
    out              = Path(output_path)

    # Legacy callers may pass a Neural2 voice name directly — honour it
    if resolved_voice.startswith("es-ES-Neural2"):
        provider = "gcp_neural2"

    if _gcp_available() and provider != "edge_tts":
        try:
            if provider in _SSML_MARK_PROVIDERS:
                return out, _gcp_synthesize_with_marks(text, out, resolved_voice, speaking_rate)
            else:
                return out, _gcp_synthesize_simple(text, out, resolved_voice, speaking_rate)
        except Exception as e:
            log.warning(f"[TTS] GCP failed ({e}) — falling back to edge-tts")

    edge_cfg   = cfg.get("voices", {}).get("edge_tts", {})
    gender     = cfg.get("gender", "male")
    edge_voice = edge_cfg.get(gender, "es-ES-AlvaroNeural")
    return out, asyncio.run(_edge_synth(text, out, edge_voice, EDGE_RATE))


def generate(text: str, output_path: str, voice: str | None = None, rate: str = EDGE_RATE) -> Path:
    path, _ = generate_with_timestamps(text, output_path, voice, rate)
    return path


# ── Word events → Whisper segment format ─────────────────────────────────────

def to_whisper_segments(word_events: list[dict], pause_s: float = 0.45) -> list[dict]:
    """Group word_events into sentence-like segments. Returns Whisper-compatible dicts."""
    if not word_events:
        return []
    segments: list[dict] = []
    current:  list[dict] = []
    for i, w in enumerate(word_events):
        current.append({"word": " " + w["word"], "start": w["start"], "end": w["end"]})
        is_last    = i == len(word_events) - 1
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
