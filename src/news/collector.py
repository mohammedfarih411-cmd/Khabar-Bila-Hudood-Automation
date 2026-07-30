from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
from typing import Iterable

import feedparser
import requests

from ..models import Article

LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (compatible; KhabarBilaHudoodBot/1.0; "
    "+https://github.com/mohammedfarih411-cmd/Khabar-Bila-Hudood-Automation)"
)


def _published(entry: object) -> datetime:
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not raw:
        return datetime.now(timezone.utc)
    try:
        value = parsedate_to_datetime(raw)
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc)


def _fetch_feed(url: str):
    """Fetch a feed with a hard timeout so one unreachable source cannot hang the run."""
    try:
        response = requests.get(
            url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.warning("RSS source unreachable, skipping | url=%s | error=%s", url, exc)
        return None
    return feedparser.parse(response.content)


def collect_rss(urls: Iterable[str], max_articles: int = 30) -> list[Article]:
    articles: list[Article] = []
    for url in urls:
        feed = _fetch_feed(url)
        if feed is None:
            continue
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
