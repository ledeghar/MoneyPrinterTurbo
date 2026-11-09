"""Lightweight speech-aware music ducking for MN Short.

Computes a short volume envelope from an existing narration file. This operates
at a low sample rate and has no model/API dependencies. The video frames are
never re-rendered by the audio analysis itself.
"""
import numpy as np


def prepare_audio_mix(samples, sample_rate: int, requested_voice_gain: float):
    """Return a peak-safe narration gain and music ducking envelope.

    music_gain is a multiplier on the user's already-selected BGM volume.
    The envelope is smooth and drops music under active speech, then restores
    it during pauses. It does not depend on the spoken language.
    """
    rate = max(1, int(sample_rate))
    pcm = np.asarray(samples, dtype=np.float32)
    if pcm.ndim == 2:
        pcm = np.mean(pcm, axis=1)
    if pcm.ndim != 1 or pcm.size == 0:
        raise ValueError("narration audio must be a nonempty mono/stereo array")
    pcm = np.nan_to_num(pcm, nan=0.0, posinf=0.0, neginf=0.0)
    peak = float(np.max(np.abs(pcm)))
    rms = float(np.sqrt(np.mean(np.square(pcm, dtype=np.float64))))
    user_gain = max(0.0, float(requested_voice_gain))
    if not np.isfinite(user_gain):
        raise ValueError("voice gain must be finite")
    # Only normalize when volume is at least 100%; honor quieter requests.
    preferred_gain = max(user_gain, 0.10 / max(rms, 1e-5)) if user_gain >= 1 else user_gain
    # Leave peak headroom for mixed music; avoid multiplying TTS peaks into clipping.
    safe_gain = min(preferred_gain, 0.85 / peak) if peak > 1e-6 else user_gain

    hop = max(1, int(0.08 * rate))
    n = (pcm.size + hop - 1) // hop
    squares = np.square(pcm, dtype=np.float64)
    padded = np.pad(squares, (0, n * hop - pcm.size))
    window_rms = np.sqrt(padded.reshape(n, hop).mean(axis=1))
    active_threshold = max(0.007, float(np.percentile(window_rms, 75)) * 0.22)
    active = window_rms >= active_threshold
    # Preserve lowered music for 240 ms around words, then fade smoothly.
    extended = np.pad(active.astype(np.float32), (3, 3))
    active_with_margin = np.maximum.reduce(
        [extended[i : i + n] for i in range(7)]
    )
    smooth = np.convolve(active_with_margin, np.ones(5) / 5, mode="same")
    times = (np.arange(n, dtype=np.float64) + 0.5) * hop / rate
    music_gain = 1.0 - 0.72 * np.clip(smooth, 0.0, 1.0)
    return float(safe_gain), times, music_gain
