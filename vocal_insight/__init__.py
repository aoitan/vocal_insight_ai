"""
vocal_insight パッケージ

ボーカル特徴量抽出と分析のための統合パッケージ
"""

from .analysis.pipeline import analyze_audio_segments
from .core.types import (
    AnalysisConfig,
    FeatureData,
    PitchAnalysisConfig,
    ReferenceVocalExtractionConfig,
    SegmentAnalysis,
)
from .pitch import (
    PitchAccuracyMetrics,
    PitchAlignmentInfo,
    PitchAnalysisResult,
    analyze_pitch_accuracy,
    analyze_pitch_accuracy_from_files,
)
from .vocals import (
    ReferenceVocalExtractionResult,
    ReferenceVocalExtractor,
    ReferenceVocalMetrics,
    extract_reference_vocals,
)

__version__ = "0.1.0"
__all__ = [
    "analyze_audio_segments",
    "FeatureData",
    "SegmentAnalysis",
    "AnalysisConfig",
    "PitchAnalysisConfig",
    "ReferenceVocalExtractionConfig",
    "ReferenceVocalExtractionResult",
    "ReferenceVocalExtractor",
    "ReferenceVocalMetrics",
    "extract_reference_vocals",
    "PitchAnalysisResult",
    "PitchAccuracyMetrics",
    "PitchAlignmentInfo",
    "analyze_pitch_accuracy",
    "analyze_pitch_accuracy_from_files",
]
