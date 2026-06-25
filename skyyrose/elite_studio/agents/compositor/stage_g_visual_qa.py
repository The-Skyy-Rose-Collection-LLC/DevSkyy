"""Stage G: visual QA gate.

Scores the composite via Gemini using a structured rubric. Integrates an
optional embedding pre-gate that short-circuits Gemini when the render is
clearly off-brand (cost savings).
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from .infra import _safe_json_extract

logger = logging.getLogger(__name__)

_DEFAULT_QA_RUBRIC = """You are QA-scoring a scene composite for SkyyRose luxury fashion.

Scene: {scene_name}
Collection: {collection}

Score on a 0-10 scale across three dimensions and reply as STRICT JSON:
{{
  "status": "pass" | "warn" | "fail",
  "lighting_match": {{"score": <0-10>, "notes": "<one sentence>"}},
  "garment_fidelity": {{"score": <0-10>, "notes": "<one sentence>"}},
  "scene_coherence": {{"score": <0-10>, "notes": "<one sentence>"}}
}}

Rules:
- "pass" requires all three scores >= 8 with no edge artifacts visible.
- "warn" if any single score is 6-7 OR mild edge halo / contact-shadow drift.
- "fail" if any score < 6, identity loss, or the subject looks pasted-on.
"""

# Default location for the persisted brand-style centroid. The pre-QA gate
# loads this file at runtime if it exists; otherwise the gate is a no-op.
_DEFAULT_CENTROID_PATH = Path(__file__).resolve().parents[2] / "data" / "brand_centroid.npz"


def visual_qa(
    composite_path: str,
    scene_name: str,
    collection: str,
    *,
    analyze_vision: Any,
) -> dict[str, Any]:
    """Score the composite via Gemini using a structured rubric.

    Returns a dict with at minimum a ``status`` key (``pass`` / ``warn`` /
    ``fail``). Soft-fails to ``warn`` rather than blocking the pipeline
    when the QA provider itself is unavailable — the audit log captures
    the failure mode.

    Args:
        composite_path: Path to the shadow-composited image.
        scene_name: Scene identifier for rubric formatting.
        collection: Collection slug for rubric formatting.
        analyze_vision: Callable from ``..gemini_rest`` — injected so tests
            can patch at the compositor_agent namespace without instantiating
            a full agent.

    Returns:
        QA result dict with ``status``, scores, and model metadata.
    """
    from ...config import COMPOSITOR_QA_MODEL

    with open(composite_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    ext = Path(composite_path).suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    rubric = _DEFAULT_QA_RUBRIC.format(
        scene_name=scene_name,
        collection=collection,
    )

    result = analyze_vision(
        model=COMPOSITOR_QA_MODEL,
        prompt=rubric,
        image_b64=b64,
        mime_type=mime,
    )

    if not result.get("success"):
        return {
            "status": "warn",
            "error": result.get("error", "QA provider returned no body"),
            "model": COMPOSITOR_QA_MODEL,
        }

    text = result.get("text", "")
    try:
        parsed = _safe_json_extract(text)
        status = parsed.get("status") or "warn"
        return {**parsed, "status": status, "model": COMPOSITOR_QA_MODEL}
    except Exception:
        return {
            "status": "warn",
            "error": f"could not parse QA JSON: {text[:120]}",
            "model": COMPOSITOR_QA_MODEL,
        }


def visual_qa_gemini(
    shadow_path: str,
    scene_name: str,
    collection: str,
    *,
    analyze_vision: Any,
) -> dict[str, Any]:
    """Module-level proxy to ``visual_qa``.

    Isolated so the pre-QA gate (``maybe_apply_gate``) and its tests can
    patch the Gemini path without instantiating a full agent.

    Args:
        shadow_path: Path to the shadow-composited image.
        scene_name: Scene identifier.
        collection: Collection slug.
        analyze_vision: Injected from ``..gemini_rest``.

    Returns:
        QA result dict.
    """
    return visual_qa(shadow_path, scene_name, collection, analyze_vision=analyze_vision)


def maybe_apply_gate(
    shadow_path: str,
    scene_name: str,
    collection: str,
    *,
    analyze_vision: Any,
    centroid_path: Path | str | None = None,
) -> dict[str, Any]:
    """Pre-QA embedding gate. Reject -> skip Gemini. Accept -> call Gemini.

    If no centroid file exists at ``centroid_path`` (or the default
    ``_DEFAULT_CENTROID_PATH``), the gate is a no-op and we fall through to
    Gemini directly. This means the gate is opt-in: deploy the centroid file
    to enable it; remove the file to disable it.

    Args:
        shadow_path: Path to the shadow-composited image.
        scene_name: Scene identifier.
        collection: Collection slug.
        analyze_vision: Injected from ``..gemini_rest``.
        centroid_path: Optional override for the brand centroid file path.

    Returns:
        QA result dict (either embedding-gate verdict or Gemini rubric scores).
    """
    from ...quality import embedding_gate
    from ...quality.brand_centroid import load_centroid

    resolved = Path(centroid_path) if centroid_path else _DEFAULT_CENTROID_PATH
    if not resolved.exists():
        return visual_qa_gemini(shadow_path, scene_name, collection, analyze_vision=analyze_vision)

    centroid = load_centroid(resolved)
    verdict = embedding_gate.evaluate(shadow_path, centroid)
    if not verdict.accepted:
        return {
            "status": "fail",
            "reason": verdict.reason,
            "embedding_score": verdict.score,
            "embedding_threshold": verdict.threshold,
            "skipped_gemini": True,
        }
    return visual_qa_gemini(shadow_path, scene_name, collection, analyze_vision=analyze_vision)
