"""Pipeline scheduler — runs the full pipeline on a configurable interval."""

from __future__ import annotations

import logging
import signal
import sys
import time

import schedule

from src.config import Settings
from src.pipeline import Pipeline

logger = logging.getLogger(__name__)


class PipelineScheduler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pipeline = Pipeline(settings)
        self._running = True

    def run_once(self) -> None:
        """Run the full pipeline once (generate + voiceover + video + upload)."""
        try:
            self.pipeline.run()
        except Exception as e:
            logger.error("Pipeline run failed: %s", e, exc_info=True)

    def start(self) -> None:
        """Start the scheduler to run the pipeline at configured intervals."""
        interval = self.settings.schedule_interval_hours
        logger.info(
            "Starting scheduler: running every %.1f hours (%d videos/day)",
            interval,
            self.settings.videos_per_day,
        )

        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self.run_once()

        schedule.every(interval).hours.do(self.run_once)

        while self._running:
            schedule.run_pending()
            time.sleep(60)

    def _handle_shutdown(self, signum: int, frame) -> None:
        logger.info("Received signal %d, shutting down...", signum)
        self._running = False
        sys.exit(0)
