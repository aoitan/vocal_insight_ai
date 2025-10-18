"""
設定管理モジュール

デフォルト設定と設定の検証機能を提供
"""

from pathlib import Path
from typing import Any, Dict, Union

from .types import (
    AnalysisConfig,
    PitchAnalysisConfig,
    ReferenceVocalExtractionConfig,
)


def get_default_config() -> AnalysisConfig:
    """デフォルト分析設定を取得

    Returns:
        デフォルトの分析設定
    """
    return AnalysisConfig(
        rms_delta_percentile=95,
        min_len_sec=8.0,
        max_len_sec=45.0,
        reference_vocal={
            "enabled": False,
            "model_type": "hpss",
            "model_path": None,
            "output_dir": None,
            "cache_dir": None,
            "cache_path": None,
            "save_audio": True,
            "reuse_existing": True,
            "overwrite": False,
            "target_sr": 44100,
            "trim_silence": True,
            "quality_metrics": True,
            "source_path": None,
            "extracted_path": None,
            "metadata_path": None,
            "demucs_model": "htdemucs",
            "demucs_device": None,
            "demucs_segment": None,
            "demucs_shifts": 1,
            "demucs_overlap": 0.25,
        },
        pitch_analysis={
            "enabled": False,
            "include_in_prompt": True,
            "algorithm": "pyin",
            "dtw_enabled": True,
            "dtw_window": None,
            "pitch_unit": "cent",
            "reference_file": None,
            "output_path": None,
            "cache_path": None,
            "section_length_sec": 30.0,
            "cent_tolerance": 50.0,
            "smoothing_ms": 80.0,
            "min_confidence": 0.6,
            "target_sr": 22050,
            "hop_length": 256,
            "fmin_hz": 65.0,
            "fmax_hz": 2000.0,
        },
    )


def validate_config(config: AnalysisConfig) -> bool:
    """分析設定の検証

    Args:
        config: 検証対象の設定

    Returns:
        設定が有効な場合True

    Raises:
        ValueError: 設定が無効な場合
    """
    if not (0 <= config["rms_delta_percentile"] <= 100):
        raise ValueError("rms_delta_percentile must be between 0 and 100")

    if config["min_len_sec"] < 0:
        raise ValueError("min_len_sec must be positive")

    if config["max_len_sec"] < 0:
        raise ValueError("max_len_sec must be positive")

    if config["min_len_sec"] >= config["max_len_sec"]:
        raise ValueError("min_len_sec must be less than max_len_sec")

    reference_cfg = config.get("reference_vocal", {})
    _validate_reference_vocal_config(reference_cfg)

    pitch_cfg = config.get("pitch_analysis", {})
    _validate_pitch_analysis_config(pitch_cfg)

    return True


def merge_config(base: AnalysisConfig, overrides: dict[str, Any]) -> AnalysisConfig:
    """設定のマージユーティリティ"""

    merged: dict[str, Any] = {**base}
    merged_reference = dict(base.get("reference_vocal", {}))
    override_reference = overrides.get("reference_vocal")
    merged_pitch = dict(base.get("pitch_analysis", {}))
    override_pitch = overrides.get("pitch_analysis")

    for key, value in overrides.items():
        if key == "reference_vocal" and isinstance(override_reference, dict):
            merged_reference.update({k: v for k, v in override_reference.items() if v is not None})
        elif key == "pitch_analysis" and isinstance(override_pitch, dict):
            merged_pitch.update({k: v for k, v in override_pitch.items() if v is not None})
        else:
            merged[key] = value

    merged["reference_vocal"] = merged_reference
    merged["pitch_analysis"] = merged_pitch
    return merged  # type: ignore[return-value]


def _validate_reference_vocal_config(config: ReferenceVocalExtractionConfig) -> None:
    if not config:
        return

    model_type = config.get("model_type")
    if model_type is not None and not isinstance(model_type, str):
        raise ValueError("reference_vocal.model_type must be a string")

    for key in (
        "model_path",
        "output_dir",
        "cache_dir",
        "cache_path",
        "source_path",
        "extracted_path",
        "metadata_path",
    ):
        value = config.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"reference_vocal.{key} must be a string path")
        Path(value)

    target_sr = config.get("target_sr")
    if target_sr is not None and target_sr <= 0:
        raise ValueError("reference_vocal.target_sr must be positive")

    for flag in ("enabled", "save_audio", "reuse_existing", "overwrite", "trim_silence", "quality_metrics"):
        if flag in config and not isinstance(config[flag], bool):
            raise ValueError(f"reference_vocal.{flag} must be a boolean")

    for key in ("demucs_model", "demucs_device"):
        value = config.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"reference_vocal.{key} must be a string")

    if "demucs_segment" in config and config["demucs_segment"] is not None:
        if config["demucs_segment"] <= 0:
            raise ValueError("reference_vocal.demucs_segment must be positive")

    if "demucs_shifts" in config and config["demucs_shifts"] is not None:
        if config["demucs_shifts"] <= 0:
            raise ValueError("reference_vocal.demucs_shifts must be positive")

    if "demucs_overlap" in config and config["demucs_overlap"] is not None:
        if not 0 < config["demucs_overlap"] < 1:
            raise ValueError("reference_vocal.demucs_overlap must be between 0 and 1")


def _validate_pitch_analysis_config(
    config: Union[PitchAnalysisConfig, Dict[str, Any]]
) -> None:
    if not config:
        return

    if "enabled" in config and not isinstance(config["enabled"], bool):
        raise ValueError("pitch_analysis.enabled must be a boolean")

    if "include_in_prompt" in config and not isinstance(config["include_in_prompt"], bool):
        raise ValueError("pitch_analysis.include_in_prompt must be a boolean")

    algorithm = config.get("algorithm")
    if algorithm is not None and not isinstance(algorithm, str):
        raise ValueError("pitch_analysis.algorithm must be a string")

    for path_key in ("reference_file", "output_path", "cache_path"):
        value = config.get(path_key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"pitch_analysis.{path_key} must be a string path")
        Path(value)

    if "section_length_sec" in config and config["section_length_sec"] <= 0:
        raise ValueError("pitch_analysis.section_length_sec must be positive")

    if "cent_tolerance" in config and config["cent_tolerance"] <= 0:
        raise ValueError("pitch_analysis.cent_tolerance must be positive")

    if "smoothing_ms" in config and config["smoothing_ms"] < 0:
        raise ValueError("pitch_analysis.smoothing_ms must be non-negative")

    if "min_confidence" in config:
        value = config["min_confidence"]
        if not 0 <= value <= 1:
            raise ValueError("pitch_analysis.min_confidence must be between 0 and 1")

    if "target_sr" in config and config["target_sr"] is not None and config["target_sr"] <= 0:
        raise ValueError("pitch_analysis.target_sr must be positive")

    if "hop_length" in config and config["hop_length"] is not None and config["hop_length"] <= 0:
        raise ValueError("pitch_analysis.hop_length must be positive")

    for hz_key in ("fmin_hz", "fmax_hz"):
        value = config.get(hz_key)
        if value is not None and value <= 0:
            raise ValueError(f"pitch_analysis.{hz_key} must be positive")

    if config.get("fmin_hz") and config.get("fmax_hz"):
        if config["fmin_hz"] >= config["fmax_hz"]:  # type: ignore[index]
            raise ValueError("pitch_analysis.fmin_hz must be less than fmax_hz")
