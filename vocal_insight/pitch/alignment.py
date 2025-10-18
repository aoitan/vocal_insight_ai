"""ピッチ系列の整合とDTWアライメント"""

from __future__ import annotations

from typing import Optional, Tuple

import librosa
import numpy as np

from .schemas import PitchAlignmentInfo


def align_pitch_series(
    target_cents: np.ndarray,
    reference_cents: np.ndarray,
    target_times: np.ndarray,
    reference_times: np.ndarray,
    *,
    use_dtw: bool = True,
    subseq: bool = True,
    window: Optional[int] = None,
) -> Tuple[np.ndarray, PitchAlignmentInfo, np.ndarray, np.ndarray]:
    """ピッチ系列を整列し、アライメント情報と整列済みペアを返す"""

    if target_cents.size == 0 or reference_cents.size == 0:
        empty = np.empty((0,), dtype=np.float64)
        info = PitchAlignmentInfo(
            method="empty",
            offset_seconds=0.0,
            dtw_cost=None,
            path_length=0,
            reference_start=0.0,
            target_start=0.0,
        )
        return empty, info, empty, empty

    if not use_dtw:
        length = min(target_cents.size, reference_cents.size)
        target_idx = np.arange(length)
        reference_idx = np.arange(length)
        aligned_target = target_cents[target_idx]
        aligned_reference = reference_cents[reference_idx]
        offset = float(target_times[0] - reference_times[0])
        info = PitchAlignmentInfo(
            method="synchronous",
            offset_seconds=offset,
            dtw_cost=None,
            path_length=length,
            reference_start=float(reference_times[0]),
            target_start=float(target_times[0]),
        )
        return aligned_target, info, aligned_reference, np.column_stack((target_idx, reference_idx))

    # DTW
    target_seq = target_cents[np.newaxis, :]
    reference_seq = reference_cents[np.newaxis, :]

    dtw_kwargs = {
        "metric": "euclidean",
        "subseq": subseq,
    }

    cost, paths = librosa.sequence.dtw(  # type: ignore[call-arg]
        target_seq,
        reference_seq,
        **dtw_kwargs,
    )

    wp = np.asarray(paths, dtype=int)
    # librosa returns path from end to start; reverse for chronological order
    wp = wp[::-1]
    aligned_target = target_cents[wp[:, 0]]
    aligned_reference = reference_cents[wp[:, 1]]

    offset = float(target_times[wp[0, 0]] - reference_times[wp[0, 1]])
    info = PitchAlignmentInfo(
        method="dtw",
        offset_seconds=offset,
        dtw_cost=float(cost[wp[-1, 0], wp[-1, 1]]) if cost.size else None,
        path_length=int(len(wp)),
        reference_start=float(reference_times[wp[0, 1]]),
        target_start=float(target_times[wp[0, 0]]),
    )
    return aligned_target, info, aligned_reference, wp
