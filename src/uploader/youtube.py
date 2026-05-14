"""Upload videos to YouTube using the YouTube Data API v3."""

from __future__ import annotations

import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.config import Settings
from src.script_generator.generator import Script

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._service = None

    def authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth 2.0."""
        creds = None
        token_path = Path(self.settings.youtube_token_file)
        secrets_path = Path(self.settings.youtube_client_secrets_file)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing YouTube OAuth token")
            creds.refresh(Request())
        elif not creds or not creds.valid:
            if not secrets_path.exists():
                raise FileNotFoundError(
                    f"YouTube client secrets file not found: {secrets_path}\n"
                    "Download it from Google Cloud Console -> APIs & Services -> Credentials.\n"
                    "See README.md for setup instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

        self._service = build("youtube", "v3", credentials=creds)
        logger.info("YouTube API authenticated successfully")

    @property
    def service(self):
        if self._service is None:
            self.authenticate()
        return self._service

    def upload(
        self,
        video_path: str | Path,
        script: Script,
        privacy: str = "public",
    ) -> str:
        """Upload a video to YouTube.

        Args:
            video_path: Path to the video file.
            script: The script (used for title, description, tags).
            privacy: Privacy status — "public", "unlisted", or "private".

        Returns:
            The YouTube video ID.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        title = script.title[:100]
        hashtag_str = " ".join(script.hashtags)
        description = (
            f"{script.text[:200]}...\n\n"
            f"{hashtag_str}\n\n"
            "---\n"
            "Subscribe for more Reddit stories! 🔥\n"
        )
        if script.source and script.source != "ai-generated":
            description += f"\nOriginal post: {script.source}"

        tags = list(set(self.settings.default_tags + [h.lstrip("#") for h in script.hashtags]))

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags[:30],
                "categoryId": self.settings.youtube_category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,
        )

        logger.info("Uploading video: %s (%s)", title, video_path.name)

        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("Upload progress: %d%%", int(status.progress() * 100))

        video_id = response["id"]
        logger.info(
            "Upload complete! Video ID: %s -> https://youtube.com/shorts/%s",
            video_id,
            video_id,
        )
        return video_id
