from __future__ import annotations

from contextlib import closing

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Iterable, Protocol, TypeVar


class ArticleLike(Protocol):
    """Minimum article fields required by the history store."""

    title: str
    url: str
    source: str
    published_at: datetime | None


ArticleType = TypeVar("ArticleType", bound=ArticleLike)


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _datetime_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None

    return _utc_datetime(value).isoformat()


def _datetime_from_text(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return _utc_datetime(parsed)


def initialize_database(database_path: str | Path) -> Path:
    """Create the database directory and news-history table."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS news_history (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TEXT,
                first_seen_at TEXT NOT NULL,
                last_accepted_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_news_history_last_accepted_at
            ON news_history(last_accepted_at)
            """
        )
        connection.commit()

    return path


def filter_recent_duplicates(
    articles: Iterable[ArticleType],
    *,
    database_path: str | Path,
    duplicate_days: int,
    now: datetime | None = None,
) -> list[ArticleType]:
    """
    Exclude URLs accepted during the configured duplicate window.

    Rejected duplicates do not extend the window. An article may be accepted
    again after the configured number of days has elapsed.
    """

    if duplicate_days < 0:
        raise ValueError("duplicate_days cannot be negative")

    current_time = _utc_datetime(now or datetime.now(timezone.utc))
    cutoff = current_time - timedelta(days=duplicate_days)
    current_time_text = current_time.isoformat()

    path = initialize_database(database_path)
    accepted: list[ArticleType] = []

    with closing(sqlite3.connect(path)) as connection:
        for article in articles:
            url = article.url.strip()

            if not url:
                continue

            existing = connection.execute(
                """
                SELECT last_accepted_at
                FROM news_history
                WHERE url = ?
                """,
                (url,),
            ).fetchone()

            if existing is not None:
                last_accepted_at = _datetime_from_text(existing[0])

                if last_accepted_at >= cutoff:
                    continue

            accepted.append(article)

            connection.execute(
                """
                INSERT INTO news_history (
                    url,
                    title,
                    source,
                    published_at,
                    first_seen_at,
                    last_accepted_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    source = excluded.source,
                    published_at = excluded.published_at,
                    last_accepted_at = excluded.last_accepted_at
                """,
                (
                    url,
                    article.title,
                    article.source,
                    _datetime_to_text(article.published_at),
                    current_time_text,
                    current_time_text,
                ),
            )

        connection.commit()

    return accepted
