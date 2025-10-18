"""HPSSベースの簡易ボーカルセパレータ"""

from __future__ import annotations

from typing import Tuple

import librosa
import numpy as np

from ...core.types import ReferenceVocalExtractionConfig


class HPSSSeparator:
    """librosaのHPSSを利用したボーカル抽出"""

    def __init__(self, config: ReferenceVocalExtractionConfig):
        self.config = config

    def separate(self, audio: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        harmonic, percussive = librosa.effects.hpss(audio)
        residual = audio - (harmonic + percussive)
        return harmonic.astype(np.float32), residual.astype(np.float32)
