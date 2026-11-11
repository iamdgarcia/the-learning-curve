#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
import argparse
import json
import logging
import sys
from pathlib import Path

from src import transcript_extractor, clip_analyzer, video_cutter, youtube_uploader
from src.clip_analyzer import ClipMode
from src.subtitle_generator import CaptionStyle
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(description="Automated YouTube Video Clipper & Publisher")
    p.add_argument("--url", required=True, help="Source YouTube video URL")
    p.add_argument("--max-clips", type=int, default=settings.max_clips_per_video,
                   help="Number of clips to generate (default: %(default)s)")
    p.add_argument("--mode", default="shorts", choices=[m.value for m in ClipMode],
                   help="Clip mode: shorts/standard/emotion/topic (default: %(default)s)")
    p.add_argument("--topic", default="",
                   help="Topic to focus on when --mode topic (e.g. 'probabilidades LLM')")
    p.add_argument("--channel-context", default="",  # auto-read from config/faceless_brand.json if empty
                   help="Brief channel description to guide the LLM")
    p.add_argument("--caption-style", default="karaoke",
                   choices=[s.value for s in CaptionStyle],
                   help="Subtitle visual style (default: %(default)s)")
    p.add_argument("--aspect", default="9:16", choices=["9:16", "1:1", "16:9"],
                   help="Output aspect ratio (default: %(default)s)")
    # OpusClip-equivalent features
    p.add_argument("--hook", action="store_true",
                   help="Burn auto hook text overlay on first 3 seconds")
    p.add_argument("--hook-template", default="hook-01",
                   choices=["hook-01","hook-02","hook-03","hook-04","hook-05"],
                   help="Hook visual template (default: %(default)s)")
    p.add_argument("--enhance-audio", action="store_true",
                   help="Denoise audio (background noise reduction)")
    p.add_argument("--diarize", action="store_true",
                   help="Speaker diarization — color captions by speaker")
    p.add_argument("--broll", action="store_true",
                   help="Auto insert B-roll stock footage (requires PEXELS_API_KEY)")
    p.add_argument("--pexels-key", default=settings.pexels_api_key,
                   help="Pexels API key for B-roll (or set PEXELS_API_KEY in .env)")
    p.add_argument("--privacy", default=settings.default_privacy_status,
                   choices=["public", "private", "unlisted"],
                   help="Upload privacy status (default: %(default)s)")
    p.add_argument("--auto-upload", action="store_true",
                   help="Automatically upload clips to YouTube after cutting")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(settings.output_dir)
    out_dir.mkdir(exist_ok=True)
    failed_uploads = []

    # 1. Transcript
    try:
        transcript = transcript_extractor.extract(args.url)
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    # 2. AI clip analysis
    try:
        result = clip_analyzer.analyze(
            transcript["text"],
            max_clips=args.max_clips,
            mode=ClipMode(args.mode),
            channel_context=args.channel_context,
            language=transcript["language_code"],
            topic=args.topic,
        )
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

    clips = result.clips
    log.info(f"Found {len(clips)} clips.")

    # Build channel handle from URL for the footer
    _channel = brand.channel_handle if hasattr(brand, "channel_handle") else ""

    def _description(clip) -> str:
        footer = (
            f"\n\n"
            f"📺 Video completo: https://youtu.be/{transcript['video_id']}?t={clip.start_seconds}\n"
            f"🔔 Suscríbete: https://www.youtube.com/{_channel}"
        )
        return clip.description + footer

    # Save metadata (with full descriptions)
    meta_path = out_dir / "clips_metadata.json"
    meta_path.write_text(json.dumps(
        [{**c.model_dump(), "full_description": _description(c)} for c in clips], indent=2, ensure_ascii=False
    ))
    log.info(f"Metadata saved → {meta_path}")

    # 3. Cut clips
    cut_files = []
    for i, clip in enumerate(clips, 1):
        log.info(f"Cutting clip {i}/{len(clips)}: {clip.title}")
        out_path = out_dir / f"clip_{clip.clip_id}_{clip.start_seconds}-{clip.end_seconds}.mp4"
        try:
            path = video_cutter.cut(
                args.url, clip.start_seconds, clip.end_seconds, str(out_path),
                language=transcript["language_code"],
                transcript_segments=transcript["raw"],
                has_word_timestamps=transcript.get("has_word_timestamps", False),
                caption_style=CaptionStyle(args.caption_style),
                aspect=args.aspect,
                enhance_audio=args.enhance_audio,
                hook_text=clip.hook if args.hook else "",
                hook_template=args.hook_template,
                diarize=args.diarize,
                broll=args.broll,
                clip_transcript_text=transcript["text"],
                pexels_key=args.pexels_key,
            )
            cut_files.append((clip, path))
        except RuntimeError as e:
            log.error(f"Failed to cut clip {i}: {e}")
            failed_uploads.append({"clip": clip.model_dump(), "error": str(e)})

    if not args.auto_upload:
        log.info("--auto-upload not set. Done. Clips are in the temp/ directory.")
        return

    # 4. Upload
    uploaded_videos = []
    for i, (clip, path) in enumerate(cut_files, 1):
        log.info(f"Uploading clip {i}/{len(cut_files)}: {clip.title}")
        try:
            info = youtube_uploader.upload(
                str(path),
                title=clip.title,
                description=_description(clip),
                tags=clip.tags,
                privacy=args.privacy,
            )
            log.info(f"  → {info['url']}")
            uploaded_videos.append({"video_id": info["video_id"], "title": clip.title, "url": info["url"]})
        except RuntimeError as e:
            log.error(f"Upload failed for clip {i}: {e}")
            failed_uploads.append({"clip": clip.model_dump(), "file": str(path), "error": str(e)})

    if failed_uploads:
        fail_path = out_dir / "failed_uploads.json"
        fail_path.write_text(json.dumps(failed_uploads, indent=2))
        log.warning(f"{len(failed_uploads)} item(s) failed — see {fail_path}")

    # Write uploaded.json for schedule_clips.py
    uploaded_path = out_dir / "uploaded.json"
    uploaded_path.write_text(json.dumps(uploaded_videos, indent=2, ensure_ascii=False))
    log.info(f"Uploaded list saved → {uploaded_path}")

    log.info("All done.")


if __name__ == "__main__":
    main()
