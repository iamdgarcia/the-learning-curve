---
name: yt-clipper
description: >
  Create and operate TheLearningCurveAI's Spanish short-form video pipelines:
  clip YouTube videos into viral Shorts (Pipeline A), generate branded faceless
  AI Shorts (B), produce animated AI explainers (C), or edit talking-head reels
  (D). Use for requests to clip a YouTube URL, extract viral moments, create
  faceless/trending AI content, animate a technical explainer, or turn raw
  talking-head footage into a reel. Applies TLC branding and karaoke captions;
  Pipeline A can upload and schedule when requested. Do not use for ordinary
  long-form editing or audio-only extraction.

license: MIT
metadata:
  author: TheLearningCurveAI (Daniel García — iamdgarcia)
  version: 3.2.0
  project-path: /home/developer/proyectos/tlc/yt-clipper
  compatibility: Python 3.10+, ffmpeg, yt-dlp, Firefox, edge-tts, Google Cloud TTS, Playwright, Claude CLI, manim, Node.js
---

# yt-clipper — Content pipelines for @TheLearningCurveAI

Four pipelines, one brand. All videos share:
- **Palette**: Substack orange `#FF6719`, warm white `#FAFAF9`, grid `#E8E4DC`
- **Logo**: `assets/logos/tlc_logo.png` injected bottom-right via Playwright on every frame
- **CTA**: fixed slide — `src/cta_slide.py` — orange bg, TLC logo, tagline, Substack screenshot, "Suscríbete gratis →", `iamdgarcia.substack.com`
- **Voice**: Google Cloud Neural2 `es-ES-Neural2-B` (primary) → `es-ES-AlvaroNeural` edge-tts fallback
- **Subtitles**: karaoke style — Pipeline C derives timing from the **narration script text** directly (not Whisper re-transcription)

---

## Pipeline A — Clip from existing YouTube video

```bash
cd /home/developer/proyectos/tlc/yt-clipper && export PATH="$HOME/.local/bin:$PATH"

python skills/yt-clipper/scripts/clip.py \
  --url "YOUTUBE_URL" \
  --max-clips 5 \
  --mode shorts \
  --channel-context "TheLearningCurveAI, Daniel García, Python, LLMs, live coding" \
  --auto-upload \
  --privacy unlisted

# Schedule after upload:
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --dry-run
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json
```

**Flags:** `--url` (required), `--max-clips` (5), `--mode` (shorts|standard), `--auto-upload`, `--privacy`, `--caption-style` (use `none` when source captions already burned in), `--caption-replace OLD=NEW`

**QA before upload:** inspect frames at beginning/middle/end; confirm one subtitle layer; confirm lips and captions agree with audio.

---

## Pipeline B — Faceless branded Shorts

Trending AI topic → visual plan → Claude Code slides → TTS → upload.

```bash
python skills/yt-clipper/scripts/faceless.py                                      # LLM picks topic
python skills/yt-clipper/scripts/faceless.py --topic "Prompt Caching en OpenAI"  # custom topic
python skills/yt-clipper/scripts/faceless.py --dry-run                            # script preview
python skills/yt-clipper/scripts/faceless.py --upload --privacy unlisted
```

Steps: `trend_finder` → `script_writer` → `visual_planner` → `slide_reviewer` → `slide_agent` (Claude Code HTML→PNG) → `cta_slide` → `tts` → `faceless_composer`

**Card types**: `comparison` (two logos), `stat` (full-width data), `logo_single` (centered brand)

---

## Pipeline C — Animated AI explainer

Animated diagrams recorded by Playwright. KodeKloud/ByteByteGo aesthetic. Warm white bg, orange accent — NOT dark mode.

