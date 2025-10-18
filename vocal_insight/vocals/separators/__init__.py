"""ボーカル分離セパレータのレジストリ"""

from __future__ import annotations

from typing import Callable, Dict

from ...core.types import ReferenceVocalExtractionConfig
from ..protocols import VocalSeparatorProtocol

SeparatorFactory = Callable[[ReferenceVocalExtractionConfig], VocalSeparatorProtocol]

_SEPARATOR_REGISTRY: Dict[str, SeparatorFactory] = {}


def register_separator(
    name: str,
    factory: SeparatorFactory,
    *,
    replace: bool = False,
) -> None:
    """セパレータを登録する"""

    key = name.lower()
    if not replace and key in _SEPARATOR_REGISTRY:
        raise ValueError(f"Separator '{name}' is already registered")
    _SEPARATOR_REGISTRY[key] = factory


def unregister_separator(name: str) -> None:
    """セパレータを登録解除する"""

    _SEPARATOR_REGISTRY.pop(name.lower(), None)


def get_separator(
    name: str | None,
    config: ReferenceVocalExtractionConfig,
) -> VocalSeparatorProtocol:
    """指定した名前のセパレータを生成して返す"""

    key = (name or "hpss").lower()
    if key not in _SEPARATOR_REGISTRY:
        available = ", ".join(sorted(_SEPARATOR_REGISTRY)) or "(none)"
        raise ValueError(f"Unknown separator '{name}'. Available: {available}")
    return _SEPARATOR_REGISTRY[key](config)


def available_separators() -> list[str]:
    """利用可能なセパレータ名の一覧"""

    return sorted(_SEPARATOR_REGISTRY)


from .demucs import DemucsSeparator  # noqa: E402  pylint: disable=wrong-import-position
from .hpss import HPSSSeparator  # noqa: E402  pylint: disable=wrong-import-position

register_separator("hpss", lambda cfg: HPSSSeparator(cfg), replace=True)
register_separator("demucs", lambda cfg: DemucsSeparator(cfg), replace=True)

__all__ = [
    "available_separators",
    "get_separator",
    "register_separator",
    "unregister_separator",
]
