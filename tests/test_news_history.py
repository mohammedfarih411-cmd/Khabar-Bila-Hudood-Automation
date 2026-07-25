from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from src.news import Article
from src.storage import filter_recent_duplicates, initialize_database


def make_article(
    *,
    url: str,
    title: str = "Test article",
) -> Article:
    return Article(
        title=title,
        url=url,
        source="Test Source",
        summary="Test summary",
        published_at=datetime(
            2026,
            7,
            25,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        priority_score=0,
    )


class NewsHistoryTests(unittest.TestCase):
    def test_creates_database_and_table(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "data" / "news.db"

            initialize_database(database_path)

            self.assertTrue(database_path.exists())

            with closing(sqlite3.connect(database_path)) as connection:
                table = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    AND name = 'news_history'
                    """
                ).fetchone()

            self.assertIsNotNone(table)

    def test_accepts_new_article(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "news.db"
            article = make_article(url="https://example.com/news/1")

            accepted = filter_recent_duplicates(
                [article],
                database_path=database_path,
                duplicate_days=30,
                now=datetime(
                    2026,
                    7,
                    25,
                    tzinfo=timezone.utc,
                ),
            )

            self.assertEqual(accepted, [article])

    def test_rejects_article_inside_duplicate_window(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "news.db"
            article = make_article(url="https://example.com/news/1")
            first_run = datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            )

            filter_recent_duplicates(
                [article],
                database_path=database_path,
                duplicate_days=30,
                now=first_run,
            )

            accepted = filter_recent_duplicates(
                [article],
                database_path=database_path,
                duplicate_days=30,
                now=first_run + timedelta(days=20),
            )

            self.assertEqual(accepted, [])

    def test_accepts_article_after_duplicate_window(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "news.db"
            article = make_article(url="https://example.com/news/1")
            first_run = datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            )

            filter_recent_duplicates(
                [article],
                database_path=database_path,
                duplicate_days=30,
                now=first_run,
            )

            accepted = filter_recent_duplicates(
                [article],
                database_path=database_path,
                duplicate_days=30,
                now=first_run + timedelta(days=31),
            )

            self.assertEqual(accepted, [article])

    def test_rejects_negative_duplicate_days(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "news.db"

            with self.assertRaisesRegex(
                ValueError,
                "duplicate_days cannot be negative",
            ):
                filter_recent_duplicates(
                    [],
                    database_path=database_path,
                    duplicate_days=-1,
                )


if __name__ == "__main__":
    unittest.main()
