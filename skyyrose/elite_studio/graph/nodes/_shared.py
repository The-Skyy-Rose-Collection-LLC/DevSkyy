"""
Shared infrastructure for Elite Studio graph nodes.

Contains: run_sync helper, cost-tracking helper, ADK render engine glue,
token-estimate constants, cost-ceiling constants, and the classifier
confidence threshold.  Imported by layer1, layer2, and ghost_mannequin;
never imported directly by callers outside the nodes package.
"""

from __future__ import annotations

import asyncio
import logging
import time  # noqa: F401 — re-exported for node modules that do `from ._shared import time`

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Async bridge
# ---------------------------------------------------------------------------


def run_sync(coro):
    """Run a coroutine from a synchronous node.

    Requires a real awaitable — passing a plain value raises ``TypeError``
    so that async/sync mismatches surface as test failures rather than being
    silently swallowed.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Token estimates (approximate, used for cost tracking)
# ---------------------------------------------------------------------------

_VISION_TOKENS_ESTIMATE = 2_000  # dual-provider: Gemini + OpenAI
_GENERATION_TOKENS_ESTIMATE = 1_500  # Gemini image generation prompt
_QC_TOKENS_ESTIMATE = 1_000  # Claude Sonnet QC call
_COMPOSITOR_TOKENS_ESTIMATE = 800  # Gemini QA gate

# Classifier confidence threshold — below this the LLM QC runs as well
_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.8

# ---------------------------------------------------------------------------
# Cost ceiling constants (USD, per-stage worst-case estimates)
# ---------------------------------------------------------------------------

_GENERATOR_EST_COST_USD = (
    0.04  # Gemini Flash ~$0.04/image — see render_pipeline/tools/generate_image.py
)
# Per-view ceiling for the ADK render_pipeline (Layer 2):
# gen (NB Pro) $0.04 + L0 Sonnet $0.005 + dual-vision $0.01 + tournament $0.10
# + max 1 refine retry $0.04 + synthesis $0.005 = ~$0.20.
_ADK_RENDER_EST_COST_USD = 0.20
_THREE_D_EST_COST_USD = 0.50  # Round-table ceiling: Meshy + Tripo + TRELLIS_local worst case
# 6-stage compositor: BRIA RMBG + IC-Light + FLUX Fill + PIL shadow + Gemini QA ~$0.115/render
_COMPOSITOR_EST_COST_USD = 0.115
# FASHN virtual try-on: single-garment inference ~$0.075/call
_TRYON_EST_COST_USD = 0.075


# ---------------------------------------------------------------------------
# Cost recording helper
# ---------------------------------------------------------------------------


def _record_cost(job_id: str | None, provider: str, tokens: int) -> None:
    """Record estimated API cost for a node call. No-ops if job_id is None."""
    if not job_id:
        return
    try:
        from ...config import COST_TRACKING_ENABLED
        from ...queue.cost_tracker import PRICING_PER_1K, CostTracker

        if not COST_TRACKING_ENABLED:
            return
        cost_usd = PRICING_PER_1K.get(provider, 0.0) * tokens / 1000
        CostTracker().record(job_id=job_id, provider=provider, tokens=tokens, cost_usd=cost_usd)
    except Exception as exc:
        logger.debug("Cost tracking skipped: %s", exc)


# ---------------------------------------------------------------------------
# ADK render engine glue
# ---------------------------------------------------------------------------


def _invoke_adk_render_engine(sku: str, view: str):
    """Invoke the ADK render_pipeline root_agent and wrap the result.

    Returns a ``GenerationResult`` (imported lazily inside the function body so
    this module stays importable without the google-adk dependency at top).

    P7: lets generator_node dispatch into Layer 2 (the 9-step ADK pipeline) when
    state["engine"] == "adk-render". Returns a GenerationResult in the same shape
    GeneratorAgent emits so downstream nodes (quality_node, etc.) see a uniform
    contract.

    The ADK pipeline runs its own QA tournament + refine loop internally; we
    pass its `qa_score`, `qa_passed`, and `cost_usd` through `metadata` so the
    Elite Studio quality_node can short-circuit if the ADK pass already cleared
    the bar.
    """
    import asyncio
    import json
    import time as _time

    from ...models import GenerationResult

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as genai_types
    except ImportError as exc:
        return GenerationResult(
            success=False,
            provider="adk-render",
            error=f"google-adk not installed in runtime env: {exc}",
        )

    try:
        from agents.render_pipeline.agent import root_agent
    except ImportError as exc:
        return GenerationResult(
            success=False,
            provider="adk-render",
            error=f"render_pipeline.agent import failed: {exc}",
        )

    async def _run() -> dict:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="elite_studio_render_pipeline",
            session_service=session_service,
        )
        user_id = "elite_studio"
        session_id = f"elite-{sku}-{view}-{int(_time.time())}"
        await session_service.create_session(
            app_name="elite_studio_render_pipeline",
            user_id=user_id,
            session_id=session_id,
        )
        user_input = json.dumps({"sku": sku, "view": view})
        new_message = genai_types.Content(role="user", parts=[genai_types.Part(text=user_input)])
        async for _event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            pass
        session = await session_service.get_session(
            app_name="elite_studio_render_pipeline",
            user_id=user_id,
            session_id=session_id,
        )
        return dict(session.state) if session else {}

    try:
        state_dict = asyncio.run(_run())
    except Exception as exc:
        return GenerationResult(
            success=False,
            provider="adk-render",
            error=f"ADK runner failed: {type(exc).__name__}: {exc}",
        )

    render_result = state_dict.get("render_result") or {}
    output_path = render_result.get("output_path") or state_dict.get("candidate_path") or ""
    qa_score = float(render_result.get("qa_score", 0.0))
    qa_passed = bool(render_result.get("qa_passed", False))
    cost_usd = float(render_result.get("cost_usd", state_dict.get("estimated_cost_usd", 0.0)))
    engine_used = render_result.get("engine") or state_dict.get("engine", "")
    model_id = render_result.get("model_id") or state_dict.get("model_id", "")

    if not output_path:
        return GenerationResult(
            success=False,
            provider="adk-render",
            model=str(model_id),
            error="ADK pipeline returned no output_path",
            metadata={
                "engine": engine_used,
                "qa_score": qa_score,
                "qa_passed": qa_passed,
                "cost_usd": cost_usd,
                "render_result": render_result,
            },
        )

    return GenerationResult(
        success=True,
        provider="adk-render",
        model=str(model_id),
        output_path=str(output_path),
        metadata={
            "engine": engine_used,
            "qa_score": qa_score,
            "qa_passed": qa_passed,
            "cost_usd": cost_usd,
            "render_result": render_result,
        },
    )
