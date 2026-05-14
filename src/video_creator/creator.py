"""Create YouTube Shorts videos by combining background footage, voiceover, and subtitles."""

from __future__ import annotations

import logging
import random
import textwrap
from pathlib import Path

from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ColorClip
from PIL import Image, ImageDraw, ImageFont

from src.config import Settings
from src.script_generator.generator import Script

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def _find_font(bold: bool = False) -> str:
    """Find the best available font."""
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            return path
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


logger = logging.getLogger(__name__)


class VideoCreator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.width = settings.video_width
        self.height = settings.video_height

    def create(
        self,
        script: Script,
        audio_path: str | Path,
        output_path: str | Path,
    ) -> Path:
        """Create a short-form video with background, voiceover, and subtitles.

        Args:
            script: The script (used for subtitles and title).
            audio_path: Path to the voiceover audio file.
            output_path: Where to save the final video.

        Returns:
            Path to the generated video file.
        """
        audio_path = Path(audio_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Creating video: %s", output_path.name)

        audio_clip = AudioFileClip(str(audio_path))
        duration = min(audio_clip.duration, self.settings.max_video_duration)

        background = self._get_background(duration)
        subtitle_overlay = self._create_subtitle_overlay(script.text, duration)

        final = CompositeVideoClip(
            [background, subtitle_overlay],
            size=(self.width, self.height),
        )

        voiceover = audio_clip.subclipped(0, duration)
        mixed_audio = self._mix_with_background_music(voiceover, duration)
        final = final.with_audio(mixed_audio)
        final = final.with_duration(duration)

        final.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None,
        )

        audio_clip.close()
        final.close()

        logger.info("Video created: %s (%.1fs)", output_path, duration)
        return output_path

    def _get_background(self, duration: float) -> VideoFileClip | ColorClip:
        """Get a background clip — either from a video file or a solid color."""
        bg_dir = self.settings.get_backgrounds_dir()
        bg_files = list(bg_dir.glob("*.mp4"))

        if bg_files:
            bg_file = random.choice(bg_files)
            logger.info("Using background: %s", bg_file.name)
            clip = VideoFileClip(str(bg_file))

            if clip.duration < duration:
                loops_needed = int(duration / clip.duration) + 1
                from moviepy.video.compositing.concatenate import concatenate_videoclips

                clip = concatenate_videoclips([clip] * loops_needed)

            clip = clip.subclipped(0, duration)
            clip = self._resize_to_fill(clip)
            return clip

        logger.warning("No background videos found, using gradient background")
        return self._create_gradient_background(duration)

    def _resize_to_fill(self, clip: VideoFileClip) -> VideoFileClip:
        """Resize and crop video to fill the target dimensions (portrait 9:16)."""
        target_ratio = self.width / self.height
        clip_ratio = clip.w / clip.h

        if clip_ratio > target_ratio:
            clip = clip.resized(height=self.height)
        else:
            clip = clip.resized(width=self.width)

        clip = clip.cropped(
            x_center=clip.w / 2,
            y_center=clip.h / 2,
            width=self.width,
            height=self.height,
        )
        return clip

    def _mix_with_background_music(
        self, voiceover: AudioFileClip, duration: float
    ) -> CompositeAudioClip:
        """Mix voiceover with background music at low volume."""
        music_dir = Path(self.settings.background_videos_dir).parent / "music"
        music_files = list(music_dir.glob("*.wav")) + list(music_dir.glob("*.mp3"))

        if not music_files:
            logger.info("No background music found, using voiceover only")
            return voiceover

        music_file = random.choice(music_files)
        logger.info("Using background music: %s", music_file.name)

        try:
            music = AudioFileClip(str(music_file))
            if music.duration < duration:
                from moviepy.audio.AudioClip import concatenate_audioclips

                loops = int(duration / music.duration) + 1
                music = concatenate_audioclips([music] * loops)

            music = music.subclipped(0, duration)
            music = music.with_volume_scaled(self.settings.background_music_volume)

            return CompositeAudioClip([voiceover, music])
        except Exception as e:
            logger.warning("Failed to add background music: %s", e)
            return voiceover

    def _create_gradient_background(self, duration: float) -> ColorClip:
        """Create a simple dark background as fallback."""
        return ColorClip(
            size=(self.width, self.height),
            color=(15, 15, 25),
            duration=duration,
        )

    def _render_card_image(self, text: str) -> str:
        """Render text on a semi-transparent white card (like the example video style)."""
        import tempfile

        font_path = _find_font(bold=False)
        font_size = self.settings.font_size
        font = ImageFont.truetype(font_path, font_size)

        card_width = self.width - 60
        wrapped = textwrap.fill(text, width=42)

        dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.multiline_textbbox((0, 0), wrapped, font=font)
        text_h = bbox[3] - bbox[1]

        padding_x = 30
        padding_y = 25
        card_height = text_h + padding_y * 2

        img = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle(
            [(0, 0), (card_width - 1, card_height - 1)],
            radius=16,
            fill=(255, 255, 255, 230),
        )

        draw.multiline_text(
            (padding_x, padding_y),
            wrapped,
            font=font,
            fill=(30, 30, 30, 255),
            align="left",
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        return tmp.name

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentence groups for progressive reveal."""
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)
        groups: list[str] = []
        current = ""
        for s in sentences:
            candidate = (current + " " + s).strip() if current else s
            if len(candidate) > 200 and current:
                groups.append(current)
                current = s
            else:
                current = candidate
        if current:
            groups.append(current)
        return groups if groups else [text]

    def _create_subtitle_overlay(self, text: str, duration: float) -> CompositeVideoClip:
        """Create progressive text card overlay matching the example video style."""
        sentences = self._split_into_sentences(text)
        accumulated = ""
        cards: list[tuple[str, float, float]] = []
        chunk_duration = duration / len(sentences)

        for i, sentence in enumerate(sentences):
            accumulated = (accumulated + " " + sentence).strip() if accumulated else sentence
            start = i * chunk_duration
            dur = chunk_duration
            cards.append((accumulated, start, dur))

        subtitle_clips = []
        card_y = int(self.height * 0.18)

        for accumulated_text, start, dur in cards:
            try:
                img_path = self._render_card_image(accumulated_text)
                from moviepy import ImageClip

                img_clip = (
                    ImageClip(img_path)
                    .with_position(("center", card_y))
                    .with_start(start)
                    .with_duration(dur)
                )
                subtitle_clips.append(img_clip)
            except Exception as e:
                logger.warning("Failed to create subtitle card: %s", e)

        if not subtitle_clips:
            transparent = ColorClip(
                size=(self.width, self.height), color=(0, 0, 0, 0), duration=duration
            )
            return CompositeVideoClip([transparent], size=(self.width, self.height))

        return CompositeVideoClip(
            subtitle_clips,
            size=(self.width, self.height),
        ).with_duration(duration)
