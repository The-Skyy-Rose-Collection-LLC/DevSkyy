"""
tests.flux_lora.test_dataset — 5 tests covering dataset.py public API.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts.flux_lora import DatasetError
from scripts.flux_lora.config import DEFAULT_TRIGGER_WORD
from scripts.flux_lora.dataset import (
    dataset_summary,
    load_dataset,
    pack_zip,
    validate_dataset,
)


class TestLoadDataset:
    def test_load_reads_images_and_captions(self, tmp_dataset: Path) -> None:
        result = load_dataset(tmp_dataset)

        assert len(result["images"]) == 5
        assert len(result["captions"]) == 5
        # Every caption starts with trigger word
        for caption in result["captions"].values():
            assert caption.startswith(DEFAULT_TRIGGER_WORD)

    def test_load_raises_dataset_error_when_dir_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        with pytest.raises(DatasetError, match="not found"):
            load_dataset(missing)


class TestValidateDataset:
    def test_validate_passes_valid_dataset(self, tmp_dataset: Path) -> None:
        # Should not raise
        validate_dataset(tmp_dataset)

    def test_validate_raises_when_captions_missing(self, tmp_dataset_no_captions: Path) -> None:
        with pytest.raises(DatasetError, match="Missing caption sidecars"):
            validate_dataset(tmp_dataset_no_captions)

    def test_validate_raises_when_trigger_word_absent(self, tmp_path: Path) -> None:
        dataset_dir = tmp_path / "bad_trigger"
        dataset_dir.mkdir()
        for i in range(1, 6):
            img = dataset_dir / f"img_{i}.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
            cap = dataset_dir / f"img_{i}.txt"
            # Caption missing trigger word
            cap.write_text(f"some caption without trigger {i}", encoding="utf-8")

        with pytest.raises(DatasetError, match=DEFAULT_TRIGGER_WORD):
            validate_dataset(dataset_dir)


class TestPackZip:
    def test_pack_zip_creates_valid_zip_with_images_and_captions(
        self, tmp_dataset: Path, tmp_path: Path
    ) -> None:
        dest = tmp_path / "out.zip"
        result = pack_zip(tmp_dataset, dest=dest)

        assert result == dest
        assert dest.exists()

        with zipfile.ZipFile(dest) as zf:
            names = set(zf.namelist())

        # 5 images + 5 captions = 10 entries
        assert len(names) == 10
        png_files = [n for n in names if n.endswith(".png")]
        txt_files = [n for n in names if n.endswith(".txt")]
        assert len(png_files) == 5
        assert len(txt_files) == 5

    def test_pack_zip_raises_on_missing_dir(self, tmp_path: Path) -> None:
        missing = tmp_path / "ghost"
        with pytest.raises(DatasetError):
            pack_zip(missing)


class TestDatasetSummary:
    def test_summary_returns_correct_counts(self, tmp_dataset: Path) -> None:
        summary = dataset_summary(tmp_dataset)

        assert summary["image_count"] == 5
        assert summary["caption_count"] == 5
        assert summary["total_bytes"] > 0
        assert summary["dataset_dir"] == str(tmp_dataset)

    def test_summary_raises_on_missing_dir(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetError, match="not found"):
            dataset_summary(tmp_path / "nowhere")
