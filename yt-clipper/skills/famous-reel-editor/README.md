# famous-reel-editor — a Claude Code skill

Turn ONE raw talking-head clip (vertical, or landscape 4K) into a finished, styled
**9:16 reel**: you in the bottom half, animated motion-graphics in the top half,
karaoke one-word subtitles, music, and by default **1–2 AI-generated B-roll cutaways**
(via the Higgsfield MCP — say "no B-roll" to skip, or hand it your own clips instead). The default look is a green "glass" style; the
accent color is themeable (e.g. orange) to match any reference reel.

This is a **skill for [Claude Code](https://claude.com/claude-code)**. You don't run the
scripts by hand — you drop the folder into Claude Code, point it at a video, and Claude
follows `SKILL.md` to do the edit, iterating with you.

---

## What's inside

```
famous-reel-editor/
├── SKILL.md                 ← the playbook Claude follows (read this to understand it)
├── README.md                ← you are here
├── SETUP.md                 ← install everything from zero (do this first)
├── INSTALL-PROMPT.md        ← a prompt to paste into Claude Code to get going
├── scripts/
│   ├── transcribe.py        ← transcription (ElevenLabs Scribe, word-level timing)
│   ├── transcribe_local.py  ← free local alternative (faster-whisper, no API key)
│   ├── cutjoin.py           ← cut + join segments (sample-accurate, no OOM)
│   ├── silence_keep.py      ← trim residual silences without clipping words
│   ├── make_edl.py          ← build an EDL from a transcript (single-take clips)
│   ├── gen.py               ← the card generator template (HTML/GSAP motion graphics)
│   ├── captions.py          ← bake karaoke subtitles as transparent PNGs (PIL)
│   └── compose.sh           ← final composite: face + cards + subs + music
├── references/
│   ├── style.md             ← the visual style + schema catalog
│   ├── animation-library.md ← a big catalog of animated schemas to use/vary
│   ├── card-snippets.md     ← copy-paste code for ready-made cards
│   └── examples/            ← two complete working card generators + a B-roll composite
└── assets/
    ├── fonts/               ← Montserrat (bundled, used for subtitles)
    ├── logos/               ← a few SVG logos (claude, github, openai, whatsapp)
    └── bg-music.m4a         ← DEFAULT background track (placeholder — see note below)
```

## Quick start

1. **Install the dependencies** → follow [SETUP.md](SETUP.md). ~10 minutes, mostly Homebrew.
2. **Install the skill**: move this whole `famous-reel-editor/` folder into `~/.claude/skills/`
   so it lives at `~/.claude/skills/famous-reel-editor/`.
   ```bash
   mv famous-reel-editor ~/.claude/skills/famous-reel-editor
   ```
3. **Use it**: open Claude Code in any folder and say something like
   *"make a reel from this video: ~/Desktop/my-clip.mov"*.
   Claude will pick up the skill and walk the pipeline (transcribe → pick clean takes →
   cut → trim silence → author the cards → subtitles → composite → self-check).
   See [INSTALL-PROMPT.md](INSTALL-PROMPT.md) for a ready-made first prompt.

## Two things to know

- **Transcription needs ONE of two things.** Either an **ElevenLabs API key** (best word
  timing — `scripts/transcribe.py`) or the **free local** path (`scripts/transcribe_local.py`,
  needs `pip install faster-whisper`, no key, runs offline). Pick one in SETUP.md.
- **The music is a placeholder.** `assets/bg-music.m4a` is just a default so things work
  out of the box. For anything you publish, **swap in your own licensed track**:
  ```bash
  MUSIC=/path/to/your-track.m4a   # compose.sh reads this env var
  ```

## Credits

Built and battle-tested by Riccardo (Martes AI). The `SKILL.md` "ERRORS NOT TO REPEAT"
table is the real value: every row is a bug that cost a re-render, already solved.
