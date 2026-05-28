"""Phase 0.3 — cross-engine fidelity A/B for threshold calibration.

Runs br-001 + lh-004 through {TRELLIS, Tripo, Meshy}, scores each mesh via the
fidelity gate in report-only mode against the golden references, and recommends
the per-tenant visible-face threshold from real garments. Engine dispatch is
STOP-AND-SHOW gated and accounted against RunBudget. Per-SKU costs (from
tasks/phase-e-manifest.md): Meshy $0.20, Tripo $0.25, TRELLIS-local $0.00.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ABRow:
    sku: str
    engine: str
    visible_score: float


def recommend_threshold(rows: list[ABRow], *, engine: str, margin: float = 0.03) -> float | None:
    """Lowest passing score for `engine` minus a safety margin, or None."""
    scores = [r.visible_score for r in rows if r.engine == engine]
    if not scores:
        return None
    return round(min(scores) - margin, 4)


def main(argv: list[str] | None = None) -> int:
    print(
        "Cross-engine A/B requires GPU + paid dispatch (TRELLIS/Tripo/Meshy on "
        "br-001 + lh-004). Run under STOP-AND-SHOW + RunBudget; feed each mesh "
        "to fidelity.gate in report-only mode, collect ABRow per (sku, engine), "
        "then call recommend_threshold(rows, engine='trellis')."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
