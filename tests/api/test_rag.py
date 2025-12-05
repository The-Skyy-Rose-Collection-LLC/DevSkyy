#!/usr/bin/env python3
"""
Test suite for RAG (Retrieval-Augmented Generation) API endpoints
Per Truth Protocol Rule #8: Test coverage ≥90%

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from fastapi.testclient import TestClient
import pytest

from main import app


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Mock authentication headers for testing
    In production, these would be JWT tokens from Auth0
    """
    return {
        "Authorization": "Bearer test_token_superadmin",
        "Content-Type": "application/json",
    }


@pytest.fixture
def mock_rag_service():
    """Mock RAG service for testing"""
    with patch("api.v1.rag.get_rag_service") as mock:
        service = MagicMock()

        # Mock ingest_text
        service.ingest_text = AsyncMock(
            return_value={
                "total_documents": 10,
                "added": 5,
                "chunks_created": 5,
                "source": "test_source",
                "ingested_at": "2025-01-12T00:00:00",
            }
        )

        # Mock ingest_document
        service.ingest_document = AsyncMock(
            return_value={
                "total_documents": 15,
                "added": 5,
                "chunks_created": 5,
                "file_path": "/tmp/test.pdf",
                "file_type": "pdf",
                "ingested_at": "2025-01-12T00:00:00",
            }
        )

        # Mock search
        service.search = AsyncMock(
            return_value=[
                {
                    "content": "DevSkyy is a multi-agent AI platform",
                    "metadata": {"source": "test", "page": 1},
                    "similarity": 0.95,
                    "distance": 0.05,
                },
                {
                    "content": "It provides 54 specialized agents",
                    "metadata": {"source": "test", "page": 2},
                    "similarity": 0.90,
                    "distance": 0.10,
                },
            ]
        )

        # Mock query
        service.query = AsyncMock(
            return_value={
                "answer": "DevSkyy is a multi-agent AI platform with 54 specialized agents.",
                "sources": [
                    {
                        "content": "DevSkyy is a multi-agent AI platform",
                        "metadata": {"source": "test", "page": 1},
                        "similarity": 0.95,
                        "distance": 0.05,
                    },
                ],
                "context_used": 1,
                "model": "claude-sonnet-4-5-20250929",
                "tokens_used": {"input": 100, "output": 50},
            }
        )

        # Mock get_stats
        service.get_stats = MagicMock(
            return_value={
                "vector_db": {
                    "collection_name": "devskyy_docs",
                    "document_count": 100,
                    "persist_directory": "./data/chroma",
                    "embedding_model": "all-MiniLM-L6-v2",
                },
                "config": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "top_k": 5,
                    "similarity_threshold": 0.7,
                },
            }
        )

        # Mock vector_db
        service.vector_db = MagicMock()
        service.vector_db.delete_collection = MagicMock()

        mock.return_value = service
        yield service


@pytest.fixture
def mock_auth():
    """Mock authentication for testing"""
    with patch("api.v1.rag.get_current_user_with_role") as mock:

        def auth_factory(roles):
            def auth_dependency():
                return {
                    "user_id": "test_user",
                    "email": "test@example.com",
                    "role": "SuperAdmin",
                }

            return auth_dependency

        mock.side_effect = auth_factory
        yield mock


# =============================================================================
# TEST INGEST TEXT ENDPOINT
# =============================================================================


