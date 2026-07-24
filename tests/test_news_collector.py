from collections import Counter
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from src.news import Article, collect_news


def make_article(
    source: str,
    index: int,
    *,
    priority: int = 0,
    url: str | None = None,
) -> Article:
    return Article(
        title=f"{source} article {index}",
        url=url or f"https://example.com/{source}/{index}",
        source=source,
        summary="Test summary",
        published_at=datetime(
            2026,
            7,
            24,
            12,
            index % 60,
            tzinfo=timezone.utc,
        ),
        priority_score=priority,
    )


class NewsCollectorTests(unittest.TestCase):
    def test_rejects_missing_rss_sources(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "No RSS sources configured",
        ):
            collect_news(
                {
                    "news": {},
                    "sources": {},
                }
            )

    @patch("src.news.collector._collect_feed")
    def test_balances_sources_and_respects_limit(
        self,
        mock_collect_feed,
    ) -> None:
        def fake_collect_feed(feed_url: str, **kwargs):
            source = {
                "feed-a": "BBC News",
                "feed-b": "Al Jazeera",
                "feed-c": "Deutsche Welle",
            }[feed_url]

            return [
                make_article(source, index)
                for index in range(12)
            ]

        mock_collect_feed.side_effect = fake_collect_feed

        articles = collect_news(
            {
                "news": {
                    "max_articles": 30,
                    "priority": [],
                    "exclude_categories": [],
                },
                "sources": {
                    "rss": [
                        "feed-a",
                        "feed-b",
                        "feed-c",
                    ]
                },
            }
        )

        counts = Counter(
            article.source
            for article in articles
        )

        self.assertEqual(len(articles), 30)
        self.assertEqual(counts["BBC News"], 10)
        self.assertEqual(counts["Al Jazeera"], 10)
        self.assertEqual(counts["Deutsche Welle"], 10)

    @patch("src.news.collector._collect_feed")
    def test_removes_duplicate_urls(
        self,
        mock_collect_feed,
    ) -> None:
        duplicate_url = "https://example.com/shared"

        mock_collect_feed.return_value = [
            make_article(
                "BBC News",
                1,
                url=duplicate_url,
            ),
            make_article(
                "BBC News",
                2,
                url=duplicate_url,
            ),
        ]

        articles = collect_news(
            {
                "news": {
                    "max_articles": 30,
                    "priority": [],
                    "exclude_categories": [],
                },
                "sources": {
                    "rss": ["feed-a"]
                },
            }
        )

        self.assertEqual(len(articles), 1)

    @patch("src.news.collector._collect_feed")
    def test_priority_is_preserved_within_source(
        self,
        mock_collect_feed,
    ) -> None:
        mock_collect_feed.return_value = [
            make_article(
                "BBC News",
                1,
                priority=0,
            ),
            make_article(
                "BBC News",
                2,
                priority=2,
            ),
        ]

        articles = collect_news(
            {
                "news": {
                    "max_articles": 2,
                    "priority": [],
                    "exclude_categories": [],
                },
                "sources": {
                    "rss": ["feed-a"]
                },
            }
        )

        self.assertEqual(
            articles[0].priority_score,
            2,
        )


if __name__ == "__main__":
    unittest.main()
