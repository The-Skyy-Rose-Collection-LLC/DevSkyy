"""Post-approval delivery: promote an approved mesh into the canonical tree.

Runs ONLY after a human approves (ApprovalRecord.status == 'approved'). Copies
the approved mesh to products/<tenant>/<sku>/v{n}/ (next version, never
overwriting). This is the only writer of the canonical product tree — no
unapproved asset can reach it.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from skyyrose.elite_studio.platform.approval import ApprovalQueue
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


class NotApprovedError(RuntimeError):
    """Raised when delivery is attempted for a non-approved record."""


def _next_version(sku_dir: Path) -> int:
    if not sku_dir.is_dir():
        return 1
    versions = [int(p.name[1:]) for p in sku_dir.glob("v*") if p.name[1:].isdigit()]
    return (max(versions) + 1) if versions else 1


def deliver_approved(
    approval_id: str,
    *,
    queue: ApprovalQueue,
    products_base: Path,
    registry: TenantRegistry | None = None,
) -> Path:
    """Promote the approved record's mesh into products/<tenant>/<sku>/v{n}/."""
    registry = registry or TenantRegistry.default()
    record = queue.get(approval_id)
    if record.status != "approved":
        raise NotApprovedError(f"record {approval_id} is {record.status!r}, not approved")
    tenant = registry.get(record.tenant_id)
    report = json.loads(Path(record.report_path).read_text())
    mesh_src = Path(report["mesh_path"])
    version = _next_version(products_base / tenant.id / record.sku)
    dest_dir = tenant.product_root(base=products_base, sku=record.sku, version=version)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / mesh_src.name
    shutil.copy2(mesh_src, dest)
    return dest
