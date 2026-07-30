from __future__ import annotations

from pathlib import Path

from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


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


def create_bulletin_video(
    segments: list[tuple[str | Path, str | Path]],
    destination: str | Path,
    fps: int = 30,
    resolution: tuple[int, int] = (1920, 1080),
) -> Path:
    """Render one Full HD video that stitches multiple news segments back to back.

    Each segment pairs a still image (a story's thumbnail/slide) with the
    narration audio for that story. Segments play in order, each for exactly
    as long as its own narration lasts.
    """
    if not segments:
        raise ValueError("At least one segment is required to build a bulletin video")

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    audio_clips = []
    try:
        for image_path, audio_path in segments:
            audio = AudioFileClip(str(audio_path))
            audio_clips.append(audio)
            clip = (
                ImageClip(str(image_path))
                .resized(new_size=resolution)
                .with_duration(audio.duration)
                .with_audio(audio)
            )
            clips.append(clip)

        final = concatenate_videoclips(clips, method="compose")
        try:
            final.write_videofile(
                str(output),
                fps=fps,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=2,
                logger=None,
            )
        finally:
            final.close()
    finally:
        for clip in clips:
            clip.close()
        for audio in audio_clips:
            audio.close()
    return output
