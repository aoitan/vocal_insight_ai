#!/bin/bash
# Note: If you encounter a "Permission denied" error, set executable permissions with: chmod +x setup.sh
set -e

echo "プロジェクトのセットアップを開始します..."

# Poetryがインストールされているか確認
if ! command -v poetry &> /dev/null
then
    echo "Poetryが見つかりません。Poetryをインストールします..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "Poetryのインストールが完了しました。環境変数を更新するため、シェルを再起動するか、PoetryをPATHに追加してください。"
    echo "再度 `./setup.sh` を実行して、残りのセットアップを完了してください。"
    exit 0
fi

echo "Poetryの依存関係をインストールします..."
poetry install

echo "pre-commitフックをインストールします..."
poetry run pre-commit install

echo "プロジェクトのセットアップが完了しました！"
