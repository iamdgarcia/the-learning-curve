"""
YouTube channel analytics — wraps YouTube Data API v3 + YouTube Analytics API v2.

Usage (CLI):
    python -m src.youtube_analytics --report channel
    python -m src.youtube_analytics --report top-videos --days 90
    python -m src.youtube_analytics --report traffic --days 30
    python -m src.youtube_analytics --report devices
    python -m src.youtube_analytics --report schedule-insights
    python -m src.youtube_analytics --report video --id VIDEO_ID

All reports are printed to stdout as readable tables.
"""
import argparse
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import settings

log = logging.getLogger(__name__)
MADRID = ZoneInfo("Europe/Madrid")

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

DAYS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


# ── Auth ──────────────────────────────────────────────────────────────────────

def _creds() -> Credentials:
    token_file   = Path(settings.youtube_token_file)
    secrets_file = settings.youtube_client_secrets_file
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())

    return creds


def _clients():
    creds = _creds()
    yt  = build("youtube",          "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)
    return yt, yta


def _channel_id(yt) -> str:
    resp = yt.channels().list(part="id", mine=True).execute()
    return resp["items"][0]["id"]


def _dur_str(iso: str) -> str:
    m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mn, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    total = h * 3600 + mn * 60 + s
    if total < 3600:
        return f"{mn}:{s:02d}"
    return f"{h}:{mn:02d}:{s:02d}"


# ── Reports ───────────────────────────────────────────────────────────────────

def report_channel(days: int = 90) -> dict:
    """Overall channel metrics for the last N days."""
    yt, yta = _clients()
    cid = _channel_id(yt)
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    # Channel snippet + totals
    ch = yt.channels().list(
        part="snippet,statistics", mine=True
    ).execute()["items"][0]
    sn = ch["snippet"]
    st = ch["statistics"]

    # Analytics period
    ana = yta.reports().query(
        ids=f"channel=={cid}", startDate=start, endDate=end,
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,shares",
    ).execute()
    cols = [c["name"] for c in ana["columnHeaders"]]
    row  = ana["rows"][0] if ana.get("rows") else [0] * len(cols)
    period = dict(zip(cols, row))

    print(f"\n{'='*55}")
    print(f"  CANAL: {sn['title']}")
    print(f"{'='*55}")
    print(f"  Suscriptores totales : {int(st.get('subscriberCount', 0)):,}")
    print(f"  Vídeos publicados    : {int(st.get('videoCount', 0)):,}")
    print(f"  Views totales        : {int(st.get('viewCount', 0)):,}")
    print(f"\n  — Últimos {days} días —")
    print(f"  Views                : {int(period.get('views', 0)):,}")
    dur = int(period.get("averageViewDuration", 0))
    print(f"  Duración media vista : {dur//60}m {dur%60}s")
    print(f"  Minutos vistos       : {int(period.get('estimatedMinutesWatched', 0)):,}")
    print(f"  Subs ganados         : +{int(period.get('subscribersGained', 0))}")
    print(f"  Subs perdidos        : -{int(period.get('subscribersLost', 0))}")
    likes = int(period.get('likes', 0))
    views = int(period.get('views', 1))
    print(f"  Likes                : {likes:,}  (ratio: {likes/views:.2%})")
    print(f"  Shares               : {int(period.get('shares', 0)):,}")
    return period


def report_top_videos(days: int = 90, limit: int = 15) -> list:
    """Top videos by views with retention %."""
    yt, yta = _clients()
    cid = _channel_id(yt)
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    top = yta.reports().query(
        ids=f"channel=={cid}", startDate=start, endDate=end,
        metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
        dimensions="video", sort="-views", maxResults=limit,
    ).execute()

    vid_ids = [r[0] for r in top.get("rows", [])]
    titles  = {}
    if vid_ids:
        det = yt.videos().list(
            part="snippet,contentDetails", id=",".join(vid_ids)
        ).execute()
        for item in det.get("items", []):
            total_s = sum(
                int(x or 0) * m
                for x, m in zip(
                    re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
                               item["contentDetails"]["duration"]).groups(),
                    [3600, 60, 1],
                )
            ) if re.search(r"PT", item["contentDetails"]["duration"]) else 0
            tipo = "🩳" if total_s <= 60 else "🎬"
            titles[item["id"]] = (item["snippet"]["title"][:48], tipo)

    print(f"\n{'='*88}")
    print(f"  TOP {limit} VÍDEOS — últimos {days} días")
    print(f"{'='*88}")
    print(f"  {'Views':>7} {'WMin':>8} {'AvgDur':>7} {'Ret%':>7}  Tipo  Título")
    print(f"  {'─'*82}")
    rows = []
    for r in top.get("rows", []):
        vid, views, wm, ad, rp = r[0], r[1], r[2], r[3], r[4]
        t, tipo = titles.get(vid, (vid, "?"))
        ds = f"{int(ad)//60}:{int(ad)%60:02d}"
        print(f"  {int(views):>7,} {wm:>8,.0f} {ds:>7} {rp:>6.1f}%   {tipo}  {t}")
        rows.append({"video_id": vid, "title": t, "views": int(views),
                     "watch_minutes": wm, "retention_pct": rp})
    return rows


