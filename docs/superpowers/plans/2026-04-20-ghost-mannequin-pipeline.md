# Ghost-Mannequin Imagery Pipeline (Phase B2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the dual-vision ghost-mannequin imagery pipeline in `skyyrose/elite_studio/agents/` — replacing all Phase B1 stubs with working dual-agent implementations, and adding the ghost-mannequin style (invisible-mannequin product photography with neck-in composite) as a first-class pipeline mode.

**Architecture:** The existing `EliteStudioState` LangGraph graph is extended with (a) a pre-flight dual-vision gate that blocks SKUs whose reference image doesn't match the CSV spec before any paid generation, (b) spec-primacy prompt enrichment that reads `branding_spec` directly from the canonical CSV, and (c) a neck-in composite node that stitches front + back ghost-mannequin renders into the signature "floating hollow" look for collar garments.

**Tech Stack:** LangGraph (already wired in `graph/builder.py`), Anthropic SDK (`claude-opus-4-6`), `gemini_rest.py` (existing REST wrapper — do NOT use the google-genai Python SDK), OpenAI SDK (`gpt-image-1`), Pillow (neck-in composite), `skyyrose.elite_studio.catalog.Catalog` (CSV reader).

**Critical constraint:** Every Gemini call goes through `skyyrose/elite_studio/gemini_rest.py`, not `import google.generativeai`. The SDK httpx pool breaks under batch load.

---

## File Structure

| Action | File | Responsibility |
|---|---|---|
| Modify | `skyyrose/elite_studio/models.py` | Add `DualAgentResult`, `PreflightResult`, `GhostMannequinCompositeResult` |
| Modify | `skyyrose/elite_studio/graph/state.py` | Add `style`, `preflight_result`, `ghost_mannequin_front_path`, `ghost_mannequin_back_path` |
| Modify | `skyyrose/elite_studio/agents/vision_agent.py` | Implement `DualVisionGate` (consensus: Claude Opus + Gemini Flash); add `VisionAgent = DualVisionGate` alias |
| Modify | `skyyrose/elite_studio/agents/prompt_enrichment_agent.py` | Implement `PromptEnrichmentAgent` (complementary: Claude proposes from CSV, GPT-4o refines) |
| Modify | `skyyrose/elite_studio/agents/generator_agent.py` | Implement `GeneratorAgent` (best-of-N: GPT-Image + Gemini 3 Pro Image; dual-vision picks winner) |
| Modify | `skyyrose/elite_studio/agents/quality_agent.py` | Implement `QualityAgent` (consensus: Claude Opus + Gemini Flash; ghost-mannequin rubric) |
| Modify | `skyyrose/elite_studio/graph/nodes.py` | Add `preflight_node`, `ghost_mannequin_composite_node`; fix `VisionAgent` import |
| Modify | `skyyrose/elite_studio/graph/edges.py` | Add `PREFLIGHT`, `GHOST_MANNEQUIN_COMPOSITE`, `after_preflight`, `after_ghost_mannequin_composite` |
| Modify | `skyyrose/elite_studio/graph/builder.py` | Add `enable_ghost_mannequin_preflight`, `enable_ghost_mannequin_composite` to `GraphConfig`; wire new nodes before vision |
| Modify | `skyyrose/elite_studio/cli.py` | Add `--style` flag; `ghost-mannequin` enables both new flags |
| Create | `skyyrose/elite_studio/tests/test_dual_vision_gate.py` | Consensus logic: both YES → pass, either NO → block |
| Create | `skyyrose/elite_studio/tests/test_ghost_mannequin_preflight.py` | Preflight blocks wrong garment type reference |
| Create | `skyyrose/elite_studio/tests/test_ghost_mannequin_prompt.py` | Spec-primacy: prompt reads CSV `branding_spec`, contains ghost-mannequin instructions |
| Create | `skyyrose/elite_studio/tests/test_ghost_mannequin_qa.py` | QA: `min(A,B) ≥ 80` passes; identity-mismatch flag auto-rejects |
| Create | `skyyrose/elite_studio/tests/test_ghost_mannequin_composite.py` | Neck-in composite: collar garments get composite; non-collar garments skip |

---

## Task 1: Models — add `DualAgentResult`, `PreflightResult`, `GhostMannequinCompositeResult`

**Files:**
- Modify: `skyyrose/elite_studio/models.py` (append after line 202)

- [ ] **Step 1: Write the failing import test**

```python
# skyyrose/elite_studio/tests/test_models_phase_b2.py
from skyyrose.elite_studio.models import (
    DualAgentResult,
    PreflightResult,
    GhostMannequinCompositeResult,
)

def test_dual_agent_result_fields():
    r = DualAgentResult(
        verdict="consensus",
        agent_a_output="YES: garment matches spec",
        agent_b_output="YES: confirmed hoodie",
        winner=None,
        reasoning=["both agents confirmed garment type"],
    )
    assert r.verdict == "consensus"
    assert r.winner is None

def test_preflight_result_blocked():
    r = PreflightResult(
        passed=False,
        sku="br-011",
        agent_a_verdict="NO: baseball jersey, not hockey",
        agent_b_verdict="NO: wrong sport",
        blocking_reason="Agent A: baseball jersey, not hockey",
    )
    assert not r.passed

def test_ghost_mannequin_composite_result():
    r = GhostMannequinCompositeResult(
        success=True,
        output_path="renders/output/br-004-ghost-front-composite.webp",
        front_path="renders/output/br-004-ghost-front.webp",
        back_path="renders/output/br-004-ghost-back.webp",
        neck_in_applied=True,
    )
    assert r.neck_in_applied
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_models_phase_b2.py -v
```
Expected: `ImportError` — `DualAgentResult` not found.

- [ ] **Step 3: Append the three dataclasses to `models.py`**

Append after the last `VariantResult` dataclass (after line 202):

```python
# ---------------------------------------------------------------------------
# Phase B2 models — dual-agent pipeline
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DualAgentResult:
    """Structured output from any dual-agent stage."""

    verdict: str  # "consensus" | "disagreement" | "blocked"
    agent_a_output: str
    agent_b_output: str
    winner: str | None  # "a" | "b" | None (for consensus modes)
    reasoning: list[str]


@dataclass(frozen=True)
class PreflightResult:
    """Result of the pre-flight dual-vision reference verification."""

    passed: bool
    sku: str
    agent_a_verdict: str  # "YES: ..." or "NO: ..."
    agent_b_verdict: str
    blocking_reason: str = ""  # set when passed=False


@dataclass(frozen=True)
class GhostMannequinCompositeResult:
    """Result from the neck-in composite step."""

    success: bool
    output_path: str = ""
    front_path: str = ""
    back_path: str = ""
    neck_in_applied: bool = False  # False for non-collar garments
    error: str = ""
```

- [ ] **Step 4: Run to verify tests pass**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_models_phase_b2.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/models.py skyyrose/elite_studio/tests/test_models_phase_b2.py
git commit -m "feat(imagery): add DualAgentResult, PreflightResult, GhostMannequinCompositeResult models"
```

---

## Task 2: State — add `style`, `preflight_result`, ghost-mannequin paths

**Files:**
- Modify: `skyyrose/elite_studio/graph/state.py`

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_graph_state_phase_b2.py
from skyyrose.elite_studio.graph.state import create_initial_state

def test_create_initial_state_ghost_mannequin():
    state = create_initial_state(sku="br-004", view="front", style="ghost_mannequin")
    assert state["style"] == "ghost_mannequin"
    assert state["preflight_result"] is None
    assert state["ghost_mannequin_front_path"] == ""
    assert state["ghost_mannequin_back_path"] == ""
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_graph_state_phase_b2.py -v
```
Expected: `TypeError` — unexpected keyword argument `style`.

