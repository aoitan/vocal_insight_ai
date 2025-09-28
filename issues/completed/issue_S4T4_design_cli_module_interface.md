---
title: "[task]: モジュール選択CLIのインターフェイス設計"
labels: "task, cli, completed"
assignees: "@[担当者]"
completed_date: "2025-01-25"
---

## 概要

モジュール化された特徴量抽出をCLIから利用するためのインターフェイス仕様を設計します。オプションやサブコマンドの構成、ヘルプテキスト、想定ユースケースを整理します。

## 目的

- ユーザーが直感的にモジュールを選択できるCLI仕様を用意する。
- 実装時の迷いを減らし、後続タスクでの手戻りを防ぐ。

## 詳細

- `vocal_insight_cli.py` に追加するオプション／サブコマンド案をまとめる。
- モジュール識別子の命名規則（例: `core`, `extended` など）とデフォルト設定を定義する。
- 将来のモジュール追加時に必要となるガイドラインを決める。

### 関連するファイル/モジュール

- `vocal_insight_cli.py`
- `doc/`

### 依存関係

- #issue_S4S1_modular_core_refactor ✅

## 完了の定義 (Definition of Done)

- [✅] CLIインターフェイス仕様が文書化され、レビュー可能な状態にある。
- [✅] モジュール識別子とデフォルト動作が定義されている。
- [✅] ユースケース（例: デフォルト利用、新モジュール指定）が整理されている。
- [✅] チームで合意済みの仕様であることを確認している。
- [✅] レビューが完了している。

## 成果物

### ✅ 作成された設計文書
1. **`doc/cli_interface_design.md`** (5,717文字) - 包括的CLI設計仕様
2. **`doc/cli_implementation_sample.py`** (20,097文字) - 実装サンプルコード
3. **`doc/cli_usecases_migration.md`** (5,646文字) - ユースケース分析
4. **`doc/s4t4_implementation_plan.md`** - 実装ガイド・チェックリスト

### ✅ 定義されたモジュール識別子
- `auto`: 自動選択（デフォルト）
- `acoustic`: 音響特徴量抽出（標準）
- `core`: 基本機能のみ
- `legacy`: 旧実装（互換性用）

### ✅ 設計されたコマンド体系
```
vocal-insight [GLOBAL-OPTIONS] COMMAND [COMMAND-OPTIONS] INPUT_FILE

Commands:
├── analyze     # メイン分析（既存互換 + 拡張）
├── extract     # 特徴量抽出のみ
├── segment     # セグメント検出のみ
├── examples    # 使用例表示
├── modules     # 利用可能モジュール表示
├── formats     # 対応フォーマット表示
└── info        # システム情報
```

## 備考

- 仕様は `doc/` への追加やIssue内リンクなど、参照しやすい場所にまとめておくこと。
- PR #17でマージ済み、S4T5実装の基盤として活用完了
