"""Text-to-speech voiceover generation using gTTS."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from gtts import gTTS

from src.config import Settings
from src.script_generator.generator import Script

logger = logging.getLogger(__name__)


class VoiceoverGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, script: Script, output_path: str | Path) -> Path:
        """Generate an MP3 voiceover from a script using gTTS.

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

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))

        logger.info("Voiceover saved: %s", output_path)
        return output_path

    def _clean_text(self, text: str) -> str:
        """Clean script text for TTS — remove hashtags, markdown, etc."""
        text = re.sub(r"#\w+", "", text)
        text = re.sub(r"\*+", "", text)
        text = re.sub(r"_+", "", text)
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def estimate_duration(self, script: Script) -> float:
        """Estimate audio duration in seconds (rough: ~2.5 words/sec for gTTS)."""
        word_count = len(script.text.split())
        return word_count / 2.5
