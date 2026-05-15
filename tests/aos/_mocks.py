"""Mock agents and learning modules for AOS tests.

Duck-typed to match the EnhancedSuperAgent / SelfLearningModule surface that
SuperAgentAdapter + LearningHook depend on. No real LLM calls.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockHealEntry:
    """Mirrors HealAttempt's read-only surface used by the adapter."""

    category: Any
    action_taken: str | None = None
    succeeded: bool = False
    timestamp: str | None = None
    notes: str | None = None


@dataclass
class MockAgentResult:
    """Mirrors enough of AgentResult for the adapter to extract telemetry."""

    content: str = ""
    error: str | None = None
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class MockLearningModule:
    """Captures record_execution calls for assertion in tests."""

    def __init__(self, agent_type: str = "mock") -> None:
        self.agent_type = agent_type
        self.records: list[dict[str, Any]] = []

    def record_execution(self, **kwargs: Any) -> None:
        self.records.append(kwargs)


@dataclass
class MockSuperAgent:
    """In-memory SuperAgent stand-in.

    Configure via:
        - result: what execute() returns
        - raise_on_call: exception to throw on first N calls (then succeeds)
        - heal_entries_to_add: heal-journal entries to inject on each call
        - consecutive_failures, circuit_state: snapshot fields
    """

    agent_type: str = "mock_commerce"
    result: MockAgentResult = field(default_factory=MockAgentResult)
    raise_on_call: int = 0
    heal_entries_to_add: list[MockHealEntry] = field(default_factory=list)
    consecutive_failures: int = 0
    circuit_state: str = "closed"
    learning_module: MockLearningModule | None = None

    def __post_init__(self) -> None:
        self._heal_journal: OrderedDict[str, MockHealEntry] = OrderedDict()
        self._consecutive_failures = self.consecutive_failures
        self._circuit_state = self.circuit_state
        self._call_count = 0
        self._initialized = False
        self.executed_prompts: list[str] = []
        if self.learning_module is None:
            self.learning_module = MockLearningModule(agent_type=self.agent_type)

    async def initialize(self) -> None:
        self._initialized = True

    async def execute(self, prompt: str, **_kwargs: Any) -> MockAgentResult:
        self._call_count += 1
        self.executed_prompts.append(prompt)
        # Inject heal entries to simulate retries that happened internally
        for i, entry in enumerate(self.heal_entries_to_add):
            self._heal_journal[f"heal_{self._call_count}_{i}"] = entry
        if self.raise_on_call >= self._call_count:
            raise RuntimeError(f"simulated failure #{self._call_count}")
        return self.result
