"""
セグメント処理器

検出された境界からセグメントを生成・調整
"""

import numpy as np
from typing import List, Tuple
from ..core.types import AnalysisConfig


class SegmentProcessor:
    """セグメント処理器クラス"""
    
    def process(
        self, 
        boundaries: np.ndarray, 
        total_duration: float, 
        config: AnalysisConfig
    ) -> List[Tuple[float, float]]:
        """境界情報からセグメントを生成・調整
        
        Args:
            boundaries: 検出された境界時刻（秒）
            total_duration: 音声の総再生時間（秒）
            config: 分析設定（最小・最大セグメント長）
            
        Returns:
            調整されたセグメント（開始時刻, 終了時刻）のリスト
        """
        # 境界に音声の開始・終了を追加
        all_boundaries = np.concatenate(([0], boundaries, [total_duration]))
        all_boundaries = np.unique(all_boundaries)  # 重複除去・ソート
        
        # 初期セグメントを生成
        segments = []
        for i in range(len(all_boundaries) - 1):
            start = all_boundaries[i]
            end = all_boundaries[i + 1]
            segments.append((start, end))
        
        # セグメント長制約を適用
        segments = self._apply_length_constraints(segments, config)
        
        return segments
    
    def _apply_length_constraints(
        self, 
        segments: List[Tuple[float, float]], 
        config: AnalysisConfig
    ) -> List[Tuple[float, float]]:
        """セグメント長制約を適用
        
        Args:
            segments: 初期セグメントリスト
            config: 分析設定
            
        Returns:
            制約適用後のセグメントリスト
        """
        min_len = config['min_len_sec']
        max_len = config['max_len_sec']
        
        adjusted_segments = []
        i = 0
        
        while i < len(segments):
            start, end = segments[i]
            length = end - start
            
            # 短すぎるセグメントの処理
            if length < min_len:
                # 次のセグメントと統合を試行
                merged_end = end
                j = i + 1
                
                while j < len(segments) and (merged_end - start) < min_len:
                    merged_end = segments[j][1]
                    j += 1
                
                adjusted_segments.append((start, merged_end))
                i = j
            
            # 長すぎるセグメントの処理
            elif length > max_len:
                # セグメントを分割
                current_start = start
                while (end - current_start) > max_len:
                    adjusted_segments.append((current_start, current_start + max_len))
                    current_start += max_len
                
                # 残りの部分
                if current_start < end:
                    adjusted_segments.append((current_start, end))
                
                i += 1
            
            # 適切な長さのセグメント
            else:
                adjusted_segments.append((start, end))
                i += 1
        
        return adjusted_segments