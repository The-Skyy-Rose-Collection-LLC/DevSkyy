"""Catalog Search API — semantic retrieval over the SkyyRose canonical catalog.

Read-only endpoints backed by `CatalogRetriever.for_production()` —
Voyage `voyage-3-large` embeddings + Pinecone serverless
(`skyyrose-catalog` @ `us-west-2`).

Prefix:  /api/v1/catalog
Auth:    public (catalog data is publicly browseable)

Endpoints:
    GET  /search                            — semantic search across all SKUs
    GET  /collections/{slug}/featured       — top-k matches scoped to a collection
    GET  /health                            — verifies retriever can initialize
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from orchestration.catalog_retriever import CatalogMatch, CatalogRetriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/catalog", tags=["Catalog"])


# ---------------------------------------------------------------------------
# Lazy singleton retriever — first request pays ~200ms init cost, all
# subsequent requests reuse the connection. Module-level so the same instance
# is shared across all FastAPI workers in this process.
# ---------------------------------------------------------------------------


_retriever: CatalogRetriever | None = None


async def _get_retriever() -> CatalogRetriever:
    """Initialize the production retriever on first call, return cached after."""
    global _retriever
    if _retriever is None:
        logger.info("Initializing CatalogRetriever (Voyage + Pinecone)")
        _retriever = await CatalogRetriever.for_production(namespace="catalog")
    return _retriever


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class CatalogMatchResponse(BaseModel):
    """A single SKU match scored against the query."""

    sku: str
    name: str
    collection: str
    score: float = Field(..., description="Cosine similarity (Pinecone native, 0-1)")
    description: str = Field(default="")
    branding_spec: str = Field(default="")

    @classmethod
    def from_match(cls, m: CatalogMatch) -> CatalogMatchResponse:
        return cls(
            sku=m.sku,
            name=m.name,
            collection=m.collection,
            score=m.score,
            description=m.description,
            branding_spec=m.branding_spec,
        )


class SearchResponse(BaseModel):
    """Envelope for a catalog search response."""

    query: str
    top_k: int
    collection: str | None
    matches: list[CatalogMatchResponse]
    elapsed_ms: float = Field(..., description="Total round-trip time including embed+query")


class CatalogHealthResponse(BaseModel):
    """Minimal liveness response for the retriever."""

    status: str
    embedder: dict | None = None
    namespace: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/search", response_model=SearchResponse)
async def search_catalog(
    q: str = Query(
        ...,
        min_length=1,
        max_length=500,
        description="Free-form natural language query (e.g. 'gothic luxury silver hoodie')",
    ),
    top_k: int = Query(5, ge=1, le=20, description="Max matches to return"),
    collection: str | None = Query(
        None,
        pattern="^[a-z][a-z0-9-]*$",
        description="Optional collection slug filter (e.g. 'black-rose', 'love-hurts')",
    ),
) -> SearchResponse:
    """Semantic search across the SkyyRose catalog.

    Backed by Voyage `voyage-3-large` embeddings (asymmetric query mode) against
    a Pinecone serverless index. Score values are native cosine similarity in
    [0,1]; higher is more relevant. Pinecone applies a similarity_threshold
    server-side, so off-target queries (e.g. 'denim' against a no-denim
    catalog) may legitimately return zero matches rather than weak ones.
    """
    t0 = time.perf_counter()

    try:
        retriever = await _get_retriever()
        matches = await retriever.retrieve(query=q, top_k=top_k, collection=collection)
    except Exception as exc:  # noqa: BLE001 — surface a generic 503 to the client
        logger.exception("Catalog search failed: query=%r collection=%r", q, collection)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Catalog retrieval temporarily unavailable: {type(exc).__name__}",
        ) from exc

    return SearchResponse(
        query=q,
        top_k=top_k,
        collection=collection,
        matches=[CatalogMatchResponse.from_match(m) for m in matches],
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
    )


@router.get("/collections/{slug}/featured", response_model=SearchResponse)
async def collection_featured(
    slug: str,
    top_k: int = Query(5, ge=1, le=20),
) -> SearchResponse:
    """Top-k semantic matches for a collection's signature pieces.

    Equivalent to issuing a generic "{slug} collection signature pieces" query
    with the collection filter applied — useful for collection landing pages
    that want the strongest representative SKUs without authoring a query.
    """
    if not slug or not slug.replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid collection slug: {slug!r}",
        )

    t0 = time.perf_counter()

    try:
        retriever = await _get_retriever()
        matches = await retriever.retrieve_by_collection(slug=slug, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Collection retrieval failed: slug=%r", slug)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Catalog retrieval temporarily unavailable: {type(exc).__name__}",
        ) from exc

    return SearchResponse(
        query=f"{slug} collection signature pieces",
        top_k=top_k,
        collection=slug,
        matches=[CatalogMatchResponse.from_match(m) for m in matches],
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
    )


@router.get("/health", response_model=CatalogHealthResponse)
async def catalog_health() -> CatalogHealthResponse:
    """Lightweight liveness check — verifies the retriever can initialize.

    Costs one Voyage init + one Pinecone control-plane call on first hit; all
    subsequent calls hit the cached singleton (zero network).
    """
    try:
        retriever = await _get_retriever()
        embedder_info = retriever._embedder.get_info() if retriever._embedder else None
        return CatalogHealthResponse(
            status="ok",
            embedder=embedder_info,
            namespace=retriever._namespace,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Catalog health check failed")
        return CatalogHealthResponse(status="error", error=f"{type(exc).__name__}: {exc}")
