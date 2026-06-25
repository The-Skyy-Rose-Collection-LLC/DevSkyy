"""Single source of truth for torch device selection.

Was copy-pasted verbatim across ``clip_embedder.py`` and ``dino_embedder.py``
(E-dedup). Imported lazily by encoders so merely importing the package does not
pull torch into the import graph.

@package SkyyRose
"""

from __future__ import annotations

import torch


def select_device() -> str:
    """Return the best available torch device string: ``cuda`` > ``mps`` > ``cpu``."""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_dtype(name: str) -> torch.dtype:
    """Map a config dtype string (e.g. ``"float32"``) to a ``torch.dtype``.

    Shared by both encoders (E-dedup). Raises :class:`EmbedError` on an unknown
    name so a typo'd ``SKYYROSE_EMBED_DTYPE`` fails loudly at load, not silently.
    """
    from skyyrose.core.embeddings.errors import EmbedError

    candidate = getattr(torch, name, None)
    if not isinstance(candidate, torch.dtype):
        raise EmbedError(f"unknown torch dtype: {name!r}")
    return candidate


def dtype_load_kwargs(dtype: torch.dtype) -> dict:
    """Return the ``from_pretrained`` dtype kwarg under the right name for the
    installed transformers major.

    transformers 5+ renamed ``torch_dtype`` -> ``dtype``; on 4.x the new name is
    silently ignored. The project floor is ``transformers>=4.53``, so pin under
    whichever name the installed version actually honors — otherwise E-determinism
    is a no-op on a 4.x install.
    """
    import transformers

    major = int(transformers.__version__.split(".")[0])
    return {"dtype": dtype} if major >= 5 else {"torch_dtype": dtype}
