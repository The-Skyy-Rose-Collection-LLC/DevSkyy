"""Shared encoder base: device, normalization, decompression-bomb guard, fd-safe
image loading, batch encoding, lazy thread-safe singleton machinery.

Centralizes everything copy-pasted across the old ``clip_embedder.py`` and
``dino_embedder.py`` (E-dedup) and fixes the cross-cutting safety gaps once:

  - E-bomb     : ``Image.MAX_IMAGE_PIXELS`` capped process-wide at import.
  - E-fd       : every ``Image.open`` is context-managed (no fd leak under bulk).
  - E-errors   : load failures become :class:`EmbedError`, never raw PIL/OS errors.
  - E-zeronorm : a near-zero vector raises instead of being accepted as cosine 0.0.
  - E-batch    : ``embed_images`` runs one forward pass per chunk, not per image.

Subclasses implement three hooks: :meth:`_build_space`, :meth:`_load`,
:meth:`_encode_pils`. Everything else (lazy load, RGB decode, L2-norm, batching)
lives here.

@package SkyyRose
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from skyyrose.core.embeddings.config import EmbeddingConfig, get_config
from skyyrose.core.embeddings.errors import EmbedError, ZeroNormEmbeddingError
from skyyrose.core.embeddings.space import EmbeddingSpace

logger = logging.getLogger(__name__)

# E-bomb: cap the pixels PIL will decode, process-wide, the moment this package
# loads. A 50k x 50k PNG would otherwise allocate multiple GB before any code
# runs. Set once here; every Image.open in the process inherits it.
Image.MAX_IMAGE_PIXELS = get_config().max_image_pixels

_ZERO_NORM_EPS = 1e-9
_DEFAULT_BATCH_SIZE = 32

ImageSource = Path | str | Image.Image


class BaseEncoder(ABC):
    """Abstract lazy-singleton image encoder.

    Thread-safe: the model loads once on first use behind a lock. Stateless after
    load — safe to share one instance across threads.
    """

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self._config = config or get_config()
        self._lock = Lock()
        self._loaded = False
        self._model: Any = None
        self._processor: Any = None
        self._device: str | None = None
        self._space: EmbeddingSpace | None = None

    # ------------------------------------------------------------------ hooks
    @abstractmethod
    def _build_space(self) -> EmbeddingSpace:
        """Return the immutable :class:`EmbeddingSpace` this encoder produces."""

    @abstractmethod
    def _load(self, device: str) -> tuple[Any, Any]:
        """Load and return ``(model, processor)`` on ``device`` (called once, locked)."""

    @abstractmethod
    def _encode_pils(self, images: list[Image.Image]) -> np.ndarray:
        """Forward pass over RGB PIL images → ``(N, dim)`` *unnormalized* float32 matrix."""

    # ------------------------------------------------------------------ public
    @property
    def space(self) -> EmbeddingSpace:
        if self._space is None:
            self._space = self._build_space()
        return self._space

    @property
    def device(self) -> str:
        self._ensure_loaded()
        assert self._device is not None  # nosec B101 — set by _ensure_loaded
        return self._device

    def embed_image(self, source: ImageSource) -> np.ndarray:
        """Encode one image → L2-normalized float32 vector of length ``space.dim``."""
        return self.embed_images([source])[0]

    def embed_images(
        self, sources: list[ImageSource], *, batch_size: int = _DEFAULT_BATCH_SIZE
    ) -> np.ndarray:
        """Encode many images → ``(N, dim)`` L2-normalized float32 matrix (E-batch).

        Runs one forward pass per ``batch_size`` chunk, bounding peak memory while
        still amortizing the GPU matmul across the batch.
        """
        if not sources:
            raise EmbedError("embed_images requires at least one image")
        if batch_size < 1:
            raise EmbedError(f"batch_size must be >= 1, got {batch_size}")
        self._ensure_loaded()
        # OBS-wire: one telemetry row per encode (latency, success, count). Imported
        # lazily so the package still imports without core/ side effects; the helper
        # never raises, so telemetry cannot break the encode path.
        from core.token_tracker import record_embedding_usage

        started = time.perf_counter()
        try:
            out: list[np.ndarray] = []
            for start in range(0, len(sources), batch_size):
                chunk = sources[start : start + batch_size]
                images = [self._open(s) for s in chunk]
                raw = self._encode_pils(images)
                out.extend(self._l2_normalize(row) for row in raw)
            result = np.stack(out)
        except Exception as exc:
            record_embedding_usage(
                model=self.space.model_id,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                success=False,
                cache_hit=False,
                dim=self.space.dim,
                count=len(sources),
                error=str(exc),
            )
            raise
        record_embedding_usage(
            model=self.space.model_id,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            success=True,
            cache_hit=False,
            dim=self.space.dim,
            count=len(sources),
        )
        return result

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Dot product of two same-shape L2-normalized vectors."""
        if a.shape != b.shape:
            raise EmbedError(f"shape mismatch: {a.shape} vs {b.shape}")
        return float(np.dot(a, b))

    # ------------------------------------------------------------------ internals
    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            # Imported here (not at module top) so the package imports without torch.
            try:
                from skyyrose.core.embeddings.device import select_device
            except ImportError as exc:
                raise ImportError(
                    f"{type(self).__name__} requires the 'ml' extra. "
                    "Install with: pip install -e '.[ml]'"
                ) from exc

            self._device = self._config.device or select_device()
            logger.info("Loading %s on %s", self.space.key(), self._device)
            self._model, self._processor = self._load(self._device)
            self._loaded = True

    @staticmethod
    def _open(source: ImageSource) -> Image.Image:
        """Load ``source`` as an RGB image, fd-safe, with typed errors.

        E-fd: the file handle is closed via the context manager. E-errors: a
        missing/corrupt/oversized image becomes :class:`EmbedError` instead of a
        raw PIL/OS exception propagating onto the render path.
        """
        if isinstance(source, Image.Image):
            return source.convert("RGB")
        if not isinstance(source, (str, Path)):
            raise EmbedError(f"expected path or PIL.Image, got {type(source).__name__}")
        try:
            with Image.open(source) as raw:
                return raw.convert("RGB")
        except FileNotFoundError as exc:
            raise EmbedError(f"image not found: {source}") from exc
        except UnidentifiedImageError as exc:
            raise EmbedError(f"unreadable image: {source}") from exc
        except OSError as exc:  # truncated file, decompression-bomb refusal, IO error
            raise EmbedError(f"failed to read image {source}: {exc}") from exc

    def _l2_normalize(self, vector: np.ndarray) -> np.ndarray:
        """L2-normalize to float32; raise on a near-zero norm (E-zeronorm)."""
        norm = float(np.linalg.norm(vector))
        if norm < _ZERO_NORM_EPS:
            raise ZeroNormEmbeddingError("zero-norm embedding (blank or degenerate image)")
        return (vector / norm).astype(np.float32)
