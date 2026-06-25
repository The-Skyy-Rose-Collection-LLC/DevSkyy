# Catalog & Dossier Steward — Design Spec

**Date:** 2026-05-29
**Status:** Approved (design, incl. §3/§8 confirmed 2026-05-29) — pending implementation plan
**Author:** DevSkyy engineering agent (brainstormed with Corey Foster)
**Supersedes concept of:** `dossier-author` + `catalog-QA` (merged into one steward)

---

## 1. Summary

A single **Catalog & Dossier Steward** that merges two responsibilities — catalog/dossier
**quality assurance** and dossier **authoring assistance** — into one SkyyRose-dedicated system.

It is built on a hard architectural principle (see §3): the value lives in an **AI-free
deterministic core**; AI is a pluggable enhancement behind a narrow port; every interface
(CLI, MCP, API, agent) is a thin shell. This makes the company resilient to AI-landscape
churn — a model/framework/interface pivot costs one small adapter rewrite, not a rebuild.

> **NOTE (confirmed by Corey 2026-05-29):** §3 (hexagonal AI-portability) and §8 (model-routing
> policy) originated as the engineering agent's design *proposals* derived from the goal "be in a
> better position for success" — they were not in the original request. Corey reviewed and
> **confirmed keeping both**. They also echo existing project rules (`rules/common/performance.md`
> model-selection; the anti-hallucination canon). All other sections follow directly from the
> confirmed decisions: scaffold+interrogate authoring, best-practice (deterministic) verification,
> Steward-first scope, and package layout B.

The "authoring" half is **canon-safe**: the steward never writes dossier prose. It generates
empty structured skeletons and interrogates the human author. Dossiers stay Corey-authored
(per `feedback_dossier_authoring`, enforced by `dossier_loader.py` hard-fail).

## 2. Goals / Non-Goals

### Goals
- One system that verifies catalog↔dossier data quality using **industry best-practice
  verification methodology** (6 data-quality dimensions, all deterministic).
- Reduce dossier-authoring friction via **scaffold + interrogate** (never generate prose).
- Be **AI-optional and vendor/framework/interface-independent** (`feedback_ai_portability_architecture`).
- Produce a **typed, structured report** with per-SKU render-readiness verdicts.
- Ship a deterministic engine reusable by CI and the Phase 2 capability-retrofit.

### Non-Goals (this slice)
- Extending other existing agents with tools/thinking/MCP — that is **Phase 2** (separate spec).
- Writing dossier descriptive content (forbidden by canon).
- Replacing the render pipeline's `DossierMissingError` hard-fail (steward *reports* gaps; the
  pipeline still enforces them).
- Full golden-reference CLIP/DINOv2 accuracy scoring is **flag-gated**, not on the critical path.

## 3. Architecture — Hexagonal (ports & adapters)

```
┌─ INTERFACES (thin shells, swappable) ────────────────────┐
│   CLI  ·  MCP tool  ·  FastAPI route  ·  ADK agent        │
│         all call ↓ the same service; none is "the" one    │
├─ PORTS (narrow interfaces) ──────────────────────────────┤
│   StewardService  ·  LLMReasoner (Protocol, 3 methods)    │
├─ ADAPTERS (thin, ~100 lines each) ───────────────────────┤
│   PydanticAIReasoner   ·   DeterministicReasoner (no LLM) │
├─ CORE  skyyrose/steward/ (core modules, AI-FREE) ─────────┤
│   engine.py · scaffold.py · models.py · config.py         │
│   imports only catalog_loader / dossier_loader /          │
│   dossier_schema / golden assets — NO llm, NO framework   │
└──────────────────────────────────────────────────────────┘
```

**Portability test (apply to every unit):** *does the value survive if the LLM is removed?*
The engine answers yes — it ships with a no-LLM `DeterministicReasoner` so the whole system
provably runs with zero AI. AI is enhancement, never dependency.

## 4. Core engine — `skyyrose/steward/engine.py` (deterministic)

