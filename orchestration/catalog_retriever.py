"""CatalogRetriever — semantic retrieval over the SkyyRose canonical catalog.

Thin wrapper over the existing orchestration stack:

- orchestration.embedding_engine — Sentence Transformers (local, free)
- orchestration.vector_store     — ChromaDB by default; Pinecone available
- skyyrose.core.catalog_loader   — canonical CSV reader
- orchestration.brand_context    — CatalogContext + load_catalog_context

The retriever indexes `branding_spec + description + name` per SKU and serves
semantic queries for agents that need "find SKUs similar to this query" or
"surface this collection's thematic matches" at runtime. ChromaDB is default
because the 30-SKU catalog is trivially small; Pinecone swap is a one-line
config change via VectorStoreConfig.

Everything is async because the underlying engines are async.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from orchestration.brand_context import CatalogSummary, load_catalog_context
from orchestration.embedding_engine import (
    BaseEmbeddingEngine,
    EmbeddingConfig,
    EmbeddingProvider,
    create_embedding_engine,
)
from orchestration.vector_store import (
    BaseVectorStore,
    Document,
    SearchResult,
    VectorDBType,
    VectorStoreConfig,
    create_vector_store,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CatalogMatch:
    """A single SKU match from semantic search, scored against a query."""

    sku: str
    name: str
    collection: str
    score: float
    branding_spec: str
    description: str


class CatalogRetriever:
    """Semantic index + retrieval over the SkyyRose canonical catalog.

    Usage:
        retriever = CatalogRetriever()
        await retriever.initialize()
        await retriever.index_catalog()
        matches = await retriever.retrieve("distressed denim jackets", top_k=5)

    Index key: `branding_spec + description + name`. Metadata carries
    `sku`, `collection`, and `price` so callers can post-filter without
    re-querying the CSV.
    """

    DEFAULT_COLLECTION = "skyyrose-catalog-v1"

    def __init__(
        self,
        embedding_engine: BaseEmbeddingEngine | None = None,
        vector_store: BaseVectorStore | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._embedder = embedding_engine
        self._store = vector_store
        self._collection_name = collection_name or self.DEFAULT_COLLECTION
        self._initialized = False

    async def initialize(self) -> None:
        """Lazy-create engine + store if not injected; init both."""
        if self._embedder is None:
            self._embedder = create_embedding_engine(
                EmbeddingConfig(provider=EmbeddingProvider.SENTENCE_TRANSFORMERS)
            )
        await self._embedder.initialize()

        if self._store is None:
            self._store = create_vector_store(
                VectorStoreConfig(
                    db_type=VectorDBType.CHROMADB,
                    collection_name=self._collection_name,
                )
            )
        await self._store.initialize()
        self._initialized = True

    async def index_catalog(self, *, dry_run: bool = False) -> dict[str, Any]:
        """Embed + upsert every SKU in the canonical catalog.

        Args:
            dry_run: when True, skip the upsert and return the count + sample
                     so callers can preview cost/work before committing.

        Returns:
            Manifest dict: {total_skus, indexed_ids, dry_run, sample_ids}
        """
        self._require_init()
        rows = self._catalog_rows()

        documents: list[Document] = []
        texts: list[str] = []
        for row in rows:
            content = self._compose_content(row)
            doc = Document(
                id=f"sku:{row['sku']}",
                content=content,
                metadata={
                    "sku": row["sku"],
                    "name": (row.get("name") or "").strip(),
                    "collection": (row.get("collection") or "").strip().lower(),
                    "price": (row.get("price") or "").strip(),
                    "badge": (row.get("badge") or "").strip(),
                    "published": (row.get("published") or "").strip() == "1",
                    "branding_spec": (row.get("branding_spec") or "").strip(),
                    "description": (row.get("description") or "").strip(),
                },
                source="wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv",
            )
            documents.append(doc)
            texts.append(content)

        manifest: dict[str, Any] = {
            "total_skus": len(documents),
            "dry_run": dry_run,
            "sample_ids": [d.id for d in documents[:5]],
            "indexed_ids": [],
        }

        if dry_run or not documents:
            logger.info(
                "CatalogRetriever.index_catalog: %s mode, %d docs prepared",
                "DRY-RUN" if dry_run else "EMPTY",
                len(documents),
            )
            return manifest

        assert self._embedder is not None and self._store is not None
        embeddings = await self._embedder.embed_batch(texts)
        ids = await self._store.add_documents(documents, embeddings)
        manifest["indexed_ids"] = ids
        logger.info(
            "CatalogRetriever.index_catalog: indexed %d SKUs into %s",
            len(ids),
            self._collection_name,
        )
        return manifest

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        collection: str | None = None,
    ) -> list[CatalogMatch]:
        """Return the top-k SKUs semantically matching ``query``.

        Args:
            query: free-form natural language (e.g. "gothic luxury silver hoodie")
            top_k: max matches to return (default 5)
            collection: optional collection-slug filter (e.g. "black-rose")
        """
        self._require_init()
        assert self._embedder is not None and self._store is not None

        query_embedding = await self._embedder.embed_query(query)
        filter_metadata = {"collection": collection} if collection else None
        results = await self._store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
        return [self._match_from_result(r) for r in results]

    async def retrieve_by_collection(self, slug: str, *, top_k: int = 5) -> list[CatalogMatch]:
        """Shorthand for scoping a generic query to a single collection."""
        return await self.retrieve(
            query=f"{slug} collection signature pieces", top_k=top_k, collection=slug
        )

    async def close(self) -> None:
        if self._store is not None:
            await self._store.close()
        self._initialized = False

    # -- helpers --

    def _catalog_rows(self) -> list[dict[str, str]]:
        """Read catalog via the shared loader; fall back to stdlib csv."""
        try:
            from skyyrose.core.catalog_loader import read_catalog_rows

            return read_catalog_rows()
        except ImportError:
            context = load_catalog_context()  # uses brand_context's fallback path
            # brand_context collapses per-row data into summaries, so when
            # skyyrose.core is unavailable we can't faithfully reconstruct
            # individual rows. Raise rather than index a degenerate view.
            raise RuntimeError(
                "CatalogRetriever requires skyyrose.core.catalog_loader. "
                f"Observed {len(context.summaries)} collection summaries via "
                "orchestration.brand_context, but SKU-level rows are unavailable."
            )

    @staticmethod
    def _compose_content(row: dict[str, str]) -> str:
        """Combine the fields that carry semantic signal for search."""
        parts: list[str] = []
        name = (row.get("name") or "").strip()
        collection = (row.get("collection") or "").strip()
        branding = (row.get("branding_spec") or "").strip()
        description = (row.get("description") or "").strip()
        if name:
            parts.append(f"Product: {name}")
        if collection:
            parts.append(f"Collection: {collection}")
        if branding:
            parts.append(f"Branding: {branding}")
        if description:
            parts.append(description)
        return "\n".join(parts)

    @staticmethod
    def _match_from_result(result: SearchResult) -> CatalogMatch:
        meta = result.document.metadata
        return CatalogMatch(
            sku=meta.get("sku", ""),
            name=meta.get("name", ""),
            collection=meta.get("collection", ""),
            score=result.score,
            branding_spec=meta.get("branding_spec", ""),
            description=meta.get("description", ""),
        )

    def _require_init(self) -> None:
        if not self._initialized:
            raise RuntimeError("CatalogRetriever not initialized — await initialize() first.")


__all__ = [
    "CatalogMatch",
    "CatalogRetriever",
    "CatalogSummary",  # re-exported for one-stop import
]
