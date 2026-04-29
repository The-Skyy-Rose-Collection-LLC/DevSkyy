"""Tests for VariantResult and VariantSpec models."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.models import VariantResult, VariantSpec


class TestVariantResultModel:
    def test_frozen(self):
        r = VariantResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = VariantResult(success=False)
        assert r.variant_name == ""
        assert r.output_path == ""
        assert r.error == ""


class TestVariantSpecModel:
    def test_frozen(self):
        s = VariantSpec(name="back_view", prompt_modifier="show back")
        with pytest.raises((AttributeError, TypeError)):
            s.name = "other"  # type: ignore[misc]

    def test_fields(self):
        s = VariantSpec(name="side_view", prompt_modifier="90 degree profile")
        assert s.name == "side_view"
        assert s.prompt_modifier == "90 degree profile"
