from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from itertools import zip_longest
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


def _article_from_entry(source: str, entry: object) -> Article | None:
    title = str(getattr(entry, "title", "")).strip()
    link = str(getattr(entry, "link", "")).strip()
    if not title or not link:
        return None
    return Article(
        title=title,
        url=link,
        source=str(source),
        summary=str(getattr(entry, "summary", "")).strip(),
        published_at=_published(entry),
    )


def collect_rss(urls: Iterable[str], max_articles: int = 30) -> list[Article]:
    """Collect articles from every configured RSS source, round-robin style.

    Sources are drained in turn (one entry per source per round) rather than
    fully draining the first sources before moving on. This guarantees a
    smaller or later-listed source (e.g. a dedicated Italy feed) still gets a
    fair share of the max_articles budget instead of being starved out by
    larger feeds listed earlier.
    """
    sources: list[str] = []
    entries_per_source: list[list[object]] = []
    for url in urls:
        feed = _fetch_feed(url)
        if feed is None:
            continue
        sources.append(str(getattr(feed.feed, "title", None) or url))
        entries_per_source.append(list(getattr(feed, "entries", [])))

    articles: list[Article] = []
    for round_entries in zip_longest(*entries_per_source):
        for source, entry in zip(sources, round_entries):
            if entry is None:
                continue
            article = _article_from_entry(source, entry)
            if article is None:
                continue
            articles.append(article)
            if len(articles) >= max_articles:
                return articles
    return articles