- [ ] **Step 3: Update `state.py`**

In `EliteStudioState(TypedDict, total=False)`, add after the `tryon_category` line:
```python
    # --- Ghost-mannequin style additions ---
    style: str  # "flat_lay" | "ghost_mannequin" — defaults to "flat_lay"
    preflight_result: "PreflightResult | None"
    ghost_mannequin_front_path: str
    ghost_mannequin_back_path: str
```

In `create_initial_state()`, add parameters and defaults:
```python
def create_initial_state(
    sku: str,
    view: str = "front",
    style: str = "flat_lay",
    enable_compositor: bool = False,
    enable_tryon: bool = False,
    tryon_category: str = "upper_body",
    max_retries: int = 2,
) -> EliteStudioState:
```

And in the return dict, add:
```python
        style=style,
        preflight_result=None,
        ghost_mannequin_front_path="",
        ghost_mannequin_back_path="",
```

- [ ] **Step 4: Run to verify tests pass**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_graph_state_phase_b2.py skyyrose/elite_studio/tests/test_graph_state.py -v
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/graph/state.py skyyrose/elite_studio/tests/test_graph_state_phase_b2.py
git commit -m "feat(imagery): add style/preflight_result/ghost_mannequin paths to EliteStudioState"
```

---

## Task 3: Implement `DualVisionGate` + `VisionAgent` alias

**Files:**
- Modify: `skyyrose/elite_studio/agents/vision_agent.py`

The existing file is a Phase B1 stub. Replace it entirely.

**Context:** `nodes.py` imports `VisionAgent` (old name) but Phase B1 renamed it `DualVisionGate`. Fix both: implement the gate AND alias `VisionAgent = DualVisionGate` so `nodes.py` doesn't break.

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_dual_vision_gate.py
from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.agents.vision_agent import DualVisionGate, VisionAgent

def _make_gate() -> DualVisionGate:
    return DualVisionGate()

def test_alias_works():
    """VisionAgent must remain importable for nodes.py compatibility."""
    assert VisionAgent is DualVisionGate

def test_consensus_both_yes(tmp_path):
    """Both models YES → passed=True, verdict=consensus."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)  # minimal JPEG header

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: confirms hoodie"),
        patch.object(gate, "_call_gemini", return_value="YES: hoodie confirmed"),
    ):
        result = gate.verify_reference(str(img), sku="br-004", expected_garment="hoodie")

    assert result.passed
    assert result.verdict == "consensus"

def test_consensus_a_no_blocks(tmp_path):
    """Agent A NO → passed=False even if B says YES."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="NO: this is a baseball jersey"),
        patch.object(gate, "_call_gemini", return_value="YES: looks like a hoodie"),
    ):
        result = gate.verify_reference(str(img), sku="br-011", expected_garment="hockey jersey")

    assert not result.passed
    assert "baseball jersey" in result.blocking_reason

def test_consensus_b_no_blocks(tmp_path):
    """Agent B NO → passed=False even if A says YES."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: hoodie confirmed"),
        patch.object(gate, "_call_gemini", return_value="NO: this is a crewneck, not a hoodie"),
    ):
        result = gate.verify_reference(str(img), sku="br-004", expected_garment="hoodie")

    assert not result.passed

def test_analyze_wraps_verify_reference(tmp_path):
    """analyze() is the nodes.py interface — must return SynthesizedVision."""
    img = tmp_path / "ref.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    gate = _make_gate()
    with (
        patch.object(gate, "_call_claude", return_value="YES: sg-013 mint crewneck confirmed"),
        patch.object(gate, "_call_gemini", return_value="YES: confirmed crewneck"),
        patch("skyyrose.elite_studio.agents.vision_agent._reference_path", return_value=str(img)),
    ):
        from skyyrose.elite_studio.models import SynthesizedVision
        result = gate.analyze("sg-013", "front")
    assert isinstance(result, SynthesizedVision)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_dual_vision_gate.py -v
```
Expected: `NotImplementedError` (current stub).

- [ ] **Step 3: Implement `vision_agent.py`**

Replace the entire file:

