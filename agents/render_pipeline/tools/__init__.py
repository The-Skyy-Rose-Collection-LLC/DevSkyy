"""ADK FunctionTool wrappers for the RenderPipeline 9-step workflow.

Each module exports a pure-Python function (suffix `_fn`). The agent
wraps them with `FunctionTool(...)` in `agents.render_pipeline.agent`.
The functions are testable without google-adk installed (ToolContext is
a forward-ref via TYPE_CHECKING).

The 9-tool deterministic chain (after the dual-vision + Sonnet-L0 upgrades):
    load_dossier → resolve_source → vision_consensus → route_engine
                 → articulate_layer0 → build_prompt
                 → generate_image → qa_tournament → (refine_image)

State keys written by each tool (read by downstream tools):
    load_dossier      : sku, product_name, collection, engine_override?
    resolve_source    : source_path
    vision_consensus  : vision_consensus (dict — merged Gemini + OpenAI)
    route_engine      : engine, model_id, estimated_cost_usd
    articulate_layer0 : layer0_directives (Sonnet 4.6's output)
    build_prompt      : prompt (full assembled), template_id
    generate_image    : candidate_path, bytes_size, generation_engine
    qa_tournament     : qa_score, qa_passed, hallucination_veto, top_issues,
                        all_fixes, infra_failures, should_refine
    refine_image      : refinement_applied, refinement_engine
"""

from agents.render_pipeline.tools.articulate_layer0 import articulate_layer0_fn
from agents.render_pipeline.tools.build_prompt import build_prompt_fn
from agents.render_pipeline.tools.generate_image import generate_image_fn
from agents.render_pipeline.tools.load_dossier import load_dossier_fn
from agents.render_pipeline.tools.qa_tournament import qa_tournament_fn
from agents.render_pipeline.tools.refine_image import refine_image_fn
from agents.render_pipeline.tools.resolve_source import resolve_source_fn
from agents.render_pipeline.tools.route_engine import route_engine_fn
from agents.render_pipeline.tools.vision_consensus import vision_consensus_fn

__all__ = [
    "load_dossier_fn",
    "resolve_source_fn",
    "vision_consensus_fn",
    "route_engine_fn",
    "articulate_layer0_fn",
    "build_prompt_fn",
    "generate_image_fn",
    "qa_tournament_fn",
    "refine_image_fn",
]
