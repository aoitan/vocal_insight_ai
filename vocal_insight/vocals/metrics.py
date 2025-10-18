"""抽出品質メトリクス"""

from __future__ import annotations

import numpy as np

try:
    import librosa
except ImportError:  # pragma: no cover - librosa は必須依存だが保険として
    librosa = None  # type: ignore


def _safe_energy(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 1e-12
    return float(np.mean(np.square(audio))) + 1e-12


def compute_snr_db(vocal: np.ndarray, residual: np.ndarray) -> float:
    """信号対残差のSNR[dB]"""

    signal_energy = _safe_energy(vocal)
    noise_energy = _safe_energy(residual)
    ratio = signal_energy / noise_energy
    return float(10.0 * np.log10(max(ratio, 1e-12)))


def compute_residual_energy_ratio(vocal: np.ndarray, residual: np.ndarray) -> float:
    signal_energy = _safe_energy(vocal)
    noise_energy = _safe_energy(residual)
    return float(noise_energy / (signal_energy + noise_energy))


def compute_pitch_track_coverage(
    vocal: np.ndarray,
    sample_rate: int,
    *,
    fmin: float | None = None,
    fmax: float | None = None,
) -> float:
    if librosa is None:
        return 0.0

    if vocal.size == 0 or sample_rate <= 0:
        return 0.0

    if fmin is None:
        fmin = librosa.note_to_hz("C2")
    if fmax is None:
        fmax = librosa.note_to_hz("C7")

    hop_length = 256
    try:
        pitches, _voiced_flags, _voiced_prob = librosa.pyin(
            vocal,
            fmin=fmin,
            fmax=fmax,
            sr=sample_rate,
            hop_length=hop_length,
        )
    except Exception:
        return 0.0

    if pitches is None or pitches.size == 0:
        return 0.0

    valid = np.count_nonzero(~np.isnan(pitches))
    return float(valid / len(pitches))
