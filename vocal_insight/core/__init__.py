"""
コア機能パッケージ

共通型定義、設定管理、ユーティリティを提供
"""

from .types import FeatureData, SegmentAnalysis, AnalysisConfig
from .config import get_default_config, validate_config

__all__ = [
    "FeatureData",
    "SegmentAnalysis", 
    "AnalysisConfig",
    "get_default_config",
    "validate_config"
]