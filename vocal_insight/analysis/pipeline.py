"""
分析パイプライン

セグメント検出から特徴量抽出までの統合処理
"""

from typing import List, Optional
import librosa
from ..core.types import SegmentAnalysis, AnalysisConfig
from ..core.config import get_default_config
from ..segments.detector import SegmentBoundaryDetector
from ..segments.processor import SegmentProcessor
from ..features.acoustic import AcousticFeatureExtractor


def analyze_audio_segments(
    audio_path: str, 
    config: Optional[AnalysisConfig] = None
) -> List[SegmentAnalysis]:
    """音声ファイルを分析してセグメント情報を返す
    
    Args:
        audio_path: 音声ファイルのパス
        config: 分析設定（省略時はデフォルト）
        
    Returns:
        セグメント分析結果のリスト
    """
    if config is None:
        config = get_default_config()
    
    # 音声ファイルを読み込み
    audio, sr = librosa.load(audio_path)
    total_duration = len(audio) / sr
    
    # セグメント境界検出
    detector = SegmentBoundaryDetector()
    boundaries = detector.detect(audio, sr, config['rms_delta_percentile'])
    
    # セグメント処理
    processor = SegmentProcessor()
    segments = processor.process(boundaries, total_duration, config)
    
    # 各セグメントから特徴量抽出
    extractor = AcousticFeatureExtractor()
    results = []
    
    for segment_id, (start_sec, end_sec) in enumerate(segments):
        # セグメント音声を抽出
        start_frame = int(start_sec * sr)
        end_frame = int(end_sec * sr)
        segment_audio = audio[start_frame:end_frame]
        
        # 特徴量抽出
        features = extractor.extract(segment_audio, sr)
        
        # 結果作成
        segment_analysis = SegmentAnalysis(
            segment_id=segment_id,
            time_start_s=start_sec,
            time_end_s=end_sec,
            features=features
        )
        
        results.append(segment_analysis)
    
    return results