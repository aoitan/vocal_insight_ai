# CLI ユースケース分析と移行戦略

## ユーザータイプ別ユースケース

### 1. 一般ユーザー（既存ユーザー）

**特徴:**
- 現在のCLIを使用中
- 基本的な音声分析が目的
- コマンドライン操作に慣れている

**ニーズ:**
- 既存コマンドの互換性維持
- シンプルな操作
- 安定した結果

**提案コマンド:**
```bash
# 現在（変更なし）
vocal-insight analyze input.wav

# 将来のオプション
vocal-insight analyze input.wav --format json  # 構造化データ
vocal-insight analyze input.wav --verbose      # 詳細情報
```

### 2. 研究者・開発者

**特徴:**
- 詳細な分析データが必要
- カスタムパラメータでの実験
- 自動化・バッチ処理

**ニーズ:**
- 柔軟なパラメータ調整
- 構造化データ出力
- 部分的な機能利用

**提案コマンド:**
```bash
# 詳細設定での分析
vocal-insight analyze input.wav \
  --min-segment 5.0 --max-segment 30.0 \
  --percentile 90 --format json

# 特徴量のみ抽出
vocal-insight extract input.wav --format csv

# セグメント検出のみ
vocal-insight segment input.wav --plot
```

### 3. システム統合ユーザー

**特徴:**
- CLIを他システムから呼び出し
- バッチ処理・自動化
- プログラマティックな利用

**ニーズ:**
- 機械可読な出力形式
- エラーハンドリング
- 静音モード

**提案コマンド:**
```bash
# バッチ処理向け
vocal-insight --quiet analyze input.wav --format json --output-dir ./batch_results

# エラーチェック付き
vocal-insight analyze input.wav || handle_error

# 構造化ログ
vocal-insight --verbose analyze input.wav 2>&1 | parse_logs
```

### 4. 教育・学習ユーザー

**特徴:**
- 音声分析の学習目的
- ステップバイステップでの理解
- 可視化が重要

**ニーズ:**
- 段階的な機能利用
- 視覚的フィードバック
- 教育的な出力

**提案コマンド:**
```bash
# ステップバイステップ分析
vocal-insight segment input.wav --plot                    # 1. セグメント検出
vocal-insight extract input.wav --format csv             # 2. 特徴量抽出
vocal-insight analyze input.wav --verbose               # 3. 統合分析

# 学習用の詳細出力
vocal-insight examples                                   # 使用例
vocal-insight info                                      # システム情報
```

## 移行シナリオ

### シナリオ1: 既存ユーザーの継続利用

**状況:** 現在のworkflowを維持したい

**移行パス:**
1. **Phase 1**: 既存コマンドをそのまま使用（内部で新モジュール使用）
2. **Phase 2**: オプション機能（`--format json`など）の段階的採用
3. **Phase 3**: 完全移行（レガシーモード廃止後）

**推奨アプローチ:**
```bash
# Phase 1: 変更不要
vocal-insight analyze input.wav

# Phase 2: 新機能の試用
vocal-insight analyze input.wav --format json
vocal-insight analyze input.wav --verbose

# Phase 3: 新機能の活用
vocal-insight analyze input.wav --module acoustic --format yaml
```

### シナリオ2: 高度な機能の段階的導入

**状況:** より詳細な分析が必要になった

**移行パス:**
1. **Phase 1**: 既存の`analyze`コマンドで出力形式をJSONに変更
2. **Phase 2**: `extract`・`segment`コマンドで部分機能を活用
3. **Phase 3**: カスタムパラメータで最適化

**推奨アプローチ:**
```bash
# Phase 1: 構造化データの取得
vocal-insight analyze input.wav --format json

# Phase 2: 部分機能の活用
vocal-insight extract input.wav --format csv
vocal-insight segment input.wav --plot

# Phase 3: 最適化
vocal-insight analyze input.wav --min-segment 5.0 --percentile 90
```

### シナリオ3: システム統合での採用

**状況:** 他システムからの呼び出し・自動化

**移行パス:**
1. **Phase 1**: 既存統合の動作確認
2. **Phase 2**: JSON出力による構造化データ取得
3. **Phase 3**: エラーハンドリング・ログ取得の最適化

**推奨アプローチ:**
```bash
# Phase 1: 動作確認
vocal-insight analyze input.wav && echo "Success"

# Phase 2: 構造化データ統合
result=$(vocal-insight --quiet analyze input.wav --format json)
process_json_result "$result"

# Phase 3: 堅牢な統合
if vocal-insight analyze input.wav --format json --output-dir ./results; then
    process_results ./results
else
    handle_analysis_error
fi
```

