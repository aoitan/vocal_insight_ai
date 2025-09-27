"""
音響特徴量抽出器

音声データから基本周波数、HNR、フォルマント周波数を抽出
"""

import numpy as np
import parselmouth

from ..core.types import FeatureData


class AcousticFeatureExtractor:
    """音響特徴量抽出器クラス"""
    
    def extract(self, audio: np.ndarray, sr: int) -> FeatureData:
        """音声データから音響特徴量を抽出
        
        Args:
            audio: 音声データ
            sr: サンプリング周波数
            
        Returns:
            抽出された音響特徴量
            
        Raises:
            TypeError: 入力パラメータの型が不正な場合
        """
        # 入力型検証
        if not isinstance(audio, np.ndarray):
            raise TypeError("audio must be a numpy array")
        if not isinstance(sr, (int, float)):
            raise TypeError("sr must be a number")
            
        # Parselmouthオブジェクトを作成
        sound = parselmouth.Sound(audio, sampling_frequency=sr)
        
        # 基本周波数（F0）抽出
        f0_values = self._extract_f0(sound)
        
        # HNR（調和対雑音比）抽出  
        hnr_value = self._extract_hnr(sound)
        
        # フォルマント周波数抽出
        formants = self._extract_formants(sound)
        
        return FeatureData(
            f0_mean_hz=f0_values['mean'],
            f0_std_hz=f0_values['std'],
            hnr_mean_db=hnr_value,
            f1_mean_hz=formants['f1'],
            f2_mean_hz=formants['f2'],
            f3_mean_hz=formants['f3']
        )
    
    def _extract_f0(self, sound: parselmouth.Sound) -> dict:
        """基本周波数を抽出"""
        try:
            pitch = sound.to_pitch()
            f0_values = pitch.selected_array['frequency']
            # 無効値（0）を除去
            valid_f0 = f0_values[f0_values > 0]
            
            if len(valid_f0) > 0:
                return {
                    'mean': float(np.mean(valid_f0)),
                    'std': float(np.std(valid_f0))
                }
            else:
                # 検出できない場合のデフォルト値
                return {'mean': 120.0, 'std': 0.0}
                
        except Exception:
            # エラー時のデフォルト値
            return {'mean': 120.0, 'std': 0.0}
    
    def _extract_hnr(self, sound: parselmouth.Sound) -> float:
        """調和対雑音比を抽出"""
        try:
            harmonicity = sound.to_harmonicity()
            hnr_values = harmonicity.values[harmonicity.values != -200]  # 無効値除去
            
            if len(hnr_values) > 0:
                return float(np.mean(hnr_values))
            else:
                return 10.0  # デフォルト値
                
        except Exception:
            return 10.0  # エラー時のデフォルト値
    
    def _extract_formants(self, sound: parselmouth.Sound) -> dict:
        """フォルマント周波数を抽出"""
        try:
            formants = sound.to_formant_burg()
            
            # 時間軸全体での平均を計算
            f1_values = []
            f2_values = []
            f3_values = []
            
            for i in range(formants.get_number_of_frames()):
                try:
                    frame_time = formants.get_time_from_frame_number(i + 1)
                    f1 = formants.get_value_at_time(1, frame_time)
                    f2 = formants.get_value_at_time(2, frame_time)
                    f3 = formants.get_value_at_time(3, frame_time)
                    
                    # 有効な値のみ追加
                    if not np.isnan(f1) and f1 > 0:
                        f1_values.append(f1)
                    if not np.isnan(f2) and f2 > 0:
                        f2_values.append(f2)
                    if not np.isnan(f3) and f3 > 0:
                        f3_values.append(f3)
                        
                except Exception:
                    continue
            
            return {
                'f1': float(np.mean(f1_values)) if f1_values else 500.0,
                'f2': float(np.mean(f2_values)) if f2_values else 1500.0,
                'f3': float(np.mean(f3_values)) if f3_values else 2500.0
            }
            
        except Exception:
            # エラー時のデフォルト値（典型的なフォルマント値）
            return {
                'f1': 500.0,
                'f2': 1500.0,
                'f3': 2500.0
            }