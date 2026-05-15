"""Tests for MemoryIndex."""

from __future__ import annotations

import time

import pytest

from aos.memory.index import MemoryIndex
from aos.memory.store import MemoryStore


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def index(store) -> MemoryIndex:
    return MemoryIndex(store)


class TestSearch:
    def test_search_empty_namespace_returns_empty(self, store, index):
        assert index.search(namespace="pid-1", tags={"goal"}) == ()

    def test_search_no_tags_returns_empty(self, store, index):
        store.write("pid-1", "x", "v", tags={"goal"})
        assert index.search(namespace="pid-1", tags=frozenset()) == ()

    def test_search_match_all_requires_all_tags(self, store, index):
        store.write("pid-1", "full", "v", tags={"goal", "urgent"})
        store.write("pid-1", "partial", "v", tags={"goal"})
        results = index.search(namespace="pid-1", tags={"goal", "urgent"}, match_all=True)
        assert len(results) == 1
        assert results[0].key == "full"

    def test_search_match_any_requires_one_tag(self, store, index):
        store.write("pid-1", "a", "v", tags={"goal"})
        store.write("pid-1", "b", "v", tags={"note"})
        results = index.search(namespace="pid-1", tags={"goal"}, match_all=False)
        assert len(results) == 1
        assert results[0].key == "a"

    def test_search_excludes_expired_entries(self, store, index):
        store.write("pid-1", "live", "v", tags={"goal"})
        store.write("pid-1", "dead", "v", tags={"goal"}, ttl=0.001)
        time.sleep(0.01)
        results = index.search(namespace="pid-1", tags={"goal"})
        assert all(e.key != "dead" for e in results)

    def test_search_results_newest_first(self, store, index):
        store.write("pid-1", "older", "v", tags={"goal"})
        time.sleep(0.01)
        store.write("pid-1", "newer", "v", tags={"goal"})
        results = index.search(namespace="pid-1", tags={"goal"})
        assert results[0].key == "newer"

    def test_search_does_not_cross_namespaces(self, store, index):
        store.write("pid-1", "k", "v", tags={"goal"})
        store.write("pid-2", "k", "v", tags={"goal"})
        results = index.search(namespace="pid-1", tags={"goal"})
        assert all(e.namespace == "pid-1" for e in results)


class TestSearchAllNamespaces:
    def test_finds_entries_across_namespaces(self, store, index):
        store.write("pid-1", "k", "v1", tags={"goal"})
        store.write("pid-2", "k", "v2", tags={"goal"})
        results = index.search_all_namespaces(tags={"goal"})
        namespaces = {e.namespace for e in results}
        assert namespaces == {"pid-1", "pid-2"}

    def test_empty_store_returns_empty(self, store, index):
        assert index.search_all_namespaces(tags={"goal"}) == ()
