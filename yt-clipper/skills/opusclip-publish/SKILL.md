---
name: opusclip-publish
description: >
  Publish short-form clips to YouTube and batch-process entire channels.
  Handles YouTube OAuth, resumable upload, privacy settings, and automatic
  description with redirect link to the original video at the exact timestamp.
  Also supports batch processing an entire YouTube channel: list videos, filter
  by duration, and run the full clip pipeline on each.
  Use when the user says: "upload the clips", "publish to YouTube", "upload as unlisted",
  "make them public", "process the whole channel", "batch process all videos from",
  "auto-upload", "schedule for upload", "upload with the redirect link",
  "process @TheLearningCurveAI channel", "clip all videos from this channel",
  "generate content from the whole channel".
  Do NOT use for: clip extraction or video editing — those are separate sub-skills.
license: MIT
compatibility: >
  Python 3.10+, google-api-python-client, config/client_secrets.json for upload.
  Run from __PROJECT_PATH__.
metadata:
  version: "2.0.0"
  author: TheLearningCurveAI
---

# OpusClip — Publish

Upload clips to YouTube and batch-process entire channels.

## Single video: generate + upload

```bash
cd __PROJECT_PATH__ && export PATH="$HOME/.local/bin:$PATH"

python main.py \
  --url "YOUTUBE_URL" \
  --max-clips 5 \
  --mode shorts \
  --channel-context "CHANNEL DESCRIPTION" \
  --auto-upload \
  --privacy unlisted
```

First run opens a browser for YouTube OAuth. Token saved to `config/token.json`
for all future runs (auto-refreshes when expired).

## Privacy options

| Value | Visible to | Use case |
|-------|-----------|---------|
| `unlisted` | Anyone with the link | Review before publishing |
| `public` | Everyone | Direct publish |
| `private` | Only you | Archive only |

## Description format

Every uploaded clip gets this description automatically:

```
{LLM-generated description with hashtags}

📺 Video completo: https://youtu.be/{video_id}?t={start_seconds}
🔔 Suscríbete: https://www.youtube.com/@ChannelHandle
```

The timestamp link sends viewers directly to the source moment.
Edit the channel handle in `main.py` → `_channel` variable.

## YouTube quota

Each upload costs ~1,600 units. Daily quota: 10,000 units (~6 uploads/day).
Failed uploads are queued in `temp/failed_uploads.json`.

Retry the next day:
```bash
python main.py --url "URL" --max-clips 5 --auto-upload --privacy unlisted
```

## Batch channel processing

Process all qualifying videos from a channel:

```bash
python -m src.channel_processor \
  --channel "https://www.youtube.com/@TheLearningCurveAI" \
  --max-videos 10 \
  --min-duration 300 \
  --max-clips-per-video 3 \
  --mode shorts \
  --channel-context "TheLearningCurveAI, Python, IA, live coding"
```

Add `--auto-upload --privacy unlisted` to upload each batch automatically.

### Batch flags

| Flag | Default | Description |
|------|---------|-------------|
| `--channel` | required | Channel URL |
| `--max-videos` | 5 | Max videos to process |
| `--min-duration` | 300 | Minimum video duration in seconds (skip shorts/trailers) |
| `--max-clips-per-video` | 3 | Clips to extract per video |
| `--mode` | `shorts` | Extraction mode for all videos |
| `--channel-context` | — | LLM context shared across all videos |
| `--caption-style` | `karaoke` | Caption style for all clips |
| `--aspect` | `9:16` | Aspect ratio for all clips |
| `--auto-upload` | off | Upload each batch after cutting |
| `--privacy` | `unlisted` | Privacy for all uploads |

### Batch output structure

```
temp/
├── {video_id_1}/
│   └── clips_metadata.json
├── {video_id_2}/
│   └── clips_metadata.json
└── clips_metadata.json        ← last video processed
```

## OAuth setup (first time only)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable YouTube Data API v3
3. Create OAuth 2.0 Client ID (Desktop app)
4. Download JSON → save as `config/client_secrets.json`
5. Run any `--auto-upload` command → browser opens for consent
6. Token saved to `config/token.json` automatically

## Troubleshooting

### Error: `quota exceeded (403)`

**Cause:** Daily 10,000-unit limit reached.
**Solution:** Failed clips saved to `temp/failed_uploads.json`. Retry tomorrow.

### Error: `client_secrets.json not found`

**Cause:** OAuth credentials not set up.
**Solution:** Follow OAuth setup steps above.

### Token expired

**Cause:** Refresh token invalid (happens if app permissions revoked).
**Solution:** Delete `config/token.json` and re-run — browser opens again.

### Batch: some videos skipped

**Cause:** Videos shorter than `--min-duration` or all clips silence-rejected.
**Solution:** Check logs for `[ERROR] Clip contains XX% silence`.
Lower `--min-duration` or use `--mode emotion` for more lenient selection.
