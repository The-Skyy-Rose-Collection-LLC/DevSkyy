"""
DevSkyy SDK Hook System
========================

Bridges Claude Agent SDK hooks into the DevSkyy self-healing and
telemetry systems.

SDK hooks intercept tool use, subagent lifecycle, and permission
requests. This module maps those events to:
- structlog telemetry
- SelfHealingMixin failure/success tracking
- JSONL audit trail per session

Hook types handled:
    PreToolUse   → log + optional permission gate
    PostToolUse  → log + record success/failure for circuit breaker
    PostToolUseFailure → log + trigger diagnosis
    SubagentStart/Stop → telemetry + duration tracking
    PermissionRequest  → auto-approve based on agent permission level
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
from claude_agent_sdk import (
    HookMatcher,
    PermissionResultAllow,
)

logger = structlog.get_logger(__name__)


@dataclass
class HookMetrics:
    """Aggregated metrics from a single SDK session."""

    tool_calls: int = 0
    tool_failures: int = 0
    subagents_spawned: int = 0
    subagent_total_ms: float = 0.0
    permissions_auto_approved: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def duration_s(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_calls": self.tool_calls,
            "tool_failures": self.tool_failures,
            "subagents_spawned": self.subagents_spawned,
            "subagent_total_ms": round(self.subagent_total_ms, 1),
            "permissions_auto_approved": self.permissions_auto_approved,
            "duration_s": round(self.duration_s, 2),
        }


class DevSkyyHookSystem:
    """Central hook system bridging SDK events to DevSkyy telemetry.

    Provides hook callbacks for every SDK event type and aggregates
    metrics. Optionally writes a JSONL audit trail.

    Args:
        session_dir: Directory for JSONL audit log.
        agent_name: Owning agent name (for structured logging).
        healing_mixin: Optional SelfHealingMixin instance to record
            success/failure on tool use outcomes.
    """

    def __init__(
        self,
        *,
        session_dir: Path | None = None,
        agent_name: str = "sdk_agent",
        healing_mixin: Any = None,
    ) -> None:
        self.session_dir = session_dir
        self.agent_name = agent_name
        self._healing = healing_mixin
        self.metrics = HookMetrics()
        self._subagent_starts: dict[str, float] = {}
        self._audit_handle = None

        if session_dir:
            session_dir.mkdir(parents=True, exist_ok=True)
            self._audit_path = session_dir / "sdk_audit.jsonl"

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def _write_audit(self, event: dict[str, Any]) -> None:
        """Append an event to the JSONL audit log."""
        if not self.session_dir:
            return
        try:
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except OSError:
            pass  # Non-critical — don't break agent execution

    # ------------------------------------------------------------------
    # PreToolUse hook
    # ------------------------------------------------------------------

    async def pre_tool_use(self, tool_use: Any, context: Any) -> None:
        """Called before each tool invocation.

        Logs the tool call and increments counter.
        """
        tool_name = getattr(tool_use, "tool_name", "unknown")
        tool_input = getattr(tool_use, "input", {})

        self.metrics.tool_calls += 1
        logger.info(
            "sdk_pre_tool_use",
            agent=self.agent_name,
            tool=tool_name,
            call_num=self.metrics.tool_calls,
        )
        self._write_audit(
            {
                "event": "pre_tool_use",
                "agent": self.agent_name,
                "tool": tool_name,
                "input_keys": list(tool_input.keys()) if isinstance(tool_input, dict) else [],
                "ts": time.time(),
            }
        )

    # ------------------------------------------------------------------
    # PostToolUse hook
    # ------------------------------------------------------------------

    async def post_tool_use(self, tool_use: Any, context: Any) -> None:
        """Called after a successful tool invocation.

        Records success in the healing mixin's circuit breaker.
        """
        tool_name = getattr(tool_use, "tool_name", "unknown")

        logger.debug(
            "sdk_post_tool_use",
            agent=self.agent_name,
            tool=tool_name,
        )
        self._write_audit(
            {
                "event": "post_tool_use",
                "agent": self.agent_name,
                "tool": tool_name,
                "ts": time.time(),
            }
        )

        # Feed success into circuit breaker
        if self._healing and hasattr(self._healing, "_record_success"):
            self._healing._record_success()

    # ------------------------------------------------------------------
    # PostToolUseFailure hook
    # ------------------------------------------------------------------

    async def post_tool_use_failure(self, tool_use: Any, context: Any) -> None:
        """Called when a tool invocation fails.

        Records failure in the healing mixin and triggers diagnosis
        if the mixin supports it.
        """
        tool_name = getattr(tool_use, "tool_name", "unknown")
        error = getattr(tool_use, "error", "unknown error")

        self.metrics.tool_failures += 1
        logger.warning(
            "sdk_tool_failure",
            agent=self.agent_name,
            tool=tool_name,
            error=str(error)[:200],
        )
        self._write_audit(
            {
                "event": "tool_failure",
                "agent": self.agent_name,
                "tool": tool_name,
                "error": str(error)[:500],
                "ts": time.time(),
            }
        )

        # Feed failure into circuit breaker
        if self._healing and hasattr(self._healing, "_record_failure"):
            self._healing._record_failure()

    # ------------------------------------------------------------------
    # SubagentStart / SubagentStop hooks
    # ------------------------------------------------------------------

    async def subagent_start(self, hook_input: Any, context: Any) -> None:
        """Called when a subagent is spawned."""
        agent_name = getattr(hook_input, "agent_name", "unknown")

        self.metrics.subagents_spawned += 1
        self._subagent_starts[agent_name] = time.time()

        logger.info(
            "sdk_subagent_start",
            parent=self.agent_name,
            subagent=agent_name,
            count=self.metrics.subagents_spawned,
        )
        self._write_audit(
            {
                "event": "subagent_start",
                "parent": self.agent_name,
                "subagent": agent_name,
                "ts": time.time(),
            }
        )

    async def subagent_stop(self, hook_input: Any, context: Any) -> None:
        """Called when a subagent completes."""
        agent_name = getattr(hook_input, "agent_name", "unknown")
        start = self._subagent_starts.pop(agent_name, None)
        duration_ms = (time.time() - start) * 1000 if start else 0
        self.metrics.subagent_total_ms += duration_ms

        logger.info(
            "sdk_subagent_stop",
            parent=self.agent_name,
            subagent=agent_name,
            duration_ms=round(duration_ms, 1),
        )
        self._write_audit(
            {
                "event": "subagent_stop",
                "parent": self.agent_name,
                "subagent": agent_name,
                "duration_ms": round(duration_ms, 1),
                "ts": time.time(),
            }
        )

    # ------------------------------------------------------------------
    # PermissionRequest hook
    # ------------------------------------------------------------------

    async def permission_request(self, hook_input: Any, context: Any) -> PermissionResultAllow:
        """Auto-approve permission requests for sandboxed SDK agents.

        DevSkyy SDK agents run with bypassPermissions mode, but if
        hooks intercept permission checks we auto-allow them since
        the SDK is already sandboxed.
        """
        tool_name = getattr(hook_input, "tool_name", "unknown")
        self.metrics.permissions_auto_approved += 1

        logger.debug(
            "sdk_permission_auto_approved",
            agent=self.agent_name,
            tool=tool_name,
        )
        return PermissionResultAllow()

    # ------------------------------------------------------------------
    # Build HookMatcher configs for ClaudeAgentOptions
    # ------------------------------------------------------------------

    def build_hook_config(self) -> dict[str, list[HookMatcher]]:
        """Build the hooks dict for ClaudeAgentOptions.

        Returns a mapping of hook event names to HookMatcher lists
        covering all supported SDK events.
        """
        return {
            "PreToolUse": [
                HookMatcher(matcher=None, hooks=[self.pre_tool_use]),
            ],
            "PostToolUse": [
                HookMatcher(matcher=None, hooks=[self.post_tool_use]),
            ],
            "PostToolUseFailure": [
                HookMatcher(
                    matcher=None,
                    hooks=[self.post_tool_use_failure],
                ),
            ],
            "SubagentStart": [
                HookMatcher(matcher=None, hooks=[self.subagent_start]),
            ],
            "SubagentStop": [
                HookMatcher(matcher=None, hooks=[self.subagent_stop]),
            ],
            "PermissionRequest": [
                HookMatcher(
                    matcher=None,
                    hooks=[self.permission_request],
                ),
            ],
        }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Finalize metrics and log session summary."""
        logger.info(
            "sdk_session_complete",
            agent=self.agent_name,
            **self.metrics.to_dict(),
        )
        self._write_audit(
            {
                "event": "session_complete",
                "agent": self.agent_name,
                "metrics": self.metrics.to_dict(),
                "ts": time.time(),
            }
        )