def report_traffic(days: int = 90) -> list:
    """Traffic sources breakdown."""
    yt, yta = _clients()
    cid = _channel_id(yt)
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    traffic = yta.reports().query(
        ids=f"channel=={cid}", startDate=start, endDate=end,
        metrics="views", dimensions="insightTrafficSourceType", sort="-views",
    ).execute()

    total = sum(int(r[1]) for r in traffic.get("rows", []))
    print(f"\n{'='*55}")
    print(f"  FUENTES DE TRÁFICO — últimos {days} días")
    print(f"{'='*55}")
    rows = []
    for r in traffic.get("rows", []):
        src, v = r[0], int(r[1])
        pct = v / max(1, total) * 100
        bar = "█" * int(pct / 2)
        print(f"  {src:<35} {v:>6,}  {pct:>5.1f}%  {bar}")
        rows.append({"source": src, "views": v, "pct": pct})
    return rows


def report_devices(days: int = 90) -> list:
    """Device breakdown."""
    yt, yta = _clients()
    cid = _channel_id(yt)
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    dev = yta.reports().query(
        ids=f"channel=={cid}", startDate=start, endDate=end,
        metrics="views", dimensions="deviceType", sort="-views",
    ).execute()

    total = sum(int(r[1]) for r in dev.get("rows", []))
    print(f"\n{'='*40}")
    print(f"  DISPOSITIVOS — últimos {days} días")
    print(f"{'='*40}")
    rows = []
    for r in dev.get("rows", []):
        d, v = r[0], int(r[1])
        pct = v / max(1, total) * 100
        print(f"  {d:<20} {v:>6,}  {pct:>5.1f}%")
        rows.append({"device": d, "views": v, "pct": pct})
    return rows


def report_schedule_insights(days: int = 30) -> dict:
    """Best days/hours to publish based on actual channel data."""
    yt, yta = _clients()
    cid = _channel_id(yt)
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    daily = yta.reports().query(
        ids=f"channel=={cid}", startDate=start, endDate=end,
        metrics="views", dimensions="day", sort="day",
    ).execute()

    dow_views: dict[int, list] = defaultdict(list)
    for r in daily.get("rows", []):
        d = datetime.strptime(r[0], "%Y-%m-%d").weekday()
        dow_views[d].append(int(r[1]))

    avg_by_day = {d: sum(v) / len(v) for d, v in dow_views.items()}
    max_v = max(avg_by_day.values(), default=1)

    print(f"\n{'='*50}")
    print(f"  MEJORES DÍAS PARA PUBLICAR (datos reales {days}d)")
    print(f"{'='*50}")
    best_days = sorted(avg_by_day.items(), key=lambda x: -x[1])
    for d, v in best_days:
        bar = "█" * int(v / max_v * 25)
        star = " ⭐" if d == best_days[0][0] else ""
        print(f"  {DAYS_ES[d]}: {v:>7.1f} avg views  {bar}{star}")

    best = [DAYS_ES[d] for d, _ in best_days[:3]]
    print(f"\n  → Publicar preferentemente: {', '.join(best)}")
    print(f"  → Evitar: {DAYS_ES[best_days[-1][0]]} (peor día)")
    return avg_by_day


def report_video(video_id: str) -> dict:
    """Stats for a specific video."""
    yt, yta = _clients()
    cid = _channel_id(yt)

    resp = yt.videos().list(
        part="snippet,statistics,contentDetails,status", id=video_id
    ).execute()
    if not resp.get("items"):
        print(f"Video {video_id} not found")
        return {}

    item = resp["items"][0]
    sn = item["snippet"]
    st = item["statistics"]
    sta = item["status"]
    cd = item["contentDetails"]

    pub = sta.get("publishAt") or sn.get("publishedAt", "")[:10]
    print(f"\n{'='*60}")
    print(f"  VIDEO: {sn['title'][:55]}")
    print(f"{'='*60}")
    print(f"  ID          : {video_id}")
    print(f"  Duración    : {_dur_str(cd['duration'])}")
    print(f"  Estado      : {sta['privacyStatus']}  (publicación: {pub})")
    print(f"  Views       : {int(st.get('viewCount', 0)):,}")
    print(f"  Likes       : {int(st.get('likeCount', 0)):,}")
    print(f"  Comentarios : {int(st.get('commentCount', 0)):,}")

    # Analytics if published
    try:
        end   = date.today().isoformat()
        start = (date.today() - timedelta(days=90)).isoformat()
        ana = yta.reports().query(
            ids=f"channel=={cid}", startDate=start, endDate=end,
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
            dimensions="video", filters=f"video=={video_id}",
        ).execute()
        if ana.get("rows"):
            r = ana["rows"][0]
            dur = int(r[3])
            print(f"  Retención   : {r[4]:.1f}%")
            print(f"  Duración med: {dur//60}:{dur%60:02d}")
            print(f"  Min. vistos : {r[2]:,.0f}")
    except Exception:
        pass

    return item


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    p = argparse.ArgumentParser(description="YouTube channel analytics")
    p.add_argument("--report", required=True,
                   choices=["channel", "top-videos", "traffic", "devices",
                            "schedule-insights", "video"])
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--id", dest="video_id", help="Video ID for --report video")
    args = p.parse_args()

    if args.report == "channel":
        report_channel(args.days)
    elif args.report == "top-videos":
        report_top_videos(args.days, args.limit)
    elif args.report == "traffic":
        report_traffic(args.days)
    elif args.report == "devices":
        report_devices(args.days)
    elif args.report == "schedule-insights":
        report_schedule_insights(args.days)
    elif args.report == "video":
        if not args.video_id:
            print("--id required for --report video")
        else:
            report_video(args.video_id)
