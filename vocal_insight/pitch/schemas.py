"""音程判定結果用のスキーマ定義"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PitchAlignmentInfo:
    method: str
    offset_seconds: float
    dtw_cost: Optional[float]
    path_length: int
    reference_start: float
    target_start: float
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "method": self.method,
            "offset_seconds": float(self.offset_seconds),
            "path_length": int(self.path_length),
            "reference_start_s": float(self.reference_start),
            "target_start_s": float(self.target_start),
        }
        if self.dtw_cost is not None:
            payload["dtw_cost"] = float(self.dtw_cost)
        if self.extra:
            payload["extra"] = self.extra
        return payload


@dataclass
class PitchSectionMetrics:
    section_id: str
    start_s: float
    end_s: float
    mean_cent_deviation: float
    hit_rate: float
    sample_count: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "start_s": float(self.start_s),
            "end_s": float(self.end_s),
            "cent_deviation": float(self.mean_cent_deviation),
            "hit_rate": float(self.hit_rate),
            "sample_count": int(self.sample_count),
        }


@dataclass
class PitchAccuracyMetrics:
    mean_cent_deviation: float
    median_cent_deviation: float
    hit_rate: float
    stability: float
    samples: int
    dtw_cost: Optional[float]
    per_section: List[PitchSectionMetrics] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "mean_cent_deviation": float(self.mean_cent_deviation),
            "median_cent_deviation": float(self.median_cent_deviation),
            "hit_rate": float(self.hit_rate),
            "stability": float(self.stability),
            "samples": int(self.samples),
        }
        if self.dtw_cost is not None:
            payload["dtw_cost"] = float(self.dtw_cost)
        if self.per_section:
            payload["per_section"] = [section.as_dict() for section in self.per_section]
        return payload


@dataclass
class PitchAnalysisResult:
    version: str
    reference_audio: Dict[str, Any]
    pitch_accuracy: Optional[PitchAccuracyMetrics]
    expression_comparison: Dict[str, Any] = field(default_factory=lambda: {
        "vibrato": None,
        "dynamics": None,
        "notes": [],
    })

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "version": self.version,
            "reference_audio": self.reference_audio,
            "expression_comparison": self.expression_comparison,
        }
        if self.pitch_accuracy is not None:
            payload["pitch_accuracy"] = self.pitch_accuracy.as_dict()
        else:
            payload["pitch_accuracy"] = None
        return payload
