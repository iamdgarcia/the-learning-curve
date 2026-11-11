#!/usr/bin/env python3
"""
Schedule already-uploaded YouTube videos for public release.

Best practices for YouTube Shorts (Spanish tech audience):
- Frequency: 3-4 Shorts/week, never more than 1/day
- Best slots: Tue/Wed/Thu/Sat at 14:00 Spain time (peak lunch engagement)
- Spacing: minimum 2 days between clips
- Avoids: Monday (low engagement), Sunday evenings (algorithm resets)

The videos must already be uploaded (any privacy). This script updates
their status to scheduled (private → auto-publish at publishAt time).

Usage:
    python schedule_clips.py --video-ids ID1 ID2 ID3 ID4 ID5
    python schedule_clips.py --from-file temp/uploaded.json
    python schedule_clips.py --from-file temp/uploaded.json --start 2026-10-27
    python schedule_clips.py --from-file temp/uploaded.json --interval-hours 2
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
import argparse
import json
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")

# Best publishing slots: (weekday 0=Mon, hour in Madrid local time)
# Priority order — algo-favoured for tech/education in Spain
PREFERRED_SLOTS = [
    (6, 14),   # Sunday   14:00  ⭐ mejor día (426 avg views reales)
    (4, 14),   # Friday   14:00  ⭐ segundo mejor (342 avg views)
    (3, 14),   # Thursday 14:00  tercer mejor (174 avg views)
    (0, 14),   # Monday   14:00
    (1, 14),   # Tuesday  14:00
    (5, 11),   # Saturday  11:00
]

MIN_GAP_DAYS = 2   # minimum days between consecutive publishes


def _get_credentials() -> Credentials:
    SCOPES = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload",
    ]
    token_file   = settings.youtube_token_file
    secrets_file = settings.youtube_client_secrets_file
    creds = None

    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(token_file).write_text(creds.to_json())

    return creds


def next_slot(after: datetime) -> datetime:
    """Return the next preferred publishing slot after `after` (Madrid time)."""
    # Start from the next day minimum
    candidate = after.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)

    for _ in range(30):  # search up to 30 days ahead
        wd = candidate.weekday()
        for slot_wd, slot_h in PREFERRED_SLOTS:
            if wd == slot_wd:
                slot = candidate.replace(hour=slot_h, minute=0, second=0)
                if slot > after + timedelta(hours=1):
                    return slot
        candidate += timedelta(days=1)

    raise RuntimeError("Could not find a slot in the next 30 days")


def build_schedule(n: int, start_after: datetime | None = None) -> list[datetime]:
    """Build n publishing slots respecting MIN_GAP_DAYS between each."""
    slots = []
    cursor = start_after or datetime.now(MADRID)

    for _ in range(n):
        slot = next_slot(cursor)
        slots.append(slot)
        cursor = slot + timedelta(days=MIN_GAP_DAYS)

    return slots


def schedule_video(youtube, video_id: str, publish_at: datetime) -> dict:
    """Update a video's status to scheduled private → public at publish_at."""
    publish_utc = publish_at.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body = {
        "id": video_id,
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_utc,
            "selfDeclaredMadeForKids": False,
        },
    }

    response = youtube.videos().update(
        part="status",
        body=body,
    ).execute()

    return response


def main():
    p = argparse.ArgumentParser(description="Schedule uploaded YouTube clips")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--video-ids", nargs="+", help="YouTube video IDs to schedule")
    g.add_argument("--from-file", help="JSON file with [{video_id, title, url}, ...]")
    p.add_argument("--start", help="Start scheduling from this date (YYYY-MM-DD), default: tomorrow")
    p.add_argument("--interval-hours", type=float, default=0,
                   help="Publish every N hours from now (bypasses preferred-slot algorithm)")
    p.add_argument("--dry-run", action="store_true", help="Show schedule without applying")
    args = p.parse_args()

    # Load video IDs
    if args.video_ids:
        videos = [{"video_id": vid, "title": f"Video {vid}"} for vid in args.video_ids]
    else:
        data = json.loads(Path(args.from_file).read_text())
        videos = data if isinstance(data, list) else data.get("uploaded", [])

    if not videos:
        log.error("No videos to schedule")
        sys.exit(1)

    # Build schedule
    if args.interval_hours:
        # Simple every-N-hours mode: start from next round hour
        base = datetime.now(MADRID).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if (base - datetime.now(MADRID)).total_seconds() < 600:
            base += timedelta(hours=1)
        slots = [base + timedelta(hours=args.interval_hours * i) for i in range(len(videos))]
    else:
        start_after = None
        if args.start:
            d = datetime.strptime(args.start, "%Y-%m-%d")
            start_after = datetime(d.year, d.month, d.day, tzinfo=MADRID) - timedelta(days=1)
        slots = build_schedule(len(videos), start_after)

    # Print plan
    print("\n📅 PUBLISHING SCHEDULE")
    print("=" * 62)
    print(f"{'#':<3} {'Date & Time (Spain)':<24} {'Video ID':<14} Title")
    print("-" * 62)
    for i, (video, slot) in enumerate(zip(videos, slots), 1):
        vid_id = video.get("video_id", "?")
        title  = video.get("title", "")[:35]
        day_en = slot.strftime("%A")
        day_map = {"Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles",
                   "Thursday":"Jueves","Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"}
        day_es = day_map.get(day_en, day_en)
        print(f"{i:<3} {day_es} {slot.strftime('%d/%m %H:%M'):<18} {vid_id:<14} {title}")
    print("=" * 62)
    print(f"Span: {slots[0].strftime('%d/%m/%Y')} → {slots[-1].strftime('%d/%m/%Y')}")
    print(f"Spacing: every {MIN_GAP_DAYS}+ days at peak hours\n")

    if args.dry_run:
        log.info("Dry run — no changes made")
        return

    # Apply schedule
    creds   = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    results = []
    for video, slot in zip(videos, slots):
        vid_id = video.get("video_id")
        title  = video.get("title", vid_id)
        log.info(f"Scheduling {vid_id} → {slot.strftime('%A %d/%m %H:%M')} (Madrid)")
        try:
            schedule_video(youtube, vid_id, slot)
            url = f"https://www.youtube.com/watch?v={vid_id}"
            log.info(f"  ✅ Scheduled: {url}")
            results.append({"video_id": vid_id, "title": title,
                            "publish_at": slot.isoformat(), "url": url})
        except Exception as e:
            log.error(f"  ❌ Failed {vid_id}: {e}")

    # Save schedule record
    out = Path("temp/schedule.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    log.info(f"\nSchedule saved → {out}")
    print(f"\n✅ {len(results)}/{len(videos)} clips scheduled successfully")


if __name__ == "__main__":
    main()
