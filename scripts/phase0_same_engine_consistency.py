"""Phase 0.2 — same-engine consistency: local TRELLIS vs hosted TRELLIS.

Closes the spec's unverified "identical fidelity profile" claim. If local-vs-
hosted similarity on the identical input clears the bar, hosted fallback is
allowed as transparent overflow; otherwise it keeps full human sign-off.
GPU + paid dispatch is STOP-AND-SHOW gated.
"""

from __future__ import annotations

import sys

CONSISTENCY_BAR = 0.95


def consistency_verdict(local_vs_hosted_score: float, bar: float = CONSISTENCY_BAR) -> dict:
    allowed = local_vs_hosted_score >= bar
    return {
        "score": round(local_vs_hosted_score, 4),
        "bar": bar,
        "transparent_overflow_allowed": allowed,
        "policy": (
            "hosted == local; transparent overflow permitted"
            if allowed
            else "hosted output diverges; hosted fallback requires human sign-off"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    print(
        "Same-engine consistency requires GPU + paid dispatch (local + hosted "
        "TRELLIS on br-001). Run under STOP-AND-SHOW; pass the two render paths "
        "to consistency_verdict() with a DINOv2 score from fidelity.metrics."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
