from __future__ import annotations

from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def create_thumbnail(
    title: str,
    destination: str | Path,
    width: int = 1280,
    height: int = 720,
    brand: str = "خبر بلا حدود",
) -> Path:
    """Create a clean, high-contrast news thumbnail without external assets."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (width, height), (15, 24, 40))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, int(height * 0.16)), fill=(175, 24, 35))
    draw.rectangle((0, int(height * 0.82), width, height), fill=(8, 14, 25))
    draw.polygon(
        [(int(width * 0.68), 0), (width, 0), (width, height), (int(width * 0.52), height)],
        fill=(28, 48, 75),
    )

    brand_font = _font(max(30, int(height * 0.065)))
    title_font = _font(max(52, int(height * 0.105)))
    source_font = _font(max(24, int(height * 0.042)))

    draw.text((width - 45, 32), brand, font=brand_font, fill="white", anchor="ra", direction="rtl")
    normalized = " ".join(title.split())
    lines = textwrap.wrap(normalized, width=22)[:3] or ["خبر عاجل"]
    y = int(height * 0.25)
    for line in lines:
        draw.text(
            (width - 55, y),
            line,
            font=title_font,
            fill=(255, 210, 55),
            stroke_width=4,
            stroke_fill=(0, 0, 0),
            anchor="ra",
            direction="rtl",
        )
        y += int(height * 0.14)

    draw.text(
        (45, height - 55),
        "NEWS • VERIFIED",
        font=source_font,
        fill="white",
        anchor="ls",
    )
    image.save(path, quality=94, optimize=True)
    return path
