---
name: youtube-manager
description: >
  Manages a YouTube channel: uploads videos, schedules publications at optimal
  times based on real channel analytics, and generates performance reports.
  Covers traffic sources, device breakdown, top videos by retention, best days
  to publish, and per-video stats. Requires client_secrets.json in config/.
  Use when the user says: "upload to YouTube", "schedule the clips", "publish
  the videos", "show me the analytics", "how are the videos performing",
  "what's the best time to post", "check channel stats", "how many views",
  "schedule for next week", "upload and schedule", "republish", "change privacy".
  Do NOT use for: video editing, clip generation, or transcript extraction —
  those belong to yt-clipper or opusclip skills.
license: MIT
compatibility: >
  Python 3.10+, google-api-python-client, google-auth-oauthlib.
  Requires config/client_secrets.json (OAuth 2.0 Desktop app from Google Cloud).
  Token saved to config/token.json after first auth (auto-refreshes).
  Run from __PROJECT_PATH__.
metadata:
  version: "1.0.0"
  author: TheLearningCurveAI
  project-path: __PROJECT_PATH__
  apis: YouTube Data API v3, YouTube Analytics API v2
---

# YouTube Manager

Upload, schedule, and analyse your YouTube channel from the terminal.

## Setup

### First time — OAuth credentials

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Library
2. Enable **YouTube Data API v3** and **YouTube Analytics API**
3. Credentials → Create Credentials → **OAuth 2.0 Client ID** → Desktop app
4. Download JSON → save as `__PROJECT_PATH__/config/client_secrets.json`
5. Run any command below — browser opens once for consent
6. Token saved to `config/token.json` — all future runs are automatic

### Verify setup

```bash
cd __PROJECT_PATH__
python -c "from src import youtube_analytics; youtube_analytics.report_channel(30)"
```

---

## Phase 1 — Upload already-generated clips

Use when clips are already in `temp/` and metadata in `temp/clips_metadata.json`.

```bash
cd __PROJECT_PATH__

# Upload as unlisted (review before publishing)
python skills/youtube-manager/scripts/upload.py --privacy unlisted

# Upload as private
python skills/youtube-manager/scripts/upload.py --privacy private

# Upload specific clips dir and metadata
python skills/youtube-manager/scripts/upload.py --metadata temp/clips_metadata.json --clips-dir temp
```

**Expected output:**
```
[INFO] Uploading [clip_1_300-360.mp4]: ¡IA juega Flappy Bird!
[INFO]   ✅ https://www.youtube.com/watch?v=VIDEO_ID
```

Saves `temp/uploaded.json` with video IDs for scheduling.

---

## Phase 2 — Schedule publications

Calculates optimal slots based on best practices + adjustable to real channel data.

```bash
# Schedule from uploaded.json (auto-detects optimal days/times)
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json

# Preview schedule without applying
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --dry-run

# Pass video IDs directly
python skills/youtube-manager/scripts/schedule.py --video-ids ID1 ID2 ID3 --dry-run

# Schedule starting from a specific date
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --start 2026-11-01
```

**Scheduling strategy (Spain audience):**
- Preferred slots: Sun/Fri 14:00, Thu 14:00, Sat 11:00, Mon/Tue 14:00
- Minimum gap: 2 days between clips
- Clips sorted by virality score (best clip first)
- Videos set to `private` + `publishAt` → auto-public at scheduled time

**Expected output:**
```
📅 PUBLISHING SCHEDULE
#   Date & Time (Spain)    Video ID       Title
1   Domingo 26/10 14:00    abc123xyz      ¡IA juega Flappy Bird!
2   Martes  28/10 14:00    def456uvw      La CLAVE: probabilidades reales
```

---

## Phase 3 — Analytics

### Channel overview

```bash
python -m src.youtube_analytics --report channel --days 90
```

Returns: views, avg view duration, watch minutes, subs gained/lost, likes, shares.

### Top performing videos

```bash
python -m src.youtube_analytics --report top-videos --days 90 --limit 15
```

Returns: views, watch minutes, avg duration, retention % per video. Marks 🩳 Shorts vs 🎬 Long.

### Traffic sources

```bash
python -m src.youtube_analytics --report traffic --days 30
```

Returns: SHORTS, SUBSCRIBER, YT_SEARCH, RELATED_VIDEO, EXT_URL breakdown with %.

### Best days to publish (real data)

```bash
python -m src.youtube_analytics --report schedule-insights --days 30
```

Returns: avg views by weekday from actual channel data. Use this to override the default schedule slots.

### Device breakdown

```bash
python -m src.youtube_analytics --report devices --days 90
```

Returns: MOBILE, DESKTOP, TABLET, TV breakdown.

### Single video stats

```bash
python -m src.youtube_analytics --report video --id VIDEO_ID
```

Returns: views, likes, comments, retention %, avg view duration, privacy status, scheduled publish time.

---

## Full workflow example

```bash
cd __PROJECT_PATH__ && export PATH="$HOME/.local/bin:$PATH"

# 1. Check current channel state
python -m src.youtube_analytics --report channel --days 30

# 2. See what's performing (informs clip selection strategy)
python -m src.youtube_analytics --report top-videos --days 90

# 3. Upload generated clips
python skills/youtube-manager/scripts/upload.py --privacy unlisted

# 4. Get real best-day data
python -m src.youtube_analytics --report schedule-insights --days 30

# 5. Schedule
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --dry-run
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json

# 6. Verify scheduled clips
python -m src.youtube_analytics --report video --id VIDEO_ID
```

---

## Success criteria

- `upload_ready_clips.py`: all mp4s in temp/ uploaded, `temp/uploaded.json` created
- `schedule_clips.py`: all videos show `private + publishAt` in YouTube Studio → Scheduled
- Analytics commands print tables without errors
- `config/token.json` exists and auto-refreshes (no browser needed after first run)

---

## Troubleshooting

### Error: `insufficientPermissions` on schedule

**Cause:** token.json was created with only `youtube.upload` scope.
**Solution:**
```bash
rm __PROJECT_PATH__/config/token.json
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json
# Browser opens → authorize again with full scopes
```

### Error: `YouTube Analytics API has not been enabled`

**Cause:** API not enabled in Google Cloud project.
**Solution:** Visit the URL in the error message → click Enable → wait 2 min → retry.

### Error: `client_secrets.json not found`

**Cause:** Credentials not set up.
**Solution:** Follow the First time — OAuth credentials section above.

### Video stuck as `unlisted` after scheduling

**Cause:** `publishAt` only works with `privacyStatus: private`, not `unlisted`.
**Solution:** `schedule_clips.py` sets `private` automatically. If video was unlisted, re-run the scheduler — it will update the status correctly.

### Analytics returns no data for recent videos

**Cause:** YouTube Analytics has a 2-3 day lag for new videos.
**Solution:** Wait 48-72h after publishing, then run analytics.

---

## Key files

| File | Purpose |
|------|---------|
| `config/client_secrets.json` | OAuth credentials (never commit) |
| `config/token.json` | Active session token (auto-managed) |
| `src/youtube_uploader.py` | Core upload logic |
| `src/youtube_analytics.py` | All analytics reports |
| `upload_ready_clips.py` | CLI: upload clips from temp/ |
| `schedule_clips.py` | CLI: schedule uploaded videos |
| `temp/uploaded.json` | Video IDs + titles after upload |
| `temp/schedule.json` | Schedule record |
| `temp/failed_uploads.json` | Failed uploads queue (retry next day) |

For API quota, metrics reference, and advanced analytics queries,
see [references/analytics-reference.md](references/analytics-reference.md).
