"""Create YouTube Shorts videos by combining background footage, voiceover, and subtitles."""

from __future__ import annotations

import logging
import random
import textwrap
from pathlib import Path

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ColorClip
from PIL import Image, ImageDraw, ImageFont

from src.config import Settings
from src.script_generator.generator import Script

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/custom/Impact.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _find_font() -> str:
    """Find the best available bold font."""
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return "DejaVu-Sans-Bold"

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

    def _render_text_image(self, text: str, font_path: str) -> str:
        """Render text to a transparent PNG with outline + shadow for maximum readability."""
        font_size = self.settings.font_size
        font = ImageFont.truetype(font_path, font_size)
        wrapped = textwrap.fill(text.upper(), width=16)
        padding = 40
        outline_width = 6

        dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.multiline_textbbox((0, 0), wrapped, font=font)
        text_w = bbox[2] - bbox[0] + padding * 2 + outline_width * 2
        text_h = bbox[3] - bbox[1] + padding * 2 + outline_width * 2

        img = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x = padding + outline_width
        y = padding + outline_width

        shadow_offset = 4
        draw.multiline_text(
            (x + shadow_offset, y + shadow_offset),
            wrapped,
            font=font,
            fill=(0, 0, 0, 160),
            align="center",
        )

        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.multiline_text(
                        (x + dx, y + dy),
                        wrapped,
                        font=font,
                        fill=(0, 0, 0, 255),
                        align="center",
                    )

        draw.multiline_text(
            (x, y), wrapped, font=font, fill="white", align="center"
        )

        import tempfile

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        return tmp.name

    def _create_subtitle_overlay(self, text: str, duration: float) -> CompositeVideoClip:
        """Create animated subtitle overlay with bold, eye-catching text."""
        font_path = _find_font()
        words = text.split()
        words_per_chunk = 4
        chunks: list[str] = []

        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i : i + words_per_chunk])
            chunks.append(chunk)

        if not chunks:
            chunks = [text]

        chunk_duration = duration / len(chunks)
        subtitle_clips = []

        for i, chunk in enumerate(chunks):
            try:
                img_path = self._render_text_image(chunk, font_path)
                from moviepy import ImageClip

                img_clip = (
                    ImageClip(img_path)
                    .with_position("center")
                    .with_start(i * chunk_duration)
                    .with_duration(chunk_duration)
                )
                subtitle_clips.append(img_clip)
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
