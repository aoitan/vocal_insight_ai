"""
vocal_insight パッケージ

ボーカル特徴量抽出と分析のための統合パッケージ
"""

from .analysis.pipeline import analyze_audio_segments
from .core.types import FeatureData, SegmentAnalysis, AnalysisConfig

__version__ = "0.1.0"
__all__ = [
    "analyze_audio_segments",
    "FeatureData",
    "SegmentAnalysis", 
    "AnalysisConfig"
]