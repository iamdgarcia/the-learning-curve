# yt-clipper

AI-powered content factory for YouTube Shorts. Four pipelines that take ideas or raw footage and produce published videos — scripts written, voices synthesised, animations generated, subtitles burned, uploaded.

Everything that makes a video yours (channel name, colors, voice, language, CTA) lives in one config file. No code changes needed to rebrand.

> **New here?**  
> Run `python setup_check.py` and tell your AI: *"guide me through setup"*.

---

## The four pipelines

| | Pipeline | What you give it | What you get |
|--|----------|-----------------|--------------|
| **A** | **Clip** | A YouTube URL | Shorts cut from the best moments, vertical, subtitled |
| **B** | **Faceless** | A topic (or nothing) | Branded slide Short with AI voice |
| **C** | **Interview** | A concept | Animated SVG explainer Short with AI voice |
| **D** | **Reel** | A raw clip you recorded | Edited 9:16 reel with animated cards and music |

```bash
python main.py         --url "https://youtu.be/..."          # A
python faceless_gen.py --topic "Prompt caching in OpenAI"    # B
python interview_gen.py --topic "What is RAG?"               # C
python reel_gen.py     --clip path/to/raw.mp4                # D
```

---

## Quick start

```bash
# 1. Clone
git clone <repo-url> && cd yt-clipper

# 2. System packages
sudo apt install ffmpeg python3 nodejs npm

# yt-dlp binary (Pipeline A — do NOT use pip version, gets 403 on live streams)
mkdir -p ~/.local/bin
curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
  -o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# 3. Python packages
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env                                      # then fill NOVITA_API_KEY
cp config/faceless_brand.example.json config/faceless_brand.json  # then fill your channel details
cp config/tts.example.json config/tts.json                # pick your TTS voice

# 5. Google Cloud (for TTS + YouTube upload)
# See "Google Cloud setup" below

# 6. Verify everything
python setup_check.py
```

---

## Configuration

All brand identity lives in `config/faceless_brand.json`. Copy from the example and edit:

```json
{
  "channel_handle":      "@YourChannel",
  "channel_owner":       "Your Name",
  "channel_niche":       "AI · Dev Tools",
  "channel_description": "One line about your channel for the LLM",
  "channel_topics":      "LLMs, RAG, embeddings, agents",
  "channel_language":    "en",

  "accent_color":    "#0047FF",
  "bg_color":        "#FFFFFF",
  "logo_path":       "assets/logos/your_logo.png",

  "cta_url":         "yourchannel.substack.com",
  "cta_button_text": "Subscribe free",
  "cta_tagline":     "One idea a week."
}
```

### Config files at a glance

| File | Purpose | Committed? |
|------|---------|-----------|
| `.env` | API keys | ❌ — copy from `.env.example` |
| `config/faceless_brand.json` | Your channel identity | ❌ — copy from `.example.json` |
| `config/tts.json` | TTS voice provider | ❌ — copy from `.example.json` |
| `config/client_secrets.json` | Google OAuth credentials | ❌ — download from GCP Console |
| `config/token.json` | YouTube OAuth token | ❌ — auto-created on first upload |
| `config/tts_token.json` | GCP TTS token | ❌ — auto-created on first TTS call |

### TTS voice

Edit `config/tts.json` to change the voice — no code changes needed:

```json
{ "provider": "gcp_chirp3", "gender": "male", "speaking_rate": 0.95 }
```

| Provider | Quality | Native timestamps |
|----------|---------|------------------|
| `gcp_chirp3` | ⭐⭐⭐⭐⭐ | No (Whisper handles subs) |
| `gcp_studio` | ⭐⭐⭐⭐ | Yes |
| `gcp_neural2` | ⭐⭐⭐ | Yes |
| `edge_tts` | ⭐⭐ free | Yes |

---

## Google Cloud setup

One GCP project, one OAuth client, covers both TTS and YouTube upload.

