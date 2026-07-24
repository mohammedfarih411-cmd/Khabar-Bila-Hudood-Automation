from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests
from bs4 import BeautifulSoup


LOGGER = logging.getLogger("KhabarBilaHudood.news")
DEFAULT_TIMEOUT_SECONDS = 20


@dataclass(frozen=True, slots=True)
class Article:
    """Normalized article collected from an RSS feed."""

    title: str
    url: str
    source: str
    summary: str
    published_at: datetime | None
    priority_score: int = 0


def _clean_text(value: Any) -> str:
    """Remove HTML and normalize whitespace."""

    if value is None:
        return ""

    plain_text = BeautifulSoup(str(value), "html.parser").get_text(
        separator=" ",
        strip=True,
    )
    return re.sub(r"\s+", " ", plain_text).strip()


def _parse_date(value: Any) -> datetime | None:
    """Convert an RSS date into a UTC datetime when possible."""

    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(str(value))
    except (TypeError, ValueError, OverflowError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _normalized_url(url: str) -> str:
    """Normalize a URL for duplicate detection."""

    if not url:
        return ""

    parts = urlsplit(url.strip())
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            parts.query,
            "",
        )
    )


def _entry_tags(entry: Any) -> str:
    tags = entry.get("tags", [])
    return " ".join(
        _clean_text(tag.get("term", ""))
        for tag in tags
        if isinstance(tag, dict)
    )


def _contains_excluded_category(
    searchable_text: str,
    excluded_categories: list[str],
) -> bool:
    lowered = searchable_text.casefold()
    return any(
        category.casefold() in lowered
        for category in excluded_categories
        if category.strip()
    )


def _priority_score(
    searchable_text: str,
    priority_terms: list[str],
) -> int:
    lowered = searchable_text.casefold()
    return sum(
        1
        for term in priority_terms
        if term.strip() and term.casefold() in lowered
    )


def _collect_feed(
    feed_url: str,
    *,
    priority_terms: list[str],
    excluded_categories: list[str],
    timeout_seconds: int,
) -> list[Article]:
    response = requests.get(
        feed_url,
        timeout=timeout_seconds,
        headers={
            "User-Agent": (
                "Khabar-Bila-Hudood-Automation/1.0 "
                "(RSS news collector)"
            )
        },
    )
    response.raise_for_status()

    parsed_feed = feedparser.parse(response.content)

    if parsed_feed.bozo and not parsed_feed.entries:
        error = getattr(parsed_feed, "bozo_exception", "Invalid RSS feed")
        raise ValueError(f"Unable to parse RSS feed: {error}")

    source = _clean_text(parsed_feed.feed.get("title"))
    if not source:
        source = urlsplit(feed_url).netloc

    articles: list[Article] = []

    for entry in parsed_feed.entries:
        title = _clean_text(entry.get("title"))
        raw_url = entry.get("link") or ""
        url = _normalized_url(str(raw_url).strip())
        summary = _clean_text(
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        if not title or not url:
            continue

        tags = _entry_tags(entry)
        searchable_text = f"{title} {summary} {tags}"

        if _contains_excluded_category(
            searchable_text,
            excluded_categories,
        ):
            continue

        published_at = _parse_date(
            entry.get("published")
            or entry.get("updated")
        )

        articles.append(
            Article(
                title=title,
                url=url,
                source=source,
                summary=summary,
                published_at=published_at,
                priority_score=_priority_score(
                    searchable_text,
                    priority_terms,
                ),
            )
        )

    return articles


def collect_news(
    config: dict[str, Any],
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    logger: logging.Logger | None = None,
) -> list[Article]:
    """Collect, filter, rank and deduplicate RSS articles."""

    active_logger = logger or LOGGER

    news_config = config.get("news", {})
    sources_config = config.get("sources", {})

    feed_urls = sources_config.get("rss", [])
    max_articles = int(news_config.get("max_articles", 30))
    priority_terms = [
        str(term)
        for term in news_config.get("priority", [])
    ]
    excluded_categories = [
        str(term)
        for term in news_config.get("exclude_categories", [])
    ]

    if not isinstance(feed_urls, list) or not feed_urls:
        raise ValueError("No RSS sources configured in config.yaml")

    collected: list[Article] = []

    for feed_url in feed_urls:
        try:
            feed_articles = _collect_feed(
                str(feed_url),
                priority_terms=priority_terms,
                excluded_categories=excluded_categories,
                timeout_seconds=timeout_seconds,
            )
            collected.extend(feed_articles)
            active_logger.info(
                "Collected %d articles from %s",
                len(feed_articles),
                feed_url,
            )
        except (requests.RequestException, ValueError) as exc:
            active_logger.warning(
                "RSS source failed: %s | %s",
                feed_url,
                exc,
            )

    unique_articles: dict[str, Article] = {}

    for article in collected:
        key = article.url.casefold()
        if key not in unique_articles:
            unique_articles[key] = article

    def sort_key(article: Article) -> tuple[int, float]:
        timestamp = (
            article.published_at.timestamp()
            if article.published_at
            else 0.0
        )
        return article.priority_score, timestamp

    ranked_articles = sorted(
        unique_articles.values(),
        key=sort_key,
        reverse=True,
    )

    articles_by_source: dict[str, list[Article]] = {}

    for article in ranked_articles:
        articles_by_source.setdefault(
            article.source,
            [],
        ).append(article)

    balanced_articles: list[Article] = []

    while len(balanced_articles) < max_articles:
        article_added = False

        for source_articles in articles_by_source.values():
            if not source_articles:
                continue

            balanced_articles.append(source_articles.pop(0))
            article_added = True

            if len(balanced_articles) >= max_articles:
                break

        if not article_added:
            break

    return balanced_articles
