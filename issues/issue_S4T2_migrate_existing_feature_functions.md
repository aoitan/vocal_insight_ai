---
title: "[task]: 既存特徴量処理を新モジュールへ移行"
labels: "task, vocal_insight_ai, partial"
assignees: "@[担当者]"
progress: "80% - 新実装完了、レガシー統合残り"
---

## 概要

現在 `vocal_insight_ai.py` に集約されている特徴量抽出・セグメント処理関数を、新しく定義したモジュールパッケージへ移行します。既存の公開インターフェイスを保ちつつ内部の構造を整理します。

## 目的

- 関数群を責務ごとにモジュールへ分割し、再利用性とテスト容易性を高める。
- オーケストレーション層と処理ロジック層を分離し、将来的な拡張に備える。

## 詳細

- `get_segment_boundaries`、`process_boundaries`、`analyze_segment_with_praat`、`generate_llm_prompt` などの関数を適切なモジュールへ移動する。
- `vocal_insight_ai.py` からは新モジュールをインポートする形に書き換える。
- モジュール移行後も公開API（例: `analyze_audio_segments`）の呼び出しシグネチャが変わらないことを保証する。

### 関連するファイル/モジュール

- `vocal_insight_ai.py`
- `vocal_insight/features/`

### 依存関係

- #issue_S4T1_define_feature_module_package

## 完了の定義 (Definition of Done)

- [x] 対象関数が新しいモジュールに物理的に移行されている。
- [ ] `vocal_insight_ai.py` からのインポートが新構造に合わせて更新されている。
- [x] 既存の公開APIに破壊的変更がないことを確認している。
- [x] リファクタ後のコードで型チェック・静的解析ツールが通過する。
- [x] コードレビューが完了している。

## 備考

- 移行後のモジュールに対してdocstringやコメントで役割を簡潔に記載しておくと、今後の拡張時に役立つ。
