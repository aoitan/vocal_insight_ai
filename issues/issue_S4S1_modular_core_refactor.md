---
title: "[story]: コア特徴量抽出パイプラインのモジュール構造を再設計"
labels: "story, vocal_insight_ai"
assignees: "@[担当者]"
---

## 概要

`vocal_insight_ai.py` に集約されている特徴量抽出ロジックをモジュール化し、機能ごとに独立したコンポーネントとして再利用できるようにします。分析ステップを明示的に分離し、拡張しやすいパッケージ構造を導入します。

## 目的

- 特徴量抽出の責務を整理し、追加機能をプラグイン的に実装できるアーキテクチャを整備する。
- モジュール分割によってユニットテストを容易にし、将来的なAPI/UI開発の基盤を固める。

## 詳細

- 新しい特徴量モジュールを配置するパッケージ（例: `vocal_insight/features/`）を定義する。
- 既存の `get_segment_boundaries` / `process_boundaries` / `analyze_segment_with_praat` / `generate_llm_prompt` などを適切なモジュールに移行し、`vocal_insight_ai.py` はオーケストレーションと公開インターフェイスに集中させる。
- モジュール間の依存関係とインターフェイス（型ヒント、プロトコルなど）を整理し、拡張方針をドキュメント化する。

### 関連するファイル/モジュール

- `vocal_insight_ai.py`
- `vocal_insight/features/` (新規)
- `tests/`

### 依存関係

- #issue_S4T1_define_feature_module_package
- #issue_S4T2_migrate_existing_feature_functions
- #issue_S4T3_update_core_pipeline_tests

## 完了の定義 (Definition of Done)

- [ ] 特徴量抽出用の新パッケージとモジュールレイアウトが決定・実装されている。
- [ ] 既存の特徴量抽出・加工関数がモジュールへ移行され、`vocal_insight_ai.py` は調整済みである。
- [ ] 新モジュール向けのユニットテストが整備され、既存テストが新構造で成功している。
- [ ] モジュール構成と利用方法の概要が `doc/` またはリポジトリ内ドキュメントに記載されている。
- [ ] コードレビューが完了している。

## 備考

- 後続で追加する特徴量モジュールが、この構造を利用して容易に組み込めることを意識してインターフェイスを設計する。
