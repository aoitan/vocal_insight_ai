#!/bin/bash
set -e

echo "プロジェクトのセットアップを開始します..."

# Poetryがインストールされているか確認
if ! command -v poetry &> /dev/null
then
    echo "Poetryが見つかりません。Poetryをインストールします..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "Poetryのインストールが完了しました。環境変数を更新するため、シェルを再起動するか、PoetryをPATHに追加してください。"
    exit 1
fi

echo "Poetryの依存関係をインストールします..."
poetry install

echo "pre-commitフックをインストールします..."
poetry run pre-commit install

echo "プロジェクトのセットアップが完了しました！"
