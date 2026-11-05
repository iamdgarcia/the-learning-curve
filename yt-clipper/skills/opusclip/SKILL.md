---
name: opusclip
description: >
  OpusClip-equivalent pipeline: turns any YouTube video or live stream into
  viral short-form clips ready to publish. Orchestrates AI clip extraction,
  vertical reframing, animated captions, and multi-platform distribution.
  Use when the user says: "clip this video like OpusClip", "create clips from
  this YouTube video", "turn this live stream into Shorts", "make viral clips
  from", "process the whole channel", "generate content from", "clip and publish",
  "extract the best moments", "create short-form content from".
  Do NOT use for: full-video download, audio-only extraction, or video editing
  tasks not related to short-form clip generation.
license: MIT
compatibility: >
  Python 3.10+, ffmpeg, yt-dlp at ~/.local/bin/yt-dlp, Firefox browser.
  GPU (CUDA) recommended for Whisper. Run from __PROJECT_PATH__.
metadata:
  version: "2.0.0"
  author: TheLearningCurveAI
  project-path: __PROJECT_PATH__
---

# OpusClip

Full pipeline replicating OpusClip.com: extract → reframe → caption → publish.

## Route the request

Read the user's goal and choose the right sub-skill:

| Goal | Sub-skill |
|------|-----------|
| Find the best clips / select moments | `opusclip-extract` |
| Change captions style, add emoji, configure subtitles | `opusclip-caption` |
| Change aspect ratio, reframe, face tracking | `opusclip-reframe` |
| Upload to YouTube, process entire channel | `opusclip-publish` |

For a full end-to-end run (most common), use **opusclip-extract** — it invokes
the complete pipeline automatically including reframing, captions, and optional upload.

## Quick start (end-to-end)

```bash
cd __PROJECT_PATH__ && export PATH="$HOME/.local/bin:$PATH"

python main.py \
  --url "YOUTUBE_URL" \
  --max-clips 5 \
  --mode shorts \
  --channel-context "BRIEF CHANNEL DESCRIPTION"
```

## All CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | required | YouTube URL — any format |
| `--max-clips` | 5 | Max clips to keep after filtering |
| `--mode` | `shorts` | `shorts` `standard` `emotion` `topic` |
| `--topic` | — | Topic filter when `--mode topic` |
| `--caption-style` | `karaoke` | `karaoke` `wordbox` `clean` `emoji` |
| `--aspect` | `9:16` | `9:16` `1:1` `16:9` |
| `--channel-context` | generic | Improves LLM clip selection significantly |
| `--privacy` | `unlisted` | `public` `private` `unlisted` |
| `--auto-upload` | off | Upload to YouTube after cutting |

## Clip modes

| Mode | Duration | Best for |
|------|----------|---------|
| `shorts` | 30–90s | Hook-first, scroll-stopping moments |
| `standard` | 2–8min | Educational setup → insight → payoff |
| `emotion` | 30–90s | Reactions, surprise, laughter, "aha!" peaks |
| `topic` | 30–90s | Filter to a specific subject (`--topic "LLMs"`) |

## Caption styles

| Style | Look | Best for |
|-------|------|---------|
| `karaoke` | 3 words, active in yellow | Default TikTok style |
| `wordbox` | Active word in coloured box | Bold, high contrast |
| `clean` | White text only, no highlight | Minimalist / professional |
| `emoji` | karaoke + keyword emoji | High engagement, fun content |

## Channel batch

```bash
python -m src.channel_processor \
  --channel "https://www.youtube.com/@TheLearningCurveAI" \
  --max-videos 10 \
  --min-duration 300 \
  --max-clips-per-video 3 \
  --mode shorts
```

## Troubleshooting

**403 on download** → Firefox must be open and logged into YouTube.
**No clips generated** → All candidates rejected by silence filter or reviewer. Increase `--max-clips`.
**No subtitles** → Whisper fallback activates automatically when YouTube captions are disabled.

For detailed configuration and internals, see [references/internals.md](references/internals.md).
