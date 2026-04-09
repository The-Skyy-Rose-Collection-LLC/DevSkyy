"""
Human Review Gate — pause the graph for manual approval.

Submits generated images to the existing ApprovalQueueManager and
polls for a decision within a configurable timeout window.

If the approval queue is unavailable (import error, service error)
the gate defaults to "approve" with a warning log so production
pipelines are never blocked indefinitely.

Timeout defaults to "approve" as well — never block production.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_DEFAULT_POLL_INTERVAL = 5.0  # seconds between queue polls
_DEFAULT_TIMEOUT = 300.0  # 5 minutes


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
            item = asyncio.get_event_loop().run_until_complete(
                self._submit_async(manager, sku, image_path, job_id)
            )
            logger.info(
                "Submitted %s for human review: review_id=%s", sku, item.id
            )
            return item.id
        except Exception as exc:
            logger.warning(
                "Approval queue unavailable (%s) — auto-approving %s", exc, sku
            )
            # Return a sentinel that get_decision() will recognise as auto-approve
            return f"auto-approve:{job_id}"

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
                notes="Auto-approved: approval queue unavailable",
            )

        deadline = time.monotonic() + timeout
        try:
            manager = self._get_manager()
            while time.monotonic() < deadline:
                item = asyncio.get_event_loop().run_until_complete(
                    manager.get_item(review_id)
                )
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
            logger.warning(
                "Error polling approval queue (%s) — defaulting to approve", exc
            )
            return ReviewDecision(
                review_id=review_id,
                decision="approve",
                reviewer="system",
                notes=f"Auto-approved due to queue error: {exc}",
            )

        # Timeout reached
        logger.warning(
            "Human review timeout after %.0fs for review_id=%s — defaulting to approve",
            timeout,
            review_id,
        )
        return ReviewDecision(
            review_id=review_id,
            decision="timeout",
            reviewer="system",
            notes=f"Timed out after {timeout:.0f}s — auto-approved",
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
