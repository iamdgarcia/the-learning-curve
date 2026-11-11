#!/usr/bin/env python3
"""
Generic uploader — uploads any list of MP4s to YouTube and writes temp/uploaded.json.
Works for Pipeline B (faceless), Pipeline C (interview), or any generated MP4.

Usage:
    # Upload specific files (title inferred from filename if not set via --titles)
    python upload_videos.py temp/interview_*.mp4

    # Upload with explicit titles (one per file, same order)
    python upload_videos.py temp/a.mp4 temp/b.mp4 --titles "Title A" "Title B"

    # Upload as public
    python upload_videos.py temp/interview_*.mp4 --privacy public

    # Then schedule every 2 hours:
    python schedule_clips.py --from-file temp/uploaded.json --interval-hours 2

    # Or schedule with the preferred-slot algorithm:
    python schedule_clips.py --from-file temp/uploaded.json
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
import argparse
import json
import logging
import sys
from pathlib import Path

from src import youtube_uploader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

DEFAULT_DESCRIPTION = (
    "Aprende a usar IA para ser más productivo y ganar dinero.\n\n"
    "🎓 The Learning Curve — Aprende IA como un ingeniero, no como un gurú de YouTube.\n"
    "👉 Suscríbete gratis: https://iamdgarcia.substack.com\n\n"
    "#IA #InteligenciaArtificial #LLMs #Claude #AIAgents"
)


def main():
    p = argparse.ArgumentParser(description="Upload MP4s to YouTube")
    p.add_argument("files", nargs="+", help="MP4 files to upload (supports globs via shell)")
    p.add_argument("--titles", nargs="+", help="Titles (one per file, same order). Default: filename stem.")
    p.add_argument("--description", default=DEFAULT_DESCRIPTION)
    p.add_argument("--tags", nargs="+", default=["IA", "Claude", "LLMs", "agentes", "productividad"])
    p.add_argument("--privacy", default="private", choices=["public", "private", "unlisted"])
    p.add_argument("--out", default="temp/uploaded.json", help="Output JSON path")
    args = p.parse_args()

    files = [Path(f) for f in args.files]
    titles = args.titles or [f.stem for f in files]

    if len(titles) != len(files):
        log.error(f"--titles count ({len(titles)}) must match file count ({len(files)})")
        sys.exit(1)

    missing = [f for f in files if not f.exists()]
    if missing:
        log.error(f"Files not found: {missing}")
        sys.exit(1)

    uploaded, failed = [], []
    for mp4, title in zip(files, titles):
        log.info(f"Uploading: {title}")
        try:
            info = youtube_uploader.upload(
                str(mp4), title=title, description=args.description,
                tags=args.tags, privacy=args.privacy,
            )
            uploaded.append({"video_id": info["video_id"], "title": title, "url": info["url"]})
            log.info(f"  ✅ {info['url']}")
        except Exception as e:
            log.error(f"  ❌ {e}")
            failed.append({"file": str(mp4), "title": title, "error": str(e)})

    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(uploaded, indent=2, ensure_ascii=False))
    log.info(f"Saved {len(uploaded)} entries → {out}")

    print(f"\n{'='*55}")
    print(f"Uploaded: {len(uploaded)}  Failed: {len(failed)}")
    for u in uploaded:
        print(f"  ✅ {u['title'][:55]}")
        print(f"     {u['url']}")
    if failed:
        print(f"\n  ❌ Failed:")
        for f in failed:
            print(f"     {f['file']}: {f['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
