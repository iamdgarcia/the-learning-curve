# yt-clipper — Internal Reference

Load this file when the user asks about tuning, debugging source code, or modifying pipeline behaviour.

## Source modules

| File | Responsibility |
|------|----------------|
| `src/transcript_extractor.py` | YouTube captions → Whisper fallback; language auto-detection via yt-dlp |
| `src/clip_analyzer.py` | Two-agent LLM pipeline; `ClipMode.shorts` / `ClipMode.standard` |
| `src/frame_analyzer.py` | Face detection (Haar cascade); activity center (frame differencing) |
| `src/video_cutter.py` | Download → silence check → face/zoom → vertical → subtitles |
| `src/subtitle_generator.py` | ASS file with TikTok karaoke style (3 words, yellow active word) |
| `src/youtube_uploader.py` | OAuth2 + resumable upload; quota error handling |
| `src/config.py` | Pydantic settings loaded from `.env` |
| `main.py` | CLI entry point; appends redirect footer to descriptions |

## Tuning parameters

| Constant | File | Default | Effect |
|----------|------|---------|--------|
| `FACE_RATIO` | `video_cutter.py` | `0.38` | Fraction of vertical height for face panel |
| `WORDS_PER_PHRASE` | `subtitle_generator.py` | `3` | Words per subtitle block |
| `SILENCE_MAX` | `video_cutter.py` | `0.40` | Max silent fraction before clip is rejected |
| `SILENCE_DUR` | `video_cutter.py` | `1.5` | Minimum silence stretch (seconds) to count |
| `PADDING` | `video_cutter.py` | `10` | Seconds of padding each side for precise trim |
| `CLIP_MODE_CONFIG` | `clip_analyzer.py` | shorts: 30–90s | Duration ranges per mode |

## Pipeline deep-dive

1. **Transcript** — `youtube-transcript-api` fetches captions. If disabled, yt-dlp downloads full audio (HLS m3u8) → Whisper `small` on GPU transcribes with `word_timestamps=True`.
2. **Two-agent LLM** — Agent 1 (Finder) proposes `max_clips × 2` candidates with rationale + hook. Agent 2 (Reviewer) scores each 1–10; rejects <7 with reason; trims timestamps ±10s for cleaner cuts.
3. **Download** — yt-dlp tries HTTPS best quality first; on 403 retries with HLS (m3u8). Selects original-language audio with `bestaudio[language^={lang}]`.
4. **Silence check** — ffmpeg `silencedetect` on the downloaded segment. Raises `RuntimeError` if >40% is silent.
5. **Face detection** — OpenCV Haar cascade. Largest detection per frame; median across 12 sampled frames. Expanded to a square panel centered on the face centroid.
6. **Activity zoom** — Frame differencing on the screen region of the raw tmp file. Weighted centroid of the top-15% motion pixels determines crop center. ~1.6× zoom.
7. **Vertical conversion** — ffmpeg `filter_complex`: face panel (top 38%) + zoomed screen (bottom 62%) → 1080×1920. All dimensions forced even.
8. **Subtitles** — Whisper `small` transcribes just the clip audio (0..duration seconds, no drift). Generates ASS with TikTok karaoke: 3 words per event, active word in yellow (`&H0000FFFF`), 400px from bottom.
9. **Upload** — YouTube Data API v3 resumable upload. `quotaExceeded` 403 caught and queued.

## Description footer template

```
{LLM description with hashtags}

📺 Video completo: https://youtu.be/{video_id}?t={start_seconds}
🔔 Suscríbete: https://www.youtube.com/@ChannelHandle
```

## LLM configuration

Uses any OpenAI-compatible API. Current default: Novita.ai / DeepSeek v3.
To switch to OpenAI: set `NOVITA_BASE_URL=https://api.openai.com/v1` and `NOVITA_MODEL=gpt-4o-mini`.
