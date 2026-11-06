# AGENTS.md — yt-clipper

Read by AI coding agents (pi, Claude Code, etc.) when entering this repository.

---

## AI Onboarding Guide

When a user says **"set this up"**, **"configure this"**, **"guide me through setup"** or similar:

### Step 1 — Run the health check
```bash
python setup_check.py
```
Read the output top to bottom. Every `❌` is a blocker. Every `⚠️` is optional.

### Step 2 — Fix blockers in order

**Missing `.env`**
```bash
cp .env.example .env
```
Ask the user: *"What is your Novita.ai API key?"* (required for LLM calls). Set it in `.env`.

**Missing `config/faceless_brand.json`**
```bash
cp config/faceless_brand.example.json config/faceless_brand.json
```
Ask the user:
- Channel handle (e.g. `@YourChannel`)
- Channel language (e.g. `en` or `es`)
- Accent color, logo path, CTA URL — or tell them to fill it in later

**Missing `config/tts.json`**
```bash
cp config/tts.example.json config/tts.json
```
Default is `gcp_chirp3` (best quality). Keep unless they say otherwise.

**Missing `config/client_secrets.json`**
Walk the user through GCP Console:
1. Enable: Cloud Text-to-Speech API + YouTube Data API v3 + YouTube Analytics API
2. Credentials → OAuth 2.0 Client ID → Desktop app → Download JSON
3. Save as `config/client_secrets.json`

**Missing OAuth tokens**
Tokens are created automatically on first pipeline run. Tell the user:
- TTS token: created on first `faceless_gen.py` or `interview_gen.py` run
- YouTube token: created on first `--upload` run

### Step 3 — Re-run the check
```bash
python setup_check.py
```
Continue until all `❌` are resolved.

### Step 4 — Test one pipeline
Run a dry-run to verify the LLM + brand config work:
```bash
python faceless_gen.py --dry-run
```
If it prints a script without errors, setup is complete.

---

## What this repo is

Four pipelines that turn ideas or raw footage into published YouTube Shorts.

| Pipeline | Entry point | Input → Output |
|----------|-------------|----------------|
| A — Clip | `main.py` | YouTube URL → auto-clipped Shorts |
| B — Faceless | `faceless_gen.py` | Topic → slide Short + AI voice |
| C — Interview | `interview_gen.py` | Concept → animated SVG explainer |
| D — Reel | `reel_gen.py` | Raw clip → 9:16 edited reel |

All brand identity (channel name, colors, language, CTA, voice) is in `config/faceless_brand.json`. No hardcoded values in the code.

---

## Before you do anything

```bash
cd /path/to/yt-clipper
export PATH="$HOME/.local/bin:$PATH"   # yt-dlp binary lives here
python setup_check.py                  # verify all dependencies
python -c "from src import brand_config; print(brand_config.load())"
```

---

## Key facts

### Runtime
- Python 3.10+. Modules in `src/`. Run from repo root.
- Always `export PATH="$HOME/.local/bin:$PATH"` before Pipeline A (yt-dlp).
- `.env` must exist with `NOVITA_API_KEY`.

### Brand config
- All identity in `config/faceless_brand.json` (gitignored — copy from `.example.json`).
- `BrandConfig` dataclass in `src/brand_config.py`. Every LLM prompt reads from it.
- Fields: `channel_handle`, `channel_owner`, `channel_niche`, `channel_description`, `channel_topics`, `channel_language`, `accent_color`, `bg_color`, `cta_url`, `cta_button_text`, `cta_tagline`, `cta_logo`, `cta_screenshot`, `logo_path`.
- Do NOT hardcode channel-specific values in `src/` — always read from `brand_config.load()`.

### LLM
- Novita.ai (OpenAI-compatible) via `NOVITA_API_KEY` + `NOVITA_BASE_URL`.
- Default model: `deepseek/deepseek_v3`.
- No `response_format: json_object` support → strips markdown fences manually.
- Config: `src/config.py` → Pydantic settings.

### TTS provider
- Config: `config/tts.json` (gitignored — copy from `.example.json`).
- Providers: `gcp_chirp3` (best, no native timestamps), `gcp_studio` (great, native timestamps), `gcp_neural2`, `edge_tts` (free fallback).
- Chirp3/Chirp: returns `[]` word_events → compose uses Whisper automatically.
- Studio/Neural2: SSML marks → native timestamps.
- Do NOT pass `voice=` to `generate_with_timestamps()` — it reads config automatically.
- To change voice: edit `provider`/`gender` in `config/tts.json`.

### Video download (Pipeline A)
- `yt-dlp` binary at `~/.local/bin/yt-dlp` (newer than pip version — avoids 403s).
- Uses `--cookies-from-browser firefox` — Firefox must be open for live streams.
- Format: HLS to avoid 403 (`bestvideo[protocol^=m3u8]+bestaudio[...]`).

