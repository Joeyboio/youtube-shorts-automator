#!/usr/bin/env python3
"""Generate sample animated background videos for YouTube Shorts.

Creates 3 satisfying animated backgrounds using pure Python + MoviePy:
1. Gradient color flow (soap-cutting-style smooth colors)
2. Moving particle field (Subway-Surfers-style dynamic motion)
3. Geometric blocks animation (Minecraft-style pixel blocks)

These are placeholder backgrounds. For best results, replace with real
gameplay footage or ASMR clips (see scripts/download_backgrounds.py).

Usage:
    python scripts/generate_sample_backgrounds.py
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from moviepy.video.VideoClip import VideoClip
from PIL import Image, ImageDraw

BACKGROUNDS_DIR = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
WIDTH, HEIGHT = 1080, 1920
DURATION = 65  # seconds
FPS = 24


def make_gradient_flow(duration: int = DURATION) -> None:
    """Smooth flowing gradient — satisfying color transitions."""
    output = BACKGROUNDS_DIR / "gradient_flow.mp4"
    print(f"Generating gradient flow background -> {output.name}")

    def make_frame(t: float) -> np.ndarray:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        for y in range(HEIGHT):
            progress = y / HEIGHT
            time_offset = t / 10.0
            r = int(127 + 127 * math.sin(2 * math.pi * (progress + time_offset)))
            g = int(127 + 127 * math.sin(2 * math.pi * (progress + time_offset + 0.33)))
            b = int(127 + 127 * math.sin(2 * math.pi * (progress + time_offset + 0.66)))
            frame[y, :] = [r, g, b]
        return frame

    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
    clip.write_videofile(str(output), codec="libx264", preset="medium", logger=None)
    clip.close()
    print(f"  Done: {output.name}")


def make_particle_field(duration: int = DURATION) -> None:
    """Moving dots/particles — dynamic motion background."""
    output = BACKGROUNDS_DIR / "particle_field.mp4"
    print(f"Generating particle field background -> {output.name}")

    np.random.seed(42)
    num_particles = 80
    px = np.random.rand(num_particles) * WIDTH
    py = np.random.rand(num_particles) * HEIGHT
    speeds = np.random.rand(num_particles) * 3 + 1
    sizes = (np.random.rand(num_particles) * 12 + 4).astype(int)
    colors_r = np.random.randint(100, 255, num_particles)
    colors_g = np.random.randint(100, 255, num_particles)
    colors_b = np.random.randint(100, 255, num_particles)

    def make_frame(t: float) -> np.ndarray:
        img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 30))
        draw = ImageDraw.Draw(img)

        for i in range(num_particles):
            x = px[i]
            y = (py[i] - speeds[i] * t * 60) % HEIGHT
            r, g, b = int(colors_r[i]), int(colors_g[i]), int(colors_b[i])
            s = int(sizes[i])
            draw.ellipse([x - s, y - s, x + s, y + s], fill=(r, g, b))

        return np.array(img)

    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
    clip.write_videofile(str(output), codec="libx264", preset="medium", logger=None)
    clip.close()
    print(f"  Done: {output.name}")


def make_block_grid(duration: int = DURATION) -> None:
    """Animated pixel blocks — Minecraft-style grid background."""
    output = BACKGROUNDS_DIR / "block_grid.mp4"
    print(f"Generating block grid background -> {output.name}")

    block_size = 60
    cols = WIDTH // block_size + 1
    rows = HEIGHT // block_size + 1

    np.random.seed(123)
    base_colors = np.random.randint(30, 200, (rows, cols, 3))

    def make_frame(t: float) -> np.ndarray:
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))
        draw = ImageDraw.Draw(img)

        for row in range(rows):
            for col in range(cols):
                wave = math.sin(t * 2 + row * 0.3 + col * 0.2) * 0.3 + 0.7
                r = int(base_colors[row, col, 0] * wave)
                g = int(base_colors[row, col, 1] * wave)
                b = int(base_colors[row, col, 2] * wave)
                r, g, b = min(r, 255), min(g, 255), min(b, 255)

                x1 = col * block_size
                y1 = row * block_size
                x2 = x1 + block_size - 2
                y2 = y1 + block_size - 2
                draw.rectangle([x1, y1, x2, y2], fill=(r, g, b))

        return np.array(img)

    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
    clip.write_videofile(str(output), codec="libx264", preset="medium", logger=None)
    clip.close()
    print(f"  Done: {output.name}")


def main() -> None:
    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("Generating sample background videos...")
    print(f"Output: {BACKGROUNDS_DIR}/")
    print(f"Resolution: {WIDTH}x{HEIGHT} | Duration: {DURATION}s | FPS: {FPS}")
    print("=" * 50)
    print()

    make_gradient_flow()
    make_particle_field()
    make_block_grid()

    print()
    print("All backgrounds generated!")
    print("For better results, replace these with real gameplay/ASMR footage.")
    print("Run: python scripts/download_backgrounds.py  for download links.")


if __name__ == "__main__":
    main()
