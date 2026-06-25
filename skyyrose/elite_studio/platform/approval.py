"""Human approval queue — the mandatory gate before any delivery.

File-backed JSON store (Phase 1 logical isolation; a DB-backed queue is a
later phase). No asset is promoted to the canonical product tree until a
record here is 'approved'.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Record IDs are uuid4().hex[:12] (12 lowercase hex). Validate before any
# filesystem interpolation — record_id can cross an API boundary in later
# phases, so reject anything that could escape the store dir (path traversal).
_ID_RE = re.compile(r"^[a-f0-9]{12}$")


@dataclass(frozen=True)
class ApprovalRecord:
    id: str
    tenant_id: str
    sku: str
    report_path: str
    status: str  # pending | approved | rejected
    reviewer: str = ""
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def with_status(self, status: str, *, reviewer: str = "", reason: str = "") -> ApprovalRecord:
        return ApprovalRecord(
            id=self.id,
            tenant_id=self.tenant_id,
            sku=self.sku,
            report_path=self.report_path,
            status=status,
            reviewer=reviewer,
            reason=reason,
            created_at=self.created_at,
        )


class ApprovalQueue:
    def __init__(self, store_dir: Path | str = "renders/fidelity/approvals") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, record_id: str) -> Path:
        if not _ID_RE.fullmatch(record_id):
            raise ValueError(f"invalid record_id: {record_id!r}")
        return self.store_dir / f"{record_id}.json"

    def _write(self, rec: ApprovalRecord) -> None:
        self._path(rec.id).write_text(json.dumps(asdict(rec), indent=2), encoding="utf-8")

    def enqueue(self, *, tenant_id: str, sku: str, report_path: str) -> ApprovalRecord:
        rec = ApprovalRecord(
            id=uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            sku=sku,
            report_path=report_path,
            status="pending",
        )
        self._write(rec)
        return rec

    def get(self, record_id: str) -> ApprovalRecord:
        return ApprovalRecord(**json.loads(self._path(record_id).read_text()))

    def approve(self, record_id: str, *, reviewer: str) -> ApprovalRecord:
        rec = self.get(record_id).with_status("approved", reviewer=reviewer)
        self._write(rec)
        return rec

    def reject(self, record_id: str, *, reviewer: str, reason: str) -> ApprovalRecord:
        rec = self.get(record_id).with_status("rejected", reviewer=reviewer, reason=reason)
        self._write(rec)
        return rec

    def pending(self, *, tenant_id: str) -> tuple[ApprovalRecord, ...]:
        out = []
        for p in sorted(self.store_dir.glob("*.json")):
            rec = ApprovalRecord(**json.loads(p.read_text()))
            if rec.tenant_id == tenant_id and rec.status == "pending":
                out.append(rec)
        return tuple(out)
