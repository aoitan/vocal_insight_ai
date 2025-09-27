"""
テスト仕様: vocal_insight.segments モジュール

このテストファイルは、音声セグメント検出と処理機能の
テスト仕様を定義します。

TDD Red Phase: 実装前のテスト記述
"""
import numpy as np
import pytest
from vocal_insight.segments.detector import SegmentBoundaryDetector
from vocal_insight.segments.processor import SegmentProcessor
from vocal_insight.core.types import AnalysisConfig


class TestSegmentBoundaryDetector:
    """セグメント境界検出機能のテスト"""
    
    def test_detect_boundaries_with_empty_audio(self):
        """空の音声データでの境界検出"""
        # Given: 空の音声データ
        detector = SegmentBoundaryDetector()
        empty_audio = np.array([])
        sr = 22050
        percentile = 95
        
        # When: 境界検出を実行
        boundaries = detector.detect(empty_audio, sr, percentile)
        
        # Then: 空の配列が返される
        assert len(boundaries) == 0
        assert isinstance(boundaries, np.ndarray)
    
    def test_detect_boundaries_with_uniform_audio(self):
        """一様な音声データでの境界検出"""
        # Given: 一様な音声データ（変化点なし）
        detector = SegmentBoundaryDetector()
        uniform_audio = np.ones(22050)  # 1秒分の一様音声
        sr = 22050
        percentile = 95
        
        # When: 境界検出を実行
        boundaries = detector.detect(uniform_audio, sr, percentile)
        
        # Then: 境界が検出されない（またはごく少ない）
        # Note: 実際にはRMS計算の枠組みで少数の境界が検出される可能性がある
        assert len(boundaries) <= 5  # 一様データでは境界は少ない
    
    def test_detect_boundaries_with_changing_audio(self):
        """変化のある音声データでの境界検出"""
        # Given: 明確な変化点を持つ音声データ
        detector = SegmentBoundaryDetector()
        # 前半静寂、後半高音量のシンプルなテストデータ
        silent_part = np.zeros(11025)
        loud_part = np.ones(11025) * 0.8
        changing_audio = np.concatenate([silent_part, loud_part])
        sr = 22050
        percentile = 90
        
        # When: 境界検出を実行
        boundaries = detector.detect(changing_audio, sr, percentile)
        
        # Then: 変化点付近に境界が検出される
        assert len(boundaries) > 0
        # 変化点は0.5秒付近に存在するはず
        assert any(0.4 <= boundary <= 0.6 for boundary in boundaries)
    
    def test_detect_boundaries_returns_time_values(self):
        """境界検出結果が時間値（秒）で返されることを確認"""
        # Given: テスト音声データ
        detector = SegmentBoundaryDetector()
        test_audio = np.random.random(44100)  # 2秒分
        sr = 22050
        percentile = 95
        
        # When: 境界検出を実行
        boundaries = detector.detect(test_audio, sr, percentile)
        
        # Then: 結果は時間値（0以上、音声長以下）
        audio_duration = len(test_audio) / sr
        assert all(0 <= boundary <= audio_duration for boundary in boundaries)


class TestSegmentProcessor:
    """セグメント処理機能のテスト"""
    
    def test_process_boundaries_empty_input(self):
        """空の境界データの処理"""
        # Given: 空の境界データ
        processor = SegmentProcessor()
        boundaries = np.array([])
        total_duration = 60.0
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: 音声が最大長制約に従って分割される
        # 60秒は max_len_sec(45秒)より長いため分割される
        assert len(segments) >= 1
        # 全てのセグメントが最大長以下
        for start, end in segments:
            assert (end - start) <= config['max_len_sec']
    
    def test_process_boundaries_single_boundary(self):
        """単一境界での処理"""
        # Given: 1つの境界
        processor = SegmentProcessor()
        boundaries = np.array([30.0])
        total_duration = 60.0
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: 2つのセグメントが生成される
        assert len(segments) == 2
        assert segments[0] == (0.0, 30.0)
        assert segments[1] == (30.0, 60.0)
    
    def test_process_boundaries_respects_min_length(self):
        """最小長制約の遵守"""
        # Given: 短すぎるセグメントを生成する境界
        processor = SegmentProcessor()
        boundaries = np.array([5.0, 15.0])  # 最初のセグメントが5秒（min_len未満）
        total_duration = 30.0
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: 全てのセグメントが最小長以上
        for start, end in segments:
            assert (end - start) >= config['min_len_sec']
    
    def test_process_boundaries_respects_max_length(self):
        """最大長制約の遵守"""
        # Given: 長すぎるセグメントになる設定
        processor = SegmentProcessor()
        boundaries = np.array([])  # 境界なし -> 全体が1セグメント
        total_duration = 120.0  # 2分（max_lenより長い）
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: 全てのセグメントが最大長以下
        for start, end in segments:
            assert (end - start) <= config['max_len_sec']
    
    def test_process_boundaries_complete_coverage(self):
        """セグメントが音声全体をカバーすることを確認"""
        # Given: 複数の境界
        processor = SegmentProcessor()
        boundaries = np.array([20.0, 40.0, 80.0])
        total_duration = 100.0
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: 
        # 1. セグメントが音声全体をカバー
        segments_sorted = sorted(segments)
        assert segments_sorted[0][0] == 0.0
        assert segments_sorted[-1][1] == total_duration
        
        # 2. セグメント間に隙間がない
        for i in range(len(segments_sorted) - 1):
            assert segments_sorted[i][1] == segments_sorted[i + 1][0]
    
    def test_process_boundaries_no_overlaps(self):
        """セグメント間に重複がないことを確認"""
        # Given: 複数の境界
        processor = SegmentProcessor()
        boundaries = np.array([15.0, 35.0, 55.0])
        total_duration = 70.0
        config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=8.0,
            max_len_sec=45.0
        )
        
        # When: 境界処理を実行
        segments = processor.process(boundaries, total_duration, config)
        
        # Then: セグメント間に重複がない
        segments_sorted = sorted(segments)
        for i in range(len(segments_sorted) - 1):
            assert segments_sorted[i][1] <= segments_sorted[i + 1][0]