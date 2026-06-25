"""
Human Review Gate — pause the graph for manual approval.

Submits generated images to the existing ApprovalQueueManager and
polls for a decision within a configurable timeout window.

Failure mode policy (changed 2026-05-25):
    Error and timeout paths default to ``reject`` so a broken queue
    cannot silently approve every image (the previous "auto-approve
    on failure" behavior turned the quality gate into a no-op under
    any failure condition).

    Operators who explicitly want the legacy "never block production"
    behavior must set ``SKYYROSE_AUTO_CONFIRM=1`` in the environment.
    That flag tells the gate to default to approve on queue errors
    and timeouts. Without it, fail-safe = reject.

Concurrency note: ``submit_for_review`` and ``get_decision`` are
synchronous methods that bridge into the async ApprovalQueueManager.
They are called from sync graph nodes that themselves run inside an
asyncio loop, so calling ``asyncio.run`` directly would raise
``RuntimeError: asyncio.run() cannot be called from a running event
loop``. ``_run_sync_safe`` detects the running-loop case and dispatches
the coroutine in a worker thread to avoid the nesting violation.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import time
from collections.abc import Awaitable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_DEFAULT_POLL_INTERVAL = 5.0  # seconds between queue polls
_DEFAULT_TIMEOUT = 300.0  # 5 minutes


def _auto_confirm_enabled() -> bool:
    """True when operators have explicitly opted into auto-approve-on-failure."""
    return os.environ.get("SKYYROSE_AUTO_CONFIRM", "").strip().lower() in {"1", "true", "yes"}


def _run_sync_safe[T](coro: Awaitable[T]) -> T:
    """Run an async coroutine from a sync caller, regardless of loop state.

    When no event loop is running, ``asyncio.run`` is safe. When a loop is
    already running (graph nodes invoke this gate via ``run_sync`` which
    drives its own loop), nesting ``asyncio.run`` raises ``RuntimeError``;
    we dispatch the coroutine into a worker thread so it gets its own loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


@dataclass(frozen=True)
class ReviewDecision:
    """Decision returned by the human reviewer (or timeout/fallback)."""

    review_id: str
    decision: str  # "approve" | "reject" | "timeout"
    reviewer: str  # reviewer ID or "system" for auto decisions
    notes: str = ""


