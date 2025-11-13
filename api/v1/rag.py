#!/usr/bin/env python3
"""
DevSkyy RAG API Endpoints
Provides HTTP API for Retrieval-Augmented Generation functionality

Per Truth Protocol:
- Rule #1: Never guess - All operations type-checked and validated
- Rule #5: No secrets in code - API keys via headers
- Rule #6: RBAC roles - Endpoint authorization
- Rule #7: Input validation - Pydantic schema enforcement
- Rule #13: Security baseline - JWT authentication required

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from security.jwt_auth import get_current_user_with_role
from services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class IngestTextRequest(BaseModel):
    """Request model for text ingestion"""

    text: str = Field(..., description="Text content to ingest", min_length=10)
    source: str = Field(default="api_input", description="Source identifier")
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
    )

    @validator("text")
    def validate_text(cls, v: str) -> str:
        """
        Validate ingest text content.
        
        Ensures the string is not empty after stripping and does not exceed 1,000,000 characters.
        
        Parameters:
            v (str): Text to validate.
        
        Returns:
            str: The original text if valid.
        
        Raises:
            ValueError: If text is empty after stripping or longer than 1,000,000 characters.
        """
        if not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v) > 1_000_000:  # 1MB text limit
            raise ValueError("Text content too large (max 1MB)")
        return v


class SearchRequest(BaseModel):
    """Request model for semantic search"""

    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(default=5, description="Number of results", ge=1, le=20)
    filters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metadata filters",
    )
    min_similarity: float = Field(
        default=0.7,
        description="Minimum similarity threshold",
        ge=0.0,
        le=1.0,
    )


class QueryRequest(BaseModel):
    """Request model for RAG query"""

    question: str = Field(..., description="Question to answer", min_length=1)
    top_k: int = Field(default=5, description="Number of context chunks", ge=1, le=20)
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="LLM model to use",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt",
    )


class IngestResponse(BaseModel):
    """Response model for document ingestion"""

    success: bool = Field(..., description="Ingestion success")
    total_documents: int = Field(..., description="Total documents in collection")
    added: int = Field(..., description="Documents added in this operation")
    chunks_created: int = Field(..., description="Number of chunks created")
    file_path: Optional[str] = Field(None, description="Source file path")
    source: Optional[str] = Field(None, description="Source identifier")
    ingested_at: str = Field(..., description="Ingestion timestamp")


class SearchResult(BaseModel):
    """Individual search result"""

    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(..., description="Document metadata")
    similarity: float = Field(..., description="Similarity score")
    distance: float = Field(..., description="Vector distance")


class SearchResponse(BaseModel):
    """Response model for semantic search"""

    results: list[SearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")
    query: str = Field(..., description="Original query")


class QueryResponse(BaseModel):
    """Response model for RAG query"""

    answer: str = Field(..., description="Generated answer")
    sources: list[SearchResult] = Field(..., description="Source documents")
    context_used: int = Field(..., description="Number of context chunks used")
    model: Optional[str] = Field(None, description="LLM model used")
    tokens_used: Optional[dict[str, int]] = Field(None, description="Token usage")


class StatsResponse(BaseModel):
    """Response model for RAG statistics"""

    vector_db: dict[str, Any] = Field(..., description="Vector database stats")
    config: dict[str, Any] = Field(..., description="RAG configuration")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/rag/ingest/text",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest text content",
    description="Ingest text content into the RAG knowledge base",
)
async def ingest_text(
    request: IngestTextRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin", "Admin", "Developer"])
    ),
):
    """
    Ingest the provided text into the RAG service and return ingestion statistics.
    
    Parameters:
        request (IngestTextRequest): Text, source, and optional metadata to ingest.
    
    Returns:
        IngestResponse: Ingestion outcome and statistics (e.g., total_documents, added, chunks_created, file_path, source, ingested_at).
    
    Raises:
        HTTPException: If ingestion fails (returns status 500 with error detail).
    """
    try:
        rag_service = get_rag_service()

        stats = await rag_service.ingest_text(
            text=request.text,
            source=request.source,
            metadata=request.metadata,
        )

        return IngestResponse(
            success=True,
            **stats,
        )

    except Exception as e:
        logger.error(f"Error ingesting text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest text: {str(e)}",
        )


@router.post(
    "/rag/ingest/file",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest document file",
    description="Ingest a document file (PDF, TXT, etc.) into the RAG knowledge base",
)
async def ingest_file(
    file: UploadFile = File(..., description="Document file to ingest"),
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin", "Admin", "Developer"])
    ),
):
    """
    Ingests an uploaded document file into the RAG system.
    
    Validates the file type (allowed: .pdf, .txt, .md), writes the upload to a temporary file, delegates ingestion to the RAG service, and cleans up the temporary file. The response includes ingestion statistics and metadata.
    
    Returns:
        IngestResponse: Contains `success`, `total_documents`, `added`, `chunks_created`, optional `file_path`, optional `source`, and `ingested_at`.
    
    Raises:
        HTTPException: 400 if the file type is unsupported.
        HTTPException: 500 if ingestion fails due to an internal error.
    """
    try:
        # Validate file type
        allowed_extensions = {".pdf", ".txt", ".md"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
            )

        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Ingest document
            rag_service = get_rag_service()
            stats = await rag_service.ingest_document(
                file_path=temp_path,
                file_type=file_ext.lstrip("."),
            )

            return IngestResponse(
                success=True,
                **stats,
            )

        finally:
            # Clean up temporary file
            Path(temp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest file: {str(e)}",
        )


@router.post(
    "/rag/search",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Perform semantic search in the RAG knowledge base",
)
async def search(
    request: SearchRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin", "Admin", "Developer", "APIUser"])
    ),
):
    """
    Perform a semantic search against the RAG knowledge base for the provided query.
    
    Returns:
        SearchResponse: A response containing a list of ranked search results (each with content, metadata, similarity, and distance), the total count of results returned, and the original query.
    """
    try:
        rag_service = get_rag_service()

        results = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            min_similarity=request.min_similarity,
        )

        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            count=len(results),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/rag/query",
    response_model=QueryResponse,
    summary="RAG query",
    description="Ask a question and get an AI-generated answer with sources",
)
async def query(
    request: QueryRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin", "Admin", "Developer", "APIUser"])
    ),
):
    """
    Perform a retrieval-augmented generation query and return the model answer together with source documents and metadata.
    
    Returns:
        QueryResponse: Contains the generated `answer`, `sources` (list of documents used with content, metadata, similarity, distance), `context_used` (text retrieved from the knowledge base), and optional `model` and `tokens_used` fields.
    
    Raises:
        HTTPException: If the query processing fails.
    """
    try:
        rag_service = get_rag_service()

        result = await rag_service.query(
            question=request.question,
            top_k=request.top_k,
            model=request.model,
            system_prompt=request.system_prompt,
        )

        return QueryResponse(
            answer=result["answer"],
            sources=[SearchResult(**s) for s in result["sources"]],
            context_used=result["context_used"],
            model=result.get("model"),
            tokens_used=result.get("tokens_used"),
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@router.get(
    "/rag/stats",
    response_model=StatsResponse,
    summary="RAG statistics",
    description="Get RAG system statistics and configuration",
)
async def get_stats(
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin", "Admin", "Developer"])
    ),
):
    """
    Retrieve aggregated RAG service statistics.
    
    Returns:
        StatsResponse: Contains vector database statistics, configuration details, and document counts.
    
    Raises:
        HTTPException: Raised with status 500 if statistics cannot be retrieved.
    """
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_stats()

        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.delete(
    "/rag/reset",
    summary="Reset RAG database",
    description="Delete all documents from the RAG knowledge base",
)
async def reset_database(
    current_user: dict[str, Any] = Depends(
        get_current_user_with_role(["SuperAdmin"])
    ),
):
    """
    Delete all documents from the RAG vector database and reinitialize the collection.
    
    This action irreversibly removes all stored vectors and documents and creates a fresh vector database instance. Access is restricted to users with the SuperAdmin role.
    
    Returns:
        JSONResponse: Object with keys `success` (bool), `message` (str), and `timestamp` (ISO 8601 str).
    
    Raises:
        HTTPException: with status 500 if the reset operation fails.
    """
    try:
        rag_service = get_rag_service()
        rag_service.vector_db.delete_collection()

        # Reinitialize collection
        from services.rag_service import VectorDatabase

        rag_service.vector_db = VectorDatabase()

        return JSONResponse(
            content={
                "success": True,
                "message": "RAG database reset successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset database: {str(e)}",
        )


@router.get(
    "/rag/health",
    summary="RAG health check",
    description="Check RAG system health",
)
async def health_check():
    """
    Return overall RAG service health as a JSONResponse.
    
    On success, returns a JSONResponse containing service status "healthy", service name, version, document_count, embedding_model, and timestamp. On failure, returns a JSONResponse with HTTP 503 containing status "unhealthy", service name, error message, and timestamp.
    
    Returns:
        JSONResponse: Health payload; status code 200 on success, 503 on failure.
    """
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_stats()

        return JSONResponse(
            content={
                "status": "healthy",
                "service": "rag",
                "version": "1.0.0",
                "document_count": stats["vector_db"]["document_count"],
                "embedding_model": stats["vector_db"]["embedding_model"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "rag",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )