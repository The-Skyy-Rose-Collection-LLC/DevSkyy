"""Tests for the orchestration protocol layer (P1 #5).

Locks in the layer rule (orchestration L3 → agents L4 must be one-way) and
verifies that the four concrete agents continue to satisfy the structural
contracts that `asset_pipeline.py` depends on.

If a future change reintroduces a top-level `from agents.X import YAgent`
in `asset_pipeline.py`, the layer-rule guard will fail.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

# ---------------------------------------------------------------------------
# Layer rule guard
# ---------------------------------------------------------------------------


def test_asset_pipeline_does_not_leak_agent_classes_at_module_level() -> None:
    """`orchestration.asset_pipeline` must not expose concrete agent classes.

    The four concrete agents are imported lazily inside `@property` bodies.
    They must never be attribute-accessible on the module itself.
    """
    import orchestration.asset_pipeline as ap

    forbidden = {
        "TripoAssetAgent",
        "FashnTryOnAgent",
        "MeshyAgent",
        "WordPressAssetAgent",
    }
    leaked = forbidden & set(dir(ap))
    assert not leaked, (
        f"Layer rule violation — concrete agent classes leaked into orchestration: "
        f"{sorted(leaked)}. They must be imported lazily inside @property methods."
    )


# ---------------------------------------------------------------------------
# Protocol conformance — each concrete agent satisfies its protocol
# ---------------------------------------------------------------------------


def test_tripo_agent_satisfies_asset_workflow_agent_protocol() -> None:
    from agents.tripo_agent import TripoAssetAgent, TripoConfig
    from orchestration.protocols import AssetWorkflowAgent

    agent = TripoAssetAgent(config=TripoConfig.from_env())
    assert isinstance(agent, AssetWorkflowAgent)


def test_fashn_agent_satisfies_asset_workflow_agent_protocol() -> None:
    from agents.fashn_agent import FashnConfig, FashnTryOnAgent
    from orchestration.protocols import AssetWorkflowAgent

    agent = FashnTryOnAgent(config=FashnConfig.from_env())
    assert isinstance(agent, AssetWorkflowAgent)


def test_wordpress_agent_satisfies_wordpress_upload_agent_protocol() -> None:
    from agents.wordpress_asset_agent import WordPressAssetAgent, WordPressAssetConfig
    from orchestration.protocols import WordPressUploadAgent

    agent = WordPressAssetAgent(config=WordPressAssetConfig.from_env())
    assert isinstance(agent, WordPressUploadAgent)


def test_meshy_agent_satisfies_preview_gate_agent_protocol() -> None:
    from agents.meshy_agent import MeshyAgent, MeshyConfig
    from orchestration.protocols import PreviewGateAgent

    agent = MeshyAgent(config=MeshyConfig.from_env())
    assert isinstance(agent, PreviewGateAgent)


# ---------------------------------------------------------------------------
# Dependency injection — injected agents are used; otherwise lazy default
# ---------------------------------------------------------------------------


def test_pipeline_uses_injected_tripo_agent() -> None:
    from orchestration.asset_pipeline import ProductAssetPipeline

    mock_agent = AsyncMock()
    pipeline = ProductAssetPipeline(tripo_agent=mock_agent)
    assert pipeline.tripo_agent is mock_agent


def test_pipeline_uses_injected_fashn_agent() -> None:
    from orchestration.asset_pipeline import ProductAssetPipeline

    mock_agent = AsyncMock()
    pipeline = ProductAssetPipeline(fashn_agent=mock_agent)
    assert pipeline.fashn_agent is mock_agent


def test_pipeline_uses_injected_wordpress_agent() -> None:
    from orchestration.asset_pipeline import ProductAssetPipeline

    mock_agent = AsyncMock()
    pipeline = ProductAssetPipeline(wordpress_agent=mock_agent)
    assert pipeline.wordpress_agent is mock_agent


def test_pipeline_uses_injected_meshy_agent() -> None:
    from orchestration.asset_pipeline import ProductAssetPipeline

    mock_agent = AsyncMock()
    pipeline = ProductAssetPipeline(meshy_agent=mock_agent)
    assert pipeline.meshy_agent is mock_agent


def test_pipeline_lazy_constructs_default_tripo_agent_when_not_injected() -> None:
    """Backward compat: existing callers that pass no agents still work."""
    from agents.tripo_agent import TripoAssetAgent
    from orchestration.asset_pipeline import ProductAssetPipeline

    pipeline = ProductAssetPipeline()
    # Force lazy construction
    assert isinstance(pipeline.tripo_agent, TripoAssetAgent)


def test_pipeline_constructor_accepts_no_agents_for_backward_compat() -> None:
    """All four agent kwargs are optional — original `ProductAssetPipeline()` still works."""
    from orchestration.asset_pipeline import ProductAssetPipeline

    pipeline = ProductAssetPipeline()
    assert pipeline._tripo_agent is None
    assert pipeline._fashn_agent is None
    assert pipeline._wordpress_agent is None
    assert pipeline._meshy_agent is None


def test_pipeline_constructor_accepts_config_only_for_backward_compat() -> None:
    """`ProductAssetPipeline(config=...)` still works — same shape as before."""
    from orchestration.asset_pipeline import PipelineConfig, ProductAssetPipeline

    pipeline = ProductAssetPipeline(config=PipelineConfig.from_env())
    assert pipeline.config is not None