### Critical bug to avoid
- Audio must be trimmed with `-t {duration}` in the ffmpeg vertical conversion command.
- Without it: video=60s, audio=80s → frozen last frame. Already fixed in `_build_vf()`.

### YouTube OAuth
- `config/client_secrets.json` required (OAuth 2.0 Desktop app from GCP).
- Token saved to `config/token.json` after first browser auth.
- Full scopes needed: `youtube`, `youtube.upload`, `yt-analytics.readonly`.
- If `insufficientPermissions`: `rm config/token.json` → re-run.

### Script quality gate (B + C)
- `src/script_writer.py` and `src/interview_writer.py` score every script using `skills/viral-video-writing/scripts/score.py`.
- Retry loop: up to 3× until score ≥90 and zero hard fails.
- Failed checks are fed back to the LLM as correction notes.

### Skills
- 9 skills in `skills/`. Key ones: `viral-video-writing` (hook rules + scorer), `famous-reel-editor` (Pipeline D scripts).
- Install: `./install_skill.sh`

---

## Module map (`src/`)

```
brand_config.py      Loads config/faceless_brand.json → BrandConfig dataclass
config.py            Pydantic settings from .env
tts.py               TTS: GCP Chirp3/Studio/Neural2 + edge-tts. Reads config/tts.json.
cta_slide.py         CTA slide HTML from BrandConfig → PNG/MP4
script_writer.py     LLM faceless script writer (B) with quality gate
interview_writer.py  LLM interview script writer (C) with quality gate
trend_finder.py      LLM topic picker, reads channel context from brand
visual_planner.py    LLM slide visual plan (B)
slide_agent.py       Claude Code → HTML → Playwright PNG (B)
slide_reviewer.py    Batch slide review (B)
animation_renderer.py Claude Code → HTML → Playwright WebM (C)
faceless_composer.py ffmpeg assembly for Pipeline B
interview_gen.py     Pipeline C orchestrator (in root)
transcript_extractor YT captions → Whisper fallback
clip_analyzer.py     Two-agent LLM: Finder + Reviewer (A)
frame_analyzer.py    Face detection + activity center
video_cutter.py      Full Pipeline A: download → vertical → subs
subtitle_generator.py ASS karaoke captions, 4 styles
speaker_diarizer.py  Resemblyzer voice embeddings → segments
hook_overlay.py      ffmpeg drawtext hook overlay
audio_enhancer.py    Noise reduction
broll_inserter.py    Pexels API → ffmpeg overlay
logo_agent.py        simple-icons SVG → PNG brand logos
brand_assets.py      Playwright logo injection
channel_processor.py Batch: list channel → pipeline per video
youtube_uploader.py  OAuth2 resumable upload, quota handling
youtube_analytics.py Analytics API reports
```

---

## CLI scripts (repo root)

```
main.py                  Pipeline A — clip YouTube video
faceless_gen.py          Pipeline B — faceless Short
interview_gen.py         Pipeline C — animated explainer
reel_gen.py              Pipeline D — talking-head clip → 9:16 reel
setup_check.py           Health check + onboarding guide
upload_ready_clips.py    Batch upload from temp/
schedule_clips.py        Schedule uploaded videos
```

---

## Output structure

```
temp/
  clip_{id}_{start}-{end}.mp4    Pipeline A clips (1080×1920)
  clips_metadata.json             LLM titles / scores
  uploaded.json                   Video IDs after upload
  schedule.json                   Publish schedule
  interview_TIMESTAMP.mp4         Pipeline C output
  reels/<name>/<name>-FINAL.mp4  Pipeline D output
config/
  client_secrets.json             OAuth credentials (gitignored)
  token.json                      YouTube token (gitignored, auto-created)
  tts_token.json                  GCP TTS token (gitignored, auto-created)
  faceless_brand.json             Your brand (gitignored, copy from .example.json)
  tts.json                        TTS provider (gitignored, copy from .example.json)
```

---

## Branch strategy

This repo uses a two-branch workflow:
- `main` — generic, publishable. Push only code that works for any channel.
- `local/tlc` (or similar) — personal working branch. Rebases on main.

Before suggesting a commit or push, check:
```bash
git diff origin/main --name-only   # what files would go out
```
Never push: `.env`, `config/faceless_brand.json`, `config/tts.json`, any token file.
Those are gitignored, but double-check before `git add .`.

---

## What NOT to do

- Do NOT hardcode channel names, colors, URLs, or language in `src/` — read from `brand_config.load()`.
- Do NOT modify `config/token.json` manually.
- Do NOT use `python -m yt_dlp` — always use the binary at `~/.local/bin/yt-dlp`.
- Do NOT remove `-t {duration}` from ffmpeg in `video_cutter._build_vf()`.
- Do NOT set `response_format: json_object` — Novita/DeepSeek doesn't support it.
- Do NOT commit `config/*.json` files that are gitignored (secrets + personal brand).
- Do NOT pass `voice=` to `tts.generate_with_timestamps()` for normal use — config drives it.