class HumanReviewGate:
    """Pauses the graph for human approval using the existing approval queue.

    Attributes:
        poll_interval: Seconds between polls when waiting for decision.
        _manager: ApprovalQueueManager instance (lazy-loaded).
    """

    def __init__(self, poll_interval: float = _DEFAULT_POLL_INTERVAL) -> None:
        self._poll_interval = poll_interval
        self._manager = None  # lazy-loaded on first use

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_for_review(self, sku: str, image_path: str, job_id: str) -> str:
        """Submit an image for human review.

        Creates an approval queue item and returns the review ID for
        subsequent polling via get_decision().

        Args:
            sku: Product SKU (used as asset_id and product_id).
            image_path: Absolute path to the generated image.
            job_id: Pipeline job identifier for correlation.

        Returns:
            review_id string to pass to get_decision().
        """
        try:
            manager = self._get_manager()
            item = _run_sync_safe(self._submit_async(manager, sku, image_path, job_id))
            logger.info("Submitted %s for human review: review_id=%s", sku, item.id)
            return item.id
        except Exception as exc:
            # The legacy "auto-approve on queue error" behavior is now
            # opt-in (SKYYROSE_AUTO_CONFIRM=1) so a broken queue cannot
            # silently approve every image.
            if _auto_confirm_enabled():
                logger.warning(
                    "Approval queue unavailable (%s) — SKYYROSE_AUTO_CONFIRM=1, auto-approving %s",
                    exc,
                    sku,
                )
                return f"auto-approve:{job_id}"
            logger.error(
                "Approval queue unavailable (%s) — fail-safe rejecting %s "
                "(set SKYYROSE_AUTO_CONFIRM=1 to revert to auto-approve)",
                exc,
                sku,
            )
            return f"auto-reject:{job_id}:{type(exc).__name__}"

    def get_decision(
        self,
        review_id: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> ReviewDecision:
        """Poll for a human review decision.

        Blocks until the reviewer acts or timeout is reached.
        On timeout: returns decision="timeout" which the caller maps to approve.
        If review_id starts with "auto-approve:" returns immediate approve.

        Args:
            review_id: ID returned by submit_for_review().
            timeout: Maximum seconds to wait. Defaults to 300 (5 minutes).

        Returns:
            ReviewDecision with decision in {"approve", "reject", "timeout"}.
        """
        if review_id.startswith("auto-approve:"):
            return ReviewDecision(
                review_id=review_id,
                decision="approve",
                reviewer="system",
                notes="Auto-approved: SKYYROSE_AUTO_CONFIRM=1 + queue unavailable",
            )
        if review_id.startswith("auto-reject:"):
            return ReviewDecision(
                review_id=review_id,
                decision="reject",
                reviewer="system",
                notes=f"Fail-safe rejected: {review_id.split(':', 2)[-1]}",
            )

        deadline = time.monotonic() + timeout
        try:
            manager = self._get_manager()
            while time.monotonic() < deadline:
                item = _run_sync_safe(manager.get_item(review_id))
                decision = self._map_status(item.status.value)
                if decision in ("approve", "reject"):
                    return ReviewDecision(
                        review_id=review_id,
                        decision=decision,
                        reviewer=item.reviewed_by or "system",
                        notes=item.review_notes or "",
                    )
                time.sleep(self._poll_interval)
        except Exception as exc:
            # Default to reject so a broken queue can never silently approve.
            # Auto-approve-on-error is opt-in via SKYYROSE_AUTO_CONFIRM=1.
            if _auto_confirm_enabled():
                logger.warning(
                    "Error polling approval queue (%s) — SKYYROSE_AUTO_CONFIRM=1, "
                    "defaulting to approve",
                    exc,
                )
                return ReviewDecision(
                    review_id=review_id,
                    decision="approve",
                    reviewer="system",
                    notes=f"Auto-approved due to queue error (opt-in): {exc}",
                )
            logger.error(
                "Error polling approval queue (%s) — fail-safe rejecting "
                "(set SKYYROSE_AUTO_CONFIRM=1 to revert)",
                exc,
            )
            return ReviewDecision(
                review_id=review_id,
                decision="reject",
                reviewer="system",
                notes=f"Fail-safe reject due to queue error: {exc}",
            )

        # Timeout reached — default to reject unless explicit opt-in.
        if _auto_confirm_enabled():
            logger.warning(
                "Human review timeout after %.0fs for review_id=%s — "
                "SKYYROSE_AUTO_CONFIRM=1, defaulting to approve",
                timeout,
                review_id,
            )
            return ReviewDecision(
                review_id=review_id,
                decision="timeout",
                reviewer="system",
                notes=f"Timed out after {timeout:.0f}s — auto-approved (opt-in)",
            )
        logger.error(
            "Human review timeout after %.0fs for review_id=%s — fail-safe rejecting "
            "(set SKYYROSE_AUTO_CONFIRM=1 to revert)",
            timeout,
            review_id,
        )
        return ReviewDecision(
            review_id=review_id,
            decision="reject",
            reviewer="system",
            notes=f"Fail-safe reject after {timeout:.0f}s timeout",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_manager(self):
        """Lazy-load the ApprovalQueueManager singleton."""
        if self._manager is None:
            from services.approval_queue_manager import get_approval_manager  # type: ignore[import]

            self._manager = get_approval_manager()
        return self._manager

    async def _submit_async(self, manager, sku: str, image_path: str, job_id: str):
        """Async helper to create approval item."""
        from services.approval_queue_manager import ApprovalItemCreate  # type: ignore[import]

        request = ApprovalItemCreate(
            asset_id=sku,
            job_id=job_id,
            original_url=image_path,
            enhanced_url=image_path,
            product_id=sku,
            product_name=sku,
            metadata={"source": "elite_studio_quality_gate", "image_path": image_path},
        )
        return await manager.create_item(request)

    @staticmethod
    def _map_status(status: str) -> str:
        """Map ApprovalStatus to decision string."""
        mapping = {
            "approved": "approve",
            "rejected": "reject",
            "pending": "pending",
            "revision_requested": "pending",
            "expired": "timeout",
        }
        return mapping.get(status, "pending")
