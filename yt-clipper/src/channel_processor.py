"""
Batch-processes an entire YouTube channel: lists videos, filters them,
and runs the clip pipeline on each.

Usage (standalone):
    python -m src.channel_processor \
        --channel "https://www.youtube.com/@TheLearningCurveAI" \
        --max-videos 10 \
        --min-duration 300 \
        --max-clips-per-video 3 \
        --mode shorts
"""
import subprocess
import sys
import json
import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

_YTDLP = shutil.which("yt-dlp") or None
_NODE  = shutil.which("node") or ""

def _ytdlp() -> list[str]:
    base = [_YTDLP] if _YTDLP else ["python", "-m", "yt_dlp"]
    return base + [
        "--no-update", "--no-warnings",
        "--cookies-from-browser", "firefox",
        "--no-js-runtimes",
        *(["--js-runtimes", f"node:{_NODE}"] if _NODE else []),
    ]


def list_videos(
    channel_url: str,
    max_videos: int = 20,
    min_duration: int = 120,    # seconds — skip very short videos
    max_duration: int = 86400,  # seconds — skip multi-day streams
) -> list[dict]:
    """Return list of {id, title, duration, url} for a channel."""
    log.info(f"Listing videos from {channel_url} (max={max_videos})...")
    cmd = _ytdlp() + [
        "--flat-playlist",
        "--print", "%(id)s\t%(title)s\t%(duration)s",
        "--playlist-end", str(max_videos * 3),  # fetch 3× to allow filtering
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    videos = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        vid_id, title, dur_str = parts[0], parts[1], parts[2]
        try:
            dur = float(dur_str)
        except ValueError:
            continue
        if min_duration <= dur <= max_duration:
            videos.append({
                "id": vid_id,
                "title": title,
                "duration": dur,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })
        if len(videos) >= max_videos:
            break

    log.info(f"Found {len(videos)} qualifying videos")
    return videos


def process_channel(
    channel_url: str,
    max_videos: int = 5,
    min_duration: int = 300,
    max_clips_per_video: int = 3,
    mode: str = "shorts",
    channel_context: str = "",
    caption_style: str = "karaoke",
    aspect: str = "9:16",
    auto_upload: bool = False,
    privacy: str = "unlisted",
    out_dir: str = "temp",
) -> list[dict]:
    """
    Process all qualifying videos from a channel.
    Returns list of {video, clips_generated, clips_uploaded}.
    """
    videos = list_videos(channel_url, max_videos=max_videos, min_duration=min_duration)
    results = []

    for i, video in enumerate(videos, 1):
        log.info(f"\n[{i}/{len(videos)}] Processing: {video['title']}")
        video_out = Path(out_dir) / video["id"]
        video_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, "main.py",
            "--url", video["url"],
            "--max-clips", str(max_clips_per_video),
            "--mode", mode,
            "--channel-context", channel_context or video["title"],
            "--caption-style", caption_style,
            "--aspect", aspect,
            "--privacy", privacy,
        ]
        if auto_upload:
            cmd.append("--auto-upload")

        result = subprocess.run(cmd, capture_output=False, text=True)

        # Read generated metadata
        meta_path = Path(out_dir) / "clips_metadata.json"
        clips = []
        if meta_path.exists():
            clips = json.loads(meta_path.read_text())

        results.append({
            "video": video,
            "returncode": result.returncode,
            "clips_generated": len(clips),
        })

        # Save per-video metadata
        if clips:
            (video_out / "clips_metadata.json").write_text(
                json.dumps(clips, ensure_ascii=False, indent=2)
            )

    # Summary
    total = sum(r["clips_generated"] for r in results)
    log.info(f"\nChannel processing complete: {total} clips from {len(videos)} videos")
    return results


if __name__ == "__main__":
    import argparse
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    p = argparse.ArgumentParser(description="Batch process a YouTube channel")
    p.add_argument("--channel", required=True, help="Channel URL")
    p.add_argument("--max-videos", type=int, default=5)
    p.add_argument("--min-duration", type=int, default=300, help="Minimum video duration (seconds)")
    p.add_argument("--max-clips-per-video", type=int, default=3)
    p.add_argument("--mode", default="shorts", choices=["shorts", "standard", "emotion", "topic"])
    p.add_argument("--channel-context", default="")
    p.add_argument("--caption-style", default="karaoke", choices=["karaoke", "wordbox", "clean", "emoji"])
    p.add_argument("--aspect", default="9:16", choices=["9:16", "1:1", "16:9"])
    p.add_argument("--auto-upload", action="store_true")
    p.add_argument("--privacy", default="unlisted")
    args = p.parse_args()

    process_channel(
        channel_url=args.channel,
        max_videos=args.max_videos,
        min_duration=args.min_duration,
        max_clips_per_video=args.max_clips_per_video,
        mode=args.mode,
        channel_context=args.channel_context,
        caption_style=args.caption_style,
        aspect=args.aspect,
        auto_upload=args.auto_upload,
        privacy=args.privacy,
    )
