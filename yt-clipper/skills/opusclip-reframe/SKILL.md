---
name: opusclip-reframe
description: >
  AI video reframing for short-form content. Converts landscape video to vertical
  (9:16), square (1:1), or keeps landscape (16:9). Automatically detects the speaker's
  face using OpenCV, zooms the screen panel to where the cursor/mouse activity is
  using frame differencing (~1.6× zoom), and splits the frame into face panel (top)
  and zoomed screen panel (bottom) for coding/teaching streams.
  Use when the user says: "reframe the video", "convert to vertical", "make it square",
  "9:16 format", "1:1 aspect ratio", "Instagram square", "face tracking", "zoom to
  the code", "split screen face and code", "vertical format for Shorts", "landscape
  keep it horizontal", "change the aspect ratio", "crop to the speaker".
  Do NOT use for: clip extraction or caption styling — those are separate sub-skills.
license: MIT
compatibility: >
  Python 3.10+, ffmpeg, OpenCV (opencv-python-headless). Run from __PROJECT_PATH__.
metadata:
  version: "2.0.0"
  author: TheLearningCurveAI
---

# OpusClip — Reframe

Smart aspect ratio conversion with face detection and activity zoom.

## Aspect ratios

### `9:16` (default) — YouTube Shorts, TikTok, Instagram Reels
Split layout:
- **Top 38%** — face panel (square crop, centered on detected face)
- **Bottom 62%** — zoomed screen area (~1.6× zoom, centered on cursor activity)

```bash
python main.py --url "URL" --aspect 9:16
```

### `1:1` — Instagram Feed, LinkedIn
Single crop centered on the face/activity zone.

```bash
python main.py --url "URL" --aspect 1:1
```

### `16:9` — YouTube standard, LinkedIn video, X/Twitter
No reframing — video is passed through at original landscape dimensions.
Subtitles still applied.

```bash
python main.py --url "URL" --aspect 16:9
```

## Face detection

Runs automatically on every clip using OpenCV Haar cascade.

**How it works:**
1. 12 frames are sampled from the raw downloaded clip
2. Haar cascade finds the largest face per frame
3. Median bounding box is computed across all frames (robust to misses)
4. Face box is expanded to a square panel centered on the face centroid
5. Panel snaps to the nearest frame edge (left/right column)

**If no face is detected:** full-frame center crop is used as fallback.
No configuration needed — it's fully automatic.

The cascade file is downloaded on first use to `~/.cache/yt-clipper/`.

## Activity zoom (screen panel)

For 9:16 output, the screen panel is zoomed ~1.6× to the area with the
most cursor/mouse activity.

**How it works:**
1. Frame differencing is computed on the screen region of the raw clip
2. A Gaussian-blurred motion heatmap is produced
3. Weighted centroid of the top 15% motion pixels is the zoom center
4. A crop of ~62% of the screen width is extracted, centered on the centroid
5. Scaled up to 1080px wide → effective ~1.6× zoom

For coding streams: zooms to the active code region.
For presentations: zooms to where the mouse/pointer is.
For talking-head videos (no screen): uses center crop.

## Layout proportions

```
Output (1080×1920):
┌─────────────────────┐
│   FACE PANEL        │  ← 38% = 729px tall
│   (square crop,     │
│    1080×1080 src)   │
├─────────────────────┤
│   SCREEN PANEL      │  ← 62% = 1191px tall
│   (~1.6× zoom,      │
│    centered on       │
│    cursor activity)  │
└─────────────────────┘
```

Adjust `FACE_RATIO` in `src/video_cutter.py` to change the split (default: 0.38).

## Troubleshooting

### Face appears cut off at top

**Cause:** Face detected near top edge of frame; square crop overshoots.
**Solution:** The square panel already compensates by centering on the face centroid.
If still cut off, reduce `FACE_RATIO` slightly (e.g., 0.35) to give the face
panel more vertical space.

### Screen panel shows wrong area (not the code)

**Cause:** Activity detection finds motion in chat overlay or notification area.
**Solution:** The activity center is logged: `[INFO] Activity center (in screen): x=N y=N`.
If x is far left (<200), the frame differencing might be picking up sidebar motion.
This is usually because the chat panel is active. Adjust sampling by editing
`_activity_center()` in `src/frame_analyzer.py`.

### 1:1 output doesn't center on the right person

**Cause:** No face detected; center crop used as fallback.
**Solution:** Verify face detection is working:
```bash
python -c "
import sys; sys.path.insert(0, '.')
from src.frame_analyzer import analyze
layout = analyze('temp/YOUR_CLIP.mp4')
print('Face:', layout.face)
"
```
