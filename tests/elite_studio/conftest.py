"""Skip embedder-dependent elite_studio tests when HF models can't be loaded.

The CLIP/DINO embedder tests load real models from the HuggingFace Hub on first
use (``openai/clip-vit-base-patch32`` ~600MB, ``facebook/dinov2`` ~330MB). On a
cold CI runner the Hub rate-limits (HTTP 429) or is unreachable; transformers
surfaces that as ``OSError`` ("We couldn't connect to 'https://huggingface.co'
... and couldn't find them in the cached files"). That is an environment
condition, not a defect, so these tests should *skip* deterministically rather
than fail the whole pipeline. They still run wherever the model is available
(warm cache / local dev), preserving real coverage.

Mirrors the root ``conftest.py`` convention of skipping tests when a prerequisite
is unavailable (there: the rebuilt ``wordpress`` module; here: the HF weights).
"""

from __future__ import annotations

import functools

import pytest

# Exceptions that mean "the model could not be fetched/loaded from the Hub or
# local cache" — i.e. an environment problem, not a code defect. transformers'
# ``from_pretrained`` raises ``OSError`` on connection/cache miss; ``ImportError``
# guards a runner without torch/transformers installed. huggingface_hub HTTP
# errors are added defensively for code paths that re-raise them un-wrapped.
_UNAVAILABLE: tuple[type[BaseException], ...] = (OSError, ImportError)
try:  # pragma: no cover - import shape varies across hub versions
    from huggingface_hub.errors import HfHubHTTPError

    _UNAVAILABLE = (*_UNAVAILABLE, HfHubHTTPError)
except ImportError:  # pragma: no cover
    pass


@functools.lru_cache(maxsize=1)
def _clip_skip_reason() -> str | None:
    """Return None if CLIP loads, else a skip reason. Loads at most once per session."""
    try:
        from skyyrose.core import clip_embedder

        clip_embedder.get_clip()
        return None
    except _UNAVAILABLE as exc:
        return f"CLIP model unavailable: {type(exc).__name__}: {exc}"


@functools.lru_cache(maxsize=1)
def _dino_skip_reason() -> str | None:
    """Return None if DINOv2 loads, else a skip reason. Loads at most once per session."""
    try:
        from skyyrose.core import dino_embedder

        dino_embedder.get_dino()
        return None
    except _UNAVAILABLE as exc:
        return f"DINOv2 model unavailable: {type(exc).__name__}: {exc}"


@pytest.fixture(scope="session")
def clip_model_available() -> None:
    """Skip the requesting test/module when the CLIP weights can't be loaded."""
    reason = _clip_skip_reason()
    if reason:
        pytest.skip(reason)


@pytest.fixture(scope="session")
def dino_model_available() -> None:
    """Skip the requesting test/module when the DINOv2 weights can't be loaded."""
    reason = _dino_skip_reason()
    if reason:
        pytest.skip(reason)
