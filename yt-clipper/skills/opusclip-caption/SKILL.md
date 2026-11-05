---
name: opusclip-caption
description: >
  AI captions and subtitles for short-form clips. Generates TikTok-style animated
  word-by-word captions in four visual styles: karaoke (yellow highlight), wordbox
  (colour box), clean (minimal white), and emoji (keyword-triggered emoji injection).
  Supports multi-language transcription via Whisper. Captions are burned into the
  video, not as a separate track.
  Use when the user says: "change the caption style", "add emoji to captions",
  "use wordbox style", "minimal captions", "no captions", "subtitle style",
  "add emojis to the subtitles", "make captions like TikTok", "change font style",
  "caption template", "animated captions", "highlight current word".
  Do NOT use for: clip extraction or reframing — those are separate sub-skills.
license: MIT
compatibility: >
  Python 3.10+, ffmpeg with ASS filter, Whisper (GPU recommended).
  Run from __PROJECT_PATH__.
metadata:
  version: "2.0.0"
  author: TheLearningCurveAI
---

# OpusClip — Caption

Generate animated TikTok-style captions burned into the clip.

## Caption styles

### `karaoke` (default)
3 words per line. Active word turns **yellow**. Rest stays white.
Mimics TikTok's standard caption look.

```bash
python main.py --url "URL" --caption-style karaoke
```

### `wordbox`
3 words per line. Active word highlighted with an **orange solid background box**.
High contrast, works well on any background.

```bash
python main.py --url "URL" --caption-style wordbox
```

### `clean`
White text only. No per-word highlight. Pure minimal look.
Best for professional or educational content.

```bash
python main.py --url "URL" --caption-style clean
```

### `emoji`
Same as `karaoke` + automatically injects contextually relevant emoji after
trigger keywords (e.g. "gratis" → 🎁, "error" → ❌, "python" → 🐍,
"modelo" → 🤖, "ia" → 🤖, "probabilidad" → 📈).

```bash
python main.py --url "URL" --caption-style emoji
```

## Caption positioning

Captions are positioned 400px from the bottom of the 1920px tall output.
This places them inside the screen panel (bottom 62%), above any channel overlay.

To adjust: edit `MarginV` in `src/subtitle_generator.py` → `_header()`.

## Multi-language

Captions are generated from Whisper word-level timestamps on the clip audio.
Language is auto-detected — no flag needed. If the video is in Spanish,
captions will be in Spanish.

For YouTube videos with existing captions, Whisper is still used for
word-level timestamps (YouTube captions only have segment-level timing).

## Sync accuracy

Subtitles are generated from Whisper running on the **clip audio** (not the
full video), so timestamps are always 0..clip_duration. No drift possible.

GPU transcription of a 60s clip takes ~5 seconds.
CPU transcription takes ~60 seconds.

## Example output frame

```
[face panel — top 38%]
─────────────────────────────────────────
[screen panel — bottom 62%]
    ...code/content visible...
    
  ← 400px from bottom →
  convierte  clasificación  en  TOKEN
              ←active→
```

## Emoji keyword map

Current keywords (ES/EN):
- gratis/free → 🎁, dinero/money → 💰, error → ❌, funciona/works → ✅
- rápido/fast → ⚡, fácil/easy → 🙌, problema/problem → ⚠️
- modelo/model → 🤖, ia/ai → 🤖, código/code → 💻
- python → 🐍, datos → 📊, probabilidad → 📈

To add keywords: edit `_EMOJI_MAP` in `src/subtitle_generator.py`.

## Troubleshooting

### Captions cut off at edges

**Cause:** MarginL/MarginR too small for long words.
**Solution:** Reduce font size (default 85) in `_header()` in `subtitle_generator.py`,
or reduce `WORDS_PER_PHRASE` from 3 to 2.

### No captions visible

**Cause:** ffmpeg ASS filter path issue or Whisper failed silently.
**Solution:** Check for `[WARNING] Subtitle generation failed` in logs.
The clip is saved without subtitles in that case.

### Captions in wrong language

**Cause:** Whisper chose wrong language (e.g., short clip with ambient noise).
**Solution:** Check GPU availability — CPU Whisper on short clips can misdetect language.
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
