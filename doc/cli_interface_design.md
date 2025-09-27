# CLI モジュールインターフェイス設計仕様

## 概要

Epic S4E1で実装されたモジュール化アーキテクチャを活用できる新しいCLIインターフェイスを設計します。

## 設計原則

1. **後方互換性**: 既存のCLIコマンドは維持
2. **モジュール選択**: ユーザーが処理モジュールを選択可能
3. **段階的移行**: 既存→新モジュール→レガシー廃止の3段階
4. **直感的操作**: 学習コストを最小化
5. **拡張性**: 将来のモジュール追加に対応

## CLI アーキテクチャ

### 現在の構造（レガシー）
```
vocal-insight analyze [OPTIONS] INPUT_FILE
```

### 新しい構造（提案）
```
vocal-insight [GLOBAL-OPTIONS] COMMAND [COMMAND-OPTIONS] INPUT_FILE

# Commands:
analyze        # 既存互換（内部で新モジュール使用）
analyze-legacy # 旧実装（廃止予定）
analyze-new    # 新モジュール明示使用
extract        # 特徴量抽出のみ
segment        # セグメント検出のみ
```

## コマンド設計

### 1. メインコマンド: `analyze`

**既存互換性を保持しつつ内部で新モジュールを使用**

```bash
vocal-insight analyze [OPTIONS] INPUT_FILE

Options:
  --output-dir TEXT          Output directory [default: current]
  --module TEXT              Processing module [default: auto]
  --min-segment FLOAT        Minimum segment length in seconds [default: 8.0]
  --max-segment FLOAT        Maximum segment length in seconds [default: 45.0]
  --percentile INTEGER       RMS percentile for boundary detection [default: 95]
  --format [txt|json|yaml]   Output format [default: txt]
  --verbose / --quiet        Verbose output
  --help                     Show this message and exit
```

**使用例:**
```bash
# 既存互換（デフォルト動作）
vocal-insight analyze input.wav

# カスタム設定
vocal-insight analyze input.wav --min-segment 5.0 --max-segment 30.0

# JSON出力
vocal-insight analyze input.wav --format json --output-dir ./results
```

### 2. 新機能: `extract`

**特徴量抽出のみを実行**

```bash
vocal-insight extract [OPTIONS] INPUT_FILE

Options:
  --output-dir TEXT          Output directory [default: current]
  --format [json|csv|yaml]   Output format [default: json]
  --extractor TEXT           Feature extractor [default: acoustic]
  --segment-start FLOAT      Start time in seconds
  --segment-end FLOAT        End time in seconds
  --help                     Show this message and exit
```

**使用例:**
```bash
# 全体の特徴量抽出
vocal-insight extract input.wav

# 特定区間の特徴量抽出
vocal-insight extract input.wav --segment-start 10.0 --segment-end 20.0

# CSV形式で出力
vocal-insight extract input.wav --format csv
```

### 3. 新機能: `segment`

**セグメント検出のみを実行**

```bash
vocal-insight segment [OPTIONS] INPUT_FILE

Options:
  --output-dir TEXT          Output directory [default: current]
  --format [json|csv|yaml]   Output format [default: json]
  --min-segment FLOAT        Minimum segment length [default: 8.0]
  --max-segment FLOAT        Maximum segment length [default: 45.0]
  --percentile INTEGER       RMS percentile [default: 95]
  --plot                     Generate visualization plot
  --help                     Show this message and exit
```

**使用例:**
```bash
# セグメント検出
vocal-insight segment input.wav

# 可視化付き
vocal-insight segment input.wav --plot --output-dir ./results
```

### 4. 開発用: `analyze-dev`

**開発・デバッグ用コマンド**

```bash
vocal-insight analyze-dev [OPTIONS] INPUT_FILE

Options:
  --module-path TEXT         Custom module path
  --debug                    Debug mode
  --profile                  Performance profiling
  --dry-run                  Validation only
  --help                     Show this message and exit
```

## モジュール識別子

