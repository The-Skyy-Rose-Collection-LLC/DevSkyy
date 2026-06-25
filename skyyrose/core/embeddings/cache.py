"""Content-hash read-through embedding cache (E-cache).

Keyed by ``sha256(image bytes)`` namespaced by :meth:`EmbeddingSpace.key`, which
gives three properties the old id/path-keyed caches lacked:

  - **Idempotent:** identical pixels are never re-embedded.
  - **Overwrite-safe:** the render pipeline overwrites shadow PNGs at *stable*
    paths; a path-keyed cache would return a stale vector for changed pixels.
    Keying on the bytes means changed pixels miss and recompute.
  - **Re-pin-safe:** a model revision change bumps ``space.key()`` so the cache
    misses cleanly instead of serving vectors from old weights.

Default backend is an in-memory dict. Pass ``disk_dir`` to persist across
processes; on-disk reads are corruption-tolerant (a truncated/garbage file is a
cache miss, never a fatal error on the render path). Disk writes are atomic
(tmp + ``os.replace``).

Only file sources (path/str) are cached — an in-memory ``PIL.Image`` has no
stable byte identity, so it falls through to a direct encode.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import numpy as np

from skyyrose.core.embeddings.base import BaseEncoder, ImageSource
from skyyrose.core.embeddings.errors import EmbedError

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Read-through cache wrapping any :class:`BaseEncoder`."""

    def __init__(self, encoder: BaseEncoder, *, disk_dir: Path | str | None = None) -> None:
        self._encoder = encoder
        self._mem: dict[str, np.ndarray] = {}
        self._disk_dir = Path(disk_dir) if disk_dir is not None else None
        if self._disk_dir is not None:
            self._disk_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _key(self, digest: str) -> str:
        return f"{self._encoder.space.key()}:{digest}"

    def _disk_path(self, key: str) -> Path:
        assert self._disk_dir is not None  # nosec B101 — guarded by caller
        # Filename is a hash of the full namespaced key (keeps it filesystem-safe).
        fname = hashlib.sha256(key.encode("utf-8")).hexdigest() + ".npy"
        return self._disk_dir / fname

    def _load_disk(self, key: str) -> np.ndarray | None:
        if self._disk_dir is None:
            return None
        path = self._disk_path(key)
        if not path.exists():
            return None
        try:
            return np.load(path, allow_pickle=False)
        except (OSError, ValueError, EOFError) as exc:  # truncated / corrupt → miss
            logger.warning("embedding cache: ignoring corrupt entry %s (%s)", path.name, exc)
            return None

    def _store_disk(self, key: str, vector: np.ndarray) -> None:
        if self._disk_dir is None:
            return
        path = self._disk_path(key)
        # Write via a file handle (not a string path) so np.save doesn't append
        # a second ".npy" to the tmp name and break the rename.
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "wb") as fh:
                np.save(fh, vector)
            os.replace(tmp, path)  # atomic
        except OSError as exc:
            logger.warning("embedding cache: failed to persist %s (%s)", path.name, exc)
            tmp.unlink(missing_ok=True)

    def embed(self, source: ImageSource) -> np.ndarray:
        """Return the (cached) embedding for ``source``.

        File sources are cached by content hash; an in-memory PIL image is
        encoded directly (no stable identity to key on).
        """
        if not isinstance(source, (str, Path)):
            return self._encoder.embed_image(source)

        try:
            data = Path(source).read_bytes()
        except OSError as exc:
            raise EmbedError(f"cache could not read {source}: {exc}") from exc

        key = self._key(self._hash_bytes(data))

        # OBS-wire: record cache HITS here (latency ~0, cache_hit=True). MISSES fall
        # through to encoder.embed_image -> BaseEncoder.embed_images, which records
        # its own cache_hit=False row — so each encode is counted exactly once.
        cached = self._mem.get(key)
        if cached is not None:
            self._record_hit()
            return cached

        disk = self._load_disk(key)
        if disk is not None:
            self._mem[key] = disk
            self._record_hit()
            return disk

        vector = self._encoder.embed_image(source)
        self._mem[key] = vector
        self._store_disk(key, vector)
        return vector

    def _record_hit(self) -> None:
        """Emit one cache-hit telemetry row (lazy import; never raises)."""
        from core.token_tracker import record_embedding_usage

        record_embedding_usage(
            model=self._encoder.space.model_id,
            latency_ms=0.0,
            success=True,
            cache_hit=True,
            dim=self._encoder.space.dim,
            count=1,
        )