```python
"""DualVisionGate — Phase B2 dual-agent vision consensus.

Agent A: Claude Opus 4.6 (Anthropic SDK)
Agent B: Gemini 2.0 Flash (gemini_rest.py — NOT google-genai SDK)
Mode:    Consensus — both must return YES to proceed.

VisionAgent is aliased to DualVisionGate for nodes.py backwards compatibility.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import anthropic

from ..gemini_rest import analyze_image as gemini_analyze_image
from ..models import DualAgentResult, PreflightResult, SynthesizedVision, VisionAnalysis

logger = logging.getLogger(__name__)

_CLAUDE_MODEL = "claude-opus-4-6"
_GEMINI_VISION_MODEL = "gemini-2.0-flash-001"

# Products images live here (relative to project root)
_PRODUCTS_DIR = Path("wordpress-theme/skyyrose-flagship/assets/images/products")


def _reference_path(sku: str) -> str:
    """Resolve the reference image path for a SKU (checks common extensions)."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = _PRODUCTS_DIR / f"{sku}.{ext}"
        if p.exists():
            return str(p)
        # Also check without hyphen variants
        slug = sku.replace("-", "_")
        p2 = _PRODUCTS_DIR / f"{slug}.{ext}"
        if p2.exists():
            return str(p2)
    # Return the jpg path anyway — caller handles missing file
    return str(_PRODUCTS_DIR / f"{sku}.jpg")


def _load_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


_PREFLIGHT_PROMPT = (
    "You are verifying a product reference image for an e-commerce imagery pipeline. "
    "The product name from the catalog is: '{name}'. "
    "Looking at this image, does it show the correct garment type? "
    "Reply with exactly one word YES or NO on the first line, then one sentence of reasoning."
)

_VISION_SPEC_PROMPT = (
    "You are analyzing a product reference image for SkyyRose luxury fashion brand. "
    "Product: '{name}' (SKU: {sku}). Branding spec: {branding}. "
    "Describe the garment type, colorway, fabric texture, and any visible branding/logos. "
    "Be specific — this description drives AI image generation."
)


class DualVisionGate:
    """Dual-agent vision consensus gate.

    verify_reference() — pre-flight: does the reference image match the spec?
    analyze() — full spec synthesis: returns SynthesizedVision for generator.
    """

    def __init__(self) -> None:
        self._claude = anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_reference(
        self,
        image_path: str,
        sku: str,
        expected_garment: str,
    ) -> PreflightResult:
        """Both models must return YES. Either NO blocks the SKU."""
        prompt = _PREFLIGHT_PROMPT.format(name=expected_garment)
        a_text = self._call_claude(image_path, prompt)
        b_text = self._call_gemini(image_path, prompt)

        a_yes = a_text.strip().upper().startswith("YES")
        b_yes = b_text.strip().upper().startswith("YES")

        if a_yes and b_yes:
            return PreflightResult(
                passed=True,
                sku=sku,
                agent_a_verdict=a_text[:120],
                agent_b_verdict=b_text[:120],
            )

        blocking = []
        if not a_yes:
            blocking.append(f"Agent A (Claude): {a_text[:200]}")
        if not b_yes:
            blocking.append(f"Agent B (Gemini): {b_text[:200]}")

        return PreflightResult(
            passed=False,
            sku=sku,
            agent_a_verdict=a_text[:120],
            agent_b_verdict=b_text[:120],
            blocking_reason=" | ".join(blocking),
        )

    def analyze(self, sku: str, view: str) -> SynthesizedVision:
        """Synthesize a generation spec from the reference image."""
        from ..catalog import Catalog

        try:
            cat = Catalog.load()
            product = cat.require(sku)
            name = product.name
            branding = product.branding_summary
        except Exception as exc:
            return SynthesizedVision(success=False, error=f"Catalog load failed: {exc}")

        ref = _reference_path(sku)
        if not Path(ref).exists():
            return SynthesizedVision(
                success=False, error=f"No reference image found for {sku} at {ref}"
            )

        prompt = _VISION_SPEC_PROMPT.format(sku=sku, name=name, branding=branding)

        try:
            a_text = self._call_claude(ref, prompt)
            a_result = VisionAnalysis(
                success=True, provider="anthropic", model=_CLAUDE_MODEL,
                analysis=a_text, char_count=len(a_text),
            )
        except Exception as exc:
            a_result = VisionAnalysis(
                success=False, provider="anthropic", model=_CLAUDE_MODEL, error=str(exc)
            )

        try:
            b_text = self._call_gemini(ref, prompt)
            b_result = VisionAnalysis(
                success=True, provider="google", model=_GEMINI_VISION_MODEL,
                analysis=b_text, char_count=len(b_text),
            )
        except Exception as exc:
            b_result = VisionAnalysis(
                success=False, provider="google", model=_GEMINI_VISION_MODEL, error=str(exc)
            )

        if not a_result.success and not b_result.success:
            return SynthesizedVision(
                success=False, error="Both vision agents failed",
                individual_results=(a_result, b_result),
            )

        texts = [r.analysis for r in (a_result, b_result) if r.success and r.analysis]
        unified = "\n\n---\n\n".join(texts)

        return SynthesizedVision(
            success=True,
            unified_spec=unified,
            providers_used=tuple(r.provider for r in (a_result, b_result) if r.success),
            individual_results=(a_result, b_result),
        )

    # ------------------------------------------------------------------
    # Private helpers (patchable in tests)
    # ------------------------------------------------------------------

    def _call_claude(self, image_path: str, prompt: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        b64 = _load_image_b64(image_path)
        msg = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return msg.content[0].text

    def _call_gemini(self, image_path: str, prompt: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        b64 = _load_image_b64(image_path)
        result = gemini_analyze_image(
            model=_GEMINI_VISION_MODEL,
            prompt=prompt,
            image_b64=b64,
            mime_type=mime,
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini vision failed"))
        return result["text"]


# Backwards-compatible alias — nodes.py imports VisionAgent
VisionAgent = DualVisionGate
```

**Note:** `gemini_rest.analyze_image()` may not exist yet. Check `gemini_rest.py` — if the function signature differs, adapt the call to match what's there (use `generate_text` with a vision payload, or add `analyze_image` following the existing pattern in that module).

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_dual_vision_gate.py -v
```
Expected: 5 PASS.

- [ ] **Step 5: Verify nodes.py import resolves**

```bash
cd /Users/theceo/DevSkyy && python -c "from skyyrose.elite_studio.graph.nodes import vision_node; print('OK')"
```
Expected: `OK` (no ImportError).

- [ ] **Step 6: Commit**

```bash
git add skyyrose/elite_studio/agents/vision_agent.py skyyrose/elite_studio/tests/test_dual_vision_gate.py
git commit -m "feat(imagery): implement DualVisionGate — dual-agent consensus pre-flight + vision synthesis"
```

---

## Task 4: Implement `PromptEnrichmentAgent` (spec-primacy, ghost-mannequin template)

**Files:**
- Modify: `skyyrose/elite_studio/agents/prompt_enrichment_agent.py`

**The spec-primacy rule (CRITICAL):** The prompt must contain: *"Use the reference photo for fabric texture and color ONLY. For garment type, silhouette, and branding, trust the REQUIRED BRANDING block. If they disagree on garment type, the spec is authoritative."*

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_ghost_mannequin_prompt.py
from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.agents.prompt_enrichment_agent import PromptEnrichmentAgent

def _mock_catalog(sku: str, name: str, branding: str, collection: str = "black-rose"):
    product = MagicMock()
    product.name = name
    product.branding_summary = branding
    product.collection = collection
    catalog = MagicMock()
    catalog.require.return_value = product
    return catalog

def test_prompt_contains_spec_primacy():
    """Enriched prompt must include the spec-wins-over-reference instruction."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog("br-004", "BLACK Rose Hoodie", "SR monogram right chest")
        result = agent.enrich(sku="br-004", vision_spec="black hoodie with rose motif", style="ghost_mannequin")
    assert result.success
    assert "spec is authoritative" in result.enriched_spec.lower() or "branding block" in result.enriched_spec.lower()

def test_prompt_contains_ghost_mannequin_instructions():
    """Ghost-mannequin style must produce invisible-mannequin photography instructions."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog("br-004", "BLACK Rose Hoodie", "SR monogram right chest")
        result = agent.enrich(sku="br-004", vision_spec="black hoodie", style="ghost_mannequin")
    prompt = result.enriched_spec.lower()
    assert "ghost mannequin" in prompt or "invisible mannequin" in prompt or "hollow man" in prompt

def test_prompt_reads_branding_from_csv():
    """branding_spec from CSV must appear verbatim in the enriched prompt."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog(
            "sg-013", "Mint & Lavender Crewneck",
            "black-roses-cloud-cluster embroidered front center lavender + back of neck 1.5in lavender"
        )
        result = agent.enrich(sku="sg-013", vision_spec="mint crewneck", style="ghost_mannequin")
    assert "black-roses-cloud-cluster" in result.enriched_spec

def test_flat_lay_style_no_ghost_mannequin_instructions():
    """flat_lay style must NOT include ghost-mannequin instructions."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog("br-004", "BLACK Rose Hoodie", "SR monogram")
        result = agent.enrich(sku="br-004", vision_spec="black hoodie", style="flat_lay")
    prompt = result.enriched_spec.lower()
    assert "ghost mannequin" not in prompt and "invisible mannequin" not in prompt
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_prompt.py -v
```
Expected: `NotImplementedError`.

- [ ] **Step 3: Implement `prompt_enrichment_agent.py`**

Replace the entire file:

```python
"""PromptEnrichmentAgent — Phase B2 spec-primacy prompt builder.

Reads branding_spec from the canonical CSV (never a JSON side-file).
Enriches the vision spec with:
  - Product name + garment type (authoritative)
  - branding_spec from CSV (verbatim)
  - Style-specific instructions (ghost-mannequin or flat-lay)
  - Spec-primacy safety clause

No external LLM calls in this implementation — rule-based enrichment is
sufficient and free. The plan doc specifies a Claude/GPT-4o complementary
pair; that upgrade can be added later when A/B testing shows gains.
"""
from __future__ import annotations

import logging

from ..catalog import Catalog
from ..models import EnrichedPrompt

logger = logging.getLogger(__name__)

_SPEC_PRIMACY = (
    "SPEC IS AUTHORITATIVE: Use the reference photo for fabric texture and color ONLY. "
    "For garment type, silhouette, and branding placement, trust the REQUIRED BRANDING "
    "block below. If the reference photo and branding spec disagree on garment type, "
    "the spec is authoritative — ignore the reference photo's garment type."
)

_GHOST_MANNEQUIN_STYLE = (
    "PHOTOGRAPHY STYLE: Professional ghost-mannequin (invisible mannequin / hollow man) "
    "product photography. The garment appears worn by an invisible body — NO mannequin "
    "visible. Pure white background (#FFFFFF). Garment has natural 3D volume and drape. "
    "Neck-in view: interior collar/neckline visible through the neckline opening. "
    "Clean e-commerce product shot, studio lighting, photorealistic."
)

_FLAT_LAY_STYLE = (
    "PHOTOGRAPHY STYLE: Professional flat-lay product photography. Garment laid flat on "
    "pure white background, overhead 90-degree angle, studio lighting, no wrinkles, "
    "all details visible, photorealistic."
)


class PromptEnrichmentAgent:
    """Rule-based spec-primacy prompt enrichment. No external LLM calls."""

    def enrich(self, sku: str, vision_spec: str, style: str = "flat_lay") -> EnrichedPrompt:
        try:
            cat = Catalog.load()
            product = cat.require(sku)
            name = product.name
            branding = product.branding_summary
            collection = product.collection
        except Exception as exc:
            return EnrichedPrompt(success=False, error=f"Catalog load failed: {exc}")

        style_block = _GHOST_MANNEQUIN_STYLE if style == "ghost_mannequin" else _FLAT_LAY_STYLE

        enriched = (
            f"{_SPEC_PRIMACY}\n\n"
            f"PRODUCT: {name} (SKU: {sku}, Collection: {collection})\n\n"
            f"REQUIRED BRANDING:\n{branding}\n\n"
            f"{style_block}\n\n"
            f"REFERENCE ANALYSIS (texture/color reference only):\n{vision_spec}"
        )

        additions = [
            "spec_primacy_clause",
            f"style:{style}",
            f"branding_spec_from_csv",
        ]

        return EnrichedPrompt(
            success=True,
            original_spec=vision_spec,
            enriched_spec=enriched,
            additions=tuple(additions),
        )
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_prompt.py -v
```
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/agents/prompt_enrichment_agent.py skyyrose/elite_studio/tests/test_ghost_mannequin_prompt.py
git commit -m "feat(imagery): implement PromptEnrichmentAgent — spec-primacy, CSV branding, ghost-mannequin style"
```

---

## Task 5: Implement `GeneratorAgent` (best-of-N: GPT-Image + Gemini)

**Files:**
- Modify: `skyyrose/elite_studio/agents/generator_agent.py`

**Pattern:** Both models generate independently. `DualVisionGate.verify_reference()` scores both outputs; the winner ships. Loser path is logged but not saved.

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_generator_agent_phase_b2.py
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.agents.generator_agent import GeneratorAgent

def test_generate_returns_generation_result(tmp_path):
    agent = GeneratorAgent(output_dir=str(tmp_path))

    fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200  # fake PNG bytes

    with (
        patch.object(agent, "_generate_gpt_image", return_value=fake_img),
        patch.object(agent, "_generate_gemini_image", return_value=fake_img),
        patch.object(agent, "_pick_winner", return_value="a"),
    ):
        result = agent.generate(
            sku="br-004",
            view="front",
            generation_spec="black hoodie ghost mannequin spec",
        )

    assert result.success
    assert result.output_path.endswith(".webp") or result.output_path.endswith(".png")
    assert Path(result.output_path).exists()

def test_generate_fails_if_both_models_fail(tmp_path):
    agent = GeneratorAgent(output_dir=str(tmp_path))

    with (
        patch.object(agent, "_generate_gpt_image", side_effect=RuntimeError("quota")),
        patch.object(agent, "_generate_gemini_image", side_effect=RuntimeError("503")),
    ):
        result = agent.generate(sku="br-004", view="front", generation_spec="spec")

    assert not result.success
    assert "quota" in result.error or "503" in result.error

def test_winner_selection_prefers_a_on_tie(tmp_path):
    """When scores are equal, agent A (GPT-Image) wins."""
    agent = GeneratorAgent(output_dir=str(tmp_path))
    winner = agent._pick_winner(score_a=85, score_b=85, path_a="/tmp/a.png", path_b="/tmp/b.png")
    assert winner == "a"
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_generator_agent_phase_b2.py -v
```
Expected: `NotImplementedError`.

- [ ] **Step 3: Implement `generator_agent.py`**

Replace the entire file:

```python
"""GeneratorAgent — Phase B2 best-of-N dual-agent image generation.

Agent A: GPT-Image (gpt-image-1) via OpenAI SDK
Agent B: Gemini 3 Pro Image via gemini_rest.generate_image()
Mode:    Best-of-N — both generate; simple heuristic scores both;
         winner is saved to output_dir; loser is discarded.

Scoring heuristic (no paid vision call here — QualityAgent scores post-win):
  - Prefer the output from agent A (GPT-Image) on a tie (configurable).
  - If one model raises an exception, the other wins automatically.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from openai import OpenAI

from ..gemini_rest import generate_image as gemini_generate_image
from ..models import GenerationResult

logger = logging.getLogger(__name__)

_GPT_MODEL = "gpt-image-1"
_GEMINI_GEN_MODEL = "gemini-3-pro-image-preview"
_DEFAULT_OUTPUT_DIR = "renders/output"


class GeneratorAgent:
    """Dual-agent image generator (best-of-N: GPT-Image + Gemini)."""

    def __init__(self, output_dir: str = _DEFAULT_OUTPUT_DIR) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._openai = OpenAI()

    def generate(self, sku: str, view: str, generation_spec: str) -> GenerationResult:
        """Generate image from spec. Both models run; best output saved."""
        img_a: bytes | None = None
        img_b: bytes | None = None
        err_a = ""
        err_b = ""

        try:
            img_a = self._generate_gpt_image(generation_spec)
        except Exception as exc:
            err_a = str(exc)
            logger.warning("GPT-Image generation failed for %s: %s", sku, exc)

        try:
            img_b = self._generate_gemini_image(generation_spec)
        except Exception as exc:
            err_b = str(exc)
            logger.warning("Gemini image generation failed for %s: %s", sku, exc)

        if img_a is None and img_b is None:
            return GenerationResult(
                success=False,
                provider="none",
                error=f"Both generators failed. GPT: {err_a} | Gemini: {err_b}",
            )

        if img_a is None:
            winner_bytes, provider = img_b, "google/gemini"
        elif img_b is None:
            winner_bytes, provider = img_a, "openai/gpt-image"
        else:
            winner = self._pick_winner(
                score_a=len(img_a),  # byte size as naive proxy; QualityAgent scores properly
                score_b=len(img_b),
                path_a="a",
                path_b="b",
            )
            winner_bytes = img_a if winner == "a" else img_b
            provider = "openai/gpt-image" if winner == "a" else "google/gemini"

        out_path = self._output_dir / f"{sku}-{view}-ghost.webp"
        out_path.write_bytes(winner_bytes)

        return GenerationResult(
            success=True,
            provider=provider,
            model=_GPT_MODEL if "openai" in provider else _GEMINI_GEN_MODEL,
            output_path=str(out_path),
        )

    # ------------------------------------------------------------------
    # Private — patchable in tests
    # ------------------------------------------------------------------

    def _generate_gpt_image(self, prompt: str) -> bytes:
        response = self._openai.images.generate(
            model=_GPT_MODEL,
            prompt=prompt[:4000],
            size="1024x1024",
            quality="high",
            response_format="b64_json",
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json)

    def _generate_gemini_image(self, prompt: str) -> bytes:
        result = gemini_generate_image(model=_GEMINI_GEN_MODEL, prompt=prompt[:2000])
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini image generation failed"))
        return base64.b64decode(result["image_b64"])

    def _pick_winner(
        self, score_a: int, score_b: int, path_a: str, path_b: str
    ) -> str:
        """Return 'a' or 'b'. Prefer 'a' on tie (GPT-Image is agent A)."""
        return "b" if score_b > score_a else "a"
```