```bash
cd /home/developer/proyectos/tlc/yt-clipper && export PATH="$HOME/.local/bin:$PATH"

# Default HTML style (ByteByteGo / KodeKloud):
python skills/yt-clipper/scripts/interview.py --topic "¿Qué es RAG en LLMs?"

# 3Blue1Brown math/CS style (requires: pip install manim):
python skills/yt-clipper/scripts/interview.py --topic "Cómo funciona la atención en Transformers" --style manim

# React whiteboard / Rough.js hand-drawn (requires: Node.js):
python skills/yt-clipper/scripts/interview.py --topic "Arquitectura de agentes IA" --style remotion

# Other flags:
python skills/yt-clipper/scripts/interview.py --topic "..." --upload --privacy unlisted
python skills/yt-clipper/scripts/interview.py --dry-run   # script only, no render
```

### Pipeline C steps

1. `src/interview_writer.py` — LLM writes 5-section narration + timing (INTRO/PROBLEMA/CÓMO FUNCIONA/RESULTADO/CTA), scores with viral-video-writing, retries 3×
2. `src/tts.py` — GCP Neural2 TTS → MP3 (falls back to edge-tts if GCP returns 400/403)
3. Renderer writes animation file, Claude Code generates content via **stdin+Popen** (see critical note below)
4. Playwright records WebM / manim renders MP4 / remotion renders MP4
5. FFmpeg: trim at `cta_start_s` → concat fixed CTA clip
6. Subtitles burned from **narration text** (exact words, proportional timing — no Whisper)

### Diagram styles

| `--style` | Renderer | Aesthetic | Requires |
|-----------|----------|-----------|----------|
| `html` (default) | Claude Code → HTML/SVG → Playwright | ByteByteGo / KodeKloud | Playwright (installed) |
| `manim` | Claude Code → Manim Python → `manim -qh` | 3Blue1Brown math | `pip install manim` ✅ |
| `remotion` | Claude Code → React/TSX → `npx remotion render` | Whiteboard / Rough.js | Node.js ✅ |

**Manim rules Claude must follow:**
- Single file, single `ExplainerScene` class; canvas `9×16` portrait
- Opacity discipline: `FadeOut` before each new section
- Monospace font for code/labels (prevents Pango kerning bugs)
- Pure Manim primitives; no external images
- Run as: `manim -qh --media_dir media scene.py ExplainerScene` (cwd = work_dir; use relative paths)

**Remotion rules Claude must follow:**
- Export `default ExplainerComp` + `compositionConfig` object
- Register with `<Composition component={Comp} {...compositionConfig} />` in `index.tsx` (NOT spread props, NOT index.ts)
- `useCurrentFrame()` + `interpolate()` for all motion (no CSS transitions)
- Spring physics for entrances: `spring({ fps, frame, config: { damping: 12 } })`
- Each section = `<Sequence from={...} durationInFrames={...}>` block

### ⚠️ Critical: Claude CLI invocation in renderers

**Always use stdin + Popen**, never `subprocess.run([..., prompt])`:

```python
# ✅ CORRECT — matches animation_renderer.py pattern
brief_file.write_text(prompt)
with open(brief_file) as stdin_f:
    proc = subprocess.Popen(
        [claude, "--print", "--dangerously-skip-permissions", "--allowedTools", "Write"],
        stdin=stdin_f, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    threading.Thread(target=lambda: [_ for _ in proc.stdout], daemon=True).start()
    # poll for output file...

# ❌ WRONG — deadlocks on large output, prompt not recognized
subprocess.run([claude, "--print", "--allowedTools", "Write", prompt])
subprocess.run([claude, "--print", "--allowedTools=Write", prompt])
```

### Subtitle pipeline (Pipeline C)

Subtitles come from the **narration script text** — not from Whisper re-transcription:

```
narration text + audio_duration → tts.text_to_word_events() → karaoke subtitles
```

Priority in `compose()`: `narration` (always pass it) > `word_events` > Whisper (last resort).

`interview_gen.py` already passes `narration` to all renderers. If adding a new renderer, always include `narration=narration` in the `compose()` call.

