"""
Graph node functions — thin wrappers around existing agents.

Each node reads from EliteStudioState, calls the corresponding agent,
and returns an updated state dict. LangGraph merges the returned dict
into the shared state automatically.

Agent instances are created once via module-level factories and reused
across invocations. Nodes are intentionally synchronous — the agents
themselves are synchronous (REST calls with retry).

Layer 4 additions:
- quality_node now runs ML classifier first; falls back to Claude Sonnet
  only when classifier confidence is below threshold.
- human_review_node submits to HumanReviewGate and polls for decision.
"""

from __future__ import annotations

import asyncio
import logging
import time

from ..agents.color_correction_agent import ColorCorrectionAgent
from ..agents.compositor_agent import CompositorAgent
from ..agents.generator_agent import GeneratorAgent
from ..agents.prompt_enrichment_agent import PromptEnrichmentAgent
from ..agents.quality_agent import QualityAgent
from ..agents.safety_agent import SafetyAgent
from ..agents.tryon_agent import TryOnAgent, _find_garment_image
from ..agents.upscaling_agent import UpscalingAgent
from ..agents.variant_agent import VariantAgent
from ..agents.vision_agent import VisionAgent
from ..quality.human_review import HumanReviewGate
from ..quality.ml_classifier import QualityClassifier
from .state import EliteStudioState

logger = logging.getLogger(__name__)

# Lazy import guard so nodes remain testable without prometheus_client installed.
try:
    from monitoring.elite_studio_metrics import record_stage_duration as _record_stage_duration
except ImportError:  # pragma: no cover

    def _record_stage_duration(stage: str, duration_s: float) -> None:  # type: ignore[misc]
        pass


logger = logging.getLogger(__name__)


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


# Approximate token estimates per node call (used for cost tracking).
_VISION_TOKENS_ESTIMATE = 2_000  # dual-provider: Gemini + OpenAI
_GENERATION_TOKENS_ESTIMATE = 1_500  # Gemini image generation prompt
_QC_TOKENS_ESTIMATE = 1_000  # Claude Sonnet QC call
_COMPOSITOR_TOKENS_ESTIMATE = 800  # Gemini QA gate

# Classifier confidence threshold — below this the LLM QC runs as well
_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.8


def _record_cost(job_id: str | None, provider: str, tokens: int) -> None:
    """Record estimated API cost for a node call. No-ops if job_id is None."""
    if not job_id:
        return
    try:
        from ..config import COST_TRACKING_ENABLED
        from ..queue.cost_tracker import PRICING_PER_1K, CostTracker

        if not COST_TRACKING_ENABLED:
            return
        cost_usd = PRICING_PER_1K.get(provider, 0.0) * tokens / 1000
        CostTracker().record(job_id=job_id, provider=provider, tokens=tokens, cost_usd=cost_usd)
    except Exception as exc:
        logger.debug("Cost tracking skipped: %s", exc)


