"""Tests for skyyrose.elite_studio.prompts (PromptLibrary SoT + hardening)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from skyyrose.elite_studio.prompts import (
    MissingVariableError,
    PromptLibrary,
)
from skyyrose.elite_studio.validation import IntegrityError

pytest.importorskip("yaml")


# ─── Fixture helpers ────────────────────────────────────────────────────


def _write_registry(tmp_path: Path, yaml_text: str) -> Path:
    p = tmp_path / "registry.yaml"
    p.write_text(textwrap.dedent(yaml_text).lstrip("\n"))
    return p


BASE_REGISTRY = """
version: 1
generated_at: "2026-04-17T00:00:00Z"
components:
  compositor:
    file_path: skyyrose/elite_studio/agents/compositor_agent.py
    description: "6-stage scene compositor"
  gemini_qa:
    file_path: skyyrose/elite_studio/agents/compositor_agent.py
    description: "Stage 6 visual QA"
prompts:
  - id: compositor.scene_prompt_builder.v3
    component: compositor
    file_path: skyyrose/elite_studio/agents/compositor_agent.py
    model: claude-opus-4-6
    purpose: "Turn scene+subject into FLUX prompt"
    status: production
    production_since: "2026-03-08"
    production_until: null
    stage: 2
    variables: [subject_description, scene_description, branding_summary]
    uses_catalog_fields: [branding_summary]
    prompt: |
      Subject: {subject_description}
      Scene: {scene_description}
      Required branding: {branding_summary}
    tags: [compositor, scene, production]
    notes: "v2 hallucinated logo placement; v3 enforces literal injection."
    impact:
      drops: ["Black Rose Preview"]
      renders: 234
      cost_usd_total: 47.12
  - id: gemini_qa.verdict.v1
    component: gemini_qa
    file_path: skyyrose/elite_studio/agents/compositor_agent.py
    model: gemini-3-pro-image-preview
    purpose: "Pass/fail visual QA verdict"
    status: retired
    production_since: "2026-02-15"
    production_until: "2026-03-08"
    variables: [render_url]
    uses_catalog_fields: []
    prompt: |
      Evaluate this render at {render_url}.
      Return JSON: {{"verdict": "pass"|"fail", "reason": "..."}}
    tags: [qa, retired]
"""


@pytest.fixture
def lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PromptLibrary:
    p = _write_registry(tmp_path, BASE_REGISTRY)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    return PromptLibrary.load()


# ─── Loading ────────────────────────────────────────────────────────────


def test_load_parses_components_and_prompts(lib: PromptLibrary) -> None:
    assert lib.version == 1
    assert set(lib.components_by_name.keys()) == {"compositor", "gemini_qa"}
    assert len(lib.prompts_by_id) == 2


def test_load_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(tmp_path / "nope.yaml"))
    with pytest.raises(FileNotFoundError):
        PromptLibrary.load()


# ─── Structural validation (__post_init__) ──────────────────────────────


def test_prompt_id_must_match_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = BASE_REGISTRY.replace(
        "id: compositor.scene_prompt_builder.v3",
        "id: BadID",
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(ValueError, match="invalid format"):
        PromptLibrary.load()


def test_undeclared_template_variable_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = BASE_REGISTRY.replace(
        "variables: [subject_description, scene_description, branding_summary]",
        "variables: [subject_description, scene_description]",
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(ValueError, match="undeclared placeholders"):
        PromptLibrary.load()


def test_unused_declared_variable_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = BASE_REGISTRY.replace(
        "variables: [subject_description, scene_description, branding_summary]",
        "variables: [subject_description, scene_description, branding_summary, unused_var]",
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(ValueError, match="not referenced"):
        PromptLibrary.load()


def test_production_status_requires_production_since(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = BASE_REGISTRY.replace(
        'production_since: "2026-03-08"',
        "production_since: null",
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(ValueError, match="production_since is required"):
        PromptLibrary.load()


def test_invalid_status_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = BASE_REGISTRY.replace("status: production", "status: zombie")
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(ValueError, match="not in allowed values"):
        PromptLibrary.load()


# ─── Referential validation ─────────────────────────────────────────────


def test_prompt_referencing_unknown_component_is_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = BASE_REGISTRY.replace(
        "component: compositor\n    file_path: skyyrose/elite_studio/agents/compositor_agent.py\n    model: claude-opus-4-6",
        "component: ghost_component\n    file_path: skyyrose/elite_studio/agents/compositor_agent.py\n    model: claude-opus-4-6",
        1,
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    loaded = PromptLibrary.load()
    assert len(loaded.violations) == 1
    assert loaded.violations[0].code == "prompt_component_missing"


def test_strict_mode_raises_on_referential_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = BASE_REGISTRY.replace(
        "component: compositor\n    file_path: skyyrose/elite_studio/agents/compositor_agent.py\n    model: claude-opus-4-6",
        "component: ghost_component\n    file_path: skyyrose/elite_studio/agents/compositor_agent.py\n    model: claude-opus-4-6",
        1,
    )
    p = _write_registry(tmp_path, bad)
    monkeypatch.setenv("SKYYROSE_PROMPTS_PATH", str(p))
    with pytest.raises(IntegrityError, match="prompt_component_missing"):
        PromptLibrary.load(strict=True)


# ─── Rendering ──────────────────────────────────────────────────────────


def test_render_succeeds_with_all_variables(lib: PromptLibrary) -> None:
    p = lib.require("compositor.scene_prompt_builder.v3")
    rendered = p.render(
        subject_description="black crewneck",
        scene_description="Oakland courtyard dusk",
        branding_summary="Embossed rose on front chest.",
    )
    assert "black crewneck" in rendered
    assert "Oakland courtyard dusk" in rendered
    assert "Embossed rose on front chest." in rendered


def test_render_raises_on_missing_variable(lib: PromptLibrary) -> None:
    p = lib.require("compositor.scene_prompt_builder.v3")
    with pytest.raises(MissingVariableError, match="requires"):
        p.render(subject_description="x", scene_description="y")


def test_render_raises_on_extra_variable(lib: PromptLibrary) -> None:
    p = lib.require("compositor.scene_prompt_builder.v3")
    with pytest.raises(MissingVariableError, match="undeclared variables"):
        p.render(
            subject_description="x",
            scene_description="y",
            branding_summary="z",
            bogus_field="zzz",
        )


# ─── Queries ────────────────────────────────────────────────────────────


def test_by_component_filters_correctly(lib: PromptLibrary) -> None:
    compositor_prompts = lib.by_component("compositor")
    assert len(compositor_prompts) == 1
    assert compositor_prompts[0].id == "compositor.scene_prompt_builder.v3"


def test_live_prompts_excludes_retired(lib: PromptLibrary) -> None:
    live = lib.live_prompts()
    assert len(live) == 1
    assert live[0].id == "compositor.scene_prompt_builder.v3"


def test_retired_prompts_returns_only_retired(lib: PromptLibrary) -> None:
    retired = lib.retired_prompts()
    assert len(retired) == 1
    assert retired[0].id == "gemini_qa.verdict.v1"


def test_is_live_property(lib: PromptLibrary) -> None:
    assert lib.require("compositor.scene_prompt_builder.v3").is_live is True
    assert lib.require("gemini_qa.verdict.v1").is_live is False


def test_require_raises_on_unknown(lib: PromptLibrary) -> None:
    with pytest.raises(KeyError, match="not found"):
        lib.require("compositor.nonexistent.v1")
