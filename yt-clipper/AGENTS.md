# AGENTS.md — yt-clipper

This file is read by AI coding agents entering this repository.

## What this repo is

A self-hosted OpusClip-equivalent: clips YouTube videos into vertical Shorts,
uploads to YouTube, and analyses channel performance. Everything is Python + ffmpeg.

## Before you do anything

```bash
cd /home/developer/proyectos/tlc/yt-clipper
export PATH="$HOME/.local/bin:$PATH"   # yt-dlp binary lives here
python -c "from src import video_cutter, clip_analyzer; print('OK')"
```

If that fails, check `requirements.txt` and run `pip install -r requirements.txt`.

## Key facts an agent must know

### Runtime
- Python 3.10 (system). Modules in `src/`. Entry point: `main.py`.
- Always `cd` to repo root and `export PATH="$HOME/.local/bin:$PATH"` first.
- `.env` must exist (copy from `.env.example`, fill `NOVITA_API_KEY`).

### LLM
- Uses Novita.ai (OpenAI-compatible) via `NOVITA_API_KEY` + `NOVITA_BASE_URL`.
- Model: `deepseek/deepseek_v3`. No `response_format: json_object` support → strips markdown fences manually.
- Config: `src/config.py` → Pydantic settings.

### Video download
- `yt-dlp` binary at `~/.local/bin/yt-dlp` (newer than pip version).
- Uses `--cookies-from-browser firefox` — Firefox must be open for live streams.
- Format: `bestvideo[protocol^=m3u8]+bestaudio[language^={lang}][protocol^=m3u8]` (HLS to avoid 403).
- Padding: downloads ±10s around requested segment, ffmpeg trims precisely with `-t {duration}`.

### Critical bug to avoid
- Audio must be trimmed with `-t {duration}` in the ffmpeg vertical conversion command.
- Without it: video=60s, audio=80s → frozen last frame for 20s. Already fixed in `_build_vf()`.

### Face detection
- OpenCV Haar cascade, auto-downloaded to `~/.cache/yt-clipper/` on first use.
- `minSize` = 5% of frame width. Takes largest detection per frame. Median across 12 frames.
- Panel expanded to square centered on face, clamped to frame height (`min(panel_w, fh)`).

### Subtitles
- Whisper `small` on GPU (cuda:0). Transcribes CLIP audio (not full video) → timestamps 0..duration.
- ASS file: 3 words per phrase, active word coloured (yellow by default, or speaker colour if diarized).
- Speaker diarizer uses Resemblyzer embeddings → AgglomerativeClustering → 5 OpusClip colours.

### YouTube OAuth
- `config/client_secrets.json` required (OAuth 2.0 Desktop app from Google Cloud).
- Token saved to `config/token.json` after first browser auth.
- Scopes needed for full functionality: `youtube`, `youtube.upload`, `yt-analytics.readonly`.
- If `insufficientPermissions`: delete `config/token.json` and re-run.

### Skills
- 7 skills in `skills/`. Install with `./install_skill.sh`.
- All skills use `__PROJECT_PATH__` placeholder replaced at install time.
- Skills follow Anthropic's Agent Skills standard + REA's pattern (route-first, progressive disclosure).

## Module map (src/)

```
config.py            Pydantic settings from .env
transcript_extractor YT captions → Whisper fallback, language auto-detect
clip_analyzer        Two-agent LLM: Finder + Reviewer, 4 modes (shorts/standard/emotion/topic)
frame_analyzer       Face detection + activity center (frame differencing)
video_cutter         Full pipeline: download → silence → face/zoom → vertical → subs → hook → broll
subtitle_generator   ASS TikTok captions, 4 styles (karaoke/wordbox/clean/emoji), speaker colours
speaker_diarizer     Resemblyzer voice embeddings → speaker segments
hook_overlay         ffmpeg drawtext, 5 templates, fade in/out
audio_enhancer       noisereduce NR → clean audio
broll_inserter       Pexels API → ffmpeg overlay
channel_processor    Batch: list channel → pipeline per video
youtube_uploader     OAuth2 resumable upload, quota handling
youtube_analytics    Analytics API: channel/top-videos/traffic/devices/schedule-insights/video
```

## CLI scripts (repo root)

```
main.py                  Full pipeline CLI
upload_ready_clips.py    Upload clips from temp/ to YouTube
schedule_clips.py        Schedule uploaded videos at optimal times
```

## Output structure

```
temp/
  clip_{id}_{start}-{end}.mp4    1080×1920, subtitles + hook burned in
  clips_metadata.json             LLM-generated titles/descriptions/tags/scores
  uploaded.json                   video IDs after upload
  schedule.json                   publish schedule
  failed_uploads.json             quota failures
config/
  client_secrets.json             OAuth credentials (gitignored)
  token.json                      Active token (gitignored)
```

## What NOT to do

- Do NOT modify `config/token.json` manually.
- Do NOT use `python -m yt_dlp` as primary — always prefer the binary at `~/.local/bin/yt-dlp`.
- Do NOT remove `-t {duration}` from the ffmpeg command in `video_cutter._build_vf()`.
- Do NOT set `response_format: json_object` — Novita/DeepSeek doesn't support it.
- Do NOT commit `config/client_secrets.json` or `config/token.json` (both in `.gitignore`).
