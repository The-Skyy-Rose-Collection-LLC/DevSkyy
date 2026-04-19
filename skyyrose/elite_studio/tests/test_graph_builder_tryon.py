"""Tests for GraphConfig and build_graph() with enable_tryon=True.

Verifies:
- GraphConfig defaults have enable_tryon=False
- GraphConfig is frozen (immutable)
- build_graph(enable_tryon=True) includes the tryon node
- build_graph(enable_tryon=False) does not include the tryon node
- GraphConfig tryon_category is passed through
"""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.graph.builder import _TRYON, GraphConfig, build_graph

# ---------------------------------------------------------------------------
# GraphConfig
# ---------------------------------------------------------------------------


class TestGraphConfig:
    def test_defaults_tryon_disabled(self) -> None:
        config = GraphConfig()
        assert config.enable_tryon is False

    def test_default_tryon_category(self) -> None:
        config = GraphConfig()
        assert config.tryon_category == "upper_body"

    def test_enable_tryon_true(self) -> None:
        config = GraphConfig(enable_tryon=True)
        assert config.enable_tryon is True

    def test_custom_tryon_category(self) -> None:
        config = GraphConfig(enable_tryon=True, tryon_category="bottoms")
        assert config.tryon_category == "bottoms"

    def test_frozen_dataclass(self) -> None:
        config = GraphConfig()
        with pytest.raises((AttributeError, TypeError)):
            config.enable_tryon = True  # type: ignore[misc]

    def test_tryon_constant_value(self) -> None:
        assert _TRYON == "tryon"


# ---------------------------------------------------------------------------
# build_graph topology
# ---------------------------------------------------------------------------


class TestBuildGraphTryon:
    def _get_node_names(self, graph) -> set[str]:
        """Extract node names from compiled LangGraph graph."""
        # LangGraph compiled graphs expose nodes via .nodes or .__dict__
        if hasattr(graph, "nodes"):
            return set(graph.nodes.keys())
        # Fallback: inspect the underlying graph structure
        if hasattr(graph, "_graph") and hasattr(graph._graph, "nodes"):
            return set(graph._graph.nodes.keys())
        return set()

    def test_tryon_node_included_when_enabled(self) -> None:
        config = GraphConfig(enable_tryon=True)
        graph = build_graph(config)
        node_names = self._get_node_names(graph)
        assert "tryon" in node_names

    def test_tryon_node_excluded_when_disabled(self) -> None:
        config = GraphConfig(enable_tryon=False)
        graph = build_graph(config)
        node_names = self._get_node_names(graph)
        assert "tryon" not in node_names

    def test_default_config_excludes_tryon(self) -> None:
        graph = build_graph()
        node_names = self._get_node_names(graph)
        assert "tryon" not in node_names

    def test_core_nodes_always_present(self) -> None:
        """Core pipeline nodes are present regardless of tryon flag."""
        for enable in (True, False):
            config = GraphConfig(enable_tryon=enable)
            graph = build_graph(config)
            node_names = self._get_node_names(graph)
            for core_node in ("vision", "generator", "quality", "compositor", "finalize"):
                assert (
                    core_node in node_names
                ), f"Core node '{core_node}' missing when enable_tryon={enable}"

    def test_graph_is_compiled_and_invocable(self) -> None:
        """build_graph returns a compiled object with an invoke method."""
        config = GraphConfig(enable_tryon=True)
        graph = build_graph(config)
        assert callable(getattr(graph, "invoke", None))
