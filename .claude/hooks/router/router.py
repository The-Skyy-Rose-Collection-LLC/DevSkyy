#!/usr/bin/env python3
"""DevSkyy task-aware resource router.

UserPromptSubmit hook. Reads the user prompt from stdin (Claude Code hook JSON),
matches against patterns in triggers.json, and emits an `additionalContext`
block recommending which skills/agents/plugins are relevant for the task.

This is NUDGE-ONLY. Claude can still invoke off-pack tools. The router exists
to bias selection toward the right subset and reduce skill-list noise.

Pattern matching:
  - First-match-wins (patterns ordered by specificity in triggers.json)
  - Case-insensitive
  - The `default` pattern (regex ".*") is a final catch-all

Hook contract:
  stdin  → JSON with at least {"prompt": "..."}
  stdout → JSON {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                        "additionalContext": "..."}}
  exit 0 always (non-blocking)

Failure modes (all silent, exit 0):
  - triggers.json missing → emit nothing
  - stdin malformed → emit nothing
  - regex error → skip that pattern, try next

@since 2026-05-26
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROUTER_DIR = Path(__file__).parent
TRIGGERS_FILE = ROUTER_DIR / "triggers.json"


def _load_triggers() -> dict:
    if not TRIGGERS_FILE.exists():
        return {"patterns": []}
    try:
        return json.loads(TRIGGERS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"patterns": []}


def _read_prompt() -> str:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return ""
    return str(payload.get("prompt", "") or payload.get("user_prompt", ""))


def _match_pattern(prompt: str, patterns: list[dict]) -> dict | None:
    for pat in patterns:
        regex_str = pat.get("regex", "")
        if not regex_str:
            continue
        try:
            if re.search(regex_str, prompt, re.IGNORECASE):
                return pat
        except re.error:
            continue
    return None


def _format_context(pat: dict) -> str:
    name = pat.get("name", "unknown")
    skills = pat.get("skills", [])
    agents = pat.get("agents", [])
    plugins = pat.get("plugins", [])

    if name == "default" and not skills and not agents and not plugins:
        return ""

    lines = [
        f"## Task Router → matched pattern: `{name}`",
        "",
        "Recommended resources for this task (use these FIRST; invoke others only if necessary):",
        "",
    ]

    if skills:
        lines.append(f"**Skills:** {', '.join(f'`{s}`' for s in skills)}")
    if agents:
        lines.append(f"**Agents:** {', '.join(f'`{a}`' for a in agents)}")
    if plugins:
        lines.append(f"**Plugins:** {', '.join(f'`{p}`' for p in plugins)}")

    lines.extend(
        [
            "",
            "_Router is nudge-only — override with explicit user request or genuine need._",
            "_Edit `.claude/hooks/router/triggers.json` to adjust patterns._",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    triggers = _load_triggers()
    patterns = triggers.get("patterns", [])
    if not patterns:
        return 0

    prompt = _read_prompt()
    if not prompt:
        return 0

    matched = _match_pattern(prompt, patterns)
    if not matched:
        return 0

    context = _format_context(matched)
    if not context:
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