def vision_node(state: EliteStudioState) -> dict:
    """Analyze product images via dual-provider vision (Gemini + OpenAI)."""
    start = time.monotonic()
    agent = VisionAgent()
    result = run_sync(agent.analyze(state["sku"], state["view"]))
    elapsed = time.monotonic() - start

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "gemini", _VISION_TOKENS_ESTIMATE // 2)
    _record_cost(job_id, "openai", _VISION_TOKENS_ESTIMATE // 2)

    timings = dict(state.get("stage_timings", {}))
    timings["vision"] = round(elapsed, 2)
    _record_stage_duration("vision", elapsed)

    if not result.success:
        return {
            "vision_result": result,
            "status": "error",
            "error": result.error,
            "failed_step": "vision",
            "stage_timings": timings,
        }

    return {
        "vision_result": result,
        "stage_timings": timings,
    }


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

    from ..models import GenerationResult

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


def generator_node(state: EliteStudioState) -> dict:
    """Generate fashion model image from vision specification.

    Branches on state["engine"]:
        "legacy"     → GeneratorAgent (default)
        "adk-render" → ADK render_pipeline root_agent (P7)
    """
    from ..budget import BudgetExceededError

    start = time.monotonic()

    engine_selector = state.get("engine", "legacy")
    vision = state.get("vision_result")

    # Legacy path requires a vision_result; ADK path can run without one
    # because the ADK pipeline does its own dossier-driven prompting.
    if engine_selector == "legacy" and (not vision or not vision.success):
        return {
            "status": "error",
            "error": "No vision result available for generation",
            "failed_step": "generation",
        }

    # ADK pipeline runs its own QA + refine loop internally; the cost ceiling
    # there is ~$0.20/view (gen+QA+refine), markedly higher than the legacy
    # $0.04/image estimate. Use the higher number for the budget pre-check
    # when the ADK engine is selected.
    est_cost = (
        _ADK_RENDER_EST_COST_USD if engine_selector == "adk-render" else _GENERATOR_EST_COST_USD
    )

    budget = state.get("budget")
    if budget is not None and hasattr(budget, "ensure_within_budget"):
        try:
            budget.ensure_within_budget(est_cost, stage="generation")
        except BudgetExceededError as exc:
            return {
                "status": "error",
                "error": f"budget exceeded before generation: {exc}",
                "failed_step": "generation",
            }

    if engine_selector == "adk-render":
        result = _invoke_adk_render_engine(state["sku"], state["view"])
    else:
        agent = GeneratorAgent()
        result = run_sync(
            agent.generate(
                sku=state["sku"],
                view=state["view"],
                generation_spec=vision.unified_spec,
            )
        )
    elapsed = time.monotonic() - start

    if budget is not None and hasattr(budget, "spend") and getattr(result, "success", False):
        # For the ADK engine prefer the per-run actual cost reported back; fall
        # back to the est_cost so we never under-account.
        actual_cost = est_cost
        if engine_selector == "adk-render":
            reported = getattr(result, "metadata", {}).get("cost_usd")
            if isinstance(reported, (int, float)) and reported > 0:
                actual_cost = float(reported)
        budget.spend(actual_cost, stage="generation")

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "gemini", _GENERATION_TOKENS_ESTIMATE)

    timings = dict(state.get("stage_timings", {}))
    timings["generation"] = round(elapsed, 2)
    _record_stage_duration("generation", elapsed)

    if not result.success:
        return {
            "generation_result": result,
            "status": "error",
            "error": result.error,
            "failed_step": "generation",
            "stage_timings": timings,
        }

    return {
        "generation_result": result,
        "stage_timings": timings,
    }


def quality_node(state: EliteStudioState) -> dict:
    """Dual-QC: ML classifier first, Claude Sonnet fallback on low confidence.

    Phase 16 Upgrade: Inspects audit_result from FLUX synthesis first. If
    blocking violations exist, fails immediately without calling ML/LLM.
    """
    start = time.monotonic()

    gen = state.get("generation_result")
    vision = state.get("vision_result")
    if not gen or not gen.success or not vision:
        return {
            "status": "error",
            "error": "No generated image available for QC",
            "failed_step": "quality",
        }

    # --- Stage 0: Fidelity Audit check (Phase 16) ---
    audit_data = gen.metadata.get("audit_result")
    if audit_data:
        from ..agents.vision_audit_agent import VisionAuditResult, VisionAuditViolation

        # Reconstruct violations first
        violation_dicts = audit_data.get("violations", [])
        violations_objs = [VisionAuditViolation(**v) for v in violation_dicts]

        # Reconstruct result object
        audit = VisionAuditResult(
            matches_dossier=bool(audit_data.get("matches_dossier", False)),
            violations=violations_objs,
            raw_text=audit_data.get("raw_text", ""),
            model=audit_data.get("model", ""),
            error=audit_data.get("error", ""),
        )

        if not audit.ok:
            logger.info("[QC] Fidelity audit failed (blocking violations found)")
            from ..models import QualityVerification

            violations = [v.element for v in audit.violations if v.is_blocking]
            quality_result = QualityVerification(
                success=True,
                provider="fidelity_audit",
                model=audit.model,
                overall_status="fail",
                recommendation="regenerate",
                details={
                    "violations": [v.to_dict() for v in audit.violations],
                    "blocking_elements": violations,
                    "reason": "fidelity audit failed",
                },
            )
            elapsed = time.monotonic() - start
            timings = dict(state.get("stage_timings", {}))
            timings["quality"] = round(elapsed, 2)
            return {
                "quality_result": quality_result,
                "stage_timings": timings,
            }

    # --- Stage 1: ML classifier ---
    classifier = QualityClassifier()
    classifier_result = classifier.predict(gen.output_path)
    logger.info(
        "[QC] classifier: sku=%s score=%.3f confidence=%.3f label=%s",
        state["sku"],
        classifier_result.score,
        classifier_result.confidence,
        classifier_result.label,
    )

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "anthropic", _QC_TOKENS_ESTIMATE)

    timings = dict(state.get("stage_timings", {}))

    # --- Stage 2: LLM QC (only when classifier is uncertain) ---
    quality_result = None
    if classifier_result.confidence >= _CLASSIFIER_CONFIDENCE_THRESHOLD:
        logger.info(
            "[QC] High-confidence classifier result — skipping LLM QC (confidence=%.3f)",
            classifier_result.confidence,
        )
        # Synthesise a QualityVerification from classifier result alone
        from ..models import QualityVerification

        passed = classifier_result.score >= 0.7
        quality_result = QualityVerification(
            success=True,
            provider="clip",
            model="openai/clip-vit-base-patch32",
            overall_status="pass" if passed else "fail",
            recommendation="approve" if passed else "regenerate",
            details={
                "classifier_score": classifier_result.score,
                "classifier_confidence": classifier_result.confidence,
                "classifier_label": classifier_result.label,
                "source": "ml_classifier",
            },
        )
    else:
        logger.info(
            "[QC] Low classifier confidence (%.3f) — running Claude Sonnet QC",
            classifier_result.confidence,
        )
        llm_agent = QualityAgent()
        quality_result = run_sync(
            llm_agent.verify(
                image_path=gen.output_path,
                expected_spec=vision.unified_spec,
            )
        )

    elapsed = time.monotonic() - start
    timings["quality"] = round(elapsed, 2)
    _record_stage_duration("quality", elapsed)

    return {
        "quality_result": quality_result,
        "classifier_result": classifier_result,
        "stage_timings": timings,
    }


