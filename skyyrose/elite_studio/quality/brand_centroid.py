"""Brand-style centroid: mean image embedding of approved hero shots.

The compositor pre-QA gate scores each new render's cosine similarity to
this centroid. A shot far from the centroid is off-brand and skipped before
the paid Gemini QA stage.

Supports two encoders:
  - "clip"   (default): openai/clip-vit-base-patch32, 512-d, text-image
  - "dino"            : facebook/dinov2-base, 768-d, image-only — empirically
                        ~2x better discrimination for this task

Choose via the ``encoder`` argument to ``build_centroid``.

Persistence: ``save_centroid`` writes the binary ``.npz``; ``write_metadata_sidecar``
writes a human-readable ``.metadata.json`` next to it. The sidecar is the
debuggability surface for "which approved set produced this centroid" —
binary ``.npz`` diffs are unreadable.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np

from skyyrose.core import clip_embedder, dino_embedder
from skyyrose.core.embeddings.config import get_config
from skyyrose.core.embeddings.errors import EmbeddingError, EmbeddingSpaceMismatch

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

EncoderName = Literal["clip", "dino"]

# Canonical on-disk location of the brand-style centroid (the CLIP variant). The
# compositor's stage_g + orchestrator recompute this same path locally to avoid an
# eager (torch-heavy) import of this module; new consumers that already pay the import
# cost (e.g. the oai_render QC gate) reference this constant instead of forking a copy.
DEFAULT_CENTROID_PATH = Path(__file__).resolve().parents[1] / "data" / "brand_centroid.npz"

SIDECAR_SCHEMA_VERSION = 1


@dataclass
class BrandCentroid:
    centroid: np.ndarray  # L2-normalized; 512-d for clip, 768-d for dino
    threshold: float  # cosine score below which renders fail the gate
    sample_count: int  # number of approved images that built it
    model_id: str  # encoder model used (for compatibility checking)
    sample_paths: list[str] = field(
        default_factory=list
    )  # paths used to build (best-effort; empty for legacy centroids loaded from older .npz)


def _list_images(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def _embed(encoder: EncoderName, path: Path) -> np.ndarray:
    if encoder == "dino":
        return dino_embedder.embed_image(path)
    return clip_embedder.embed_image(path)


def _model_id(encoder: EncoderName) -> str:
    return dino_embedder.MODEL_ID if encoder == "dino" else clip_embedder.MODEL_ID


def is_dino_model(model_id: str | None) -> bool:
    """True if ``model_id`` denotes a DINOv2 encoder (vs CLIP).

    Single source of truth for encoder dispatch — imported by ``embedding_gate``
    and ``render_quality`` so they cannot diverge (they previously used ``"dino"``
    vs ``"dinov2"``, which silently mis-routed any id containing one but not the
    other).
    """
    return "dino" in (model_id or "").lower()


def _expected_dim(model_id: str) -> int | None:
    """Centroid dimension implied by ``model_id``, or None when unknown.

    Synthetic ids (e.g. ``"test"``) return None so the load-time guard is skipped
    rather than rejecting a legitimately-shaped synthetic centroid.
    """
    cfg = get_config()
    if is_dino_model(model_id):
        return cfg.dino_dim
    if "clip" in (model_id or "").lower():
        return cfg.clip_dim
    return None


def build_centroid(
    approved_dir: Path,
    threshold_percentile: float = 10.0,
    encoder: EncoderName = "clip",
) -> BrandCentroid:
    """Compute centroid + a robust threshold from approved hero shots.

    Threshold is the `threshold_percentile`-th percentile of in-cluster
    cosine similarities (each approved image vs centroid). Setting it to
    10 means we accept renders at least as similar to the centroid as 90%
    of our approved set already is.

    Args:
        approved_dir: Directory of approved hero shots.
        threshold_percentile: Lower = more permissive gate.
        encoder: "clip" or "dino". DINOv2 typically ~2x discrimination gap.
    """
    paths = _list_images(approved_dir)
    if not paths:
        raise ValueError(f"no image files in {approved_dir}")

    embeddings = np.stack([_embed(encoder, p) for p in paths])
    raw_centroid = embeddings.mean(axis=0)
    norm = np.linalg.norm(raw_centroid)
    if norm < 1e-9:
        raise ValueError("degenerate centroid (zero magnitude)")
    centroid = (raw_centroid / norm).astype(np.float32)

    # In-cluster similarity distribution -> robust threshold.
    sims = embeddings @ centroid
    threshold = float(np.percentile(sims, threshold_percentile))

    return BrandCentroid(
        centroid=centroid,
        threshold=threshold,
        sample_count=len(paths),
        model_id=_model_id(encoder),
        sample_paths=[str(p) for p in paths],
    )


def save_centroid(c: BrandCentroid, path: Path) -> None:
    """Write the centroid ``.npz`` atomically (tmp + ``os.replace``).

    A crash mid-write would otherwise leave a truncated ``.npz`` that passes
    ``exists()`` but fails ``np.load`` — routing a paid render into a crash
    instead of the graceful fallback (E-store). ``dim`` is stamped for provenance
    and load-time validation (E-space). Written via a file handle so ``np.savez``
    does not append a second ``.npz`` to the tmp name and break the rename.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "wb") as fh:
            np.savez(
                fh,
                centroid=c.centroid,
                threshold=np.array(c.threshold, dtype=np.float32),
                sample_count=np.array(c.sample_count, dtype=np.int64),
                model_id=np.array(c.model_id),
                dim=np.array(int(c.centroid.shape[0]), dtype=np.int64),
            )
        os.replace(tmp, path)
    except OSError:
        Path(tmp).unlink(missing_ok=True)
        raise


