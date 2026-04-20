"""Phase 3 tests for triggers.py dispatch routing.

Verifies:
- _AGENT_FOR_KIND routes the three new kinds to the correct agent
- trigger_pipeline returns PipelineReport with the right agent for each new kind
- _dispatch_theme(platform='shopify') raises NotImplementedError with a clear
  message pointing at the deferred scaffold
- _dispatch_theme(platform='wp') still routes to the WordPress path (default)
- Unknown kinds raise ValueError

Uses real functions; no LLM / subprocess / network. The theme_deploy and
imagery paths are NOT exercised end-to-end here (those would invoke
scripts/deploy-theme.sh or the imagery pipeline).
"""

from __future__ import annotations

import pytest
from triggers import (
    _AGENT_FOR_KIND,
    PipelineEvent,
    _dispatch_theme,
    trigger_pipeline,
)


class TestAgentForKindMap:
    """The routing dict must include all new kinds and still preserve legacy ones."""

    def test_new_photography_kinds(self) -> None:
        for kind in ("photography", "product_shoot", "lookbook"):
            assert (
                _AGENT_FOR_KIND[kind] == "ecommerce_photography"
            ), f"{kind!r} should route to ecommerce_photography"

    def test_new_garment_3d_kinds(self) -> None:
        for kind in ("garment_3d", "meshy_generate"):
            assert _AGENT_FOR_KIND[kind] == "garment_3d"

    def test_new_competitor_scout_kinds(self) -> None:
        for kind in ("competitor_scout", "ad_teardown", "ad_blueprint"):
            assert _AGENT_FOR_KIND[kind] == "competitor_scout"

    def test_legacy_routing_preserved(self) -> None:
        """Phase 3 must not break any legacy route."""
        assert _AGENT_FOR_KIND["imagery"] == "imagery"
        assert _AGENT_FOR_KIND["social_media"] == "social_media"
        assert _AGENT_FOR_KIND["theme_deploy"] == "theme_builder"


class TestNewDispatchers:
    """Each new kind must reach its dispatcher and return a PipelineReport."""

    def test_photography_dispatch(self) -> None:
        report = trigger_pipeline(
            kind="photography",
            task={"sku": "br-001", "style": "flat-lay"},
        )
        assert report is not None
        assert report.agent == "ecommerce_photography"
        assert report.success is True
        assert any(
            "photography" in note.lower() or "brief" in note.lower() for note in report.notes
        )

    def test_garment_3d_dispatch(self) -> None:
        report = trigger_pipeline(
            kind="garment_3d",
            task={"sku": "sg-005", "lod": "hero"},
        )
        assert report is not None
        assert report.agent == "garment_3d"
        assert report.success is True
        assert any("meshy" in note.lower() or "3d" in note.lower() for note in report.notes)

    def test_competitor_scout_dispatch(self) -> None:
        report = trigger_pipeline(
            kind="competitor_scout",
            task={"brand": "fear_of_god"},
        )
        assert report is not None
        assert report.agent == "competitor_scout"
        assert report.success is True
        assert any(
            "fixture" in note.lower() or "blueprint" in note.lower() for note in report.notes
        )


class TestThemeDualPlatform:
    """theme_builder must keep WP as default and defer Shopify cleanly."""

    def test_shopify_platform_raises_not_implemented(self) -> None:
        event = PipelineEvent(
            kind="theme_build",
            task={"platform": "shopify"},
        )
        with pytest.raises(NotImplementedError) as exc_info:
            _dispatch_theme(event)
        msg = str(exc_info.value)
        assert "Shopify" in msg
        assert "scaffold" in msg.lower() or "deferred" in msg.lower()

    def test_unknown_platform_raises_value_error(self) -> None:
        event = PipelineEvent(
            kind="theme_build",
            task={"platform": "magento"},
        )
        with pytest.raises(ValueError, match="Unknown theme platform"):
            _dispatch_theme(event)

    def test_wp_platform_default_used_when_omitted(self) -> None:
        """Omitting platform == 'wp' path. Non-deploy kinds return stub reports."""
        report = trigger_pipeline(
            kind="theme_build",
            task={},  # no platform key → defaults to wp
        )
        assert report is not None
        assert report.agent == "theme_builder"
        assert report.success is True


class TestInvalidKind:
    def test_unknown_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown pipeline kind"):
            trigger_pipeline(kind="made_up_kind_xyz", task={})
