"""Transcribe a video with ElevenLabs Scribe (word-level timestamps).

Standalone version bundled with the reel-editor skill: no external project needed,
only `requests` + `ffmpeg` on PATH. Extracts mono 16kHz audio, uploads to Scribe with
verbatim + word-level timestamps, and writes the full response to
<edit_dir>/transcripts/<video_stem>.json in the shape gen.py / captions.py expect:
{ "words": [ { "text": "...", "start": 0.12, "end": 0.34, "type": "word" }, ... ] }

API key: reads ELEVENLABS_API_KEY from the environment, or from a `.env` file in the
current directory or next to this script. NEVER hard-code it.

Cached: if the output JSON already exists, the upload is skipped.

Usage:
    python scripts/transcribe.py <video_path>
    python scripts/transcribe.py <video_path> --edit-dir edit
    python scripts/transcribe.py <video_path> --language en
    python scripts/transcribe.py <video_path> --language it --num-speakers 1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def load_api_key() -> str:
    script_dir = Path(__file__).resolve().parent
    for candidate in [Path.cwd() / ".env", script_dir / ".env", script_dir.parent / ".env"]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "ELEVENLABS_API_KEY":
                    return v.strip().strip('"').strip("'")
    v = os.environ.get("ELEVENLABS_API_KEY", "")
    if not v:
        sys.exit(
            "ELEVENLABS_API_KEY not found.\n"
            "  Set it once:  export ELEVENLABS_API_KEY=sk_...   (add to ~/.zshrc)\n"
            "  Or put a line  ELEVENLABS_API_KEY=sk_...  in a .env file here.\n"
            "  Get a key at https://elevenlabs.io (Speech-to-Text / Scribe).\n"
            "  No key? Use scripts/transcribe_local.py instead (free, local Whisper)."
        )
    return v


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def call_scribe(audio_path: Path, api_key: str, language=None, num_speakers=None) -> dict:
    data = {
        "model_id": "scribe_v1",
        "diarize": "true",
        "tag_audio_events": "true",
        "timestamps_granularity": "word",
    }
    if language:
        data["language_code"] = language
    if num_speakers:
        data["num_speakers"] = str(num_speakers)

    with open(audio_path, "rb") as f:
        resp = requests.post(
            SCRIBE_URL,
            headers={"xi-api-key": api_key},
            files={"file": (audio_path.name, f, "audio/wav")},
            data=data,
            timeout=1800,
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Scribe returned {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def transcribe_one(video: Path, edit_dir: Path, api_key: str, language=None, num_speakers=None) -> Path:
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"
    if out_path.exists():
        print(f"cached: {out_path.name}")
        return out_path

    print(f"  extracting audio from {video.name}", flush=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video.stem}.wav"
        extract_audio(video, audio)
        size_mb = audio.stat().st_size / (1024 * 1024)
        print(f"  uploading {video.stem}.wav ({size_mb:.1f} MB)", flush=True)
        payload = call_scribe(audio, api_key, language, num_speakers)

    out_path.write_text(json.dumps(payload, indent=2))
    dt = time.time() - t0
    kb = out_path.stat().st_size / 1024
    print(f"  saved: {out_path.name} ({kb:.1f} KB) in {dt:.1f}s")
    if isinstance(payload, dict) and "words" in payload:
        print(f"    words: {len(payload['words'])}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribe a video with ElevenLabs Scribe")
    ap.add_argument("video", type=Path, help="Path to video file")
    ap.add_argument("--edit-dir", type=Path, default=None,
                    help="Edit output directory (default: <video_parent>/edit)")
    ap.add_argument("--language", type=str, default=None,
                    help="ISO language code (e.g. 'en', 'it'). Omit to auto-detect.")
    ap.add_argument("--num-speakers", type=int, default=None,
                    help="Number of speakers when known (use 1 for a single talking head).")
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")
    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    api_key = load_api_key()
    transcribe_one(video, edit_dir, api_key, args.language, args.num_speakers)


if __name__ == "__main__":
    main()
