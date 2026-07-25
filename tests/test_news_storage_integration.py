from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.news.collector import Article, _apply_news_history


def make_article(url: str) -> Article:
    return Article(
        title="Storage integration article",
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


class NewsStorageIntegrationTests(unittest.TestCase):
    def test_returns_articles_when_storage_settings_are_missing(self) -> None:
        article = make_article("https://example.com/news/missing-settings")

        result = _apply_news_history(
            [article],
            {"news": {}},
        )

        self.assertEqual(result, [article])

    def test_filters_article_already_accepted(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "news.db"
            article = make_article(
                "https://example.com/news/duplicate"
            )

            config = {
                "news": {
                    "duplicate_days": 30,
                },
                "database": {
                    "path": str(database_path),
                },
            }

            first_result = _apply_news_history(
                [article],
                config,
            )

            second_result = _apply_news_history(
                [article],
                config,
            )

            self.assertEqual(first_result, [article])
            self.assertEqual(second_result, [])


if __name__ == "__main__":
    unittest.main()
