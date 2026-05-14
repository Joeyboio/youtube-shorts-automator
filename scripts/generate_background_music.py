"""Generate royalty-free lo-fi background music tracks using synthesis.

Creates soothing, playful ambient music suitable for YouTube Shorts backgrounds.
No external dependencies beyond numpy and standard audio encoding.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"


def sine_wave(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return (volume * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def apply_envelope(
    audio: np.ndarray, attack: float = 0.05, release: float = 0.1
) -> np.ndarray:
    """Apply attack/release envelope to smooth note transitions."""
    n = len(audio)
    attack_samples = int(attack * SAMPLE_RATE)
    release_samples = int(release * SAMPLE_RATE)
    envelope = np.ones(n, dtype=np.float32)

    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    if release_samples > 0:
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)

    return audio * envelope


def save_wav(audio: np.ndarray, path: Path) -> None:
    """Save float32 audio array to WAV file."""
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def generate_lofi_chill(duration: float = 70.0) -> np.ndarray:
    """Generate a soothing lo-fi chill beat with gentle piano-like tones."""
    total_samples = int(SAMPLE_RATE * duration)
    output = np.zeros(total_samples, dtype=np.float32)

    # Chord progression: Cmaj7 -> Am7 -> Fmaj7 -> G7 (classic lo-fi)
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],  # Am7
        [174.61, 220.00, 261.63, 329.63],  # Fmaj7
        [196.00, 246.94, 293.66, 349.23],  # G7
    ]

    note_duration = 0.8
    chord_duration = 4.0

    for chord_idx in range(int(duration / chord_duration)):
        chord = chords[chord_idx % len(chords)]
        chord_start = int(chord_idx * chord_duration * SAMPLE_RATE)

        for note_idx in range(int(chord_duration / note_duration)):
            note_start = chord_start + int(note_idx * note_duration * SAMPLE_RATE)
            freq = chord[note_idx % len(chord)]

            # Main tone
            note = sine_wave(freq, note_duration * 0.9, volume=0.15)
            # Add soft harmonic
            note += sine_wave(freq * 2, note_duration * 0.9, volume=0.04)
            # Add sub tone
            note += sine_wave(freq * 0.5, note_duration * 0.9, volume=0.06)
            note = apply_envelope(note, attack=0.02, release=0.15)

            end = min(note_start + len(note), total_samples)
            if note_start < total_samples:
                length = end - note_start
                output[note_start:end] += note[:length]

    # Add a gentle pad/drone underneath
    pad = sine_wave(130.81, duration, volume=0.04)  # Low C
    pad += sine_wave(196.00, duration, volume=0.03)  # G
    pad_envelope = np.ones(total_samples, dtype=np.float32) * 0.8
    output += pad[:total_samples] * pad_envelope

    # Normalize
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / peak * 0.7

    return output


def generate_ambient_dreamy(duration: float = 70.0) -> np.ndarray:
    """Generate dreamy ambient pads — ethereal and relaxing."""
    total_samples = int(SAMPLE_RATE * duration)
    output = np.zeros(total_samples, dtype=np.float32)

    # Slow evolving pads
    freqs = [130.81, 164.81, 196.00, 246.94, 293.66]
    for i, freq in enumerate(freqs):
        t = np.linspace(0, duration, total_samples, endpoint=False)
        # Slowly modulate volume
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + i * 0.02) * t)
        tone = np.sin(2 * np.pi * freq * t) * 0.08 * mod
        # Add detuned copy for warmth
        tone += np.sin(2 * np.pi * (freq * 1.003) * t) * 0.05 * mod
        output += tone.astype(np.float32)

    # Add gentle high sparkles
    sparkle_freqs = [523.25, 659.25, 783.99]
    for freq in sparkle_freqs:
        t = np.linspace(0, duration, total_samples, endpoint=False)
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t)
        sparkle = np.sin(2 * np.pi * freq * t) * 0.02 * mod
        output += sparkle.astype(np.float32)

    # Normalize
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / peak * 0.6

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating lo-fi chill track...")
    lofi = generate_lofi_chill(70.0)
    lofi_path = OUTPUT_DIR / "lofi_chill.wav"
    save_wav(lofi, lofi_path)
    print(f"  Saved: {lofi_path} ({lofi_path.stat().st_size / 1024:.0f} KB)")

    print("Generating ambient dreamy track...")
    ambient = generate_ambient_dreamy(70.0)
    ambient_path = OUTPUT_DIR / "ambient_dreamy.wav"
    save_wav(ambient, ambient_path)
    print(f"  Saved: {ambient_path} ({ambient_path.stat().st_size / 1024:.0f} KB)")

    print("\nDone! Music files saved to assets/music/")
    print("The pipeline will automatically pick from these for background music.")


if __name__ == "__main__":
    main()
