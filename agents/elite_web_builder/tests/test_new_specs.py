"""Structural tests for the three new Elite Team specialists.

Covers ECOMMERCE_PHOTOGRAPHY_SPEC, GARMENT_3D_SPEC, COMPETITOR_SCOUT_SPEC
added alongside the existing 10 specs. Uses the standard elite_web_builder
import pattern (conftest.py shims `agents` to the local package).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from agents.base import AgentCapability, AgentRole, AgentSpec
from agents.competitor_scout import COMPETITOR_SCOUT_SPEC
from agents.ecommerce_photography import ECOMMERCE_PHOTOGRAPHY_SPEC
from agents.garment_3d import GARMENT_3D_SPEC


def _load_package_all_specs() -> tuple[AgentSpec, ...]:
    """Return the real ALL_SPECS tuple from agents/__init__.py.

    The conftest.py shim registers `agents` as a bare module so submodule
    imports resolve, but that path never runs __init__.py. Loading the file
    manually here tests the exact tuple downstream callers see via
    `from agents import ALL_SPECS`. Runs once per session (module-level).
    """
    init_path = Path(__file__).resolve().parents[1] / "agents" / "__init__.py"
    spec = importlib.util.spec_from_file_location("_ewb_init", init_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ALL_SPECS


# Locally aliased ALL_SPECS_PACKAGE (not ALL_SPECS — that name collides
# with the top-level DevSkyy agents package when pytest imports from repo root).
ALL_SPECS_PACKAGE: tuple[AgentSpec, ...] = _load_package_all_specs()

NEW_SPECS: tuple[tuple[str, AgentSpec], ...] = (
    ("ecommerce_photography", ECOMMERCE_PHOTOGRAPHY_SPEC),
    ("garment_3d", GARMENT_3D_SPEC),
    ("competitor_scout", COMPETITOR_SCOUT_SPEC),
)

NEW_ROLE_VALUES: tuple[str, ...] = tuple(name for name, _ in NEW_SPECS)


# Knowledge files live relative to the elite_web_builder directory root.
_EWB_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# AgentRole enum
# ---------------------------------------------------------------------------


class TestNewAgentRoles:
    def test_new_role_values_exist(self) -> None:
        role_values = {r.value for r in AgentRole}
        for value in NEW_ROLE_VALUES:
            assert value in role_values, f"AgentRole.{value.upper()} missing"

    def test_all_role_values_unique(self) -> None:
        values = [r.value for r in AgentRole]
        assert len(values) == len(set(values)), f"Duplicate AgentRole values: {values}"

    def test_new_role_values_snake_case(self) -> None:
        for value in NEW_ROLE_VALUES:
            assert value == value.lower(), f"{value} must be lowercase"
            assert " " not in value
            assert "-" not in value


# ---------------------------------------------------------------------------
# Per-spec structure (mirrors tests/test_sub_agents.py:68-73 contract)
# ---------------------------------------------------------------------------


class TestNewSpecsStructure:
    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_mentions_skyyrose(self, name: str, spec: AgentSpec) -> None:
        """Brand anchor — every SkyyRose agent names the brand in its prompt."""
        prompt = spec.system_prompt.lower()
        assert (
            "skyyrose" in prompt or "skyy" in prompt
        ), f"{name}.system_prompt must mention SkyyRose brand"

    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_has_minimum_capabilities(self, name: str, spec: AgentSpec) -> None:
        """Production-lead scope: ≥5 capabilities per spec."""
        assert (
            len(spec.capabilities) >= 5
        ), f"{name} has {len(spec.capabilities)} capabilities; expected ≥ 5"

    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_capability_names_unique(self, name: str, spec: AgentSpec) -> None:
        cap_names = [c.name for c in spec.capabilities]
        assert len(cap_names) == len(
            set(cap_names)
        ), f"{name} has duplicate capability names: {cap_names}"

    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_capabilities_are_immutable(self, name: str, spec: AgentSpec) -> None:
        """AgentCapability is a frozen dataclass — catches accidental mutations."""
        for cap in spec.capabilities:
            assert isinstance(cap, AgentCapability)

    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_knowledge_files_exist_on_disk(self, name: str, spec: AgentSpec) -> None:
        missing: list[str] = []
        for relpath in spec.knowledge_files:
            full = _EWB_ROOT / relpath
            if not full.exists():
                missing.append(str(full))
        assert not missing, f"{name} references missing knowledge files: {missing}"

    @pytest.mark.parametrize("name,spec", NEW_SPECS)
    def test_spec_role_matches_name(self, name: str, spec: AgentSpec) -> None:
        assert spec.role.value == spec.name == name, (
            f"Inconsistent role/name: role.value={spec.role.value}, "
            f"spec.name={spec.name}, expected={name}"
        )


# ---------------------------------------------------------------------------
# ALL_SPECS_PACKAGE tuple invariants
# ---------------------------------------------------------------------------


class TestAllSpecsTuple:
    def test_thirteen_specs_total(self) -> None:
        """10 legacy + 3 new = 13 specialists."""
        assert (
            len(ALL_SPECS_PACKAGE) == 13
        ), f"ALL_SPECS_PACKAGE has {len(ALL_SPECS_PACKAGE)} entries; expected 13"

    def test_legacy_specs_preserved_at_original_indices(self) -> None:
        """Indices 0-9 must hold the pre-existing specs so any downstream code
        that indexes ALL_SPECS_PACKAGE by position keeps working."""
        expected_legacy = (
            "theme_builder",
            "design_system",
            "frontend_dev",
            "backend_dev",
            "accessibility",
            "performance",
            "seo_content",
            "qa",
            "imagery",
            "social_media",
        )
        for i, expected_name in enumerate(expected_legacy):
            actual_name = ALL_SPECS_PACKAGE[i].name
            assert (
                actual_name == expected_name
            ), f"ALL_SPECS_PACKAGE[{i}] is '{actual_name}'; legacy order requires '{expected_name}'"

    def test_new_specs_appended_at_end(self) -> None:
        assert ALL_SPECS_PACKAGE[10].name == "ecommerce_photography"
        assert ALL_SPECS_PACKAGE[11].name == "garment_3d"
        assert ALL_SPECS_PACKAGE[12].name == "competitor_scout"

    def test_all_spec_names_unique(self) -> None:
        names = [s.name for s in ALL_SPECS_PACKAGE]
        assert len(names) == len(set(names)), f"Duplicate spec names: {names}"

    def test_all_roles_match_names(self) -> None:
        for spec in ALL_SPECS_PACKAGE:
            assert (
                spec.role.value == spec.name
            ), f"Mismatch: role.value='{spec.role.value}' vs name='{spec.name}'"
