"""
共通型定義モジュール

アプリケーション全体で使用される型定義を提供
"""

from typing import TypedDict


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
