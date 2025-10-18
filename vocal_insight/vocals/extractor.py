"""リファレンスボーカル抽出ロジック"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from ..core.types import ReferenceVocalExtractionConfig
from .loader import ensure_directory, load_audio, resolve_path
from .metrics import (
    compute_pitch_track_coverage,
    compute_residual_energy_ratio,
    compute_snr_db,
)
from .postprocess import ensure_mono, normalize_audio, resample_audio, trim_silence
from .protocols import VocalSeparatorProtocol
from .separators import get_separator
from .types import ReferenceVocalExtractionResult, ReferenceVocalMetrics


class ReferenceVocalExtractor:
    """リファレンスボーカルを抽出するクラス"""

    def __init__(self, config: Optional[ReferenceVocalExtractionConfig] = None):
        self.config: ReferenceVocalExtractionConfig = config or {}
        self.model_type = str(self.config.get("model_type", "hpss")).lower()
        self.config["model_type"] = self.model_type
        self._separator: VocalSeparatorProtocol | None = None

        model_path = self.config.get("model_path")
        if model_path:
            path = resolve_path(model_path)
            if path and not path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")

    def extract_from_path(
        self,
        source: str | Path,
        *,
        output_dir: str | Path | None = None,
    ) -> ReferenceVocalExtractionResult:
        resolved_source = resolve_path(source)
        source_str = str(resolved_source) if resolved_source else str(source)

        audio, sr = load_audio(
            source,
            target_sr=self.config.get("target_sr"),
            mono=False,
        )
        return self.extract(audio, sr, source_path=source_str, output_dir=output_dir)

    def extract(
        self,
        audio: np.ndarray,
        sample_rate: int,
        *,
        source_path: str | None = None,
        output_dir: str | Path | None = None,
    ) -> ReferenceVocalExtractionResult:
        preprocessed, sr = self._preprocess(audio, sample_rate)

        output_base = self._resolve_output_dir(output_dir, source_path)
        output_path = self._build_output_path(output_base, source_path)
        cache_dir = resolve_path(self.config.get("cache_dir"))
        metadata_path = self._resolve_metadata_path(output_path, cache_dir, source_path)

        if (
            output_path
            and output_path.exists()
            and self.config.get("reuse_existing", True)
            and not self.config.get("overwrite", False)
        ):
            return self._load_cached_result(output_path, metadata_path, source_path, cache_dir)

        start_time = time.perf_counter()

        vocal_raw, residual = self._separate(preprocessed, sr)
        vocal_out = vocal_raw

        if self.config.get("trim_silence", True):
            trimmed, _ = trim_silence(vocal_out, sr)
            if trimmed.size > 0:
                vocal_out = trimmed

        vocal_out = normalize_audio(vocal_out.astype(np.float32))

        metrics = None
        if self.config.get("quality_metrics", True):
            metrics = ReferenceVocalMetrics(
                snr_db=compute_snr_db(vocal_raw, residual),
                pitch_track_coverage=compute_pitch_track_coverage(vocal_out, sr),
                residual_energy_ratio=compute_residual_energy_ratio(vocal_raw, residual),
            )

        processing_time = time.perf_counter() - start_time

        cache_path = self._persist_outputs(vocal_out, sr, output_path, cache_dir, source_path)
        result = ReferenceVocalExtractionResult(
            audio=vocal_out,
            sample_rate=sr,
            source_path=Path(source_path) if source_path else None,
            output_path=output_path,
            cache_path=cache_path,
            metadata_path=metadata_path,
            model_type=self.model_type,
            metrics=metrics,
            processing_time_sec=float(processing_time),
        )

        if metadata_path:
            self._save_metadata(metadata_path, result)

        return result

    def _preprocess(self, audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, int]:
        mono = ensure_mono(audio)
        resampled, sr = resample_audio(mono, sample_rate, self.config.get("target_sr"))
        return resampled.astype(np.float32), sr

    def _get_separator(self) -> VocalSeparatorProtocol:
        if self._separator is None:
            self._separator = get_separator(self.model_type, self.config)
        return self._separator

    def _separate(self, audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
        separator = self._get_separator()
        return separator.separate(audio, sample_rate)

    def _resolve_output_dir(
        self,
        output_dir: str | Path | None,
        source_path: str | None,
    ) -> Path | None:
        target = resolve_path(output_dir) if output_dir else None
        if target is None:
            config_path = self.config.get("output_dir") or self.config.get("cache_dir")
            target = resolve_path(config_path)
        if target is None and source_path:
            target = Path(source_path).parent / "reference"
        if target is None:
            return None
        return ensure_directory(target)

    def _build_output_path(self, base_dir: Path | None, source_path: str | None) -> Path | None:
        if not self.config.get("save_audio", True):
            return None
        if base_dir is None and source_path is None:
            base_dir = ensure_directory(Path.cwd() / "output" / "reference")
        elif base_dir is None:
            base_dir = ensure_directory(Path(source_path).parent / "reference")
        filename = "reference_vocals.wav"
        if source_path:
            filename = f"{Path(source_path).stem}_reference_vocals.wav"
        return base_dir / filename if base_dir else None

    def _resolve_metadata_path(
        self,
        output_path: Path | None,
        cache_dir: Path | None,
        source_path: str | None,
    ) -> Path | None:
        if output_path is not None:
            return output_path.with_suffix(".json")
        if cache_dir is not None:
            ensure_directory(cache_dir)
            base = Path(source_path).stem if source_path else "reference"
            return cache_dir / f"{base}_reference_vocals.json"
        return None

    def _persist_outputs(
        self,
        vocal: np.ndarray,
        sample_rate: int,
        output_path: Path | None,
        cache_dir: Path | None,
        source_path: str | None,
    ) -> Path | None:
        cache_path = None

        if output_path:
            ensure_directory(output_path.parent)
            sf.write(output_path, vocal, sample_rate)

        if cache_dir:
            ensure_directory(cache_dir)
            base_stem = "reference"
            if output_path:
                base_stem = output_path.stem
            elif source_path:
                base_stem = Path(source_path).stem
            cache_path = cache_dir / f"{base_stem}_vocal.npy"
            np.save(cache_path, vocal)

        return cache_path

    def _save_metadata(self, metadata_path: Path, result: ReferenceVocalExtractionResult) -> None:
        ensure_directory(metadata_path.parent)
        metadata = result.metadata()
        metadata["config"] = {
            key: value
            for key, value in self.config.items()
            if key
            not in {
                "model_path",
            }
        }
        metadata["processed_at"] = datetime.utcnow().replace(tzinfo=None).isoformat() + "Z"
        with metadata_path.open("w", encoding="utf-8") as fp:
            json.dump(metadata, fp, ensure_ascii=False, indent=2)

    def _load_cached_result(
        self,
        audio_path: Path,
        metadata_path: Path | None,
        source_path: str | None,
        cache_dir: Path | None,
    ) -> ReferenceVocalExtractionResult:
        audio, sr = load_audio(audio_path, target_sr=self.config.get("target_sr"))
        metrics = None
        processed_at = datetime.utcnow()
        processing_time = 0.0
        cache_path = None

        if cache_dir:
            candidate = cache_dir / f"{audio_path.stem}_vocal.npy"
            if candidate.exists():
                cache_path = candidate

        if metadata_path and metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            metrics_payload = data.get("metrics")
            if metrics_payload:
                metrics = ReferenceVocalMetrics(
                    snr_db=float(metrics_payload.get("snr_db", 0.0)),
                    pitch_track_coverage=float(metrics_payload.get("pitch_track_coverage", 0.0)),
                    residual_energy_ratio=float(metrics_payload.get("residual_energy_ratio", 0.0)),
                )
            timestamp = data.get("processed_at")
            if isinstance(timestamp, str):
                try:
                    processed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    processed_at = datetime.utcnow()
            processing_time = float(data.get("processing_time_sec", 0.0))

        return ReferenceVocalExtractionResult(
            audio=audio,
            sample_rate=sr,
            source_path=Path(source_path) if source_path else None,
            output_path=audio_path,
            cache_path=cache_path,
            metadata_path=metadata_path,
            model_type=self.model_type,
            metrics=metrics,
            processed_at=processed_at,
            processing_time_sec=processing_time,
        )


def extract_reference_vocals(
    source: str | Path,
    config: Optional[ReferenceVocalExtractionConfig] = None,
    *,
    output_dir: str | Path | None = None,
) -> ReferenceVocalExtractionResult:
    extractor = ReferenceVocalExtractor(config)
    return extractor.extract_from_path(source, output_dir=output_dir)
