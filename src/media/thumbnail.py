from __future__ import annotations

from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw, ImageFont


_HEADLINE_COLORS: Final[tuple[tuple[int, int, int], ...]] = (
    (255, 255, 255),
    (255, 207, 51),
    (255, 116, 42),
)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a bold font that supports Arabic on Windows and GitHub Actions."""
    candidates = (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/tahomabd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _draw_right_aligned_text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    **kwargs: object,
) -> None:
    """Draw RTL text when libraqm exists, with a Windows-safe fallback."""
    try:
        draw.text(position, text, anchor="ra", direction="rtl", **kwargs)
    except (KeyError, ValueError):
        draw.text(position, text, anchor="ra", **kwargs)


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    """Return the rendered width of a text fragment."""
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _balanced_lines(
    draw: ImageDraw.ImageDraw,
    title: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    max_lines: int = 3,
) -> list[str]:
    """Split a headline into balanced, mobile-readable lines."""
    words = title.split()
    if not words:
        return ["خبر جديد"]

    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join((*current, word))
        if current and _text_width(draw, candidate, font) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        lines.append(" ".join(current))

    if len(lines) <= max_lines:
        return lines

    visible = lines[: max_lines - 1]
    visible.append(" ".join(lines[max_lines - 1 :]))
    return visible


def _fit_headline(
    draw: ImageDraw.ImageDraw,
    title: str,
    width: int,
    height: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str]]:
    """Choose the largest headline size that fits three lines."""
    max_width = int(width * 0.82)
    for size in range(int(height * 0.13), int(height * 0.07), -2):
        font = _font(size)
        lines = _balanced_lines(draw, title, font, max_width)
        if len(lines) <= 3 and all(
            _text_width(draw, line, font) <= max_width for line in lines
        ):
            return font, lines

    fallback = _font(max(48, int(height * 0.07)))
    return fallback, _balanced_lines(draw, title, fallback, max_width)


def create_thumbnail(
    title: str,
    destination: str | Path,
    width: int = 1280,
    height: int = 720,
    brand: str = "خبر بلا حدود",
) -> Path:
    """Create a polished news thumbnail with a clear three-color hierarchy."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (width, height), (12, 22, 39))
    draw = ImageDraw.Draw(image)

    header_height = int(height * 0.15)
    footer_top = int(height * 0.84)
    draw.rectangle((0, 0, width, header_height), fill=(177, 25, 38))
    draw.rectangle((0, header_height, width, footer_top), fill=(14, 27, 47))
    draw.rectangle((0, footer_top, width, height), fill=(6, 13, 24))
    draw.polygon(
        [
            (int(width * 0.72), 0),
            (width, 0),
            (width, height),
            (int(width * 0.57), height),
        ],
        fill=(30, 53, 82),
    )

    accent_y = header_height
    draw.rectangle(
        (0, accent_y, width, accent_y + max(6, int(height * 0.012))),
        fill=(255, 190, 24),
    )

    brand_font = _font(max(30, int(height * 0.06)))
    footer_font = _font(max(24, int(height * 0.038)))
    headline_font, lines = _fit_headline(draw, " ".join(title.split()), width, height)

    _draw_right_aligned_text(
        draw,
        (width - 45, int(height * 0.035)),
        brand,
        font=brand_font,
        fill=(255, 255, 255),
        stroke_width=1,
        stroke_fill=(100, 10, 20),
    )

    card = (
        int(width * 0.09),
        int(height * 0.22),
        int(width * 0.94),
        int(height * 0.76),
    )
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        card,
        radius=max(18, int(height * 0.035)),
        fill=(3, 10, 21, 105),
        outline=(255, 255, 255, 30),
        width=2,
    )
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    line_height = int(height * 0.145)
    total_height = line_height * len(lines)
    y = int(height * 0.48 - total_height / 2)
    for index, line in enumerate(lines):
        color = _HEADLINE_COLORS[min(index, len(_HEADLINE_COLORS) - 1)]
        _draw_right_aligned_text(
            draw,
            (int(width * 0.90), y),
            line,
            font=headline_font,
            fill=color,
            stroke_width=max(3, int(height * 0.007)),
            stroke_fill=(0, 0, 0),
        )
        if index == len(lines) - 1:
            line_width = _text_width(draw, line, headline_font)
            underline_y = y + int(line_height * 0.78)
            draw.rounded_rectangle(
                (
                    int(width * 0.90) - min(line_width, int(width * 0.72)),
                    underline_y,
                    int(width * 0.90),
                    underline_y + max(6, int(height * 0.012)),
                ),
                radius=5,
                fill=(230, 35, 48),
            )
        y += line_height

    draw.text(
        (45, height - 50),
        "KHABAR • VERIFIED NEWS",
        font=footer_font,
        fill=(220, 228, 239),
        anchor="ls",
    )

    image.save(path, quality=95, optimize=True)
    return path
