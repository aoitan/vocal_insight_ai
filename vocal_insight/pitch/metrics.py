"""音程判定用メトリクス計算"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np


A4_HZ = 440.0
LOG2 = math.log(2.0)


def hz_to_cents(pitch_hz: np.ndarray) -> np.ndarray:
    """周波数[Hz]をA4=440Hz基準のセント値に変換"""

    cents = np.full_like(pitch_hz, np.nan, dtype=np.float64)
    valid = pitch_hz > 0
    cents[valid] = 1200.0 * np.log(pitch_hz[valid] / A4_HZ) / LOG2
    return cents


def smooth_series(values: np.ndarray, window: int) -> np.ndarray:
    """移動平均で簡易平滑化（NaNは無視）"""

    if window <= 1:
        return values

    pad = window // 2
    padded = np.pad(values, (pad, pad), constant_values=np.nan)
    smoothed = np.empty_like(values)
    for i in range(len(values)):
        segment = padded[i : i + window]
        valid = ~np.isnan(segment)
        smoothed[i] = np.nanmean(segment[valid]) if np.any(valid) else np.nan
    return smoothed


def interpolate_nans(values: np.ndarray) -> np.ndarray:
    """NaNを線形補間で埋めたコピーを返す"""

    result = values.copy()
    n = len(result)
    if n == 0:
        return result

    nan_mask = np.isnan(result)
    if not np.any(nan_mask):
        return result

    indices = np.arange(n)
    valid = ~nan_mask
    if np.sum(valid) < 2:
        return result

    result[nan_mask] = np.interp(indices[nan_mask], indices[valid], result[valid])
    return result


def compute_deviation_metrics(
    deviations: np.ndarray,
    tolerance_cent: float,
) -> Tuple[float, float, float]:
    """平均偏差・中央値・ヒット率を算出"""

    if deviations.size == 0:
        return 0.0, 0.0, 0.0

    abs_dev = np.abs(deviations)
    mean_dev = float(np.mean(abs_dev))
    median_dev = float(np.median(abs_dev))
    hit_rate = float(np.count_nonzero(abs_dev <= tolerance_cent) / len(abs_dev))
    return mean_dev, median_dev, hit_rate


def compute_stability(deviations: np.ndarray) -> float:
    """偏差の標準偏差を用いた安定度指標（0〜1）"""

    if deviations.size == 0:
        return 0.0

    std_cents = float(np.std(deviations))
    # 0 centなら安定度1. 200セントで0に近づくよう減衰（経験的選択）
    stability = max(0.0, 1.0 - (std_cents / 200.0))
    return float(min(stability, 1.0))
