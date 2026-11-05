#!/usr/bin/env python3
"""
Upload already-generated clips from temp/ using clips_metadata.json.
Does NOT re-run the full pipeline — just reads existing mp4s and uploads them.

Usage:
    python upload_ready_clips.py --privacy unlisted
    python upload_ready_clips.py --privacy public
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from src import youtube_uploader
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser(description="Upload pre-generated clips to YouTube")
    p.add_argument("--privacy", default="unlisted", choices=["public", "private", "unlisted"])
    p.add_argument("--metadata", default="temp/clips_metadata.json")
    p.add_argument("--clips-dir", default="temp")
    args = p.parse_args()

    meta_path = Path(args.metadata)
    if not meta_path.exists():
        log.error(f"Metadata not found: {meta_path}")
        sys.exit(1)

    clips = json.loads(meta_path.read_text())
    log.info(f"Found {len(clips)} clips in metadata")

    clips_dir = Path(args.clips_dir)
    failed = []
    uploaded = []

    for clip in clips:
        cid  = clip["clip_id"]
        s, e = clip["start_seconds"], clip["end_seconds"]

        # Find the mp4 — exact name pattern
        mp4 = clips_dir / f"clip_{cid}_{s}-{e}.mp4"
        if not mp4.exists():
            log.warning(f"File not found, skipping: {mp4}")
            continue

        title       = clip["title"]
        description = clip.get("full_description", clip.get("description", ""))
        tags        = clip.get("tags", [])

        log.info(f"Uploading [{mp4.name}]: {title}")
        try:
            info = youtube_uploader.upload(
                str(mp4), title=title, description=description,
                tags=tags, privacy=args.privacy,
            )
            uploaded.append({"clip": title, **info})
            log.info(f"  ✅ {info['url']}")
        except RuntimeError as exc:
            log.error(f"  ❌ {exc}")
            failed.append({"clip": title, "file": str(mp4), "error": str(exc)})

    print(f"\n{'='*50}")
    print(f"Uploaded: {len(uploaded)}  Failed: {len(failed)}")
    for u in uploaded:
        print(f"  ✅ {u['clip'][:60]}")
        print(f"     {u['url']}")
    if uploaded:
        uploaded_path = clips_dir / "uploaded.json"
        uploaded_path.write_text(json.dumps(
            [{"video_id": u["video_id"], "title": u["clip"], "url": u["url"]} for u in uploaded],
            indent=2, ensure_ascii=False,
        ))
        log.info(f"Uploaded list saved → {uploaded_path}")
    if failed:
        fail_path = clips_dir / "failed_uploads.json"
        fail_path.write_text(json.dumps(failed, indent=2, ensure_ascii=False))
        log.warning(f"Failures saved → {fail_path}")


if __name__ == "__main__":
    main()
