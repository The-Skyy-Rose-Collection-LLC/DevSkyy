"""
scripts.flux_lora.dataset_builder — Assemble a FLUX LoRA training dataset.

Public API
----------
build_dataset(sources, dest_dir, *, trigger_word, overwrite) -> Path

Rules
-----
- Caption sidecar (.txt) MUST start with trigger_word.
- If caller supplies "caption" that already starts with trigger_word → use as-is.
- If caller supplies "caption" without trigger_word → prepend it.
- If caller supplies "garment" only → compose "<trigger_word> <garment>".
- If neither "caption" nor "garment" → raise DatasetError (no ML-authored captions).
- Non-empty dest_dir without overwrite=True → raise DatasetError.
- Each source["image"] must exist on disk → raise DatasetError if missing.
- Preserves source image extension (stems normalized: img_01, img_02, …).
- Pure stdlib — no network, no third-party deps.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from scripts.flux_lora import DatasetError
from scripts.flux_lora.config import DEFAULT_TRIGGER_WORD
from scripts.flux_lora.dataset import IMAGE_EXTENSIONS, validate_dataset


def _compose_caption(
    source: dict[str, Any],
    trigger_word: str,
) -> str:
    """
    Derive a caption string from a source dict.

    Priority:
      1. "caption" key — use as-is if already starts with trigger_word, else prepend.
      2. "garment" key — compose "<trigger_word> <garment>".
      3. Neither → raise DatasetError.
    """
    caption: str | None = source.get("caption")
    garment: str | None = source.get("garment")

    if caption is not None:
        caption = caption.strip()
        if caption.lower().startswith(trigger_word.lower()):
            return caption
        return f"{trigger_word} {caption}"

    if garment is not None:
        garment = garment.strip()
        if not garment:
            raise DatasetError(
                "source 'garment' value is empty; provide a non-empty garment description "
                "or an explicit 'caption'."
            )
        return f"{trigger_word} {garment}"

    raise DatasetError(
        "Every source must include 'caption' or 'garment'. "
        "ML-authored captions are not permitted — provide an author-written caption."
    )


def build_dataset(
    sources: list[dict[str, Any]],
    dest_dir: str | Path,
    *,
    trigger_word: str = DEFAULT_TRIGGER_WORD,
    overwrite: bool = False,
) -> Path:
    """
    Assemble a FLUX LoRA training dataset directory from a list of source dicts.

    Parameters
    ----------
    sources:
        List of dicts, each with:
          - "image"   : str or Path — source image file (required, must exist).
          - "caption" : str          — author-written caption (optional).
          - "garment" : str          — garment description, used when caption absent.
        Either "caption" or "garment" must be present.

    dest_dir:
        Directory to write normalized images + caption sidecars into.

    trigger_word:
        Token prepended to every caption (default: "SKYYROSE").

    overwrite:
        If True, clear dest_dir contents before writing.
        If False (default), raise DatasetError when dest_dir is non-empty.

    Returns
    -------
    Path
        Resolved path to dest_dir after successful build + validation.

    Raises
    ------
    DatasetError
        - dest_dir non-empty and overwrite=False.
        - Any source image missing or not a file.
        - Any source has neither "caption" nor "garment".
        - validate_dataset() fails (< MIN_IMAGES, missing sidecar, bad trigger).
    """
    if not sources:
        raise DatasetError("sources list is empty; provide at least one source image.")

    dest = Path(dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    # Clobber guard
    existing = list(dest.iterdir())
    if existing and not overwrite:
        raise DatasetError(
            f"dest_dir '{dest}' is non-empty ({len(existing)} entries). "
            "Pass overwrite=True to replace its contents."
        )
    if existing and overwrite:
        # Remove dataset files only (images + .txt sidecars) to avoid nuking unrelated files
        for child in dest.iterdir():
            if child.suffix.lower() in IMAGE_EXTENSIONS or child.suffix == ".txt":
                child.unlink()

    # Validate all source images exist before writing anything
    errors: list[str] = []
    for i, src in enumerate(sources):
        img_path = Path(src.get("image", ""))
        if not img_path.exists() or not img_path.is_file():
            errors.append(f"source[{i}] image not found: '{img_path}'")
    if errors:
        raise DatasetError("\n".join(errors))

    # Copy images + write sidecars
    for idx, src in enumerate(sources, start=1):
        img_src = Path(src["image"])
        suffix = img_src.suffix.lower()

        stem = f"img_{idx:02d}"
        img_dest = dest / f"{stem}{suffix}"
        txt_dest = dest / f"{stem}.txt"

        shutil.copy2(img_src, img_dest)

        caption = _compose_caption(src, trigger_word)
        txt_dest.write_text(caption, encoding="utf-8")

    # Validate the assembled dataset
    validate_dataset(dest)

    return dest
