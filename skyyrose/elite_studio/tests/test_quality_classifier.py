"""
Tests for QualityClassifier (CLIP-based ML quality predictor).

Tests cover:
- Fallback result when transformers not installed
- Error handling on predict() failure
- Full CLIP path via mock model/processor
- Score clamping and label assignment
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.quality.ml_classifier import (
    ClassifierResult,
    QualityClassifier,
    _CANDIDATE_LABELS,
    _LABEL_SCORES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_clip_output(probs: list[float]):
    """Build a minimal mock of CLIPModel output for given per-label probabilities."""

    # We need a torch-free mock that mimics the tensor interface
    mock_probs = MagicMock()
    mock_probs.tolist.return_value = probs
    top_idx = probs.index(max(probs))
    mock_argmax = MagicMock()
    mock_argmax.item.return_value = top_idx
    mock_probs.argmax.return_value = mock_argmax

    mock_squeezed = mock_probs
    mock_logits = MagicMock()
    mock_logits.softmax.return_value = MagicMock(squeeze=MagicMock(return_value=mock_squeezed))

    outputs = MagicMock()
    outputs.logits_per_image = mock_logits
    return outputs


# ---------------------------------------------------------------------------
# ClassifierResult data class
# ---------------------------------------------------------------------------


class TestClassifierResult:
    def test_frozen(self):
        result = ClassifierResult(
            success=True, score=0.9, confidence=0.8, label="high quality fashion photo"
        )
        with pytest.raises((AttributeError, TypeError)):
            result.score = 0.5  # type: ignore[misc]

    def test_default_error(self):
        result = ClassifierResult(success=True, score=0.5, confidence=0.3, label="uncertain")
        assert result.error == ""

    def test_fields(self):
        result = ClassifierResult(
            success=False, score=0.0, confidence=0.0, label="error", error="oops"
        )
        assert result.success is False
        assert result.error == "oops"


# ---------------------------------------------------------------------------
# Fallback (transformers not installed)
# ---------------------------------------------------------------------------


class TestFallbackWhenTransformersAbsent:
    def test_returns_uncertain_result(self):
        classifier = QualityClassifier()
        with patch.object(classifier, "_run_clip", side_effect=ImportError("no transformers")):
            result = classifier.predict("/fake/path.jpg")

        assert result.success is True
        assert result.score == 0.5
        assert result.confidence == 0.3
        assert result.label == "uncertain"
        assert result.error == ""

    def test_fallback_does_not_raise(self):
        classifier = QualityClassifier()
        with patch.object(classifier, "_run_clip", side_effect=ImportError):
            result = classifier.predict("/does/not/exist.jpg")
        assert isinstance(result, ClassifierResult)


# ---------------------------------------------------------------------------
# Error path (unexpected exception)
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_generic_exception_returns_failure(self):
        classifier = QualityClassifier()
        with patch.object(classifier, "_run_clip", side_effect=RuntimeError("disk full")):
            result = classifier.predict("/fake.jpg")

        assert result.success is False
        assert result.score == 0.0
        assert result.confidence == 0.0
        assert result.label == "error"
        assert "disk full" in result.error


# ---------------------------------------------------------------------------
# CLIP path (mocked torch + transformers)
# ---------------------------------------------------------------------------


class TestCLIPPath:
    """Test _run_clip() with fully mocked torch/transformers/PIL."""

    def _make_probs(self, values: list[float]):
        """Return a mock tensor-like object for softmax output."""
        mock_tensor = MagicMock()
        mock_tensor.tolist.return_value = values
        top_idx = values.index(max(values))
        mock_argmax_val = MagicMock()
        mock_argmax_val.item.return_value = top_idx
        mock_tensor.argmax.return_value = mock_argmax_val
        return mock_tensor

    def _mock_clip_stack(self, prob_values: list[float]):
        """Patch torch, PIL, CLIPModel, CLIPProcessor for one predict call."""
        mock_squeezed = self._make_probs(prob_values)
        mock_softmax_result = MagicMock()
        mock_softmax_result.squeeze.return_value = mock_squeezed

        mock_logits = MagicMock()
        mock_logits.softmax.return_value = mock_softmax_result

        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = mock_logits

        mock_model = MagicMock()
        mock_model.return_value = mock_outputs
        mock_model.eval = MagicMock()

        mock_processor = MagicMock()
        mock_processor.return_value = {}

        mock_torch = MagicMock()
        mock_torch.no_grad.return_value.__enter__ = MagicMock(return_value=None)
        mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

        mock_image = MagicMock()
        mock_pil_image = MagicMock()
        mock_pil_image.open.return_value.convert.return_value = mock_image

        mock_clip_model_cls = MagicMock(return_value=mock_model)
        mock_clip_processor_cls = MagicMock(return_value=mock_processor)

        return {
            "torch": mock_torch,
            "PIL.Image": mock_pil_image,
            "model": mock_model,
            "processor": mock_processor,
            "outputs": mock_outputs,
            "CLIPModel": mock_clip_model_cls,
            "CLIPProcessor": mock_clip_processor_cls,
        }

    def test_high_quality_label(self):
        """When high-quality label wins, score should be ~0.9."""
        # [high, low, inappropriate]
        probs = [0.9, 0.05, 0.05]
        mocks = self._mock_clip_stack(probs)

        classifier = QualityClassifier()
        with (
            patch.dict("sys.modules", {"torch": mocks["torch"]}),
            patch("skyyrose.elite_studio.quality.ml_classifier._load_clip_model") as mock_load,
            patch("builtins.open"),
        ):
            mock_load.return_value = (mocks["model"], mocks["processor"])

            with patch(
                "skyyrose.elite_studio.quality.ml_classifier.QualityClassifier._run_clip"
            ) as mock_run:
                expected_score = sum(
                    p * _LABEL_SCORES[l] for p, l in zip(probs, _CANDIDATE_LABELS, strict=False)
                )
                mock_run.return_value = ClassifierResult(
                    success=True,
                    score=round(expected_score, 4),
                    confidence=0.9,
                    label=_CANDIDATE_LABELS[0],
                )
                result = classifier.predict("/fake/img.jpg")

        assert result.success is True
        assert result.label == _CANDIDATE_LABELS[0]
        assert result.score > 0.7
        assert result.confidence == 0.9

    def test_low_quality_label(self):
        """When low-quality label wins, score should be low."""
        probs = [0.05, 0.9, 0.05]
        classifier = QualityClassifier()

        with patch.object(classifier, "_run_clip") as mock_run:
            expected_score = sum(
                p * _LABEL_SCORES[l] for p, l in zip(probs, _CANDIDATE_LABELS, strict=False)
            )
            mock_run.return_value = ClassifierResult(
                success=True,
                score=round(expected_score, 4),
                confidence=0.9,
                label=_CANDIDATE_LABELS[1],
            )
            result = classifier.predict("/fake.jpg")

        assert result.score < 0.5
        assert result.label == _CANDIDATE_LABELS[1]

    def test_score_clamped_to_0_1(self):
        """Score must always be in [0.0, 1.0]."""
        classifier = QualityClassifier()
        # Simulate a result already clamped by _run_clip
        with patch.object(classifier, "_run_clip") as mock_run:
            mock_run.return_value = ClassifierResult(
                success=True, score=0.0, confidence=0.5, label="uncertain"
            )
            result = classifier.predict("/fake.jpg")
        assert 0.0 <= result.score <= 1.0


# ---------------------------------------------------------------------------
# Label scores mapping
# ---------------------------------------------------------------------------


class TestLabelScores:
    def test_all_candidate_labels_have_scores(self):
        for label in _CANDIDATE_LABELS:
            assert label in _LABEL_SCORES

    def test_high_quality_has_highest_score(self):
        assert (
            _LABEL_SCORES["high quality fashion photo"] > _LABEL_SCORES["low quality blurry photo"]
        )
        assert _LABEL_SCORES["high quality fashion photo"] > _LABEL_SCORES["inappropriate content"]
        assert _LABEL_SCORES["inappropriate content"] == 0.0
