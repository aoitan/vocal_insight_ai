# ボーカル特徴量抽出パイプライン モジュール化設計

## 概要

`vocal_insight_ai.py` に集約されている特徴量抽出と分析パイプラインを、再利用性とテスト容易性を高めるために機能ごとにモジュール分割します。

## 設計原則

1. **単一責任の原則**: 各モジュールは明確な責任範囲を持つ
2. **依存関係の最小化**: モジュール間の結合度を低く保つ
3. **拡張性**: 新しい特徴量抽出機能を容易に追加できる
4. **テスト容易性**: 各モジュールが独立してテスト可能
5. **再利用性**: CLI、API、UIなど複数のクライアントで利用可能

## モジュール構造

```
vocal_insight/
├── __init__.py                 # 公開API
├── core/
│   ├── __init__.py
│   ├── types.py               # 共通型定義
│   └── config.py              # 設定管理
├── features/
│   ├── __init__.py
│   ├── base.py                # 特徴量抽出の基底クラス・プロトコル
│   ├── acoustic.py            # 音響特徴量抽出（f0, HNR, フォルマント）
│   └── temporal.py            # 時間的特徴量（セグメント境界検出）
├── segments/
│   ├── __init__.py
│   ├── detector.py            # セグメント境界検出
│   └── processor.py           # セグメント処理・統合
└── analysis/
    ├── __init__.py
    ├── pipeline.py            # 分析パイプライン統合
    └── formatter.py           # LLMプロンプト生成
```

## モジュール詳細

### vocal_insight.core

共通の型定義、設定、ユーティリティを提供。

**責務:**
- 型定義（FeatureData, SegmentAnalysis, AnalysisConfig）
- デフォルト設定の管理
- 共通例外クラス

### vocal_insight.features

特徴量抽出機能を提供。拡張可能な設計で新しい特徴量抽出器を追加可能。

**責務:**
- 音響特徴量抽出（基本周波数、HNR、フォルマント）
- 特徴量抽出器の基底クラス・プロトコル定義
- 将来的な特徴量追加のためのプラガブルな仕組み

### vocal_insight.segments

音声セグメント検出と処理を担当。

**責務:**
- RMS変化点によるセグメント境界検出
- セグメント長調整・統合処理
- セグメント品質評価

### vocal_insight.analysis

分析パイプライン全体の統合とフォーマット処理。

**責務:**
- セグメント検出から特徴量抽出までの統合処理
- LLMプロンプト生成
- 結果のフォーマット・集約

## 公開API設計

### メイン関数
```python
def analyze_audio_segments(
    audio_path: str, 
    config: Optional[AnalysisConfig] = None
) -> List[SegmentAnalysis]:
    """音声ファイルを分析してセグメント情報を返す"""
```

### モジュール別公開関数
```python
# vocal_insight.features
def extract_acoustic_features(audio_segment: np.ndarray, sr: int) -> FeatureData

# vocal_insight.segments  
def detect_segment_boundaries(audio: np.ndarray, sr: int, config: AnalysisConfig) -> np.ndarray
def process_segment_boundaries(boundaries: np.ndarray, duration: float, config: AnalysisConfig) -> List[Tuple[float, float]]

# vocal_insight.analysis
def generate_analysis_prompt(segments: List[SegmentAnalysis]) -> str
```

## 移行戦略

1. **Phase 1**: モジュール構造とテストの準備
   - パッケージ構造の作成
   - 型定義の移行
   - 基本テストフレームワークの確立

2. **Phase 2**: 機能移行
   - セグメント検出機能の移行
   - 特徴量抽出機能の移行
   - プロンプト生成機能の移行

3. **Phase 3**: 統合とリファクタリング
   - メインモジュールの更新
   - CLI インターフェースの調整
   - パフォーマンステストと最適化

## テスト戦略

- **ユニットテスト**: 各モジュールの個別機能
- **統合テスト**: モジュール間の連携
- **リグレッションテスト**: 既存機能の動作保証
- **パフォーマンステスト**: 処理時間とメモリ使用量

## 将来の拡張ポイント

1. **新しい特徴量抽出器**: `features` モジュールへのプラグイン追加
2. **異なるセグメント検出手法**: `segments` モジュールでの実装選択
3. **カスタム分析パイプライン**: `analysis` モジュールでのワークフロー定義
4. **出力フォーマット**: 様々なクライアント向けのフォーマッター追加