"""
Speaker diarization using Resemblyzer voice embeddings.
Identifies who is speaking at each moment, assigns OpusClip-style
speaker labels and colors. Returns speaker segments that subtitle_generator
can use to color-code captions per speaker.

Opus speaker colors (from their JS):
  SPEAKER_00 → #979BFF (purple)
  SPEAKER_01 → #FFDA7D (yellow)
  SPEAKER_02 → #C3FF7A (green)
  SPEAKER_03 → #97F8F8 (cyan)
  SPEAKER_04 → #FF759A (pink)
"""
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

SPEAKER_COLORS = [
    "#979BFF",  # purple  - Speaker 1
    "#FFDA7D",  # yellow  - Speaker 2
    "#C3FF7A",  # green   - Speaker 3
    "#97F8F8",  # cyan    - Speaker 4
    "#FF759A",  # pink    - Speaker 5
]

# ASS colour format &HAABBGGRR from hex #RRGGBB
def _hex_to_ass(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}"


@dataclass
class SpeakerSegment:
    speaker_id: int        # 0-based index
    start: float           # seconds
    end: float             # seconds
    color_hex: str         # #RRGGBB
    color_ass: str         # &H00BBGGRR


def diarize(audio_path: str, min_segment_s: float = 1.0) -> list[SpeakerSegment]:
    """
    Run speaker diarization on an audio file.
    Returns list of SpeakerSegments sorted by start time.
    Falls back to single-speaker if resemblyzer fails or only 1 speaker.
    """
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        import librosa
    except ImportError:
        log.warning("resemblyzer not available — skipping diarization")
        return []

    path = Path(audio_path)
    log.info("Running speaker diarization...")

    # Resample to 16kHz WAV if needed
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    subprocess.run([
        "ffmpeg", "-y", "-i", str(path),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        wav_path
    ], capture_output=True, check=True)

    try:
        wav = preprocess_wav(wav_path)
    finally:
        Path(wav_path).unlink(missing_ok=True)

    # Embed speaker voice in sliding windows
    encoder = VoiceEncoder("cpu")
    window_s = 1.5
    step_s   = 0.5
    sr = 16000
    win = int(window_s * sr)
    stp = int(step_s * sr)

    embeddings = []
    times = []
    for i in range(0, max(1, len(wav) - win), stp):
        chunk = wav[i : i + win]
        if len(chunk) < sr // 4:
            break
        emb = encoder.embed_utterance(chunk)
        embeddings.append(emb)
        times.append(i / sr)

    if len(embeddings) < 2:
        log.info("Audio too short for diarization — single speaker assumed")
        return []

    embeddings = np.array(embeddings)

    # Cluster into speakers with simple cosine-similarity agglomerative
    try:
        from sklearn.cluster import AgglomerativeClustering
        n_speakers = _estimate_speakers(embeddings)
        log.info(f"Estimated {n_speakers} speaker(s)")
        if n_speakers < 2:
            return []
        labels = AgglomerativeClustering(
            n_clusters=n_speakers,
            metric="cosine",
            linkage="average",
        ).fit_predict(embeddings)
    except ImportError:
        # Fallback: simple thresholding
        labels = _simple_cluster(embeddings)
        n_speakers = max(labels) + 1
        if n_speakers < 2:
            return []

    # Build segments by merging consecutive same-speaker windows
    segments: list[SpeakerSegment] = []
    cur_speaker = int(labels[0])
    seg_start   = times[0]

    for i in range(1, len(labels)):
        speaker = int(labels[i])
        if speaker != cur_speaker or i == len(labels) - 1:
            seg_end = times[i]
            if seg_end - seg_start >= min_segment_s:
                color = SPEAKER_COLORS[cur_speaker % len(SPEAKER_COLORS)]
                segments.append(SpeakerSegment(
                    speaker_id=cur_speaker,
                    start=seg_start,
                    end=seg_end,
                    color_hex=color,
                    color_ass=_hex_to_ass(color),
                ))
            cur_speaker = speaker
            seg_start   = times[i]

    log.info(f"Diarization: {n_speakers} speakers, {len(segments)} segments")
    return segments


def _estimate_speakers(embeddings: np.ndarray, max_speakers: int = 5) -> int:
    """Estimate number of speakers from embedding spread."""
    from numpy.linalg import norm
    normed = embeddings / (norm(embeddings, axis=1, keepdims=True) + 1e-9)
    sim_matrix = normed @ normed.T
    avg_sim = (sim_matrix.sum() - len(sim_matrix)) / max(1, len(sim_matrix) ** 2 - len(sim_matrix))
    # High similarity → 1 speaker; lower → more speakers
    if avg_sim > 0.92:
        return 1
    if avg_sim > 0.80:
        return 2
    if avg_sim > 0.70:
        return 3
    return min(4, max_speakers)


def _simple_cluster(embeddings: np.ndarray, threshold: float = 0.15) -> np.ndarray:
    """Simple speaker clustering without sklearn."""
    from numpy.linalg import norm
    n = len(embeddings)
    labels = np.zeros(n, dtype=int)
    centroids = [embeddings[0]]
    for i in range(1, n):
        e = embeddings[i]
        sims = [np.dot(e, c) / (norm(e) * norm(c) + 1e-9) for c in centroids]
        best = max(range(len(sims)), key=lambda j: sims[j])
        if sims[best] < 1 - threshold:
            centroids.append(e)
            labels[i] = len(centroids) - 1
        else:
            labels[i] = best
    return labels


def speaker_for_time(segments: list[SpeakerSegment], t: float) -> SpeakerSegment | None:
    """Return the speaker segment active at time t."""
    for seg in segments:
        if seg.start <= t < seg.end:
            return seg
    return None