def human_review_node(state: EliteStudioState) -> dict:
    """Submit generated image to HumanReviewGate and wait for decision.

    On timeout or queue unavailability, defaults to approve so production
    is never blocked indefinitely.

    The review decision is stored in human_review_result. If the reviewer
    rejects the image, quality_result.recommendation is set to "regenerate"
    so the after_quality_v2 edge can trigger a retry.
    """
    start = time.monotonic()

    gen = state.get("generation_result")
    if not gen or not gen.success:
        return {
            "status": "error",
            "error": "No generated image to submit for human review",
            "failed_step": "human_review",
        }

    gate = HumanReviewGate()
    sku = state["sku"]
    job_id = state.get("workflow_id", sku)

    review_id = gate.submit_for_review(sku=sku, image_path=gen.output_path, job_id=job_id)
    decision = gate.get_decision(review_id)

    logger.info(
        "[HumanReview] sku=%s decision=%s reviewer=%s",
        sku,
        decision.decision,
        decision.reviewer,
    )

    elapsed = time.monotonic() - start
    timings = dict(state.get("stage_timings", {}))
    timings["human_review"] = round(elapsed, 2)

    # If reviewer rejected: override quality recommendation to trigger regeneration
    if decision.decision == "reject":
        existing_qc = state.get("quality_result")
        if existing_qc:
            from ..models import QualityVerification

            updated_qc = QualityVerification(
                success=existing_qc.success,
                provider=existing_qc.provider,
                model=existing_qc.model,
                overall_status="fail",
                recommendation="regenerate",
                details={**existing_qc.details, "human_rejected": True, "notes": decision.notes},
                error=existing_qc.error,
            )
            return {
                "human_review_result": decision,
                "quality_result": updated_qc,
                "stage_timings": timings,
            }

    return {
        "human_review_result": decision,
        "stage_timings": timings,
    }