### Topics for this channel (AI/LLMs niche, in Spanish)

RAG, embeddings, fine-tuning, ventana de contexto, tokens, MCP, agentes IA,
transformers/atención, prompt caching, vector databases, LangChain, quantización, LoRA,
Claude Suite, agentes autónomos, subagentes, servicios IA a precio fijo

---

## Pipeline D — Reel from talking-head clip

Raw vertical MP4 → 9:16 reel: face in bottom half, animated green cards in top half, karaoke one-word subtitles, background music. Style: Ambra/green-glass.

```bash
python skills/famous-reel-editor/scripts/reel.py --clip path/to/raw.mp4 [--name myname] [--transcriber groq|local|elevenlabs]
```

**Flags:** `--clip` (required), `--name` (default: clip stem), `--transcriber` (default: elevenlabs), `--step N` (resume), `--upload`, `--privacy`

Steps: transcribe → build EDL (review!) → silence-trim → cut+join → animated cards → karaoke captions → compose → upload

**Output:** `temp/reels/<name>/<name>-FINAL.mp4`

---

## Upload + Schedule (Pipelines B & C)

Pipelines B and C do NOT auto-upload. After generating:

```bash
cd /home/developer/proyectos/tlc/yt-clipper && export PATH="$HOME/.local/bin:$PATH"

# 1. Upload MP4s (titles from --titles or inferred from filename)
python skills/youtube-manager/scripts/upload.py temp/interview_*.mp4
python skills/youtube-manager/scripts/upload.py temp/interview_*.mp4 \
  --titles "Título 1" "Título 2" \
  --privacy private

# 2a. Preferred-slot algorithm (Tue/Thu/Fri/Sun 14:00, 2-day gap — best for algo)
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --dry-run
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json

# 2b. Blitz mode — every N hours from now
python skills/youtube-manager/scripts/schedule.py --from-file temp/uploaded.json --interval-hours 2
```

**Pipeline A** has `--auto-upload` built in; `upload_videos.py` is not needed for it.

---

## TTS — Google Cloud Neural2

**Primary**: `es-ES-Neural2-B` (Neural2, male, Spain). OAuth2 Desktop flow.
**Token**: `config/tts_token.json`. **Project**: `gen-lang-client-0480118193`. **API**: `v1beta1`.
**Fallback**: `es-ES-AlvaroNeural` via edge-tts (auto, no config needed).

> **GCP TTS HTTP 400**: Delete `config/tts_token.json` and rerun — it re-auths automatically.
> GCP returning 400 on all runs means the token is expired. edge-tts fallback works fine in the meantime.

Word timestamps: SSML `<mark name="wN"/>` → `enableTimePointing: ["SSML_MARK"]` → exact per-word timing.
Pipeline C does NOT need TTS timestamps for subtitles — it uses `text_to_word_events(narration, duration)` instead.

---

## Brand config — `config/faceless_brand.json`

```json
{
  "channel_handle": "@TheLearningCurveAI",
  "channel_niche":  "IA · LLMs · Agentes",
  "accent_color":   "#FF6719",
  "bg_color":       "#FAFAF9",
  "grid_color":     "#E8E4DC",
  "text_color":     "#1C1B1F",
  "tts_voice":      "es-ES-Neural2-B",
  "tts_rate":       "+0%",
  "default_privacy":"unlisted",
  "logo_path":      "assets/logos/tlc_logo.png"
}
```

---

## Fixed CTA — `src/cta_slide.py`

Always identical, rendered once and cached. Orange bg, TLC logo, tagline, Substack screenshot, "Suscríbete gratis →", `iamdgarcia.substack.com`.

To update: replace `assets/substack_screenshot.png` → delete `temp/*/cta*.png`.

---

## Cinematic scenes (roadmap)

Pipeline C generates animated diagram explainers. The original reference videos also use cinematic B-roll (product shots, ambient lighting). Roadmap: after `render_animation()`, call **Higgsfield MCP** to generate 1-2 cinematic clips intercut with diagram sections — same as Pipeline D already does via `famous-reel-editor`.