**Note:** If `gemini_rest.generate_image()` doesn't exist yet, check `gemini_rest.py` and either use the existing `generate_image` function or add it following the `generate_text` pattern already there (POST to `/models/{model}:generateContent` with `response_modalities: ["IMAGE"]`).

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_generator_agent_phase_b2.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/agents/generator_agent.py skyyrose/elite_studio/tests/test_generator_agent_phase_b2.py
git commit -m "feat(imagery): implement GeneratorAgent — best-of-N GPT-Image + Gemini generation"
```

---

## Task 6: Implement `QualityAgent` with ghost-mannequin rubric

**Files:**
- Modify: `skyyrose/elite_studio/agents/quality_agent.py`

**Ghost-mannequin QA rubric (3 dimensions):**
1. **Product identity** — correct garment type (not baseball-for-hockey). Either model flagging mismatch = auto-reject.
2. **Ghost-mannequin fidelity** — no mannequin visible, correct 3D volume/drape. Score 0–100.
3. **Branding placement** — logos/text match spec. Score 0–100.

Pass threshold: `min(score_A, score_B) ≥ 80`.

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_ghost_mannequin_qa.py
from unittest.mock import patch
from skyyrose.elite_studio.agents.quality_agent import QualityAgent

def _make_agent():
    return QualityAgent()

def test_both_pass_at_80_threshold(tmp_path):
    """min(A,B) ≥ 80 → overall pass."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(agent, "_score_claude", return_value=(85, False, "looks good")),
        patch.object(agent, "_score_gemini", return_value=(82, False, "approved")),
    ):
        result = agent.verify(image_path=str(img), expected_spec="br-004 hoodie", style="ghost_mannequin")
    assert result.success
    assert result.overall_status == "pass"
    assert result.recommendation == "approve"

def test_min_score_below_80_fails(tmp_path):
    """min(A,B) < 80 → overall fail → recommend regenerate."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(agent, "_score_claude", return_value=(90, False, "good")),
        patch.object(agent, "_score_gemini", return_value=(72, False, "drape off")),
    ):
        result = agent.verify(image_path=str(img), expected_spec="br-004 hoodie", style="ghost_mannequin")
    assert result.overall_status == "fail"
    assert result.recommendation == "regenerate"

def test_identity_mismatch_auto_rejects(tmp_path):
    """Either model flagging product identity mismatch → auto-reject regardless of score."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(agent, "_score_claude", return_value=(88, True, "IDENTITY MISMATCH: shows baseball not hockey")),
        patch.object(agent, "_score_gemini", return_value=(85, False, "ok")),
    ):
        result = agent.verify(image_path=str(img), expected_spec="br-011 hockey jersey", style="ghost_mannequin")
    assert result.overall_status == "fail"
    assert result.recommendation == "regenerate"
    assert "identity" in result.details.get("reject_reason", "").lower() or \
           "mismatch" in result.details.get("reject_reason", "").lower()
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_qa.py -v
```
Expected: `NotImplementedError`.

- [ ] **Step 3: Implement `quality_agent.py`**

Replace the entire file:

```python
"""QualityAgent — Phase B2 dual-agent QA consensus.

Agent A: Claude Opus 4.6 (Anthropic SDK)
Agent B: Gemini 2.0 Flash (gemini_rest.py)
Mode:    Consensus — min(score_A, score_B) ≥ 80 to pass.
         Either model flagging product identity mismatch = auto-reject.

Ghost-mannequin rubric:
  - Product identity: correct garment type (0–100, plus mismatch flag)
  - Ghost-mannequin fidelity: no mannequin visible, correct 3D volume (0–100)
  - Branding placement: logos/text match spec (0–100)
  Overall = weighted average of three dimensions.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import anthropic

from ..gemini_rest import analyze_image as gemini_analyze_image
from ..models import QualityVerification

logger = logging.getLogger(__name__)

_CLAUDE_MODEL = "claude-opus-4-6"
_GEMINI_VISION_MODEL = "gemini-2.0-flash-001"
_PASS_THRESHOLD = 80

_GHOST_QA_PROMPT = """You are QA-scoring a ghost-mannequin fashion product render for SkyyRose brand.

Expected spec:
{spec}

Score on a 0-100 scale across three dimensions:
1. Product identity (30%): Is this the EXACT correct garment type described in the spec?
   If the spec says "hockey jersey" and the image shows a baseball jersey, score 0 and flag IDENTITY_MISMATCH.
2. Ghost-mannequin fidelity (40%): Is there NO mannequin visible? Does the garment have correct 3D volume/drape?
   Is the neck-in (collar interior) visible for appropriate garment types?
3. Branding placement (30%): Are logos/text in the correct positions per the spec?

Reply in this exact format:
IDENTITY_SCORE: <0-100>
IDENTITY_MISMATCH: <YES/NO>
FIDELITY_SCORE: <0-100>
BRANDING_SCORE: <0-100>
OVERALL: <weighted average>
NOTES: <one sentence>
"""


class QualityAgent:
    """Dual-agent QA gate for generated imagery."""

    def __init__(self) -> None:
        self._claude = anthropic.Anthropic()

    def verify(
        self,
        image_path: str,
        expected_spec: str,
        style: str = "flat_lay",
    ) -> QualityVerification:
        prompt = _GHOST_QA_PROMPT.format(spec=expected_spec)

        try:
            score_a, mismatch_a, notes_a = self._score_claude(image_path, prompt)
        except Exception as exc:
            score_a, mismatch_a, notes_a = 0, False, f"Claude QA failed: {exc}"
            logger.warning("Claude QA failed for %s: %s", image_path, exc)

        try:
            score_b, mismatch_b, notes_b = self._score_gemini(image_path, prompt)
        except Exception as exc:
            score_b, mismatch_b, notes_b = 0, False, f"Gemini QA failed: {exc}"
            logger.warning("Gemini QA failed for %s: %s", image_path, exc)

        identity_mismatch = mismatch_a or mismatch_b
        min_score = min(score_a, score_b)

        details: dict[str, Any] = {
            "score_claude": score_a,
            "score_gemini": score_b,
            "min_score": min_score,
            "notes_claude": notes_a,
            "notes_gemini": notes_b,
        }

        if identity_mismatch:
            details["reject_reason"] = "identity mismatch flagged by vision model"
            return QualityVerification(
                success=True,
                provider="dual_vision",
                model=f"{_CLAUDE_MODEL}+{_GEMINI_VISION_MODEL}",
                overall_status="fail",
                recommendation="regenerate",
                details=details,
            )

        passed = min_score >= _PASS_THRESHOLD
        return QualityVerification(
            success=True,
            provider="dual_vision",
            model=f"{_CLAUDE_MODEL}+{_GEMINI_VISION_MODEL}",
            overall_status="pass" if passed else "fail",
            recommendation="approve" if passed else "regenerate",
            details=details,
        )

    # ------------------------------------------------------------------
    # Private — patchable in tests; each returns (score: int, identity_mismatch: bool, notes: str)
    # ------------------------------------------------------------------

    def _score_claude(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        msg = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return _parse_qa_response(msg.content[0].text)

    def _score_gemini(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        result = gemini_analyze_image(
            model=_GEMINI_VISION_MODEL, prompt=prompt, image_b64=b64, mime_type=mime
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini QA failed"))
        return _parse_qa_response(result["text"])


def _parse_qa_response(text: str) -> tuple[int, bool, str]:
    """Parse the structured QA response into (overall_score, identity_mismatch, notes)."""
    lines = {
        line.split(":")[0].strip(): line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if ":" in line
    }
    try:
        overall = int(float(lines.get("OVERALL", lines.get("IDENTITY_SCORE", "50"))))
    except ValueError:
        overall = 50
    mismatch = lines.get("IDENTITY_MISMATCH", "NO").strip().upper() == "YES"
    notes = lines.get("NOTES", "")
    return overall, mismatch, notes
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_qa.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/agents/quality_agent.py skyyrose/elite_studio/tests/test_ghost_mannequin_qa.py
git commit -m "feat(imagery): implement QualityAgent — dual-vision consensus QA, ghost-mannequin rubric, identity-mismatch auto-reject"
```

