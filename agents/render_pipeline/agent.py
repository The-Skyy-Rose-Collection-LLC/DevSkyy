"""RenderPipeline ADK agent — root_agent definition.

Architecture (validated against /google/adk-python via Context7):

    SequentialAgent (framework-dispatched, no top-level LLM)
    │
    ├── 1. LoadDossierAgent          gemini-2.5-flash  → load_dossier_fn
    ├── 2. ResolveSourceAgent        gemini-2.5-flash  → resolve_source_fn
    ├── 3. VisionConsensusAgent      gemini-2.5-flash  → vision_consensus_fn
    │      └─ tool internally: gemini-3-flash-preview + gpt-4o vision in parallel
    ├── 4. RouteEngineAgent          gemini-2.5-flash  → route_engine_fn
    │      └─ catalog `engine_override` first; vision-driven fallback
    ├── 5. ArticulateLayer0Agent     claude-sonnet-4-6  (no tool — direct LLM)
    │      └─ writes Layer 0 (rendering directives ONLY)
    │      └─ NEVER touches Layers 3 + 2 (canonical dossier — verbatim)
    ├── 6. BuildPromptAgent          gemini-2.5-flash  → build_prompt_fn
    │      └─ assembler: L0 (Sonnet) + L3 (verbatim) + L2 (verbatim)
    ├── 7. GenerateImageAgent        gemini-2.5-flash  → generate_image_fn  ($)
    │      └─ engine = NB Pro / GPT-image-1.5 / FLUX-pro-v1.1
    ├── 8. QAAndRefineLoop           LoopAgent(max_iterations=2)
    │      ├── QaTournamentAgent     gemini-2.5-flash  → qa_tournament_fn  ($$$)
    │      │     └─ tournament internally: gpt-5.5-pro + gemini-3.1-pro-preview + opus-4-7
    │      │     └─ also records to learning loops (Loops 1, 2, 3)
    │      ├── ScoreReasonerAgent    gemini-3-pro-preview  (no tool — reasoning)
    │      │     └─ outputs 'pass' | 'refine' | 'abort' (F5 classifier)
    │      ├── StopChecker (custom BaseAgent — escalates on pass/abort, skipping refine)
    │      └── RefineImageAgent      gemini-2.5-flash  → refine_image_fn  ($$)
    └── 9. SynthesisAgent            claude-opus-4-7  (no tool — Pydantic output_schema)
           └─ reads full session state, emits RenderResult

State flow: each sub-agent reads from `tool_context.state` (auto-injected) and
writes via tool side-effects + `output_key`. SequentialAgent guarantees order
without LLM drift. LoopAgent handles iterative refinement up to max_iterations.

Dependencies that MUST be installed in .venv-agents/ (numpy isolation per CLAUDE.md):
    pip install google-adk pydantic anthropic openai google-genai fal-client
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import AsyncGenerator

# sys.path setup (same pattern as tools/_paths.py — agents/render_pipeline/agent.py)
_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO, _REPO / "scripts"):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

# ADK imports (require google-adk installed — see .venv-agents/ note above)
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

# Tool functions — pure-Python wrappers around verified nano_banana surfaces
from agents.render_pipeline.tools import (
    articulate_layer0_fn,
    build_prompt_fn,
    generate_image_fn,
    load_dossier_fn,
    qa_tournament_fn,
    refine_image_fn,
    resolve_source_fn,
    route_engine_fn,
    vision_consensus_fn,
)

# Verified model IDs from llm/model_ids.py (single source of truth)
from llm.model_ids import (
    CLAUDE_OPUS_MODEL,
    CLAUDE_SONNET_MODEL,
    GEMINI_PRO_MODEL,
)

# ---------------------------------------------------------------------------
# Model assignments — verified per-task per CLAUDE.md + llm/model_ids.py
# ---------------------------------------------------------------------------

DISPATCH_MODEL = "gemini-2.5-flash"  # tool-dispatch sub-agents (cheap, fast, reliable)
SONNET_LAYER0 = CLAUDE_SONNET_MODEL  # layer 0 articulation (engine-style adaptation)
GEMINI_REASONING = GEMINI_PRO_MODEL  # F5 score classifier (reasoning over signals)
OPUS_SYNTHESIS = CLAUDE_OPUS_MODEL  # final RenderResult (deepest reasoning)


# ---------------------------------------------------------------------------
# Pydantic schema for the synthesis agent's structured output
# ---------------------------------------------------------------------------


class RenderResult(BaseModel):
    """Final structured output from the pipeline. Returned by SynthesisAgent."""

    sku: str = Field(description="Catalog SKU code")
    view: str = Field(description="Render view: front | back | branding")
    output_path: str | None = Field(default=None, description="Absolute path to final render")
    qa_score: float = Field(description="Final QA aggregate score (0-100)")
    qa_passed: bool = Field(description="Did the score clear the passing threshold?")
    engine_used: str = Field(description="Image generation engine that produced the final render")
    refinement_applied: bool = Field(description="Did the loop run a refinement pass?")
    refinement_engine: str = Field(default="", description="kontext|gemini-composite|none")
    cost_usd: float = Field(description="Cumulative paid-API cost for this render")
    hallucination_veto: bool = Field(
        description="Did the synthesis judge fire a hallucination veto?"
    )
    issues: list[str] = Field(default_factory=list, description="Top issues from QA tournament")
    infra_failures: list[dict] = Field(
        default_factory=list,
        description="Judges that hit infra timeouts (F5) — score may be unreliable",
    )
    final_status: str = Field(description="shipped | needs_review | failed_quality | failed_infra")
    rationale: str = Field(
        description="1-2 sentence reasoning over the run — why this result, what to watch"
    )


# ---------------------------------------------------------------------------
# StopChecker — custom BaseAgent that terminates the refinement loop
# ---------------------------------------------------------------------------


class StopChecker(BaseAgent):
    """Reads `state['loop_decision']` and escalates the loop on pass/abort.

    Placed in the LoopAgent's sub_agents BETWEEN ScoreReasoner and RefineImage,
    so a 'pass' or 'abort' decision skips the costly refine_image_fn call.
    Mirrors the canonical ADK iterative-refinement pattern (verified from
    /google/adk-python docs).
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        decision = ctx.session.state.get("loop_decision", "refine")
        should_stop = decision in ("pass", "abort")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))