def compositor_node(state: EliteStudioState) -> dict:  # noqa: C901
    """Composite generated model into scene backgrounds."""
    from ..budget import BudgetExceededError

    start = time.monotonic()

    gen = state.get("generation_result")
    if not gen or not gen.success:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["compositing"] = round(elapsed, 2)
        return {
            "compositor_result": None,
            "stage_timings": timings,
        }

    # Budget guard — 6-stage compositor dispatches Gemini, IC-Light, and FLUX;
    # pre-check before any provider fires.
    budget = state.get("budget")
    if budget is not None and hasattr(budget, "ensure_within_budget"):
        try:
            budget.ensure_within_budget(_COMPOSITOR_EST_COST_USD, stage="compositing")
        except BudgetExceededError as exc:
            return {
                "status": "error",
                "error": f"budget exceeded before compositing: {exc}",
                "failed_step": "compositing",
            }

    agent = CompositorAgent()
    comp_result = None

    try:
        from ..agents.compositor_agent import SCENE_LOOKBOOK
        from ..utils import discover_scene_images

        for scene_name, sku_prefix in SCENE_LOOKBOOK.items():
            if state["sku"].startswith(sku_prefix):
                collection = (
                    scene_name.rsplit("-", 2)[0] if scene_name.count("-") > 2 else scene_name
                )
                scenes = discover_scene_images(collection)
                if scenes:
                    # composite() is sync since the Phase B2 rewrite — no
                    # run_sync wrapper needed. The model image is the B1
                    # generator output; the scene image is the first scene
                    # discovered for the collection.
                    comp_result = agent.composite(
                        sku=state["sku"],
                        scene_image_path=str(scenes[0]),
                        model_image_path=gen.output_path,
                        scene_name=scene_name,
                        collection=collection,
                    )
                break
    except Exception:
        # Don't crash the graph if compositing breaks — but DO surface the
        # failure. Bare ``pass`` here previously masked real provider errors
        # and made the compositor stage look like a no-op when it had failed.
        logger.exception("compositor_node: composite() raised for sku=%s", state.get("sku"))

    elapsed = time.monotonic() - start

    if comp_result and comp_result.success:
        job_id: str | None = state.get("job_id")  # type: ignore[assignment]
        _record_cost(job_id, "gemini", _COMPOSITOR_TOKENS_ESTIMATE)
        if budget is not None and hasattr(budget, "spend"):
            budget.spend(_COMPOSITOR_EST_COST_USD, stage="compositing")

    timings = dict(state.get("stage_timings", {}))
    timings["compositing"] = round(elapsed, 2)
    _record_stage_duration("compositing", elapsed)

    return {
        "compositor_result": comp_result,
        "stage_timings": timings,
    }


def tryon_node(state: EliteStudioState) -> dict:
    """Run virtual try-on in parallel with compositor (additive — never fails the job).

    Skips silently when:
    - generation_result is absent or unsuccessful
    - no garment image can be found for the SKU
    - budget ceiling would be exceeded
    """
    from ..budget import BudgetExceededError

    start = time.monotonic()
    timings = dict(state.get("stage_timings", {}))

    gen = state.get("generation_result")
    if not gen or not gen.success:
        logger.debug("tryon_node: skipping — no successful generation result")
        timings["tryon"] = round(time.monotonic() - start, 2)
        return {"tryon_result": None, "stage_timings": timings}

    sku = state["sku"]
    garment_path = _find_garment_image(sku)
    if not garment_path:
        logger.debug("tryon_node: skipping — no garment image found for %s", sku)
        timings["tryon"] = round(time.monotonic() - start, 2)
        return {"tryon_result": None, "stage_timings": timings}

    # Budget guard — FASHN tryon incurs real per-call cost; check ceiling before dispatch.
    budget = state.get("budget")
    if budget is not None and hasattr(budget, "ensure_within_budget"):
        try:
            budget.ensure_within_budget(_TRYON_EST_COST_USD, stage="tryon")
        except BudgetExceededError as exc:
            logger.warning("tryon_node: skipping — %s", exc)
            timings["tryon"] = round(time.monotonic() - start, 2)
            return {"tryon_result": None, "stage_timings": timings}

    category = state.get("tryon_category", "upper_body")
    agent = TryOnAgent()
    result = run_sync(
        agent.execute_tryon(
            garment_image_path=garment_path,
            model_image_path=gen.output_path,
            category=category,
            garment_sku=sku,
        )
    )

    if budget is not None and hasattr(budget, "spend") and getattr(result, "success", False):
        budget.spend(_TRYON_EST_COST_USD, stage="tryon")

    timings["tryon"] = round(time.monotonic() - start, 2)
    return {"tryon_result": result, "stage_timings": timings}


