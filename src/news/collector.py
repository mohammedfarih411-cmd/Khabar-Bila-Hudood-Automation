from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable

import feedparser

from ..models import Article


def _published(entry: object) -> datetime:
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not raw:
        return datetime.now(timezone.utc)
    try:
        value = parsedate_to_datetime(raw)
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc)


def collect_rss(urls: Iterable[str], max_articles: int = 30) -> list[Article]:
    articles: list[Article] = []
    for url in urls:
        feed = feedparser.parse(url)
        source = getattr(feed.feed, "title", None) or url
        for entry in getattr(feed, "entries", []):
            title = str(getattr(entry, "title", "")).strip()
            link = str(getattr(entry, "link", "")).strip()
            if not title or not link:
                continue
            articles.append(
                Article(
                    title=title,
                    url=link,
                    source=str(source),
                    summary=str(getattr(entry, "summary", "")).strip(),
                    published_at=_published(entry),
                )
            )
            if len(articles) >= max_articles:
                return articles
    return articles
