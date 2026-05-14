"""Generate royalty-free background music tracks using synthesis.

Creates soothing, warm background music suitable for YouTube Shorts AITA videos.
Inspired by "Lè Bossa" style — gentle bossa nova with soft plucked notes.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"


def pluck_note(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
    """Simulate a plucked string sound (guitar-like) using Karplus-Strong-inspired synthesis."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    # Fundamental + harmonics with quick decay for plucked sound
    decay = np.exp(-t * 4.0)
    tone = np.sin(2 * np.pi * freq * t) * 0.6
    tone += np.sin(2 * np.pi * freq * 2 * t) * 0.2 * np.exp(-t * 6.0)
    tone += np.sin(2 * np.pi * freq * 3 * t) * 0.1 * np.exp(-t * 8.0)
    tone += np.sin(2 * np.pi * freq * 4 * t) * 0.05 * np.exp(-t * 10.0)

    return (tone * decay * volume).astype(np.float32)


def soft_pad(freq: float, duration: float, volume: float = 0.05) -> np.ndarray:
    """Gentle sustained pad tone."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Soft sine with slow vibrato
    vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 4.5 * t)
    tone = np.sin(2 * np.pi * freq * vibrato * t) * volume
    # Detuned copy for warmth
    tone += np.sin(2 * np.pi * freq * 1.002 * t) * volume * 0.6
    # Gentle attack/release
    env = np.ones(n_samples, dtype=np.float32)
    attack = int(0.1 * SAMPLE_RATE)
    release = int(0.2 * SAMPLE_RATE)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    if release > 0:
        env[-release:] = np.linspace(1, 0, release)
    return (tone * env).astype(np.float32)


def save_wav(audio: np.ndarray, path: Path) -> None:
    """Save float32 audio array to WAV file."""
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def generate_bossa_nova(duration: float = 70.0) -> np.ndarray:
    """Generate a warm bossa nova style track with plucked guitar-like notes.

    Inspired by "Lè Bossa" — gentle, soothing, perfect for storytelling videos.
    """
    total_samples = int(SAMPLE_RATE * duration)
    output = np.zeros(total_samples, dtype=np.float32)

    # Bossa nova chord progression (Cmaj7 - Dm7 - G7 - Cmaj7)
    # Using note frequencies
    chord_patterns = [
        # Cmaj7 - gentle arpeggio pattern
        [261.63, 329.63, 392.00, 493.88, 392.00, 329.63],
        # Dm7
        [293.66, 349.23, 440.00, 523.25, 440.00, 349.23],
        # Em7
        [329.63, 392.00, 493.88, 587.33, 493.88, 392.00],
        # Am7
        [220.00, 261.63, 329.63, 392.00, 329.63, 261.63],
        # Fmaj7
        [174.61, 220.00, 261.63, 329.63, 261.63, 220.00],
        # G7
        [196.00, 246.94, 293.66, 349.23, 293.66, 246.94],
    ]

    # Bossa nova rhythm: syncopated pattern (beats in 8th notes)
    # Classic bossa pattern: x . x . . x . x (where x = pluck)
    beat_pattern = [True, False, True, False, False, True, False, True]
    eighth_note_dur = 0.25  # At ~120 BPM
    note_dur = 0.4

    beat_time = 0.0
    chord_idx = 0
    note_in_chord = 0
    beat_in_pattern = 0

    while beat_time < duration:
        if beat_pattern[beat_in_pattern % len(beat_pattern)]:
            chord = chord_patterns[chord_idx % len(chord_patterns)]
            freq = chord[note_in_chord % len(chord)]

            note = pluck_note(freq, note_dur, volume=0.2)
            start_sample = int(beat_time * SAMPLE_RATE)
            end_sample = min(start_sample + len(note), total_samples)
            if start_sample < total_samples:
                length = end_sample - start_sample
                output[start_sample:end_sample] += note[:length]

            note_in_chord += 1

        beat_in_pattern += 1
        beat_time += eighth_note_dur

        # Change chord every 2 bars (16 eighth notes)
        if beat_in_pattern % 16 == 0:
            chord_idx += 1
            note_in_chord = 0

    # Add warm bass notes (root of each chord, sustained)
    bass_roots = [130.81, 146.83, 164.81, 110.00, 87.31, 98.00]
    chord_dur = 16 * eighth_note_dur  # 2 bars per chord
    for i in range(int(duration / chord_dur)):
        root = bass_roots[i % len(bass_roots)]
        bass = soft_pad(root, chord_dur, volume=0.04)
        start = int(i * chord_dur * SAMPLE_RATE)
        end = min(start + len(bass), total_samples)
        if start < total_samples:
            output[start:end] += bass[: end - start]

    # Add gentle high pad for airiness
    pad_freqs = [523.25, 659.25]
    for freq in pad_freqs:
        t = np.linspace(0, duration, total_samples, endpoint=False)
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t)
        sparkle = np.sin(2 * np.pi * freq * t) * 0.012 * mod
        output += sparkle.astype(np.float32)

    # Normalize
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / peak * 0.65

    return output


def generate_warm_ambient(duration: float = 70.0) -> np.ndarray:
    """Generate warm ambient pads — cozy and emotional."""
    total_samples = int(SAMPLE_RATE * duration)
    output = np.zeros(total_samples, dtype=np.float32)

    # Warm chord tones with slow movement
    pad_chords = [
        [130.81, 164.81, 196.00, 261.63],  # C
        [110.00, 130.81, 164.81, 220.00],  # Am
        [87.31, 110.00, 130.81, 174.61],   # F
        [98.00, 123.47, 146.83, 196.00],   # G
    ]

    chord_duration = 8.0
    for chord_idx in range(int(duration / chord_duration)):
        chord = pad_chords[chord_idx % len(pad_chords)]
        chord_start = int(chord_idx * chord_duration * SAMPLE_RATE)

        for freq in chord:
            t = np.linspace(0, chord_duration, int(chord_duration * SAMPLE_RATE), endpoint=False)
            # Slow warm tone with gentle vibrato
            vibrato = 1.0 + 0.002 * np.sin(2 * np.pi * 3.5 * t)
            tone = np.sin(2 * np.pi * freq * vibrato * t) * 0.06
            # Detuned for warmth
            tone += np.sin(2 * np.pi * freq * 1.003 * t) * 0.03
            # Envelope
            env = np.ones(len(t), dtype=np.float32)
            fade = int(1.0 * SAMPLE_RATE)
            env[:fade] = np.linspace(0, 1, fade)
            env[-fade:] = np.linspace(1, 0, fade)
            tone = (tone * env).astype(np.float32)

            end = min(chord_start + len(tone), total_samples)
            if chord_start < total_samples:
                length = end - chord_start
                output[chord_start:end] += tone[:length]

    # Add gentle plucked arpeggios on top
    arp_notes = [523.25, 440.00, 392.00, 329.63, 261.63, 329.63, 392.00, 440.00]
    arp_spacing = 0.6
    arp_time = 0.0
    arp_idx = 0
    while arp_time < duration:
        freq = arp_notes[arp_idx % len(arp_notes)]
        note = pluck_note(freq, 0.5, volume=0.08)
        start = int(arp_time * SAMPLE_RATE)
        end = min(start + len(note), total_samples)
        if start < total_samples:
            output[start:end] += note[: end - start]
        arp_time += arp_spacing
        arp_idx += 1

    # Normalize
    peak = np.max(np.abs(output))
    if peak > 0:
        output = output / peak * 0.55

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating bossa nova track (Lè Bossa style)...")
    bossa = generate_bossa_nova(70.0)
    bossa_path = OUTPUT_DIR / "bossa_nova.wav"
    save_wav(bossa, bossa_path)
    print(f"  Saved: {bossa_path} ({bossa_path.stat().st_size / 1024:.0f} KB)")

    print("Generating warm ambient track...")
    ambient = generate_warm_ambient(70.0)
    ambient_path = OUTPUT_DIR / "warm_ambient.wav"
    save_wav(ambient, ambient_path)
    print(f"  Saved: {ambient_path} ({ambient_path.stat().st_size / 1024:.0f} KB)")

    print("\nDone! Music files saved to assets/music/")
    print("The pipeline will automatically pick from these for background music.")


if __name__ == "__main__":
    main()
