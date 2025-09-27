"""
設定管理モジュール

デフォルト設定と設定の検証機能を提供
"""

from .types import AnalysisConfig


def get_default_config() -> AnalysisConfig:
    """デフォルト分析設定を取得
    
    Returns:
        デフォルトの分析設定
    """
    return AnalysisConfig(
        rms_delta_percentile=95,
        min_len_sec=8.0,
        max_len_sec=45.0
    )


def validate_config(config: AnalysisConfig) -> bool:
    """分析設定の検証
    
    Args:
        config: 検証対象の設定
        
    Returns:
        設定が有効な場合True
        
    Raises:
        ValueError: 設定が無効な場合
    """
    if not (0 <= config['rms_delta_percentile'] <= 100):
        raise ValueError("rms_delta_percentile must be between 0 and 100")
    
    if config['min_len_sec'] < 0:
        raise ValueError("min_len_sec must be positive")
    
    if config['max_len_sec'] < 0:
        raise ValueError("max_len_sec must be positive")
        
    if config['min_len_sec'] >= config['max_len_sec']:
        raise ValueError("min_len_sec must be less than max_len_sec")
    
    return True