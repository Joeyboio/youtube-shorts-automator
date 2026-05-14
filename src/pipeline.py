"""Full pipeline orchestrator: script -> voiceover -> video -> upload."""

from __future__ import annotations

import logging
import time

from src.config import Settings
from src.script_generator import ScriptGenerator
from src.uploader import YouTubeUploader
from src.video_creator import VideoCreator
from src.voiceover import VoiceoverGenerator

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.script_gen = ScriptGenerator(settings)
        self.voiceover_gen = VoiceoverGenerator(settings)
        self.video_creator = VideoCreator(settings)
        self.uploader = YouTubeUploader(settings)

    def run(self, upload: bool = True, privacy: str = "public") -> dict:
        """Execute the full pipeline.

        Args:
            upload: Whether to upload to YouTube (set False for local testing).
            privacy: YouTube privacy status for the upload.

        Returns:
            dict with paths and metadata for the generated content.
        """
        timestamp = int(time.time())
        result: dict = {"timestamp": timestamp}

        # Step 1: Generate script
        logger.info("=" * 60)
        logger.info("STEP 1: Generating script...")
        script = self.script_gen.generate()
        logger.info("Script: %s (%d words)", script.title, len(script.text.split()))

        script_path = self.settings.get_output_dir("scripts") / f"script_{timestamp}.json"
        self.script_gen.save_script(script, str(script_path))
        result["script_path"] = str(script_path)
        result["title"] = script.title

        # Step 2: Generate voiceover
        logger.info("STEP 2: Generating voiceover...")
        audio_path = self.settings.get_output_dir("audio") / f"voiceover_{timestamp}.mp3"
        self.voiceover_gen.generate(script, audio_path)
        result["audio_path"] = str(audio_path)

        # Step 3: Create video
        logger.info("STEP 3: Creating video...")
        video_path = self.settings.get_output_dir("videos") / f"short_{timestamp}.mp4"
        self.video_creator.create(script, audio_path, video_path)
        result["video_path"] = str(video_path)

        # Step 4: Upload to YouTube
        if upload:
            logger.info("STEP 4: Uploading to YouTube...")
            try:
                video_id = self.uploader.upload(video_path, script, privacy=privacy)
                result["video_id"] = video_id
                result["url"] = f"https://youtube.com/shorts/{video_id}"
                logger.info("Uploaded: %s", result["url"])
            except Exception as e:
                logger.error("Upload failed: %s", e)
                logger.info("Video saved locally at: %s", video_path)
                result["upload_error"] = str(e)
        else:
            logger.info("STEP 4: Skipping upload (upload=False)")

        logger.info("=" * 60)
        logger.info("Pipeline complete! Results: %s", result)
        return result
