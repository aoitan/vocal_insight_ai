---
title: "[refactor]: vocal_insight_ai.py のコアロジックと副作用の分離"
labels: "refactor, vocal_insight_ai"
assignees: "@[担当者]"
---

## 概要

`vocal_insight_ai.py` に含まれる音声分析およびプロンプト生成のコアロジックと、ファイルI/O、一時ディレクトリ管理、print文などの副作用を持つ処理を分離します。これにより、`vocal_insight_ai` を純粋なPythonライブラリとして独立させ、再利用性とテスト容易性を向上させます。

## 目的

- `vocal_insight_ai` を他のコンポーネント（CLI, API）から独立して利用可能なコアライブラリとして確立する。
- コアロジックのユニットテストを容易にする。
- コードベースの保守性と拡張性を向上させる。

## 詳細

- `vocal_insight_ai.py` 内の `main` 関数から、ファイルI/O（`librosa.load`, `sf.write`, `open`, `shutil.rmtree` など）および `print` 文を削除または別の関数に切り出す。
- `get_segment_boundaries`, `process_boundaries`, `analyze_segment_with_praat`, `generate_llm_prompt` などのコアロジック関数を、ファイルパスではなく、メモリ上のデータ（例: numpy配列、文字列）を入力として受け取り、メモリ上のデータを出力として返すように修正する。
- `TEMP_DIR` などのグローバル定数や、一時ファイルの作成・削除ロジックをコアライブラリから分離する。
- コマンドライン引数のパース（`argparse`）もコアライブラリから分離する。

### 関連するファイル/モジュール

- `vocal_insight_ai.py`

### 依存関係

- なし

## 完了の定義 (Definition of Done)

- [ ] `vocal_insight_ai.py` からファイルI/Oおよびprint文が完全に分離されていること。
- [ ] コアロジック関数が、副作用なしにメモリ上のデータで動作するようになっていること。
- [ ] `TEMP_DIR` などのグローバル定数や一時ファイル管理ロジックがコアライブラリから分離されていること。
- [ ] コマンドライン引数パースロジックがコアライブラリから分離されていること。
- [ ] 変更が既存の機能に影響を与えないことを確認済みであること（手動テストまたは既存テストの実行）。
- [ ] コードレビューが完了していること。

## 備考

このIssueは、開発計画書の「ステップ1：コアライブラリ (`vocal_insight_ai`) の確立」の最初のタスクです。