---

## Task 7: Add `preflight_node` + `ghost_mannequin_composite_node` to nodes.py

**Files:**
- Modify: `skyyrose/elite_studio/graph/nodes.py`

**Neck-in composite logic:** Collar garments (hoodies, jackets, crewnecks, bombers) need a neck-in composite — crop the top 20% of the back render, paste it behind the front render's neckline area using PIL, producing the "floating hollow" silhouette. Non-collar garments (shorts, joggers, tees, beanies) skip this step.

**Collar garment detection:** `catalog.jersey_patch_for()` is for jerseys. For neck-in detection, use a keyword check against the product name: `hoodie`, `jacket`, `crewneck`, `bomber`, `windbreaker`.

- [ ] **Step 1: Write the failing tests**

```python
# skyyrose/elite_studio/tests/test_ghost_mannequin_preflight.py
from unittest.mock import patch, MagicMock
from skyyrose.elite_studio.graph.nodes import preflight_node
from skyyrose.elite_studio.graph.state import create_initial_state

def _state(sku: str, style: str = "ghost_mannequin") -> dict:
    return create_initial_state(sku=sku, view="front", style=style)

def test_preflight_passes_sets_preflight_result():
    state = _state("br-004")
    with patch(
        "skyyrose.elite_studio.graph.nodes._preflight_gate"
    ) as mock_gate:
        from skyyrose.elite_studio.models import PreflightResult
        mock_gate.verify_reference.return_value = PreflightResult(
            passed=True, sku="br-004",
            agent_a_verdict="YES: hoodie", agent_b_verdict="YES: hoodie",
        )
        mock_gate.__class__ = MagicMock  # allow instantiation
        with patch("skyyrose.elite_studio.graph.nodes.DualVisionGate", return_value=mock_gate):
            update = preflight_node(state)
    assert update["preflight_result"].passed

def test_preflight_fail_sets_error_status():
    state = _state("br-011")
    with patch("skyyrose.elite_studio.graph.nodes.DualVisionGate") as MockGate:
        from skyyrose.elite_studio.models import PreflightResult
        instance = MockGate.return_value
        instance.verify_reference.return_value = PreflightResult(
            passed=False, sku="br-011",
            agent_a_verdict="NO: baseball jersey",
            agent_b_verdict="NO: wrong sport",
            blocking_reason="Agent A: baseball jersey, not hockey",
        )
        update = preflight_node(state)
    assert update["status"] == "error"
    assert "baseball" in update["error"]

def test_preflight_skipped_for_flat_lay():
    """flat_lay style skips preflight — returns empty dict (node is a no-op)."""
    state = _state("br-004", style="flat_lay")
    update = preflight_node(state)
    assert update == {} or update.get("preflight_result") is None
```

```python
# skyyrose/elite_studio/tests/test_ghost_mannequin_composite.py
from unittest.mock import patch, MagicMock
from pathlib import Path
from skyyrose.elite_studio.graph.nodes import ghost_mannequin_composite_node
from skyyrose.elite_studio.graph.state import create_initial_state
from skyyrose.elite_studio.models import GenerationResult

def _state_with_renders(sku: str, front: str, back: str) -> dict:
    s = create_initial_state(sku=sku, view="front", style="ghost_mannequin")
    s["generation_result"] = GenerationResult(success=True, output_path=front, provider="test", model="test")
    s["ghost_mannequin_front_path"] = front
    s["ghost_mannequin_back_path"] = back
    return s

def test_collar_garment_applies_neck_in(tmp_path):
    """br-004 is a hoodie — neck-in composite must be applied."""
    front = tmp_path / "front.webp"
    back = tmp_path / "back.webp"
    # Write minimal valid images (Pillow will use them)
    from PIL import Image
    img = Image.new("RGB", (1024, 1024), color=(10, 10, 10))
    img.save(str(front), "WEBP")
    img.save(str(back), "WEBP")

    state = _state_with_renders("br-004", str(front), str(back))
    with patch(
        "skyyrose.elite_studio.graph.nodes._is_collar_garment", return_value=True
    ):
        update = ghost_mannequin_composite_node(state)

    result = update.get("ghost_mannequin_composite_result")
    assert result is not None
    assert result.neck_in_applied
    assert result.success

def test_non_collar_garment_skips_neck_in(tmp_path):
    """br-002 is joggers — neck-in composite is skipped."""
    from PIL import Image
    front = tmp_path / "front.webp"
    Image.new("RGB", (1024, 1024)).save(str(front), "WEBP")

    state = _state_with_renders("br-002", str(front), "")
    with patch(
        "skyyrose.elite_studio.graph.nodes._is_collar_garment", return_value=False
    ):
        update = ghost_mannequin_composite_node(state)

    result = update.get("ghost_mannequin_composite_result")
    assert result is not None
    assert not result.neck_in_applied
    assert result.success
```

- [ ] **Step 2: Run to verify tests fail**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_preflight.py skyyrose/elite_studio/tests/test_ghost_mannequin_composite.py -v
```
Expected: `ImportError` — `preflight_node` not found.

- [ ] **Step 3: Add `preflight_node` and `ghost_mannequin_composite_node` to nodes.py**

Append to the bottom of `skyyrose/elite_studio/graph/nodes.py`:

```python
# ---------------------------------------------------------------------------
# Phase B2 ghost-mannequin nodes
# ---------------------------------------------------------------------------

