from __future__ import annotations

import unittest

from src.youtube.publisher import build_description, build_title


class YouTubeMetadataTests(unittest.TestCase):
    """Protect the public YouTube title and description contracts."""

    def test_title_uses_exactly_first_three_hashtags(self) -> None:
        title = build_title(
            "عنوان الخبر",
            ("خبر", "#عاجل", "العالم", "الرابع"),
        )

        self.assertEqual(title, "عنوان الخبر #خبر #عاجل #العالم")
        self.assertNotIn("#الرابع", title)
        self.assertLessEqual(len(title), 100)

    def test_description_uses_exactly_first_five_hashtags_without_source(self) -> None:
        description = build_description(
            "ملخص إخباري مستقل.",
            ("خبر", "#عاجل", "العالم", "سياسة", "أخبار", "السادس"),
        )

        self.assertEqual(
            description,
            "ملخص إخباري مستقل.\n\n#خبر #عاجل #العالم #سياسة #أخبار",
        )
        self.assertNotIn("#السادس", description)
        self.assertNotIn("المصدر", description)
        self.assertNotIn("http://", description)
        self.assertNotIn("https://", description)

    def test_description_omits_empty_hashtag_section(self) -> None:
        self.assertEqual(build_description("  نص الخبر  ", ()), "نص الخبر")


if __name__ == "__main__":
    unittest.main()