Six DAMA-DMBOK data-quality dimensions, each a pure-code check over real data:

| Dimension | Concrete check | Source |
|-----------|---------------|--------|
| **Validity** | `DossierSchema.from_raw()` parses; `garment_type_lock` + negatives non-empty; hex format valid | `dossier_schema.py` |
| **Completeness** | `coverage_for()` color hex/pantone %; `scene_pose`/`scene_setting` present; ≥1 branding region; golden front/back coverage (33 front / 10 back as of 2026-05-29) | `coverage_for`, golden dir |
| **Integrity** (referential) | every CSV `dossier_slug` → file exists; every dossier `sku` → in CSV; `render_output_slug`/`render_source_override`/`render_back_source_override` → asset on disk; logo refs resolve | `catalog_loader` + filesystem |
| **Consistency** | `garment_type_lock` CSV↔dossier match; `collection`↔`name` align; CSV `branding_spec` not contradicting dossier branding | both sources |
| **Uniqueness** | no duplicate SKU; no duplicate `dossier_slug`; conflation guard (br-001 history) | CSV |
| **Accuracy** (golden-reference) | CLIP/DINOv2 vs golden refs — **flag-gated** (`--with-vision`, needs models); falls back to presence + dimension checks | fidelity gate |

- Public entrypoint: `verify_catalog(skus: list[str] | None = None) -> StewardReport`.
- Each check emits `Finding(dimension, sku, severity, message, evidence_path)`.
- No LLM touches a verdict — `Path.exists()` cannot hallucinate. Aligns with the
  anti-hallucination protocol.
- If `engine.py` exceeds ~800 lines, split into `dimensions/{validity,completeness,...}.py`.

## 5. Scaffold + interrogate — the "author" half (canon-safe)

- `scaffold.py::build_skeleton(sku) -> DossierSkeleton`: from `_template.md` + catalog-row
  facts (sku/name/collection/garment_type). Placeholders only — **zero prose**.
- `scaffold.py::write_draft(skeleton) -> Path`: writes to
  `wordpress-theme/skyyrose-flagship/data/dossiers/_drafts/{slug}.draft.md` — **never** the
  canonical `{slug}.md` path. Machine text never reaches a canonical dossier.
- Interrogate: engine computes gaps → `LLMReasoner.interrogate(skeleton, known)` orders them
  into targeted questions for Corey → Corey fills → re-verify. The steward never authors content.

## 6. The LLMReasoner port — the only AI surface

```python
class LLMReasoner(Protocol):
    def prioritize(self, findings: list[Finding]) -> list[Finding]: ...
    def interrogate(self, skeleton: DossierSkeleton, known: dict) -> list[str]: ...
    def narrate(self, report: StewardReport) -> str: ...
```

- `PydanticAIReasoner` — current adapter; model is **config-driven** (see §8), uses the latest
  Claude models. Built on the existing `PydanticAIAgent[T]` pattern in `sdk/python/adk/pydantic_adk.py`.
- `DeterministicReasoner` — no-LLM fallback: severity-sort for `prioritize`, templated question
  generation for `interrogate`, templated summary for `narrate`. Proves AI-optionality.
- Swapping LLM frameworks (or to none) = implement one ~100-line adapter behind this Protocol.

## 7. Error handling

