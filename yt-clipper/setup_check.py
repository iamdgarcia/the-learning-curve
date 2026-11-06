#!/usr/bin/env python3
"""
yt-clipper — Setup health check.

Run this after cloning to verify every dependency and config file.
Your AI reads this output and guides you through any failures interactively.

Usage:
  python setup_check.py          # full check, human-readable output
  python setup_check.py --json   # machine-readable (for AI tooling)
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ── Helpers ───────────────────────────────────────────────────────────────────

OK   = "✅"
WARN = "⚠️ "
FAIL = "❌"

def _check(label: str, ok: bool | None, detail: str = "", fix: str = "") -> dict:
    status = OK if ok is True else (WARN if ok is None else FAIL)
    return {"label": label, "status": status, "ok": ok, "detail": detail, "fix": fix}

def _cmd(args: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

def _pkg(name: str) -> bool:
    return importlib.util.find_spec(name) is not None

def _env(key: str) -> bool:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    return bool(os.environ.get(key, "").strip())

# ── Checks ────────────────────────────────────────────────────────────────────

def check_system() -> list[dict]:
    results = []

    # Python version
    major, minor = sys.version_info[:2]
    ok = major == 3 and minor >= 10
    results.append(_check(
        "Python 3.10+", ok,
        detail=f"Python {major}.{minor}.{sys.version_info[2]}",
        fix="Install Python 3.10 or later: https://www.python.org/downloads/",
    ))

    # ffmpeg
    ok, out = _cmd(["ffmpeg", "-version"])
    version = out.split("\n")[0] if ok else ""
    results.append(_check(
        "ffmpeg", ok,
        detail=version[:60] if ok else "not found",
        fix="sudo apt install ffmpeg",
    ))

    # yt-dlp binary
    ytdlp_bin = Path.home() / ".local/bin/yt-dlp"
    ok = ytdlp_bin.exists() and os.access(ytdlp_bin, os.X_OK)
    if ok:
        _, ver = _cmd([str(ytdlp_bin), "--version"])
        detail = f"~/.local/bin/yt-dlp {ver.strip()}"
    else:
        detail = "not found at ~/.local/bin/yt-dlp"
    results.append(_check(
        "yt-dlp binary", ok, detail=detail,
        fix=(
            "mkdir -p ~/.local/bin && "
            "curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp "
            "-o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp"
        ),
    ))

    # Node.js (Pipeline D only)
    ok, out = _cmd(["node", "--version"])
    results.append(_check(
        "Node.js (Pipeline D only)", True if ok else None,
        detail=out.strip() if ok else "not found — only needed for reel_gen.py",
        fix="sudo apt install nodejs npm",
    ))

    return results


def check_python_packages() -> list[dict]:
    required = [
        ("openai",                    "pip install openai"),
        ("anthropic",                 "pip install anthropic"),
        ("yt_dlp",                    "pip install yt-dlp"),
        ("whisper",                   "pip install openai-whisper"),
        ("playwright",                "pip install playwright && playwright install chromium"),
        ("google.cloud.texttospeech", "pip install google-cloud-texttospeech"),
        ("google_auth_oauthlib",      "pip install google-auth-oauthlib"),
        ("googleapiclient",           "pip install google-api-python-client"),
        ("edge_tts",                  "pip install edge-tts"),
        ("cv2",                       "pip install opencv-python"),
        ("dotenv",                    "pip install python-dotenv"),
        ("pydantic_settings",         "pip install pydantic-settings"),
        ("pexels_api",                "pip install pexels-api"),
    ]
    missing = [(name, fix) for name, fix in required if not _pkg(name.split(".")[0])]

    if not missing:
        return [_check("Python packages", True, detail=f"all {len(required)} packages installed")]

    fixes = "  ".join(fix for _, fix in missing)
    return [_check(
        "Python packages", False,
        detail=f"missing: {', '.join(n for n, _ in missing)}",
        fix=f"pip install -r requirements.txt  (or individually: {fixes})",
    )]


def check_env() -> list[dict]:
    results = []

    env_file = ROOT / ".env"
    if not env_file.exists():
        results.append(_check(
            ".env file", False,
            detail=".env not found",
            fix="cp .env.example .env  then fill in NOVITA_API_KEY",
        ))
        return results
    results.append(_check(".env file", True, detail=str(env_file)))

    # Required keys
    required_keys = {
        "NOVITA_API_KEY": "Required for all LLM calls (script writing). Get at novita.ai",
    }
    optional_keys = {
        "PEXELS_API_KEY": "B-roll in Pipeline A. Free tier at pexels.com/api",
    }
    for key, description in required_keys.items():
        ok = _env(key)
        results.append(_check(
            f"  {key}", ok,
            detail="set" if ok else "not set",
            fix=f"Add to .env:  {key}=your-key   ({description})",
        ))
    for key, description in optional_keys.items():
        ok = _env(key)
        results.append(_check(
            f"  {key} (optional)", True if ok else None,
            detail="set" if ok else "not set — B-roll disabled",
            fix=f"Add to .env:  {key}=your-key   ({description})",
        ))

    return results


def check_config() -> list[dict]:
    results = []

    files = {
        "config/client_secrets.json": (
            False,
            "Google OAuth credentials — download from Google Cloud Console\n"
            "  1. console.cloud.google.com → APIs → Credentials → Create OAuth 2.0 Client ID → Desktop app\n"
            "  2. Enable: Cloud Text-to-Speech API + YouTube Data API v3 + YouTube Analytics API\n"
            "  3. Download JSON → save as config/client_secrets.json"
        ),
        "config/tts.json": (
            None,
            "TTS provider config — cp config/tts.example.json config/tts.json"
        ),
        "config/faceless_brand.json": (
            None,
            "Brand config — cp config/faceless_brand.example.json config/faceless_brand.json"
        ),
    }

    for path, (severity_if_missing, fix) in files.items():
        p = ROOT / path
        if p.exists():
            extra = ""
            if path == "config/tts.json":
                try:
                    cfg = json.loads(p.read_text())
                    extra = f"  provider={cfg.get('provider')} gender={cfg.get('gender')}"
                except Exception:
                    pass
            results.append(_check(path, True, detail=f"found{extra}"))
        else:
            results.append(_check(path, severity_if_missing, detail="not found", fix=fix))

    # Auth tokens (warn only — created automatically on first run)
    tokens = {
        "config/token.json":     "YouTube OAuth token — created automatically on first upload/schedule run",
        "config/tts_token.json": "GCP TTS token — created automatically on first TTS call",
    }
    for path, note in tokens.items():
        p = ROOT / path
        results.append(_check(
            path,
            True if p.exists() else None,
            detail="found" if p.exists() else f"not yet — {note}",
        ))

    return results


def check_gcp_tts() -> list[dict]:
    token = ROOT / "config" / "tts_token.json"
    secrets = ROOT / "config" / "client_secrets.json"

    if not secrets.exists():
        return [_check("GCP TTS", False, detail="client_secrets.json missing — see config check above")]

    if not token.exists():
        return [_check(
            "GCP TTS", None,
            detail="not yet authenticated",
            fix="Run any pipeline (faceless_gen.py or interview_gen.py) — browser auth opens automatically",
        )]

    try:
        sys.path.insert(0, str(ROOT))
        from src.tts import _gcp_credentials, _load_config, _resolve_voice
        cfg = _load_config()
        provider, voice = _resolve_voice(cfg)
        creds = _gcp_credentials()
        return [_check("GCP TTS", True, detail=f"authenticated  provider={provider}  voice={voice}")]
    except Exception as e:
        return [_check(
            "GCP TTS", False, detail=str(e)[:120],
            fix="rm config/tts_token.json and re-run any pipeline to re-authenticate",
        )]


def check_youtube() -> list[dict]:
    token = ROOT / "config" / "token.json"
    secrets = ROOT / "config" / "client_secrets.json"

    if not secrets.exists():
        return [_check("YouTube OAuth", False, detail="client_secrets.json missing")]

    if not token.exists():
        return [_check(
            "YouTube OAuth", None,
            detail="not yet authenticated",
            fix="Run any pipeline with --upload  (e.g. python faceless_gen.py --upload --privacy unlisted)",
        )]

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        SCOPES = [
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ]
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.write_text(creds.to_json())
        scopes_ok = all(s in (creds.scopes or []) for s in SCOPES)
        detail = "authenticated" + ("" if scopes_ok else " (limited scopes — rm config/token.json to re-auth with full scopes)")
        return [_check("YouTube OAuth", True if scopes_ok else None, detail=detail)]
    except Exception as e:
        return [_check(
            "YouTube OAuth", False, detail=str(e)[:120],
            fix="rm config/token.json and re-run with --upload",
        )]


# ── Report ────────────────────────────────────────────────────────────────────

def run() -> list[dict]:
    sections = [
        ("System",           check_system()),
        ("Python packages",  check_python_packages()),
        ("Environment",      check_env()),
        ("Config files",     check_config()),
        ("GCP TTS",          check_gcp_tts()),
        ("YouTube",          check_youtube()),
    ]
    return sections


def print_report(sections: list) -> int:
    print("\nyt-clipper — Setup Check")
    print("=" * 50)
    errors = warnings = 0
    for section_name, checks in sections:
        print(f"\n{section_name}")
        for c in checks:
            print(f"  {c['status']}  {c['label']}", end="")
            if c["detail"]:
                print(f"  ({c['detail']})", end="")
            print()
            if c["ok"] is False:
                errors += 1
                if c["fix"]:
                    for line in c["fix"].split("\n"):
                        print(f"       → {line}")
            elif c["ok"] is None:
                warnings += 1

    print("\n" + "=" * 50)
    if errors == 0 and warnings == 0:
        print("✅  All checks passed. You're ready to run any pipeline.")
    elif errors == 0:
        print(f"⚠️   {warnings} warning(s). Pipelines will work but some optional features are disabled.")
    else:
        print(f"❌  {errors} error(s), {warnings} warning(s). Fix the errors above before running pipelines.")
        print("\nTell your AI: \"guide me through the yt-clipper setup\" and share this output.")
    print()
    return errors


if __name__ == "__main__":
    sections = run()

    if "--json" in sys.argv:
        flat = [c for _, checks in sections for c in checks]
        print(json.dumps(flat, indent=2))
    else:
        exit_code = print_report(sections)
        sys.exit(exit_code)
