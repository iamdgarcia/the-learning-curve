# yt-clipper — OpusClip-equivalent pipeline

📖 **[Arquitectura visual del pipeline →](docs/pipeline.html)**

Automated pipeline that turns any YouTube video or live stream into
viral short-form clips, uploads them to YouTube, and analyses channel performance.
Replicates the core of [OpusClip](https://www.opus.pro) as a self-hosted CLI.

---

## What it does

```
YouTube URL
    │
    ├─ Transcript (YT captions → Whisper fallback)
    ├─ Two-agent LLM  (Finder proposes → Reviewer scores & filters)
    ├─ Download       (yt-dlp HLS, original-language audio, max quality)
    ├─ Silence check  (rejects dead air / stream exits)
    ├─ Face detection (OpenCV Haar cascade, dynamic per clip)
    ├─ Activity zoom  (frame differencing → cursor/motion center, ~1.6×)
    ├─ Audio enhance  (noisereduce NR)
    ├─ Vertical conv  (1080×1920: face panel top 38% + zoomed screen 62%)
    ├─ Diarization    (Resemblyzer speaker colours in subtitles)
    ├─ Subtitles      (Whisper on clip audio → word-level ASS, 4 styles)
    ├─ Hook overlay   (ffmpeg drawtext, 5 templates, 3s animated)
    ├─ B-roll         (Pexels API → ffmpeg composite, optional)
    └─ YouTube        (upload + smart schedule via Analytics API)
```

---

## Quick start

### 1. System dependencies

```bash
# ffmpeg (required)
sudo apt install ffmpeg

# yt-dlp binary — newer than pip version, avoids 403s
curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
  -o ~/.local/bin/yt-dlp && chmod +x ~/.local/bin/yt-dlp
export PATH="$HOME/.local/bin:$PATH"   # add to ~/.bashrc
```

### 2. Python environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Fill in: NOVITA_API_KEY (or any OpenAI-compatible key)
```

### 4. First run

```bash
python main.py \
  --url "https://youtu.be/VIDEO_ID" \
  --max-clips 5 \
  --mode shorts \
  --channel-context "Brief channel description"
```

Clips land in `temp/`. Add `--auto-upload --privacy unlisted` to upload directly.

---

## Full CLI reference

```bash
python main.py \
  --url            "URL"          # Any YouTube URL format
  --max-clips      5              # Max clips after reviewer filtering
  --mode           shorts         # shorts | standard | emotion | topic
  --topic          "LLMs"         # Filter by topic (--mode topic)
  --caption-style  karaoke        # karaoke | wordbox | clean | emoji
  --aspect         9:16           # 9:16 | 1:1 | 16:9
  --channel-context "..."         # Improves LLM clip selection
  --hook                          # Burn hook text overlay (first 3s)
  --hook-template  hook-02        # hook-01…05
  --enhance-audio                 # Noise reduction
  --diarize                       # Speaker colours in subtitles
  --broll                         # B-roll from Pexels (needs PEXELS_API_KEY)
  --auto-upload                   # Upload to YouTube after cutting
  --privacy        unlisted       # public | private | unlisted
```

### Clip modes

| Mode | Duration | Selects |
|------|----------|---------|
| `shorts` | 30–90s | Hook-first, scroll-stopping moments |
| `standard` | 2–8min | Setup → insight → payoff arc |
| `emotion` | 30–90s | Emotional peaks, reactions, "aha!" moments |
| `topic` | 30–90s | Only clips about `--topic` |

### Caption styles

| Style | Look |
|-------|------|
| `karaoke` | 3 words, active word yellow (default TikTok) |
| `wordbox` | Active word in orange/cyan box |
| `clean` | White text only, no highlight |
| `emoji` | Karaoke + auto emoji on keywords (🤖💡⚡...) |

---

## YouTube upload & scheduling

### Upload already-generated clips

```bash
# Clips already in temp/ from a previous run
python upload_ready_clips.py --privacy unlisted
```

### Schedule for optimal publish times

```bash
# Preview schedule (no changes)
python schedule_clips.py --from-file temp/uploaded.json --dry-run

# Apply schedule
python schedule_clips.py --from-file temp/uploaded.json

# Custom start date
python schedule_clips.py --from-file temp/uploaded.json --start 2026-11-01
```

Scheduling strategy (Spain tech audience):
- Preferred: **Sunday/Friday 14:00**, Thursday 14:00, Saturday 11:00
- Minimum 2-day gap between clips
- Videos set to `private + publishAt` → auto-public at scheduled time
- Override with real channel data: `python -m src.youtube_analytics --report schedule-insights`

### YouTube OAuth setup (first time)

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services
2. Enable **YouTube Data API v3** and **YouTube Analytics API**
3. Credentials → OAuth 2.0 Client ID → Desktop app → Download JSON
4. Save as `config/client_secrets.json`
5. Run any upload/schedule command → browser opens once → `config/token.json` saved

---

## Analytics

```bash
# Channel overview (last 90 days)
python -m src.youtube_analytics --report channel --days 90

# Top videos by views + retention
python -m src.youtube_analytics --report top-videos --days 90 --limit 15

# Traffic sources (SHORTS, SEARCH, SUBSCRIBER...)
python -m src.youtube_analytics --report traffic --days 30

# Best days to publish (from real channel data)
python -m src.youtube_analytics --report schedule-insights --days 30

# Device breakdown (MOBILE, DESKTOP, TV...)
python -m src.youtube_analytics --report devices

# Single video stats + retention
python -m src.youtube_analytics --report video --id VIDEO_ID
```

---

## Channel batch processing

```bash
python -m src.channel_processor \
  --channel "https://www.youtube.com/@ChannelHandle" \
  --max-videos 10 \
  --min-duration 300 \
  --max-clips-per-video 3 \
  --mode shorts \
  --caption-style emoji \
  --hook --hook-template hook-02 \
  --enhance-audio --diarize
```

---

## Pi Skills suite

Install all 7 skills globally (active in all pi sessions):

```bash
./install_skill.sh           # global (default)
./install_skill.sh local     # project-only
./install_skill.sh both      # both
```

| Skill | Triggers | Purpose |
|-------|----------|---------|
| `yt-clipper` | "clip this video" | Core pipeline |
| `opusclip` | "like OpusClip", "process channel" | Orchestrator |
| `opusclip-extract` | "find viral moments", "clip by emotion" | AI extraction |
| `opusclip-caption` | "caption style", "add emoji" | Subtitle styles |
| `opusclip-reframe` | "reframe", "9:16", "face tracking" | Vertical conversion |
| `opusclip-publish` | "upload", "process whole channel" | Distribution |
| `youtube-manager` | "upload", "schedule", "analytics", "channel stats" | YouTube management |

Verify: `pi skill list` — Force-load: `/skill:opusclip`

---

## Source modules

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point — orchestrates full pipeline |
| `src/config.py` | Pydantic settings from `.env` |
| `src/transcript_extractor.py` | YT captions → Whisper fallback; language auto-detection |
| `src/clip_analyzer.py` | Two-agent LLM (Finder + Reviewer); 4 clip modes |
| `src/frame_analyzer.py` | Face detection (Haar cascade); activity zoom (frame diff) |
| `src/video_cutter.py` | Download → silence check → vertical → subs → hook → B-roll |
| `src/subtitle_generator.py` | ASS TikTok captions (4 styles, word-level, speaker colours) |
| `src/speaker_diarizer.py` | Resemblyzer voice embeddings → speaker segments + colours |
| `src/hook_overlay.py` | ffmpeg drawtext hook overlay (5 templates, fade in/out) |
| `src/audio_enhancer.py` | noisereduce NR → clean audio track |
| `src/broll_inserter.py` | Pexels keyword search → ffmpeg overlay (optional) |
| `src/channel_processor.py` | Batch: list channel videos → pipeline per video |
| `src/youtube_uploader.py` | OAuth2 resumable upload; quota error handling |
| `src/youtube_analytics.py` | Analytics API: channel, top videos, traffic, devices, schedule |
| `upload_ready_clips.py` | Upload clips already in temp/ |
| `schedule_clips.py` | Schedule uploaded videos at optimal times |

---

## Output files

```
temp/
├── clip_{id}_{start}-{end}.mp4    # 1080×1920 final clip (subs + hook burned in)
├── clips_metadata.json             # titles, descriptions, tags, scores, full_description
├── uploaded.json                   # video IDs + titles after upload
├── schedule.json                   # publish schedule record
└── failed_uploads.json             # quota failures (retry next day)
```

Each clip's `full_description` contains the redirect link:
```
{LLM description with hashtags}

📺 Video completo: https://youtu.be/{video_id}?t={start_seconds}
🔔 Suscríbete: https://www.youtube.com/@ChannelHandle
```

---

## Known constraints

| Constraint | Detail |
|------------|--------|
| yt-dlp binary | Must be `~/.local/bin/yt-dlp` (binary). `export PATH="$HOME/.local/bin:$PATH"` required |
| Firefox cookies | yt-dlp uses `--cookies-from-browser firefox` for live stream 403 bypass |
| Live stream quality | YouTube caps live VOD at ~300–400 kbps. Normal VODs are better |
| Whisper GPU | `small` model on CPU takes ~1 min/clip. GPU (CUDA) recommended |
| Haar cascade | Auto-downloaded on first use → `~/.cache/yt-clipper/` |
| YouTube quota | 1,600 units/upload, 10,000/day (~6 uploads/day max) |
| Analytics lag | YouTube Analytics has 2–3 day lag for new videos |
| B-roll | Requires `PEXELS_API_KEY` in `.env` |

---

## Troubleshooting

**403 on download** → Firefox must be open and logged into YouTube.

**`No subtitles available`** → Whisper fallback activates automatically.

**Frozen last frame** → Fixed: `-t {duration}` truncates all streams to exact clip length.

**Face not detected** → Haar cascade downloads on first use. If still failing:
```bash
python -c "from src.frame_analyzer import analyze; print(analyze('temp/clip.mp4').face)"
```

**`insufficientPermissions` on schedule** → Delete `config/token.json` and re-run (re-auth with full scopes).

**`dayOfWeek` analytics error** → Use `--report schedule-insights` which derives DOW from daily dimension.
