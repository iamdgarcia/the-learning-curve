"""
Audio enhancement — removes background noise from clip audio.
Uses noisereduce (stationary + non-stationary NR) then recombines
with the video via ffmpeg.

Matches OpusClip's "enhance_speech" workflow type.
"""
import logging
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import noisereduce as nr

log = logging.getLogger(__name__)


def enhance(input_path: str, output_path: str, prop_decrease: float = 0.85) -> Path:
    """
    Denoise the audio track of a video clip.
    prop_decrease: 0-1, how aggressively to reduce noise (0.85 = strong but preserves voice)
    """
    inp = Path(input_path)
    out = Path(output_path)

    log.info("Enhancing audio (noise reduction)...")

    with tempfile.TemporaryDirectory() as tmp:
        raw_audio  = Path(tmp) / "raw.wav"
        clean_audio = Path(tmp) / "clean.wav"

        # Extract audio as WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", str(inp),
            "-vn", "-ar", "44100", "-ac", "1",
            "-c:a", "pcm_s16le", str(raw_audio),
        ], check=True, capture_output=True)

        # Load and denoise
        data, sr = sf.read(str(raw_audio))
        data = data.astype(np.float32)

        # Estimate noise from first 0.5s (usually silence/ambient)
        noise_clip = data[: int(sr * 0.5)] if len(data) > sr * 0.5 else data

        reduced = nr.reduce_noise(
            y=data,
            sr=sr,
            y_noise=noise_clip,
            prop_decrease=prop_decrease,
            stationary=False,          # non-stationary for streaming audio
            n_fft=1024,
        )

        sf.write(str(clean_audio), reduced, sr, subtype="PCM_16")

        # Recombine with original video
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(inp),          # original video (has original audio too)
            "-i", str(clean_audio),   # enhanced audio
            "-map", "0:v",            # video from original
            "-map", "1:a",            # audio from enhanced
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            str(out),
        ], check=True, capture_output=True)

    log.info(f"Audio enhanced → {out}")
    return out
