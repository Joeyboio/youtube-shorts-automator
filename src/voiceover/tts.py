"""Text-to-speech voiceover generation using edge-tts (natural) or gTTS (fallback)."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from src.config import Settings
from src.script_generator.generator import Script

logger = logging.getLogger(__name__)


class VoiceoverGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, script: Script, output_path: str | Path) -> Path:
        """Generate an MP3 voiceover from a script.

        Uses edge-tts for natural-sounding speech, falls back to gTTS.

        Args:
            script: The script to convert to speech.
            output_path: Where to save the audio file.

        Returns:
            Path to the generated audio file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        text = self._clean_text(script.text)

        if not text.strip():
            raise ValueError("Script text is empty, cannot generate voiceover")

        logger.info("Generating voiceover (%d chars) -> %s", len(text), output_path)

        try:
            self._generate_edge_tts(text, output_path)
        except Exception as e:
            logger.warning("edge-tts failed (%s), falling back to gTTS", e)
            self._generate_gtts(text, output_path)

        logger.info("Voiceover saved: %s", output_path)
        return output_path

    def _generate_edge_tts(self, text: str, output_path: Path) -> None:
        """Generate voiceover using Microsoft Edge TTS (free, natural-sounding)."""
        import edge_tts

        voice = self.settings.tts_voice
        rate = self.settings.tts_rate
        pitch = self.settings.tts_pitch

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(str(output_path))

        asyncio.run(_run())

    def _generate_gtts(self, text: str, output_path: Path) -> None:
        """Generate voiceover using gTTS (fallback)."""
        from gtts import gTTS

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))

    def _clean_text(self, text: str) -> str:
        """Clean script text for TTS — remove hashtags, markdown, etc."""
        text = re.sub(r"#\w+", "", text)
        text = re.sub(r"\*+", "", text)
        text = re.sub(r"_+", "", text)
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def estimate_duration(self, script: Script) -> float:
        """Estimate audio duration in seconds (rough: ~2.5 words/sec)."""
        word_count = len(script.text.split())
        return word_count / 2.5
