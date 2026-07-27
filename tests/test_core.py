from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.database.store import NewsStore
from src.models import Article
from src.news.ranking import classify_and_score, rank_articles


class RankingTests(unittest.TestCase):
    def article(self, title: str, summary: str = "") -> Article:
        return Article(
            title=title,
            url=f"https://example.com/{abs(hash(title))}",
            source="Example",
            summary=summary,
            published_at=datetime.now(timezone.utc),
        )

    def test_italy_has_highest_priority(self) -> None:
        italy = self.article("Italy announces a new migration measure")
        world = self.article("Global summit opens today")
        ranked = rank_articles([world, italy])
        self.assertEqual(ranked[0].category, "italy")

    def test_excluded_economy_story_is_removed(self) -> None:
        article = self.article("Global economy and stocks update")
        self.assertEqual(classify_and_score(article).category, "excluded")
        self.assertEqual(rank_articles([article]), [])

    def test_fingerprint_is_stable_for_spacing_and_case(self) -> None:
        first = self.article("Breaking   News")
        second = self.article("breaking news")
        self.assertEqual(first.fingerprint, second.fingerprint)


class StoreTests(unittest.TestCase):
    def test_save_and_detect_duplicate(self) -> None:
        article = Article("Test story", "https://example.com/test", "Example")
        with TemporaryDirectory() as directory:
            store = NewsStore(Path(directory) / "news.db")
            self.assertFalse(store.contains(article))
            store.save(article, "selected")
            self.assertTrue(store.contains(article))


if __name__ == "__main__":
    unittest.main()
