"""Poetry設定のオプション依存関係を検証するテスト"""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - Python 3.11 以降では tomllib が標準
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 以前向けフォールバック
    import tomli as tomllib  # type: ignore[no-redef]


def test_demucs_extra_is_defined() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    extras = payload.get("tool", {}).get("poetry", {}).get("extras", {})
    assert "demucs" in extras, "[tool.poetry.extras.demucs] が定義されていません"

    packages = set(extras["demucs"])
    required = {"demucs", "torch", "torchaudio"}
    missing = required - packages
    assert not missing, f"demucsエクストラに不足しているパッケージがあります: {sorted(missing)}"
