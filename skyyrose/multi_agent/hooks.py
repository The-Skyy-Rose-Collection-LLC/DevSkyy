"""
Hook Callbacks — Real-time monitoring for the multi-agent system.

Hooks intercept agent events for:
  - Audit logging (every tool call)
  - Cost tracking (token usage)
  - Safety guardrails (block dangerous ops)
  - Progress reporting (agent activity)
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any

from claude_agent_sdk import HookMatcher

from .config import AUDIT_LOG_DIR

# ---------------------------------------------------------------------------
# Audit Logger — Logs every tool call to disk
# ---------------------------------------------------------------------------

_AUDIT_LOG = AUDIT_LOG_DIR / "audit.jsonl"


async def audit_tool_use(input_data: dict, tool_use_id: str, context: Any) -> dict:
    """Log every tool call to audit.jsonl for traceability."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    agent_id = input_data.get("agent_id", "main")

    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent_id,
        "tool": tool_name,
        "input_summary": _summarize_input(tool_input),
        "tool_use_id": tool_use_id,
    }

    with open(_AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {}


def _summarize_input(tool_input: dict) -> str:
    """Create a short summary of tool input for audit log."""
    if "file_path" in tool_input:
        return f"file: {tool_input['file_path']}"
    if "command" in tool_input:
        cmd = tool_input["command"]
        return f"cmd: {cmd[:80]}..." if len(cmd) > 80 else f"cmd: {cmd}"
    if "pattern" in tool_input:
        return f"pattern: {tool_input['pattern']}"
    if "sku" in tool_input:
        return f"sku: {tool_input['sku']}"
    # Generic: first key-value
    for k, v in tool_input.items():
        val = str(v)[:50]
        return f"{k}: {val}"
    return "(empty)"


# ---------------------------------------------------------------------------
# Safety Guard — Block destructive commands
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "DROP TABLE",
    "DROP DATABASE",
    "git push --force",
    "git reset --hard",
    "format c:",
    "mkfs.",
]


async def guard_bash(input_data: dict, tool_use_id: str, context: Any) -> dict:
    """Block known-destructive Bash commands."""
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in command.lower():
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked destructive command matching '{pattern}'"
                    ),
                }
            }

    return {}


# ---------------------------------------------------------------------------
# File Edit Logger — Track what files agents modify
# ---------------------------------------------------------------------------

_EDIT_LOG = AUDIT_LOG_DIR / "edits.jsonl"


async def log_file_edit(input_data: dict, tool_use_id: str, context: Any) -> dict:
    """Log file edits for review."""
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "unknown")
    agent_id = input_data.get("agent_id", "main")

    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent_id,
        "file": file_path,
        "action": input_data.get("tool_name", "edit"),
    }

    with open(_EDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {}


# ---------------------------------------------------------------------------
# Progress Reporter — Print activity to console
# ---------------------------------------------------------------------------


async def report_progress(input_data: dict, tool_use_id: str, context: Any) -> dict:
    """Print agent activity to console for visibility."""
    tool_name = input_data.get("tool_name", "unknown")
    agent_id = input_data.get("agent_id", "main")
    agent_type = input_data.get("agent_type", "")

    # Only report for subagents — main agent output is visible
    if agent_type:
        tool_input = input_data.get("tool_input", {})
        summary = _summarize_input(tool_input)
        print(f"  [{agent_type}] {tool_name}: {summary}")

    return {}


# ---------------------------------------------------------------------------
# Hook Configuration — Ready to plug into ClaudeAgentOptions
# ---------------------------------------------------------------------------

HOOKS = {
    "PreToolUse": [
        # Safety: block destructive Bash commands
        HookMatcher(matcher="Bash", hooks=[guard_bash]),
        # Audit: log ALL tool calls
        HookMatcher(matcher=".*", hooks=[audit_tool_use, report_progress]),
    ],
    "PostToolUse": [
        # Track file modifications
        HookMatcher(matcher="Edit|Write", hooks=[log_file_edit]),
    ],
}
