"""Transcription via the Groq API (whisper-large-v3, word-level timestamps).

Drop-in alternative to transcribe.py / transcribe_local.py: same CLI, same output JSON
shape, so every other script in this skill (gen.py, captions.py, make_edl.py) reads it
without changes:
{ "language": "en", "words": [ { "text": "...", "start": 0.12, "end": 0.34, "type": "word" }, ... ] }

Why Groq: Whisper large-v3 quality at API speed (a 10-min video transcribes in seconds,
no local model download) and near-zero cost. Word timings are Whisper-alignment quality —
same as transcribe_local.py, slightly looser than ElevenLabs Scribe.

Needs:  GROQ_API_KEY in the environment (console.groq.com), ffmpeg + curl on PATH.

Usage:
    python scripts/transcribe_groq.py <video_path> --edit-dir edit --language en
    python scripts/transcribe_groq.py <video_path> --language it
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def load_api_key() -> str:
    """GROQ_API_KEY from the environment, or from a .env file (cwd, scripts/, skill root)."""
    v = os.environ.get("GROQ_API_KEY", "")
    if v:
        return v
    script_dir = Path(__file__).resolve().parent
    for candidate in [Path.cwd() / ".env", script_dir / ".env", script_dir.parent / ".env"]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, val = line.split("=", 1)
                if k.strip() == "GROQ_API_KEY":
                    val = val.strip().strip('"').strip("'")
                    if val and not val.startswith("gsk_your"):
                        return val
    sys.exit(
        "GROQ_API_KEY not found.\n"
        "  Put a line  GROQ_API_KEY=gsk_...  in the skill's .env file\n"
        "  (famous-reel-editor/.env) or export it in ~/.zshrc.\n"
        "  Get a key at https://console.groq.com.\n"
        "  No key? Use scripts/transcribe_local.py instead (free, local Whisper)."
    )


API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL = "whisper-large-v3"
MAX_UPLOAD_MB = 24  # free-tier limit is 25MB; at 32kbps mono that's ~100 minutes


def extract_audio(video_path: Path, dest: Path) -> None:
    # 16kHz mono 32kbps mp3: all Whisper needs, tiny upload.
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribe a video via the Groq API")
    ap.add_argument("video", type=Path, help="Path to video file")
    ap.add_argument("--edit-dir", type=Path, default=None,
                    help="Edit output directory (default: <video_parent>/edit)")
    ap.add_argument("--language", type=str, default=None,
                    help="ISO language code (e.g. 'en', 'it'). Omit to auto-detect.")
    ap.add_argument("--num-speakers", type=int, default=None,
                    help="Accepted for CLI parity; ignored (Whisper is single-speaker).")
    args = ap.parse_args()

    api_key = load_api_key()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")
    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"
    if out_path.exists():
        print(f"cached: {out_path.name}")
        return

    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video.stem}.mp3"
        print(f"  extracting audio from {video.name}", flush=True)
        extract_audio(video, audio)
        size_mb = audio.stat().st_size / 1e6
        if size_mb > MAX_UPLOAD_MB:
            sys.exit(f"audio is {size_mb:.0f}MB (> {MAX_UPLOAD_MB}MB Groq limit) — "
                     "split the video first, or transcribe halves and merge the JSONs.")

        print(f"  uploading to Groq ({size_mb:.1f}MB, {MODEL})...", flush=True)
        cmd = [
            "curl", "-sS", "-X", "POST", API_URL,
            "-H", f"Authorization: Bearer {api_key}",
            "-F", f"file=@{audio}",
            "-F", f"model={MODEL}",
            "-F", "response_format=verbose_json",
            "-F", "timestamp_granularities[]=word",
        ]
        if args.language:
            cmd += ["-F", f"language={args.language}"]
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        try:
            data = json.loads(res.stdout)
        except json.JSONDecodeError:
            sys.exit(f"Groq returned non-JSON: {res.stdout[:500]}")
        if "error" in data:
            sys.exit(f"Groq error: {data['error']}")

    words = [
        {
            "text": str(w["word"]).strip(),
            "start": round(float(w["start"]), 3),
            "end": round(float(w["end"]), 3),
            "type": "word",
        }
        for w in data.get("words", [])
    ]
    if not words:
        sys.exit("no word timestamps in response — check the API output above.")

    payload = {"language": data.get("language", args.language or ""), "words": words}
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"  saved: {out_path.name} ({len(words)} words) -> {out_path}")


if __name__ == "__main__":
    main()
