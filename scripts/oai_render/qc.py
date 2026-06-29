"""Post-generation QC gate — deterministic checks + VLM judge, pre-acceptance.

Layered, cheapest-first:
  1. Deterministic (free, ~20ms): PNG decodes, expected dimensions, collage
     panel detection (uniform full-span separator bands through the central
     region — a centered garment breaks any central line, a collage gutter
     doesn't).
  2. VLM judge (~$0.0001): a vision model compares the render against its own
     reference images under a strict JSON schema — single image, correct
     garment, correct view, patch/text fidelity, both garments present (pairs).

The gate never writes accepted files itself; ``pipeline.render_sku`` owns the
retry loop and quarantine. Judge failures are tagged so recurring failure modes
are queryable from logs.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

from . import config

log = logging.getLogger(__name__)

# Judge verdict schema — boolean gates fail before any quality consideration
# (OpenAI Image Evals cookbook pattern). ``strict`` schema enforcement makes
# the response machine-parseable without retry-on-parse-failure logic.
_JUDGE_SCHEMA: dict = {
    "name": "render_qc_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "visual_analysis": {
                "type": "string",
                "description": "FIRST, before any verdict: describe what the candidate render "
                "ACTUALLY shows, grounded in REFERENCE IMAGE 1 (the real garment). State the "
                "garment TYPE and SILHOUETTE, the BODY COLOR, the MATERIAL and any lining/"
                "texture (e.g. visible sherpa/fleece at hood and cuffs, or its ABSENCE), and "
                "every logo/graphic/patch you see — its artwork, colorway family, and which "
                "panel it sits on. Then compare each to the reference. This forced description "
                "must precede the boolean gates so they are decided from observation, not guess.",
            },
            "is_single_photograph": {
                "type": "boolean",
                "description": "True only if the ENTIRE frame is one continuous photograph — "
                "not a collage, grid, reference sheet, diptych, or multi-panel layout.",
            },
            "garment_matches_reference": {
                "type": "boolean",
                "description": "True if the rendered garment is the SAME product as the "
                "reference images (silhouette, color, graphics).",
            },
            "view_correct": {
                "type": "boolean",
                "description": "True if the rendered view (front or back) matches the "
                "requested view; a mirrored/duplicated FRONT presented as a back view is False.",
            },
            "branding_legible_and_correct": {
                "type": "boolean",
                "description": "True if visible logos/patches/text match the references — "
                "no invented, missing, truncated, or garbled marks, and NO logo added on a "
                "panel whose reference shows that panel blank.",
            },
            "photorealistic_not_flat": {
                "type": "boolean",
                "description": "True only if the garment reads as a photograph of a real "
                "manufactured garment — dimensional fabric, drape, texture, lighting. A flat "
                "vector-style technical drawing or illustration look is False.",
            },
            "all_garments_present": {
                "type": "boolean",
                "description": "For paired looks: True only if BOTH specified garments are "
                "worn and visible. For single-garment renders: True.",
            },
            "reason": {
                "type": "string",
                "description": "One or two sentences explaining any False verdicts, or "
                "'pass' when all checks hold.",
            },
        },
        "required": [
            "visual_analysis",
            "is_single_photograph",
            "garment_matches_reference",
            "view_correct",
            "branding_legible_and_correct",
            "photorealistic_not_flat",
            "all_garments_present",
            "reason",
        ],
        "additionalProperties": False,
    },
}

# Anthropic structured-output equivalent of _JUDGE_SCHEMA: a FORCED tool call
# (tool_choice={"type":"any"}) returns the verdict as parsed args. Reuses the exact
# same schema body + gate descriptions, so OpenAI and Claude judge identical gates —
# one source of truth, no drift between the two provider paths.
_JUDGE_TOOL: dict = {
    "name": _JUDGE_SCHEMA["name"],
    "description": "Record the QC verdict for the candidate product render.",
    "input_schema": _JUDGE_SCHEMA["schema"],
}

# Map schema gate → failure tag recorded in logs / quarantine metadata.
_GATE_TAGS = {
    "is_single_photograph": "collage_panels",
    "garment_matches_reference": "wrong_garment",
    "view_correct": "wrong_view",
    "branding_legible_and_correct": "branding_drift",
    "photorealistic_not_flat": "flat_render",
    "all_garments_present": "missing_pair_garment",
}

# Max reference images attached to a judge call — generated image + these.
_JUDGE_MAX_REFS = 3

# Hard cap on the stored visual_analysis. Enforced at verdict construction so the
# contract "analysis ≤ N chars" holds everywhere downstream (logs, runlog, monitor).
_ANALYSIS_MAX_CHARS = 600

# Transient-network retries per judge call. Without these, one TCP hiccup falls
# through to accept-unjudged — a paid render ships ungated because of a blip the
# render client itself would have retried five times.
_JUDGE_API_RETRIES = 2
_JUDGE_RETRY_BACKOFF_S = 1.5


@dataclass(frozen=True)
class QCVerdict:
    passed: bool
    failure_tags: tuple[str, ...] = ()
    reason: str = ""
    judge_cost_usd: float = 0.0
    analysis: str = ""  # judge's forced visual_analysis — auditable, never gates pass/fail
    needs_review: bool = False  # Q-unavail: judge infra failed → mandatory human sign-off

    @property
    def summary(self) -> str:
        if self.needs_review:
            return f"needs_review: {self.reason}"
        return "pass" if self.passed else f"{','.join(self.failure_tags)}: {self.reason}"


@dataclass(frozen=True)
class RenderExpectation:
    """What the QC gate should hold this render to (derived from the SkuPlan)."""

    sku: str
    name: str
    style: str  # "ghost" | "on-model" | "flatlay"
    view: str  # "front" | "back"
    is_pair: bool
    is_patch: bool
    branding_spec: str = ""  # dossier's per-view branding bullets (ground truth)
    reference_paths: tuple[Path, ...] = field(default_factory=tuple)


def _decode_image(data: bytes):
    """Return a PIL Image or None (Pillow is a hard dependency of the gate)."""
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except Exception as exc:  # fail closed, but keep the why (bomb/corrupt/OOM)
        log.warning("Image decode failed: %s: %s", type(exc).__name__, exc)
        return None


def _detect_collage_bands(img) -> bool:
    """True when a uniform full-span separator band crosses the CENTRAL region.

    A correctly framed render has the garment/model centered, so every central
    row/column crosses content and varies. A collage gutter is a near-uniform
    band spanning the full width/height. Only the central 25–75% band of each
    axis is scanned to avoid false positives from uniform studio backgrounds at
    the margins.
    """
    import numpy as np

    arr = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = arr.shape

    def has_uniform_band(axis: int) -> bool:
        # Per-line std along the axis; a separator line is near-zero-variance.
        stds = arr.std(axis=axis)
        n = stds.shape[0]
        lo, hi = int(n * 0.25), int(n * 0.75)
        central = stds[lo:hi]
        # Require >= 3 consecutive near-uniform lines (anti single-pixel noise).
        uniform = central < 2.0
        run = 0
        for u in uniform:
            run = run + 1 if u else 0
            if run >= 3:
                return True
        return False

    return has_uniform_band(axis=1) or has_uniform_band(axis=0)


def deterministic_checks(data: bytes) -> list[str]:
    """Free pre-checks. Returns failure tags (empty = pass)."""
    tags: list[str] = []
    img = _decode_image(data)
    if img is None:
        return ["invalid_image"]
    if (img.width, img.height) != config.EXPECTED_RENDER_SIZE:
        tags.append("wrong_dimensions")
    if _detect_collage_bands(img):
        tags.append("collage_panels")
    return tags


_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def _b64_raw(data: bytes) -> str:
    """Plain base64, no ``data:`` URL prefix — Anthropic image blocks require raw base64."""
    return base64.b64encode(data).decode("ascii")


def _b64_data_url(data: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{_b64_raw(data)}"


@lru_cache(maxsize=32)
def _ref_payload(path_str: str) -> tuple[bytes, str] | None:
    """Read + cache one reference image as ``(raw_bytes, media_type)``.

    Reference files are stable for the life of a batch process, and each judged
    retry re-attaches the same refs — without the cache a 40-SKU run with retries
    re-reads the same images from disk hundreds of times. ``None`` for an
    unsupported extension or a missing file.
    """
    path = Path(path_str)
    mime = _MIME_MAP.get(path.suffix.lower())
    if mime is None or not path.exists():
        return None
    return path.read_bytes(), mime


def _ref_data_url(path: Path) -> str | None:
    payload = _ref_payload(str(path))
    if payload is None:
        return None
    data, mime = payload
    return _b64_data_url(data, mime)


def _ref_b64(path: Path) -> tuple[str, str] | None:
    """Return ``(raw_base64, media_type)`` for an Anthropic image block, or None."""
    payload = _ref_payload(str(path))
    if payload is None:
        return None
    data, mime = payload
    return _b64_raw(data), mime


def _judge_instructions(exp: RenderExpectation) -> str:
    view_line = (
        "The render must show the BACK of the garment (rear-facing). A mirrored or "
        "duplicated FRONT is a failure."
        if exp.view == "back"
        else "The render must show the FRONT of the garment."
    )
    style_line = {
        "ghost": "Presentation: ghost-mannequin — garment holds 3D shape, NO person/mannequin.",
        "on-model": "Presentation: worn by ONE full-body model in a scene.",
        "flatlay": "Presentation: single garment laid flat, top-down.",
    }.get(exp.style, "")
    pair_line = (
        "This is a PAIRED look: BOTH garments (top AND bottom) must be worn and visible "
        "on the one model."
        if exp.is_pair
        else ""
    )
    patch_line = (
        "The garment carries an embroidered sport patch — it must be present, complete "
        "(top and bottom halves), and match the patch reference exactly."
        if exp.is_patch
        else ""
    )
    # The branding gate is judged against the REAL PRODUCT PHOTO (reference image 1) at
    # product-card level, NOT pixel-perfect dossier compliance. The dossier spec says
    # WHICH branding exists and WHERE; the real photo says what "correct" looks like.
    branding_line = (
        "BRANDING — the dossier lists what this view carries (use it to know which "
        f"logos/graphics/text are present and WHERE):\n{exp.branding_spec}\n"
        "Judge each element's correctness against REFERENCE IMAGE 1 (the real garment "
        "photo) at product-card level: the right ARTWORK (e.g. a multi-rose cluster, not a "
        "single bloom), the right COLORWAY FAMILY (greyscale vs full-color, matching what "
        "the real garment shows), and the right PLACEMENT/panel. If the dossier marks a "
        "panel blank / 'no decoration', absence there is CORRECT — do not invent a defect."
        if exp.branding_spec
        else ""
    )
    # Tolerate cosmetic micro-deviations gpt-image renders cannot avoid; fail only
    # identity-level branding errors. This stops the false-rejects on shade/count/texture.
    micro_line = (
        "Do NOT fail for cosmetic micro-deviations that do not change the product's "
        "identity: exact petal/stem/thread SHADE, precise vine or leaf COUNT, exact cloud "
        "SHAPE, print-vs-embroidery TEXTURE, raised-vs-flat RELIEF, or minor scale/position "
        "shifts WITHIN the same panel. A flat product photo cannot convey tactile depth. "
        "Fail a logo only when it is MISSING, the WRONG artwork, the WRONG colorway family, "
        "or on the WRONG panel/region (within-panel nudges are fine; cross-panel moves are not)."
    )
    # Gross defects the judge has historically MISSED — make them explicit so a missing
    # sherpa lining or a wrong body color is caught, not waved through.
    gross_line = (
        "DO fail GROSS defects that misrepresent the product: wrong garment TYPE or "
        "MATERIAL (e.g. a sherpa-/fleece-lined jacket rendered with no visible lining at "
        "the hood or cuffs; a knit shown as leather), wrong BODY COLOR HUE FAMILY (compare "
        "the candidate's base fabric hue side-by-side with REFERENCE IMAGE 1 — a dark "
        "forest-green or navy garment rendered as pure black IS a colorway fail; do not "
        "excuse a hue shift as 'lighting'), wrong silhouette, distortion or extra limbs, "
        "or branding/appliqué rendered on a DIFFERENT PANEL or GARMENT REGION than "
        "REFERENCE IMAGE 1 shows (e.g. a SLEEVE appliqué moved onto the torso/hip/hem, or "
        "a chest patch mirrored to the opposite side), or branding entirely absent. In "
        "your visual_analysis, explicitly name the candidate's base hue and each mark's "
        "panel BEFORE deciding these gates."
    )
    return "\n".join(
        line
        for line in (
            "You are an e-commerce product-photography QC judge. The FIRST image is the "
            f"AI-generated candidate render of: {exp.name} (SKU {exp.sku}). REFERENCE IMAGE 1 "
            "(the next image) is a PHOTO OF THE REAL GARMENT — the ultimate authority on what "
            "this product looks like; any further images are supporting references. Decide "
            "whether the candidate is a SHIPPABLE product card that accurately represents the "
            "real garment.",
            style_line,
            view_line,
            branding_line,
            micro_line,
            gross_line,
            pair_line,
            patch_line,
            "Judge SHIPPABILITY against the real garment (reference image 1), not pixel-"
            "perfect dossier compliance. Pass when the candidate accurately represents the "
            "real product as a card; fail only clear identity-level or gross defects, and "
            "name the specific defect in `reason`.",
        )
        if line
    )


class QCGate:
    """Deterministic checks + optional VLM judge. One instance per batch run."""

    def __init__(self, *, use_judge: bool = True, judge_fn=None) -> None:
        self._use_judge = use_judge and config.QC_ENABLED
        self._provider = config.QC_JUDGE_PROVIDER
        self._judge_fn = judge_fn  # injection seam: callable(req) -> (verdict_dict, cost_usd)
        self._client = None
        self._model = ""
        if self._use_judge and self._judge_fn is None:
            try:
                if self._provider == "anthropic":
                    import anthropic

                    key = os.environ.get(config.ANTHROPIC_API_KEY_ENV, "").strip()
                    if not key:
                        raise RuntimeError(
                            f"{config.ANTHROPIC_API_KEY_ENV} not set — the Claude QC judge "
                            "cannot start. Add it to gemini/.env (loaded override=True) or set "
                            "QC_JUDGE_PROVIDER='openai' to use the (unreliable) fallback."
                        )
                    self._client = anthropic.Anthropic(
                        api_key=key, timeout=config.REQUEST_TIMEOUT_S
                    )
                    self._model = config.QC_JUDGE_MODEL_ANTHROPIC
                else:
                    from openai import OpenAI

                    self._client = OpenAI(
                        api_key=config.get_api_key(), timeout=config.REQUEST_TIMEOUT_S
                    )
                    self._model = config.QC_JUDGE_MODEL
            except Exception as exc:
                # No silent degradation: a judge that cannot start is a hard error,
                # otherwise a paid batch would run ungated without anyone noticing.
                raise RuntimeError(f"QC judge client failed to initialize: {exc}") from exc

    def check(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        det_tags = deterministic_checks(data)
        if det_tags:
            return QCVerdict(
                passed=False,
                failure_tags=tuple(det_tags),
                reason="deterministic pre-check failed",
            )
        if not self._use_judge:
            return QCVerdict(passed=True, reason="deterministic only (judge disabled)")
        return self._judge(data, exp)

    def _judge(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        """Dispatch to an injected judge_fn (seam), else the configured provider's judge."""
        if self._judge_fn is not None:
            return self._judge_injected(data, exp)
        if self._provider == "anthropic":
            return self._judge_anthropic(data, exp)
        return self._judge_openai(data, exp)

    def _judge_injected(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        """Judge via an injected callable — the swappable seam (tests + alt backends).

        ``judge_fn`` receives a provider-agnostic request dict and returns
        ``(verdict_dict, cost_usd)``. Any exception routes to mandatory review
        (judge_unavailable), identical to a real judge-infrastructure failure — a
        paid render is held for human sign-off, never shipped unjudged.
        """
        req = {
            "instructions": _judge_instructions(exp),
            "image": data,
            "reference_paths": tuple(exp.reference_paths),
        }
        try:
            verdict, cost = self._judge_fn(req)
        except Exception as exc:
            return self._unavailable(exp, exc)
        return replace(self._verdict_from_dict(verdict, exp), judge_cost_usd=float(cost))

    def _judge_openai(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        content: list[dict] = [{"type": "text", "text": _judge_instructions(exp)}]
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": _b64_data_url(data), "detail": config.QC_JUDGE_DETAIL},
            }
        )
        for ref in exp.reference_paths[:_JUDGE_MAX_REFS]:
            url = _ref_data_url(ref)
            if url:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": config.QC_JUDGE_DETAIL},
                    }
                )

        # GPT-5 / o-series reject `max_tokens` (require `max_completion_tokens`) and
        # may spend reasoning tokens before the JSON verdict, so give them more room.
        is_next_gen = self._model.startswith(("gpt-5", "o1", "o3", "o4"))
        token_kwarg = (
            {"max_completion_tokens": max(config.QC_JUDGE_MAX_OUTPUT_TOKENS, 2000)}
            if is_next_gen
            else {"max_tokens": config.QC_JUDGE_MAX_OUTPUT_TOKENS}
        )
        try:
            resp = self._call_judge_api(
                lambda: self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": content}],
                    response_format={"type": "json_schema", "json_schema": _JUDGE_SCHEMA},
                    **token_kwarg,
                )
            )
            verdict = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            return self._unavailable(exp, exc)
        return self._verdict_from_dict(verdict, exp)

    def _judge_anthropic(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        """Claude vision judge: raw-base64 image blocks + a forced tool call for the verdict."""
        content: list[dict] = [
            {"type": "text", "text": _judge_instructions(exp)},
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": _b64_raw(data)},
            },
        ]
        for ref in exp.reference_paths[:_JUDGE_MAX_REFS]:
            result = _ref_b64(ref)
            if result:
                raw, mime = result
                content.append(
                    {"type": "image", "source": {"type": "base64", "media_type": mime, "data": raw}}
                )
        try:
            resp = self._call_judge_api(
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=config.QC_JUDGE_MAX_OUTPUT_TOKENS,
                    tools=[_JUDGE_TOOL],
                    tool_choice={"type": "any"},  # forces exactly one render_qc_verdict tool call
                    messages=[{"role": "user", "content": content}],
                )
            )
            verdict: dict = {}
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == _JUDGE_TOOL["name"]:
                    verdict = dict(block.input)  # SDK already parsed + schema-validated
                    break
            if not verdict:
                raise ValueError("no render_qc_verdict tool_use block in response")
        except Exception as exc:
            return self._unavailable(exp, exc)
        return self._verdict_from_dict(verdict, exp)

    def _call_judge_api(self, send):
        """Call the provider API with transient-error retries.

        A judge that gives up on the first connection blip downgrades the run to
        accept-unjudged; retry like the render client does before conceding.
        """
        for attempt in range(_JUDGE_API_RETRIES + 1):
            try:
                return send()
            except Exception:
                if attempt == _JUDGE_API_RETRIES:
                    raise
                delay = _JUDGE_RETRY_BACKOFF_S * (attempt + 1)
                log.warning(
                    "Judge API call failed (attempt %d) — retrying in %.1fs", attempt + 1, delay
                )
                time.sleep(delay)

    def _unavailable(self, exp: RenderExpectation, exc: Exception) -> QCVerdict:
        """Judge infrastructure failure ≠ render failure — but an unjudged render must
        NOT ship. Q-unavail: route to mandatory human review (needs_review) instead of
        auto-accepting. The deterministic checks passed, so the bytes are kept for the
        reviewer; never silently swallow the error."""
        log.error("QC judge call failed for %s: %s — routing to mandatory review", exp.sku, exc)
        # Exception strings from SDKs can embed request metadata; the runlog JSONL
        # and monitor surface this reason verbatim, so keep it typed + truncated.
        return QCVerdict(
            passed=False,
            needs_review=True,
            failure_tags=("judge_unavailable",),
            reason=f"judge error: {type(exc).__name__}: {str(exc)[:120]}",
            judge_cost_usd=0.0,
        )

    def _verdict_from_dict(self, verdict: dict, exp: RenderExpectation) -> QCVerdict:
        """Map a provider-agnostic verdict dict to a QCVerdict via the shared gate tags."""
        tags = tuple(tag for gate, tag in _GATE_TAGS.items() if verdict.get(gate) is False)
        passed = not tags
        reason = str(verdict.get("reason", ""))[:300]
        analysis = str(verdict.get("visual_analysis", ""))
        if len(analysis) > _ANALYSIS_MAX_CHARS:
            analysis = analysis[:_ANALYSIS_MAX_CHARS] + "…"
        if not passed:
            log.warning("QC judge failed %s [%s]: %s", exp.sku, ",".join(tags), reason)
        return QCVerdict(
            passed=passed,
            failure_tags=tags,
            reason=reason,
            judge_cost_usd=config.EST_JUDGE_COST_USD,
            analysis=analysis,
        )
