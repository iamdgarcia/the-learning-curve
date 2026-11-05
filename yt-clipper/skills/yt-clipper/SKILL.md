---
name: yt-clipper
description: >
  Three pipelines for short-form video content at TheLearningCurveAI (@TheLearningCurveAI).

  Pipeline A — yt-clipper: clip existing YouTube videos into viral Shorts.
  Takes a URL, two-agent LLM finds best moments, downloads segments, converts
  to 1080x1920 vertical (face + zoomed screen), burns karaoke subtitles, uploads.
  Use when: "clip this video", "extract shorts from", "make clips from [URL]".

  Pipeline B — faceless: original branded Shorts from trending AI topics.
  LLM picks topic → script → visual plan → slide_agent (Claude Code writes HTML
  → Playwright renders PNGs) → TTS → karaoke subtitles → upload.
  Use when: "generate a faceless short", "create content on [topic]", "faceless video".

  Pipeline C — interview: animated CS/AI explainer Shorts, like KodeKloud/ByteByteGo.
  LLM picks AI concept → script → Claude Code writes animated HTML (JS timeline,
  SVG diagrams) → Playwright records video → GCP Neural2 TTS → karaoke subtitles
  → fixed CTA slide → upload.
  Use when: "make an animated explainer", "interview question video", "explain [AI concept]",
  "dynamic video like KodeKloud".

  All content in Spanish. Substack palette (#FF6719 orange, #FAFAF9 warm white).
  Always Spanish, always @TheLearningCurveAI brand.

license: MIT
compatibility: >
  Python 3.10+, ffmpeg, yt-dlp at ~/.local/bin/yt-dlp, Firefox (yt-dlp cookies),
  edge-tts, google-cloud-texttospeech, google-auth-oauthlib, playwright, claude CLI.
  Run from /home/developer/proyectos/tlc/yt-clipper. PATH="$HOME/.local/bin:$PATH".
metadata:
  author: TheLearningCurveAI (Daniel García — iamdgarcia)
  version: 3.0.0
  project-path: /home/developer/proyectos/tlc/yt-clipper
---

# yt-clipper — Content pipelines for @TheLearningCurveAI

Three pipelines, one brand. All videos share:
- **Palette**: Substack orange `#FF6719`, warm white `#FAFAF9`, grid `#E8E4DC`
- **Logo**: `assets/logos/tlc_logo.png` injected bottom-right via Playwright on every frame
- **CTA**: fixed slide — `src/cta_slide.py` — same in every video:
  orange bg, TLC logo, tagline, Substack screenshot, "Suscríbete gratis →", `iamdgarcia.substack.com`
- **Voice**: Google Cloud Neural2 `es-ES-Neural2-B` (primary) → edge-tts fallback
- **Subtitles**: karaoke style, word timestamps from TTS engine (no Whisper for TTS audio)

---

## Pipeline A — Clip from existing YouTube video

```bash
cd /home/developer/proyectos/tlc/yt-clipper && export PATH="$HOME/.local/bin:$PATH"

python main.py \
  --url "YOUTUBE_URL" \
  --max-clips 5 \
  --mode shorts \
  --channel-context "TheLearningCurveAI, Daniel García, Python, LLMs, live coding" \
  --auto-upload \
  --privacy unlisted
```

**Schedule after upload:**
```bash
python schedule_clips.py --from-file temp/uploaded.json --dry-run
python schedule_clips.py --from-file temp/uploaded.json
```

**Flags:** `--url` (required), `--max-clips` (5), `--mode` (shorts|standard), `--auto-upload`, `--privacy`

---

## Pipeline B — Faceless branded Shorts

Trending AI topic → visual plan → Claude Code slides → TTS → upload.

```bash
python faceless_gen.py                                      # LLM picks topic
python faceless_gen.py --topic "Prompt Caching en OpenAI"  # custom topic
python faceless_gen.py --dry-run                            # script preview
python faceless_gen.py --upload --privacy unlisted
```

**Agents in the pipeline:**
1. `src/trend_finder.py` — LLM picks trending AI topic
2. `src/script_writer.py` — script + 5 sections with visual specs
3. `src/visual_planner.py` — LLM designs tabs, card types, logos per slide
4. `src/slide_reviewer.py` — batch reviews all slides (1-2 LLM calls), fixes issues
5. `src/slide_agent.py` — Claude Code (`--allowedTools Write`) writes HTML → Playwright PNG
6. `src/cta_slide.py` — fixed CTA PNG replaces last slide (always identical)
7. `src/tts.py` — GCP Neural2 TTS with word timestamps
8. `src/faceless_composer.py` — Whisper section timing → FFmpeg concat → burn subtitles

**Card types** (visual_planner decides):
- `comparison` — two branded logo cards side by side
- `stat` — full-width orange card with key data
- `logo_single` — one brand card centered

**Logo agent** (`src/logo_agent.py`): resolves brand name → simple-icons SVG via GitHub → cairosvg → PNG.
Seed map for common AI brands (LangChain, Anthropic, OpenAI, etc.). LLM resolves unknowns.
Cache: `temp/logos/slugs.json` + `temp/logos/*.png`.

---

## Pipeline C — Animated AI explainer (interview style)

Animated HTML + SVG diagrams, recorded by Playwright. KodeKloud/ByteByteGo aesthetic.
Substack palette (warm white bg, orange accent — NOT dark mode).

```bash
python interview_gen.py                                           # LLM picks AI topic
python interview_gen.py --topic "¿Qué es RAG en LLMs?"           # custom topic
python interview_gen.py --topic "..." --upload --privacy unlisted
python interview_gen.py --dry-run                                 # script only
```

**Pipeline steps:**
1. `src/interview_writer.py` — LLM writes 5-section narration + timing (INTRO/PROBLEMA/CÓMO FUNCIONA/RESULTADO/CTA)
2. `src/tts.py` — GCP Neural2 TTS → MP3 + exact word timestamps (SSML marks, v1beta1 API)
3. `src/animation_renderer.py` → `generate_html()`:
   - Writes brief to temp file, runs `claude --print --dangerously-skip-permissions --allowedTools Write`
   - Claude Code writes the animated HTML (SVG diagrams, JS setTimeout timeline, stroke-dashoffset arrows)
   - Polls for file existence (stdout=PIPE + drain thread to avoid deadlock)
   - Timeout: 480s (complex HTML takes 150-450s)
4. Playwright records animation as WebM (real-time, `record_video_dir`)
5. FFmpeg: trim animation at `cta_start_s` → concat fixed CTA clip
6. Karaoke subtitles burned (stop at CTA start — CTA slide stays clean)

**Topics for this channel** (AI/LLMs niche only, in Spanish):
RAG, embeddings, fine-tuning, ventana de contexto, tokens, MCP, agentes IA,
transformers/atención, prompt caching, vector databases, LangChain, quantización, LoRA

**Known intermittent issue**: Claude sometimes fails to write the HTML (exits without writing).
Simple retry: rerun the same command. Second attempt almost always succeeds.

---

## Brand config — `config/faceless_brand.json`

```json
{
  "channel_handle":    "@TheLearningCurveAI",
  "channel_niche":     "IA · LLMs · Agentes",
  "accent_color":      "#FF6719",
  "bg_color":          "#FAFAF9",
  "grid_color":        "#E8E4DC",
  "grid_size":         54,
  "text_color":        "#1C1B1F",
  "card_text_color":   "#FFFFFF",
  "font_bold":         "assets/fonts/InterDisplay-Bold.ttf",
  "font_regular":      "assets/fonts/Inter-Medium.ttf",
  "tts_voice":         "es-ES-Neural2-B",
  "tts_rate":          "+0%",
  "default_privacy":   "unlisted",
  "tiktok_enabled":    false,
  "youtube_channel_url": "https://www.youtube.com/@TheLearningCurveAI",
  "logo_path":         "assets/logos/tlc_logo.png"
}
```

| Field | What it does |
|-------|-------------|
| `channel_handle` | `@TheLearningCurveAI` — top-right watermark |
| `channel_niche` | Top-left label (e.g. "IA · LLMs · Agentes") |
| `accent_color` | Substack orange `#FF6719` |
| `bg_color` / `grid_color` | Warm white / warm gray — NOT dark mode |
| `tts_voice` | `es-ES-Neural2-B` (GCP Neural2 male Spain). Fallback: `es-ES-AlvaroNeural` |
| `tts_rate` | `+0%` — do not speed up, sounds robotic |
| `logo_path` | TLC wordmark PNG injected via Playwright on every frame |

---

## TTS — Google Cloud Neural2

Primary voice: `es-ES-Neural2-B` (Neural2, male, Spain). Much more natural than edge-tts.

**Auth**: OAuth2 Desktop flow using existing `config/client_secrets.json`.
Token saved to `config/tts_token.json` after first authorization.
Project: `gen-lang-client-0480118193`.
API: `v1beta1` (NOT v1 — v1 lacks `enableTimePointing`).

**Word timestamps**: SSML `<mark name="wN"/>` per word → `enableTimePointing: ["SSML_MARK"]`
→ exact timestamps returned in response → no Whisper needed for TTS audio.

**Fallback**: if GCP fails, auto-switches to `es-ES-AlvaroNeural` via edge-tts.

```python
# In src/tts.py
from src.tts import generate_with_timestamps, to_whisper_segments

path, word_events = generate_with_timestamps(text, output_path, voice="es-ES-Neural2-B")
segments = to_whisper_segments(word_events)  # → subtitle_generator compatible
```

---

## Fixed CTA — `src/cta_slide.py`

**Always identical** — not generated by Claude. Rendered once (Playwright), cached.

Content:
- Orange `#FF6719` full background
- "The Learning Curve" logo (white, from `assets/logos/tlc_logo.png`)
- Tagline: "Aprende IA como un ingeniero, no como un gurú de YouTube."
- Rounded card with Substack page screenshot (`assets/substack_screenshot.png`)
- White button: "Suscríbete gratis →"
- URL: `iamdgarcia.substack.com`

**Interview**: animation trimmed at `sections[-1]["start_s"]`, CTA clip appended.
**Faceless**: last slide PNG (`section_04.png`) replaced with CTA PNG.

To update the screenshot: replace `assets/substack_screenshot.png` and delete `temp/*/cta*.png`.

---

## Logo injection — `src/brand_assets.py`

```python
from src.brand_assets import inject_logo
inject_logo(page)  # call after page.goto(), before screenshot/record
```

Injects `assets/logos/tlc_logo.png` as `position:fixed; bottom:28px; right:32px; width:260px`
via `file://` URI. Works for both static PNGs (faceless) and recorded video (interview).

---

## Scheduling

```bash
# After upload (any pipeline):
python schedule_clips.py --from-file temp/uploaded.json --dry-run
python schedule_clips.py --from-file temp/uploaded.json

# Default slots (Spain, Thu/Mon 14:00, 2-day gap):
# Clips sorted by virality score. Videos set to private + publishAt.
```

**Token scope error on schedule**: `rm config/token.json` then rerun.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Pipeline A: `403 Forbidden` | Firefox must be open and logged into YouTube |
| Pipeline A: `Clip contains XX% silence` | Expected — silence filter working, other clips continue |
| Pipeline B/C: Claude HTML timeout | Retry — second attempt almost always succeeds |
| Pipeline C: `GCP TTS 403` | Check `config/tts_token.json` exists, reauth if expired |
| Pipeline C: animation blank | Claude wrote HTML but Playwright didn't render — check HTML file size |
| Both: `YouTube quota exceeded` | ~6 uploads/day limit. Retry next day. |
| Schedule: `insufficientPermissions` | `rm config/token.json` → rerun for full-scope reauth |

---

## Key files

| File | Purpose |
|------|---------|
| `faceless_gen.py` | Pipeline B entry point |
| `interview_gen.py` | Pipeline C entry point |
| `main.py` | Pipeline A entry point |
| `schedule_clips.py` | Schedule uploaded videos |
| `config/faceless_brand.json` | Brand identity (colors, voice, handle) |
| `config/client_secrets.json` | OAuth2 Desktop credentials (YouTube + GCP TTS) |
| `config/token.json` | YouTube OAuth token |
| `config/tts_token.json` | GCP TTS OAuth token |
| `assets/logos/tlc_logo.png` | "The Learning Curve" wordmark (transparent bg) |
| `assets/substack_screenshot.png` | Substack homepage screenshot for CTA |
| `assets/fonts/InterDisplay-Bold.ttf` | Title font |
| `assets/fonts/Inter-Medium.ttf` | UI font |
| `src/tts.py` | TTS: GCP Neural2 primary, edge-tts fallback, word timestamps |
| `src/cta_slide.py` | Fixed CTA slide (HTML → PNG/MP4) |
| `src/brand_assets.py` | Logo injection for Playwright pages |
| `src/animation_renderer.py` | Claude Code → HTML → Playwright record → FFmpeg |
| `src/slide_agent.py` | Claude Code → HTML → Playwright PNG (faceless) |
| `src/visual_planner.py` | LLM visual plan (tabs, card types, logos) |
| `src/slide_reviewer.py` | Batch slide review + pixel sanity check |
| `src/logo_agent.py` | Brand logo resolver (simple-icons + LLM fallback) |
| `src/interview_writer.py` | Animated explainer script writer |
| `src/faceless_composer.py` | Faceless video assembly (sections → bg → audio → subs) |
