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
        """
        Produce a rule string expressing the correction for inclusion in agent prompts.
        
        Returns:
            rule (str): A rule formatted as "RULE: Do NOT {mistake}. INSTEAD: {correct}".
        """
        return f"RULE: Do NOT {self.mistake}. INSTEAD: {self.correct}"


class LearningJournal:
    """Accumulates mistake→rule pairs and persists to JSON."""

    def __init__(self, path: Path | None = None) -> None:
        """
        Initialize the LearningJournal, optionally backing it with a JSON file.
        
        Parameters:
            path (Path | None): Optional filesystem path to a JSON file used for persistence.
                If provided and the file exists, existing entries are loaded from that file.
        """
        self._path = path
        self._entries: list[LearningEntry] = []
        if self._path and self._path.exists():
            self._load()

    @property
    def entries(self) -> list[LearningEntry]:
        """
        Return a shallow copy of the stored learning entries.
        
        Returns:
            list[LearningEntry]: A list of LearningEntry objects representing the current entries. Modifying the returned list does not affect the journal's internal state.
        """
        return list(self._entries)

    def add_entry(self, entry: LearningEntry) -> None:
        """
        Record a LearningEntry in the journal.
        
        Appends the provided entry to the journal's collection and, if a persistence path is configured, persists the updated entries to disk.
        
        Parameters:
            entry (LearningEntry): The learning record linking a mistake to its correction.
        """
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
        """
        Collect applicable learning-journal rules for a specific agent.
        
        Parameters:
            agent (str): Identifier of the agent to retrieve rules for; entries with agent equal to this value or "all" are considered.
        
        Returns:
            list[str]: Rule strings produced from matching LearningEntry instances.
        """
        rules = []
        for entry in self._entries:
            if entry.agent == agent or entry.agent == "all":
                rules.append(entry.to_rule())
        return rules

    def _load(self) -> None:
        """
        Load persisted learning entries from the configured JSON file into the journal.
        
        Reads the configured path and replaces the journal's internal entries list with
        LearningEntry instances constructed from the top-level "entries" list in the JSON.
        If the file contains invalid JSON or an unexpected structure, a warning is
        logged and the existing entries are left unchanged.
        """
        try:
            data = json.loads(self._path.read_text())
            self._entries = [LearningEntry(**e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to load learning journal: %s", exc)

    def _save(self) -> None:
        """
        Persist current learning entries to the configured JSON file.
        
        Writes a JSON object with a top-level "entries" list (each entry serialized as a dict) to self._path, creating parent directories as needed and overwriting any existing file.
        """
        data = {"entries": [asdict(e) for e in self._entries]}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))