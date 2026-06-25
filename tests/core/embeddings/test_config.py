"""EmbeddingConfig: pinned revisions (E-revpin), frozen (E-config), env-overridable.

Model-free — never constructs an encoder or loads a model."""

from __future__ import annotations

import pydantic
import pytest

from skyyrose.core.embeddings.config import EmbeddingConfig, get_config


def test_defaults_carry_pinned_revisions():
    cfg = EmbeddingConfig()
    # Real SHAs resolved via HfApi on 2026-06-24 — full 40-char commit hashes, not branch names.
    assert cfg.clip_revision == "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
    assert cfg.dino_revision == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    assert len(cfg.clip_revision) == 40
    assert len(cfg.dino_revision) == 40


def test_default_models_and_dims():
    cfg = EmbeddingConfig()
    assert cfg.clip_model_id == "openai/clip-vit-base-patch32"
    assert cfg.clip_dim == 512
    assert cfg.dino_model_id == "facebook/dinov2-base"
    assert cfg.dino_dim == 768
    assert cfg.dtype == "float32"
    assert cfg.max_image_pixels == 64_000_000


def test_is_frozen():
    cfg = EmbeddingConfig()
    with pytest.raises(pydantic.ValidationError):
        cfg.clip_dim = 999  # type: ignore[misc]


def test_env_override(monkeypatch):
    monkeypatch.setenv("SKYYROSE_EMBED_CLIP_DIM", "1024")
    monkeypatch.setenv("SKYYROSE_EMBED_DTYPE", "bfloat16")
    cfg = EmbeddingConfig()
    assert cfg.clip_dim == 1024
    assert cfg.dtype == "bfloat16"


def test_get_config_is_singleton():
    assert get_config() is get_config()
