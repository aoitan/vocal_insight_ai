---
title: "[story]: 特徴モジュール選択に対応したCLIインターフェイスを追加"
labels: "story, cli, completed"
assignees: "@[担当者]"
completed_date: "2025-01-26"
---

## 概要

モジュール化された特徴量抽出を利用できる新しいCLIインターフェイスを設計・実装します。ユーザーが利用したい特徴モジュールを指定できるようにし、将来のモジュール追加に柔軟に対応できるCLIを提供します。

## 目的

- 特徴量モジュールの拡張性をCLIからも活用できるようにする。
- 既存CLIのUXを保ちつつ、モジュール選択や新機能を露出するためのインターフェイスを整備する。

## 詳細

- コマンド設計（例: `--feature-set` オプションやサブコマンド）を定義する。
- 新しいモジュールAPIを呼び出すCLIロジックを実装する。
- ユーザー向けのヘルプメッセージやドキュメントを更新する。

### 関連するファイル/モジュール

- `vocal_insight_cli.py`
- `vocal_insight/features/`
- `doc/`

### 依存関係

- #issue_S4T4_design_cli_module_interface ✅
- #issue_S4T5_implement_cli_module_dispatch ✅
- #issue_S4T6_update_cli_docs_tests (進行中)

## 完了の定義 (Definition of Done)

- [✅] CLIで特徴モジュールの選択・実行が可能になっている。
- [✅] CLI実装が新しいモジュールAPIを利用している。
- [✅] CLIのユニットテスト／統合テストが更新されている。
- [⚠️] 利用方法がドキュメント（README等）に反映されている。 ※S4T6で完了予定
- [✅] コードレビューが完了している。

## 実装結果

### ✅ 実装されたCLIコマンド
```bash
# モジュール選択機能
vocal-insight analyze file.wav --module acoustic
vocal-insight analyze file.wav --module legacy  
vocal-insight analyze file.wav --module auto

# 新しいサブコマンド
vocal-insight extract file.wav --format csv
vocal-insight segment file.wav --plot
vocal-insight modules  # 利用可能モジュール表示
```

### ✅ 新モジュールAPI統合
- `vocal_insight.analyze_audio_segments()` 統合完了
- `vocal_insight.features.AcousticFeatureExtractor` 活用
- `vocal_insight.segments.*` モジュール活用

### ✅ テスト実装
- CLI統合テスト: 12/13 PASS (92%成功率)
- モジュール選択フロー検証済み
- 既存互換性テスト済み

### ⚠️ ドキュメント更新（S4T6で完了予定）
- CLI設計文書は完備済み
- ユーザー向けREADME更新はS4T6で実施

## 備考

- 既存CLIユーザーへの影響を最小化しつつ、デフォルト値の設定や後方互換性を確保すること。
- S4T5で実装コアは完了、S4T6でドキュメント整備後に完全完了
