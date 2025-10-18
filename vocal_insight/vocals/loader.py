"""音声入力の読み込みユーティリティ"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import librosa
import numpy as np


def resolve_path(path: str | Path | None) -> Path | None:
    """環境変数やホームディレクトリを展開したパスを返す"""

    if path is None:
        return None
    return Path(os.path.expandvars(str(path))).expanduser()


def ensure_directory(path: Path) -> Path:
    """ディレクトリが存在しない場合は作成"""

    path.mkdir(parents=True, exist_ok=True)
    return path


def load_audio(
    source: str | Path,
    *,
    target_sr: int | None = None,
    mono: bool = True,
) -> Tuple[np.ndarray, int]:
    """音声ファイルを読み込む"""

    path = resolve_path(source)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Audio source not found: {source}")

    audio, sr = librosa.load(path, sr=target_sr, mono=mono)
    return audio, sr
