---
name: viral-video-writing
description: Train Claude to write scripts for Instagram Reels, TikTok, YouTube Shorts and YouTube that people watch to the end. Hook rules (clarity + curiosity, the 4 hook killers, contrast), story arcs (the villain, rock bottom, the turn, the callback payoff), re-hooks every few seconds, anti-AI writing rules, engagement checks, the tools to use, and a checker that scores every draft. Claude drafts, scores and rewrites until the script passes. Use when someone asks for a script, a hook, a story, "write me a reel about X", "make this script better", "why did this video flop", or "break down this viral video".
argument-hint: [topic, story, link, or your own hook]
---

# Viral video writing

Viral videos are written, not lucky. Every one that works has a hook that stops the scroll,
a story or a promise that keeps people watching, and a new reason to stay every few seconds.
This skill writes that script, checks it, and rewrites it until it passes.

Files next to this one (read the ones the job needs):
- `hook-craft.md`: the hook rules. Clarity + curiosity, the 4 hook killers, the 2-3 line formula, contrast, the first frame, the hook checklist.
- `story.md`: the story arc. The 7 story beats with a real 103K-view example, story shapes, and how to put a story inside a tutorial.
- `retention.md`: re-hooks, pace, open loops, the middle sag, and the ending.
- `writing.md`: how to write lines people say out loud, the anti-AI writing rules, and the CTA.
- `checks.md`: every engagement check in one place: idea, hook, story, retention, AI writing, the 3 viewer tests, and how to read the numbers after posting.
- `tools.md`: the tools to use for ideas, writing, filming, editing, sound and tracking, free ones first.
- `scripts/score.py`: the checker. `python3 scripts/score.py draft.txt` gives a score out of 100 and every failed check.

## The parts of every video that works

| # | Part | Time | Job |
|---|------|------|-----|
| 1 | **Hook** | 0-3 s | Stop the scroll. Clear topic + a gap the viewer needs closed. A specific number or a named thing helps. |
| 2 | **Stakes** | 3-8 s | Why this matters to THEM, or who is against the hero. |
| 3 | **Promise** | inside 1 or 2 | What they get by the end, so they wait for it. |
| 4 | **Beats** | the middle | One idea or one scene per beat. Each one lands one concrete detail. |
| 5 | **Re-hooks** | every 5-8 s | A new question, a number, a twist or a time jump before attention drops. |
| 6 | **Proof** | near the end | A real number, a real result, real footage. |
| 7 | **Payoff + CTA** | last 3-5 s | Close the loop from the hook, then one clear ask. End on the last word. |

If a video flopped, check these in order. It is almost always the hook, a slow first 3 seconds, or a middle with no re-hook.

## The loop (do every step, every time)

1. **Facts sheet.** List every fact the script will use and where it came from (a link, the user's own words). If a line needs a fact you don't have, cut it or ask. Never invent results, numbers, quotes or struggles.
2. **Pick the shape.**
   - A personal story or a case study: the 7 story beats in `story.md`.
   - A lesson or a how-to: the 3-beat story wrapper in `story.md` (problem as a moment, the fix as steps, the after as proof).
3. **Hook shortlist (5).** Judge every one with the checklist in `hook-craft.md`. If the user gave a hook, it is #1 and you keep their words. Rank by clarity, curiosity, and whether it's true.
4. **Write 3 drafts,** each with a different hook and angle. Shorts: 30-60 seconds (about 4 spoken words a second). Stories can run longer if every beat raises the stakes. One idea per sentence.
5. **Check each draft** with every section of `checks.md`.
   - `python3 scripts/score.py <file>`
   - Stopwatch check from `retention.md`: a re-hook at least every 8 seconds?
   - For a story: a doubter early, a lowest point, a callback at the end?
   - `writing.md`: would a real person say every line out loud? Any metaphor, flourish or AI word?
   - Is every number on the facts sheet? Is the hook the strongest line?
6. **Rewrite and re-score.** Take the best draft, fix every failed check and the weakest beat, score it again. Repeat until 90+ with zero hard fails (max 5 passes). Keep a short log of what changed and why.
7. **Deliver:**
   - The final script, one spoken line per line, with the time of each beat.
   - 2 alternate hooks.
   - A caption: the hook line, then the CTA, then 3-5 hashtags.
   - The facts sheet with links.
   - If they asked how to film or edit it, point them to `tools.md`.

## Long-form YouTube
Same rules, bigger. Say what the title promised in the first 10 seconds, show the result first, and give every
chapter (every 1-3 minutes) its own hook, payoff and re-hook into the next one.

## Breaking down someone else's viral video
When the user sends a video or a transcript and asks why it worked:
1. Write the transcript with timestamps (or ask for it).
2. Label every line with its part from the table above.
3. Write the hook's shape as a template with blanks.
4. Find the re-hooks and measure the gaps between them.
5. For a story, mark the 7 beats from `story.md`.
6. Say what to steal (the shape, the beat order, the pacing) and what not to (the words, the topic, their claims).
7. Offer to write the user's version with the loop above.

## Rules
- **Real numbers only.** Every number says where it comes from.
- **The user's own hook wins.** If they hand you one, build the script under it.
- **No AI writing.** Read `writing.md` before every draft.
- **One CTA.** One keyword, one word.
- **Show, don't claim.** If the script says "I found" or "I tested", there must be real proof on screen.