- The engine **records, never crashes** on data problems: a missing dossier is a `Finding`
  (`severity=critical`), not an exception. (The render pipeline still hard-fails via
  `DossierMissingError`; the steward's job is to *report*, not enforce.)
- Only infrastructure errors (CSV unreadable, dossiers dir missing) raise.
- `PydanticAIReasoner` failure → auto-degrade to `DeterministicReasoner`. System keeps working
  with no model.

## 8. Model routing (config-driven, living policy)

Model choice is **never hardcoded** — it resolves through `skyyrose/steward/config.py`,
which reads the project-wide policy documented in `docs/model-routing.md`:

| Task class | Model | Rationale |
|-----------|-------|-----------|
| **Deep reasoning** — `prioritize`, `narrate`, interrogation strategy synthesis | `claude-opus-4-8` | maximum reasoning |
| **Quick actions** — single-gap question phrasing, classification, field-level summary | `claude-haiku-4-5` | ~3× cheaper, fast, ~90% capability |
| **Default / medium** (if needed) | `claude-sonnet-4-6` | best general/coding |

`docs/model-routing.md` is a living document — update it as models change; the config reads
the policy so code follows automatically. The stale strings in `pydantic_adk.py`
(`gpt-4o-mini`, `claude-sonnet-4-0`) are known debt to fix when that file is next touched.

## 9. Testing

- **Engine:** pure unit tests, good/bad catalog+dossier fixtures, one test module per dimension,
  85%+ coverage. Reuses `tests/test_dossier_schema.py` / `test_dossier_completeness.py` patterns.
- **LLM adapter:** Pydantic AI `TestModel` (deterministic, no API calls).
- **Deterministic adapter:** direct unit tests.
- **Snapshot:** asserts today's 33-SKU report shape (front=33, back=10) so future drift is caught.

## 10. Supersession of existing agents

`PRODUCT_ANALYST` + `QA_INSPECTOR` (`skyyrose/multi_agent/agents.py`) keep their entrypoints but
delegate catalog/QA to the Steward service — their currently-aspirational tools
(`get_product_catalog`, etc.) become real, backed by the engine. Full absorption is the **Phase 2**
retrofit milestone (separate spec), not this slice.

## 11. Proposed file layout

One dedicated package, `skyyrose/steward/`. Core (AI-free) modules and the AI adapters live in
the same package; the import rule (not the directory) keeps them separate — `engine.py`,
`scaffold.py`, `models.py`, `config.py` must NOT import any LLM/framework module.

```
skyyrose/steward/
  __init__.py
  models.py          # StewardReport, Finding, DimensionScore, RenderReadiness, DossierSkeleton
  engine.py          # verify_catalog(); six dimension checks   [AI-FREE]
  scaffold.py        # build_skeleton(), write_draft()          [AI-FREE]
  config.py          # model-routing config (task-class → model) [AI-FREE]
  service.py         # StewardService — use-case API
  ports.py           # LLMReasoner Protocol, errors
  dimensions/        # only if engine.py > 800 lines            [AI-FREE]
  adapters/
    __init__.py
    pydantic_ai_reasoner.py
    deterministic_reasoner.py
  interfaces/
    __init__.py
    cli.py           # python -m skyyrose.steward
    mcp.py           # MCP tool exposure
  agent.py           # optional ADK PydanticAIAgent[StewardReport] wrapper
docs/model-routing.md
tests/steward/
  test_engine_validity.py … (one per dimension)
  test_scaffold.py
  test_deterministic_reasoner.py
  test_pydantic_ai_reasoner.py
  test_snapshot.py
```

`__init__.py` required in every new package dir (project rule — no implicit namespace packages).
The AI-free guarantee is enforced by import discipline (a unit test asserts `engine.py`,
`scaffold.py`, `models.py`, `config.py` import no `pydantic_ai` / framework modules), not by
directory placement.

## 12. Phasing (within this slice)

1. Core models + engine (deterministic, all 6 dimensions except flag-gated Accuracy) + tests.
2. Scaffold + draft writer + tests.
3. Ports + `DeterministicReasoner` + `StewardService` + tests (system runs with zero AI here).
4. `PydanticAIReasoner` (config-driven model) + TestModel tests.
5. Interfaces: CLI first, then MCP. API + ADK agent optional.
6. Snapshot test + docs (`model-routing.md` already exists; add steward usage doc).

Phase 2 (separate spec): retrofit `PRODUCT_ANALYST` / `QA_INSPECTOR` / SuperAgents onto the
shared engine; broaden capabilities (tools/thinking/MCP) across the agent fleet.
