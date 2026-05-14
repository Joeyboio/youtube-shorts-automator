"""Create YouTube Shorts videos by combining background footage, voiceover, and subtitles."""

from __future__ import annotations

import logging
import random
import textwrap
from pathlib import Path

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ColorClip, TextClip

from src.config import Settings
from src.script_generator.generator import Script

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
        final = final.with_audio(audio_clip.subclipped(0, duration))
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

    def _create_gradient_background(self, duration: float) -> ColorClip:
        """Create a simple dark background as fallback."""
        return ColorClip(
            size=(self.width, self.height),
            color=(15, 15, 25),
            duration=duration,
        )

    def _create_subtitle_overlay(self, text: str, duration: float) -> CompositeVideoClip:
        """Create animated subtitle overlay that shows text in chunks."""
        words = text.split()
        words_per_chunk = 6
        chunks: list[str] = []

        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i : i + words_per_chunk])
            chunks.append(chunk)

        if not chunks:
            chunks = [text]

        chunk_duration = duration / len(chunks)
        subtitle_clips = []

        for i, chunk in enumerate(chunks):
            wrapped = textwrap.fill(chunk, width=20)
            try:
                txt_clip = (
                    TextClip(
                        text=wrapped,
                        font_size=self.settings.font_size,
                        color=self.settings.font_color,
                        font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        stroke_color="black",
                        stroke_width=3,
                        size=(self.width - 100, None),
                        method="caption",
                    )
                    .with_position("center")
                    .with_start(i * chunk_duration)
                    .with_duration(chunk_duration)
                )
                subtitle_clips.append(txt_clip)
            except Exception as e:
                logger.warning("Failed to create subtitle chunk %d: %s", i, e)

        if not subtitle_clips:
            transparent = ColorClip(
                size=(self.width, self.height), color=(0, 0, 0, 0), duration=duration
            )
            return CompositeVideoClip([transparent], size=(self.width, self.height))

        return CompositeVideoClip(
            subtitle_clips,
            size=(self.width, self.height),
        ).with_duration(duration)
