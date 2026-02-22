"""
Boris Cherny learning protocol + instinct extraction.

Every mistake an agent makes gets encoded as a permanent rule. Over time,
repeated mistakes get promoted to instincts — high-confidence rules that
are automatically injected into agent prompts.

Three learning mechanisms:
1. Immediate: mistake → rule (JournalEntry)
2. Session: repeated mistakes → instinct (Instinct, confidence scored)
3. Context: rules injected into agent prompts (generate_context)

Usage:
    journal = LearningJournal(storage_dir=Path("./instincts"))
    journal.add_entry(JournalEntry(mistake="...", correct="...", agent="..."))
    journal.save()
    instincts = journal.extract_instincts(min_occurrences=3)
    context = journal.generate_context(agent="frontend_dev")
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class JournalEntry:
    """A single mistake → correction record."""

    mistake: str
    correct: str
    agent: str
    story_id: str
    tags: list[str] | None = None
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "mistake": self.mistake,
            "correct": self.correct,
            "agent": self.agent,
            "story_id": self.story_id,
            "tags": self.tags or [],
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> JournalEntry:
        return JournalEntry(
            mistake=data["mistake"],
            correct=data["correct"],
            agent=data["agent"],
            story_id=data.get("story_id", ""),
            tags=data.get("tags", []),
            timestamp=data.get("timestamp"),
        )


@dataclass(frozen=True)
class Instinct:
    """A learned behavior extracted from repeated mistakes."""

    rule: str
    confidence: float  # 0.0 → 1.0
    source_count: int
    agent: str
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "agent": self.agent,
            "tags": list(self.tags),
        }


# ---------------------------------------------------------------------------
# Learning Journal
# ---------------------------------------------------------------------------

_JOURNAL_FILE = "journal.json"
_INSTINCTS_FILE = "instincts.json"


class LearningJournal:
    """
    Persistent learning journal with instinct extraction.

    Stores mistake→correction pairs, persists to JSON, and extracts
    high-confidence instincts from repeated patterns.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[JournalEntry] = []

    @property
    def entries(self) -> list[JournalEntry]:
        """Read-only access to entries."""
        return list(self._entries)

    def add_entry(self, entry: JournalEntry) -> None:
        """Add a new mistake→correction entry."""
        self._entries.append(entry)
        logger.info(
            "Journal entry added: agent=%s story=%s mistake=%s",
            entry.agent,
            entry.story_id,
            entry.mistake[:50],
        )

    def query(
        self,
        agent: str | None = None,
        tag: str | None = None,
    ) -> list[JournalEntry]:
        """Query entries by agent and/or tag."""
        results = self._entries

        if agent is not None:
            results = [e for e in results if e.agent == agent]

        if tag is not None:
            results = [
                e for e in results
                if e.tags is not None and tag in e.tags
            ]

        return results

    # -- Persistence --

    def save(self) -> None:
        """Save journal entries to disk."""
        data = [e.to_dict() for e in self._entries]
        path = self._storage_dir / _JOURNAL_FILE
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Journal saved: %d entries → %s", len(data), path)

    def load(self) -> None:
        """Load journal entries from disk."""
        path = self._storage_dir / _JOURNAL_FILE
        if not path.exists():
            logger.debug("No journal file at %s — starting fresh", path)
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._entries = [JournalEntry.from_dict(d) for d in data]
            logger.info("Journal loaded: %d entries from %s", len(self._entries), path)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to load journal from %s: %s", path, exc)

    # -- Instinct extraction --

    def extract_instincts(
        self,
        min_occurrences: int = 3,
    ) -> list[Instinct]:
        """
        Extract instincts from repeated mistake patterns.

        Groups entries by mistake text, and for groups with >= min_occurrences,
        creates an Instinct with confidence based on repetition count.

        Confidence formula:
            min(0.3 + 0.15 * (count - min_occurrences), 0.95)
        """
        # Group by normalized mistake text
        groups: dict[str, list[JournalEntry]] = {}
        for entry in self._entries:
            key = entry.mistake.strip().lower()
            groups.setdefault(key, []).append(entry)

        instincts: list[Instinct] = []
        for key, entries in groups.items():
            if len(entries) < min_occurrences:
                continue

            # Use the most recent correction as the rule
            latest = max(entries, key=lambda e: e.timestamp or "")
            confidence = min(0.3 + 0.15 * (len(entries) - min_occurrences), 0.95)

            # Collect all tags
            all_tags: set[str] = set()
            for e in entries:
                if e.tags:
                    all_tags.update(e.tags)

            # Determine primary agent
            agent_counts = Counter(e.agent for e in entries)
            primary_agent = agent_counts.most_common(1)[0][0]

            instincts.append(Instinct(
                rule=f"NEVER: {latest.mistake} → ALWAYS: {latest.correct}",
                confidence=confidence,
                source_count=len(entries),
                agent=primary_agent,
                tags=tuple(sorted(all_tags)),
            ))

        # Sort by confidence descending
        instincts.sort(key=lambda i: i.confidence, reverse=True)
        return instincts

    def save_instincts(self, instincts: list[Instinct]) -> None:
        """Save extracted instincts to disk."""
        data = [i.to_dict() for i in instincts]
        path = self._storage_dir / _INSTINCTS_FILE
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Instincts saved: %d → %s", len(data), path)

    # -- Context generation for agent prompts --

    def generate_context(self, agent: str) -> str:
        """
        Generate a learning context block for an agent's prompt.

        Returns a formatted string of past mistakes and corrections
        that the agent should be aware of.
        """
        agent_entries = self.query(agent=agent)

        if not agent_entries:
            return ""

        lines = ["## Learning Rules (from past mistakes)\n"]
        for entry in agent_entries:
            lines.append(f"- NEVER: {entry.mistake}")
            lines.append(f"  ALWAYS: {entry.correct}")
            lines.append("")

        return "\n".join(lines)
