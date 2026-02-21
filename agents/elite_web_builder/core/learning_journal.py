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
        Create a single-line rule string encoding the mistake and its correction for agent prompt injection.
        
        Returns:
            rule (str): A formatted rule in the form "RULE: Do NOT {mistake}. INSTEAD: {correct}".
        """
        return f"RULE: Do NOT {self.mistake}. INSTEAD: {self.correct}"


class LearningJournal:
    """Accumulates mistake→rule pairs and persists to JSON."""

    def __init__(self, path: Path | None = None) -> None:
        """
        Initialize the LearningJournal and optionally load existing entries from disk.
        
        Parameters:
            path (Path | None): Filesystem path for persisting and loading journal data. If provided and the file exists, entries are loaded from that JSON file; if None, the journal operates in-memory only.
        """
        self._path = path
        self._entries: list[LearningEntry] = []
        if self._path and self._path.exists():
            self._load()

    @property
    def entries(self) -> list[LearningEntry]:
        """
        Provide a read-only copy of the stored learning entries.
        
        Returns:
            list[LearningEntry]: A new list containing the current LearningEntry objects; modifying this list does not alter the journal's internal entries.
        """
        return list(self._entries)

    def add_entry(self, entry: LearningEntry) -> None:
        """
        Add a learning entry to the journal.
        
        Appends the provided LearningEntry to the journal's entries and, if a persistence path was configured, writes the updated entries to disk.
        
        Parameters:
            entry (LearningEntry): The learning entry describing a mistake and its correction.
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
        Collects injection rules applicable to the specified agent.
        
        Parameters:
            agent (str): Identifier of the target agent to filter rules for.
        
        Returns:
            list[str]: Rule strings for entries whose `agent` matches the given agent or is "all".
        """
        rules = []
        for entry in self._entries:
            if entry.agent == agent or entry.agent == "all":
                rules.append(entry.to_rule())
        return rules

    def _load(self) -> None:
        """
        Load stored learning entries from the configured JSON file into the journal's internal entries list.
        
        If the file contains a top-level "entries" list, each item is used to construct a LearningEntry and replace the current entries. If JSON parsing fails or the expected structure is missing, a warning is logged and existing entries are left unchanged.
        """
        try:
            data = json.loads(self._path.read_text())
            self._entries = [LearningEntry(**e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to load learning journal: %s", exc)

    def _save(self) -> None:
        """
        Persist current entries to the configured JSON file path.
        
        Serializes the internal entries list to a JSON object with an "entries" key (each entry converted via dataclass asdict), ensures parent directories exist, and writes formatted JSON to the configured path, overwriting any existing file.
        """
        data = {"entries": [asdict(e) for e in self._entries]}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2))