## 互換性保証戦略

### 1. コマンド互換性

**保証レベル:**
- **完全互換**: 既存の`analyze`コマンドの引数・動作
- **機能互換**: 同等の結果を新しい方法で提供
- **移行支援**: 段階的な機能拡張

**実装方針:**
```python
# 既存コマンドラインの完全サポート
@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output-dir", default=".", help="Output directory")
def analyze(input_file: str, output_dir: str):
    # 内部実装は新モジュールを使用するが、
    # 外部インターフェイスは既存と同一
```

### 2. 出力互換性

**保証レベル:**
- **形式互換**: 既存のテキスト出力形式を維持
- **内容互換**: 同等の分析結果を提供
- **拡張互換**: 新しい形式を追加オプションで提供

**実装方針:**
```python
# デフォルト出力は既存形式
if output_format == "txt":  # デフォルト
    generate_legacy_compatible_output()
elif output_format == "json":  # 新機能
    generate_structured_output()
```

### 3. エラーハンドリング互換性

**保証レベル:**
- **動作互換**: 同じ状況で同じエラーコードを返す
- **メッセージ互換**: 理解しやすいエラーメッセージ
- **復旧互換**: 同じ回復手順で問題解決可能

## テスト戦略

### 1. 回帰テスト

**テスト対象:**
- 既存のCLIコマンドライン引数
- 既存の出力形式・内容
- 既存のエラーケース

**テスト手法:**
```bash
# 既存コマンドのテスト
test_legacy_compatibility() {
    # 同じ入力で同じ出力が得られることを確認
    old_output=$(legacy_vocal_insight analyze test.wav)
    new_output=$(vocal_insight analyze test.wav)
    compare_outputs "$old_output" "$new_output"
}
```

### 2. 新機能テスト

**テスト対象:**
- 新しいコマンド（extract, segment）
- 新しい出力形式（JSON, YAML, CSV）
- 新しいオプション

**テスト手法:**
```bash
# 新機能のテスト
test_new_features() {
    # 新しいコマンドが正しく動作することを確認
    vocal-insight extract test.wav --format json
    validate_json_output
    
    vocal-insight segment test.wav --plot
    check_plot_generation
}
```

### 3. 統合テスト

**テスト対象:**
- 新旧モジュール間の結果整合性
- パフォーマンス特性
- リソース使用量

**テスト手法:**
```bash
# 統合テスト
test_module_integration() {
    # 新旧モジュールで同等の結果が得られることを確認
    legacy_result=$(vocal-insight analyze test.wav --module legacy)
    new_result=$(vocal-insight analyze test.wav --module acoustic)
    compare_analysis_results "$legacy_result" "$new_result"
}
```

## 成功指標

### 1. 互換性指標
- **既存テスト通過率**: 100%（既存機能の完全互換）
- **既存ユーザー満足度**: 95%以上（アンケートベース）
- **移行エラー率**: 5%未満

### 2. 採用指標
- **新機能使用率**: 30%以上（3ヶ月後）
- **JSON出力使用率**: 20%以上（構造化データニーズ）
- **部分機能使用率**: 15%以上（extract, segment）

### 3. 品質指標
- **エラー率**: 1%未満
- **性能劣化**: 10%未満
- **ユーザーサポート問い合わせ**: 20%削減

## リスク分析と対策

### 1. 互換性リスク

**リスク:** 既存ユーザーのworkflowが破綻
**影響度:** 高
**対策:**
- 段階的移行
- レガシーモードの維持
- 綿密な回帰テスト

### 2. 複雑性リスク

**リスク:** CLIが複雑になりすぎる
**影響度:** 中
**対策:**
- デフォルト動作の簡素化
- 段階的な機能公開
- 充実したヘルプシステム

### 3. 性能リスク

**リスク:** 新モジュールでの性能劣化
**影響度:** 中
**対策:**
- 性能ベンチマークテスト
- モジュール選択オプション
- 最適化の継続実施

## まとめ

本CLI設計は以下を実現します：

1. **完全な後方互換性** - 既存ユーザーの作業継続
2. **段階的な機能拡張** - 新機能の自然な導入
3. **柔軟な利用方法** - 様々なユースケースへの対応
4. **将来への対応** - モジュール追加・機能拡張への準備

この設計により、Epic S4E1で構築したモジュール化アーキテクチャの価値を最大化し、ユーザーに革新的な音声分析体験を提供できます。