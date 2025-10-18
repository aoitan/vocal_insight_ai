"""ボーカル抽出プロトコル定義"""

from __future__ import annotations

from typing import Protocol, Tuple

import numpy as np

from .types import ReferenceVocalExtractionResult


class VocalExtractorProtocol(Protocol):
    """ボーカル抽出器のインターフェース"""

    def extract(
        self,
        audio: np.ndarray,
        sample_rate: int,
        *,
        source_path: str | None = None,
        output_dir: str | None = None,
    ) -> ReferenceVocalExtractionResult:
        ...


class VocalSeparatorProtocol(Protocol):
    """音源分離アルゴリズムのインターフェース"""

    def separate(self, audio: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        ...