### 標準モジュール
- `auto`: 自動選択（デフォルト）
- `acoustic`: 音響特徴量抽出（標準）
- `core`: 基本機能のみ
- `extended`: 拡張機能付き（将来）

### カスタムモジュール
- `custom:path/to/module`: カスタムモジュール指定
- `plugin:name`: プラグインモジュール（将来）

## 出力フォーマット

### 1. テキスト（txt）- デフォルト
```
# 既存のLLMプロンプト形式
Vocal Analysis Results for input.wav
=====================================
...
```

### 2. JSON
```json
{
  "filename": "input.wav",
  "analysis_config": {...},
  "segments": [...],
  "llm_prompt": "...",
  "metadata": {...}
}
```

### 3. YAML
```yaml
filename: input.wav
analysis_config:
  rms_delta_percentile: 95
  min_len_sec: 8.0
  max_len_sec: 45.0
segments:
  - segment_id: 0
    time_start_s: 0.0
    time_end_s: 15.2
    features:
      f0_mean_hz: 150.5
      ...
```

### 4. CSV（特徴量のみ）
```csv
segment_id,time_start_s,time_end_s,f0_mean_hz,f0_std_hz,hnr_mean_db,f1_mean_hz,f2_mean_hz,f3_mean_hz
0,0.0,15.2,150.5,25.2,15.8,520.1,1580.3,2520.7
1,15.2,28.5,145.8,22.1,18.2,510.5,1620.8,2480.2
```

## エラーハンドリング

### 1. ファイル関連
- 存在しないファイル: 明確なエラーメッセージ
- 対応外フォーマット: サポートフォーマット表示
- 読み込みエラー: 詳細情報とトラブルシューティング

### 2. パラメータ関連
- 不正な値: 有効範囲の表示
- 矛盾する設定: 自動調整または警告
- モジュール不明: 利用可能モジュール表示

### 3. 処理関連
- 分析失敗: 部分結果の保存と継続可否
- メモリ不足: 推奨設定の提案
- 予期しないエラー: デバッグ情報の収集

## ヘルプシステム

### 1. 基本ヘルプ
```bash
vocal-insight --help
vocal-insight COMMAND --help
```

### 2. 例示
```bash
vocal-insight examples           # 使用例表示
vocal-insight modules            # 利用可能モジュール表示
vocal-insight formats            # 対応フォーマット表示
```

### 3. バージョン情報
```bash
vocal-insight --version          # バージョンとモジュール情報
vocal-insight info               # システム情報
```

## 移行戦略

### Phase 1: 新CLI実装（現在のタスク）
- 新しいコマンド構造の実装
- 既存コマンドの互換性維持
- 新モジュールとの統合

### Phase 2: 機能拡張
- `extract`、`segment`コマンドの実装
- 複数出力フォーマット対応
- 可視化機能追加

### Phase 3: レガシー廃止
- `analyze-legacy`への移行促進
- 既存コマンドの段階的廃止
- 完全移行完了

## ユースケース

### 1. 一般ユーザー（既存互換）
```bash
# 従来通りの使用
vocal-insight analyze recording.wav
```

### 2. パワーユーザー（詳細制御）
```bash
# カスタム設定
vocal-insight analyze recording.wav \
  --min-segment 5.0 \
  --max-segment 30.0 \
  --format json \
  --output-dir ./analysis_results
```

### 3. 開発者（部分機能利用）
```bash
# 特徴量のみ抽出
vocal-insight extract recording.wav --format csv

# セグメント検出のみ
vocal-insight segment recording.wav --plot
```

### 4. 研究者（詳細分析）
```bash
# デバッグ情報付き
vocal-insight analyze-dev recording.wav --debug --profile
```

## 実装優先順位

1. **High Priority**: `analyze`コマンドの新モジュール統合
2. **Medium Priority**: `extract`、`segment`コマンドの実装
3. **Low Priority**: 可視化、プロファイリング機能

## 検証項目

- [ ] 既存CLIとの完全互換性
- [ ] 新モジュールとの正常統合
- [ ] エラーハンドリングの適切性
- [ ] ヘルプシステムの完備
- [ ] パフォーマンスの維持・向上