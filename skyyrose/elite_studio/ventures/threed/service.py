"""Tenant-scoped replica path: generate -> fidelity gate -> approval.

Composes the existing ThreeDPipeline engine with the platform fidelity gate +
approval queue. Verdict routing: REJECT -> bounded regen then escalate;
HUMAN_QUEUE / PASS_PENDING_HUMAN -> enqueue for human sign-off. Delivery to the
canonical product tree happens ONLY after a human approves (separate step).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from skyyrose.elite_studio.platform.approval import ApprovalQueue
from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str, str], dict]  # (image_path, sku) -> result dict
EvaluateFn = Callable[[str, str, str], FidelityReport]  # (tenant_id, sku, mesh_path) -> report


@dataclass(frozen=True)
class ReplicaOutcome:
    tenant_id: str
    sku: str
    status: str  # generated | rejected | queued_for_human | engine_failed
    report_path: str = ""
    approval_id: str = ""
    delivered_path: str = ""  # populated only after human approval (separate step)


def run_replica(
    *,
    tenant_id: str,
    sku: str,
    source_image: str,
    generate_fn: GenerateFn,
    evaluate_fn: EvaluateFn,
    report_base: Path,
    approval_dir: Path,
    max_attempts: int = 2,
) -> ReplicaOutcome:
    last_report_path = ""
    for _attempt in range(1, max_attempts + 1):
        result = generate_fn(source_image, sku)
        mesh_path = str(result.get("local_path", ""))
        if not mesh_path or result.get("status") != "completed":
            return ReplicaOutcome(tenant_id, sku, status="engine_failed")

        report = evaluate_fn(tenant_id, sku, mesh_path)
        last_report_path = str(report.persist(base=report_base, suffix=f"_attempt{_attempt}"))

        if report.verdict is FidelityVerdict.REJECT:
            # Bounded regen: threshold is FIXED across attempts. Retry is honest
            # only because the front has ground truth; exhausting attempts
            # escalates (status 'rejected') — never auto-ships a best-of-failed.
            continue

        queue = ApprovalQueue(store_dir=approval_dir)
        rec = queue.enqueue(tenant_id=tenant_id, sku=sku, report_path=last_report_path)
        return ReplicaOutcome(
            tenant_id,
            sku,
            status="queued_for_human",
            report_path=last_report_path,
            approval_id=rec.id,
        )

    return ReplicaOutcome(tenant_id, sku, status="rejected", report_path=last_report_path)


def _trellis_generate_fn() -> GenerateFn:
    """Build a generate_fn backed by the local self-hosted TRELLIS engine."""
    import asyncio

    from agents.trellis_agent import TrellisAgent

    agent = TrellisAgent()

    def _gen(image_path: str, sku: str) -> dict:
        return asyncio.run(agent.image_to_3d(image_path=image_path, product_name=sku))

    return _gen


def _gate_evaluate_fn(tenant) -> EvaluateFn:
    """Build an evaluate_fn backed by the fidelity gate's full evaluate()."""
    from skyyrose.elite_studio.platform.fidelity import gate

    def _eval(tenant_id: str, sku: str, mesh_path: str) -> FidelityReport:
        return gate.evaluate(tenant, sku, mesh_path)

    return _eval


def default_replica_runner(
    *,
    tenant,
    sku: str,
    source_image: str,
    generate_fn: GenerateFn | None = None,
    evaluate_fn: EvaluateFn | None = None,
    report_base: Path | None = None,
    approval_dir: Path | None = None,
) -> ReplicaOutcome:
    """Production runner: real local-TRELLIS engine + fidelity gate via run_replica.

    Resolved lazily by `platform.service.generate_3d`. The seams (generate_fn,
    evaluate_fn, dirs) are injectable so the wiring is testable without GPU; the
    defaults use the real engine + gate (gated-integration).
    """
    from skyyrose.elite_studio.config import OUTPUT_DIR

    base = report_base or (Path(OUTPUT_DIR) / "fidelity")
    return run_replica(
        tenant_id=tenant.id,
        sku=sku,
        source_image=source_image,
        generate_fn=generate_fn or _trellis_generate_fn(),
        evaluate_fn=evaluate_fn or _gate_evaluate_fn(tenant),
        report_base=base,
        approval_dir=approval_dir or (base / "approvals"),
    )
