"""音程判定アルゴリズム"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import librosa
import numpy as np

from ..core.types import PitchAnalysisConfig
from .alignment import align_pitch_series
from .metrics import (
    compute_deviation_metrics,
    compute_stability,
    hz_to_cents,
    interpolate_nans,
    smooth_series,
)
from .schemas import PitchAccuracyMetrics, PitchAnalysisResult, PitchSectionMetrics

PITCH_VERSION = "1.0"


def analyze_pitch_accuracy_from_files(
    target_path: str | Path,
    reference_path: Optional[str | Path],
    config: PitchAnalysisConfig,
) -> PitchAnalysisResult:
    target_audio, target_sr = librosa.load(target_path, sr=config.get("target_sr"))
    ref_audio = None
    ref_sr = None
    if reference_path:
        ref_audio, ref_sr = librosa.load(reference_path, sr=config.get("target_sr"))
    return analyze_pitch_accuracy(target_audio, target_sr, ref_audio, ref_sr, config)


def analyze_pitch_accuracy(
    target_audio: np.ndarray,
    target_sr: int,
    reference_audio: Optional[np.ndarray],
    reference_sr: Optional[int],
    config: PitchAnalysisConfig,
    *,
    reference_metadata: Optional[Dict[str, str]] = None,
) -> PitchAnalysisResult:
    if not config.get("enabled", False):
        return PitchAnalysisResult(
            version=PITCH_VERSION,
            reference_audio=_reference_payload(reference_metadata, config),
            pitch_accuracy=None,
        )

    if reference_audio is None or reference_sr is None:
        return PitchAnalysisResult(
            version=PITCH_VERSION,
            reference_audio=_reference_payload(reference_metadata, config, available=False),
            pitch_accuracy=None,
        )

    start_time = time.perf_counter()

    target_audio = np.asarray(target_audio, dtype=np.float32)
    reference_audio = np.asarray(reference_audio, dtype=np.float32)

    target_sr, reference_sr, target_audio, reference_audio = _ensure_same_sr(
        target_sr, reference_sr, target_audio, reference_audio, config
    )

    hop_length = config.get("hop_length") or 256
    fmin = config.get("fmin_hz") or librosa.note_to_hz("C2")
    fmax = config.get("fmax_hz") or librosa.note_to_hz("C7")

    target_times, target_cents = _estimate_pitch_series(
        target_audio, target_sr, hop_length, fmin, fmax, config
    )
    reference_times, reference_cents = _estimate_pitch_series(
        reference_audio, reference_sr, hop_length, fmin, fmax, config
    )

    target_filled = interpolate_nans(target_cents)
    reference_filled = interpolate_nans(reference_cents)

    aligned_target, alignment_info, aligned_reference, path = align_pitch_series(
        target_filled,
        reference_filled,
        target_times,
        reference_times,
        use_dtw=config.get("dtw_enabled", True),
        subseq=True,
        window=config.get("dtw_window"),
    )

    deviations = aligned_target - aligned_reference

    mean_dev, median_dev, hit_rate = compute_deviation_metrics(
        deviations,
        tolerance_cent=config.get("cent_tolerance", 50.0),
    )
    stability = compute_stability(deviations)

    per_section = _compute_section_metrics(
        path,
        target_times,
        deviations,
        section_length=config.get("section_length_sec", 30.0),
        tolerance=config.get("cent_tolerance", 50.0),
    )

    processing_time = time.perf_counter() - start_time

    reference_payload = _reference_payload(
        reference_metadata,
        config,
        duration=float(len(reference_audio) / reference_sr) if reference_sr else None,
        alignment=alignment_info,
        processing_time=processing_time,
    )

    accuracy = PitchAccuracyMetrics(
        mean_cent_deviation=mean_dev,
        median_cent_deviation=median_dev,
        hit_rate=hit_rate,
        stability=stability,
        samples=len(deviations),
        dtw_cost=alignment_info.dtw_cost,
        per_section=per_section,
    )

    return PitchAnalysisResult(
        version=PITCH_VERSION,
        reference_audio=reference_payload,
        pitch_accuracy=accuracy,
    )


def _ensure_same_sr(
    target_sr: int,
    reference_sr: int,
    target_audio: np.ndarray,
    reference_audio: np.ndarray,
    config: PitchAnalysisConfig,
) -> Tuple[int, int, np.ndarray, np.ndarray]:
    target_sr = int(target_sr)
    reference_sr = int(reference_sr)
    target_sr_out = target_sr
    reference_sr_out = reference_sr

    desired_sr = config.get("target_sr")
    if desired_sr:
        desired_sr = int(desired_sr)
    else:
        desired_sr = max(target_sr, reference_sr)

    if target_sr != desired_sr:
        target_audio = librosa.resample(target_audio, orig_sr=target_sr, target_sr=desired_sr)
        target_sr_out = desired_sr
    if reference_sr != desired_sr:
        reference_audio = librosa.resample(
            reference_audio, orig_sr=reference_sr, target_sr=desired_sr
        )
        reference_sr_out = desired_sr

    return target_sr_out, reference_sr_out, target_audio, reference_audio


def _estimate_pitch_series(
    audio: np.ndarray,
    sr: int,
    hop_length: int,
    fmin: float,
    fmax: float,
    config: PitchAnalysisConfig,
) -> Tuple[np.ndarray, np.ndarray]:
    pitches, voiced_flags, voiced_prob = librosa.pyin(
        audio,
        sr=sr,
        hop_length=hop_length,
        fmin=fmin,
        fmax=fmax,
    )

    times = librosa.frames_to_time(np.arange(len(pitches)), sr=sr, hop_length=hop_length)

    # pyin returns array of shape (frames,)
    confidence = voiced_prob if voiced_prob is not None else np.ones_like(pitches)
    min_conf = config.get("min_confidence", 0.6)

    pitches = np.where(confidence >= min_conf, pitches, np.nan)

    cents = hz_to_cents(pitches.astype(float))

    smoothing_ms = config.get("smoothing_ms", 80.0)
    if smoothing_ms and smoothing_ms > 0:
        window = int((smoothing_ms / 1000.0) * sr / hop_length)
        window = max(1, window)
        if window % 2 == 0:
            window += 1
        cents = smooth_series(cents, window)

    return times, cents


def _compute_section_metrics(
    path: np.ndarray,
    target_times: np.ndarray,
    deviations: np.ndarray,
    section_length: float,
    tolerance: float,
) -> list[PitchSectionMetrics]:
    if deviations.size == 0 or path.size == 0:
        return []

    section_length = max(section_length, 1.0)

    indexed_times = target_times[path[:, 0]]
    max_time = float(np.max(indexed_times))
    sections: list[PitchSectionMetrics] = []

    current_start = 0.0
    section_idx = 1
    while current_start < max_time:
        current_end = current_start + section_length
        mask = (indexed_times >= current_start) & (indexed_times < current_end)
        segment_devs = deviations[mask]
        if segment_devs.size:
            mean_dev, _, hit_rate = compute_deviation_metrics(
                segment_devs, tolerance_cent=tolerance
            )
            sections.append(
                PitchSectionMetrics(
                    section_id=f"section_{section_idx}",
                    start_s=current_start,
                    end_s=min(current_end, max_time),
                    mean_cent_deviation=mean_dev,
                    hit_rate=hit_rate,
                    sample_count=int(segment_devs.size),
                )
            )
        current_start += section_length
        section_idx += 1
    return sections


def _reference_payload(
    metadata: Optional[Dict[str, str]],
    config: PitchAnalysisConfig,
    *,
    available: bool = True,
    duration: Optional[float] = None,
    alignment: Optional[object] = None,
    processing_time: Optional[float] = None,
) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "reference_path": metadata.get("reference_path") if metadata else config.get("reference_file"),
        "available": available,
    }
    if duration is not None:
        payload["duration_sec"] = float(duration)
    if alignment is not None:
        payload["alignment"] = alignment.as_dict()  # type: ignore[assignment]
    if processing_time is not None:
        payload["analysis_time_sec"] = float(processing_time)
    return payload
