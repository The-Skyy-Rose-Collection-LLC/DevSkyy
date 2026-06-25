"""DINOv2 encoder — ``facebook/dinov2-base``, 768-d CLS token, image-only.

Stronger than CLIP-base for pure image-image visual similarity (brand-style
centroid scoring). Revision-pinned and dtype-pinned via :class:`EmbeddingConfig`
(E-revpin, E-determinism). No text encoder — complementary to CLIP, not a
replacement.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

from skyyrose.core.embeddings.base import BaseEncoder
from skyyrose.core.embeddings.device import dtype_load_kwargs, resolve_dtype
from skyyrose.core.embeddings.space import EmbeddingSpace


class DinoEncoder(BaseEncoder):
    """Thread-safe lazy DINOv2 singleton producing 768-d L2-normalized CLS vectors."""

    def _build_space(self) -> EmbeddingSpace:
        c = self._config
        return EmbeddingSpace(
            model_id=c.dino_model_id,
            dim=c.dino_dim,
            preprocess_version=c.preprocess_version,
            normalized=True,
            revision=c.dino_revision,
        )

    def _load(self, device: str) -> tuple[Any, Any]:
        c = self._config
        dtype = resolve_dtype(c.dtype)
        model = (
            AutoModel.from_pretrained(
                c.dino_model_id,
                revision=c.dino_revision,
                use_safetensors=c.dino_use_safetensors,
                **dtype_load_kwargs(dtype),
            )
            .to(device)
            .eval()
        )  # nosec B615 — revision pinned to a full commit SHA from EmbeddingConfig (E-revpin)
        processor = AutoImageProcessor.from_pretrained(
            c.dino_model_id,
            revision=c.dino_revision,
        )  # nosec B615 — processor carries no weights; revision pinned (E-revpin)
        return model, processor

    def _encode_pils(self, images: list[Image.Image]) -> np.ndarray:
        inputs = self._processor(images=images, return_tensors="pt").to(self._device)
        with torch.no_grad():
            outputs = self._model(**inputs)
        # CLS token is position 0 of the last hidden state.
        cls = outputs.last_hidden_state[:, 0, :].cpu().numpy().astype(np.float32)
        return cls