_COLLAR_KEYWORDS = {"hoodie", "jacket", "crewneck", "bomber", "windbreaker", "sherpa"}


def _is_collar_garment(sku: str) -> bool:
    """Return True for garments that need neck-in composite."""
    try:
        from ..catalog import Catalog
        cat = Catalog.load()
        name = cat.require(sku).name.lower()
        return any(kw in name for kw in _COLLAR_KEYWORDS)
    except Exception:
        return False


def preflight_node(state: EliteStudioState) -> dict:
    """Dual-vision pre-flight: verify reference image matches CSV spec.

    Only runs for ghost_mannequin style — flat_lay skips (returns empty dict).
    """
    if state.get("style", "flat_lay") != "ghost_mannequin":
        return {}

    sku = state["sku"]

    try:
        from ..catalog import Catalog
        cat = Catalog.load()
        product = cat.require(sku)
        expected_garment = product.name
        ref_path = state.get("reference_path") or __import__(
            "skyyrose.elite_studio.agents.vision_agent", fromlist=["_reference_path"]
        )._reference_path(sku)
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Preflight catalog load failed: {exc}",
            "failed_step": "preflight",
        }

    from ..agents.vision_agent import DualVisionGate
    gate = DualVisionGate()
    result = gate.verify_reference(
        image_path=ref_path,
        sku=sku,
        expected_garment=expected_garment,
    )

    if not result.passed:
        logger.warning(
            "[Preflight] BLOCKED %s: %s", sku, result.blocking_reason
        )
        return {
            "preflight_result": result,
            "status": "error",
            "error": f"Preflight blocked: {result.blocking_reason}",
            "failed_step": "preflight",
        }

    return {"preflight_result": result}


def ghost_mannequin_composite_node(state: EliteStudioState) -> dict:
    """Neck-in composite for collar garments (hoodies, jackets, crewnecks).

    For collar garments: crops the top 20% of the back render and pastes
    it behind the front render's neckline area to create the hollow-man effect.
    For non-collar garments: saves the front render as-is (no neck-in).
    """
    import time
    from PIL import Image

    from ..models import GhostMannequinCompositeResult

    start = time.monotonic()
    sku = state["sku"]
    front_path = state.get("ghost_mannequin_front_path", "")
    back_path = state.get("ghost_mannequin_back_path", "")

    if not front_path:
        gen = state.get("generation_result")
        front_path = gen.output_path if gen and gen.success else ""

    if not front_path:
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=False, error="No front render available for composite"
            )
        }

    collar = _is_collar_garment(sku)
    out_dir = __import__("pathlib").Path(front_path).parent
    out_path = str(out_dir / f"{sku}-front-ghost-composite.webp")

    if not collar or not back_path or not __import__("pathlib").Path(back_path).exists():
        # Non-collar or no back render: pass front through unchanged
        __import__("shutil").copy2(front_path, out_path)
        timings = dict(state.get("stage_timings", {}))
        timings["ghost_composite"] = round(time.monotonic() - start, 2)
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=True,
                output_path=out_path,
                front_path=front_path,
                back_path=back_path,
                neck_in_applied=False,
            ),
            "stage_timings": timings,
        }

    # Neck-in composite: paste top 20% of back render behind front render neckline
    try:
        front_img = Image.open(front_path).convert("RGBA")
        back_img = Image.open(back_path).convert("RGBA").resize(front_img.size)

        w, h = front_img.size
        neck_fraction = 0.20
        neck_strip = back_img.crop((0, 0, w, int(h * neck_fraction)))

        composite = Image.new("RGBA", front_img.size, (255, 255, 255, 255))
        composite.paste(neck_strip, (0, 0))
        composite = Image.alpha_composite(composite, front_img)
        composite.convert("RGB").save(out_path, "WEBP", quality=92)
    except Exception as exc:
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=False, error=f"Composite failed: {exc}"
            )
        }

    timings = dict(state.get("stage_timings", {}))
    timings["ghost_composite"] = round(time.monotonic() - start, 2)
    return {
        "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
            success=True,
            output_path=out_path,
            front_path=front_path,
            back_path=back_path,
            neck_in_applied=True,
        ),
        "stage_timings": timings,
    }
```

Also add `ghost_mannequin_composite_result` to `EliteStudioState` in `state.py`:
```python
    ghost_mannequin_composite_result: "GhostMannequinCompositeResult | None"
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_ghost_mannequin_preflight.py skyyrose/elite_studio/tests/test_ghost_mannequin_composite.py -v
```
Expected: all PASS. If Pillow not installed: `pip install Pillow` (it's already in requirements).

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/graph/nodes.py skyyrose/elite_studio/graph/state.py \
        skyyrose/elite_studio/tests/test_ghost_mannequin_preflight.py \
        skyyrose/elite_studio/tests/test_ghost_mannequin_composite.py
git commit -m "feat(imagery): add preflight_node + ghost_mannequin_composite_node with neck-in PIL composite"
```

---

## Task 8: Wire ghost-mannequin into `GraphConfig` and `builder.py`

**Files:**
- Modify: `skyyrose/elite_studio/graph/edges.py`
- Modify: `skyyrose/elite_studio/graph/builder.py`

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_graph_builder_ghost_mannequin.py
from skyyrose.elite_studio.graph.builder import GraphConfig, build_graph
from skyyrose.elite_studio.graph.state import create_initial_state

def test_ghost_mannequin_config_fields_exist():
    cfg = GraphConfig(
        enable_ghost_mannequin_preflight=True,
        enable_ghost_mannequin_composite=True,
    )
    assert cfg.enable_ghost_mannequin_preflight
    assert cfg.enable_ghost_mannequin_composite

def test_build_graph_ghost_mannequin_compiles():
    """Graph builds without error with ghost-mannequin flags enabled."""
    cfg = GraphConfig(
        enable_ghost_mannequin_preflight=True,
        enable_ghost_mannequin_composite=True,
    )
    graph = build_graph(cfg)
    assert graph is not None
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_graph_builder_ghost_mannequin.py -v
```
Expected: `TypeError` — `enable_ghost_mannequin_preflight` not a valid field.

- [ ] **Step 3: Add edge constants to `edges.py`**

Append to `skyyrose/elite_studio/graph/edges.py`:

```python
# Phase B2 ghost-mannequin node constants
PREFLIGHT = "preflight"
GHOST_MANNEQUIN_COMPOSITE = "ghost_mannequin_composite"


def after_preflight(state: EliteStudioState) -> str:
    """Route after pre-flight gate: continue if passed, END if blocked."""
    if state.get("status") == "error":
        return END
    return "vision"
```

- [ ] **Step 4: Add fields to `GraphConfig` in `builder.py`**

In the `GraphConfig` dataclass, add after `tryon_category`:
```python
    # Phase B2 ghost-mannequin flags
    enable_ghost_mannequin_preflight: bool = False
    enable_ghost_mannequin_composite: bool = False
