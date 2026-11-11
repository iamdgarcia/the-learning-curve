# AGENTS.md — yt-clipper

> Read this first. Every task has a skill. Load the skill, then act.

## Task → Skill mapping

| What the user wants | Skill to load |
|---------------------|---------------|
| Clip a YouTube video into Shorts | `skills/yt-clipper/SKILL.md` |
| Generate a faceless AI Short (slides + voice) | `skills/yt-clipper/SKILL.md` |
| Generate an animated explainer Short | `skills/yt-clipper/SKILL.md` |
| Edit a raw talking-head clip into a reel | `skills/famous-reel-editor/SKILL.md` |
| Upload videos to YouTube | `skills/youtube-manager/SKILL.md` |
| Schedule uploads | `skills/youtube-manager/SKILL.md` |
| Write or score a viral script | `skills/viral-video-writing/SKILL.md` |
| View channel analytics | `skills/youtube-manager/SKILL.md` |

## Setup (first time only)

```bash
python setup_check.py   # diagnoses missing deps and config
```

Tells you exactly what's missing and how to fix it. Repeat until all green.

## Repository layout

```
yt-clipper/
├── AGENTS.md                      ← you are here
├── setup_check.py                 ← health check and onboarding
├── src/                           ← shared Python library (brand_config, tts, renderers…)
├── config/                        ← copy *.example.json → *.json, fill in your details
├── assets/                        ← fonts and logos
└── skills/
    ├── yt-clipper/                ← Pipelines A (clip), B (faceless), C (interview/animated)
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── clip.py            ← Pipeline A
    │       ├── faceless.py        ← Pipeline B
    │       └── interview.py       ← Pipeline C  (--style html|manim|remotion)
    ├── youtube-manager/           ← upload, schedule, analytics
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── upload.py          ← upload any MP4 list → temp/uploaded.json
    │       └── schedule.py        ← schedule by preferred slots or --interval-hours N
    ├── famous-reel-editor/        ← Pipeline D: raw clip → styled reel
    │   ├── SKILL.md
    │   └── scripts/
    │       └── reel.py
    └── viral-video-writing/       ← script scoring and hook rules
        ├── SKILL.md
        └── scripts/
            └── score.py
```

## Rules for agents

- **Always load the skill** before writing any code or running any command.
- **Never create a new script** for something a skill already covers. Upload → `youtube-manager`. Animate → `yt-clipper`. Edit → `famous-reel-editor`.
- **All scripts live in `skills/*/scripts/`** — don't create new `.py` files at the root.
- Shared library code goes in `src/` and is imported by all skill scripts.
- Config is in `config/faceless_brand.json` (never committed — copy from `.example.json`).
- Run all commands from the `yt-clipper/` root: `python skills/yt-clipper/scripts/interview.py --topic "..."`
