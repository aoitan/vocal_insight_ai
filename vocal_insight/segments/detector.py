"""
セグメント境界検出器

音声データからRMS変化点を検出してセグメント境界を特定
"""

import librosa
import numpy as np


class SegmentBoundaryDetector:
    """セグメント境界検出器クラス"""

    def detect(self, audio: np.ndarray, sr: int, percentile: int) -> np.ndarray:
        """音声データからセグメント境界を検出

        Args:
            audio: 音声データ
            sr: サンプリング周波数
            percentile: RMS変化点検出に使用するパーセンタイル

        Returns:
            検出された境界時刻（秒）の配列
        """
        if len(audio) == 0:
            return np.array([])

        # RMS特徴量を計算
        rms = librosa.feature.rms(y=audio)[0]

        # RMSの変化量を計算
        delta_rms = np.abs(np.diff(rms))

        if len(delta_rms) == 0:
            return np.array([])

        # 閾値以上の変化点を検出
        threshold = np.percentile(delta_rms, percentile)
        change_points_frames = np.where(delta_rms > threshold)[0]

        # フレーム番号を時間に変換
        boundaries_sec = librosa.frames_to_time(change_points_frames + 1, sr=sr)

        return boundaries_sec
