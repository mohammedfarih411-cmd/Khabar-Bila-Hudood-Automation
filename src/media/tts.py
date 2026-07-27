from __future__ import annotations

import os
from pathlib import Path

import requests


class ElevenLabsNarrator:
    """Generate Arabic narration with ElevenLabs without storing secrets in Git."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        timeout_seconds: int = 120,
    ) -> None:
        if not api_key.strip():
            raise ValueError("ELEVENLABS_API_KEY is required")
        if not voice_id.strip():
            raise ValueError("ELEVENLABS_VOICE_ID is required")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds

    def synthesize(self, text: str, destination: str | Path) -> Path:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Narration text is empty")

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
            headers={
                "xi-api-key": self.api_key,
                "accept": "audio/mpeg",
                "content-type": "application/json",
            },
            json={
                "text": cleaned,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.75,
                    "style": 0.15,
                    "use_speaker_boost": True,
                },
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        path.write_bytes(response.content)
        return path


def build_narrator(config: dict) -> ElevenLabsNarrator:
    tts_config = config.get("tts", {})
    return ElevenLabsNarrator(
        api_key=os.environ.get("ELEVENLABS_API_KEY", ""),
        voice_id=os.environ.get("ELEVENLABS_VOICE_ID", ""),
        model_id=str(tts_config.get("model", "eleven_multilingual_v2")),
        timeout_seconds=int(tts_config.get("timeout_seconds", 120)),
    )