class TestIngestTextEndpoint:
    """Test suite for POST /api/v1/rag/ingest/text"""

    def test_ingest_text_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful text ingestion"""
        response = client.post(
            "/api/v1/rag/ingest/text",
            json={
                "text": "This is a test document about DevSkyy platform.",
                "source": "test_source",
                "metadata": {"category": "test"},
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["success"] is True
        assert data["chunks_created"] == 5
        assert data["source"] == "test_source"
        assert "ingested_at" in data

    def test_ingest_text_validation_empty(self, client, auth_headers, mock_auth):
        """Test validation for empty text"""
        response = client.post(
            "/api/v1/rag/ingest/text",
            json={"text": "   "},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_text_validation_too_short(self, client, auth_headers, mock_auth):
        """Test validation for text too short"""
        response = client.post(
            "/api/v1/rag/ingest/text",
            json={"text": "short"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_text_with_metadata(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test text ingestion with custom metadata"""
        response = client.post(
            "/api/v1/rag/ingest/text",
            json={
                "text": "DevSkyy platform provides enterprise-grade AI orchestration.",
                "source": "documentation",
                "metadata": {
                    "category": "platform",
                    "version": "5.1.0",
                    "author": "DevSkyy Team",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_ingest_text_unauthorized(self, client, mock_rag_service):
        """Test text ingestion without authentication"""
        with patch("api.v1.rag.get_current_user_with_role") as mock_auth:
            mock_auth.side_effect = Exception("Unauthorized")

            response = client.post(
                "/api/v1/rag/ingest/text",
                json={"text": "Test document content here."},
            )

            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]


# =============================================================================
# TEST INGEST FILE ENDPOINT
# =============================================================================


class TestIngestFileEndpoint:
    """Test suite for POST /api/v1/rag/ingest/file"""

    def test_ingest_pdf_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful PDF ingestion"""
        # Create a temporary PDF file (minimal valid PDF)
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000214 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n308\n%%EOF"

        response = client.post(
            "/api/v1/rag/ingest/file",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["success"] is True
        assert data["chunks_created"] == 5
        assert data["file_type"] == "pdf"

    def test_ingest_text_file_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful text file ingestion"""
        text_content = "DevSkyy platform documentation.\n\nThis is a test document."

        response = client.post(
            "/api/v1/rag/ingest/file",
            files={"file": ("test.txt", text_content.encode(), "text/plain")},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_ingest_unsupported_file_type(self, client, auth_headers, mock_auth):
        """Test rejection of unsupported file types"""
        response = client.post(
            "/api/v1/rag/ingest/file",
            files={"file": ("test.exe", b"fake executable", "application/octet-stream")},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in response.json()["detail"]


# =============================================================================
# TEST SEARCH ENDPOINT
# =============================================================================


class TestSearchEndpoint:
    """Test suite for POST /api/v1/rag/search"""

    def test_search_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful semantic search"""
        response = client.post(
            "/api/v1/rag/search",
            json={"query": "What is DevSkyy?"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "results" in data
        assert data["count"] == 2
        assert data["query"] == "What is DevSkyy?"
        assert len(data["results"]) == 2

        # Verify result structure
        result = data["results"][0]
        assert "content" in result
        assert "metadata" in result
        assert "similarity" in result
        assert result["similarity"] == 0.95

    def test_search_with_filters(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test search with metadata filters"""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "security features",
                "top_k": 10,
                "filters": {"category": "security"},
                "min_similarity": 0.8,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_validation_empty_query(self, client, auth_headers, mock_auth):
        """Test validation for empty query"""
        response = client.post(
            "/api/v1/rag/search",
            json={"query": ""},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_validation_top_k_limits(self, client, auth_headers, mock_auth):
        """Test validation for top_k parameter limits"""
        # Test lower bound
        response = client.post(
            "/api/v1/rag/search",
            json={"query": "test", "top_k": 0},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test upper bound
        response = client.post(
            "/api/v1/rag/search",
            json={"query": "test", "top_k": 25},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# TEST QUERY ENDPOINT
# =============================================================================


class TestQueryEndpoint:
    """Test suite for POST /api/v1/rag/query"""

    def test_query_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful RAG query"""
        response = client.post(
            "/api/v1/rag/query",
            json={"question": "What is DevSkyy?"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "context_used" in data
        assert data["context_used"] == 1
        assert "model" in data
        assert "tokens_used" in data

    def test_query_with_custom_model(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test RAG query with custom model"""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "question": "Explain DevSkyy security",
                "model": "claude-3-opus-20240229",
                "top_k": 10,
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_query_with_custom_system_prompt(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test RAG query with custom system prompt"""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "question": "What are the key features?",
                "system_prompt": "You are a technical expert. Answer concisely.",
            },
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_query_validation_empty_question(self, client, auth_headers, mock_auth):
        """Test validation for empty question"""
        response = client.post(
            "/api/v1/rag/query",
            json={"question": ""},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# TEST STATS ENDPOINT
# =============================================================================


class TestStatsEndpoint:
    """Test suite for GET /api/v1/rag/stats"""

    def test_get_stats_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful stats retrieval"""
        response = client.get(
            "/api/v1/rag/stats",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "vector_db" in data
        assert "config" in data

        # Verify vector_db stats
        assert data["vector_db"]["document_count"] == 100
        assert data["vector_db"]["collection_name"] == "devskyy_docs"

        # Verify config
        assert data["config"]["chunk_size"] == 1000


# =============================================================================
# TEST HEALTH CHECK ENDPOINT
# =============================================================================


class TestHealthCheckEndpoint:
    """Test suite for GET /api/v1/rag/health"""

    def test_health_check_success(self, client, mock_rag_service):
        """Test successful health check"""
        response = client.get("/api/v1/rag/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "rag"
        assert data["version"] == "1.0.0"
        assert "document_count" in data
        assert "timestamp" in data

    def test_health_check_failure(self, client):
        """Test health check failure scenario"""
        with patch("api.v1.rag.get_rag_service") as mock:
            mock.side_effect = Exception("Service unavailable")

            response = client.get("/api/v1/rag/health")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()

            assert data["status"] == "unhealthy"
            assert "error" in data


# =============================================================================
# TEST RESET ENDPOINT
# =============================================================================


class TestResetEndpoint:
    """Test suite for DELETE /api/v1/rag/reset"""

    def test_reset_success(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test successful database reset"""
        response = client.delete(
            "/api/v1/rag/reset",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert "message" in data
        assert "timestamp" in data


# =============================================================================
# TEST RBAC AUTHORIZATION
# =============================================================================


class TestRBACAuthorization:
    """Test role-based access control for RAG endpoints"""

    def test_ingest_requires_admin_role(self, client, mock_rag_service):
        """Test that ingestion requires admin role"""
        with patch("api.v1.rag.get_current_user_with_role") as mock_auth:
            # Mock unauthorized user
            def auth_factory(roles):
                def auth_dependency():
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

                return auth_dependency

            mock_auth.side_effect = auth_factory

            response = client.post(
                "/api/v1/rag/ingest/text",
                json={"text": "Test document content"},
                headers={"Authorization": "Bearer readonly_token"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_search_allows_api_user(self, client, mock_rag_service):
        """Test that search allows APIUser role"""
        with patch("api.v1.rag.get_current_user_with_role") as mock_auth:

            def auth_factory(roles):
                if "APIUser" in roles:

                    def auth_dependency():
                        return {"user_id": "api_user", "role": "APIUser"}

                    return auth_dependency
                return None

            mock_auth.side_effect = auth_factory

            response = client.post(
                "/api/v1/rag/search",
                json={"query": "test"},
                headers={"Authorization": "Bearer apiuser_token"},
            )

            # Should succeed for APIUser
            assert response.status_code == status.HTTP_200_OK


# =============================================================================
# TEST ERROR HANDLING
# =============================================================================


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_service_exception_handling(self, client, auth_headers, mock_auth):
        """Test handling of service exceptions"""
        with patch("api.v1.rag.get_rag_service") as mock:
            service = MagicMock()
            service.ingest_text = AsyncMock(side_effect=Exception("Database error"))
            mock.return_value = service

            response = client.post(
                "/api/v1/rag/ingest/text",
                json={"text": "Test document content here."},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to ingest text" in response.json()["detail"]

    def test_search_exception_handling(self, client, auth_headers, mock_auth):
        """Test handling of search exceptions"""
        with patch("api.v1.rag.get_rag_service") as mock:
            service = MagicMock()
            service.search = AsyncMock(side_effect=Exception("Search error"))
            mock.return_value = service

            response = client.post(
                "/api/v1/rag/search",
                json={"query": "test query"},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# TEST INTEGRATION
# =============================================================================


class TestRAGIntegration:
    """Integration tests for RAG workflow"""

    def test_full_rag_workflow(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test complete RAG workflow: ingest -> search -> query"""
        # 1. Ingest document
        ingest_response = client.post(
            "/api/v1/rag/ingest/text",
            json={
                "text": "DevSkyy is an enterprise AI platform with 54 agents.",
                "source": "integration_test",
            },
            headers=auth_headers,
        )
        assert ingest_response.status_code == status.HTTP_201_CREATED

        # 2. Search for document
        search_response = client.post(
            "/api/v1/rag/search",
            json={"query": "DevSkyy agents"},
            headers=auth_headers,
        )
        assert search_response.status_code == status.HTTP_200_OK
        assert len(search_response.json()["results"]) > 0

        # 3. Query with RAG
        query_response = client.post(
            "/api/v1/rag/query",
            json={"question": "How many agents does DevSkyy have?"},
            headers=auth_headers,
        )
        assert query_response.status_code == status.HTTP_200_OK
        assert "answer" in query_response.json()

    def test_stats_after_ingestion(self, client, auth_headers, mock_rag_service, mock_auth):
        """Test stats endpoint after document ingestion"""
        # Ingest document
        client.post(
            "/api/v1/rag/ingest/text",
            json={"text": "Test document for stats validation."},
            headers=auth_headers,
        )

        # Check stats
        stats_response = client.get("/api/v1/rag/stats", headers=auth_headers)
        assert stats_response.status_code == status.HTTP_200_OK
        assert stats_response.json()["vector_db"]["document_count"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.v1.rag", "--cov-report=term-missing"])