def finalize_node(state: EliteStudioState) -> dict:
    """Set final status + persist the run summary for downstream auditing.

    Always emits a summary JSON — success or error — so post-run analysis
    can reconstruct what each SKU's pipeline did, what it spent, and
    where it failed. Telemetry write is best-effort: a failed write
    never overrides the run status.
    """
    from ..telemetry import write_run_summary

    final_status = "success" if state.get("status") != "error" else "error"

    budget = state.get("budget")
    budget_snap = budget.snapshot() if budget is not None and hasattr(budget, "snapshot") else None

    qa = state.get("quality_result")
    gen = state.get("generation_result")
    three_d_score = state.get("three_d_fidelity_score") or 0.0

    summary = {
        "workflow_id": state.get("workflow_id"),
        "sku": state.get("sku"),
        "view": state.get("view"),
        "style": state.get("style"),
        "status": final_status,
        "error": state.get("error", ""),
        "failed_step": state.get("failed_step", ""),
        "generation_engine": getattr(gen, "provider", None) or getattr(gen, "model", None),
        "qa_score": getattr(qa, "score", None) if qa else None,
        "qa_passed": getattr(qa, "passed", None) if qa else None,
        "three_d_fidelity_score": three_d_score,
        "three_d_model_path": state.get("three_d_model_path", ""),
        "budget": budget_snap,
        "stage_timings": dict(state.get("stage_timings", {}) or {}),
    }

    workflow_id = state.get("workflow_id") or "unknown"
    summary_path = write_run_summary(workflow_id, summary)

    out: dict = {"status": final_status}
    if summary_path is not None:
        out["run_summary_path"] = str(summary_path)
    return out


# ---------------------------------------------------------------------------
# Layer 2 nodes — optional pipeline stages
# ---------------------------------------------------------------------------


def prompt_enrichment_node(state: EliteStudioState) -> dict:
    """Enrich vision spec with brand/collection DNA and style modifiers."""
    start = time.monotonic()
    agent = PromptEnrichmentAgent()

    vision = state.get("vision_result")
    spec = vision.unified_spec if vision and vision.success else ""

    # PromptEnrichmentAgent.enrich is synchronous (returns EnrichedPrompt directly).
    # Calling run_sync on a non-awaitable raises TypeError.
    result = agent.enrich(sku=state["sku"], vision_spec=spec, style=state.get("style", "flat_lay"))
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["prompt_enrichment"] = round(elapsed, 2)

    update: dict = {
        "enriched_prompt": result,
        "stage_timings": timings,
    }

    # When enrichment succeeds, propagate the enriched spec back into the
    # vision_result's unified_spec so downstream nodes use it.
    if result.success and vision and result.enriched_spec:
        from ..models import SynthesizedVision

        enriched_vision = SynthesizedVision(
            success=vision.success,
            unified_spec=result.enriched_spec,
            providers_used=vision.providers_used,
            individual_results=vision.individual_results,
            error=vision.error,
        )
        update["vision_result"] = enriched_vision

    return update


def upscaling_node(state: EliteStudioState) -> dict:
    """Upscale the current output image via Real-ESRGAN or PIL LANCZOS."""
    start = time.monotonic()
    agent = UpscalingAgent()

    # Use upscaled path if already upscaled, else generation output
    gen = state.get("generation_result")
    image_path = gen.output_path if gen and gen.success else ""

    if not image_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["upscaling"] = round(elapsed, 2)
        return {
            "upscale_result": None,
            "stage_timings": timings,
        }

    result = agent.upscale(image_path=image_path)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["upscaling"] = round(elapsed, 2)

    return {
        "upscale_result": result,
        "stage_timings": timings,
    }


def color_correction_node(state: EliteStudioState) -> dict:
    """Apply brand-palette color corrections to the current image."""
    start = time.monotonic()
    agent = ColorCorrectionAgent()

    # Prefer upscaled output if available, else generation output
    upscale = state.get("upscale_result")
    gen = state.get("generation_result")

    if upscale and upscale.success and upscale.output_path:
        image_path = upscale.output_path
    elif gen and gen.success and gen.output_path:
        image_path = gen.output_path
    else:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["color_correction"] = round(elapsed, 2)
        return {
            "color_result": None,
            "stage_timings": timings,
        }

    result = run_sync(agent.correct(image_path=image_path))
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["color_correction"] = round(elapsed, 2)

    return {
        "color_result": result,
        "stage_timings": timings,
    }


def safety_node(state: EliteStudioState) -> dict:
    """Check generated image for content safety violations."""
    start = time.monotonic()
    agent = SafetyAgent()

    gen = state.get("generation_result")
    image_path = gen.output_path if gen and gen.success else ""

    if not image_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["safety"] = round(elapsed, 2)
        return {
            "safety_result": None,
            "stage_timings": timings,
        }

    result = agent.check(image_path=image_path)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["safety"] = round(elapsed, 2)

    update: dict = {
        "safety_result": result,
        "stage_timings": timings,
    }

    # If flagged, mark pipeline as error — routing edge will send to END
    if result.success and result.flagged:
        update["status"] = "error"
        update["failed_step"] = "safety_filter"
        update["error"] = f"Safety filter triggered: {', '.join(result.categories)}"

    return update


