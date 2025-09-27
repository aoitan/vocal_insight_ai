"""
特徴量抽出器の基底クラス・プロトコル

拡張可能な特徴量抽出システムのためのインターフェイス定義
"""

from typing import Protocol

import numpy as np

from ..core.types import FeatureData


class FeatureExtractor(Protocol):
    """特徴量抽出器のプロトコル"""
    
    def extract(self, audio: np.ndarray, sr: int) -> FeatureData:
        """音声データから特徴量を抽出
        
        Args:
            audio: 音声データ
            sr: サンプリング周波数
            
        Returns:
            抽出された特徴量データ
        """
        ...