def load_centroid(path: Path) -> BrandCentroid:
    """Load a centroid ``.npz``, guarding corruption and embedding-space mismatch.

    Raises :class:`EmbeddingError` on an unreadable/corrupt/incomplete file and
    :class:`EmbeddingSpaceMismatch` when the stored dimension disagrees with the
    encoder implied by ``model_id`` (e.g. a 512-d CLIP centroid mislabeled as
    DINOv2) — a clear typed failure instead of a cryptic numpy shape error on a
    paid render (E-space).
    """
    path = Path(path)
    try:
        data = np.load(path, allow_pickle=False)
    except (OSError, ValueError, EOFError, zipfile.BadZipFile) as exc:
        raise EmbeddingError(f"corrupt or unreadable centroid {path}: {exc}") from exc
    try:
        centroid = data["centroid"]
        model_id = str(data["model_id"])
        threshold = float(data["threshold"])
        sample_count = int(data["sample_count"])
    except KeyError as exc:
        raise EmbeddingError(f"centroid {path} missing required key {exc}") from exc

    expected = _expected_dim(model_id)
    actual = int(centroid.shape[0])
    if expected is not None and actual != expected:
        raise EmbeddingSpaceMismatch(
            f"centroid dim {actual} != {expected} expected for model {model_id!r} ({path})"
        )

    return BrandCentroid(
        centroid=centroid,
        threshold=threshold,
        sample_count=sample_count,
        model_id=model_id,
    )


def _sample_paths_hash(paths: list[str]) -> str:
    """Stable hash of the (sorted) basenames that built a centroid.

    Used as a provenance fingerprint in the sidecar. If the approved-shot
    set changes (rename, add, remove), the hash changes — surfaces drift
    that would otherwise be invisible because ``.npz`` diffs are binary.
    """
    basenames = sorted(Path(p).name for p in paths)
    payload = "\n".join(basenames).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _file_sha256(path: Path) -> str:
    """SHA-256 of a file (truncated to 16 hex chars for readability)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def write_metadata_sidecar(
    c: BrandCentroid,
    npz_path: Path,
    *,
    encoder: EncoderName | None = None,
) -> Path:
    """Write a human-readable JSON sidecar next to ``npz_path``.

    Returns the sidecar path. Idempotent — overwrites if it exists.

    The sidecar records: schema version, encoder + model_id (so a CLIP/DINOv2
    swap is detectable), sample count + threshold + centroid dim/norm
    (cheap sanity checks), sample paths + their hash (provenance), and
    a SHA-256 of the .npz itself (catches binary tampering).
    """
    npz_path = Path(npz_path)
    sidecar_path = npz_path.with_suffix(".metadata.json")

    inferred_encoder: EncoderName
    if encoder is not None:
        inferred_encoder = encoder
    elif "dino" in c.model_id.lower():
        inferred_encoder = "dino"
    else:
        inferred_encoder = "clip"

    payload = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "encoder": inferred_encoder,
        "model_id": c.model_id,
        "sample_count": c.sample_count,
        "threshold": round(c.threshold, 6),
        "centroid_dim": int(c.centroid.shape[0]),
        "centroid_l2_norm": round(float(np.linalg.norm(c.centroid)), 6),
        "sample_paths": list(c.sample_paths),
        "sample_paths_hash": _sample_paths_hash(c.sample_paths) if c.sample_paths else None,
        "npz_filename": npz_path.name,
        "npz_sha256": _file_sha256(npz_path) if npz_path.exists() else None,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return sidecar_path


def save_centroid_with_sidecar(
    c: BrandCentroid,
    path: Path,
    *,
    encoder: EncoderName | None = None,
) -> tuple[Path, Path]:
    """Convenience: write both the ``.npz`` and the ``.metadata.json``.

    Returns (npz_path, sidecar_path).
    """
    save_centroid(c, path)
    sidecar_path = write_metadata_sidecar(c, path, encoder=encoder)
    return Path(path), sidecar_path