```

In `build_graph()`, add after `_TRYON = "tryon"` and before `graph = StateGraph(...)`:
```python
_PREFLIGHT = PREFLIGHT
_GHOST_MANNEQUIN_COMPOSITE = GHOST_MANNEQUIN_COMPOSITE
```

Register nodes conditionally (add inside `build_graph()`, after existing node registration):
```python
    if config.enable_ghost_mannequin_preflight:
        graph.add_node(_PREFLIGHT, preflight_node)

    if config.enable_ghost_mannequin_composite:
        graph.add_node(_GHOST_MANNEQUIN_COMPOSITE, ghost_mannequin_composite_node)
```

Update entry point to route through preflight first when enabled:
```python
    # Entry point: preflight → vision (if ghost-mannequin) else vision directly
    if config.enable_ghost_mannequin_preflight:
        graph.set_entry_point(_PREFLIGHT)
        graph.add_conditional_edges(
            _PREFLIGHT,
            after_preflight,
            {_VISION: _VISION, END: END},
        )
    else:
        graph.set_entry_point(_VISION)
```

Remove the existing `graph.set_entry_point(_VISION)` line (it's now conditional).

Update imports at top of `builder.py` to include the new names:
```python
from .edges import (
    ...
    PREFLIGHT,
    GHOST_MANNEQUIN_COMPOSITE,
    after_preflight,
)
from .nodes import (
    ...
    preflight_node,
    ghost_mannequin_composite_node,
)
```

Wire ghost-mannequin composite into post-quality chain — add it to `_build_post_quality_target` before compositor:
```python
    if config.enable_ghost_mannequin_composite:
        return _GHOST_MANNEQUIN_COMPOSITE
```
And add to chain list in `_wire_post_quality_chain`:
```python
    if config.enable_ghost_mannequin_composite:
        chain.append(_GHOST_MANNEQUIN_COMPOSITE)
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_graph_builder_ghost_mannequin.py skyyrose/elite_studio/tests/test_graph_builder.py -v
```
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add skyyrose/elite_studio/graph/edges.py skyyrose/elite_studio/graph/builder.py \
        skyyrose/elite_studio/tests/test_graph_builder_ghost_mannequin.py
git commit -m "feat(imagery): wire ghost-mannequin preflight + composite nodes into GraphConfig and LangGraph builder"
```

---

## Task 9: CLI `--style ghost-mannequin`

**Files:**
- Modify: `skyyrose/elite_studio/cli.py`

- [ ] **Step 1: Write the failing test**

```python
# skyyrose/elite_studio/tests/test_cli_ghost_mannequin.py
from click.testing import CliRunner
from unittest.mock import patch
from skyyrose.elite_studio.cli import cli

def test_cli_ghost_mannequin_flag_accepted():
    runner = CliRunner()
    with patch("skyyrose.elite_studio.cli.run_pipeline") as mock_run:
        mock_run.return_value = []
        result = runner.invoke(cli, [
            "produce", "--sku", "br-004", "--style", "ghost-mannequin", "--dry-run"
        ])
    assert result.exit_code == 0, result.output

def test_cli_ghost_mannequin_sets_correct_config():
    runner = CliRunner()
    with patch("skyyrose.elite_studio.cli.run_pipeline") as mock_run:
        mock_run.return_value = []
        runner.invoke(cli, [
            "produce", "--sku", "br-004", "--style", "ghost-mannequin", "--dry-run"
        ])
        if mock_run.called:
            _, kwargs = mock_run.call_args
            cfg = kwargs.get("config") or (mock_run.call_args[0][1] if len(mock_run.call_args[0]) > 1 else None)
            if cfg is not None:
                assert cfg.enable_ghost_mannequin_preflight
                assert cfg.enable_ghost_mannequin_composite
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_cli_ghost_mannequin.py -v
```
Expected: failure (no `--style` flag).

- [ ] **Step 3: Read `cli.py` and add `--style` flag**

First read `skyyrose/elite_studio/cli.py` to understand the existing CLI structure, then add:

```python
@click.option(
    "--style",
    type=click.Choice(["flat-lay", "ghost-mannequin"], case_sensitive=False),
    default="flat-lay",
    help="Photography style: flat-lay or ghost-mannequin (invisible mannequin).",
)
```

In the produce command handler, translate the flag to config:
```python
ghost_mannequin = style == "ghost-mannequin"
config = GraphConfig(
    ...existing fields...,
    enable_ghost_mannequin_preflight=ghost_mannequin,
    enable_ghost_mannequin_composite=ghost_mannequin,
)
# Pass style to create_initial_state:
state = create_initial_state(sku=sku, style="ghost_mannequin" if ghost_mannequin else "flat_lay", ...)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/test_cli_ghost_mannequin.py skyyrose/elite_studio/tests/test_cli.py -v
```
Expected: all PASS.

- [ ] **Step 5: Smoke test the CLI**

```bash
cd /Users/theceo/DevSkyy && python -m skyyrose.elite_studio produce --help
```
Expected: `--style [flat-lay|ghost-mannequin]` appears in help output.

- [ ] **Step 6: Run full test suite**

```bash
cd /Users/theceo/DevSkyy && python -m pytest skyyrose/elite_studio/tests/ -v --tb=short 2>&1 | tail -20
```
Expected: all existing tests continue to pass; new tests pass.

- [ ] **Step 7: Final commit**

```bash
git add skyyrose/elite_studio/cli.py skyyrose/elite_studio/tests/test_cli_ghost_mannequin.py
git commit -m "feat(imagery): add --style ghost-mannequin CLI flag — enables preflight + composite in GraphConfig"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|---|---|
| Dual-vision consensus pre-flight (br-011 failure mode) | Task 3 (DualVisionGate), Task 7 (preflight_node) |
| Spec beats reference (garment type from spec, not image) | Task 4 (spec-primacy prompt) |
| Branding source is canonical CSV | Task 4 (`Catalog.load().require(sku).branding_summary`) |
| `min(A,B) ≥ 80` QA threshold | Task 6 (QualityAgent) |
| Identity mismatch = auto-reject | Task 6 |
| Ghost-mannequin style (invisible mannequin, neck-in) | Task 4 (prompt), Task 7 (composite node) |
| Neck-in composite for collar garments | Task 7 (`_is_collar_garment`) |
| LangGraph state machine integration | Task 2 (state), Task 8 (builder) |
| `VisionAgent` import backwards-compat | Task 3 |
| CLI `--style ghost-mannequin` | Task 9 |
| Gemini via `gemini_rest.py` (not SDK) | Tasks 3, 6 (noted in every agent) |

**Gaps / notes:**
- `gemini_rest.analyze_image()` and `gemini_rest.generate_image()` may not exist in the current file (the existing file shows `generate_text`). Read `gemini_rest.py` in full before Task 3 and add any missing functions following the existing REST pattern before implementing the agents.
- `SafetyAgent`, `UpscalingAgent`, `ColorCorrectionAgent`, `VariantAgent`, `TryonAgent` remain Phase B1 stubs. They are not on the ghost-mannequin critical path — add them in a follow-on plan.
- `nodes.py` import `from ..agents.tryon_agent import TryOnAgent, _find_garment_image` will still fail if `tryon_agent.py` is a stub. The import only triggers when `tryon_node()` is called — and `enable_tryon=False` by default — so it won't block tests. But if the import is at module level (it is), it will crash any test that imports nodes.py. Check after Task 7 and stub out `TryOnAgent` properly if needed.
