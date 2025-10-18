"""vocal_insight.pitch モジュールのテスト"""

from __future__ import annotations

import numpy as np
import pytest

from vocal_insight.core.config import get_default_config
from vocal_insight.pitch import analyze_pitch_accuracy


def _generate_sine(freq: float, sr: int, duration: float = 2.0) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float64)
    waveform = 0.5 * np.sin(2 * np.pi * freq * t)
    return waveform.astype(np.float32)


def test_pitch_analysis_disabled_returns_none():
    config = get_default_config()
    result = analyze_pitch_accuracy(
        _generate_sine(440.0, 22050),
        22050,
        _generate_sine(440.0, 22050),
        22050,
        config["pitch_analysis"],
    )
    assert result.pitch_accuracy is None


def test_pitch_analysis_without_reference_returns_none():
    config = get_default_config()
    pitch_config = config["pitch_analysis"].copy()
    pitch_config["enabled"] = True
    result = analyze_pitch_accuracy(
        _generate_sine(440.0, 22050),
        22050,
        None,
        None,
        pitch_config,
    )
    assert result.pitch_accuracy is None


def test_pitch_analysis_identical_signals_produce_low_deviation():
    config = get_default_config()
    pitch_config = config["pitch_analysis"].copy()
    pitch_config.update(
        {
            "enabled": True,
            "dtw_enabled": False,
            "target_sr": 22050,
            "cent_tolerance": 50.0,
            "smoothing_ms": 40.0,
            "min_confidence": 0.0,
        }
    )

    audio = _generate_sine(440.0, 22050, duration=3.0)
    result = analyze_pitch_accuracy(audio, 22050, audio, 22050, pitch_config)

    assert result.pitch_accuracy is not None
    assert result.pitch_accuracy.mean_cent_deviation < 5.0
    assert result.pitch_accuracy.hit_rate >= 0.9


def test_pitch_analysis_detects_pitch_offset():
    config = get_default_config()
    pitch_config = config["pitch_analysis"].copy()
    pitch_config.update(
        {
            "enabled": True,
            "dtw_enabled": False,
            "target_sr": 22050,
            "cent_tolerance": 50.0,
            "smoothing_ms": 40.0,
            "min_confidence": 0.0,
        }
    )

    reference_audio = _generate_sine(440.0, 22050, duration=3.0)
    target_audio = _generate_sine(466.16, 22050, duration=3.0)  # 約1半音上

    result = analyze_pitch_accuracy(target_audio, 22050, reference_audio, 22050, pitch_config)

    assert result.pitch_accuracy is not None
    assert result.pitch_accuracy.mean_cent_deviation > 80.0
    assert result.pitch_accuracy.hit_rate < 0.5
