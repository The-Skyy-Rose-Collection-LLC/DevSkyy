"""
Tests for namespace isolation in BaseVectorStore (ChromaVectorStore impl).
=========================================================================

Pinecone uses native namespaces; Chroma emulates via the `_namespace` metadata
key. This test asserts that emulation is airtight: writes, reads, and deletes
in one namespace must NOT touch another.

Uses real ChromaDB with tmp_path (mocking ChromaDB internals is brittle —
its API surface changes faster than the test contract). Same approach as
tests/test_rag_integration.py.
"""

from __future__ import annotations

import pytest

# Skip module if ChromaDB is unavailable on this Python — keeps the suite green
# in environments that haven't installed the optional dep.
try:
    import chromadb  # noqa: F401
except Exception as e:  # noqa: BLE001
    pytest.skip(f"chromadb unavailable: {e}", allow_module_level=True)

from orchestration.vector_store import (
    ChromaVectorStore,
    Document,
    VectorDBType,
    VectorStoreConfig,
    get_vector_search_cache,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# Embedding dim must be >= 64 (VectorStoreConfig pydantic floor).
# We use axis-aligned unit vectors so similarity scores are predictable.
_DIM = 64


def _embed(direction: int) -> list[float]:
    """Return an axis-aligned unit vector pointing along axis ``direction``."""
    v = [0.0] * _DIM
    v[direction % _DIM] = 1.0
    return v


@pytest.fixture
async def store(tmp_path):
    """Fresh ChromaVectorStore per test, isolated by tmp_path."""
    config = VectorStoreConfig(
        db_type=VectorDBType.CHROMADB,
        collection_name="test_namespace",
        persist_directory=str(tmp_path / "chroma"),
        dimension=_DIM,
        similarity_threshold=0.0,  # accept all matches; we test namespace, not relevance
        default_top_k=20,
    )
    s = ChromaVectorStore(config)
    await s.initialize()
    yield s
    await s.close()


@pytest.fixture(autouse=True)
async def _clear_search_cache():
    """Vector search cache is global — clear so prior tests don't leak."""
    cache = get_vector_search_cache()
    await cache.clear()
    yield
    await cache.clear()


def _doc(doc_id: str, content: str) -> Document:
    return Document(id=doc_id, content=content, source="test")


# ---------------------------------------------------------------------------
# Add + search isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_within_namespace_excludes_other_namespaces(store):
    """Docs in ns='A' must not appear when searching ns='B'."""
    await store.add_documents(
        [_doc("a1", "alpha 1"), _doc("a2", "alpha 2")],
        [_embed(0), _embed(0)],
        namespace="A",
    )
    await store.add_documents(
        [_doc("b1", "bravo 1"), _doc("b2", "bravo 2")],
        [_embed(0), _embed(0)],
        namespace="B",
    )

    results_a = await store.search(query_embedding=_embed(0), top_k=10, namespace="A")
    results_b = await store.search(query_embedding=_embed(0), top_k=10, namespace="B")

    a_ids = {r.document.id for r in results_a}
    b_ids = {r.document.id for r in results_b}

    assert a_ids == {"a1", "a2"}
    assert b_ids == {"b1", "b2"}
    assert a_ids.isdisjoint(b_ids)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_without_namespace_returns_all(store):
    """A None namespace search returns docs across every namespace.

    This is the documented contract — None means "default partition / no filter."
    Callers that want strict isolation MUST pass a namespace.
    """
    await store.add_documents([_doc("a1", "alpha")], [_embed(0)], namespace="A")
    await store.add_documents([_doc("b1", "bravo")], [_embed(0)], namespace="B")
    await store.add_documents([_doc("c1", "no-ns")], [_embed(0)], namespace=None)

    results = await store.search(query_embedding=_embed(0), top_k=10, namespace=None)
    ids = {r.document.id for r in results}

    assert ids == {"a1", "b1", "c1"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_namespace_metadata_round_trip(store):
    """The `_namespace` metadata key survives a write→read cycle."""
    await store.add_documents([_doc("a1", "alpha")], [_embed(0)], namespace="luxury")

    results = await store.search(query_embedding=_embed(0), top_k=1, namespace="luxury")
    assert len(results) == 1
    assert results[0].document.metadata.get("_namespace") == "luxury"


# ---------------------------------------------------------------------------
# Delete isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_targeting_wrong_namespace_is_a_noop(store):
    """Deleting an ID while passing the wrong namespace must NOT remove it.

    This verifies the `where={"_namespace": ns}` constraint on Chroma deletes
    actually scopes the operation. Without it, a buggy caller could delete
    cross-namespace by passing the wrong (or no) namespace.

    NOTE: Chroma enforces global ID uniqueness at the collection level, so
    we can't have the same ID in two namespaces. Instead we test the inverse:
    asking Chroma to delete `alpha-1` under ns=B is a no-op because the
    where filter excludes it.
    """
    await store.add_documents([_doc("alpha-1", "alpha")], [_embed(0)], namespace="A")
    await store.add_documents([_doc("bravo-1", "bravo")], [_embed(0)], namespace="B")

    # Try to delete A's ID while claiming we're in namespace B — should be no-op
    await store.delete_documents(["alpha-1"], namespace="B")

    # alpha-1 must still exist in ns=A (proves the namespace filter held)
    results_a = await store.search(query_embedding=_embed(0), top_k=10, namespace="A")
    assert {r.document.id for r in results_a} == {"alpha-1"}

    # bravo-1 must still exist in ns=B (proves the misdirected delete didn't drop it)
    results_b = await store.search(query_embedding=_embed(0), top_k=10, namespace="B")
    assert {r.document.id for r in results_b} == {"bravo-1"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_with_correct_namespace_succeeds(store):
    """Deleting an ID under its own namespace removes it; sibling namespace untouched."""
    await store.add_documents([_doc("alpha-1", "alpha")], [_embed(0)], namespace="A")
    await store.add_documents([_doc("bravo-1", "bravo")], [_embed(0)], namespace="B")

    await store.delete_documents(["alpha-1"], namespace="A")

    # alpha-1 gone from A
    results_a = await store.search(query_embedding=_embed(0), top_k=10, namespace="A")
    assert len(results_a) == 0

    # bravo-1 untouched in B
    results_b = await store.search(query_embedding=_embed(0), top_k=10, namespace="B")
    assert {r.document.id for r in results_b} == {"bravo-1"}


# ---------------------------------------------------------------------------
# Cache key correctness — namespace must participate
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_cache_key_includes_namespace(store):
    """A cached search for ns='A' must NOT serve ns='B'.

    Internally, namespace is merged into effective_filter before the cache
    lookup, so two searches with same embedding but different namespaces hash
    to different keys.
    """
    await store.add_documents([_doc("a1", "alpha")], [_embed(0)], namespace="A")
    await store.add_documents([_doc("b1", "bravo")], [_embed(0)], namespace="B")

    # First: warm cache for namespace A
    r_a1 = await store.search(query_embedding=_embed(0), top_k=10, namespace="A")
    # Second: same embedding, different namespace — must NOT return cached A results
    r_b1 = await store.search(query_embedding=_embed(0), top_k=10, namespace="B")

    a_ids = {r.document.id for r in r_a1}
    b_ids = {r.document.id for r in r_b1}
    assert a_ids == {"a1"}
    assert b_ids == {"b1"}


# ---------------------------------------------------------------------------
# Filter merging — explicit metadata filters compose with namespace filter
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_namespace_filter_composes_with_explicit_filter(store):
    """A caller-supplied filter_metadata is ANDed with the namespace filter."""
    await store.add_documents(
        [_doc("a-red", "red"), _doc("a-blue", "blue")],
        [_embed(0), _embed(0)],
        namespace="A",
    )
    # Manually set color metadata via re-add with metadata
    # (simpler: re-create with metadata directly)
    await store.add_documents(
        [
            Document(id="a-green", content="green", metadata={"color": "green"}, source="t"),
            Document(id="a-yellow", content="yellow", metadata={"color": "yellow"}, source="t"),
        ],
        [_embed(0), _embed(0)],
        namespace="A",
    )

    # Search ns=A with explicit color=green filter
    results = await store.search(
        query_embedding=_embed(0),
        top_k=10,
        filter_metadata={"color": "green"},
        namespace="A",
    )
    ids = {r.document.id for r in results}
    assert ids == {"a-green"}
