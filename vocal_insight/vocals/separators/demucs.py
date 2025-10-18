"""Demucsベースのボーカルセパレータ"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np

from ...core.types import ReferenceVocalExtractionConfig
from ..postprocess import resample_audio


class DemucsSeparator:
    """Demucsによるボーカル抽出をラップする"""

    def __init__(self, config: ReferenceVocalExtractionConfig):
        self.config = config
        self.model_name = config.get("demucs_model", "htdemucs")
        self.device = config.get("demucs_device")
        self.shifts = int(config.get("demucs_shifts", 1) or 1)
        self.overlap = float(config.get("demucs_overlap", 0.25) or 0.25)
        self.segment = config.get("demucs_segment")
        self._model = None
        self._model_sr: Optional[int] = None

    def _ensure_deps(self):
        try:
            import torch  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Demucs分離には PyTorch (torch) のインストールが必要です。"
            ) from exc

        try:
            from demucs.apply import apply_model  # noqa: F401
            from demucs.pretrained import get_model  # noqa: F401
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Demucs分離を利用するには demucs および torch/torchaudio のインストールが必要です。"
                " `pip install demucs torch torchaudio` を実行してください。"
            ) from exc

        return torch

    def _load_model(self, torch_module):
        if self._model is not None:
            return self._model

        from demucs.pretrained import get_model

        model = get_model(self.model_name)
        model.eval()
        device = self._resolve_device(torch_module)
        model.to(device)
        self._model = model
        self._model_sr = int(getattr(model, "samplerate", 44100))
        return model

    def _resolve_device(self, torch_module):
        candidate = self.device
        if candidate:
            candidate = str(candidate)
        else:
            candidate = "cuda" if torch_module.cuda.is_available() else "cpu"

        if candidate.startswith("cuda") and not torch_module.cuda.is_available():
            candidate = "cpu"
        return torch_module.device(candidate)

    def _prepare_mix(self, audio: np.ndarray, sample_rate: int, target_channels: int):
        if audio.ndim == 1:
            mix = np.tile(audio[np.newaxis, :], (target_channels, 1))
        elif audio.ndim == 2:
            mix = audio
            if audio.shape[0] < target_channels:
                repeat = math.ceil(target_channels / audio.shape[0])
                mix = np.tile(audio, (repeat, 1))[:target_channels]
            elif audio.shape[0] > target_channels:
                mix = audio[:target_channels]
        else:  # pragma: no cover - unexpected dimensionality
            mix = audio.reshape(target_channels, -1)
        return mix.astype(np.float32)

    def separate(self, audio: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        torch_module = self._ensure_deps()
        from demucs.apply import apply_model

        model = self._load_model(torch_module)
        target_sr = self._model_sr or sample_rate

        if target_sr != sample_rate:
            audio, sample_rate = resample_audio(audio, sample_rate, target_sr)

        mix = self._prepare_mix(audio, sample_rate, getattr(model, "audio_channels", 2))
        device = self._resolve_device(torch_module)
        mix_tensor = torch_module.as_tensor(mix, dtype=torch_module.float32, device=device).unsqueeze(0)

        segment = self.segment
        if segment is not None:
            segment = float(segment)

        with torch_module.no_grad():
            sources = apply_model(
                model,
                mix_tensor,
                shifts=self.shifts,
                overlap=self.overlap,
                segment=segment,
                device=device,
                split=True,
                progress=False,
            )

        sources = sources.squeeze(0).detach().cpu().numpy()

        source_names = getattr(model, "sources", ["vocals"])
        if "vocals" in source_names:
            vocal_index = source_names.index("vocals")
        else:
            vocal_index = 0

        vocals = sources[vocal_index]
        residual_components = [sources[i] for i in range(len(source_names)) if i != vocal_index]

        if vocals.ndim == 2:
            vocals = np.mean(vocals, axis=0)
        else:
            vocals = vocals.squeeze()

        if residual_components:
            residual_stack = []
            for comp in residual_components:
                if comp.ndim == 2:
                    residual_stack.append(np.mean(comp, axis=0))
                else:
                    residual_stack.append(comp.squeeze())
            residual = np.sum(residual_stack, axis=0)
        else:
            residual = np.zeros_like(vocals)

        return vocals.astype(np.float32), residual.astype(np.float32)