> **Status**: planned. Pipeline D already supports Higgsfield B-roll.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Pipeline A: `403 Forbidden` | Firefox must be open and logged into YouTube |
| Pipeline A: `Clip contains XX% silence` | Expected — silence filter working, other clips continue |
| Pipeline B/C: Claude HTML/scene timeout | Retry — second attempt almost always succeeds (Claude Code is intermittent) |
| Pipeline C: `GCP TTS 400/403` | `rm config/tts_token.json` → rerun to re-auth; edge-tts works as fallback |
| Pipeline C: animation blank | Claude wrote file but Playwright didn't render — check file size, retry |
| Pipeline C `--style manim`: `ExplainerScene.mp4` not found | Check `work_dir.resolve()/media` — relative path double-nesting bug; use `scene_path.name` and `--media_dir media` |
| Pipeline C `--style remotion`: esbuild JSX error | Ensure entry point is `index.tsx` not `index.ts`; ensure `tsconfig.json` exists in scaffold |
| Pipeline C `--style remotion`: composition not found | Use `<Composition component={Comp} {...compositionConfig} />` pattern in registerRoot |
| Parallel runs clobbering temp files | Each run uses `timestamp_PID` prefix — PIDs prevent collision |
| YouTube quota exceeded | ~6 uploads/day limit. Retry next day |
| Schedule: `insufficientPermissions` | `rm config/token.json` → rerun for full-scope reauth |

---

## Key files

| File | Purpose |
|------|---------|
| `main.py` | Pipeline A entry point |
| `faceless_gen.py` | Pipeline B entry point |
| `interview_gen.py` | Pipeline C entry point (`--style html|manim|remotion`) |
| `reel_gen.py` | Pipeline D entry point |
| `upload_videos.py` | Generic uploader — any MP4 list → `temp/uploaded.json` |
| `schedule_clips.py` | Schedule uploaded videos (preferred slots or `--interval-hours N`) |
| `config/faceless_brand.json` | Brand identity (colors, voice, handle) |
| `config/client_secrets.json` | OAuth2 Desktop credentials (YouTube + GCP TTS) |
| `config/token.json` | YouTube OAuth token |
| `config/tts_token.json` | GCP TTS OAuth token (delete to re-auth) |
| `src/tts.py` | TTS: GCP Neural2 primary, edge-tts fallback, `text_to_word_events()` |
| `src/animation_renderer.py` | Style `html`: Claude Code → HTML → Playwright → FFmpeg |
| `src/manim_renderer.py` | Style `manim`: Claude Code → Manim Python → `manim -qh` → FFmpeg |
| `src/remotion_renderer.py` | Style `remotion`: Claude Code → React/TSX → `npx remotion render` → FFmpeg |
| `src/interview_writer.py` | Script writer: 5-section narration, viral score, 3 retries |
| `src/faceless_composer.py` | Pipeline B assembly: sections → bg → audio → subtitles |
| `src/cta_slide.py` | Fixed CTA slide (HTML → PNG/MP4, cached) |
| `src/brand_assets.py` | Logo injection for Playwright pages |
| `src/visual_planner.py` | LLM visual plan (card types, logos per slide) |
| `src/slide_reviewer.py` | Batch slide review + pixel sanity check |
| `src/logo_agent.py` | Brand logo resolver (simple-icons SVG → PNG) |
| `src/brand_config.py` | `load()` → BrandConfig — always call at start of `write()` functions |
| `assets/logos/tlc_logo.png` | TLC wordmark (transparent bg) |
| `assets/substack_screenshot.png` | Substack page screenshot for CTA |
| `skills/viral-video-writing/` | Hook rules + score.py (used by B+C writers) |
| `skills/famous-reel-editor/` | Reel scripts + style reference (Pipeline D) |
