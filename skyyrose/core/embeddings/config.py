"""Frozen embedding configuration: model ids, pinned weight revisions, dims, dtype.

Replaces the hardcoded ``MODEL_ID``/``EMBED_DIM`` constants scattered across the
old embedders (E-config). Every field is overridable via a ``SKYYROSE_EMBED_*``
environment variable; the instance is **frozen** so a loaded config cannot be
mutated mid-run (which would be a silent model swap).

Pinned HF revisions (E-revpin) default to the commit SHAs resolved 2026-06-24 via
the HF Hub API (``HfApi().model_info(repo).sha``). Pinning ``revision`` makes
``from_pretrained`` resolve a fixed commit instead of branch ``HEAD``, removing
the silent-weight-drift supply-chain risk.

No secrets live on this object — the encoders load public HF models anonymously,
so there is nothing to leak via serialization.

@package SkyyRose
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingConfig(BaseSettings):
    """Immutable embedding configuration. Override fields via ``SKYYROSE_EMBED_*`` env vars."""

    model_config = SettingsConfigDict(env_prefix="SKYYROSE_EMBED_", frozen=True)

    # CLIP (openai/clip-vit-base-patch32) — 512-d, text+image.
    clip_model_id: str = "openai/clip-vit-base-patch32"
    clip_revision: str = "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
    clip_dim: int = 512
    # This repo/SHA ships ONLY pytorch_model.bin (no safetensors), so we cannot
    # force safetensors here. transformers 5.x loads the .bin with weights_only=True
    # (no arbitrary-code-exec); the revision pin is the supply-chain control.
    clip_use_safetensors: bool = False

    # DINOv2 (facebook/dinov2-base) — 768-d CLS token, image only.
    dino_model_id: str = "facebook/dinov2-base"
    dino_revision: str = "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    dino_dim: int = 768
    # This repo/SHA ships model.safetensors, so enforce the no-pickle load path.
    dino_use_safetensors: bool = True

    # Determinism (E-determinism): pin load dtype so MPS/CUDA bit-drift can't move vectors.
    dtype: str = "float32"
    # Bumped whenever the HF transformers major changes preprocessing; folded into EmbeddingSpace.
    preprocess_version: str = "hf-transformers-5"

    # Decompression-bomb cap (E-bomb): max pixels PIL will decode. 64 MP ~ 8000x8000,
    # comfortably above any product render, far below a multi-GB OOM bomb.
    max_image_pixels: int = 64_000_000

    # None => auto-detect via device.select_device().
    device: str | None = None


@lru_cache(maxsize=1)
def get_config() -> EmbeddingConfig:
    """Process-wide singleton config (reads env once)."""
    return EmbeddingConfig()
