"""
テスト仕様: vocal_insight.features モジュール

このテストファイルは、音響特徴量抽出機能の
テスト仕様を定義します。

TDD Red Phase: 実装前のテスト記述
"""
import numpy as np
import pytest
from vocal_insight.features.acoustic import AcousticFeatureExtractor
from vocal_insight.features.base import FeatureExtractor
from vocal_insight.core.types import FeatureData


class TestFeatureExtractorProtocol:
    """特徴量抽出器のプロトコル/基底クラステスト"""
    
    def test_feature_extractor_interface(self):
        """FeatureExtractorが正しいインターフェイスを持つことを確認"""
        # Given: FeatureExtractorプロトコル
        # Then: 必要なメソッドシグネチャが存在する
        import inspect
        assert hasattr(FeatureExtractor, 'extract')
        
        # AcousticFeatureExtractorがプロトコルを実装していることを確認
        extractor = AcousticFeatureExtractor()
        assert hasattr(extractor, 'extract')
        assert callable(extractor.extract)


class TestAcousticFeatureExtractor:
    """音響特徴量抽出器のテスト"""
    
    def test_extract_features_with_valid_audio(self):
        """有効な音声データから特徴量を抽出"""
        # Given: 有効な音声データとサンプリング周波数
        extractor = AcousticFeatureExtractor()
        # シンプルな正弦波のテストデータ
        duration = 1.0  # 1秒
        sr = 22050
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t)  # 440Hz の正弦波
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: FeatureData構造で結果が返される
        assert isinstance(features, dict)  # TypedDictはdictとして認識される
        
        # 必要なフィールドが存在する
        required_fields = ['f0_mean_hz', 'f0_std_hz', 'hnr_mean_db', 
                          'f1_mean_hz', 'f2_mean_hz', 'f3_mean_hz']
        for field in required_fields:
            assert field in features
            assert isinstance(features[field], (int, float))
            assert not np.isnan(features[field])
    
    def test_extract_features_f0_reasonable_range(self):
        """F0が合理的な範囲内であることを確認"""
        # Given: 既知の周波数の正弦波
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 2.0
        fundamental_freq = 200.0  # 200Hz
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * fundamental_freq * t)
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: F0が期待値に近い
        assert 150.0 <= features['f0_mean_hz'] <= 250.0  # ±50Hzの許容範囲
        assert features['f0_std_hz'] >= 0.0  # 標準偏差は非負
        
        # 人間の音声の一般的な範囲内
        assert 50.0 <= features['f0_mean_hz'] <= 500.0
    
    def test_extract_features_hnr_valid_range(self):
        """HNR（倍音対雑音比）が有効な範囲内であることを確認"""
        # Given: クリーンな正弦波（高HNR）
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 150 * t)  # 150Hzの正弦波
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: HNRが合理的な範囲内
        # 注意: 高品質な正弦波では非常に高いHNR値が得られる可能性がある
        assert -10.0 <= features['hnr_mean_db'] <= 100.0  # 拡張された範囲
    
    def test_extract_features_formants_reasonable_values(self):
        """フォルマント周波数が合理的な値であることを確認"""
        # Given: 音声に近いスペクトルを持つテストデータ
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        # 複数の周波数成分を持つ信号（音声に類似）
        audio = (np.sin(2 * np.pi * 120 * t) +     # F0
                0.5 * np.sin(2 * np.pi * 600 * t) + # F1近似
                0.3 * np.sin(2 * np.pi * 1200 * t) + # F2近似
                0.2 * np.sin(2 * np.pi * 2400 * t))  # F3近似
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: フォルマントが人間音声の一般的な範囲内
        assert 200.0 <= features['f1_mean_hz'] <= 1000.0   # F1の一般的範囲
        assert 800.0 <= features['f2_mean_hz'] <= 2500.0   # F2の一般的範囲
        assert 1500.0 <= features['f3_mean_hz'] <= 4000.0  # F3の一般的範囲
        
        # フォルマントの順序関係（F1 < F2 < F3）
        assert features['f1_mean_hz'] < features['f2_mean_hz']
        assert features['f2_mean_hz'] < features['f3_mean_hz']
    
    def test_extract_features_with_silent_audio(self):
        """無音データでの特徴量抽出"""
        # Given: 無音データ
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 1.0
        audio = np.zeros(int(sr * duration))
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: 全ての特徴量が数値として取得される
        # 無音でも NaN や None ではなく数値が返される
        for value in features.values():
            assert isinstance(value, (int, float))
            # F0は検出できない場合があるが、数値として返される
            # HNRは低い値になる可能性がある
            # フォルマントも検出困難だが、デフォルト値や推定値が返される
    
    def test_extract_features_with_noisy_audio(self):
        """ノイズのあるデータでの特徴量抽出"""
        # Given: ノイズのあるデータ
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        signal = np.sin(2 * np.pi * 150 * t)  # 基本信号
        noise = np.random.normal(0, 0.1, len(signal))  # ノイズ
        audio = signal + noise
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: ロバストに特徴量が抽出される
        assert isinstance(features, dict)
        for value in features.values():
            assert isinstance(value, (int, float))
            assert not np.isnan(value)
    
    def test_extract_features_consistent_results(self):
        """同じ入力に対して一貫した結果を返すことを確認"""
        # Given: 同じ音声データを2回用意
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 200 * t)
        
        # When: 2回特徴量抽出を実行
        features1 = extractor.extract(audio.copy(), sr)
        features2 = extractor.extract(audio.copy(), sr)
        
        # Then: 結果が一致する
        for key in features1.keys():
            assert abs(features1[key] - features2[key]) < 1e-6  # 数値誤差範囲内
    
    def test_extract_features_with_short_audio(self):
        """短い音声データでの特徴量抽出"""
        # Given: 非常に短い音声データ
        extractor = AcousticFeatureExtractor()
        sr = 22050
        duration = 0.1  # 100ms
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 200 * t)
        
        # When: 特徴量抽出を実行
        features = extractor.extract(audio, sr)
        
        # Then: エラーにならずに特徴量が返される
        assert isinstance(features, dict)
        # 短い音声でも全フィールドが存在する
        required_fields = ['f0_mean_hz', 'f0_std_hz', 'hnr_mean_db', 
                          'f1_mean_hz', 'f2_mean_hz', 'f3_mean_hz']
        for field in required_fields:
            assert field in features
    
    def test_extract_features_validates_input_types(self):
        """入力パラメータの型検証"""
        # Given: 特徴量抽出器
        extractor = AcousticFeatureExtractor()
        
        # When & Then: 不正な型でエラーが発生
        with pytest.raises(TypeError):
            extractor.extract("invalid_audio", 22050)  # 文字列は無効
        
        with pytest.raises(TypeError):
            extractor.extract(np.array([1, 2, 3]), "invalid_sr")  # srが文字列は無効