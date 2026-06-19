"""FineTuneBuffer — quality-gated accumulator for OpenAI fine-tuning traces.

Only reflections above quality_threshold are stored. FIFO eviction at max_capacity
is handled by deque(maxlen=N) — no explicit management needed.

JSONL format follows OpenAI's supervised fine-tuning schema:
    {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from aos.cognition.reflector import Reflection

_DEFAULT_QUALITY_THRESHOLD = 0.7
_DEFAULT_MAX_CAPACITY = 500


class FineTuneRecord(BaseModel):
    """A single fine-tuning example in OpenAI chat format."""

    model_config = {"frozen": True}

    messages: tuple[dict[str, str], ...]
    metadata: dict[str, Any] = Field(default_factory=dict)


class FineTuneBuffer:
    """Quality-gated ring buffer of fine-tuning records.

    Thread-safety: not thread-safe — designed for single-event-loop use.
    """

    def __init__(
        self,
        *,
        quality_threshold: float = _DEFAULT_QUALITY_THRESHOLD,
        max_capacity: int = _DEFAULT_MAX_CAPACITY,
    ) -> None:
        self.quality_threshold = quality_threshold
        self.max_capacity = max_capacity
        self._buffer: deque[FineTuneRecord] = deque(maxlen=max_capacity)

    @property
    def size(self) -> int:
        """Current number of buffered records."""
        return len(self._buffer)

    def add(self, reflection: Reflection) -> bool:
        """Add a reflection if it meets the quality threshold.

        Returns True when the record was accepted and buffered.
        """
        if reflection.quality_score < self.quality_threshold:
            return False
        self._buffer.append(_build_record(reflection))
        return True

    def export_jsonl(self, path: str | Path) -> int:
        """Write all buffered records to a JSONL file. Returns record count."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        records = list(self._buffer)
        with dest.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps({"messages": list(record.messages)}) + "\n")
        return len(records)

    def drain(self) -> list[FineTuneRecord]:
        """Return all buffered records and clear the buffer."""
        records = list(self._buffer)
        self._buffer.clear()
        return records


def _build_record(reflection: Reflection) -> FineTuneRecord:
    trace = reflection.trace
    result_str = str(trace.result) if trace.result is not None else ""
    messages: tuple[dict[str, str], ...] = (
        {"role": "system", "content": f"You are a {trace.agent_type} agent."},
        {"role": "user", "content": trace.prompt},
        {"role": "assistant", "content": result_str},
    )
    return FineTuneRecord(
        messages=messages,
        metadata={
            "agent_type": trace.agent_type,
            "quality_score": reflection.quality_score,
            "success": reflection.success,
            "failure_category": (
                reflection.failure_category.value if reflection.failure_category else None
            ),
        },
    )
