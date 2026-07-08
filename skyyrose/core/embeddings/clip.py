"""CLIP encoder — ``openai/clip-vit-base-patch32``, 512-d, shared text+image space.

Revision-pinned and dtype-pinned via :class:`EmbeddingConfig` (E-revpin,
E-determinism). The projected image/text features are extracted via
:meth:`_projected`: transformers >=5 wraps ``get_*_features`` output in a
``BaseModelOutputWithPooling`` whose ``pooler_output`` holds the projected
embeds; older versions returned the tensor directly. The fallback handles both.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from PIL import Image

from skyyrose.core.embeddings.base import BaseEncoder
from skyyrose.core.embeddings.errors import EmbedError
from skyyrose.core.embeddings.space import EmbeddingSpace

if TYPE_CHECKING:
    import torch


class ClipEncoder(BaseEncoder):
    """Thread-safe lazy CLIP singleton producing 512-d L2-normalized vectors."""

    def _build_space(self) -> EmbeddingSpace:
        c = self._config
        return EmbeddingSpace(
            model_id=c.clip_model_id,
            dim=c.clip_dim,
            preprocess_version=c.preprocess_version,
            normalized=True,
            revision=c.clip_revision,
        )

    def _load(self, device: str) -> tuple[Any, Any]:
        try:
            from transformers import CLIPModel, CLIPProcessor

            from skyyrose.core.embeddings.device import dtype_load_kwargs, resolve_dtype
        except ImportError as exc:
            raise ImportError(
                "CLIP embeddings require the 'ml' extra. Install with: pip install -e '.[ml]'"
            ) from exc

        c = self._config
        dtype = resolve_dtype(c.dtype)
        model = (
            CLIPModel.from_pretrained(
                c.clip_model_id,
                revision=c.clip_revision,
                use_safetensors=c.clip_use_safetensors,
                **dtype_load_kwargs(dtype),
            )
            .to(device)
            .eval()
        )  # nosec B615 — revision pinned to a full commit SHA from EmbeddingConfig (E-revpin)
        processor = CLIPProcessor.from_pretrained(
            c.clip_model_id,
            revision=c.clip_revision,
        )  # nosec B615 — processor carries no weights; revision pinned (E-revpin)
        return model, processor

    @staticmethod
    def _projected(features: Any) -> torch.Tensor:
        """Extract the projected embedding tensor.

        transformers 5.x ``get_image_features`` / ``get_text_features`` return a
        ``BaseModelOutputWithPooling`` whose ``.pooler_output`` is the projected
        (512-d) embedding; the fallback returns ``features`` itself when it is a
        raw tensor (e.g. test doubles).
        """
        return getattr(features, "pooler_output", features)

    def _encode_pils(self, images: list[Image.Image]) -> np.ndarray:
        import torch

        inputs = self._processor(images=images, return_tensors="pt").to(self._device)
        with torch.no_grad():
            feats = self._projected(self._model.get_image_features(**inputs))
        return feats.cpu().numpy().astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        """Encode text → 512-d L2-normalized vector (shares CLIP's image space)."""
        if not text or not text.strip():
            raise EmbedError("embed_text requires non-empty text")
        self._ensure_loaded()
        import torch

        inputs = self._processor(
            text=[text], return_tensors="pt", padding=True, truncation=True
        ).to(self._device)
        with torch.no_grad():
            feats = self._projected(self._model.get_text_features(**inputs))
        vec = feats.squeeze(0).cpu().numpy().astype(np.float32)
        return self._l2_normalize(vec)
