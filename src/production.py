from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re

from .ai.truthguard import EditorialPackage
from .media.thumbnail import create_thumbnail
from .media.tts import build_narrator
from .media.video import create_video
from .models import Article
from .youtube.publisher import upload_video


@dataclass(slots=True)
class ProductionResult:
    article: Article
    output_dir: Path
    audio_path: Path
    thumbnail_path: Path
    video_path: Path
    youtube_video_id: str | None = None


def _slug(value: str) -> str:
    normalized = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE).strip("-")
    return normalized[:60] or "news-video"


def produce_and_publish(
    article: Article,
    package: EditorialPackage,
    config: dict,
    logger: logging.Logger,
) -> ProductionResult:
    if not package.approved:
        raise ValueError("Cannot produce a rejected editorial package")

    production = config.get("production", {})
    root = Path(production.get("output_dir", "output")) / _slug(package.title_ar)
    root.mkdir(parents=True, exist_ok=True)
    audio_path = root / "narration.mp3"
    thumbnail_path = root / "thumbnail.jpg"
    video_path = root / "video.mp4"

    narrator = build_narrator(config)
    narrator.synthesize(package.script_ar, audio_path)

    thumbnail_config = config.get("thumbnail", {})
    create_thumbnail(
        package.title_ar,
        thumbnail_path,
        width=int(thumbnail_config.get("width", 1280)),
        height=int(thumbnail_config.get("height", 720)),
        brand=str(thumbnail_config.get("brand", "خبر بلا حدود")),
    )

    width, height = (int(part) for part in str(config["video"]["resolution"]).split("x", 1))
    create_video(
        thumbnail_path,
        audio_path,
        video_path,
        fps=int(config["video"].get("fps", 30)),
        resolution=(width, height),
    )

    video_id: str | None = None
    youtube_config = config.get("youtube", {})
    if bool(youtube_config.get("upload_enabled", False)):
        video_id = upload_video(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=package.title_ar,
            description=package.description_ar,
            tags=package.tags,
            hashtags=package.hashtags,
            source_url=article.url,
            privacy=str(youtube_config.get("privacy", "private")),
            category_id=str(youtube_config.get("category", 25)),
            made_for_kids=bool(youtube_config.get("made_for_kids", False)),
            token_path=str(youtube_config.get("token_path", "token.json")),
        )
        logger.info("Uploaded private YouTube video | video_id=%s", video_id)
    else:
        logger.info("Media generated; YouTube upload is disabled | path=%s", video_path)

    return ProductionResult(article, root, audio_path, thumbnail_path, video_path, video_id)
