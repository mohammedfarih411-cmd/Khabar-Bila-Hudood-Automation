from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
LOGGER = logging.getLogger(__name__)


def _load_credentials(token_path: str | Path = "token.json") -> Credentials:
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    if token_json:
        info = json.loads(token_json)
        return Credentials.from_authorized_user_info(info, SCOPES)
    path = Path(token_path)
    if not path.exists():
        raise FileNotFoundError(
            "YouTube token not found. Create token.json locally or set YOUTUBE_TOKEN_JSON."
        )
    return Credentials.from_authorized_user_file(str(path), SCOPES)


def build_description(description: str, hashtags: tuple[str, ...]) -> str:
    """Build public YouTube copy without exposing internal source metadata."""
    cleaned_tags = [tag if tag.startswith("#") else f"#{tag}" for tag in hashtags]
    sections = [description.strip()]
    if cleaned_tags:
        sections.append(" ".join(cleaned_tags))
    return "\n\n".join(section for section in sections if section)


def upload_video(
    video_path: str | Path,
    thumbnail_path: str | Path,
    title: str,
    description: str,
    tags: tuple[str, ...],
    source_url: str,
    hashtags: tuple[str, ...] = (),
    privacy: str = "private",
    category_id: str = "25",
    made_for_kids: bool = False,
    token_path: str | Path = "token.json",
) -> str:
    """Upload a private video while keeping source_url internal."""
    credentials = _load_credentials(token_path)
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title[:100],
                "description": build_description(description, hashtags)[:5000],
                "tags": list(tags)[:15],
                "categoryId": str(category_id),
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": made_for_kids,
            },
        },
        media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = str(response["id"])

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_path)),
        ).execute()
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        if status in {401, 403}:
            LOGGER.warning(
                "Video uploaded, but the custom thumbnail could not be set due to channel permissions | "
                "video_id=%s | status=%s",
                video_id,
                status,
            )
        else:
            raise

    return video_id
