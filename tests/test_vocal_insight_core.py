"""
テスト仕様: vocal_insight.core モジュール

このテストファイルは、新しいモジュール構造における core パッケージの
型定義と設定管理機能のテスト仕様を定義します。

TDD Red Phase: 実装前のテスト記述
"""

import pytest

from vocal_insight.core.config import get_default_config, validate_config
from vocal_insight.core.types import AnalysisConfig, FeatureData, SegmentAnalysis


class TestCoreTypes:
    """コア型定義のテスト"""

    def test_feature_data_structure(self):
        """FeatureData型が正しい構造を持つことを確認"""
        # Given: 完全な特徴量データ
        feature_data = FeatureData(
            f0_mean_hz=150.0,
            f0_std_hz=25.0,
            hnr_mean_db=15.0,
            f1_mean_hz=500.0,
            f2_mean_hz=1500.0,
            f3_mean_hz=2500.0,
        )

        # When & Then: 全てのフィールドにアクセス可能
        assert feature_data["f0_mean_hz"] == 150.0
        assert feature_data["f0_std_hz"] == 25.0
        assert feature_data["hnr_mean_db"] == 15.0
        assert feature_data["f1_mean_hz"] == 500.0
        assert feature_data["f2_mean_hz"] == 1500.0
        assert feature_data["f3_mean_hz"] == 2500.0

    def test_segment_analysis_structure(self):
        """SegmentAnalysis型が正しい構造を持つことを確認"""
        # Given: セグメント分析データ
        features = FeatureData(
            f0_mean_hz=150.0,
            f0_std_hz=25.0,
            hnr_mean_db=15.0,
            f1_mean_hz=500.0,
            f2_mean_hz=1500.0,
            f3_mean_hz=2500.0,
        )
        segment = SegmentAnalysis(
            segment_id=1, time_start_s=0.0, time_end_s=10.0, features=features
        )

        # When & Then: 全てのフィールドにアクセス可能
        assert segment["segment_id"] == 1
        assert segment["time_start_s"] == 0.0
        assert segment["time_end_s"] == 10.0
        assert segment["features"]["f0_mean_hz"] == 150.0

    def test_analysis_config_structure(self):
        """AnalysisConfig型が正しい構造を持つことを確認"""
        # Given: 分析設定データ
        config = AnalysisConfig(
            rms_delta_percentile=95, min_len_sec=8.0, max_len_sec=45.0
        )

        # When & Then: 全てのフィールドにアクセス可能
        assert config["rms_delta_percentile"] == 95
        assert config["min_len_sec"] == 8.0
        assert config["max_len_sec"] == 45.0


class TestCoreConfig:
    """設定管理機能のテスト"""

    def test_get_default_config_returns_valid_config(self):
        """デフォルト設定が有効な値を返すことを確認"""
        # When: デフォルト設定を取得
        config = get_default_config()

        # Then: 期待される値が設定されている
        assert config["rms_delta_percentile"] == 95
        assert config["min_len_sec"] == 8.0
        assert config["max_len_sec"] == 45.0

    def test_validate_config_with_valid_config(self):
        """有効な設定の検証が成功することを確認"""
        # Given: 有効な設定
        valid_config = AnalysisConfig(
            rms_delta_percentile=95, min_len_sec=8.0, max_len_sec=45.0
        )

        # When & Then: 検証が成功する
        assert validate_config(valid_config) is True

    def test_validate_config_with_invalid_percentile(self):
        """無効なパーセンタイルで検証が失敗することを確認"""
        # Given: 無効なパーセンタイル値
        invalid_config = AnalysisConfig(
            rms_delta_percentile=101,  # 100を超える値は無効
            min_len_sec=8.0,
            max_len_sec=45.0,
        )

        # When & Then: 検証が失敗する
        with pytest.raises(
            ValueError, match="rms_delta_percentile must be between 0 and 100"
        ):
            validate_config(invalid_config)

    def test_validate_config_with_invalid_segment_length(self):
        """無効なセグメント長で検証が失敗することを確認"""
        # Given: 最小長が最大長より大きい無効な設定
        invalid_config = AnalysisConfig(
            rms_delta_percentile=95,
            min_len_sec=50.0,  # max_len_secより大きい
            max_len_sec=45.0,
        )

        # When & Then: 検証が失敗する
        with pytest.raises(
            ValueError, match="min_len_sec must be less than max_len_sec"
        ):
            validate_config(invalid_config)
