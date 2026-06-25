"""Tests for MemoryStore."""

from __future__ import annotations

import time

import pytest

from aos.memory.store import MemoryStore
from aos.memory.types import MemoryEntry, MemoryKeyError, MemoryNamespaceError


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


class TestWrite:
    def test_write_returns_memory_entry(self, store):
        entry = store.write("pid-1", "goal", "finish report")
        assert isinstance(entry, MemoryEntry)
        assert entry.key == "goal"
        assert entry.value == "finish report"
        assert entry.namespace == "pid-1"

    def test_write_sets_created_at(self, store):
        before = time.time()
        entry = store.write("pid-1", "k", "v")
        after = time.time()
        assert before <= entry.created_at <= after

    def test_write_no_ttl_gives_none_expires_at(self, store):
        entry = store.write("pid-1", "k", "v")
        assert entry.expires_at is None

    def test_write_with_ttl_sets_expires_at(self, store):
        before = time.time()
        entry = store.write("pid-1", "k", "v", ttl=60.0)
        assert entry.expires_at is not None
        assert entry.expires_at >= before + 59.9

    def test_write_with_tags_stores_frozenset(self, store):
        entry = store.write("pid-1", "k", "v", tags={"a", "b"})
        assert entry.tags == frozenset({"a", "b"})

    def test_write_overwrites_existing_key(self, store):
        store.write("pid-1", "goal", "old")
        store.write("pid-1", "goal", "new")
        assert store.get("pid-1", "goal") == "new"

    def test_write_creates_namespace_on_demand(self, store):
        store.write("new-ns", "k", "v")
        assert "new-ns" in store.list_namespaces()


class TestRead:
    def test_read_returns_entry(self, store):
        store.write("pid-1", "x", 42)
        entry = store.read("pid-1", "x")
        assert entry.value == 42

    def test_read_missing_namespace_raises(self, store):
        with pytest.raises(MemoryKeyError):
            store.read("ghost", "x")

    def test_read_missing_key_raises(self, store):
        store.write("pid-1", "other", "v")
        with pytest.raises(MemoryKeyError):
            store.read("pid-1", "missing")

    def test_read_expired_entry_raises(self, store):
        store.write("pid-1", "tmp", "v", ttl=0.001)
        time.sleep(0.01)
        with pytest.raises(MemoryKeyError):
            store.read("pid-1", "tmp")

    def test_get_returns_value(self, store):
        store.write("pid-1", "x", "hello")
        assert store.get("pid-1", "x") == "hello"

    def test_get_missing_returns_default(self, store):
        assert store.get("pid-1", "absent", "fallback") == "fallback"

    def test_get_expired_returns_default(self, store):
        store.write("pid-1", "tmp", "v", ttl=0.001)
        time.sleep(0.01)
        assert store.get("pid-1", "tmp") is None


class TestDelete:
    def test_delete_removes_key(self, store):
        store.write("pid-1", "x", "v")
        store.delete("pid-1", "x")
        assert not store.has("pid-1", "x")

    def test_delete_missing_raises(self, store):
        with pytest.raises(MemoryKeyError):
            store.delete("pid-1", "ghost")

    def test_clear_namespace_removes_all(self, store):
        store.write("pid-1", "a", 1)
        store.write("pid-1", "b", 2)
        count = store.clear_namespace("pid-1")
        assert count == 2
        assert store.list_keys("pid-1") == ()

    def test_clear_unknown_namespace_raises(self, store):
        with pytest.raises(MemoryNamespaceError):
            store.clear_namespace("ghost")


class TestQuery:
    def test_list_keys_returns_live_keys(self, store):
        store.write("pid-1", "a", 1)
        store.write("pid-1", "b", 2)
        keys = store.list_keys("pid-1")
        assert set(keys) == {"a", "b"}

    def test_list_keys_excludes_expired(self, store):
        store.write("pid-1", "live", "v")
        store.write("pid-1", "dead", "v", ttl=0.001)
        time.sleep(0.01)
        assert "dead" not in store.list_keys("pid-1")

    def test_list_namespaces_returns_active(self, store):
        store.write("ns-a", "k", "v")
        store.write("ns-b", "k", "v")
        assert "ns-a" in store.list_namespaces()
        assert "ns-b" in store.list_namespaces()

    def test_has_returns_true_for_live(self, store):
        store.write("pid-1", "x", "v")
        assert store.has("pid-1", "x")

    def test_has_returns_false_for_expired(self, store):
        store.write("pid-1", "x", "v", ttl=0.001)
        time.sleep(0.01)
        assert not store.has("pid-1", "x")

    def test_total_entries_counts_live(self, store):
        store.write("pid-1", "a", 1)
        store.write("pid-1", "b", 2)
        store.write("pid-2", "c", 3)
        assert store.total_entries == 3

    def test_total_entries_excludes_expired(self, store):
        store.write("pid-1", "live", "v")
        store.write("pid-1", "dead", "v", ttl=0.001)
        time.sleep(0.01)
        assert store.total_entries == 1
