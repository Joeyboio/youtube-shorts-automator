# YouTube Shorts Automator 🎬

Automatically generate, voiceover, and upload YouTube Shorts from Reddit stories (AITA, TIFU, etc.) with satisfying background videos.

## How It Works

1. **Script Generation** — Fetches stories from Reddit (r/AmItheAsshole, r/tifu, etc.) and uses OpenAI GPT to rewrite them as punchy 30-50 second voiceover scripts. Can also generate original stories.
2. **Voiceover** — Converts the script to speech using Google Text-to-Speech (gTTS).
3. **Video Creation** — Combines a satisfying background video (slime, soap cutting, etc.) with the voiceover audio and animated subtitles using MoviePy.
4. **YouTube Upload** — Uploads the final video to YouTube as a Short using the YouTube Data API v3.
5. **Scheduler** — Optionally runs the pipeline on a schedule (e.g., 3 videos/day).

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/youtube-shorts-automator.git
cd youtube-shorts-automator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

### 2. Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required keys:**
- `OPENAI_API_KEY` — Get one at [platform.openai.com](https://platform.openai.com/api-keys)

**Optional keys:**
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — For fetching real Reddit posts. Create an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- YouTube OAuth credentials (see below)

### 3. Add Background Videos

Place satisfying `.mp4` background videos in `assets/backgrounds/`. These should be:
- High quality (1080p+)
- Vertical (9:16) or landscape (will be auto-cropped)
- Satisfying content: slime mixing, soap cutting, sand kinetic, etc.

You can download royalty-free clips from sites like [Pexels](https://www.pexels.com/videos/) or [Pixabay](https://pixabay.com/videos/).

### 4. YouTube API Setup

To enable automatic uploads:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **YouTube Data API v3**
4. Go to **APIs & Services → Credentials**
5. Create an **OAuth 2.0 Client ID** (Desktop application)
6. Download the JSON and save it as `config/client_secrets.json`
7. On first upload, a browser window will open for OAuth consent

### 5. Run

```bash
# Generate a single video (no upload)
yt-shorts run --no-upload

# Generate and upload (private by default)
yt-shorts run --privacy private

# Generate and upload as public
yt-shorts run --privacy public

# Run on a schedule (every 8 hours by default)
yt-shorts schedule

# Just generate a script (no video)
yt-shorts generate-script
```

## Configuration

All settings can be configured via environment variables or the `.env` file. See `.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key (required for script generation) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `REDDIT_CLIENT_ID` | — | Reddit API client ID (optional) |
| `REDDIT_CLIENT_SECRET` | — | Reddit API client secret (optional) |
| `SUBREDDITS` | `AmItheAsshole,tifu,...` | Subreddits to pull stories from |
| `VIDEOS_PER_DAY` | `3` | Target videos per day |
| `SCHEDULE_INTERVAL_HOURS` | `8` | Hours between pipeline runs |
| `MAX_VIDEO_DURATION` | `59` | Max video length in seconds |
| `VIDEO_WIDTH` | `1080` | Video width (portrait) |
| `VIDEO_HEIGHT` | `1920` | Video height (portrait) |
| `FONT_SIZE` | `48` | Subtitle font size |

## Project Structure

```
youtube-shorts-automator/
├── src/
│   ├── main.py              # CLI entry point
│   ├── pipeline.py          # Full pipeline orchestrator
│   ├── config.py            # Settings (pydantic-settings)
│   ├── script_generator/    # Reddit fetching + GPT script writing
│   ├── voiceover/           # gTTS text-to-speech
│   ├── video_creator/       # MoviePy video composition
│   ├── uploader/            # YouTube Data API upload
│   └── scheduler/           # Cron-like scheduling
├── assets/
│   └── backgrounds/         # Background .mp4 videos
├── config/
│   └── client_secrets.json  # YouTube OAuth (not committed)
├── output/                  # Generated content (not committed)
│   ├── scripts/
│   ├── audio/
│   └── videos/
├── .env.example
├── pyproject.toml
└── README.md
```

## System Dependencies

MoviePy requires FFmpeg and ImageMagick:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg imagemagick

# macOS
brew install ffmpeg imagemagick
```

## License

MIT
