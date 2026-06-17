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
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class QCVerdict:
    passed: bool
    failure_tags: tuple[str, ...] = ()
    reason: str = ""
    judge_cost_usd: float = 0.0

    @property
    def summary(self) -> str:
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
    reference_paths: tuple[Path, ...] = field(default_factory=tuple)


def _decode_image(data: bytes):
    """Return a PIL Image or None (Pillow is a hard dependency of the gate)."""
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except Exception:
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


def _b64_data_url(data: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _ref_data_url(path: Path) -> str | None:
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower())
    if mime is None or not path.exists():
        return None
    return _b64_data_url(path.read_bytes(), mime)


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
    return "\n".join(
        line
        for line in (
            "You are a strict e-commerce product-photography QC judge. The FIRST image is "
            f"the AI-generated candidate render of: {exp.name} (SKU {exp.sku}). The images "
            "after it are the ground-truth references for the same product.",
            style_line,
            view_line,
            pair_line,
            patch_line,
            "Judge ONLY against the schema gates. Be strict: when uncertain on a gate, "
            "answer False and say why in `reason`.",
        )
        if line
    )


class QCGate:
    """Deterministic checks + optional VLM judge. One instance per batch run."""

    def __init__(self, *, use_judge: bool = True, judge_fn=None) -> None:
        self._use_judge = use_judge and config.QC_ENABLED
        self._provider = config.QC_JUDGE_PROVIDER
        self._judge_fn = judge_fn
        self._client = None
        if self._use_judge and judge_fn is None and self._provider == "openai":
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=config.get_api_key(), timeout=config.REQUEST_TIMEOUT_S
                )
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
        if self._provider == "anthropic" or self._judge_fn is not None:
            return self._judge_anthropic(data, exp)
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

        try:
            resp = self._client.chat.completions.create(
                model=config.QC_JUDGE_MODEL,
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_schema", "json_schema": _JUDGE_SCHEMA},
                max_tokens=config.QC_JUDGE_MAX_OUTPUT_TOKENS,
            )
            verdict = json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            # Judge infrastructure failure ≠ render failure. Accept the render
            # (deterministic checks already passed) but tag it for human review.
            log.error("QC judge call failed for %s: %s — accepting unjudged", exp.sku, exc)
            return QCVerdict(
                passed=True,
                failure_tags=("judge_unavailable",),
                reason=f"judge error: {exc}",
                judge_cost_usd=0.0,
            )

        tags = tuple(tag for gate, tag in _GATE_TAGS.items() if verdict.get(gate) is False)
        passed = not tags
        reason = str(verdict.get("reason", ""))[:300]
        if not passed:
            log.warning("QC judge failed %s [%s]: %s", exp.sku, ",".join(tags), reason)
        return QCVerdict(
            passed=passed,
            failure_tags=tags,
            reason=reason,
            judge_cost_usd=config.EST_JUDGE_COST_USD,
        )

    def _judge_anthropic(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        from evaluation.domains.imagery import ImageryAdapter
        from evaluation.judge import ClaudeJudge, make_client

        adapter = ImageryAdapter()
        request = adapter.build_judge_request(data, exp)
        judge_fn = self._judge_fn
        if judge_fn is None:
            judge = ClaudeJudge(
                client=make_client(),
                model=config.QC_JUDGE_ANTHROPIC_MODEL,
                max_tokens=config.QC_JUDGE_ANTHROPIC_MAX_TOKENS,
            )

            def judge_fn(req):
                return judge.run(messages=req["messages"], tool=req["tool"])

        try:
            output, cost = judge_fn(request)
        except Exception as exc:
            log.error("Claude QC judge failed for %s: %s — accepting unjudged", exp.sku, exc)
            return QCVerdict(
                passed=True,
                failure_tags=("judge_unavailable",),
                reason=f"judge error: {exc}",
            )
        verdict = adapter.parse_verdict(output, det_failures=[])
        return QCVerdict(
            passed=verdict.passed,
            failure_tags=verdict.failure_tags,
            reason=verdict.reason,
            judge_cost_usd=cost,
        )
