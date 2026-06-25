"""Orchestration mode — a session-level standing-consent fan-out loop.

Refactored from Anthropic's "Build an orchestration mode" reference into the
DevSkyy house idiom: async ``AsyncAnthropic`` streaming, ``structlog``,
``llm.model_ids`` constants, and an ``asyncio`` fan-out (in
``orchestration_mode_tools``) rather than the reference's sync
``ThreadPoolExecutor``.

An orchestration mode is a session-level switch. When it is **on**, the agent
runs every substantive request at maximum effort and fans work out to parallel
subagents by default. When it is **off**, the same Workflow tool reverts to
per-request opt-in. The mode is built from three documented pieces, never an API
flag:

1. **Effort** — ``output_config={"effort": ...}``, defaulting to ``"xhigh"`` to
   match the house precedent in ``scripts/nano_banana/tournament.py``.
2. **Mode reminder** — a mid-conversation message placed *after* the user turn
   it applies to, so the static top-level ``system`` prefix never changes and
   the cached prefix stays intact. Transported today as a ``<system-reminder>``
   user turn (``role:"system"`` is next-opus only); the ``SYSTEM_ROLE`` seam is
   ready for when that lands.
3. **Standing consent** — written into ``WORKFLOW_TOOL``'s description.

Spec: docs/superpowers/specs/2026-06-01-orchestration-mode-design.html
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import structlog

try:
    from config import ANTHROPIC_API_KEY
except ImportError:  # pragma: no cover - standalone usage fallback
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

from anthropic import AsyncAnthropic

from llm.model_ids import ORCHESTRATOR_MODEL, SUBAGENT_MODEL
from orchestration.orchestration_mode_tools import (
    BASH_TOOL,
    WORKFLOW_TOOL,
    handle_bash_block,
    run_workflow,
)

logger = structlog.get_logger(__name__)


# The top-level system field is static for the whole session — never mutate it,
# or the cached prefix breaks. Mode state rides in the messages array instead.
SYSTEM_PROMPT = "You are a helpful general-purpose agent. Answer the user's request directly."

MODE_ENTER = (
    "Orchestration mode is on: optimize for the most exhaustive, correct answer rather "
    "than the fastest or cheapest one. Use the Workflow tool on every substantive task; "
    "token cost is not a constraint. See the Workflow tool's standing consent section and "
    "quality patterns. Work solo only on conversational or trivial turns."
)
MODE_REFRESH = (
    "Orchestration mode is still on. Use the Workflow tool; see its standing consent section."
)
MODE_EXIT = "Orchestration mode is off. The Workflow tool's standard opt-in rule applies again."


class ReminderTransport(StrEnum):
    """How a mid-conversation mode reminder is delivered."""

    USER_REMINDER = "user_reminder"  # runs today: a <system-reminder> user turn
    SYSTEM_ROLE = "system_role"  # next-opus: a true role:"system" message


@dataclass(frozen=True)
class ModeConfig:
    """Immutable knobs for the orchestration-mode loop.

    Models resolve from ``llm.model_ids`` so a roll-forward updates every caller.
    ``effort`` defaults to ``"xhigh"`` to match the shipping house precedent; the
    config seam lets it drop to ``"max"`` if an org loses next-opus access.
    """

    orchestrator_model: str = ORCHESTRATOR_MODEL
    subagent_model: str = SUBAGENT_MODEL
    effort: str = "xhigh"
    reminder_transport: ReminderTransport = ReminderTransport.USER_REMINDER
    max_tokens: int = 64000
    max_main_turns: int = 30
    max_subagent_turns: int = 15
    max_parallel_agents: int = 10
    turns_between_refreshers: int = 10
    bash_timeout_seconds: int = 60
    tool_result_max_chars: int = 8000


class ModeAgent:
    """An agent loop whose orchestration mode toggles via mid-conversation reminders.

    The Anthropic client is injectable so tests fake the boundary; in production
    it defaults to an ``AsyncAnthropic`` built from the configured key.
    """

    def __init__(
        self,
        model: str | None = None,
        config: ModeConfig | None = None,
        client: AsyncAnthropic | None = None,
        mode_on: bool = True,
    ) -> None:
        self.config = config or ModeConfig()
        self._model = model or self.config.orchestrator_model
        self._client = client or AsyncAnthropic(api_key=ANTHROPIC_API_KEY or None)
        self.mode_on = mode_on
        self.messages: list[dict[str, Any]] = []
        self._mode_announced = False
        self._exit_pending = False
        self._turns_since_reminder = 0

    def set_mode(self, mode_on: bool) -> None:
        """Turn the mode on or off. The notice is delivered with the next turn."""
        if mode_on == self.mode_on:
            return
        if mode_on:
            self._exit_pending = False
        elif self._mode_announced:
            self._exit_pending = True
        self.mode_on = mode_on

    def _due_reminder_texts(self) -> list[str]:
        """Reminder strings owed this turn (pure state machine).

        Emits the exit notice once on turn-off, the full mode text once on
        entry, or a one-line refresher every ``turns_between_refreshers`` turns.
        """
        due: list[str] = []
        if self._exit_pending:
            self._exit_pending = False
            self._mode_announced = False
            due.append(MODE_EXIT)
        if self.mode_on:
            if not self._mode_announced:
                self._mode_announced = True
                self._turns_since_reminder = 0
                due.append(MODE_ENTER)
            elif self._turns_since_reminder >= self.config.turns_between_refreshers:
                self._turns_since_reminder = 0
                due.append(MODE_REFRESH)
        return due

    def _build_user_messages(
        self, user_input: str, reminder_texts: list[str]
    ) -> list[dict[str, Any]]:
        """Attach due reminders to the user turn per the configured transport.

        The top-level ``system`` prefix never changes — reminders ride here. The
        Messages API is trained on alternating user/assistant turns, so
        ``USER_REMINDER`` folds reminders into the user turn's content as extra
        text blocks (not separate user messages, which would create consecutive
        user turns). ``SYSTEM_ROLE`` (newer SDK / next-opus) emits standalone
        ``role:"system"`` messages, which sit outside that alternation. Either
        way the cached prefix ahead of the reminder is left untouched.
        """
        if not reminder_texts:
            return [{"role": "user", "content": user_input}]
        if self.config.reminder_transport is ReminderTransport.SYSTEM_ROLE:
            messages: list[dict[str, Any]] = [{"role": "user", "content": user_input}]
            messages.extend({"role": "system", "content": text} for text in reminder_texts)
            return messages
        content: list[dict[str, Any]] = [{"type": "text", "text": user_input}]
        content.extend(
            {"type": "text", "text": f"<system-reminder>\n{text}\n</system-reminder>"}
            for text in reminder_texts
        )
        return [{"role": "user", "content": content}]

    async def turn(self, user_input: str) -> str:
        """Run one user turn, executing tool calls until the model stops."""
        # The reminder rides with the user turn it applies to (folded into its
        # content under USER_REMINDER, or as a trailing system message under
        # SYSTEM_ROLE), keeping the cached prefix ahead of it untouched.
        reminder_texts = self._due_reminder_texts()
        self.messages.extend(self._build_user_messages(user_input, reminder_texts))
        self._turns_since_reminder += 1

        for _ in range(self.config.max_main_turns):
            async with self._client.messages.stream(
                model=self._model,
                max_tokens=self.config.max_tokens,
                system=SYSTEM_PROMPT,
                thinking={"type": "adaptive"},
                output_config={"effort": self.config.effort},
                tools=[WORKFLOW_TOOL, BASH_TOOL],
                messages=self.messages,
            ) as stream:
                response = await stream.get_final_message()
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue
            if response.stop_reason != "tool_use":
                text = "".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                )
                if response.stop_reason == "max_tokens":
                    # Drop the truncated assistant turn so later turns don't build on it.
                    self.messages.pop()
                    text += "\n\n(warning: response was truncated at max_tokens)"
                return text

            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                if block.name == "Workflow":
                    payload = block.input or {}
                    output, is_error = await run_workflow(
                        self._client, payload.get("subtasks", []), self.config
                    )
                elif block.name == "bash":
                    output, is_error = await handle_bash_block(block, self.config)
                else:
                    output, is_error = f"unknown tool: {block.name}", True
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )
            self.messages.append({"role": "user", "content": tool_results})
        return "(hit the main loop turn limit before finishing)"
