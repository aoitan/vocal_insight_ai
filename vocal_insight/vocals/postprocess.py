"""ボーカル抽出後の後処理ユーティリティ"""

from __future__ import annotations

import librosa
import numpy as np


def ensure_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return librosa.to_mono(audio)


def resample_audio(audio: np.ndarray, sr: int, target_sr: int | None) -> tuple[np.ndarray, int]:
    if target_sr is None or sr == target_sr:
        return audio, sr
    resampled = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return resampled.astype(np.float32), target_sr


def trim_silence(audio: np.ndarray, sr: int, top_db: float = 40.0) -> tuple[np.ndarray, tuple[int, int]]:
    trimmed, idx = librosa.effects.trim(audio, top_db=top_db)
    if trimmed.size == 0:
        return audio, (0, len(audio))
    return trimmed, tuple(idx)


def normalize_audio(audio: np.ndarray, max_abs: float = 0.99) -> np.ndarray:
    peak = np.max(np.abs(audio)) if audio.size else 0.0
    if peak == 0:
        return audio
    return (audio / peak) * max_abs
