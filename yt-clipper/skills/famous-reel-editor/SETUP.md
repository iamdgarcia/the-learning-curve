# SETUP — install everything from zero

You only do this once. Target: macOS (notes for Linux at the bottom). ~10 minutes.

The easiest way: paste this whole file to Claude Code and say *"set this up for me, ask
before installing anything"* — it'll run the steps and check what's already there. Or do
it by hand below.

---

## 1. Homebrew (macOS package manager)

If you don't have it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Check: `brew --version`.

## 2. System tools: ffmpeg, node, python, yt-dlp

```bash
brew install ffmpeg node python yt-dlp
```
- **ffmpeg / ffprobe** — the whole video pipeline. Required.
- **node** — provides `npx`, used to render the motion-graphics cards (`npx hyperframes render`). Required. (npx downloads `hyperframes` itself on first run.)
- **python** (3.10+) — runs all the scripts. Required.
- **yt-dlp** — only to download a *reference* reel (IG/TikTok link) you want to copy the style from. Optional.

Check:
```bash
ffmpeg -version | head -1
node -v
python3 --version
```

## 3. Python packages

```bash
python3 -m pip install --upgrade pillow requests
```
- **pillow** (PIL) — bakes the subtitles. Required.
- **requests** — used by the ElevenLabs transcription. Required if you use `transcribe.py`.

If you'll use the **free local transcription** instead of the API (see step 5):
```bash
python3 -m pip install faster-whisper
```

## 4. The font

Already bundled at `assets/fonts/Montserrat-VariableFont_wght.ttf` and `captions.py`
finds it automatically. Nothing to do. (If you ever move it, set `CAPTION_FONT=/path/to/Montserrat.ttf`.)

## 5. Transcription — pick ONE

The pipeline needs word-level timestamps. Three options, same output, same script args:

### Option A — ElevenLabs Scribe (best timing, paid, recommended for reels)
1. Get an API key at https://elevenlabs.io (Settings → API keys).
2. Either export it once:
   ```bash
   echo 'export ELEVENLABS_API_KEY=sk_your_key_here' >> ~/.zshrc
   source ~/.zshrc
   ```
   or put the line `ELEVENLABS_API_KEY=sk_your_key_here` in a `.env` file inside this skill folder.
   `scripts/transcribe.py` picks it up automatically.

### Option B — Groq API (whisper-large-v3, near-free, very fast)
1. Get an API key at https://console.groq.com.
2. Export it once:
   ```bash
   echo 'export GROQ_API_KEY=gsk_your_key_here' >> ~/.zshrc
   source ~/.zshrc
   ```
   Claude uses `scripts/transcribe_groq.py` (same CLI). Whisper-quality words in seconds,
   no model download. Word boundaries slightly looser than Scribe — occasional extra
   caption-sync fix. Fallback only; Scribe (Option A) is the default everywhere.

### Option C — Local Whisper (free, offline, no key)
1. `python3 -m pip install faster-whisper` (from step 3).
2. That's it. Claude uses `scripts/transcribe_local.py` (same CLI). First run downloads
   the model (~1.5 GB for `large-v3`, cached afterward). Same quality and timing as
   Groq (same model), just slower and fully offline.

> Tell Claude which one you picked, e.g. *"use groq for transcription"* — otherwise reels
> default to `transcribe.py` (ElevenLabs) and YouTube edits default to `transcribe_groq.py`.

## 6. Optional: music download (only if you'll pull tracks from YouTube)
```bash
brew install deno          # yt-dlp needs it for some YouTube URLs (else 403)
```
Not needed for the bundled track or for downloading IG reference reels.

## 7. Install the skill into Claude Code

Move the whole folder so it lives here:
```bash
mv famous-reel-editor ~/.claude/skills/famous-reel-editor
```
Open Claude Code (in any folder) and it auto-discovers the skill. Test:
> *"do you have the famous-reel-editor skill?"*

---

## One-shot check

```bash
echo "ffmpeg:  $(command -v ffmpeg)"
echo "ffprobe: $(command -v ffprobe)"
echo "node:    $(node -v 2>/dev/null)"
echo "python:  $(python3 --version 2>/dev/null)"
python3 -c "import PIL, requests; print('python deps: ok')"
echo "skill:   $([ -f ~/.claude/skills/famous-reel-editor/SKILL.md ] && echo installed || echo MISSING)"
echo "11labs key: ${ELEVENLABS_API_KEY:+set}${ELEVENLABS_API_KEY:-(unset)}"
echo "groq key:   ${GROQ_API_KEY:+set}${GROQ_API_KEY:-(unset)}"
echo "(no keys set? -> local transcription: pip install faster-whisper)"
```

## Linux notes
- Use your package manager instead of brew: `sudo apt install ffmpeg nodejs npm python3 python3-pip` (Debian/Ubuntu); `yt-dlp` via pip if not packaged.
- The bundled font works as-is. If you prefer a system install, drop the `.ttf` in `~/.fonts/` and run `fc-cache -f`.
- Everything else (the scripts, the skill) is identical.

## Troubleshooting
- **`npx hyperframes` is slow the first time** — it's downloading the renderer. Normal; cached after.
- **Subtitles look wrong / font error** — set `CAPTION_FONT` to a full path to a Montserrat `.ttf`.
- **`ELEVENLABS_API_KEY not found`** — either export it (Option A) or switch to local transcription (Option B).
- **Video won't open after export** — it should already have `+faststart`; if you remux by hand add `-movflags +faststart`.
