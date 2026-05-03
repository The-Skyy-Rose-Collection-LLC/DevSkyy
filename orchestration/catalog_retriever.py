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
        namespace: str | None = "catalog",
    ) -> None:
        """
        Args:
            embedding_engine: Override the default Sentence Transformers engine
                (e.g. pass a configured VoyageEmbeddingEngine for production).
            vector_store: Override the default ChromaDB store
                (e.g. pass a Pinecone store for production).
            collection_name: Override the Chroma collection name.
            namespace: Logical partition within the index. Defaults to "catalog";
                pass `None` to write/read in the default partition.
        """
        self._embedder = embedding_engine
        self._store = vector_store
        self._collection_name = collection_name or self.DEFAULT_COLLECTION
        self._namespace = namespace
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

        Each SKU's content is composed from its CSV row PLUS its per-product
        dossier markdown (technique, color, embroidery placement, scene
        setting). SKUs without a dossier (retired, or not yet authored) are
        skipped and listed in `manifest['skipped_skus']` rather than failing
        the run — call sites can decide whether the skip set is acceptable.

        Args:
            dry_run: when True, skip the upsert and return the count + sample
                     so callers can preview cost/work before committing.

        Returns:
            Manifest dict: {total_skus, indexed_ids, skipped_skus, dry_run,
            sample_ids, namespace}
        """
        self._require_init()
        rows = self._catalog_rows()

        # Lazy import — keeps skyyrose.core optional at module load
        try:
            from skyyrose.core.dossier_loader import (
                DossierMissingError,
                get_product_with_dossier,
            )
        except ImportError as exc:
            raise RuntimeError(
                f"CatalogRetriever now requires skyyrose.core.dossier_loader. Import failed: {exc}"
            ) from exc

        documents: list[Document] = []
        texts: list[str] = []
        skipped: list[dict[str, str]] = []

        for row in rows:
            sku = (row.get("sku") or "").strip()
            try:
                merged = get_product_with_dossier(sku)
            except (DossierMissingError, KeyError) as exc:
                logger.info("Skipping %s: %s", sku, exc)
                skipped.append({"sku": sku, "reason": type(exc).__name__})
                continue

            dossier_data = merged.get("dossier", {})
            content = self._compose_content(row, dossier_data)
            doc = Document(
                id=f"sku:{sku}",
                content=content,
                metadata={
                    "sku": sku,
                    "name": (row.get("name") or "").strip(),
                    "collection": (row.get("collection") or "").strip().lower(),
                    "price": (row.get("price") or "").strip(),
                    "badge": (row.get("badge") or "").strip(),
                    "published": (row.get("published") or "").strip() == "1",
                    "garment_type_lock": (dossier_data.get("garment_type_lock") or "").strip(),
                    "branding_block": (dossier_data.get("branding_block") or "").strip(),
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
            "skipped_skus": skipped,
            "namespace": self._namespace,
        }

        if dry_run or not documents:
            logger.info(
                "CatalogRetriever.index_catalog: %s mode, %d docs prepared, %d skipped",
                "DRY-RUN" if dry_run else "EMPTY",
                len(documents),
                len(skipped),
            )
            return manifest

        assert self._embedder is not None and self._store is not None
        embeddings = await self._embedder.embed_batch(texts)
        ids = await self._store.add_documents(documents, embeddings, namespace=self._namespace)
        manifest["indexed_ids"] = ids
        logger.info(
            "CatalogRetriever.index_catalog: indexed %d SKUs into %s (ns=%s, skipped=%d)",
            len(ids),
            self._collection_name,
            self._namespace,
            len(skipped),
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
            namespace=self._namespace,
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
    def _compose_content(row: dict[str, str], dossier_data: dict[str, str]) -> str:
        """Compose semantic content from CSV row + parsed dossier.

        Dossier fields carry the high-signal content (technique, color,
        embroidery placement, scene context); CSV fields anchor the product
        identity (name, collection, price tier). The dossier's `negative_block`
        is intentionally OMITTED — it describes what NOT to render and would
        pollute similarity scoring (a query like "no chest logo" would otherwise
        be drawn to negative-block-rich documents).
        """
        parts: list[str] = []
        name = (row.get("name") or "").strip()
        collection = (row.get("collection") or "").strip()
        description = (row.get("description") or "").strip()

        if name:
            parts.append(f"Product: {name}")
        if collection:
            parts.append(f"Collection: {collection}")

        garment_lock = (dossier_data.get("garment_type_lock") or "").strip()
        if garment_lock:
            parts.append(f"Garment: {garment_lock}")

        branding = (dossier_data.get("branding_block") or "").strip()
        if branding:
            parts.append(f"Branding:\n{branding}")

        setting = (dossier_data.get("scene_setting") or "").strip()
        if setting:
            parts.append(f"Setting: {setting}")

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
            # Prefer the rich dossier branding_block; fall back to legacy CSV
            # branding_spec for any pre-existing index entries.
            branding_spec=meta.get("branding_block") or meta.get("branding_spec", ""),
            description=meta.get("description", ""),
        )

    @classmethod
    async def for_production(
        cls,
        *,
        namespace: str | None = "catalog",
        pinecone_index: str | None = None,
    ) -> "CatalogRetriever":
        """Pre-configured retriever using Voyage 3-large + Pinecone serverless.

        Reads PINECONE_API_KEY and VOYAGE_API_KEY from environment. Creates the
        Pinecone index if it does not exist (dimension 1024 for voyage-3-large).

        Returns an already-initialized retriever — call sites can go straight
        to `index_catalog()` or `retrieve()` without an extra `initialize()`.
        """
        import os

        embedding = create_embedding_engine(EmbeddingConfig(provider=EmbeddingProvider.VOYAGE))
        await embedding.initialize()

        store = create_vector_store(
            VectorStoreConfig(
                db_type=VectorDBType.PINECONE,
                pinecone_index_name=pinecone_index or os.getenv("PINECONE_INDEX_NAME", "skyyrose"),
                dimension=embedding.dimension or 1024,
            )
        )
        await store.initialize()

        retriever = cls(
            embedding_engine=embedding,
            vector_store=store,
            namespace=namespace,
        )
        retriever._initialized = True
        return retriever

    def _require_init(self) -> None:
        if not self._initialized:
            raise RuntimeError("CatalogRetriever not initialized — await initialize() first.")


__all__ = [
    "CatalogMatch",
    "CatalogRetriever",
    "CatalogSummary",  # re-exported for one-stop import
]
