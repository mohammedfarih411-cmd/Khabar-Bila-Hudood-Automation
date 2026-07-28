from __future__ import annotations

import unittest

from src.youtube.publisher import build_description


class YouTubeDescriptionTests(unittest.TestCase):
    """Protect the public YouTube description contract."""

    def test_description_contains_only_editorial_copy_and_hashtags(self) -> None:
        description = build_description(
            "ملخص إخباري مستقل.",
            ("خبر", "#عاجل"),
        )

        self.assertEqual(description, "ملخص إخباري مستقل.\n\n#خبر #عاجل")
        self.assertNotIn("المصدر", description)
        self.assertNotIn("http://", description)
        self.assertNotIn("https://", description)

    def test_description_omits_empty_hashtag_section(self) -> None:
        self.assertEqual(build_description("  نص الخبر  ", ()), "نص الخبر")


if __name__ == "__main__":
    unittest.main()
