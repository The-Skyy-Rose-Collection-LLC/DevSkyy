"""
RAGAnything API — Multimodal Knowledge Base
============================================

Prefix:  /api/v1/rag
Auth:    JWT Bearer (get_current_user dependency)
Billing: "rag-query" and "rag-ingest" intents — gated by tier

Endpoints:
    POST   /collections/{collection}/ingest  — upload + ingest a document
    POST   /query                            — graph-vector hybrid query
    GET    /collections                      — list all collections
    DELETE /collections/{collection}         — delete a collection and its storage
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from services.rag_anything_service import RAGAnythingService, get_rag_anything_service

from billing.entitlements import EntitlementChecker
from billing.metering import UsageMetering
from security.jwt_oauth2_auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAGAnything"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class IngestResponse(BaseModel):
    """Response returned after a successful document ingest."""

    doc_id: str
    collection: str
    status: str
    file: str


class QueryRequest(BaseModel):
    """Request body for a knowledge-base query."""

    question: str = Field(..., min_length=3, max_length=2000, description="Query text")
    collection: str = Field(..., min_length=1, max_length=100, description="Target collection")
    mode: str | None = Field(
        default=None,
        description="Retrieval mode: local | global | hybrid | naive | mix",
        pattern=r"^(local|global|hybrid|naive|mix)$",
    )
    top_k: int = Field(default=10, ge=1, le=50, description="Retrieval breadth")


class QueryResponse(BaseModel):
    """Response returned after a knowledge-base query."""

    answer: str
    collection: str
    mode: str
    sources: list[dict[str, Any]]


class CollectionInfo(BaseModel):
    """Metadata for a single knowledge-base collection."""

    name: str
    size_mb: float
    loaded: bool


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _metering() -> UsageMetering:
    return UsageMetering()


def _checker(metering: UsageMetering = Depends(_metering)) -> EntitlementChecker:
    return EntitlementChecker(metering=metering)


async def _service() -> RAGAnythingService:
    return await get_rag_anything_service()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/collections/{collection}/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a document into a RAG collection",
    description=(
        "Upload and parse a document into the named knowledge-base collection. "
        "Supports PDF (with embedded images and tables), DOCX, plain text, CSV, "
        "and common image formats. "
        "Requires the **starter** plan or above."
    ),
)
async def ingest_document(
    collection: str,
    file: UploadFile = File(...),
    user: TokenPayload = Depends(get_current_user),
    checker: EntitlementChecker = Depends(_checker),
    svc: RAGAnythingService = Depends(_service),
) -> IngestResponse:
    # 1. Billing gate — blocks free tier
    result = checker.check(tenant_id=user.sub, tier=user.tier, intent="rag-ingest")
    if not result.allowed:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=result.reason)

    # 2. Write upload to a temp file so RAGAnything can read it by path
    suffix = Path(file.filename or "upload.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await file.read())

        ingestion_result = await svc.ingest_document(
            collection=collection,
            file_path=tmp_path,
            metadata={"original_filename": file.filename, "tenant_id": user.sub},
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    # 3. Meter usage — one unit per document, auditable and user-intuitive
    checker._metering.record(user.sub, "rag-ingest", 1)

    return IngestResponse(**ingestion_result)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query a RAG knowledge base",
    description=(
        "Run a natural-language query against a collection using LightRAG's "
        "graph-vector hybrid retrieval. "
        "Mode options: **local** (entity-centric), **global** (theme-centric), "
        "**hybrid**, **naive** (vector-only), **mix** (default). "
        "Requires the **starter** plan or above."
    ),
)
async def query_collection(
    body: QueryRequest,
    user: TokenPayload = Depends(get_current_user),
    checker: EntitlementChecker = Depends(_checker),
    svc: RAGAnythingService = Depends(_service),
) -> QueryResponse:
    # Billing gate
    result = checker.check(tenant_id=user.sub, tier=user.tier, intent="rag-query")
    if not result.allowed:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=result.reason)

    query_result = await svc.query(
        collection=body.collection,
        question=body.question,
        mode=body.mode,
        top_k=body.top_k,
    )

    # Meter after successful query
    checker._metering.record(user.sub, "rag-query", 1)

    return QueryResponse(**query_result)


@router.get(
    "/collections",
    response_model=list[CollectionInfo],
    summary="List all RAG collections",
    description="Return all knowledge-base collections with their disk size and load status.",
)
async def list_collections(
    user: TokenPayload = Depends(get_current_user),
    svc: RAGAnythingService = Depends(_service),
) -> list[CollectionInfo]:
    # Available to any authenticated user — no billing gate
    collections = await svc.list_collections()
    return [CollectionInfo(**c) for c in collections]


@router.delete(
    "/collections/{collection}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a RAG collection",
    description=(
        "Permanently delete a knowledge-base collection and all its storage. "
        "This action cannot be undone."
    ),
)
async def delete_collection(
    collection: str,
    user: TokenPayload = Depends(get_current_user),
    svc: RAGAnythingService = Depends(_service),
) -> None:
    await svc.delete_collection(collection)
