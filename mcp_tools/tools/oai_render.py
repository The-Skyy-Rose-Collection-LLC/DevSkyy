"""OAI gpt-image-2 product-render tools — plan (free) + generate (paid, gated).

Exposes the ``scripts/oai_render`` pipeline as MCP tools so the dashboard / an
agent can plan and fire SkyyRose product renders. The paid ``generate`` tool is
gated by an explicit ``confirm`` flag (the tool-callable form of STOP-AND-SHOW):
the first call returns the cost manifest and spends nothing; only ``confirm=true``
incurs OpenAI charges, and the hard cost cap is enforced before any spend.
"""

import asyncio

from pydantic import Field

from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput
from scripts.oai_render import config, cost, pipeline
from scripts.oai_render.prompt import PRESENTATIONS
from scripts.oai_render.references import build_dossier_index, load_catalog

_VALID_STYLES = sorted(PRESENTATIONS)


class OAIRenderPlanInput(BaseAgentInput):
    """Target + style selection for an OAI render plan (no API calls)."""

    skus: list[str] | None = Field(
        default=None,
        description="Explicit SKUs to render, e.g. ['br-010', 'br-001']. Mutually exclusive "
        "with collection/all_skus.",
        max_length=50,
    )
    collection: str | None = Field(
        default=None,
        description="Render a whole collection slug: black-rose | signature | love-hurts | "
        "kids-capsule.",
        max_length=40,
    )
    all_skus: bool = Field(
        default=False,
        description="Render the entire catalog (overrides skus/collection when true).",
    )
    styles: list[str] = Field(
        default_factory=lambda: ["ghost", "on-model"],
        description="Presentation styles per SKU: ghost (product card), on-model (collection "
        "scene), flatlay. Default ['ghost', 'on-model'].",
        max_length=3,
    )


class OAIRenderGenerateInput(OAIRenderPlanInput):
    """Same selection as the plan tool, plus the explicit paid-spend confirmation."""

    confirm: bool = Field(
        default=False,
        description="MUST be true to incur OpenAI charges. When false (default) the tool returns "
        "the cost manifest and spends NOTHING — the tool-callable STOP-AND-SHOW gate.",
    )


def _validate_styles(styles: list[str]) -> list[str] | str:
    """Return the cleaned style list, or an error string if any style is unknown."""
    cleaned = [s.strip() for s in styles if s.strip()]
    bad = [s for s in cleaned if s not in PRESENTATIONS]
    if bad or not cleaned:
        return f"ERROR: invalid styles {bad or '(empty)'}. Valid: {_VALID_STYLES}."
    return cleaned


def _plan(params: OAIRenderPlanInput) -> dict | str:
    """Resolve targets + build the dry-run plan/manifest (zero API calls). Returns dict or error."""
    styles = _validate_styles(params.styles)
    if isinstance(styles, str):
        return styles

    catalog = load_catalog()
    dossier_index = build_dossier_index()
    try:
        targets = pipeline.resolve_targets(
            catalog,
            skus=params.skus,
            collection=params.collection,
            all_skus=params.all_skus,
        )
    except KeyError as exc:
        return f"ERROR: {exc}"
    if not targets:
        return "ERROR: no SKUs matched. Provide skus, collection, or all_skus=true."

    dry = pipeline.run(targets, catalog, dossier_index, styles=styles, dry_run=True)
    return dry


@mcp.tool(
    name="devskyy_oai_render_plan",
    annotations={
        "title": "OAI Render — Plan & Cost (no API)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "defer_loading": True,
    },
)
@secure_tool("oai_render_plan")
async def oai_render_plan(params: OAIRenderPlanInput) -> str:
    """Plan a SkyyRose gpt-image-2 product render and show its cost manifest. NO API CALLS.

    Resolves the requested SKUs (or a collection, or the whole catalog) through the
    canonical catalog CSV + per-SKU dossiers, builds the exact (sku, style, view)
    render matrix — ghost-front always, ghost-back when a back source exists,
    on-model (paired-look when the SKU is part of a sold-separately set) — and
    returns the estimated cost manifest. Spends nothing; use this before generate.

    Args:
        params (OAIRenderPlanInput): skus | collection | all_skus, plus styles.

    Returns:
        str: the cost manifest (products, image count, $ estimate, per-row breakdown).
    """
    dry = await asyncio.to_thread(_plan, params)
    if isinstance(dry, str):
        return dry
    return cost.format_manifest(dry["manifest"])


@mcp.tool(
    name="devskyy_oai_render_generate",
    annotations={
        "title": "OAI Render — Generate (PAID, gated)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
    },
)
@secure_tool("oai_render_generate")
async def oai_render_generate(params: OAIRenderGenerateInput) -> str:
    """Generate SkyyRose product renders via OpenAI gpt-image-2. PAID — gated by ``confirm``.

    Safety (tool-callable STOP-AND-SHOW):
      - confirm=false (default) → returns the cost manifest and spends NOTHING.
      - confirm=true → enforces the hard cost cap, then renders. PNGs are written to
        renders/oai/<slug>/ (solo) or renders/oai/pair__<a>__<b>/ (paired looks).

    The render runs off the event loop (asyncio.to_thread); a large batch can take
    minutes. Per-SKU failures are captured, never abort the batch.

    Args:
        params (OAIRenderGenerateInput): skus | collection | all_skus, styles, confirm.

    Returns:
        str: the manifest (when not confirmed) or a per-SKU render result summary.
    """
    dry = await asyncio.to_thread(_plan, params)
    if isinstance(dry, str):
        return dry

    manifest = dry["manifest"]
    if not params.confirm:
        return (
            cost.format_manifest(manifest)
            + "\n\nNOT CONFIRMED — nothing was generated. Re-call with confirm=true to spend "
            f"~${manifest.est_total_usd:.2f} (hard cap ${config.HARD_COST_CAP_USD:.2f})."
        )

    try:
        cost.enforce_cap(manifest)
    except cost.CostCapExceeded as exc:
        return f"ABORT (cost cap): {exc}"

    renderable = [p for p in dry["plans"] if p.renderable]
    if not renderable:
        return (
            "Nothing renderable (all targets skipped). Resolve references first.\n\n"
            + "\n".join(f"  SKIP {p.sku}: {p.error}" for p in dry["plans"] if not p.renderable)
        )

    from scripts.oai_render.client import OAIImageClient

    client = OAIImageClient()  # validates OPENAI_API_KEY
    # Render the EXACT plans the manifest was built from (no re-plan → no TOCTOU).
    results = await asyncio.to_thread(pipeline.render_all, dry["plans"], client)

    rendered = [r for r in results if r.status == "rendered"]
    errored = [r for r in results if r.status == "error"]
    skipped = [r for r in results if r.status == "skipped"]
    qc_failed = [r for r in results if r.status == "qc_failed"]
    lines = [
        f"Done — {len(rendered)} rendered, {len(skipped)} skipped, {len(errored)} errored, "
        f"{len(qc_failed)} QC-failed "
        f"(~${len(rendered) * config.EST_COST_PER_IMAGE_USD:.2f} est).",
    ]
    lines += [f"  ✓ {r.sku} → {r.output_path}" for r in rendered]
    lines += [f"  ✗ {r.sku}: {r.reason}" for r in errored]
    lines += [
        f"  ⚠ {r.sku} QC-failed (quarantined in renders/oai/_rejected/): {r.reason}"
        for r in qc_failed
    ]
    lines += [f"  - {r.sku} skipped: {r.reason}" for r in skipped]
    return "\n".join(lines)
