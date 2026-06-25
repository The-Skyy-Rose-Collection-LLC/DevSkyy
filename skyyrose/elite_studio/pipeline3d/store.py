"""File-based stage-level idempotency.

A job that dies at remesh must NOT re-bill image-to-3D + texture on retry.
Each completed stage result is persisted keyed by an input hash; resumed jobs
skip stages already present. One JSON file per input hash, stages as keys.

Phase 3 swaps this for the Redis-backed IdempotencyCache used by the async API;
the interface (has/get/put) is identical so callers are unaffected.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from .models import Artifact, Stage, StageResult

log = logging.getLogger(__name__)


class StageStore:
    """Persist and retrieve StageResults keyed by (input_hash, stage)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, input_hash: str) -> Path:
        return self._root / f"{input_hash}.json"

    def _load(self, input_hash: str) -> dict:
        p = self._path(input_hash)
        if not p.is_file():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            # Don't crash a resume on a corrupt/half-written record, but never lose
            # it silently — a swallowed record means already-paid stages re-bill.
            log.warning(
                "stage store unreadable at %s (%s) — treating as empty; "
                "completed stages may re-bill on resume",
                p,
                exc,
            )
            return {}

    def has(self, input_hash: str, stage: Stage) -> bool:
        return stage.value in self._load(input_hash)

    def get(self, input_hash: str, stage: Stage) -> StageResult | None:
        rec = self._load(input_hash).get(stage.value)
        if not rec:
            return None
        art = dict(rec["artifact"])
        art["path"] = Path(art["path"]) if art.get("path") else None
        return StageResult(
            stage=stage,
            artifact=Artifact(**art),
            cost_usd=rec["cost_usd"],
            duration_ms=rec["duration_ms"],
            cached=True,
        )

    def put(self, input_hash: str, result: StageResult) -> None:
        data = self._load(input_hash)
        art = asdict(result.artifact)
        art["path"] = str(art["path"]) if art["path"] is not None else None
        data[result.stage.value] = {
            "artifact": art,
            "cost_usd": result.cost_usd,
            "duration_ms": result.duration_ms,
        }
        self._path(input_hash).write_text(
            json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )


__all__ = ["StageStore"]
