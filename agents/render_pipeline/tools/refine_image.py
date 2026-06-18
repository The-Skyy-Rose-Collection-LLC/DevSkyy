"""Tool 7: Refine the candidate using synthesis-aware corrections. PAID API CALL.

Refinement strategy mirrors `pipeline._build_refinement_prompt`:
    Tier 1 (preferred) — Opus synthesis judge produced consensus-filtered
                         issues + suggested_fixes. Hallucination veto, when
                         set, prepends a hard CRITICAL constraint.
    Tier 2 (fallback)  — synthesis missing/failed; use vision-pair union.
    Tier 3 (catchall)  — no fix data; generic correction prompt.

Engine selection:
    1. FLUX Kontext Pro (reference-guided editing — preserves composition)
    2. Gemini composite (fallback when Kontext unavailable or fails)

State writes (and re-reads qa_score after re-running implicitly via
the agent's instruction to re-call qa_tournament_fn after refine):
    refinement_applied, refinement_engine
"""

from __future__ import annotations

import logging
from pathlib import Path

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

log = logging.getLogger(__name__)

from google.adk.tools.tool_context import ToolContext


def _build_refine_prompt(
    name: str,
    sku: str,
    score: float,
    veto: bool,
    issues: list[str],
    fixes: list[str],
) -> str:
    """Three-tier prompt builder mirroring pipeline._build_refinement_prompt."""
    parts = [
        f"This is a {name} ({sku}) product render that scored "
        f"{score:.0f}/100 in QA review and needs correction."
    ]

    if veto:
        parts.append(
            "CRITICAL: This render contains hallucinated decorative elements "
            "not in the spec. These must be completely removed. Do not "
            "introduce any new decorations, motifs, logos, text, or details "
            "that are not explicitly listed in the corrections below."
        )

    if issues:
        issues_block = "\n".join(f"  - {i}" for i in issues[:5])
        parts.append(f"DEFECTS PRESENT IN CURRENT RENDER:\n{issues_block}")

    if fixes:
        fixes_block = "\n".join(f"  - {f}" for f in fixes[:5])
        parts.append(f"REQUIRED CORRECTIONS:\n{fixes_block}")
    elif not issues:
        # Tier 3 catchall when both empty
        parts.append(
            f"Fix the text and logo accuracy on this {name}. "
            "Make all branding crisp and legible. Keep everything else identical."
        )

    parts.append(
        "Apply these corrections precisely. Preserve all unrelated elements "
        "unchanged. Do not add any decorations, text, logos, or details "
        "beyond what is explicitly required."
    )

    return "\n\n".join(parts)


def refine_image_fn(sku: str, tool_context: ToolContext) -> dict:
    """Refine via Kontext first, Gemini composite as fallback.

    Reads state: candidate_path, source_path, qa_score, hallucination_veto,
                 top_issues, all_fixes, product_name
    Writes state: refinement_applied, refinement_engine

    Returns dict with refined (bool), engine_used, candidate_path
    (overwritten in place — same file as before refinement). The agent
    is instructed to re-call qa_tournament_fn after refinement to update
    qa_score with the post-refine value.
    """
    from nano_banana.client import get_genai_client
    from nano_banana.engine_fal import refine_with_kontext
    from nano_banana.generate import composite_gemini
    from nano_banana.utils import save_image

    candidate_path_str = tool_context.state.get("candidate_path", "")
    source_path_str = tool_context.state.get("source_path", "")
    if not candidate_path_str:
        return {
            "refined": False,
            "error": "no candidate_path in state — generate_image must run first",
        }

    candidate_path = Path(candidate_path_str)
    source_path = Path(source_path_str) if source_path_str else None

    score = float(tool_context.state.get("qa_score", 0.0))
    veto = bool(tool_context.state.get("hallucination_veto", False))
    issues = list(tool_context.state.get("top_issues", []))
    fixes = list(tool_context.state.get("all_fixes", []))
    name = tool_context.state.get("product_name", "garment")

    refine_prompt = _build_refine_prompt(name, sku, score, veto, issues, fixes)
    log.info("refine_image_fn: %s refine prompt (%d chars)", sku, len(refine_prompt))

    # Tier 1 — FLUX Kontext Pro
    refined_bytes = None
    used_engine = ""
    try:
        refined_bytes = refine_with_kontext(candidate_path, refine_prompt)
        if refined_bytes:
            used_engine = "flux-kontext"
    except Exception as exc:
        log.warning("refine_image_fn: kontext failed (%s) — falling back to gemini composite", exc)

    # Tier 2 — Gemini composite fallback
    if not refined_bytes and source_path and source_path.exists():
        try:
            client = get_genai_client()
            refined_bytes = composite_gemini(client, candidate_path, source_path, refine_prompt)
            if refined_bytes:
                used_engine = "gemini-composite"
        except Exception as exc:
            log.warning("refine_image_fn: gemini composite failed: %s", exc)

    if not refined_bytes:
        return {
            "refined": False,
            "error": "all refinement engines failed (kontext + gemini composite)",
        }

    # Overwrite in place — keeps the same path so qa_tournament_fn re-runs
    # against the updated bytes without state path changes.
    save_image(refined_bytes, candidate_path)

    tool_context.state["refinement_applied"] = True
    tool_context.state["refinement_engine"] = used_engine

    return {
        "refined": True,
        "engine_used": used_engine,
        "candidate_path": str(candidate_path),
        "bytes_size": len(refined_bytes),
    }
