"""Phase 4 tests for orchestration/catalog_retriever.py.

Validates wiring only — not embedding or ANN search quality. The underlying
embedding_engine + vector_store modules have their own dedicated tests; this
file exercises the composition layer.

No sentence-transformers or chromadb calls happen here. Both dependencies
are stubbed with minimal fakes so the test runs in any environment.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from orchestration.catalog_retriever import (
    CatalogMatch,
    CatalogRetriever,
)
from orchestration.vector_store import Document, SearchResult


@pytest.fixture
def fake_embedder() -> AsyncMock:
    """Async mock embedder that returns fixed-length vectors."""
    embedder = AsyncMock()
    embedder.initialize = AsyncMock()
    embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3] for _ in range(100)])
    embedder.embed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return embedder


@pytest.fixture
def fake_store() -> AsyncMock:
    """Async mock vector store that records upserts and returns canned search results."""
    store = AsyncMock()
    store.initialize = AsyncMock()
    store.close = AsyncMock()
    store.add_documents = AsyncMock(side_effect=lambda docs, embs, **_kwargs: [d.id for d in docs])

    def _search(**_kwargs):
        # Values mirror the canonical CSV's br-001 row so tests assert on
        # realistic data shape, not invented fixtures.
        fake_doc = Document(
            id="sku:br-001",
            content=(
                "Product: BLACK Rose Crewneck\n"
                "Collection: black-rose\n"
                "Branding: Embossed on front chest, approximately 10 inches wide.\n"
                "Gothic luxury blooms in twilight."
            ),
            metadata={
                "sku": "br-001",
                "name": "BLACK Rose Crewneck",
                "collection": "black-rose",
                "branding_spec": "Embossed on front chest, approximately 10 inches wide.",
                "description": "Gothic luxury blooms in twilight.",
            },
        )
        return [SearchResult(document=fake_doc, score=0.92, distance=0.08)]

    store.search = AsyncMock(side_effect=_search)
    return store


@pytest.mark.asyncio
async def test_requires_init_before_use(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    with pytest.raises(RuntimeError, match="not initialized"):
        await retriever.retrieve("test query")


@pytest.mark.asyncio
async def test_initialize_boots_embedder_and_store(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    await retriever.initialize()
    fake_embedder.initialize.assert_awaited_once()
    fake_store.initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_index_catalog_dry_run_does_not_upsert(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    await retriever.initialize()
    manifest = await retriever.index_catalog(dry_run=True)

    assert manifest["dry_run"] is True
    assert manifest["total_skus"] > 0, "canonical CSV must have SKUs for this assertion"
    assert manifest["indexed_ids"] == []
    fake_embedder.embed_batch.assert_not_called()
    fake_store.add_documents.assert_not_called()


@pytest.mark.asyncio
async def test_index_catalog_commit_upserts(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    await retriever.initialize()
    manifest = await retriever.index_catalog(dry_run=False)

    assert manifest["dry_run"] is False
    assert manifest["total_skus"] > 0
    assert len(manifest["indexed_ids"]) == manifest["total_skus"]
    fake_embedder.embed_batch.assert_awaited_once()
    fake_store.add_documents.assert_awaited_once()


@pytest.mark.asyncio
async def test_retrieve_returns_catalog_matches(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    await retriever.initialize()
    matches = await retriever.retrieve("gothic luxury hoodie", top_k=3)

    assert len(matches) == 1
    match = matches[0]
    assert isinstance(match, CatalogMatch)
    assert match.sku == "br-001"
    assert match.name == "BLACK Rose Crewneck"
    assert match.collection == "black-rose"
    assert match.score == 0.92
    assert match.branding_spec == "Embossed on front chest, approximately 10 inches wide."
    assert match.description == "Gothic luxury blooms in twilight."


@pytest.mark.asyncio
async def test_retrieve_by_collection_applies_filter(fake_embedder, fake_store) -> None:
    retriever = CatalogRetriever(embedding_engine=fake_embedder, vector_store=fake_store)
    await retriever.initialize()
    await retriever.retrieve_by_collection("black-rose", top_k=5)

    fake_store.search.assert_awaited_once()
    call_kwargs = fake_store.search.call_args.kwargs
    assert call_kwargs["filter_metadata"] == {"collection": "black-rose"}
    assert call_kwargs["top_k"] == 5


def test_compose_content_includes_all_signal_fields() -> None:
    row = {
        "sku": "br-001",
        "name": "Test Crewneck",
        "collection": "black-rose",
        "description": "Gothic luxury blooms in twilight.",
    }
    dossier_data = {
        "branding_block": "rose gold chest logo, black thread on interior tag",
    }
    content = CatalogRetriever._compose_content(row, dossier_data)
    assert "Product: Test Crewneck" in content
    assert "Collection: black-rose" in content
    assert "Branding:\nrose gold chest logo" in content
    assert "Gothic luxury blooms" in content


def test_compose_content_skips_empty_fields() -> None:
    row = {"sku": "x-1", "name": "Only Name"}
    content = CatalogRetriever._compose_content(row, {})
    assert content == "Product: Only Name"
