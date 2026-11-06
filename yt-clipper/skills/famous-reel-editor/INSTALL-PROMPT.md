# Paste-into-Claude-Code prompts

## First time — setup
Open Claude Code in the folder where you unzipped this, and paste:

> I have the `famous-reel-editor` skill folder here. Read `famous-reel-editor/SETUP.md` and set me up:
> check what's already installed, and ask me before installing anything. I'll be
> transcribing with **[ElevenLabs / local Whisper — pick one]**. When done, move the
> folder to `~/.claude/skills/famous-reel-editor` and confirm the skill is discoverable.

## Making a reel
Open Claude Code anywhere, and paste (edit the path + describe the look you want):

> Make a vertical reel from this clip: `~/Desktop/my-clip.mov`
> Use the **famous-reel-editor** skill. Default green style is fine.
> It's a single talking-head in English. Keep it punchy.

Variations you can add:
- **Match a reference reel:** *"make it look like this reel: <Instagram/TikTok link> — copy the style and the accent color, not the text."*
- **Theme the color:** *"use an orange accent (Claude style)."*
- **Landscape 4K source:** *"the source is landscape 4K, crop it to vertical centered on my face first."*
- **Show B-roll over your face:** *"while I talk about the website around 0:10, overlay this screen-recording: <path>."*
- **Your own music:** *"use this track instead of the default: <path to .m4a/.mp3>."*

## What Claude will do (so you know what to expect)
1. Transcribe the raw clip (word-level timing).
2. Read it and **pick the clean takes** (raws are often multi-take with spoken notes — it drops those).
3. Cut + trim silences, then **re-transcribe the cut** for exact sync.
4. Author the animated cards (one per beat, anchored to the words you say).
5. Bake the karaoke subtitles and composite face + cards + subs + music.
6. Self-check frames against the reference style and show you the result, then iterate on your feedback.

It iterates with you — expect a round or two of "tighten this pause / fix this word /
change this card" before it's final. The skill learns from that feedback over time.
