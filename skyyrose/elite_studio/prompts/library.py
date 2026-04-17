"""Prompt Library — source of truth for prompts with production impact.

Reads `assets/prompts/registry.yaml`. Every prompt that has shipped (or been
formally considered for shipment) lives here with versioning, model, dates,
and quantified impact. Retired prompts stay visible for audit and regression.

    from skyyrose.elite_studio.prompts import PromptLibrary
    from skyyrose.elite_studio.catalog import Catalog

    lib = PromptLibrary.load()
    cat = Catalog.load()

    p = lib.require("compositor.scene_prompt_builder.v3")
    rendered = p.render(
        subject_description="black crewneck with embossed rose",
        scene_description="Oakland concrete courtyard, dusk",
        branding_summary=cat.require("br-001").branding_summary,
    )

Validation happens at load():
  - Structural (raises ValueError immediately): id format, required fields,
    production_since present when status=production, declared variables
    match template placeholders exactly.
  - Referential (violations list; raises IntegrityError if strict=True):
    component must exist in components block, prompt ids unique.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Formatter
from typing import Any

try:
    import yaml
except ImportError as _e:  # pragma: no cover
    raise ImportError(
        "PyYAML is required to load registry.yaml. Install with `pip install pyyaml`."
    ) from _e

from ..validation import (
    IntegrityError,
    Violation,
    collect_duplicates,
    validate_enum,
    validate_iso_date,
    validate_not_empty,
)

_ENV_PROMPTS_PATH = "SKYYROSE_PROMPTS_PATH"
PROMPT_STATUS = {"production", "retired", "candidate"}
_PROMPT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\.v\d+$")


class MissingVariableError(KeyError):
    """Raised when Prompt.render() is called without a declared variable, or with extras."""


def default_prompts_path() -> Path:
    override = os.getenv(_ENV_PROMPTS_PATH)
    if override:
        return Path(override)
    # library.py lives at skyyrose/elite_studio/prompts/library.py → parents[3] = repo root
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "assets" / "prompts" / "registry.yaml"


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Component:
    """A code location that uses prompts — e.g., the compositor agent."""

    name: str
    file_path: str
    description: str


@dataclass(frozen=True)
class Prompt:
    id: str  # e.g. 'compositor.scene_prompt_builder.v3'
    component: str  # key into components block
    file_path: str  # where this prompt is invoked (code location)
    model: str  # e.g. 'claude-opus-4-6', 'gemini-3-pro-image-preview'
    purpose: str  # one-line description
    status: str  # 'production' | 'retired' | 'candidate'
    prompt: str  # the template, with {variable} placeholders
    variables: tuple[str, ...]
    uses_catalog_fields: tuple[str, ...]  # e.g. ('branding_summary', 'color_spec')
    production_since: str | None
    production_until: str | None
    tags: tuple[str, ...]
    stage: int | None = None  # for pipeline prompts (e.g., compositor stage 2)
    impact: dict[str, Any] = field(default_factory=dict)  # {drops, renders, cost_usd_total}
    notes: str = ""

    def __post_init__(self) -> None:
        # Structural validation — fail loud, not silent
        validate_not_empty(self.id, f"prompts[{self.id!r}].id")
        if not _PROMPT_ID_RE.match(self.id):
            raise ValueError(
                f"prompts[{self.id!r}].id: invalid format "
                "(expected 'component.name.vN', lowercase snake_case)"
            )
        validate_not_empty(self.component, f"prompts[{self.id!r}].component")
        validate_not_empty(self.file_path, f"prompts[{self.id!r}].file_path")
        validate_not_empty(self.model, f"prompts[{self.id!r}].model")
        validate_not_empty(self.purpose, f"prompts[{self.id!r}].purpose")
        validate_enum(self.status, PROMPT_STATUS, f"prompts[{self.id!r}].status")
        validate_not_empty(self.prompt, f"prompts[{self.id!r}].prompt")
        if self.status == "production" and not self.production_since:
            raise ValueError(
                f"prompts[{self.id!r}]: production_since is required when status=production"
            )
        validate_iso_date(self.production_since, f"prompts[{self.id!r}].production_since")
        validate_iso_date(self.production_until, f"prompts[{self.id!r}].production_until")

        # Declared variables ↔ template placeholders must match exactly
        formatter = Formatter()
        template_placeholders: set[str] = set()
        try:
            for _literal, field_name, _format, _conv in formatter.parse(self.prompt):
                if field_name is not None and field_name != "":
                    # Strip dotted / indexed accessors — we only care about the base name
                    base = field_name.split(".")[0].split("[")[0]
                    template_placeholders.add(base)
        except Exception as e:
            raise ValueError(
                f"prompts[{self.id!r}].prompt: template has invalid format string: {e}"
            ) from e

        declared = set(self.variables)
        undeclared = template_placeholders - declared
        if undeclared:
            raise ValueError(
                f"prompts[{self.id!r}]: template uses undeclared placeholders "
                f"{sorted(undeclared)} (declare them in variables: [])"
            )
        unused = declared - template_placeholders
        if unused:
            raise ValueError(
                f"prompts[{self.id!r}]: declared variables {sorted(unused)} are not "
                f"referenced in the prompt template"
            )

        # Stage must be positive if set
        if self.stage is not None and (not isinstance(self.stage, int) or self.stage < 1):
            raise ValueError(
                f"prompts[{self.id!r}].stage: must be a positive integer or null, got {self.stage!r}"
            )

    # ─── Rendering ──────────────────────────────────────────────────────

    def render(self, **variables: Any) -> str:
        """Render the prompt template. Raises MissingVariableError on any mismatch."""
        declared = set(self.variables)
        given = set(variables.keys())
        missing = declared - given
        if missing:
            raise MissingVariableError(
                f"Prompt {self.id!r} requires {sorted(missing)} — not passed"
            )
        extra = given - declared
        if extra:
            raise MissingVariableError(
                f"Prompt {self.id!r} got undeclared variables: {sorted(extra)}"
            )
        return self.prompt.format(**variables)

    @property
    def is_live(self) -> bool:
        return self.status == "production" and self.production_until is None


@dataclass(frozen=True)
class PromptLibrary:
    version: int
    generated_at: str
    components_by_name: dict[str, Component]
    prompts_by_id: dict[str, Prompt]
    violations: tuple[Violation, ...] = ()

    @classmethod
    def load(cls, path: Path | str | None = None, *, strict: bool = False) -> PromptLibrary:
        p = Path(path) if path else default_prompts_path()
        if not p.is_file():
            raise FileNotFoundError(f"Prompt registry not found at {p}")
        data = yaml.safe_load(p.read_text()) or {}
        if not isinstance(data, dict):
            raise ValueError(f"registry.yaml must parse to a dict, got {type(data).__name__}")
        return cls._from_dict(data, strict=strict)

    @classmethod
    def _from_dict(cls, data: dict, *, strict: bool = False) -> PromptLibrary:
        components_by_name: dict[str, Component] = {}
        for name, meta in (data.get("components") or {}).items():
            meta = meta or {}
            components_by_name[name] = Component(
                name=name,
                file_path=str(meta.get("file_path") or meta.get("path") or ""),
                description=str(meta.get("description") or ""),
            )

        prompts_by_id: dict[str, Prompt] = {}
        raw_ids: list[str] = []
        for i, raw in enumerate(data.get("prompts") or []):
            if not isinstance(raw, dict):
                raise ValueError(f"prompts[{i}]: expected mapping, got {type(raw).__name__}")
            if "id" not in raw:
                raise ValueError(f"prompts[{i}]: missing required 'id' field")
            pid = raw["id"]
            raw_ids.append(pid)
            prompts_by_id[pid] = Prompt(
                id=raw["id"],
                component=str(raw.get("component") or ""),
                file_path=str(raw.get("file_path") or ""),
                model=str(raw.get("model") or ""),
                purpose=str(raw.get("purpose") or ""),
                status=str(raw.get("status") or "candidate"),
                prompt=str(raw.get("prompt") or ""),
                variables=tuple(raw.get("variables") or []),
                uses_catalog_fields=tuple(raw.get("uses_catalog_fields") or []),
                production_since=raw.get("production_since"),
                production_until=raw.get("production_until"),
                tags=tuple(raw.get("tags") or []),
                stage=raw.get("stage"),
                impact=dict(raw.get("impact") or {}),
                notes=str(raw.get("notes") or ""),
            )

        violations = cls._validate_integrity(components_by_name, prompts_by_id, raw_ids)
        if strict and violations:
            raise IntegrityError(list(violations))

        return cls(
            version=int(data.get("version") or 0),
            generated_at=str(data.get("generated_at") or ""),
            components_by_name=components_by_name,
            prompts_by_id=prompts_by_id,
            violations=tuple(violations),
        )

    @staticmethod
    def _validate_integrity(
        components: dict[str, Component],
        prompts: dict[str, Prompt],
        raw_ids: list[str],
    ) -> list[Violation]:
        viols: list[Violation] = []

        # Each prompt must reference a declared component
        for pid, p in prompts.items():
            if p.component not in components:
                viols.append(
                    Violation(
                        severity="referential",
                        code="prompt_component_missing",
                        path=f"prompts[{pid}].component",
                        message=(
                            f"component {p.component!r} is not declared "
                            "in the top-level components: block"
                        ),
                    )
                )

        # Duplicate prompt ids (dict would overwrite; catch the raw list)
        for dup in collect_duplicates(raw_ids):
            viols.append(
                Violation(
                    severity="referential",
                    code="duplicate_prompt_id",
                    path=f"prompts[{dup}]",
                    message="prompt id appears more than once in registry.yaml",
                )
            )

        return viols

    # ─── Queries ────────────────────────────────────────────────────────

    def get(self, prompt_id: str) -> Prompt | None:
        return self.prompts_by_id.get(prompt_id)

    def require(self, prompt_id: str) -> Prompt:
        p = self.prompts_by_id.get(prompt_id)
        if p is None:
            raise KeyError(f"Prompt {prompt_id!r} not found in registry")
        return p

    def by_component(self, component: str, *, status: str | None = None) -> list[Prompt]:
        out = [p for p in self.prompts_by_id.values() if p.component == component]
        if status:
            out = [p for p in out if p.status == status]
        return out

    def live_prompts(self) -> list[Prompt]:
        return [p for p in self.prompts_by_id.values() if p.is_live]

    def retired_prompts(self) -> list[Prompt]:
        return [p for p in self.prompts_by_id.values() if p.status == "retired"]
