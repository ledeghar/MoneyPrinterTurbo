import numpy as np

from app.services.audio_mastering import prepare_audio_mix


def test_music_ducks_during_speech_and_returns_between_phrases():
    fps = 1000
    audio = np.zeros(4 * fps, dtype=np.float32)
    audio[fps : 2 * fps] = 0.16
    gain, times, bgm_multiplier = prepare_audio_mix(audio, fps, 2.0)
    assert 0 < gain <= 0.85 / 0.16 + 1e-6
    assert bgm_multiplier[0] > 0.95
    assert np.interp(1.5, times, bgm_multiplier) < 0.40
    assert np.interp(3.5, times, bgm_multiplier) > 0.95


def test_peak_limiter_caps_boosted_tts_and_supports_stereo():
    fps = 1000
    mono = np.full(fps, 0.64, dtype=np.float32)
    stereo = np.column_stack([mono, mono])
    gain, times, music = prepare_audio_mix(stereo, fps, 2.0)
    assert 0.0 < gain <= 0.85 / 0.64 + 0.01
    assert len(times) == len(music)
    assert np.all((0.28 - 1e-6 <= music) & (music <= 1.0))


def test_quieter_voice_request_is_preserved():
    gain, _, _ = prepare_audio_mix(np.full(1000, 0.2), 1000, 0.6)
    assert abs(gain - 0.6) < 1e-6


def test_empty_audio_is_rejected():
    try:
        prepare_audio_mix(np.empty(0), 1000, 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected a ValueError")
