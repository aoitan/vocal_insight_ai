"""
セグメント機能パッケージ

音声セグメント検出と処理機能を提供
"""

from .detector import SegmentBoundaryDetector
from .processor import SegmentProcessor

__all__ = ["SegmentBoundaryDetector", "SegmentProcessor"]
