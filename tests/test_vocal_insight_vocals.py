"""vocal_insight.vocals モジュールのテスト"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from vocal_insight.core.config import get_default_config
from vocal_insight.vocals import ReferenceVocalExtractor, extract_reference_vocals
from vocal_insight.vocals.separators import (
    register_separator,
    unregister_separator,
)


def _create_test_audio(path: Path, frequency: float = 220.0, sr: int = 16000) -> int:
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    vocal = 0.6 * np.sin(2 * np.pi * frequency * t)
    accompaniment = 0.2 * np.sin(2 * np.pi * (frequency * 2) * t)
    mix = vocal + accompaniment
    sf.write(path, mix.astype(np.float32), sr)
    return sr


def test_reference_extractor_produces_audio_and_metadata(tmp_path: Path):
    input_path = tmp_path / "mix.wav"
    sr = _create_test_audio(input_path)
    output_dir = tmp_path / "reference_out"
    cache_dir = tmp_path / "reference_cache"

    reference_config = get_default_config()["reference_vocal"].copy()
    reference_config.update(
        {
            "enabled": True,
            "output_dir": str(output_dir),
            "cache_dir": str(cache_dir),
            "target_sr": sr,
            "quality_metrics": True,
        }
    )

    extractor = ReferenceVocalExtractor(reference_config)
    result = extractor.extract_from_path(input_path)

    assert result.audio.size > 0
    assert result.sample_rate == sr
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.metadata_path is not None
    assert result.metadata_path.exists()
    assert result.metrics is not None

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["model_type"] == reference_config["model_type"]
    assert "metrics" in metadata
    assert metadata["metrics"]["snr_db"] == pytest.approx(result.metrics.snr_db, rel=1e-1)


def test_extract_reference_vocals_respects_no_save_and_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "mix.wav"
    sr = _create_test_audio(input_path)

    cache_dir = tmp_path / "cache_env"
    monkeypatch.setenv("REFERENCE_CACHE", str(cache_dir))

    config = get_default_config()["reference_vocal"].copy()
    config.update(
        {
            "enabled": True,
            "output_dir": None,
            "cache_dir": "$REFERENCE_CACHE",
            "save_audio": False,
            "target_sr": sr,
            "quality_metrics": False,
        }
    )

    result = extract_reference_vocals(str(input_path), config)

    assert result.output_path is None
    assert result.cache_path is not None
    assert result.cache_path.exists()
    assert result.metadata_path is not None
    assert result.metadata_path.exists()
    cache_payload = np.load(result.cache_path)
    assert cache_payload.ndim == 1
    assert cache_payload.size > 0


def test_reference_extractor_uses_custom_registered_separator(tmp_path: Path):
    input_path = tmp_path / "mix.wav"
    sr = _create_test_audio(input_path)

    calls: dict[str, object] = {}

    class DummySeparator:
        def __init__(self, config: dict[str, object]):
            calls["config"] = config

        def separate(self, audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
            calls["call"] = {
                "sample_rate": sample_rate,
                "frames": audio.shape,
            }
            vocal = audio * 0.5
            residual = audio - vocal
            return vocal, residual

    register_separator("dummy", lambda cfg: DummySeparator(cfg))
    try:
        reference_config = get_default_config()["reference_vocal"].copy()
        reference_config.update(
            {
                "enabled": True,
                "model_type": "dummy",
                "output_dir": str(tmp_path / "out"),
                "cache_dir": str(tmp_path / "cache"),
                "target_sr": sr,
                "quality_metrics": False,
            }
        )

        extractor = ReferenceVocalExtractor(reference_config)
        result = extractor.extract_from_path(input_path)

        assert result.model_type == "dummy"
        assert "call" in calls
        assert calls["call"] == {
            "sample_rate": sr,
            "frames": (sr,),
        }
    finally:
        unregister_separator("dummy")


def test_demucs_separator_requires_dependency(tmp_path: Path):
    input_path = tmp_path / "mix.wav"
    sr = _create_test_audio(input_path)

    reference_config = get_default_config()["reference_vocal"].copy()
    reference_config.update(
        {
            "enabled": True,
            "model_type": "demucs",
            "output_dir": str(tmp_path / "out"),
            "target_sr": sr,
            "quality_metrics": False,
        }
    )

    extractor = ReferenceVocalExtractor(reference_config)

    try:
        import demucs  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError) as exc:
            extractor.extract_from_path(input_path)

        assert "demucs" in str(exc.value).lower()
    else:
        result = extractor.extract_from_path(input_path)
        assert result.model_type == "demucs"
        assert result.audio.size > 0
        assert result.sample_rate == sr
