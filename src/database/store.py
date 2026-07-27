from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from ..models import Article


class NewsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    fingerprint TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def contains(self, article: Article) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT 1 FROM articles WHERE fingerprint = ?",
                (article.fingerprint,),
            ).fetchone()
        return row is not None

    def save(self, article: Article, status: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO articles
                (fingerprint, title, url, source, category, status, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.fingerprint,
                    article.title,
                    article.url,
                    article.source,
                    article.category,
                    status,
                    article.score,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.commit()
