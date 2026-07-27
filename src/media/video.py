from __future__ import annotations

from pathlib import Path

from moviepy import AudioFileClip, ImageClip


def create_video(
    image_path: str | Path,
    audio_path: str | Path,
    destination: str | Path,
    fps: int = 30,
    resolution: tuple[int, int] = (1920, 1080),
) -> Path:
    """Render a reliable Full HD news video from narration and a thumbnail."""
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(str(audio_path))
    clip = (
        ImageClip(str(image_path))
        .resized(new_size=resolution)
        .with_duration(audio.duration)
        .with_audio(audio)
    )
    try:
        clip.write_videofile(
            str(output),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2,
            logger=None,
        )
    finally:
        clip.close()
        audio.close()
    return output
