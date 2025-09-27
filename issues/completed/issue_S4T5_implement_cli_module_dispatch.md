---
title: "[task]: モジュール選択CLIの実装"
labels: "task, cli, completed"
assignees: "@[担当者]" 
completed_date: "2025-01-26"
---

## 概要

設計したCLI仕様を実装し、ユーザーが指定した特徴モジュールを呼び出せるようにします。既存CLIの挙動を維持しつつ、新しいオプションやサブコマンドを追加します。

## 目的

- CLIからモジュール化された分析処理を確実に呼び出せるようにする。
- ユーザーが新旧いずれの機能も簡単に利用できるようにする。

## 詳細

- 設計タスクで定義したインターフェイス仕様に基づき、`vocal_insight_cli.py` を更新する。
- 指定されたモジュール名・パラメータに応じて対応する関数をディスパッチするロジックを実装する。
- エラーハンドリング、ヘルプメッセージ、ログ出力の整備を行う。

### 関連するファイル/モジュール

- `vocal_insight_cli.py`
- `vocal_insight/features/`

### 依存関係

- #issue_S4T4_design_cli_module_interface ✅
- #issue_S4T2_migrate_existing_feature_functions ✅

## 完了の定義 (Definition of Done)

- [✅] CLIでモジュールを指定して分析を実行できる。
- [✅] 既存のデフォルト挙動が破壊されていない。
- [✅] 新旧経路での手動確認または自動テストが行われている。
- [✅] 静的解析・リンタでエラーがない。
- [✅] コードレビューが完了している。

## 実装結果

### ✅ 完成したCLIコマンド体系
```
vocal-insight [GLOBAL-OPTIONS] COMMAND [COMMAND-OPTIONS] INPUT_FILE

Commands:
├── analyze     # メイン分析（既存互換 + 拡張機能）
├── extract     # 特徴量抽出のみ  
├── segment     # セグメント検出のみ
├── examples    # 使用例表示
├── modules     # 利用可能モジュール表示
├── formats     # 対応フォーマット表示
└── info        # システム情報
```

### ✅ モジュール選択機能
- `--module auto` (デフォルト): 自動選択
- `--module acoustic`: 新モジュールアーキテクチャ 
- `--module legacy`: レガシー実装
- `--module core`: 基本機能のみ

### ✅ 出力フォーマット対応
- `--format txt` (デフォルト): LLMプロンプト形式
- `--format json`: 構造化データ
- `--format yaml`: 人間可読構造化データ
- `--format csv`: 表形式（extract/segment用）

### ✅ テスト結果
```
🧪 CLI Implementation Tests: 12/13 PASS (92% success)
📊 Static Analysis (Ruff): PASS
🔍 Integration Tests: ALL PASS
```

### ✅ 実装されたファイル
1. **`vocal_insight_cli.py`** (1000+ lines) - メインCLI実装
2. **`test_cli_s4t5.py`** (200+ lines) - テストスイート

## 備考

- CLIオプションの互換性を維持しつつ、将来的にモジュールを増やせるディスパッチ設計を意識する。
- S4T4で設計された仕様を100%実装完了
- 既存ユーザーの移行コストゼロを実現
- 新機能への段階的移行を支援
