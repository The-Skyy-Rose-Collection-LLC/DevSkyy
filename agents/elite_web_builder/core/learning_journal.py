"""
Learning Journal — Boris Cherny protocol for self-correcting behavior.

Every mistake gets encoded as a permanent rule that is injected
into future agent prompts to prevent recurrence.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LearningEntry:
    """A single mistake→correction entry."""

    mistake: str
    correct: str
    agent: str
    story_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    confidence: float = 0.9

    def to_rule(self) -> str:
        """Format as a rule string for injection into agent prompts."""
        return f"RULE: Do NOT {self.mistake}. INSTEAD: {self.correct}"


class LearningJournal:
    """Accumulates mistake→rule pairs and persists to JSON."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._entries: list[LearningEntry] = []
        if self._path and self._path.exists():
            self._load()

    @property
    def entries(self) -> list[LearningEntry]:
        """Read-only access to entries."""
        return list(self._entries)

    def add_entry(self, entry: LearningEntry) -> None:
        """Add a new learning entry."""
        self._entries.append(entry)
        logger.info(
            "Learning journal: %s → %s (agent=%s, story=%s)",
            entry.mistake,
            entry.correct,
            entry.agent,
            entry.story_id,
        )
        if self._path:
            self._save()

    def get_rules_for_agent(self, agent: str) -> list[str]:
        """Get all rules applicable to an agent."""
        rules = []
        for entry in self._entries:
            if entry.agent == agent or entry.agent == "all":
                rules.append(entry.to_rule())
        return rules

    def _load(self) -> None:
        """Load entries from JSON file."""
        try:
            data = json.loads(self._path.read_text())
            self._entries = [LearningEntry(**e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to load learning journal: %s", exc)

    def _save(self) -> None:
        """Save entries to JSON file."""
        data = {"entries": [asdict(e) for e in self._entries]}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))
