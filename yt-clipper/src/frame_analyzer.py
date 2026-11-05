"""
Detects face and screen/content regions from a video clip.

Uses OpenCV Haar cascade (downloaded on first use to ~/.cache/yt-clipper/).
Samples N frames, takes median bounding box, infers screen as the largest
rectangle not covered by the face panel.
"""
import logging
import urllib.request
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import cv2

log = logging.getLogger(__name__)

_CACHE_DIR  = Path.home() / ".cache" / "yt-clipper"
_CASCADE_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades"
    "/haarcascade_frontalface_default.xml"
)
_CASCADE_PATH = _CACHE_DIR / "haarcascade_frontalface_default.xml"


def _get_cascade() -> cv2.CascadeClassifier:
    if not _CASCADE_PATH.exists():
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        log.info("Downloading Haar cascade...")
        urllib.request.urlretrieve(_CASCADE_URL, _CASCADE_PATH)
    return cv2.CascadeClassifier(str(_CASCADE_PATH))


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int

    def area(self) -> int:
        return self.w * self.h


@dataclass
class LayoutResult:
    frame_w: int
    frame_h: int
    face: Region | None      # None if no face detected
    screen: Region           # main content/code area
    activity_cx: int = -1   # cursor/activity X inside screen region (-1 = center)
    activity_cy: int = -1   # cursor/activity Y inside screen region (-1 = center)


def _sample_frames(video_path: str, n: int = 12, offset_s: float = 0.0) -> list[np.ndarray]:
    cap   = cv2.VideoCapture(video_path)
    fps   = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start = int(offset_s * fps)
    end   = max(start + 1, total - 1)
    frames = []
    for pos in np.linspace(start, end, n, dtype=int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(pos))
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    return frames


def _detect_faces(frames: list[np.ndarray]) -> list[tuple]:
    cascade = _get_cascade()
    hits = []
    for frame in frames:
        fh, fw = frame.shape[:2]
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # minSize = 5% of frame width (filters noise but keeps webcam panels)
        min_dim = int(fw * 0.05)
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3, minSize=(min_dim, min_dim)
        )
        if len(faces):
            # Keep only the LARGEST detection per frame (webcam > thumbnails)
            largest = max(faces.tolist(), key=lambda f: f[2] * f[3])
            hits.append(largest)
    return hits


def _median_region(hits: list[tuple], fw: int, fh: int) -> Region | None:
    if not hits:
        return None
    arr = np.array(hits)
    r = Region(
        x=int(np.median(arr[:, 0])),
        y=int(np.median(arr[:, 1])),
        w=int(np.median(arr[:, 2])),
        h=int(np.median(arr[:, 3])),
    )
    # Clamp to frame bounds
    r.x = max(0, min(r.x, fw - 1))
    r.y = max(0, min(r.y, fh - 1))
    r.w = min(r.w, fw - r.x)
    r.h = min(r.h, fh - r.y)
    return r


def _expand_to_panel(face: Region, fw: int, fh: int) -> Region:
    """
    Build a SQUARE crop region centered on the detected face.
    Extends horizontally to the nearest frame edge (the webcam panel side).
    Square keeps the aspect ratio manageable so ffmpeg scaling doesn't
    push the face out of the visible crop area.
    """
    cx = face.x + face.w / 2
    face_cy = int(face.y + face.h / 2)

    if cx > fw * 0.5:   # face on the right
        panel_x = max(0, face.x - face.w)  # extend a bit left of face
        panel_w = fw - panel_x
    else:               # face on the left
        panel_x = 0
        panel_w = min(fw, face.x + face.w * 2)

    # Square: height = width, but clamped to frame height
    panel_h = min(panel_w, fh)
    panel_y = face_cy - panel_h // 2
    panel_y = max(0, min(fh - panel_h, panel_y))

    return Region(x=panel_x, y=panel_y, w=panel_w, h=panel_h)


def _infer_screen(face_panel: Region, fw: int, fh: int) -> Region:
    """Pick the largest rectangle on any of the four sides of the face panel."""
    p = face_panel
    candidates = [
        Region(x=0,       y=0, w=p.x,       h=fh),
        Region(x=p.x+p.w, y=0, w=fw-(p.x+p.w), h=fh),
        Region(x=0,       y=0, w=fw,         h=p.y),
        Region(x=0,       y=p.y+p.h, w=fw,   h=fh-(p.y+p.h)),
    ]
    best = max(candidates, key=lambda r: r.area())
    if best.area() < fw * fh * 0.15:
        log.warning("Screen region suspiciously small — using full frame")
        return Region(x=0, y=0, w=fw, h=fh)
    return best


def _activity_center(frames: list[np.ndarray], screen: Region) -> tuple[int, int]:
    """
    Find where most motion happens inside the screen region (cursor / scrolling).
    Returns (cx, cy) relative to the screen region top-left.
    Uses frame differencing — works on the raw landscape tmp file.
    """
    # Crop each frame to the screen region only
    crops = [
        cv2.cvtColor(
            f[screen.y : screen.y + screen.h, screen.x : screen.x + screen.w],
            cv2.COLOR_BGR2GRAY,
        ).astype(np.float32)
        for f in frames
    ]
    if len(crops) < 2:
        return screen.w // 2, screen.h // 2

    diffs = [np.abs(crops[i + 1] - crops[i]) for i in range(len(crops) - 1)]
    heat  = np.mean(diffs, axis=0)

    # Blur to suppress single-pixel noise (font antialiasing, compression)
    heat = cv2.GaussianBlur(heat, (31, 31), 0)

    thresh = np.percentile(heat, 85)
    hot_y, hot_x = np.where(heat > thresh)
    if len(hot_x):
        cx = int(np.average(hot_x, weights=heat[hot_y, hot_x]))
        cy = int(np.average(hot_y, weights=heat[hot_y, hot_x]))
        return cx, cy
    return screen.w // 2, screen.h // 2


def analyze(video_path: str, offset_s: float = 0.0, n_frames: int = 12) -> LayoutResult:
    frames = _sample_frames(video_path, n=n_frames, offset_s=offset_s)
    if not frames:
        raise RuntimeError(f"Could not read frames from {video_path}")

    fh, fw = frames[0].shape[:2]
    hits   = _detect_faces(frames)
    face   = _median_region(hits, fw, fh)

    if face:
        log.info(
            f"Face detected: x={face.x} y={face.y} {face.w}×{face.h} "
            f"({len(hits)} hits across {len(frames)} frames)"
        )
        face = _expand_to_panel(face, fw, fh)
        log.info(f"Face panel:    x={face.x} y={face.y} {face.w}×{face.h}")
        screen = _infer_screen(face, fw, fh)
        log.info(f"Screen region: x={screen.x} y={screen.y} {screen.w}×{screen.h}")
    else:
        log.warning("No face detected — using full frame as screen")
        screen = Region(x=0, y=0, w=fw, h=fh)

    # Detect where the action/cursor is inside the screen region
    act_cx, act_cy = _activity_center(frames, screen)
    log.info(f"Activity center (in screen): x={act_cx} y={act_cy}")

    return LayoutResult(frame_w=fw, frame_h=fh, face=face, screen=screen,
                        activity_cx=act_cx, activity_cy=act_cy)
