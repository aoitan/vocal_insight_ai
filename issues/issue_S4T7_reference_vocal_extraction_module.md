---
title: "[Task]: リファレンスボーカル抽出機能の実装"
labels: "Task, audio-processing"
assignees: "@aoitan"
---

## 概要

音程判定に利用するリファレンスボーカルをローカルで抽出できるよう、新しいボーカル抽出モジュールを実装する。抽出したボーカルは既存パイプラインおよび他システムから再利用可能とする。

## 目的

- 音程判定機能の前提となるリファレンスボーカルを自動生成し、分析フローを完結させる。
- 抽出モジュールを再利用可能な形で提供し、将来のモデル差し替えや外部システムからの参照に備える。

## 詳細

- 要件定義書 `doc/reference_vocal_extraction_requirements.md` に基づき、`vocal_insight/vocals/` モジュールを新設する。
- 軽量なボーカル分離モデルを標準実装し、抽出結果を `numpy.ndarray` として返す API を提供する。
- 抽出結果のファイル出力・キャッシュ機構と、保存先パスやモデル配置パスを設定で制御できるようにする。
- `AnalysisConfig` に抽出設定を追加し、CLI/API/UI から抽出を有効化できるようにする。
- 品質指標（例: SNR、ピッチトラッカビリティ）を計算し、ログおよびメタデータとして記録する。
- README と CLI ヘルプにボーカル抽出手順と要求環境を追記する。

### 関連するファイル/モジュール

- `doc/reference_vocal_extraction_requirements.md`
- `vocal_insight_ai.py` および予定する `vocal_insight/vocals/` 配下の新規ファイル
- `vocal_insight_cli.py`
- `vocal_insight/core/config.py`（想定）
- `README.md`

### 依存関係

- #22 : 音程判定・リファレンス抽出要件のレビュー（対応するPR）

## 完了の定義 (Definition of Done)

- [ ] `vocal_insight/vocals/` モジュールが追加され、要件に沿ったAPIが実装されている
- [ ] `AnalysisConfig` 等の設定に抽出機能が統合されている
- [ ] CLI/API/UI から抽出処理が起動でき、出力先パスを指定可能である
- [ ] 抽出結果と品質指標がログ/メタデータとして記録される
- [ ] ユニットテスト・統合テストが追加され、CI がパスしている
- [ ] README や CLI ヘルプに関連ドキュメントが追加されている
- [ ] コードレビューが完了し、PR がマージされている

## 備考

- モデル実装には OSS の軽量分離モデル（例: Spleeter, Demucs light など）を想定。モデルダウンロードサイズや処理時間の制約に留意すること。
- 共有ストレージ参照や環境変数展開など、要件定義書で求められるパス設定機能を忘れずに盛り込むこと。
