from __future__ import annotations

import unittest

from src.media.tts import ElevenLabsNarrator
from src.youtube.publisher import build_description


class PublishingTests(unittest.TestCase):
    def test_description_includes_hashtags_without_source(self) -> None:
        result = build_description(
            "وصف الخبر",
            ("إيطاليا", "هجرة"),
        )
        self.assertIn("#إيطاليا", result)
        self.assertIn("#هجرة", result)
        self.assertNotIn("المصدر", result)
        self.assertNotIn("http://", result)
        self.assertNotIn("https://", result)

    def test_narrator_requires_secrets(self) -> None:
        with self.assertRaises(ValueError):
            ElevenLabsNarrator("", "voice")
        with self.assertRaises(ValueError):
            ElevenLabsNarrator("key", "")


if __name__ == "__main__":
    unittest.main()
