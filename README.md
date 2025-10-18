# VocalInsight AI

`VocalInsight AI` は、Praatの音響分析機能とLLM（大規模言語モデル）を組み合わせ、歌声のパフォーマンスを分析するためのシステムです。手動のプロンプト実行から脱却し、APIやCLIを通じて利用可能な、再利用性と拡張性の高いシステムへと進化させることを目指しています。

中核となる音声分析・プロンプト生成ロジックを**「コアライブラリ」**として独立させ、それを様々なクライアント（CLI, WebUIなど）から利用できるアーキテクチャを構築しています。

## ✨ 主要コンポーネント

- **コアライブラリ (`vocal_insight_ai`)**: 音声分析とプロンプト生成の純粋なロジックを提供します。
- **CLIクライアント (`vocal_insight_cli`)**: コアライブラリを利用し、コマンドラインから音声分析を実行します。現在、基本的な分析機能が実装されています。
- **Web API (`vocal_insight_api`)**: コアライブラリとLLMゲートウェイを介して、Webベースの分析機能を提供します。
- **Web UI (`vocal_insight_ui`)**: Gradioベースの簡易的なWebインターフェースで、ユーザーが音声ファイルをアップロードし、対話的に分析を進めることができます。
- **リファレンスボーカル抽出 (`vocal_insight/vocals`)**: リファレンス音源からボーカルのみを抽出し、音程判定や対照分析で再利用できるようにします。

## 🚀 プロジェクトの進め方

本プロジェクトは、以下のステップで開発を進めています。

1.  **コアライブラリ (`vocal_insight_ai`) の確立**: システム全体の心臓部となる、独立した音声分析・プロンプト生成ライブラリを完成させます。
2.  **CLIクライアント (`vocal_insight_cli`) の開発**: コアライブラリを実際に利用する最初のクライアントを作成し、ライブラリの使いやすさを検証します。現在、基本的な分析機能が実装済みです。
3.  **Webアプリケーションの開発**: 対話的な分析体験を提供するWebアプリケーションを構築します。

各ステップの詳細は `doc/spec_design_plan.md` を参照してください。

## ⚙️ 動作環境とインストール

### プロジェクトのセットアップ

リポジトリをクローンした後、以下のセットアップスクリプトを実行することで、必要な依存関係のインストールとpre-commitフックの設定を自動的に行えます。

```bash
./setup.sh
```

このスクリプトは、Poetryがインストールされていない場合はインストールを促し、その後 `poetry install` と `poetry run pre-commit install` を実行します。

### コアライブラリとCLIのインストール

本プロジェクトはPoetryで管理されています。

1.  **依存ライブラリのインストール**
    ```bash
    poetry install
    ```

    Demucs ベースのボーカル抽出を利用する場合は、追加のオプション依存をインストールします。

    ```bash
    poetry install --extras demucs
    ```

    すでに環境が構築済みでエクストラだけ追加する場合は `poetry install --only-root --extras demucs` などを利用してください。

### CLIの使い方

```bash
poetry run vocal-insight analyze <path_to_audio_file.wav> [--output-dir <output_directory>]
```

例:
```bash
poetry run vocal-insight analyze audio/sample.wav --output-dir output
```

実行後、指定された出力ディレクトリに `<入力ファイル名>_prompt.txt` という名前で分析結果のプロンプトが出力されます。

### リファレンスボーカル付きの分析実行

抽出済みのリファレンスボーカルを音程判定などに利用する場合、`analyze` コマンドに `--reference-audio` オプションを追加します。抽出結果は指定したディレクトリに保存され、分析レポートのJSON/YAML出力には品質指標（SNR、ピッチトラッカビリティなど）が含まれます。

```bash
poetry run vocal-insight analyze user.wav \
  --output-dir output \
  --format json \
  --reference-audio reference.wav \
  --reference-output-dir output/reference \
  --reference-cache-dir output/reference/cache
```

主なオプション:

- `--reference-audio`: リファレンス音源のパスを指定。
- `--reference-output-dir`: 抽出したボーカルの保存先ディレクトリ。
- `--reference-cache-dir`: NumPy形式でのキャッシュ保存先。
- `--reference-model-type`: 使用する抽出モデル種別（`hpss` または `demucs`）。
- `--reference-no-save`: 抽出結果のWAV保存をスキップし、キャッシュとメタデータのみを残します。

Demucs ベースの抽出を利用する場合は `--reference-model-type demucs` を指定し、`poetry install --extras demucs` でオプション依存を追加します（pip で個別に導入しても問題ありません）。`vocal_insight/core/config.py` 内の `reference_vocal.demucs_*` 設定を通してモデル名や処理パラメータを細かく調整可能です。

### 音程判定を含む分析実行

リファレンスボーカルが利用可能な場合、`--pitch-analysis-enabled` を指定すると音程一致度の計算結果が JSON/YAML に含まれ、任意の JSON ファイルにも保存できます。

```bash
poetry run vocal-insight analyze user.wav \
  --output-dir output \
  --format json \
  --reference-audio reference.wav \
  --pitch-analysis-enabled \
  --pitch-results-path output/pitch/user_pitch.json
```

主なオプション:

- `--pitch-analysis-enabled`: 音程判定を有効化します。
- `--pitch-results-path`: ピッチ分析結果を JSON として保存するパス。
- `--pitch-cent-tolerance`: ヒット率計算時の許容誤差（セント）を指定。
- `--pitch-disable-prompt`: 生成されるプロンプト内への音程要約の挿入を無効化。

## 🤝 貢献

貢献を歓迎します！貢献のガイドラインについては `doc/issue_workflow.md` を参照してください。

## ©️ ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。
