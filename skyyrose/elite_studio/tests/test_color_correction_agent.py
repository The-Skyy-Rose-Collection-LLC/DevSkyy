"""Tests for ColorCorrectionResult model."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.models import ColorCorrectionResult


class TestColorCorrectionResultModel:
    def test_frozen(self):
        r = ColorCorrectionResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = ColorCorrectionResult(success=False)
        assert r.output_path == ""
        assert r.adjustments_applied == ()
        assert r.error == ""

    def test_stores_adjustments(self):
        r = ColorCorrectionResult(success=True, adjustments_applied=("contrast_boost:1.1",))
        assert "contrast_boost:1.1" in r.adjustments_applied
