"""Tenant-scoped 3D generation orchestrator (public entry point).

resolve tenant -> probe capability (refuse on red, zero spend) -> on
green+generate, delegate to the venture replica runner (generate -> fidelity
gate -> approval). No silent fallback: unknown tenant, red capability, and
missing source image all produce honest hard-states. The replica runner is
injectable for testing; the real one is resolved lazily so this module has no
import-time dependency on the venture wiring.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from skyyrose.elite_studio.platform.capability import CapabilityMatrix
from skyyrose.elite_studio.platform.tenancy import Tenant, TenantRegistry, UnknownTenantError

logger = logging.getLogger(__name__)

REQUIRED_CAPS = ("catalog", "reference_store", "fidelity_scorer", "engine_local")


class _Outcome(Protocol):
    status: str
    report_path: str
    approval_id: str


ReplicaRunner = Callable[..., _Outcome]


@dataclass(frozen=True)
class GenerationResult:
    tenant_id: str
    sku: str
    status: str
    report_path: str = ""
    approval_id: str = ""


def _default_replica_runner(*, tenant: Tenant, sku: str, source_image: str) -> _Outcome:
    """Lazily resolve the real venture replica runner (avoids import cycle)."""
    from skyyrose.elite_studio.ventures.threed.service import default_replica_runner

    return default_replica_runner(tenant=tenant, sku=sku, source_image=source_image)


def generate_3d(
    tenant_id: str,
    sku: str,
    *,
    source_image: str | None = None,
    generate: bool = False,
    registry: TenantRegistry | None = None,
    matrix: CapabilityMatrix | None = None,
    replica_runner: ReplicaRunner | None = None,
) -> GenerationResult:
    registry = registry or TenantRegistry.default()
    try:
        tenant = registry.get(tenant_id)
    except UnknownTenantError:
        return GenerationResult(tenant_id, sku, status="unknown_tenant")

    probed = (matrix or CapabilityMatrix(tenant)).probe()
    if not probed.required_ok(REQUIRED_CAPS):
        red = [s.name for s in probed.statuses if not s.ok]
        logger.info("generate_3d refused: red caps %s", red)
        return GenerationResult(tenant_id, sku, status="capability_unavailable")

    if not generate:
        return GenerationResult(tenant_id, sku, status="not_requested")

    if not source_image:
        return GenerationResult(tenant_id, sku, status="missing_source_image")

    runner = replica_runner or _default_replica_runner
    outcome = runner(tenant=tenant, sku=sku, source_image=source_image)
    return GenerationResult(
        tenant_id,
        sku,
        status=outcome.status,
        report_path=outcome.report_path,
        approval_id=outcome.approval_id,
    )
