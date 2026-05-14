#!/usr/bin/env python3
"""Download background videos for YouTube Shorts.

This script provides instructions and helpers for obtaining background videos.
Due to website protections, videos must be downloaded manually from these sources.

Usage:
    python scripts/download_backgrounds.py

After downloading, place the .mp4 files in assets/backgrounds/
"""

from pathlib import Path

BACKGROUNDS_DIR = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"


def main() -> None:
    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(BACKGROUNDS_DIR.glob("*.mp4"))
    if existing:
        print(f"Found {len(existing)} existing background video(s):")
        for f in existing:
            print(f"  - {f.name}")
        print()

    print("=" * 60)
    print("BACKGROUND VIDEO DOWNLOAD GUIDE")
    print("=" * 60)
    print()
    print("Download these 3 types of background videos and save them")
    print(f"to: {BACKGROUNDS_DIR}/")
    print()
    print("1. SOAP CUTTING (satisfying ASMR)")
    print("   - Pixabay: https://pixabay.com/videos/search/soap%20cutting/")
    print("   - Pexels:  https://www.pexels.com/search/videos/soap%20cutting/")
    print("   -> Save as: soap_cutting.mp4")
    print()
    print("2. SUBWAY SURFERS GAMEPLAY")
    print("   - Pixabay: https://pixabay.com/videos/search/subway%20surfers%20gameplay/")
    print("   - YouTube (No Copyright): https://www.youtube.com/watch?v=i0M4ARe9v0Y")
    print("   -> Save as: subway_surfers.mp4")
    print()
    print("3. MINECRAFT PARKOUR")
    print("   - Pixabay: https://pixabay.com/videos/search/minecraft%20parkour/")
    print("   - YouTube (Free to Use): https://www.youtube.com/watch?v=lekKHbYQGxM")
    print("   -> Save as: minecraft_parkour.mp4")
    print()
    print("TIPS:")
    print("  - Videos should be at least 60 seconds long")
    print("  - Vertical (9:16) is preferred but landscape works too (auto-cropped)")
    print("  - The app randomly picks a background for each video")
    print()

    if not existing:
        print("NOTE: No background videos found yet!")
        print("The app will use a solid dark background as fallback until you add videos.")
    print()


if __name__ == "__main__":
    main()
