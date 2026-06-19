"""ApprovalGate — STOP-AND-SHOW enforcement for irreversible/paid actions.

Per project CLAUDE.md: every paid API call, production write, or destructive
operation requires explicit confirmation. ApprovalGate produces ApprovalRequest
records, suspends the requesting process, and resumes only on approval.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    """Lifecycle of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class RiskLevel(StrEnum):
    """How dangerous the action is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(BaseModel):
    """A pending request for human approval before an action proceeds."""

    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    requester_pid: int
    action: str
    description: str
    risk: RiskLevel
    estimated_cost_usd: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


class ApprovalDecision(BaseModel):
    """The resolved outcome of an ApprovalRequest."""

    model_config = {"frozen": True}

    request_id: str
    status: ApprovalStatus
    approver: str | None = None
    reason: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_approved(self) -> bool:
        """True if the request was approved."""
        return self.status == ApprovalStatus.APPROVED


class ApprovalGate:
    """Suspends processes until a human decides on an ApprovalRequest.

    Usage:
        decision = await gate.request_and_wait(req, timeout_seconds=300)
        if not decision.is_approved:
            raise PermissionError(decision.reason)
    Operators call gate.approve(id) / gate.deny(id, reason) to resolve.
    """

    def __init__(self, *, max_resolved_cache: int = 1000) -> None:
        self._pending: dict[str, tuple[ApprovalRequest, asyncio.Future[ApprovalDecision]]] = {}
        self._resolved: dict[str, ApprovalDecision] = {}
        self._resolved_order: list[str] = []
        self._max_resolved_cache = max_resolved_cache
        self._lock = asyncio.Lock()
        self._auto_approve_risk: RiskLevel | None = None
        self._history: list[ApprovalDecision] = []

    def set_auto_approve(self, max_risk: RiskLevel | None) -> None:
        """Auto-approve requests at or below this risk level. None disables auto-approve."""
        self._auto_approve_risk = max_risk

    async def submit(self, request: ApprovalRequest) -> str:
        """Register a request. Returns the request id."""
        async with self._lock:
            loop = asyncio.get_running_loop()
            fut: asyncio.Future[ApprovalDecision] = loop.create_future()
            self._pending[request.id] = (request, fut)

        if self._should_auto_approve(request):
            await self.approve(request.id, approver="auto", reason="below auto-approve threshold")
        return request.id

    async def wait(
        self,
        request_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> ApprovalDecision:
        """Block until the request is decided. Optional timeout marks it EXPIRED."""
        async with self._lock:
            already = self._resolved.get(request_id)
            if already is not None:
                return already
            entry = self._pending.get(request_id)
        if entry is None:
            msg = f"Approval request {request_id} not found"
            raise KeyError(msg)
        _req, fut = entry
        try:
            return await asyncio.wait_for(asyncio.shield(fut), timeout=timeout_seconds)
        except TimeoutError:
            decision = ApprovalDecision(
                request_id=request_id,
                status=ApprovalStatus.EXPIRED,
                reason="timeout",
            )
            await self._resolve(request_id, decision)
            return decision

    async def request_and_wait(
        self,
        request: ApprovalRequest,
        *,
        timeout_seconds: float | None = None,
    ) -> ApprovalDecision:
        """Convenience: submit + wait in one call."""
        await self.submit(request)
        return await self.wait(request.id, timeout_seconds=timeout_seconds)

    async def approve(self, request_id: str, *, approver: str, reason: str | None = None) -> None:
        """Resolve a request as approved."""
        decision = ApprovalDecision(
            request_id=request_id,
            status=ApprovalStatus.APPROVED,
            approver=approver,
            reason=reason,
        )
        await self._resolve(request_id, decision)

    async def deny(self, request_id: str, *, approver: str = "operator", reason: str) -> None:
        """Resolve a request as denied."""
        decision = ApprovalDecision(
            request_id=request_id,
            status=ApprovalStatus.DENIED,
            approver=approver,
            reason=reason,
        )
        await self._resolve(request_id, decision)

    async def list_pending(self) -> list[ApprovalRequest]:
        """Return all currently pending requests."""
        async with self._lock:
            return [req for req, fut in self._pending.values() if not fut.done()]

    @property
    def history(self) -> list[ApprovalDecision]:
        """Read-only view of all decided requests."""
        return list(self._history)

    async def _resolve(self, request_id: str, decision: ApprovalDecision) -> None:
        async with self._lock:
            entry = self._pending.pop(request_id, None)
            if entry is None:
                return
            _req, fut = entry
            if not fut.done():
                fut.set_result(decision)
            self._resolved[request_id] = decision
            self._resolved_order.append(request_id)
            while len(self._resolved_order) > self._max_resolved_cache:
                old_id = self._resolved_order.pop(0)
                self._resolved.pop(old_id, None)
            self._history.append(decision)

    def _should_auto_approve(self, req: ApprovalRequest) -> bool:
        if self._auto_approve_risk is None:
            return False
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return levels.index(req.risk) <= levels.index(self._auto_approve_risk)
