"""Catalog Search API — semantic retrieval over the SkyyRose canonical catalog.

Read-only endpoints backed by `CatalogRetriever.for_production()` —
Voyage `voyage-3-large` embeddings + Pinecone serverless
(`skyyrose-catalog` @ `us-west-2`).

Prefix:  /api/v1/catalog
Auth:    public (catalog data is publicly browseable)

Endpoints:
    GET  /search                            — semantic search across all SKUs
    GET  /collections/{slug}/featured       — top-k matches scoped to a collection
    GET  /products/{sku}                    — full product detail (CSV row + dossier)
    GET  /products/{sku}/similar            — semantic "you might also like"
    GET  /answer                            — natural-language Q&A grounded in catalog (RAG)
    GET  /health                            — verifies retriever can initialize
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from orchestration.catalog_retriever import CatalogAnswer, CatalogMatch, CatalogRetriever

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


# ---------------------------------------------------------------------------
# /products/{sku} — direct lookup (no LLM, no embed, free)
# ---------------------------------------------------------------------------


class DossierResponse(BaseModel):
    """Parsed product dossier — the rich per-product spec the render pipeline reads."""

    slug: str
    garment_type_lock: str = ""
    branding_block: str = ""
    negative_block: str = ""
    scene_pose: str = ""
    scene_setting: str = ""


class ProductDetailResponse(BaseModel):
    """Full product detail — canonical CSV row + parsed dossier when present."""

    sku: str
    name: str
    collection: str
    price: str = ""
    badge: str = ""
    description: str = ""
    branding_spec: str = Field(default="", description="Legacy single-line spec; prefer dossier.")
    image: str = ""
    published: bool = False
    is_preorder: bool = False
    dossier: DossierResponse | None = None


def _coerce_bool(value: str | None) -> bool:
    return (value or "").strip() in ("1", "true", "True", "yes")


@router.get("/products/{sku}", response_model=ProductDetailResponse)
async def get_product(sku: str) -> ProductDetailResponse:
    """Direct SKU lookup with full dossier when available.

    Pure read against the canonical catalog CSV + per-product dossier markdown.
    No Voyage call, no Pinecone call, no LLM — zero per-request cost. Returns
    404 if the SKU is not in the catalog. If the SKU exists but its dossier
    file is missing, returns the CSV-derived fields with `dossier: null`
    (deliberate choice: a missing dossier is a render-pipeline blocker, not
    a display-layer blocker).
    """
    # Lazy import — keeps skyyrose.core optional at API module load
    from skyyrose.core.dossier_loader import (
        DossierMissingError,
        get_product_with_dossier,
    )

    try:
        merged = get_product_with_dossier(sku)
        dossier = merged.get("dossier") or None
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DossierMissingError:
        # SKU exists in CSV but dossier is missing — read the row directly
        from skyyrose.core.catalog_loader import read_catalog_rows

        rows = {row["sku"]: row for row in read_catalog_rows()}
        merged = rows[sku]
        dossier = None

    dossier_response = (
        DossierResponse(
            slug=dossier.get("slug", ""),
            garment_type_lock=dossier.get("garment_type_lock", ""),
            branding_block=dossier.get("branding_block", ""),
            negative_block=dossier.get("negative_block", ""),
            scene_pose=dossier.get("scene_pose", ""),
            scene_setting=dossier.get("scene_setting", ""),
        )
        if dossier
        else None
    )

    return ProductDetailResponse(
        sku=merged.get("sku", sku),
        name=(merged.get("name") or "").strip(),
        collection=(merged.get("collection") or "").strip().lower(),
        price=(merged.get("price") or "").strip(),
        badge=(merged.get("badge") or "").strip(),
        description=(merged.get("description") or "").strip(),
        branding_spec=(merged.get("branding_spec") or "").strip(),
        image=(merged.get("image") or "").strip(),
        published=_coerce_bool(merged.get("published")),
        is_preorder=_coerce_bool(merged.get("is_preorder")),
        dossier=dossier_response,
    )


# ---------------------------------------------------------------------------
# /products/{sku}/similar — semantic "you might also like"
# ---------------------------------------------------------------------------


class SimilarResponse(BaseModel):
    """Wrapper for the similar-SKU result set."""

    sku: str = Field(..., description="Source SKU (excluded from matches)")
    top_k: int
    matches: list[CatalogMatchResponse]
    elapsed_ms: float


@router.get("/products/{sku}/similar", response_model=SimilarResponse)
async def get_similar_products(
    sku: str,
    top_k: int = Query(5, ge=1, le=20),
) -> SimilarResponse:
    """Top-k SKUs semantically nearest to the given SKU (excluding itself).

    Re-embeds the source SKU's dossier-rich content via Voyage, queries
    Pinecone for nearest neighbors, drops the source SKU from results.
    Costs one Voyage query embed (~$0.0001).
    """
    from skyyrose.core.dossier_loader import DossierMissingError

    t0 = time.perf_counter()

    try:
        retriever = await _get_retriever()
        matches = await retriever.find_similar_by_sku(sku, top_k=top_k)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DossierMissingError as exc:
        # Dossier is required to compose the query content — without it we
        # would query against a degenerate string and return misleading matches.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU {sku!r} has no dossier; cannot compute similarity.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Similar lookup failed: sku=%r", sku)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Catalog retrieval temporarily unavailable: {type(exc).__name__}",
        ) from exc

    return SimilarResponse(
        sku=sku,
        top_k=top_k,
        matches=[CatalogMatchResponse.from_match(m) for m in matches],
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 2),
    )


# ---------------------------------------------------------------------------
# /answer — RAG with LLM synthesis (Voyage retrieve → Claude Haiku answer)
# ---------------------------------------------------------------------------


class AnswerResponse(BaseModel):
    """Natural-language answer grounded in catalog excerpts."""

    question: str
    answer: str
    citations: list[str] = Field(
        default_factory=list,
        description="SKUs cited in the answer text (in order of first mention)",
    )
    matches: list[CatalogMatchResponse] = Field(
        default_factory=list,
        description="Full retrieval context the LLM saw (top-k matches)",
    )
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_ms: float

    @classmethod
    def from_answer(cls, ans: CatalogAnswer, elapsed_ms: float) -> AnswerResponse:
        return cls(
            question=ans.question,
            answer=ans.answer,
            citations=ans.citations,
            matches=[CatalogMatchResponse.from_match(m) for m in ans.matches],
            model=ans.model,
            input_tokens=ans.input_tokens,
            output_tokens=ans.output_tokens,
            elapsed_ms=elapsed_ms,
        )


@router.get("/answer", response_model=AnswerResponse)
async def answer_question(
    q: str = Query(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language question about SkyyRose products",
    ),
    top_k: int = Query(
        5,
        ge=1,
        le=10,
        description="How many catalog matches to surface as grounding context",
    ),
) -> AnswerResponse:
    """Natural-language Q&A grounded in the SkyyRose catalog (RAG).

    Pipeline:
        1. Voyage embed query (~$0.0001)
        2. Pinecone retrieve top-k matches (free)
        3. Claude Haiku 4.5 synthesizes a grounded answer with [SKU] citations
           (~$0.001-0.002 per request)

    The LLM is instructed to cite SKUs in [brackets] and to refuse rather than
    hallucinate when the retrieval doesn't cover the question. Total cost per
    request is typically under $0.003.
    """
    t0 = time.perf_counter()

    try:
        retriever = await _get_retriever()
        ans = await retriever.answer_question(q, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Catalog Q&A failed: q=%r", q)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Catalog Q&A temporarily unavailable: {type(exc).__name__}",
        ) from exc

    return AnswerResponse.from_answer(ans, elapsed_ms=round((time.perf_counter() - t0) * 1000, 2))


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
