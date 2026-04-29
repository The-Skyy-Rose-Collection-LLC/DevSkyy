"""Tests for TryOnResult model."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.models import TryOnResult


class TestTryOnResultModel:
    def test_frozen(self):
        r = TryOnResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = TryOnResult(success=False)
        assert r.output_path == ""
        assert r.garment_sku == ""
        assert r.provider == "fashn"
        assert r.latency_s == 0.0
        assert r.error == ""

    def test_fields_stored(self):
        r = TryOnResult(
            success=True,
            garment_sku="br-001",
            provider="fashn",
            latency_s=1.2,
        )
        assert r.garment_sku == "br-001"
        assert r.latency_s == 1.2
