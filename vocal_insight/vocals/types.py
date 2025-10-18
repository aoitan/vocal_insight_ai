"""リファレンスボーカル抽出結果の型定義"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np


@dataclass
class ReferenceVocalMetrics:
    """抽出品質を示すメトリクス"""

    snr_db: float
    pitch_track_coverage: float
    residual_energy_ratio: float

    def as_dict(self) -> dict[str, float]:
        return {
            "snr_db": float(self.snr_db),
            "pitch_track_coverage": float(self.pitch_track_coverage),
            "residual_energy_ratio": float(self.residual_energy_ratio),
        }


@dataclass
class ReferenceVocalExtractionResult:
    """リファレンスボーカル抽出の結果"""

    audio: np.ndarray
    sample_rate: int
    source_path: Optional[Path] = None
    output_path: Optional[Path] = None
    cache_path: Optional[Path] = None
    metadata_path: Optional[Path] = None
    model_type: str = "hpss"
    metrics: Optional[ReferenceVocalMetrics] = None
    processed_at: datetime = field(default_factory=lambda: datetime.utcnow())
    processing_time_sec: float = 0.0

    def metadata(self) -> dict[str, Any]:
        """メタデータを辞書形式で取得"""

        data: dict[str, Any] = {
            "model_type": self.model_type,
            "sample_rate": self.sample_rate,
            "processed_at": self.processed_at.replace(tzinfo=None).isoformat() + "Z",
            "processing_time_sec": float(self.processing_time_sec),
            "duration_sec": float(len(self.audio) / self.sample_rate)
            if self.sample_rate
            else 0.0,
        }
        if self.source_path:
            data["source_path"] = str(self.source_path)
        if self.output_path:
            data["output_path"] = str(self.output_path)
        if self.cache_path:
            data["cache_path"] = str(self.cache_path)
        if self.metadata_path:
            data["metadata_path"] = str(self.metadata_path)
        if self.metrics:
            data["metrics"] = self.metrics.as_dict()
        return data
