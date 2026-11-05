---
name: opusclip-extract
description: >
  AI clip extraction: finds the most viral moments in a YouTube video using a
  two-agent LLM pipeline (Finder + Reviewer). Supports four extraction modes:
  spoken-word relevance, emotional peaks, topic filtering, and standard educational arcs.
  Each clip gets a virality score, hook, title, description, and redirect link.
  Use when the user says: "find the best clips", "extract viral moments",
  "clip by emotion", "find clips about [topic]", "score the clips", "re-clip with
  different criteria", "find funny moments", "find the aha moments",
  "clip only the parts about X", "extract shorts from this live stream".
  Do NOT use for: reframing, caption styling, or uploading — those are separate sub-skills.
license: MIT
compatibility: >
  Python 3.10+, Novita API key in .env. Run from __PROJECT_PATH__.
metadata:
  version: "2.0.0"
  author: TheLearningCurveAI
---

# OpusClip — Extract

Find viral moments using a two-agent LLM pipeline.

## Extraction modes

### Mode: `shorts` (default)
Hook-first moments, scroll-stopping energy, 30–90s.

```bash
python main.py --url "URL" --max-clips 5 --mode shorts \
  --channel-context "CHANNEL DESCRIPTION"
```

### Mode: `emotion`
Surprise, laughter, frustration → resolution, genuine "aha!" peaks.

```bash
python main.py --url "URL" --max-clips 5 --mode emotion \
  --channel-context "CHANNEL DESCRIPTION"
```

Emotion clips are scored highest when there's an audible reaction, an unexpected
turn, or a visibly relatable human moment in the first 5 seconds.

### Mode: `topic`
Only clips directly about a specific subject.

```bash
python main.py --url "URL" --max-clips 5 --mode topic \
  --topic "probabilidades en LLMs" \
  --channel-context "CHANNEL DESCRIPTION"
```

The reviewer rejects clips where the topic is only mentioned in passing.

### Mode: `standard`
2–8 min clips with clear 3-part arc: setup → insight → payoff.
Best for educational/tutorial content.

```bash
python main.py --url "URL" --max-clips 3 --mode standard \
  --channel-context "CHANNEL DESCRIPTION"
```

## Two-agent pipeline

**Agent 1 (Finder)** — scans the transcript, proposes `max_clips × 2` candidates
with a rationale and verbatim hook for each.

**Agent 2 (Reviewer)** — scores each 1–10, rejects <7 with a reason,
trims timestamps ±10s for cleaner cuts, writes final title/description/tags/hook.
Rejected clips are logged: `[INFO] ✗ clip_N: REASON`.

## Output

```
temp/clips_metadata.json   ← titles, descriptions, scores, hooks, tags
temp/clip_N_START-END.mp4  ← one per approved clip
```

Each clip in `clips_metadata.json`:
```json
{
  "clip_id": 3,
  "start_seconds": 371, "end_seconds": 411,
  "title": "El TRUCO para leer probabilidades de un LLM",
  "description": "Convertir clasificación en single token... #IA #LLM",
  "tags": ["IA", "LLM", "probabilidades"],
  "hook": "El truco: convertir clasificación en un problema de single token.",
  "score": 8,
  "mode": "shorts",
  "full_description": "...description...\n\n📺 Video completo: https://youtu.be/ID?t=371\n🔔 Suscríbete: ..."
}
```

## Reprompt / refine

To re-run with different criteria without re-downloading:

```bash
# Different mode
python main.py --url "URL" --max-clips 8 --mode emotion

# Topic focus
python main.py --url "URL" --max-clips 5 --mode topic --topic "Docker"

# Increase clips if too few approved
python main.py --url "URL" --max-clips 10 --mode shorts
```

## Success criteria

- `[INFO] Found N clips.` → N ≥ 1
- Each mp4 exists in `temp/` and is non-empty
- `clips_metadata.json` has `score` ≥ 7 for every entry
- Log shows rejected clips with reasons (normal)
- Silence-rejected clips show `Clip contains XX% silence` (expected, not an error)

## Troubleshooting

### All clips rejected

**Cause:** Reviewer score threshold (≥7) too strict for this content type.
**Solution:** Try `--mode emotion` or `--mode topic` with a specific subject.
Also try increasing `--max-clips` to give the reviewer more candidates.

### Transcript error

**Cause:** YouTube captions disabled.
**Solution:** Whisper fallback activates automatically. Wait 2–10 min for transcription.
GPU (`cuda`) makes this ~10× faster.

### Wrong language in titles/descriptions

**Cause:** YouTube auto-detects wrong language or no language tag.
**Solution:** Check `.env` and verify `NOVITA_MODEL` is set to a multilingual model.
The pipeline auto-detects language from yt-dlp metadata.
