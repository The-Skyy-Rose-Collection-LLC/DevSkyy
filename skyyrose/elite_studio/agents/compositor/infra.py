"""Shared infrastructure for the compositor package.

Contains:
- Logging stub (_SilentLogger)
- FAL upload + BRIA matte helpers (upload_to_fal, _matte_via_fal)
- File-hash and cache-dir helpers (_file_hash, _cache_dir)
- Base64 image helpers (_b64_image, _b64_image_for_claude)
- JSON helpers (_safe_json_extract, _extract_first_image_url)
- Budget gate helper (_gate_budget, _strict_budget_enabled)
- Module-level rembg / fal_client optional imports
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from ...budget import BudgetExceededError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional runtime deps (patched by tests at the compositor_agent namespace)
# ---------------------------------------------------------------------------

_REMBG_UNAVAILABLE_SENTINEL = "__REMBG_UNAVAILABLE__"

try:  # pragma: no cover - exercised via tests that patch this name
    from rembg import remove  # type: ignore[import-not-found]
except (ImportError, AttributeError, Exception):  # pragma: no cover

    def remove(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(_REMBG_UNAVAILABLE_SENTINEL)


try:  # pragma: no cover
    import fal_client  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    fal_client = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Logging stub
# ---------------------------------------------------------------------------


class _SilentLogger:
    """No-op default logger when caller doesn't supply one.

    Avoids a circular import with ``..coordinator.NullLogger`` (coordinator
    itself imports CompositorAgent). Any duck-typed logger with the same
    methods works in its place — tests pass ``coordinator.NullLogger()``.
    """

    def info(self, msg: str) -> None: ...
    def step(self, step_num: int, total: int, label: str) -> None: ...
    def ok(self, msg: str) -> None: ...
    def fail(self, msg: str) -> None: ...
    def separator(self) -> None: ...


# ---------------------------------------------------------------------------
# FAL upload + BRIA matte
# ---------------------------------------------------------------------------


def upload_to_fal(local_path: str | Path) -> str:
    """Upload a local file to the fal CDN and return its public URL.

    Synchronous wrapper around ``fal_client.upload_file`` so the compositor's
    sync API stays linear. Tests patch this symbol directly to avoid network.
    """
    if fal_client is None:  # pragma: no cover
        raise RuntimeError(
            "fal_client is not installed. `pip install fal_client` to enable Stages 3-4."
        )
    path = str(local_path)
    if not Path(path).is_file():
        raise FileNotFoundError(f"upload source not found: {path}")
    return fal_client.upload_file(path)  # type: ignore[no-any-return]


def _matte_via_fal(image_bytes: bytes) -> bytes:
    """Run BRIA RMBG 2.0 via FAL when local rembg is unavailable.

    Same model, same ~$0.005 cost — the only difference is that the matte
    runs hosted instead of locally. Used as a transparent fallback when the
    rembg toolchain can't load (typically Python 3.14 + numpy 2.x).
    """
    if fal_client is None:
        raise RuntimeError("Neither rembg nor fal_client is available; cannot extract alpha matte.")
    image_url = fal_client.upload(image_bytes, content_type="image/png")
    result = fal_client.run(
        "fal-ai/bria/background/remove",
        arguments={"image_url": image_url},
    )
    out_url = _extract_first_image_url(result)
    if not out_url:
        raise RuntimeError("FAL BRIA endpoint returned no image URL")
    resp = httpx.get(out_url, timeout=60.0)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _file_hash(path: str | Path, *, prefix: str = "") -> str:
    """SHA-256 of file bytes, truncated for filename safety."""
    p = Path(path)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"{prefix}{h.hexdigest()[:16]}" if prefix else h.hexdigest()[:16]


def _cache_dir(stage: str) -> Path:
    """Repo-relative cache directory per stage. Created on first use."""
    repo = Path(__file__).resolve().parents[4]
    d = repo / "renders" / "cache" / stage
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Base64 helpers
# ---------------------------------------------------------------------------


def _b64_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("ascii")


def _b64_image_for_claude(path: str, *, max_dim: int = 1568) -> str:
    """Base64-encode an image, downscaling first to fit Anthropic's 5MB-per-image limit.

    Anthropic's published guidance is 1568px on the longest side as the
    sweet spot for accuracy + cost. Below that, vision quality degrades;
    above 5MB after base64, the API rejects the request outright.
    """
    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        longest = max(w, h)
        if longest > max_dim:
            ratio = max_dim / longest
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88, optimize=True)
        return base64.standard_b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def _extract_first_image_url(result: Any) -> str | None:
    """Pull the first output URL from a fal_client response.

    fal endpoints vary: some return ``{"images": [{"url": ...}]}``, others
    ``{"image": {"url": ...}}``, others raw strings.
    """
    if not isinstance(result, dict):
        return None
    if "images" in result:
        items = result["images"]
        if isinstance(items, list) and items:
            head = items[0]
            if isinstance(head, dict) and "url" in head:
                return str(head["url"])
            if isinstance(head, str):
                return head
    if "image" in result:
        item = result["image"]
        if isinstance(item, dict) and "url" in item:
            return str(item["url"])
        if isinstance(item, str):
            return item
    return None


def _safe_json_extract(text: str) -> dict[str, Any]:
    """Pull JSON out of an LLM response that may have prose around it."""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    # Find first { and matching last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in text")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------------------
# FLUX cost constants (used by FluxProviderMixin and stage_d_flux)
# ---------------------------------------------------------------------------

_FLUX_FILL_FAL_COST_USD: float = 0.05
_FLUX_KONTEXT_FALLBACK_COST_USD: float = 0.04
_FLUX_FILL_REPLICATE_COST_USD: float = 0.05

# ---------------------------------------------------------------------------
# Budget gate helper (shared across all paid FAL calls in stage_d_flux)
# ---------------------------------------------------------------------------

_STRICT_BUDGET_ENV = "ELITE_STUDIO_STRICT_BUDGET"


def _strict_budget_enabled() -> bool:
    """Return True when ELITE_STUDIO_STRICT_BUDGET is set to a truthy value.

    Mirrors ``synthesis.stages.base_render._strict_budget_enabled`` — extracted
    here so compositor stages don't take a cross-subpackage import dependency.
    """
    return os.environ.get(_STRICT_BUDGET_ENV, "").lower() in ("1", "true", "yes", "on")


def _gate_budget(budget: Any, cost_usd: float, label: str) -> None:
    """Check budget headroom before a paid FAL call.

    Args:
        budget: A ``RunBudget``-like object with ``ensure_within_budget(cost)``
            and ``spend(cost)`` methods, or ``None`` for back-compat callers.
        cost_usd: Expected cost of the call in USD.
        label: Human-readable name for logging / error messages.

    Raises:
        BudgetExceededError: when the budget is set, headroom is insufficient,
            and ``ELITE_STUDIO_STRICT_BUDGET`` is enabled.

    When ``budget`` is ``None`` a WARNING is emitted and execution continues
    (back-compat mode). The caller is responsible for calling
    ``budget.spend(cost_usd)`` on the SUCCESS path after the actual API call.
    """
    if budget is None:
        if _strict_budget_enabled():
            raise BudgetExceededError(
                f"compositor [{label}] called without a budget object and "
                "ELITE_STUDIO_STRICT_BUDGET is set — refusing to proceed."
            )
        logger.warning(
            "compositor [%s]: no RunBudget supplied — proceeding unbudgeted (cost ~$%.3f). "
            "Set ELITE_STUDIO_STRICT_BUDGET=1 to make this a hard error.",
            label,
            cost_usd,
        )
        return

    try:
        budget.ensure_within_budget(cost_usd)
    except Exception as exc:
        # Re-raise as-is; callers treat any exception from ensure_within_budget
        # as a budget-exceeded signal.
        raise exc
