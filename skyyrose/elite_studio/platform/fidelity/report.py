"""FidelityReport — the audit trail behind '100% replica'.

Persisted per asset, tenant-namespaced. Nothing delivers without one + a human
approval. Records every visible-face score, which angles were verified vs
inferred, hidden-face violations, and the regeneration attempt count.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path


class FidelityVerdict(StrEnum):
    PASS_PENDING_HUMAN = "pass_pending_human"  # visible passed, hidden in-range
    HUMAN_QUEUE = "human_queue"  # visible passed, hidden flagged
    REJECT = "reject"  # visible failed


@dataclass(frozen=True)
class FidelityReport:
    tenant_id: str
    sku: str
    mesh_path: str
    verdict: FidelityVerdict
    composite_by_angle: dict[str, float]
    verified_angles: tuple[str, ...]
    inferred_angles: tuple[str, ...]
    violations: tuple[str, ...]
    attempts: int
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["verified_angles"] = list(self.verified_angles)
        d["inferred_angles"] = list(self.inferred_angles)
        d["violations"] = list(self.violations)
        return d

    def persist(self, base: Path, *, suffix: str = "") -> Path:
        """Write to <base>/<tenant>/<sku>/fidelity_report{suffix}.json.

        `suffix` (e.g. "_attempt2") preserves each regeneration attempt's
        report instead of clobbering — the audit trail keeps every try's
        scores, as the spec requires.
        """
        out_dir = base / self.tenant_id / self.sku
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"fidelity_report{suffix}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
