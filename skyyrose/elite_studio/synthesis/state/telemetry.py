"""Cost tracker + structured logging for the FLUX synthesis pipeline.

Per the architecture doc, no hard cost cap — but we track and warn at
$5 / $10 / $20 / $50 thresholds so spend doesn't go silent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Per-call cost estimates in USD. Pulled from public pricing as of 2026-04;
# update via env if vendor pricing changes.
COST_USD: dict[str, float] = {
    "fal-ai/flux-pro/kontext": 0.04,
    "fal-ai/flux-pro/v1/fill": 0.05,
    "fal-ai/flux-kontext-lora/inpaint": 0.05,
    "fal-ai/iclight-v2": 0.02,
    "gemini-3-flash-preview": 0.005,
    "gemini-3-flash-preview:vision-audit": 0.005,
    "gemini-3-flash-preview:mask-derive": 0.005,
}


@dataclass
class StageRecord:
    sku: str
    view: str
    attempt: int
    stage: str
    model: str
    duration_ms: int
    estimated_cost_usd: float
    request_id: str | None = None
    output_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """In-process cost accumulator.

    Singleton-ish — pass the same instance through the pipeline. Logs at
    spending tier crossings.
    """

    TIERS_USD: tuple[float, ...] = (5.0, 10.0, 20.0, 50.0)

    def __init__(self) -> None:
        self._total: float = 0.0
        self._records: list[StageRecord] = []
        self._tier_alerts_fired: set[float] = set()

    @property
    def total_usd(self) -> float:
        return self._total

    @property
    def records(self) -> list[StageRecord]:
        return list(self._records)

    def record(self, record: StageRecord) -> None:
        self._records.append(record)
        self._total += record.estimated_cost_usd
        self._maybe_warn_tier()

    def add(
        self, *, model: str, sku: str, view: str, attempt: int, stage: str, **extra: Any
    ) -> StageRecord:
        """Record a stage call using the canned cost-per-model lookup."""
        cost = COST_USD.get(model, 0.0)
        if model not in COST_USD:
            logger.warning("no cost estimate for model %s — recording $0", model)
        record = StageRecord(
            sku=sku,
            view=view,
            attempt=attempt,
            stage=stage,
            model=model,
            duration_ms=int(extra.pop("duration_ms", 0)),
            estimated_cost_usd=cost,
            request_id=extra.pop("request_id", None),
            output_url=extra.pop("output_url", None),
            extra=extra,
        )
        self.record(record)
        return record

    def summary(self) -> dict[str, Any]:
        by_model: dict[str, float] = {}
        by_sku: dict[str, float] = {}
        for r in self._records:
            by_model[r.model] = by_model.get(r.model, 0.0) + r.estimated_cost_usd
            by_sku[r.sku] = by_sku.get(r.sku, 0.0) + r.estimated_cost_usd
        return {
            "total_usd": round(self._total, 4),
            "calls": len(self._records),
            "by_model_usd": {k: round(v, 4) for k, v in by_model.items()},
            "by_sku_usd": {k: round(v, 4) for k, v in by_sku.items()},
        }

    def _maybe_warn_tier(self) -> None:
        for tier in self.TIERS_USD:
            if self._total >= tier and tier not in self._tier_alerts_fired:
                self._tier_alerts_fired.add(tier)
                logger.warning(
                    "FLUX synthesis batch cost crossed $%.2f (total now $%.4f, calls=%d)",
                    tier,
                    self._total,
                    len(self._records),
                )


def log_stage(
    *,
    sku: str,
    view: str,
    attempt: int,
    stage: str,
    model: str,
    duration_ms: int = 0,
    request_id: str | None = None,
    output_url: str | None = None,
    **extra: Any,
) -> None:
    """Emit a structured log line for a stage event.

    Use directly when you don't need cost accounting; otherwise prefer
    CostTracker.add which writes the structured log AND tracks spend.
    """
    payload = {
        "event": "synthesis.stage",
        "sku": sku,
        "view": view,
        "attempt": attempt,
        "stage": stage,
        "model": model,
        "duration_ms": duration_ms,
        "request_id": request_id,
        "output_url": output_url,
        **extra,
    }
    logger.info("synthesis.stage %s", payload)
