"""
特徴量抽出機能パッケージ

音響特徴量の抽出機能を提供
"""

from .acoustic import AcousticFeatureExtractor
from .base import FeatureExtractor

__all__ = ["FeatureExtractor", "AcousticFeatureExtractor"]
