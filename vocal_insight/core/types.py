"""
共通型定義モジュール

アプリケーション全体で使用される型定義を提供
"""

from __future__ import annotations

from typing import TypedDict


class ReferenceVocalExtractionConfig(TypedDict, total=False):
    """リファレンスボーカル抽出設定の型定義"""

    enabled: bool
    model_type: str
    model_path: str | None
    output_dir: str | None
    cache_dir: str | None
    cache_path: str | None
    save_audio: bool
    reuse_existing: bool
    overwrite: bool
    target_sr: int | None
    trim_silence: bool
    quality_metrics: bool
    source_path: str | None
    extracted_path: str | None
    metadata_path: str | None
    demucs_model: str | None
    demucs_device: str | None
    demucs_segment: float | None
    demucs_shifts: int | None
    demucs_overlap: float | None


class PitchAnalysisConfig(TypedDict, total=False):
    """音程精度分析設定の型定義"""

    enabled: bool
    include_in_prompt: bool
    algorithm: str
    dtw_enabled: bool
    dtw_window: int | None
    pitch_unit: str
    reference_file: str | None
    output_path: str | None
    cache_path: str | None
    section_length_sec: float
    cent_tolerance: float
    smoothing_ms: float
    min_confidence: float
    target_sr: int | None
    hop_length: int | None
    fmin_hz: float | None
    fmax_hz: float | None


class FeatureData(TypedDict):
    """音響特徴量データの型定義"""

    f0_mean_hz: float
    f0_std_hz: float
    hnr_mean_db: float
    f1_mean_hz: float
    f2_mean_hz: float
    f3_mean_hz: float


class SegmentAnalysis(TypedDict):
    """セグメント分析結果の型定義"""

    segment_id: int
    time_start_s: float
    time_end_s: float
    features: FeatureData


class AnalysisConfig(TypedDict):
    """分析設定の型定義"""

    rms_delta_percentile: int
    min_len_sec: float
    max_len_sec: float
    reference_vocal: ReferenceVocalExtractionConfig
    pitch_analysis: PitchAnalysisConfig
