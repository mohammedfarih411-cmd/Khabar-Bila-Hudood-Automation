from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.ai.truthguard import EditorialPackage
from src.models import Article
from src.pipeline import run_pipeline


class FakeVerifier:
    def verify(self, article: Article) -> EditorialPackage:
        if "rumor" in article.title.casefold():
            return EditorialPackage(False, 0.35, "المادة غير مؤكدة")
        return EditorialPackage(
            True,
            0.94,
            "المادة واضحة وقابلة للنشر",
            title_ar="إيطاليا تعلن إجراءً جديدًا للهجرة",
            script_ar="نص خبري عربي محايد.",
            description_ar="وصف موجز للفيديو.",
            tags=("إيطاليا", "الهجرة"),
            hashtags=("#إيطاليا", "#الهجرة"),
        )


class TruthGuardPipelineTests(unittest.TestCase):
    def test_pipeline_skips_rejected_story_and_selects_verified_story(self) -> None:
        now = datetime.now(timezone.utc)
        stories = [
            Article("Italy migration rumor spreads", "https://example.com/rumor", "Example", published_at=now),
            Article("Italy announces migration measure", "https://example.com/verified", "Example", published_at=now),
        ]
        with TemporaryDirectory() as directory:
            config = {
                "news": {"max_articles": 30, "publish_per_run": 1},
                "sources": {"rss": ["https://example.com/rss"]},
                "database": {"path": str(Path(directory) / "news.db")},
            }
            with patch("src.pipeline.collect_rss", return_value=stories):
                result = run_pipeline(config, logging.getLogger("test"), verifier=FakeVerifier())

        self.assertEqual(len(result.selected), 1)
        self.assertEqual(result.selected[0].url, "https://example.com/verified")
        package = result.editorial[result.selected[0].fingerprint]
        self.assertTrue(package.approved)
        self.assertEqual(package.title_ar, "إيطاليا تعلن إجراءً جديدًا للهجرة")


if __name__ == "__main__":
    unittest.main()
