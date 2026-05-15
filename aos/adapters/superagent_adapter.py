"""SuperAgentAdapter — non-invasive wrapper around the existing EnhancedSuperAgent.

The adapter does NOT modify the wrapped agent. After execute() runs, it inspects
the agent's _heal_journal (from SelfHealingMixin) to extract retry telemetry and
emits structured records the kernel can audit.

Protocol the wrapped agent must satisfy (duck-typed):
    - agent.agent_type: str
    - async agent.execute(prompt: str, **kwargs) -> Any
    - agent._heal_journal: OrderedDict (optional)
    - agent._consecutive_failures: int (optional)
    - agent._circuit_state (optional)

Any of the optional attrs that are missing are tolerated — the adapter degrades
to "no telemetry" rather than failing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealJournalEntry(BaseModel):
    """A single retry/heal attempt extracted from the agent's journal."""

    model_config = {"frozen": True}

    category: str
    action_taken: str | None = None
    succeeded: bool = False
    timestamp: str | None = None
    notes: str | None = None


class AdapterRun(BaseModel):
    """Outcome of a single adapter.run() invocation."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    agent_type: str
    success: bool
    raw_result: Any | None = None
    error: str | None = None
    heal_journal: tuple[HealJournalEntry, ...] = ()
    consecutive_failures: int = 0
    circuit_state: str = "closed"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SuperAgentAdapter:
    """Wraps an existing SuperAgent instance for kernel-managed execution."""

    def __init__(self, agent: Any) -> None:
        self.agent = agent
        self._journal_snapshot_keys: set[str] = set()

    @property
    def agent_type(self) -> str:
        return getattr(self.agent, "agent_type", "unknown")

    async def initialize(self) -> None:
        """Call agent.initialize() if available (idempotent)."""
        if hasattr(self.agent, "initialize") and callable(self.agent.initialize):
            init_fn = self.agent.initialize
            if not getattr(self.agent, "_initialized", False):
                await init_fn()

    def _snapshot_journal_baseline(self) -> None:
        """Record current journal keys so consume_new_entries() returns only the new ones."""
        journal = getattr(self.agent, "_heal_journal", None)
        if journal is not None:
            self._journal_snapshot_keys = set(journal.keys())
        else:
            self._journal_snapshot_keys = set()

    def _consume_new_entries(self) -> tuple[HealJournalEntry, ...]:
        """Return heal-journal entries added since the last snapshot."""
        journal = getattr(self.agent, "_heal_journal", None)
        if journal is None:
            return ()
        new_keys = [k for k in journal.keys() if k not in self._journal_snapshot_keys]
        entries: list[HealJournalEntry] = []
        for key in new_keys:
            raw = journal[key]
            entries.append(
                HealJournalEntry(
                    category=getattr(
                        getattr(raw, "category", None),
                        "value",
                        str(getattr(raw, "category", "unknown")),
                    ),
                    action_taken=getattr(raw, "action_taken", None),
                    succeeded=getattr(raw, "succeeded", False),
                    timestamp=getattr(raw, "timestamp", None),
                    notes=getattr(raw, "notes", None),
                )
            )
        # Move baseline forward so next run() only returns its own new entries
        self._journal_snapshot_keys = set(journal.keys())
        return tuple(entries)

    async def run(self, prompt: str, **kwargs: Any) -> AdapterRun:
        """Run the agent and capture structured telemetry.

        Never raises — any exception is captured into AdapterRun.error.
        """
        await self.initialize()
        self._snapshot_journal_baseline()

        success = True
        raw_result: Any = None
        error: str | None = None

        try:
            raw_result = await self.agent.execute(prompt, **kwargs)
            agent_error = _read_error(raw_result)
            if agent_error is not None:
                success = False
                error = agent_error
        except Exception as exc:  # noqa: BLE001 — adapter is the catch-all boundary
            success = False
            error = f"{type(exc).__name__}: {exc}"

        return AdapterRun(
            agent_type=self.agent_type,
            success=success,
            raw_result=raw_result,
            error=error,
            heal_journal=self._consume_new_entries(),
            consecutive_failures=int(getattr(self.agent, "_consecutive_failures", 0) or 0),
            circuit_state=_read_circuit_state(self.agent),
            metadata=_extract_metadata(raw_result),
        )


def _read_error(result: Any) -> str | None:
    """Pull an error message from an AgentResult-like object if present."""
    if result is None:
        return None
    err = getattr(result, "error", None)
    if err:
        return str(err)
    if isinstance(result, dict):
        e = result.get("error")
        return str(e) if e else None
    return None


def _read_circuit_state(agent: Any) -> str:
    state = getattr(agent, "_circuit_state", None)
    if state is None:
        return "closed"
    return getattr(state, "value", str(state))


def _extract_metadata(result: Any) -> dict[str, Any]:
    """Pull stable metadata out of an AgentResult for the audit record."""
    if result is None:
        return {}
    if isinstance(result, dict):
        return {k: v for k, v in result.items() if k in {"cost_usd", "latency_ms", "iterations"}}
    metadata: dict[str, Any] = {}
    for field in ("cost_usd", "latency_ms", "iterations", "input_tokens", "output_tokens"):
        value = getattr(result, field, None)
        if value is not None:
            metadata[field] = value
    return metadata