# ---------------------------------------------------------------------------
# Tool wrappers — convert pure functions to ADK FunctionTools
# ---------------------------------------------------------------------------

load_dossier_tool = FunctionTool(load_dossier_fn)
resolve_source_tool = FunctionTool(resolve_source_fn)
vision_consensus_tool = FunctionTool(vision_consensus_fn)
route_engine_tool = FunctionTool(route_engine_fn)
build_prompt_tool = FunctionTool(build_prompt_fn)
generate_image_tool = FunctionTool(generate_image_fn)
qa_tournament_tool = FunctionTool(qa_tournament_fn)
refine_image_tool = FunctionTool(refine_image_fn)
# articulate_layer0_fn is also wrapped as a tool for non-ADK callers (CLI preflight, tests),
# but the ADK agent uses a direct LlmAgent with output_key (see articulate_layer0_agent below).
articulate_layer0_tool = FunctionTool(articulate_layer0_fn)

# ---------------------------------------------------------------------------
# Sub-agents (steps 1-9)
# ---------------------------------------------------------------------------

load_dossier_agent = LlmAgent(
    name="LoadDossierAgent",
    model=DISPATCH_MODEL,
    description="Step 1 — load canonical dossier for the SKU (Tier 2 hard-fail).",
    instruction=(
        "You are step 1 of a 9-step render pipeline. The user provides a SKU and view. "
        "Call load_dossier_fn with the sku. The function will hard-fail if the dossier "
        "is missing — that is intentional (Tier 2 contract). "
        "After the tool returns, output a one-line confirmation."
    ),
    tools=[load_dossier_tool],
)

resolve_source_agent = LlmAgent(
    name="ResolveSourceAgent",
    model=DISPATCH_MODEL,
    description="Step 2 — resolve the source image path for the SKU.",
    instruction=(
        "Step 2 of 9. Read the sku from state['sku'] (set by LoadDossierAgent). "
        "Call resolve_source_fn with that sku. After the tool returns, output a one-line "
        "confirmation including the source filename."
    ),
    tools=[resolve_source_tool],
)

vision_consensus_agent = LlmAgent(
    name="VisionConsensusAgent",
    model=DISPATCH_MODEL,
    description="Step 3 — dual vision describe (Gemini + OpenAI in parallel).",
    instruction=(
        "Step 3 of 9. Read sku from state['sku']. Call vision_consensus_fn with that sku. "
        "The tool runs Gemini-3-flash-preview and GPT-4o vision in parallel against the "
        "source image and merges them. Output a one-line confirmation including how many "
        "providers succeeded and the consensus garment_type."
    ),
    tools=[vision_consensus_tool],
)

route_engine_agent = LlmAgent(
    name="RouteEngineAgent",
    model=DISPATCH_MODEL,
    description="Step 4 — pick the image-gen engine (catalog override → vision-driven).",
    instruction=(
        "Step 4 of 9. Read sku from state['sku'] and view from the original user input "
        "(default 'front' if not specified). Call route_engine_fn with sku and view. "
        "The function checks catalog `engine_override` first (F3 fix); falls through to "
        "vision-driven routing. Output the chosen engine + reason."
    ),
    tools=[route_engine_tool],
)

