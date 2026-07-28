from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from PIL import Image

from src.media.thumbnail import create_thumbnail


class ThumbnailDesignTests(unittest.TestCase):
    """Verify that the thumbnail renderer produces the branded layout."""

    def test_thumbnail_has_expected_size_and_accent_colors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "thumbnail.jpg"
            result = create_thumbnail(
                "ترامب يحذر إيران قبل لقاء البيت الأبيض",
                destination,
            )

            self.assertEqual(result, destination)
            self.assertTrue(destination.exists())

            with Image.open(destination) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertEqual(image.mode, "RGB")

                header = image.getpixel((100, 40))
                accent = image.getpixel((100, 112))
                self.assertGreater(header[0], header[1] * 3)
                self.assertGreater(accent[0], 180)
                self.assertGreater(accent[1], 100)


if __name__ == "__main__":
    unittest.main()
