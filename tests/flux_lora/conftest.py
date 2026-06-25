"""
Isolated conftest for tests/flux_lora/.

Prevents the root tests/conftest.py (which imports main_enterprise and
security.rate_limiting) from being loaded when running this subdirectory.
All fixtures needed by flux_lora tests are defined here.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def tmp_dataset(tmp_path: Path) -> Path:
    """
    Create a minimal valid dataset directory with 5 images + caption sidecars.
    Captions begin with the trigger word 'SKYYROSE'.
    """
    dataset_dir = tmp_path / "skyyrose_lora_test"
    dataset_dir.mkdir()

    for i in range(1, 6):
        # Fake minimal PNG header bytes
        img = dataset_dir / f"image_{i:02d}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
        caption = dataset_dir / f"image_{i:02d}.txt"
        caption.write_text(
            f"SKYYROSE luxury streetwear product shot {i}, studio lighting",
            encoding="utf-8",
        )

    return dataset_dir


@pytest.fixture()
def tmp_dataset_no_captions(tmp_path: Path) -> Path:
    """Dataset with images but missing caption sidecars."""
    dataset_dir = tmp_path / "skyyrose_no_caps"
    dataset_dir.mkdir()
    for i in range(1, 6):
        img = dataset_dir / f"image_{i:02d}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    return dataset_dir


@pytest.fixture(autouse=True)
def _clear_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove real REPLICATE_API_TOKEN so tests never hit the live API."""
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
