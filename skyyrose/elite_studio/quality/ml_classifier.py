"""
ML Classifier — CLIP-based fast quality predictor.

Uses openai/clip-vit-base-patch32 to score images without an LLM call.
Falls back to a neutral mock result when transformers is not installed.

Model is cached per-process via lru_cache so it loads once.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

_CANDIDATE_LABELS = [
    "high quality fashion photo",
    "low quality blurry photo",
    "inappropriate content",
]
_CLIP_MODEL_ID = "openai/clip-vit-base-patch32"

# Label → numeric quality score mapping
_LABEL_SCORES: dict[str, float] = {
    "high quality fashion photo": 0.9,
    "low quality blurry photo": 0.2,
    "inappropriate content": 0.0,
}


@dataclass(frozen=True)
class ClassifierResult:
    """Output from the CLIP quality classifier."""

    success: bool
    score: float  # 0.0 – 1.0 quality score
    confidence: float  # softmax confidence of the top label
    label: str  # winning label text
    error: str = ""


# ---------------------------------------------------------------------------
# Model loading — cached once per process
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_clip_model() -> tuple:
    """Load CLIP model and processor, cached for the process lifetime.

    Returns:
        (model, processor) tuple from transformers.

    Raises:
        ImportError: if transformers is not installed.
    """
    from transformers import CLIPModel, CLIPProcessor  # type: ignore[import]

    logger.info("Loading CLIP model %s (first call — subsequent calls use cache)", _CLIP_MODEL_ID)
    processor = CLIPProcessor.from_pretrained(_CLIP_MODEL_ID)  # nosec B615 — model ID constant defined at module level; well-known public CLIP model
    model = CLIPModel.from_pretrained(_CLIP_MODEL_ID)  # nosec B615 — same
    model.eval()
    return model, processor


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


class QualityClassifier:
    """CLIP-based fast quality predictor.

    Scores an image against candidate labels using zero-shot classification.
    The resulting score is a weighted combination of label probabilities,
    mapped to a 0.0–1.0 quality range.

    If transformers is not installed the classifier returns a neutral
    fallback result (score=0.5, confidence=0.3, label="uncertain") so
    the graph can fall through to the LLM-based QualityAgent instead.
    """

    def predict(self, image_path: str) -> ClassifierResult:
        """Score image quality.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            ClassifierResult with score 0.0–1.0.
        """
        try:
            return self._run_clip(image_path)
        except ImportError:
            logger.warning(
                "transformers not installed — returning neutral classifier fallback. "
                "Install with: pip install transformers torch"
            )
            return ClassifierResult(
                success=True,
                score=0.5,
                confidence=0.3,
                label="uncertain",
            )
        except Exception as exc:
            logger.error("CLIP classifier error: %s", exc)
            return ClassifierResult(
                success=False,
                score=0.0,
                confidence=0.0,
                label="error",
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_clip(self, image_path: str) -> ClassifierResult:
        """Run CLIP zero-shot classification.

        Args:
            image_path: Path to image.

        Returns:
            ClassifierResult.

        Raises:
            ImportError: if transformers or PIL is not installed.
        """
        import torch  # type: ignore[import]
        from PIL import Image  # type: ignore[import]

        model, processor = _load_clip_model()

        image = Image.open(image_path).convert("RGB")
        inputs = processor(
            text=_CANDIDATE_LABELS,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image  # (1, num_labels)
            probs = logits_per_image.softmax(dim=1).squeeze(0)  # (num_labels,)

        prob_list: list[float] = probs.tolist()
        top_idx: int = int(probs.argmax().item())
        top_label = _CANDIDATE_LABELS[top_idx]
        confidence = prob_list[top_idx]

        # Compute weighted quality score across all labels
        score = sum(
            prob * _LABEL_SCORES[label]
            for prob, label in zip(prob_list, _CANDIDATE_LABELS, strict=True)
        )
        score = max(0.0, min(1.0, score))

        return ClassifierResult(
            success=True,
            score=round(score, 4),
            confidence=round(confidence, 4),
            label=top_label,
        )
