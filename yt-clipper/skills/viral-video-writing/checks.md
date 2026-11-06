# Checks: is it engaging before you post it?

Every check in one place. Claude runs these on every draft, and you can run them yourself on any script or finished video.
A script isn't done until it passes all five.

## 1. The idea check (before writing)
- [ ] Has this idea, or this shape of video, already worked for the same audience?
- [ ] Does it give the viewer value or entertainment? If neither, stop here.
- [ ] Is it aimed at a real want: money, health, love, status or time?
- [ ] Is the promise believable? "$20 a night" beats "$7K a week".

## 2. The hook check (first 3 seconds)
- [ ] The topic is clear in under 2 seconds.
- [ ] A specific number, name or result is in the first sentence.
- [ ] There's a contrast or an open question the viewer needs closed.
- [ ] It's aimed at one viewer and their problem.
- [ ] It's true, and the video delivers it.
- [ ] The first frame moves and makes sense on mute.
- [ ] It's the strongest line in the script.

Write 5 hooks. Pick the one that passes the most checks, not the one you like best. (More in `hook-craft.md`.)

## 3. The story check
- [ ] The first line is a decision, a conflict or a result, never backstory.
- [ ] There's someone or something to root against in the first 10 seconds.
- [ ] There's a clear lowest point.
- [ ] The ending calls back to the opening: the same people or place, the opposite result.
- [ ] Every fact, struggle and quote really happened.

## 4. The retention check (read it with a stopwatch)
- [ ] The first re-hook comes before 8 seconds.
- [ ] No gap over 8 seconds without a new number, twist, reveal or time jump.
- [ ] Something new is on screen every 2-3 seconds. Write down what.
- [ ] The best part is in the middle, where people usually leave.
- [ ] It ends on the last word. No outro.

## 5. The AI-writing check
- [ ] `python3 scripts/score.py draft.txt` scores 90+ with zero hard fails.
- [ ] Read it out loud. Every line sounds like talking, not reading.
- [ ] No line from the AI tells list in `writing.md` (metaphor punchlines, "it's not X, it's Y", stage directions, banned words).
- [ ] Every technical word is explained the first time, in 10 words or fewer.

## The 3 viewer tests (on the finished video)
1. **Mute test:** watch it on a phone with the sound off. Does it still make sense?
2. **Eyes-closed test:** listen without watching. Does the audio alone keep you?
3. **Stranger test:** show someone the first 3 seconds and ask what the video is about. If they can't say, the hook isn't clear.

## After posting (read the numbers at 3 days)
| Result | What it means | What to do |
|---|---|---|
| 50K+ views | The format works | Make 3 variations now |
| 10K-50K | It's working | Keep it in rotation |
| 1K-10K | Maybe | One more try with a new hook |
| Under 1K twice | It doesn't work | Drop it |

Then open the retention graph. The spot where it drops is the line to fix next time.
