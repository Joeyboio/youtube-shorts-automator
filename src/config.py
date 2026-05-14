"""Central configuration using pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- OpenAI (for script generation) ---
    openai_api_key: str = Field(default="", description="OpenAI API key for GPT script generation")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")

    # --- Reddit (optional, for fetching real AITA posts) ---
    reddit_client_id: str = Field(default="", description="Reddit app client ID")
    reddit_client_secret: str = Field(default="", description="Reddit app client secret")
    reddit_user_agent: str = Field(
        default="youtube-shorts-automator/0.1", description="Reddit API user agent"
    )
    subreddits: list[str] = Field(
        default=["AmItheAsshole", "tifu", "pettyrevenge", "MaliciousCompliance"],
        description="Subreddits to pull stories from",
    )

    # --- YouTube ---
    youtube_client_secrets_file: str = Field(
        default="config/client_secrets.json",
        description="Path to YouTube OAuth client secrets JSON",
    )
    youtube_token_file: str = Field(
        default="config/youtube_token.json",
        description="Path to cached YouTube OAuth token",
    )
    youtube_category_id: str = Field(default="22", description="YouTube video category (22=People)")
    default_tags: list[str] = Field(
        default=["shorts", "reddit", "aita", "storytime", "redditstories"],
        description="Default tags for uploaded videos",
    )

    # --- TTS settings ---
    tts_voice: str = Field(
        default="en-US-GuyNeural",
        description="Edge TTS voice (e.g. en-US-GuyNeural, en-US-ChristopherNeural)",
    )
    tts_rate: str = Field(
        default="+10%", description="Edge TTS speaking rate (e.g. -5%, +10%)"
    )

    # --- Video settings ---
    video_width: int = Field(default=1080, description="Video width (portrait for Shorts)")
    video_height: int = Field(default=1920, description="Video height (portrait for Shorts)")
    font_size: int = Field(default=72, description="Subtitle font size")
    font_color: str = Field(default="white", description="Subtitle font color")
    max_video_duration: int = Field(default=59, description="Max Shorts duration in seconds")
    background_music_volume: float = Field(
        default=0.08, description="Background music volume (0.0 to 1.0)"
    )

    # --- Background videos ---
    background_videos_dir: str = Field(
        default="assets/backgrounds",
        description="Directory containing background .mp4 files",
    )
    background_video_urls: list[str] = Field(
        default=[],
        description="URLs of background videos to download (satisfying clips, etc.)",
    )

    # --- Scheduler ---
    videos_per_day: int = Field(default=3, description="Number of videos to produce per day")
    schedule_interval_hours: float = Field(
        default=8.0, description="Hours between each pipeline run"
    )

    # --- Paths ---
    output_dir: str = Field(default="output", description="Base output directory")

    def get_output_dir(self, subdir: str = "") -> Path:
        base = Path(self.output_dir)
        if subdir:
            base = base / subdir
        base.mkdir(parents=True, exist_ok=True)
        return base

    def get_backgrounds_dir(self) -> Path:
        p = Path(self.background_videos_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


def get_settings() -> Settings:
    return Settings()
