"""
特徴量抽出機能パッケージ

音響特徴量の抽出機能を提供
"""

from .base import FeatureExtractor
from .acoustic import AcousticFeatureExtractor

__all__ = [
    "FeatureExtractor",
    "AcousticFeatureExtractor"
]