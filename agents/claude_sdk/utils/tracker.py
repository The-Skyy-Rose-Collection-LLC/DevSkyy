"""
DevSkyy Subagent Tracker
=========================

Adapted from research-agent/utils/subagent_tracker.py.
Integrates with DevSkyy's structlog for structured JSON logging
and writes tool call records to JSONL for telemetry.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ToolCallRecord:
    """Record of a single tool call."""

    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any | None = None
    error: str | None = None


@dataclass
class SubagentSession:
    """Information about a subagent execution session."""

    subagent_type: str
    parent_tool_use_id: str
    spawned_at: str
    description: str
    prompt_preview: str
    subagent_id: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


class DevSkyySubagentTracker:
    """Tracks subagent tool calls via SDK hooks with structlog integration.

    Writes structured JSONL to ``session_dir/tool_calls.jsonl`` and logs
    events through DevSkyy's ``structlog`` pipeline for observability.
    """

    def __init__(self, session_dir: Path | None = None) -> None:
        self.sessions: dict[str, SubagentSession] = {}
        self.tool_call_records: dict[str, ToolCallRecord] = {}
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = defaultdict(int)

        self._tool_log_file = None
        if session_dir:
            session_dir.mkdir(parents=True, exist_ok=True)
            tool_log_path = session_dir / "tool_calls.jsonl"
            self._tool_log_file = open(tool_log_path, "w", encoding="utf-8")

    # ------------------------------------------------------------------
    # Subagent spawn tracking
    # ------------------------------------------------------------------

    def register_subagent_spawn(
        self,
        tool_use_id: str,
        subagent_type: str,
        description: str,
        prompt: str,
    ) -> str:
        self.subagent_counters[subagent_type] += 1
        subagent_id = f"{subagent_type.upper()}-{self.subagent_counters[subagent_type]}"

        session = SubagentSession(
            subagent_type=subagent_type,
            parent_tool_use_id=tool_use_id,
            spawned_at=datetime.now().isoformat(),
            description=description,
            prompt_preview=prompt[:200] + "..." if len(prompt) > 200 else prompt,
            subagent_id=subagent_id,
        )
        self.sessions[tool_use_id] = session

        logger.info(
            "subagent_spawned",
            subagent_id=subagent_id,
            subagent_type=subagent_type,
            description=description,
        )
        return subagent_id

    def set_current_context(self, parent_tool_use_id: str | None) -> None:
        self._current_parent_id = parent_tool_use_id

    # ------------------------------------------------------------------
    # Hook callbacks
    # ------------------------------------------------------------------

    async def pre_tool_use_hook(self, hook_input: dict, tool_use_id: str, context: Any) -> dict:
        tool_name = hook_input["tool_name"]
        tool_input = hook_input["tool_input"]
        timestamp = datetime.now().isoformat()

        is_subagent = self._current_parent_id and self._current_parent_id in self.sessions

        if is_subagent:
            session = self.sessions[self._current_parent_id]
            record = ToolCallRecord(
                timestamp=timestamp,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_use_id=tool_use_id,
                subagent_type=session.subagent_type,
                parent_tool_use_id=self._current_parent_id,
            )
            session.tool_calls.append(record)
            self.tool_call_records[tool_use_id] = record

            logger.info(
                "subagent_tool_call",
                agent_id=session.subagent_id,
                tool=tool_name,
            )
            self._log_to_jsonl(
                {
                    "event": "tool_call_start",
                    "timestamp": timestamp,
                    "tool_use_id": tool_use_id,
                    "agent_id": session.subagent_id,
                    "agent_type": session.subagent_type,
                    "tool_name": tool_name,
                }
            )
        elif tool_name != "Task":
            logger.info("lead_agent_tool_call", tool=tool_name)
            self._log_to_jsonl(
                {
                    "event": "tool_call_start",
                    "timestamp": timestamp,
                    "tool_use_id": tool_use_id,
                    "agent_id": "LEAD_AGENT",
                    "tool_name": tool_name,
                }
            )

        return {"continue_": True}

    async def post_tool_use_hook(self, hook_input: dict, tool_use_id: str, context: Any) -> dict:
        tool_response = hook_input.get("tool_response")
        record = self.tool_call_records.get(tool_use_id)

        if record:
            record.tool_output = tool_response
            error = tool_response.get("error") if isinstance(tool_response, dict) else None
            if error:
                record.error = error
                logger.warning(
                    "subagent_tool_error",
                    tool=record.tool_name,
                    error=error,
                )

            self._log_to_jsonl(
                {
                    "event": "tool_call_complete",
                    "timestamp": datetime.now().isoformat(),
                    "tool_use_id": tool_use_id,
                    "tool_name": record.tool_name,
                    "success": error is None,
                }
            )

        return {"continue_": True}

    # ------------------------------------------------------------------
    # JSONL output
    # ------------------------------------------------------------------

    def _log_to_jsonl(self, entry: dict[str, Any]) -> None:
        if self._tool_log_file:
            self._tool_log_file.write(json.dumps(entry) + "\n")
            self._tool_log_file.flush()

    def close(self) -> None:
        if self._tool_log_file:
            self._tool_log_file.close()
            self._tool_log_file = None
