"""Generate short video scripts from Reddit stories, OpenAI, or built-in templates."""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field

import praw
from openai import OpenAI

from src.config import Settings
from src.script_generator.stories import BUILTIN_SCRIPTS

logger = logging.getLogger(__name__)

SCRIPT_SYSTEM_PROMPT = """\
You are a viral YouTube Shorts scriptwriter. You adapt Reddit stories (AITA, TIFU, etc.)
into punchy, engaging 30-50 second voiceover scripts.

Rules:
- Start with a hook like "So this person on Reddit..." or "Am I the jerk for..."
- Keep it conversational and dramatic
- Use short sentences for pacing
- End with a cliffhanger or question to drive engagement
- Output ONLY the voiceover script text, nothing else
- Keep it under 120 words (about 50 seconds of speech)
- Do NOT include stage directions, timestamps, or speaker labels
"""

GENERATE_PROMPT = """\
Create a YouTube Shorts voiceover script based on this Reddit story:

Title: {title}
Story: {body}

Adapt it into a dramatic, engaging short-form voiceover script (under 120 words).
"""

ORIGINAL_PROMPT = """\
Generate an original Reddit-style AITA (Am I The Asshole) story and turn it into
a YouTube Shorts voiceover script (under 120 words). Make it dramatic, relatable,
and engaging. The story should feel real and have a moral dilemma.
"""


@dataclass
class Script:
    title: str
    text: str
    source: str = ""
    hashtags: list[str] = field(default_factory=list)


class ScriptGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._reddit: praw.Reddit | None = None
        self._openai: OpenAI | None = None

    @property
    def reddit(self) -> praw.Reddit | None:
        if self._reddit is None and self.settings.reddit_client_id:
            self._reddit = praw.Reddit(
                client_id=self.settings.reddit_client_id,
                client_secret=self.settings.reddit_client_secret,
                user_agent=self.settings.reddit_user_agent,
            )
        return self._reddit

    @property
    def openai_client(self) -> OpenAI | None:
        if self._openai is None and self.settings.openai_api_key:
            self._openai = OpenAI(api_key=self.settings.openai_api_key)
        return self._openai

    def fetch_reddit_stories(self, limit: int = 10) -> list[dict[str, str]]:
        """Fetch top stories from configured subreddits."""
        if not self.reddit:
            logger.warning("Reddit credentials not configured, using AI-generated stories")
            return []

        stories: list[dict[str, str]] = []
        subreddit_name = random.choice(self.settings.subreddits)
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.hot(limit=limit):
                if post.is_self and len(post.selftext) > 100:
                    stories.append(
                        {
                            "title": post.title,
                            "body": post.selftext[:2000],
                            "subreddit": subreddit_name,
                            "url": post.url,
                        }
                    )
        except Exception as e:
            logger.error("Failed to fetch from r/%s: %s", subreddit_name, e)

        return stories

    def generate_script_from_story(self, story: dict[str, str]) -> Script:
        """Use OpenAI to adapt a Reddit story into a voiceover script."""
        client = self.openai_client
        if not client:
            return self._fallback_script(story)

        response = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": GENERATE_PROMPT.format(
                        title=story["title"], body=story["body"]
                    ),
                },
            ],
            temperature=0.8,
            max_tokens=300,
        )

        script_text = response.choices[0].message.content or ""
        subreddit = story.get("subreddit", "reddit")

        return Script(
            title=story["title"][:80],
            text=script_text.strip(),
            source=story.get("url", ""),
            hashtags=["#reddit", f"#{subreddit}", "#shorts", "#storytime"],
        )

    def generate_builtin_script(self) -> Script:
        """Pick a random script from the built-in story library (no API needed)."""
        story = random.choice(BUILTIN_SCRIPTS)
        logger.info("Using built-in script: %s", story["title"][:60])
        return Script(
            title=story["title"],
            text=story["text"],
            source="builtin",
            hashtags=["#reddit", "#aita", "#shorts", "#storytime", "#redditstories"],
        )

    def generate_original_script(self) -> Script:
        """Generate a completely original AITA-style script using AI."""
        client = self.openai_client
        if not client:
            logger.info("No OpenAI key, falling back to built-in scripts")
            return self.generate_builtin_script()

        response = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {"role": "user", "content": ORIGINAL_PROMPT},
            ],
            temperature=0.9,
            max_tokens=300,
        )

        script_text = response.choices[0].message.content or ""

        title_response = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Generate a catchy YouTube Shorts title (under 60 chars) for this script. "
                        "Output ONLY the title, nothing else:\n\n" + script_text
                    ),
                },
            ],
            temperature=0.7,
            max_tokens=30,
        )

        raw_title = title_response.choices[0].message.content or "Reddit Story Time"
        title = raw_title.strip().strip('"')

        return Script(
            title=title,
            text=script_text.strip(),
            source="ai-generated",
            hashtags=["#reddit", "#aita", "#shorts", "#storytime", "#redditstories"],
        )

    def generate(self) -> Script:
        """Main entry: fetch a Reddit story and generate a script, or create an original one."""
        stories = self.fetch_reddit_stories(limit=10)

        if stories:
            story = random.choice(stories)
            logger.info("Generating script from: %s", story["title"][:60])
            return self.generate_script_from_story(story)

        logger.info("No Reddit stories available, generating original script")
        if not self.openai_client:
            return self.generate_builtin_script()
        try:
            return self.generate_original_script()
        except Exception as e:
            logger.warning("OpenAI script generation failed (%s), using built-in script", e)
            return self.generate_builtin_script()

    def _fallback_script(self, story: dict[str, str]) -> Script:
        """Simple fallback when OpenAI is not available — just truncate the story."""
        body = story["body"]
        sentences = body.split(". ")
        short = ". ".join(sentences[:6]) + "."
        if len(short) > 500:
            short = short[:500] + "..."

        hook = f"So get this. Someone posted on Reddit asking, {story['title']}. "
        return Script(
            title=story["title"][:80],
            text=hook + short,
            source=story.get("url", ""),
            hashtags=["#reddit", "#shorts", "#storytime"],
        )

    def save_script(self, script: Script, path: str) -> None:
        """Save script to a JSON file."""
        data = {
            "title": script.title,
            "text": script.text,
            "source": script.source,
            "hashtags": script.hashtags,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Script saved to %s", path)
