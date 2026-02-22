"""Tests for core/learning_journal.py — Boris Cherny protocol + instinct extraction."""

import json
import tempfile
from pathlib import Path

import pytest

from core.learning_journal import (
    Instinct,
    JournalEntry,
    LearningJournal,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def journal(tmp_path: Path) -> LearningJournal:
    return LearningJournal(storage_dir=tmp_path)


@pytest.fixture
def sample_entry() -> JournalEntry:
    return JournalEntry(
        mistake="Used #FFB6C1 for rose gold",
        correct="Rose gold is #B76E79 (from brand-variables.css)",
        agent="design_system",
        story_id="US-003",
        tags=["color", "brand"],
    )


# ---------------------------------------------------------------------------
# JournalEntry
# ---------------------------------------------------------------------------


class TestJournalEntry:
    def test_entry_creation(self, sample_entry: JournalEntry) -> None:
        assert sample_entry.mistake == "Used #FFB6C1 for rose gold"
        assert sample_entry.agent == "design_system"
        assert "color" in sample_entry.tags

    def test_entry_has_timestamp(self, sample_entry: JournalEntry) -> None:
        assert sample_entry.timestamp is not None
        assert isinstance(sample_entry.timestamp, str)

    def test_entry_to_dict(self, sample_entry: JournalEntry) -> None:
        d = sample_entry.to_dict()
        assert d["mistake"] == "Used #FFB6C1 for rose gold"
        assert d["correct"] == "Rose gold is #B76E79 (from brand-variables.css)"
        assert d["agent"] == "design_system"

    def test_entry_from_dict(self) -> None:
        data = {
            "mistake": "wrong import",
            "correct": "correct import",
            "agent": "backend_dev",
            "story_id": "US-010",
            "tags": ["imports"],
            "timestamp": "2026-02-20T12:00:00",
        }
        entry = JournalEntry.from_dict(data)
        assert entry.agent == "backend_dev"
        assert entry.story_id == "US-010"


# ---------------------------------------------------------------------------
# LearningJournal — add/query entries
# ---------------------------------------------------------------------------


class TestJournalOperations:
    def test_add_entry(self, journal: LearningJournal, sample_entry: JournalEntry) -> None:
        journal.add_entry(sample_entry)
        assert len(journal.entries) == 1

    def test_add_multiple_entries(self, journal: LearningJournal) -> None:
        for i in range(5):
            journal.add_entry(JournalEntry(
                mistake=f"Mistake {i}",
                correct=f"Correct {i}",
                agent="qa",
                story_id=f"US-{i:03d}",
            ))
        assert len(journal.entries) == 5

    def test_query_by_agent(self, journal: LearningJournal) -> None:
        journal.add_entry(JournalEntry(
            mistake="m1", correct="c1", agent="frontend_dev", story_id="US-001",
        ))
        journal.add_entry(JournalEntry(
            mistake="m2", correct="c2", agent="backend_dev", story_id="US-002",
        ))
        journal.add_entry(JournalEntry(
            mistake="m3", correct="c3", agent="frontend_dev", story_id="US-003",
        ))
        results = journal.query(agent="frontend_dev")
        assert len(results) == 2

    def test_query_by_tag(self, journal: LearningJournal) -> None:
        journal.add_entry(JournalEntry(
            mistake="m1", correct="c1", agent="design_system",
            story_id="US-001", tags=["color", "brand"],
        ))
        journal.add_entry(JournalEntry(
            mistake="m2", correct="c2", agent="design_system",
            story_id="US-002", tags=["typography"],
        ))
        results = journal.query(tag="color")
        assert len(results) == 1
        assert results[0].tags is not None and "color" in results[0].tags

    def test_query_empty(self, journal: LearningJournal) -> None:
        results = journal.query(agent="nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# Persistence — save/load
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_and_load(self, journal: LearningJournal, sample_entry: JournalEntry) -> None:
        journal.add_entry(sample_entry)
        journal.save()

        # Create a new journal pointing to same dir
        loaded = LearningJournal(storage_dir=journal._storage_dir)
        loaded.load()
        assert len(loaded.entries) == 1
        assert loaded.entries[0].mistake == sample_entry.mistake

    def test_save_creates_file(self, journal: LearningJournal, sample_entry: JournalEntry) -> None:
        journal.add_entry(sample_entry)
        journal.save()
        assert (journal._storage_dir / "journal.json").exists()

    def test_load_empty_dir(self, tmp_path: Path) -> None:
        journal = LearningJournal(storage_dir=tmp_path)
        journal.load()  # Should not crash
        assert len(journal.entries) == 0


# ---------------------------------------------------------------------------
# Instinct extraction
# ---------------------------------------------------------------------------


class TestInstinctExtraction:
    def test_extract_instincts_from_repeated_mistakes(self, journal: LearningJournal) -> None:
        """Same mistake 3+ times → instinct."""
        for i in range(3):
            journal.add_entry(JournalEntry(
                mistake="Forgot to validate input",
                correct="Always validate at boundaries",
                agent="backend_dev",
                story_id=f"US-{i:03d}",
                tags=["validation"],
            ))
        instincts = journal.extract_instincts(min_occurrences=3)
        assert len(instincts) >= 1
        # At exactly min_occurrences, confidence starts at 0.3 (tentative)
        assert instincts[0].confidence >= 0.3

    def test_extract_instincts_below_threshold(self, journal: LearningJournal) -> None:
        """Not enough repetitions → no instinct."""
        journal.add_entry(JournalEntry(
            mistake="One-time mistake",
            correct="One-time fix",
            agent="qa",
            story_id="US-001",
        ))
        instincts = journal.extract_instincts(min_occurrences=3)
        assert len(instincts) == 0

    def test_instinct_has_rule(self, journal: LearningJournal) -> None:
        for i in range(3):
            journal.add_entry(JournalEntry(
                mistake="Used hardcoded path",
                correct="Use config variable",
                agent="frontend_dev",
                story_id=f"US-{i:03d}",
                tags=["config"],
            ))
        instincts = journal.extract_instincts(min_occurrences=3)
        assert len(instincts) >= 1
        assert "hardcoded" in instincts[0].rule.lower() or "config" in instincts[0].rule.lower()


# ---------------------------------------------------------------------------
# Generate context for agent prompts
# ---------------------------------------------------------------------------


class TestContextGeneration:
    def test_generate_agent_context(self, journal: LearningJournal) -> None:
        journal.add_entry(JournalEntry(
            mistake="Used wrong API",
            correct="Use REST API v2",
            agent="backend_dev",
            story_id="US-001",
        ))
        context = journal.generate_context(agent="backend_dev")
        assert isinstance(context, str)
        assert "wrong API" in context or "REST API v2" in context

    def test_generate_context_empty(self, journal: LearningJournal) -> None:
        context = journal.generate_context(agent="backend_dev")
        assert isinstance(context, str)
        # Empty is fine — no rules yet