# Step 5 — Sonnet writes Layer 0 directly. No tool, no Flash dispatch wrapper.
# The output_key writes Sonnet's response into state['layer0_directives'], which
# build_prompt_fn reads in step 6. The instruction here is the FULL Sonnet system
# prompt — the same one in articulate_layer0._SONNET_INSTRUCTION (kept in sync there
# for the non-ADK call path used by CLI preflight + tests).
articulate_layer0_agent = LlmAgent(
    name="ArticulateLayer0Agent",
    model=SONNET_LAYER0,
    description="Step 5 — Sonnet 4.6 writes engine-specific Layer 0 rendering directives.",
    instruction=(
        "You write engine-specific RENDERING DIRECTIVES (Layer 0) for a luxury fashion "
        "product-render pipeline. Your output is ONE PART of a 3-part prompt:\n\n"
        "   [Layer 3 — canonical positives, verbatim from dossier]   ← NOT YOU\n"
        "   [Layer 0 — your output: rendering directives]            ← YOU\n"
        "   [Layer 2 — canonical negatives, verbatim from dossier]   ← NOT YOU\n\n"
        "Read state['product_name'], state['collection'], state['engine'], and "
        "state['vision_consensus'] (a dict with garment_type, fabric_appearance, colors, "
        "graphics, construction).\n\n"
        "Your scope is STRICTLY rendering style:\n"
        "  + Studio setup (lighting, backdrop, drape, ghost-mannequin language)\n"
        "  + Fabric photorealism cues tuned to consensus fabric_appearance\n"
        "  + View restriction (front-only / back-only based on input)\n"
        "  + Engine-specific framing (FLUX: terse + visual; Gemini: structured + descriptive; "
        "GPT: narrative + studio-photography vocabulary)\n\n"
        "You MUST NOT:\n"
        "  - Describe the garment type, color, branding, logos, text, or graphics\n"
        "  - Negate anything (no 'do not include X')\n"
        "  - Reference the dossier — Layers 3 + 2 handle product-identity content\n"
        "  - Add brand language ('luxurious', etc.)\n\n"
        "OUTPUT: emit the layer0_directives string DIRECTLY as your response (no JSON wrapper, "
        "no preamble, no commentary). 200-450 characters. Tone: clinical, technical. "
        "Picture: Vogue editorial product shot."
    ),
    output_key="layer0_directives",
)

build_prompt_agent = LlmAgent(
    name="BuildPromptAgent",
    model=DISPATCH_MODEL,
    description="Step 6 — assemble L0 (Sonnet) + L3 (verbatim) + L2 (verbatim).",
    instruction=(
        "Step 6 of 9. Read sku from state['sku'] and view from the original user input. "
        "Call build_prompt_fn with sku and view. The function reads state['layer0_directives'] "
        "(written by Sonnet in step 5), prepends the canonical dossier positives (Layer 3 — "
        "verbatim from dossier.garment_type_lock + dossier.branding_block), and appends the "
        "canonical negatives (Layer 2 — verbatim from dossier.negative_block). Output the "
        "total prompt char count + per-layer breakdown."
    ),
    tools=[build_prompt_tool],
)

generate_image_agent = LlmAgent(
    name="GenerateImageAgent",
    model=DISPATCH_MODEL,
    description="Step 7 — render via the routed engine (PAID).",
    instruction=(
        "Step 7 of 9. PAID API CALL. Read sku and view. Call generate_image_fn with sku "
        "and view. The function reads state['engine'], state['model_id'], state['prompt'], "
        "state['source_path'] and dispatches to the correct provider (Gemini NB Pro / "
        "GPT-image-1.5 / FLUX-pro-v1.1). Output the engine used and bytes_size."
    ),
    tools=[generate_image_tool],
)

# Refinement loop sub-agents
qa_tournament_agent = LlmAgent(
    name="QaTournamentAgent",
    model=DISPATCH_MODEL,
    description="Step 8a (loop) — 3-judge QA tournament with learning-loop recording.",
    instruction=(
        "PAID API CALLS. Read sku from state['sku']. Call qa_tournament_fn with that sku. "
        "The function runs GPT-5.5-pro + Gemini-3.1-pro-preview vision judges in parallel, "
        "then Claude Opus 4.7 synthesis judge over their reports. Records to learning Loops "
        "1, 2, 3. Output the aggregate score, hallucination_veto, and any infra_failures."
    ),
    tools=[qa_tournament_tool],
)

