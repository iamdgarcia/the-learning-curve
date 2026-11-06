import logging
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from src.config import settings

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _get_credentials() -> Credentials:
    token_file = settings.youtube_token_file
    secrets_file = settings.youtube_client_secrets_file
    creds = None

    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            log.info("Starting OAuth flow — browser will open...")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(token_file).write_text(creds.to_json())

    return creds


def upload(
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "unlisted",
) -> dict:
    """Upload a clip to YouTube. Returns {"video_id": ..., "url": ...}."""
    log.info(f"Uploading: {title}")
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "22",  # People & Blogs
        },
        "status": {"privacyStatus": privacy},
    }

    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()
    except HttpError as e:
        if e.resp.status == 403 and b"quotaExceeded" in e.content:
            raise RuntimeError("YouTube quota exceeded (403). Upload failed.")
        raise

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    log.info(f"Uploaded → {url}")
    return {"video_id": video_id, "url": url}
