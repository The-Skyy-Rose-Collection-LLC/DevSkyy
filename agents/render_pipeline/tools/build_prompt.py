"""Tool 4: Compose Layer 0 + Layer 3 + Layer 2 final prompt.

ASSEMBLER ONLY. The three layers come from three different sources:
    Layer 0 — Sonnet 4.6's `articulate_layer0_fn` writes engine-specific
              rendering directives. Falls back to registry's
              `canonical_mode_v1` when Sonnet didn't run (no Anthropic
              key OR articulate_layer0_agent skipped).
    Layer 3 — Canonical positives PREPENDED, VERBATIM from
              `dossier.garment_type_lock` + `dossier.branding_block`.
              No LLM, no rewriting.
    Layer 2 — Canonical negatives APPENDED, VERBATIM from
              `dossier.negative_block`. No LLM, no rewriting.

The "identical to my products" guarantee lives here: Layers 3 + 2 are
the brand author's words going UNTOUCHED to the generator. Sonnet only
adapts rendering style (Layer 0); it cannot reach the canonical text.

F4 finding (verified): the canonical-mode prompt structure scores
88/100 first-attempt on br-001 — no contradictions, no defect-loop
hallucination. This tool preserves that contract while adding Sonnet's
engine-aware Layer 0 styling.

State writes:
    prompt (str — full assembled text)
    template_id (registry key OR 'sonnet_layer0' when Sonnet wrote it)
"""

from __future__ import annotations

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

from google.adk.tools.tool_context import ToolContext


def build_prompt_fn(sku: str, view: str, tool_context: ToolContext) -> dict:
    """Assemble L0 + L3 + L2 into the final generator prompt.

    Reads state:
        layer0_directives (Sonnet's output if articulate_layer0_agent ran)
        engine (for fallback registry path)
    Writes state:
        prompt (final assembled text)
        template_id

    Returns dict with template_id, total_chars, per-layer chars, canonical_mode,
    layer0_source ('sonnet' | 'registry_fallback').
    """
    from nano_banana.prompt_registry import PromptRegistry
    from nano_banana.spec_builder import (
        augment_prompt_with_dossier_negatives,
        augment_prompt_with_dossier_positives,
        build_dna_from_sku,
    )

    dna = build_dna_from_sku(sku)
    engine = tool_context.state.get("engine", "")
    catalog_with_sku = {**dna.catalog, "sku": sku}

    # Layer 0 — Sonnet's articulation if available, else registry fallback
    sonnet_layer0 = tool_context.state.get("layer0_directives", "")
    if sonnet_layer0:
        layer0 = sonnet_layer0
        template_id = "sonnet_layer0"
        layer0_source = "sonnet"
    else:
        registry = PromptRegistry.load()
        layer0, template_id = registry.get_prompt(dna, catalog_with_sku, view, engine)
        layer0_source = "registry_fallback"

    layer0_chars = len(layer0)

    # Layer 3 — VERBATIM dossier positives PREPENDED
    after_l3 = augment_prompt_with_dossier_positives(layer0, dna)
    layer3_chars = len(after_l3) - layer0_chars

    # Layer 2 — VERBATIM dossier negatives APPENDED
    after_l2 = augment_prompt_with_dossier_negatives(after_l3, dna)
    layer2_chars = len(after_l2) - len(after_l3)

    tool_context.state["prompt"] = after_l2
    tool_context.state["template_id"] = template_id

    return {
        "template_id": template_id,
        "layer0_source": layer0_source,
        "canonical_mode": template_id in ("canonical_mode_v1", "sonnet_layer0"),
        "total_chars": len(after_l2),
        "layer0_chars": layer0_chars,
        "layer3_chars": layer3_chars,
        "layer2_chars": layer2_chars,
    }