score_reasoner_agent = LlmAgent(
    name="ScoreReasonerAgent",
    model=GEMINI_REASONING,
    description="Step 8b (loop) — F5-aware decision: pass / refine / abort.",
    instruction=(
        "Read state['qa_score'], state['hallucination_veto'], and state['infra_failures']. "
        "Output exactly ONE word — your decision:\n\n"
        "  'pass'   if qa_score >= 80 AND hallucination_veto is False AND infra_failures is empty\n"
        "  'abort'  if len(infra_failures) >= 2 (the F5 fragility case — multiple judge timeouts "
        "mean the score is unreliable; refining won't help, escalate to human review)\n"
        "  'refine' otherwise (real quality issue we can try to fix)\n\n"
        "Edge cases:\n"
        "  - hallucination_veto=True with score>=80: still 'refine' (luxury veto disqualifies)\n"
        "  - 1 infra_failure with passable score: 'pass' (single judge timeout, vision-pair-mean is enough)\n"
        "  - score < 50 with no veto: 'refine' (try Kontext correction)\n\n"
        "Output JUST the single word. No explanation, no JSON."
    ),
    output_key="loop_decision",
)

refine_image_agent = LlmAgent(
    name="RefineImageAgent",
    model=DISPATCH_MODEL,
    description="Step 8d (loop) — refine via Kontext or Gemini composite (PAID).",
    instruction=(
        "PAID API CALL. This step only runs if state['loop_decision'] == 'refine' "
        "(StopChecker before this step would have escalated for pass/abort). Read sku from "
        "state['sku']. Call refine_image_fn with sku. Output the engine used (kontext / "
        "gemini-composite / failed)."
    ),
    tools=[refine_image_tool],
)

refinement_loop = LoopAgent(
    name="QAAndRefineLoop",
    max_iterations=2,  # initial judge + at most 1 refine + re-judge
    sub_agents=[
        qa_tournament_agent,
        score_reasoner_agent,
        StopChecker(name="StopChecker"),
        refine_image_agent,
    ],
)

# Step 9 — Opus synthesizes the final RenderResult
synthesis_agent = LlmAgent(
    name="SynthesisAgent",
    model=OPUS_SYNTHESIS,
    description="Step 9 — Opus 4.7 produces the structured RenderResult.",
    instruction=(
        "Read the full session state and emit a structured RenderResult JSON.\n\n"
        "Required field derivation:\n"
        "  - sku, view: from original input\n"
        "  - output_path: state['candidate_path']\n"
        "  - qa_score: state['qa_score']\n"
        "  - qa_passed: state['qa_passed']\n"
        "  - engine_used: state['generation_engine']\n"
        "  - refinement_applied: state.get('refinement_applied', False)\n"
        "  - refinement_engine: state.get('refinement_engine', '')\n"
        "  - cost_usd: state['estimated_cost_usd'] (+ 0.04 if refinement applied)\n"
        "  - hallucination_veto: state['hallucination_veto']\n"
        "  - issues: state['top_issues']\n"
        "  - infra_failures: state['infra_failures']\n\n"
        "Status logic (final_status):\n"
        "  - 'shipped'        : qa_passed AND qa_score >= 80 AND not hallucination_veto\n"
        "  - 'needs_review'   : qa_score in [50, 80) with no veto and no infra failures\n"
        "  - 'failed_quality' : qa_score < 50 OR hallucination_veto fired\n"
        "  - 'failed_infra'   : len(infra_failures) >= 2 (F5 case)\n\n"
        "Rationale: 1-2 sentences. State the score, the engine choice (note if catalog "
        "override applied), refinement outcome, and any qualifications about infra reliability."
    ),
    output_schema=RenderResult,
    output_key="render_result",
)

# ---------------------------------------------------------------------------
# Root SequentialAgent — the framework dispatches sub-agents in order
# ---------------------------------------------------------------------------

root_agent = SequentialAgent(
    name="RenderPipeline",
    description=(
        "Generate a validated, scored product render for a SkyyRose SKU. "
        "9-step pipeline with dual-vision consensus, catalog-pinned engine routing, "
        "Sonnet-articulated rendering directives, 3-judge QA tournament, and "
        "iterative refinement up to 2 cycles. Final output is a Pydantic RenderResult "
        "synthesized by Opus 4.7."
    ),
    sub_agents=[
        load_dossier_agent,
        resolve_source_agent,
        vision_consensus_agent,
        route_engine_agent,
        articulate_layer0_agent,
        build_prompt_agent,
        generate_image_agent,
        refinement_loop,
        synthesis_agent,
    ],
)


__all__ = ["root_agent", "RenderResult", "StopChecker"]
