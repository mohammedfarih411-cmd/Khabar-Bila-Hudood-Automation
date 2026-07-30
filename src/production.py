from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re

from .ai.truthguard import EditorialPackage
from .media.thumbnail import create_thumbnail
from .media.tts import build_narrator
from .media.video import create_bulletin_video
from .models import Article
from .youtube.publisher import upload_video


@dataclass(slots=True)
class ProductionResult:
    articles: list[Article]
    output_dir: Path
    audio_paths: list[Path]
    thumbnail_path: Path
    video_path: Path
    youtube_video_id: str | None = None


def _slug(value: str) -> str:
    normalized = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE).strip("-")
    return normalized[:60] or "news-video"


def produce_and_publish(
    articles: list[Article],
    editorial: dict[str, EditorialPackage],
    config: dict,
    logger: logging.Logger,
) -> ProductionResult:
    """Produce and publish a single bulletin video covering several stories."""
    packages = [
        (article, editorial[article.fingerprint])
        for article in articles
        if article.fingerprint in editorial and editorial[article.fingerprint].approved
    ]
    if not packages:
        raise ValueError("No approved editorial package is available for production")

    production = config.get("production", {})
    lead_title = packages[0][1].title_ar
    root = Path(production.get("output_dir", "output")) / _slug(lead_title)
    root.mkdir(parents=True, exist_ok=True)

    narrator = build_narrator(config)
    thumbnail_config = config.get("thumbnail", {})
    width = int(thumbnail_config.get("width", 1280))
    height = int(thumbnail_config.get("height", 720))
    brand = str(thumbnail_config.get("brand", "خبر بلا حدود"))

    segments: list[tuple[Path, Path]] = []
    audio_paths: list[Path] = []
    for index, (article, package) in enumerate(packages, start=1):
        audio_path = root / f"narration_{index}.mp3"
        slide_path = root / f"slide_{index}.jpg"
        narrator.synthesize(package.script_ar, audio_path)
        create_thumbnail(package.title_ar, slide_path, width=width, height=height, brand=brand)
        segments.append((slide_path, audio_path))
        audio_paths.append(audio_path)

    video_path = root / "video.mp4"
    thumbnail_path = root / "thumbnail.jpg"
    cover_title = (
        lead_title
        if len(packages) == 1
        else f"{lead_title} و{len(packages) - 1} أخبار أخرى"
    )
    create_thumbnail(cover_title, thumbnail_path, width=width, height=height, brand=brand)

    video_width, video_height = (
        int(part) for part in str(config["video"]["resolution"]).split("x", 1)
    )
    create_bulletin_video(
        segments,
        video_path,
        fps=int(config["video"].get("fps", 30)),
        resolution=(video_width, video_height),
    )

    combined_description = "\n\n".join(
        f"{i}. {package.description_ar}".strip()
        for i, (_, package) in enumerate(packages, start=1)
    )

    combined_tags: list[str] = []
    seen_tags: set[str] = set()
    for _, package in packages:
        for tag in package.tags:
            key = tag.casefold()
            if key not in seen_tags:
                seen_tags.add(key)
                combined_tags.append(tag)

    combined_hashtags: list[str] = []
    seen_hashtags: set[str] = set()
    for _, package in packages:
        for hashtag in package.hashtags:
            key = hashtag.casefold()
            if key not in seen_hashtags:
                seen_hashtags.add(key)
                combined_hashtags.append(hashtag)

    video_id: str | None = None
    youtube_config = config.get("youtube", {})
    if bool(youtube_config.get("upload_enabled", False)):
        video_id = upload_video(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=cover_title,
            description=combined_description,
            tags=tuple(combined_tags),
            hashtags=tuple(combined_hashtags),
            source_url="; ".join(article.url for article, _ in packages),
            privacy=str(youtube_config.get("privacy", "private")),
            category_id=str(youtube_config.get("category", 25)),
            made_for_kids=bool(youtube_config.get("made_for_kids", False)),
            token_path=str(youtube_config.get("token_path", "token.json")),
        )
        logger.info(
            "Uploaded private YouTube bulletin video | video_id=%s | stories=%d",
            video_id,
            len(packages),
        )
    else:
        logger.info(
            "Bulletin media generated; YouTube upload is disabled | path=%s | stories=%d",
            video_path,
            len(packages),
        )

    return ProductionResult(
        [article for article, _ in packages],
        root,
        audio_paths,
        thumbnail_path,
        video_path,
        video_id,
    )