1. [console.cloud.google.com](https://console.cloud.google.com)
2. Enable: **Cloud Text-to-Speech API** + **YouTube Data API v3** + **YouTube Analytics API**
3. Credentials → Create **OAuth 2.0 Client ID** → Desktop app → Download JSON
4. Save as `config/client_secrets.json`
5. First run triggers browser auth and saves the token automatically

---

## API keys needed

| Key | For | Where |
|-----|-----|-------|
| `NOVITA_API_KEY` | LLM (script writing) | [novita.ai ↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) |
| Google OAuth | GCP TTS + YouTube | GCP Console (see below) |
| `PEXELS_API_KEY` | B-roll in Pipeline A | [pexels.com/api](https://www.pexels.com/api/) — optional |
| `ELEVENLABS_API_KEY` | Pipeline D transcription | [elevenlabs.io ↗](https://try.elevenlabs.io/5rwirobe89kq) — optional, best timing |
| `GROQ_API_KEY` | Pipeline D transcription | [console.groq.com](https://console.groq.com) — optional, free |

→ Not sure which tools to pick? See the [full recommended stack guide](../STACK.md).

---

## Pipeline usage

### A — Clip an existing YouTube video
```bash
export PATH="$HOME/.local/bin:$PATH"
python main.py --url "https://youtu.be/VIDEO_ID" --max-clips 5 --mode shorts \
               --auto-upload --privacy unlisted

# Schedule the uploaded clips
python schedule_clips.py --from-file temp/uploaded.json
```
Modes: `shorts` (60s) · `standard` (90s) · `emotion` (peak moments) · `topic "keyword"`

### B — Faceless branded Short
```bash
python faceless_gen.py --topic "Prompt caching in OpenAI"
python faceless_gen.py              # LLM picks trending topic
python faceless_gen.py --dry-run    # preview script only
python faceless_gen.py --upload --privacy unlisted
```

### C — Animated explainer
```bash
python interview_gen.py --topic "What is RAG?"
python interview_gen.py --upload --privacy unlisted
python interview_gen.py --dry-run
```

### D — Reel from your raw clip
```bash
python reel_gen.py --clip path/to/raw.mp4 --name myname --transcriber groq
# Pauses for EDL review and crop_y tuning
```
Transcribers: `elevenlabs` · `groq` · `local` (offline, no key)

---

## Script quality gate (Pipelines B + C)

Every script is auto-scored by the `viral-video-writing` skill (hook rules, re-hooks every 8s, anti-AI writing checks). Rewritten up to 3× until ≥90/100 with zero hard fails.

```
[Script] attempt 1/3 — score 85/100, hard=0, soft=3
[Script] attempt 2/3 — score 92/100, hard=0, soft=1  ← pipeline continues
```

---

## Analytics
```bash
python -m src.youtube_analytics --report channel --days 90
python -m src.youtube_analytics --report top-videos --days 30
python -m src.youtube_analytics --report schedule-insights --days 30
python -m src.youtube_analytics --report video --id VIDEO_ID
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Pipeline A: `403 Forbidden` | Firefox must be open and logged into YouTube |
| Any upload: `insufficientPermissions` | `rm config/token.json` and re-run |
| GCP TTS `403` | `rm config/tts_token.json` and re-run |
| Pipeline B/C: Claude HTML timeout | Retry — second attempt almost always succeeds |
| YouTube quota exceeded | ~6 uploads/day limit |

---

## Project layout

```
yt-clipper/
├── main.py                Pipeline A
├── faceless_gen.py        Pipeline B
├── interview_gen.py       Pipeline C
├── reel_gen.py            Pipeline D
├── setup_check.py         Health check + onboarding
├── schedule_clips.py      Schedule uploaded videos
├── src/
│   ├── brand_config.py    Loads config/faceless_brand.json
│   ├── tts.py             GCP Chirp3/Studio/Neural2 + edge-tts fallback
│   ├── script_writer.py   LLM script (B) with quality gate
│   ├── interview_writer.py LLM script (C) with quality gate
│   ├── cta_slide.py       CTA slide from brand config
│   ├── clip_analyzer.py   Two-agent clip finder + reviewer (A)
│   ├── video_cutter.py    Download → vertical → subtitles (A)
│   ├── youtube_uploader.py OAuth2 upload
│   └── ...
├── config/
│   ├── faceless_brand.example.json  ← copy to faceless_brand.json
│   ├── tts.example.json             ← copy to tts.json
│   └── .gitkeep
├── skills/                AI skills for pi / Claude Code
└── assets/                Fonts, logos
```

---

## AI skills

Install skills for your AI coding agent (pi or Claude Code):

```bash
./install_skill.sh        # global — active in all sessions
./install_skill.sh local  # project-only
```

| Skill | Triggers |
|-------|----------|
| `yt-clipper` | "clip this video", "extract shorts", "faceless video", "reel" |
| `viral-video-writing` | "write a script", "hook", "score my draft" |
| `famous-reel-editor` | "edit my raw clip", "reel style" |
| `youtube-manager` | "schedule", "analytics", "channel stats" |
