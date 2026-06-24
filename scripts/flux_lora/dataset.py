"""
scripts.flux_lora.dataset — Dataset loading, validation, and packaging.

Public API:
  load_dataset(dataset_dir)      -> dict with metadata + image paths
  validate_dataset(dataset_dir)  -> None (raises DatasetError on failure)
  pack_zip(dataset_dir, dest)    -> Path to created zip
  dataset_summary(dataset_dir)   -> dict with counts and sizes
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from scripts.flux_lora import DatasetError
from scripts.flux_lora.config import DATASET_DIR, DEFAULT_TRIGGER_WORD

IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})
MIN_IMAGES: int = 5


def _image_files(dataset_dir: Path) -> list[Path]:
    """Return sorted list of image files in dataset_dir."""
    return sorted(p for p in dataset_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)


def load_dataset(dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    """
    Load dataset metadata and enumerate image/caption pairs.

    Returns:
        {
          "dataset_dir": Path,
          "images": [Path, ...],
          "captions": {stem: str, ...},   # keyed by image stem
          "metadata": dict | None,
        }

    Raises:
        DatasetError: if directory absent or no metadata file present.
    """
    if not dataset_dir.exists():
        raise DatasetError(f"Dataset directory not found: {dataset_dir}")

    images = _image_files(dataset_dir)

    # Load captions from .txt sidecars
    captions: dict[str, str] = {}
    for img in images:
        sidecar = img.with_suffix(".txt")
        if sidecar.exists():
            captions[img.stem] = sidecar.read_text(encoding="utf-8").strip()

    # Optional metadata.jsonl
    metadata: dict[str, Any] | None = None
    meta_path = dataset_dir / "metadata.jsonl"
    if meta_path.exists():
        lines = meta_path.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(ln) for ln in lines if ln.strip()]
        metadata = {"rows": rows}

    return {
        "dataset_dir": dataset_dir,
        "images": images,
        "captions": captions,
        "metadata": metadata,
    }


def validate_dataset(dataset_dir: Path = DATASET_DIR) -> None:
    """
    Validate dataset is ready for training.

    Checks:
      - Directory exists
      - At least MIN_IMAGES images present
      - Every image has a corresponding .txt caption sidecar
      - Every caption begins with DEFAULT_TRIGGER_WORD

    Raises:
        DatasetError: with a descriptive message on first failure found.
    """
    if not dataset_dir.exists():
        raise DatasetError(f"Dataset directory not found: {dataset_dir}")

    images = _image_files(dataset_dir)
    if len(images) < MIN_IMAGES:
        raise DatasetError(
            f"Dataset has {len(images)} image(s); minimum is {MIN_IMAGES}. Directory: {dataset_dir}"
        )

    missing_captions: list[str] = []
    bad_trigger: list[str] = []

    for img in images:
        sidecar = img.with_suffix(".txt")
        if not sidecar.exists():
            missing_captions.append(img.name)
            continue
        caption = sidecar.read_text(encoding="utf-8").strip()
        if not caption.startswith(DEFAULT_TRIGGER_WORD):
            bad_trigger.append(img.name)

    if missing_captions:
        raise DatasetError(f"Missing caption sidecars for: {', '.join(missing_captions)}")
    if bad_trigger:
        raise DatasetError(
            f"Captions must start with trigger word '{DEFAULT_TRIGGER_WORD}'. "
            f"Offending images: {', '.join(bad_trigger)}"
        )


def pack_zip(dataset_dir: Path = DATASET_DIR, dest: Path | None = None) -> Path:
    """
    Zip images + caption sidecars for upload to Replicate.

    Args:
        dataset_dir: Source dataset directory.
        dest:        Destination path for zip. Defaults to
                     dataset_dir.parent / (dataset_dir.name + ".zip").

    Returns:
        Path to the created zip file.

    Raises:
        DatasetError: if dataset_dir is missing or has no images.
    """
    validate_dataset(dataset_dir)

    if dest is None:
        dest = dataset_dir.parent / f"{dataset_dir.name}.zip"

    images = _image_files(dataset_dir)

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for img in images:
            zf.write(img, img.name)
            sidecar = img.with_suffix(".txt")
            if sidecar.exists():
                zf.write(sidecar, sidecar.name)

    return dest


def dataset_summary(dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    """
    Return a summary dict with image counts and total size.

    Returns:
        {
          "image_count": int,
          "caption_count": int,
          "total_bytes": int,
          "dataset_dir": str,
        }

    Raises:
        DatasetError: if directory absent.
    """
    if not dataset_dir.exists():
        raise DatasetError(f"Dataset directory not found: {dataset_dir}")

    images = _image_files(dataset_dir)
    total_bytes = sum(img.stat().st_size for img in images)
    caption_count = sum(1 for img in images if img.with_suffix(".txt").exists())

    return {
        "image_count": len(images),
        "caption_count": caption_count,
        "total_bytes": total_bytes,
        "dataset_dir": str(dataset_dir),
    }