def variant_node(state: EliteStudioState) -> dict:
    """Generate image variants (alternate angles/colorways)."""
    start = time.monotonic()
    agent = VariantAgent()

    gen = state.get("generation_result")

    base_path = gen.output_path if gen and gen.success else ""
    # Variant names come from state (set via GraphConfig at invocation time)
    variants: list[str] = state.get("variant_specs", [])  # type: ignore[assignment]

    if not variants or not base_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["variants"] = round(elapsed, 2)
        return {
            "variant_results": [],
            "stage_timings": timings,
        }

    results = run_sync(
        agent.generate_variants(
            sku=state["sku"],
            base_image_path=base_path,
            variant_specs=variants,
        )
    )
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["variants"] = round(elapsed, 2)

    return {
        "variant_results": results,
        "stage_timings": timings,
    }


def three_d_node(state: EliteStudioState) -> dict:
    """Legendary 3D generation node.

    Generates a 3D .glb replica and renders front/back/ghost shots.
    Updates the state with the 3D-rendered paths.

    Sync wrapper around an async agent — matches the convention used by every
    other node in this file. The shared `run_sync` helper handles both
    no-running-loop (sync `graph.invoke()`) and running-loop (`graph.ainvoke()`)
    cases via `nest_asyncio`. Async safety inside the agent itself is enforced
    by `asyncio.to_thread` wrappers around `subprocess.run` (Blender) and
    `shutil.move` (cross-device renders) — see three_d_agent.py.
    """
    from ..agents.three_d_agent import ThreeDAgent
    from ..agents.vision_agent import _reference_path
    from ..budget import BudgetExceededError

    sku = state["sku"]

    # Reference image: techflat from state or vision-agent lookup
    ref_path = state.get("reference_path") or _reference_path(sku)

    # Budget guard — round-table tournament (Meshy + Tripo + TRELLIS local +
    # AniGen) can dispatch up to 4 providers in parallel; estimate the
    # ceiling at $0.50 to cover the worst case before any provider fires.
    budget = state.get("budget")
    if budget is not None and hasattr(budget, "ensure_within_budget"):
        try:
            budget.ensure_within_budget(_THREE_D_EST_COST_USD, stage="three_d")
        except BudgetExceededError as exc:
            return {
                "status": "error",
                "error": f"budget exceeded before 3D generation: {exc}",
                "failed_step": "3d_generation",
            }

    # The dossier loaded inside generate_replica is now the source of truth for
    # branding spec; enrichment_prompt and vision_result are no longer fed
    # into the RAS prompt (they were thin and could drift from the dossier).
    agent = ThreeDAgent()
    replica_result = run_sync(agent.generate_replica(sku, ref_path))

    if budget is not None and hasattr(budget, "spend") and replica_result.get("success"):
        budget.spend(_THREE_D_EST_COST_USD, stage="three_d")

    if not replica_result["success"]:
        return {
            "status": "error",
            "error": replica_result.get("error", "3D Generation failed"),
            "failed_step": "3d_generation",
        }

    # Map the renders to the state paths
    renders = replica_result["renders"]

    # Convert to standard GenerationResult for compatibility
    gen_result = agent.generate_result_bridge(replica_result, state["view"])

    return {
        "generation_result": gen_result,
        "ghost_mannequin_front_path": renders.get("front", ""),
        "ghost_mannequin_back_path": renders.get("back", ""),
        "3d_model_path": replica_result["glb_path"],
        "3d_fidelity_score": replica_result["fidelity_score"],
    }


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

        # Use catalog-defined source image if available, else fallback to rigid SKU lookup
        source_img = product.source_files[0] if product.source_files else ""
        if source_img:
            # Source images live in wordpress-theme/skyyrose-flagship/assets/images/products/
            ref_path = str(
                __import__(
                    "skyyrose.elite_studio.agents.vision_agent", fromlist=["_PRODUCTS_DIR"]
                )._PRODUCTS_DIR
                / source_img
            )
        else:
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
    result = run_sync(
        gate.verify_reference(
            image_path=ref_path,
            sku=sku,
            expected_garment=expected_garment,
        )
    )

    if not result.passed:
        logger.warning("[Preflight] BLOCKED %s: %s", sku, result.blocking_reason)
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
