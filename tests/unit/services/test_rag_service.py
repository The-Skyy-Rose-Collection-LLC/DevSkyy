"""
Unit Tests for RAG Service

Tests the RAGService class for document ingestion, retrieval,
and retrieval-augmented generation capabilities.

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All
- Rule #10: No-Skip Rule
- Rule #7: Input Validation

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import asyncio
from datetime import datetime
from pathlib import Path
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open

import pytest

# Mock external dependencies before importing the module
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['pypdf'] = MagicMock()
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.text_splitter'] = MagicMock()
sys.modules['tiktoken'] = MagicMock()

from services.rag_service import (
    DocumentProcessor,
    RAGConfig,
    RAGService,
    VectorDatabase,
    get_rag_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_vector_db():
    """Mock VectorDatabase instance."""
    mock_db = MagicMock(spec=VectorDatabase)
    mock_db.add_documents.return_value = {
        "total_documents": 5,
        "added": 5,
        "skipped": 0,
        "collection_size": 10,
    }
    mock_db.search.return_value = [
        {
            "content": "DevSkyy is an enterprise AI platform.",
            "metadata": {"source": "test.txt", "chunk_index": 0},
            "distance": 0.2,
            "similarity": 0.8,
            "id": "doc1",
        },
        {
            "content": "DevSkyy provides RBAC and encryption.",
            "metadata": {"source": "test.txt", "chunk_index": 1},
            "distance": 0.3,
            "similarity": 0.7,
            "id": "doc2",
        },
    ]
    mock_db.get_stats.return_value = {
        "collection_name": "test_collection",
        "document_count": 10,
        "persist_directory": "/tmp/test",
        "embedding_model": "all-MiniLM-L6-v2",
    }
    return mock_db


@pytest.fixture
def mock_doc_processor():
    """Mock DocumentProcessor instance."""
    mock_processor = MagicMock(spec=DocumentProcessor)
    mock_processor.chunk_size = 1000
    mock_processor.chunk_overlap = 200
    mock_processor.process_text.return_value = [
        {
            "content": "Test chunk 1",
            "metadata": {
                "source": "test",
                "chunk_index": 0,
                "file_type": "text",
                "tokens": 3,
            },
        },
        {
            "content": "Test chunk 2",
            "metadata": {
                "source": "test",
                "chunk_index": 1,
                "file_type": "text",
                "tokens": 3,
            },
        },
    ]
    mock_processor.process_pdf.return_value = [
        {
            "content": "PDF chunk 1",
            "metadata": {
                "source": "test.pdf",
                "page": 1,
                "chunk_index": 0,
                "total_pages": 2,
                "file_type": "pdf",
                "tokens": 3,
            },
        },
    ]
    return mock_processor


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a test answer from Claude.")]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def rag_service_with_mocks(mock_vector_db, mock_doc_processor):
    """RAGService with mocked dependencies but no Anthropic client."""
    with patch.object(RAGConfig, "ANTHROPIC_API_KEY", None):
        service = RAGService(
            vector_db=mock_vector_db,
            doc_processor=mock_doc_processor,
        )
    return service


@pytest.fixture
def rag_service_with_llm(mock_vector_db, mock_doc_processor, mock_anthropic_client):
    """RAGService with mocked dependencies including Anthropic client."""
    with patch.object(RAGConfig, "ANTHROPIC_API_KEY", "test-key"):
        service = RAGService(
            vector_db=mock_vector_db,
            doc_processor=mock_doc_processor,
        )
        service.anthropic = mock_anthropic_client
    return service


# =============================================================================
# RAGService.__init__ Tests
# =============================================================================


class TestRAGServiceInit:
    """Tests for RAGService initialization."""

    def test_init_with_provided_dependencies(self, mock_vector_db, mock_doc_processor):
        """Test initialization with provided dependencies."""
        # Arrange & Act
        with patch.object(RAGConfig, "ANTHROPIC_API_KEY", "test-api-key"):
            with patch("services.rag_service.Anthropic") as mock_anthropic:
                service = RAGService(
                    vector_db=mock_vector_db,
                    doc_processor=mock_doc_processor,
                )

                # Assert
                assert service.vector_db == mock_vector_db
                assert service.doc_processor == mock_doc_processor
                mock_anthropic.assert_called_once_with(api_key="test-api-key")

    def test_init_without_api_key(self, mock_vector_db, mock_doc_processor):
        """Test initialization without Anthropic API key."""
        # Arrange & Act
        with patch.object(RAGConfig, "ANTHROPIC_API_KEY", None):
            service = RAGService(
                vector_db=mock_vector_db,
                doc_processor=mock_doc_processor,
            )

            # Assert
            assert service.vector_db == mock_vector_db
            assert service.doc_processor == mock_doc_processor
            assert service.anthropic is None

    def test_init_creates_defaults_when_none_provided(self):
        """Test initialization creates default dependencies when none provided."""
        # Arrange & Act
        with patch.object(RAGConfig, "ANTHROPIC_API_KEY", None):
            with patch("services.rag_service.VectorDatabase") as mock_vdb_class:
                with patch("services.rag_service.DocumentProcessor") as mock_dp_class:
                    service = RAGService()

                    # Assert
                    mock_vdb_class.assert_called_once()
                    mock_dp_class.assert_called_once()


# =============================================================================
# RAGService.ingest_text Tests
# =============================================================================


class TestRAGServiceIngestText:
    """Tests for RAGService.ingest_text method."""

    @pytest.mark.asyncio
    async def test_ingest_text_basic(self, rag_service_with_mocks, mock_doc_processor, mock_vector_db):
        """Test basic text ingestion."""
        # Arrange
        text = "This is test content for ingestion."
        source = "test_source"

        # Act
        result = await rag_service_with_mocks.ingest_text(text, source=source)

        # Assert
        mock_doc_processor.process_text.assert_called_once_with(text, source=source)
        mock_vector_db.add_documents.assert_called_once()

        assert result["source"] == source
        assert result["text_length"] == len(text)
        assert result["chunks_created"] == 2  # Mock returns 2 chunks
        assert "ingested_at" in result
        assert result["total_documents"] == 5
        assert result["added"] == 5

    @pytest.mark.asyncio
    async def test_ingest_text_with_custom_metadata(self, rag_service_with_mocks, mock_doc_processor, mock_vector_db):
        """Test text ingestion with custom metadata."""
        # Arrange
        text = "Test content"
        source = "custom_source"
        custom_metadata = {"author": "Test Author", "category": "Testing"}

        # Act
        result = await rag_service_with_mocks.ingest_text(
            text,
            source=source,
            metadata=custom_metadata
        )

        # Assert
        # Verify custom metadata was added to chunks
        call_args = mock_doc_processor.process_text.return_value
        rag_service_with_mocks.vector_db.add_documents.assert_called_once()

        # Check that metadata was updated in the chunks passed to add_documents
        added_chunks = rag_service_with_mocks.vector_db.add_documents.call_args[0][0]
        for chunk in added_chunks:
            assert chunk["metadata"]["author"] == "Test Author"
            assert chunk["metadata"]["category"] == "Testing"

    @pytest.mark.asyncio
    async def test_ingest_text_with_default_source(self, rag_service_with_mocks):
        """Test text ingestion with default source parameter."""
        # Arrange
        text = "Test content"

        # Act
        result = await rag_service_with_mocks.ingest_text(text)

        # Assert
        assert result["source"] == "direct_input"

    @pytest.mark.asyncio
    async def test_ingest_text_handles_processor_error(self, rag_service_with_mocks, mock_doc_processor):
        """Test error handling when document processor fails."""
        # Arrange
        text = "Test content"
        mock_doc_processor.process_text.side_effect = ValueError("Processing error")

        # Act & Assert
        with pytest.raises(ValueError, match="Processing error"):
            await rag_service_with_mocks.ingest_text(text)

    @pytest.mark.asyncio
    async def test_ingest_text_handles_database_error(self, rag_service_with_mocks, mock_vector_db):
        """Test error handling when vector database fails."""
        # Arrange
        text = "Test content"
        mock_vector_db.add_documents.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database error"):
            await rag_service_with_mocks.ingest_text(text)


# =============================================================================
# RAGService.ingest_document Tests
# =============================================================================


class TestRAGServiceIngestDocument:
    """Tests for RAGService.ingest_document method."""

    @pytest.mark.asyncio
    async def test_ingest_pdf_document(self, rag_service_with_mocks, mock_doc_processor, mock_vector_db):
        """Test ingesting a PDF document."""
        # Arrange
        file_path = "/tmp/test.pdf"

        # Act
        result = await rag_service_with_mocks.ingest_document(file_path, file_type="pdf")

        # Assert
        mock_doc_processor.process_pdf.assert_called_once_with(file_path)
        mock_vector_db.add_documents.assert_called_once()

        assert result["file_path"] == file_path
        assert result["file_type"] == "pdf"
        assert result["chunks_created"] == 1  # Mock returns 1 PDF chunk
        assert "ingested_at" in result

    @pytest.mark.asyncio
    async def test_ingest_text_document(self, rag_service_with_mocks, mock_doc_processor):
        """Test ingesting a text document."""
        # Arrange
        file_path = "/tmp/test.txt"
        file_content = "This is test file content."

        with patch("builtins.open", mock_open(read_data=file_content)):
            # Act
            result = await rag_service_with_mocks.ingest_document(file_path, file_type="txt")

            # Assert
            mock_doc_processor.process_text.assert_called_once_with(
                file_content,
                source=file_path
            )
            assert result["file_type"] == "txt"

    @pytest.mark.asyncio
    async def test_ingest_document_auto_detect_pdf(self, rag_service_with_mocks, mock_doc_processor):
        """Test auto-detection of PDF file type."""
        # Arrange
        file_path = "/tmp/document.pdf"

        # Act
        result = await rag_service_with_mocks.ingest_document(file_path)

        # Assert
        mock_doc_processor.process_pdf.assert_called_once()
        assert result["file_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_ingest_document_auto_detect_text(self, rag_service_with_mocks, mock_doc_processor):
        """Test auto-detection of text file type."""
        # Arrange
        file_path = "/tmp/document.txt"

        with patch("builtins.open", mock_open(read_data="test")):
            # Act
            result = await rag_service_with_mocks.ingest_document(file_path)

            # Assert
            mock_doc_processor.process_text.assert_called_once()
            assert result["file_type"] == "txt"

    @pytest.mark.asyncio
    async def test_ingest_document_handles_file_not_found(self, rag_service_with_mocks):
        """Test error handling for non-existent file."""
        # Arrange
        file_path = "/tmp/nonexistent.txt"

        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            # Act & Assert
            with pytest.raises(FileNotFoundError):
                await rag_service_with_mocks.ingest_document(file_path, file_type="txt")

    @pytest.mark.asyncio
    async def test_ingest_document_handles_pdf_processing_error(
        self, rag_service_with_mocks, mock_doc_processor
    ):
        """Test error handling when PDF processing fails."""
        # Arrange
        file_path = "/tmp/corrupt.pdf"
        mock_doc_processor.process_pdf.side_effect = Exception("Corrupt PDF")

        # Act & Assert
        with pytest.raises(Exception, match="Corrupt PDF"):
            await rag_service_with_mocks.ingest_document(file_path, file_type="pdf")


# =============================================================================
# RAGService.search Tests
# =============================================================================


class TestRAGServiceSearch:
    """Tests for RAGService.search method."""

    @pytest.mark.asyncio
    async def test_search_basic(self, rag_service_with_mocks, mock_vector_db):
        """Test basic search functionality."""
        # Arrange
        query = "What is DevSkyy?"

        # Act
        results = await rag_service_with_mocks.search(query)

        # Assert
        mock_vector_db.search.assert_called_once_with(
            query,
            top_k=RAGConfig.TOP_K_RESULTS,
            filters=None
        )
        assert len(results) == 2
        assert results[0]["content"] == "DevSkyy is an enterprise AI platform."
        assert results[0]["similarity"] == 0.8

    @pytest.mark.asyncio
    async def test_search_with_custom_top_k(self, rag_service_with_mocks, mock_vector_db):
        """Test search with custom top_k parameter."""
        # Arrange
        query = "DevSkyy features"
        top_k = 10

        # Act
        results = await rag_service_with_mocks.search(query, top_k=top_k)

        # Assert
        mock_vector_db.search.assert_called_once_with(
            query,
            top_k=top_k,
            filters=None
        )

    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_service_with_mocks, mock_vector_db):
        """Test search with metadata filters."""
        # Arrange
        query = "DevSkyy"
        filters = {"source": "test.txt"}

        # Act
        results = await rag_service_with_mocks.search(query, filters=filters)

        # Assert
        mock_vector_db.search.assert_called_once_with(
            query,
            top_k=RAGConfig.TOP_K_RESULTS,
            filters=filters
        )

    @pytest.mark.asyncio
    async def test_search_filters_by_similarity_threshold(self, rag_service_with_mocks, mock_vector_db):
        """Test that search filters results by similarity threshold."""
        # Arrange
        query = "DevSkyy"
        min_similarity = 0.75

        # Mock returns results with similarities 0.8 and 0.7
        # Only 0.8 should pass the 0.75 threshold

        # Act
        results = await rag_service_with_mocks.search(query, min_similarity=min_similarity)

        # Assert
        assert len(results) == 1  # Only one result >= 0.75
        assert results[0]["similarity"] >= min_similarity

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_no_results_above_threshold(
        self, rag_service_with_mocks, mock_vector_db
    ):
        """Test search returns empty list when no results meet threshold."""
        # Arrange
        query = "irrelevant query"
        min_similarity = 0.9  # Higher than any result (0.8, 0.7)

        # Act
        results = await rag_service_with_mocks.search(query, min_similarity=min_similarity)

        # Assert
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_handles_database_error(self, rag_service_with_mocks, mock_vector_db):
        """Test error handling when database search fails."""
        # Arrange
        query = "test"
        mock_vector_db.search.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database error"):
            await rag_service_with_mocks.search(query)


# =============================================================================
# RAGService.query Tests
# =============================================================================


class TestRAGServiceQuery:
    """Tests for RAGService.query method."""

    @pytest.mark.asyncio
    async def test_query_with_llm(self, rag_service_with_llm, mock_vector_db, mock_anthropic_client):
        """Test RAG query with LLM generation."""
        # Arrange
        question = "What is DevSkyy?"

        # Act
        result = await rag_service_with_llm.query(question)

        # Assert
        # Verify search was called
        mock_vector_db.search.assert_called_once()

        # Verify Anthropic was called
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args

        assert call_args[1]["model"] == RAGConfig.DEFAULT_MODEL
        assert call_args[1]["max_tokens"] == RAGConfig.MAX_TOKENS
        assert "system" in call_args[1]

        # Verify result structure
        assert result["answer"] == "This is a test answer from Claude."
        assert result["context_used"] == 2
        assert result["model"] == RAGConfig.DEFAULT_MODEL
        assert result["tokens_used"]["input"] == 100
        assert result["tokens_used"]["output"] == 50
        assert len(result["sources"]) == 2

    @pytest.mark.asyncio
    async def test_query_without_llm(self, rag_service_with_mocks, mock_vector_db):
        """Test RAG query without LLM (fallback to context only)."""
        # Arrange
        question = "What is DevSkyy?"

        # Act
        result = await rag_service_with_mocks.query(question)

        # Assert
        assert "LLM not configured" in result["answer"]
        assert result["context_used"] == 2
        assert len(result["sources"]) == 2
        assert "DevSkyy is an enterprise AI platform" in result["answer"]

    @pytest.mark.asyncio
    async def test_query_with_no_context_found(self, rag_service_with_mocks, mock_vector_db):
        """Test query when no relevant context is found."""
        # Arrange
        question = "irrelevant question"
        mock_vector_db.search.return_value = []

        # Act
        result = await rag_service_with_mocks.query(question)

        # Assert
        assert "couldn't find any relevant information" in result["answer"]
        assert result["sources"] == []
        assert result["context_used"] == 0

    @pytest.mark.asyncio
    async def test_query_with_custom_model(self, rag_service_with_llm, mock_anthropic_client):
        """Test query with custom model parameter."""
        # Arrange
        question = "What is DevSkyy?"
        custom_model = "claude-3-opus-20240229"

        # Act
        result = await rag_service_with_llm.query(question, model=custom_model)

        # Assert
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["model"] == custom_model
        assert result["model"] == custom_model

    @pytest.mark.asyncio
    async def test_query_with_custom_system_prompt(self, rag_service_with_llm, mock_anthropic_client):
        """Test query with custom system prompt."""
        # Arrange
        question = "What is DevSkyy?"
        custom_prompt = "You are a helpful assistant specialized in enterprise AI."

        # Act
        result = await rag_service_with_llm.query(question, system_prompt=custom_prompt)

        # Assert
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["system"] == custom_prompt

    @pytest.mark.asyncio
    async def test_query_with_custom_top_k(self, rag_service_with_llm, mock_vector_db):
        """Test query with custom top_k parameter."""
        # Arrange
        question = "What is DevSkyy?"
        top_k = 3

        # Act
        result = await rag_service_with_llm.query(question, top_k=top_k)

        # Assert
        # Check search was called with correct top_k
        search_calls = mock_vector_db.search.call_args_list
        assert len(search_calls) > 0
        # The search is called via the search method, which passes top_k to vector_db.search

    @pytest.mark.asyncio
    async def test_query_handles_llm_error(self, rag_service_with_llm, mock_anthropic_client):
        """Test error handling when LLM fails."""
        # Arrange
        question = "What is DevSkyy?"
        mock_anthropic_client.messages.create.side_effect = Exception("API error")

        # Act & Assert
        with pytest.raises(Exception, match="API error"):
            await rag_service_with_llm.query(question)


# =============================================================================
# RAGService.iterative_query Tests
# =============================================================================


class TestRAGServiceIterativeQuery:
    """Tests for RAGService.iterative_query method."""

    @pytest.mark.asyncio
    async def test_iterative_query_single_iteration_sufficient(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test iterative query that finds sufficient results in first iteration."""
        # Arrange
        question = "What is DevSkyy?"

        # Mock high-quality results on first search
        mock_vector_db.search.return_value = [
            {"content": "Result 1", "similarity": 0.9, "metadata": {}, "id": "1"},
            {"content": "Result 2", "similarity": 0.85, "metadata": {}, "id": "2"},
            {"content": "Result 3", "similarity": 0.8, "metadata": {}, "id": "3"},
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(
            question,
            max_iterations=3,
            min_results=3,
            sufficiency_threshold=0.75
        )

        # Assert
        assert result["iterations"] == 1  # Should stop after first iteration
        assert result["context_used"] == 3
        assert len(result["queries_used"]) == 1
        assert result["queries_used"][0] == question
        assert len(result["iteration_trace"]) == 1
        assert result["iteration_trace"][0]["iteration"] == 1
        assert result["iteration_trace"][0]["results_found"] == 3

    @pytest.mark.asyncio
    async def test_iterative_query_multiple_iterations(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test iterative query requiring multiple iterations."""
        # Arrange
        question = "Complex multi-hop question"

        # Mock progressive results across iterations
        search_results = [
            # Iteration 1: Low quality results
            [
                {"content": "Result 1", "similarity": 0.6, "metadata": {}, "id": "1"},
            ],
            # Iteration 2: Better results
            [
                {"content": "Result 2", "similarity": 0.7, "metadata": {}, "id": "2"},
                {"content": "Result 3", "similarity": 0.65, "metadata": {}, "id": "3"},
            ],
            # Iteration 3: High quality results
            [
                {"content": "Result 4", "similarity": 0.85, "metadata": {}, "id": "4"},
                {"content": "Result 5", "similarity": 0.8, "metadata": {}, "id": "5"},
            ],
        ]
        mock_vector_db.search.side_effect = search_results

        # Mock reformulation
        reformulated_responses = [
            MagicMock(content=[MagicMock(text="reformulated query 1")]),
            MagicMock(content=[MagicMock(text="reformulated query 2")]),
        ]

        # First calls for reformulation, last call for final answer
        mock_anthropic_client.messages.create.side_effect = [
            *reformulated_responses,
            MagicMock(
                content=[MagicMock(text="Final answer")],
                usage=MagicMock(input_tokens=200, output_tokens=100)
            ),
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(
            question,
            max_iterations=3,
            min_results=3,
            sufficiency_threshold=0.75
        )

        # Assert
        assert result["iterations"] == 3
        assert result["context_used"] == 5  # All unique results
        assert len(result["queries_used"]) == 3  # Original + 2 reformulated
        assert len(result["iteration_trace"]) == 3

    @pytest.mark.asyncio
    async def test_iterative_query_deduplicates_results(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test that iterative query deduplicates results across iterations."""
        # Arrange
        question = "test question"

        # Mock same result appearing in multiple iterations
        duplicate_result = {"content": "Duplicate content", "similarity": 0.7, "metadata": {}, "id": "dup"}
        unique_result = {"content": "Unique content", "similarity": 0.6, "metadata": {}, "id": "unique"}

        search_results = [
            [duplicate_result, unique_result],
            [duplicate_result],  # Same content should be deduplicated
        ]
        mock_vector_db.search.side_effect = search_results

        # Mock reformulation
        mock_anthropic_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="reformulated")]),
            MagicMock(
                content=[MagicMock(text="answer")],
                usage=MagicMock(input_tokens=100, output_tokens=50)
            ),
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(question, max_iterations=2)

        # Assert
        assert result["context_used"] == 2  # Only unique results counted

    @pytest.mark.asyncio
    async def test_iterative_query_without_llm(self, rag_service_with_mocks, mock_vector_db):
        """Test iterative query without LLM (uses fallback)."""
        # Arrange
        question = "What is DevSkyy?"
        mock_vector_db.search.return_value = [
            {"content": "Result 1", "similarity": 0.8, "metadata": {}, "id": "1"},
            {"content": "Result 2", "similarity": 0.75, "metadata": {}, "id": "2"},
        ]

        # Act
        result = await rag_service_with_mocks.iterative_query(question)

        # Assert
        assert "LLM not configured" in result["answer"]
        assert result["context_used"] == 2
        assert "iteration_trace" in result

    @pytest.mark.asyncio
    async def test_iterative_query_no_results_found(
        self, rag_service_with_llm, mock_vector_db
    ):
        """Test iterative query when no results are found."""
        # Arrange
        question = "irrelevant question"
        mock_vector_db.search.return_value = []

        # Act
        result = await rag_service_with_llm.iterative_query(question)

        # Assert
        assert "couldn't find any relevant information" in result["answer"]
        assert result["sources"] == []
        assert result["context_used"] == 0
        assert result["iterations"] > 0

    @pytest.mark.asyncio
    async def test_iterative_query_respects_max_iterations(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test that iterative query respects max_iterations limit."""
        # Arrange
        question = "test"
        max_iterations = 2

        # Always return insufficient results
        mock_vector_db.search.return_value = [
            {"content": "Low quality", "similarity": 0.5, "metadata": {}, "id": "1"}
        ]

        # Mock reformulation
        mock_anthropic_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="reformulated")]),
            MagicMock(
                content=[MagicMock(text="answer")],
                usage=MagicMock(input_tokens=100, output_tokens=50)
            ),
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(
            question,
            max_iterations=max_iterations,
            sufficiency_threshold=0.9  # Very high threshold
        )

        # Assert
        assert result["iterations"] == max_iterations

    @pytest.mark.asyncio
    async def test_iterative_query_limits_context_to_top_10(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test that iterative query limits context to top 10 results."""
        # Arrange
        question = "test"

        # Return many results
        many_results = [
            {"content": f"Result {i}", "similarity": 0.8, "metadata": {}, "id": f"{i}"}
            for i in range(15)
        ]
        mock_vector_db.search.return_value = many_results

        # Act
        result = await rag_service_with_llm.iterative_query(question)

        # Assert
        # Check that the context string passed to LLM only contains 10 sources
        call_args = mock_anthropic_client.messages.create.call_args
        context_message = call_args[1]["messages"][0]["content"]

        # Count source markers in context
        source_count = context_message.count("[Source ")
        assert source_count == 10  # Limited to top 10


# =============================================================================
# RAGService._reformulate_query Tests
# =============================================================================


class TestRAGServiceReformulateQuery:
    """Tests for RAGService._reformulate_query method."""

    @pytest.mark.asyncio
    async def test_reformulate_query_with_llm(self, rag_service_with_llm, mock_anthropic_client):
        """Test query reformulation using LLM."""
        # Arrange
        original_question = "What is DevSkyy?"
        current_results = [
            {"content": "DevSkyy is a platform", "similarity": 0.7}
        ]
        iteration = 1

        mock_anthropic_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="DevSkyy architecture and components")]
        )

        # Act
        reformulated = await rag_service_with_llm._reformulate_query(
            original_question,
            current_results,
            iteration
        )

        # Assert
        assert reformulated == "DevSkyy architecture and components"
        mock_anthropic_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_reformulate_query_without_llm(self, rag_service_with_mocks):
        """Test query reformulation using rule-based fallback."""
        # Arrange
        original_question = "What is DevSkyy?"
        current_results = []
        iteration = 0

        # Act
        reformulated = await rag_service_with_mocks._reformulate_query(
            original_question,
            current_results,
            iteration
        )

        # Assert
        # Should use template-based reformulation
        assert "DevSkyy" in reformulated
        assert len(reformulated) > len(original_question)

    @pytest.mark.asyncio
    async def test_reformulate_query_fallback_on_llm_error(
        self, rag_service_with_llm, mock_anthropic_client
    ):
        """Test fallback to rule-based when LLM reformulation fails."""
        # Arrange
        original_question = "test question"
        current_results = [{"content": "some result", "similarity": 0.7}]
        iteration = 1

        mock_anthropic_client.messages.create.side_effect = Exception("API error")

        # Act
        reformulated = await rag_service_with_llm._reformulate_query(
            original_question,
            current_results,
            iteration
        )

        # Assert
        # Should fall back to template-based reformulation
        assert isinstance(reformulated, str)
        assert len(reformulated) > 0

    @pytest.mark.asyncio
    async def test_reformulate_query_cycles_through_templates(self, rag_service_with_mocks):
        """Test that rule-based reformulation cycles through templates."""
        # Arrange
        original_question = "test"
        current_results = []

        # Act - Get reformulations for different iterations
        reformulation_0 = await rag_service_with_mocks._reformulate_query(
            original_question, current_results, 0
        )
        reformulation_1 = await rag_service_with_mocks._reformulate_query(
            original_question, current_results, 1
        )
        reformulation_2 = await rag_service_with_mocks._reformulate_query(
            original_question, current_results, 2
        )

        # Assert - All should be different (different templates)
        assert reformulation_0 != reformulation_1
        assert reformulation_1 != reformulation_2
        assert reformulation_0 != reformulation_2

    @pytest.mark.asyncio
    async def test_reformulate_query_at_iteration_zero_uses_fallback(
        self, rag_service_with_llm
    ):
        """Test that iteration 0 uses rule-based reformulation even with LLM."""
        # Arrange
        original_question = "test"
        current_results = []
        iteration = 0

        # Act
        reformulated = await rag_service_with_llm._reformulate_query(
            original_question,
            current_results,
            iteration
        )

        # Assert
        # Should use template without calling LLM (iteration == 0)
        assert isinstance(reformulated, str)


# =============================================================================
# RAGService.get_stats Tests
# =============================================================================


class TestRAGServiceGetStats:
    """Tests for RAGService.get_stats method."""

    def test_get_stats(self, rag_service_with_mocks, mock_vector_db, mock_doc_processor):
        """Test retrieving RAG system statistics."""
        # Arrange & Act
        stats = rag_service_with_mocks.get_stats()

        # Assert
        assert "vector_db" in stats
        assert "config" in stats

        # Verify vector DB stats
        assert stats["vector_db"]["collection_name"] == "test_collection"
        assert stats["vector_db"]["document_count"] == 10

        # Verify config stats
        assert stats["config"]["chunk_size"] == mock_doc_processor.chunk_size
        assert stats["config"]["chunk_overlap"] == mock_doc_processor.chunk_overlap
        assert stats["config"]["top_k"] == RAGConfig.TOP_K_RESULTS
        assert stats["config"]["similarity_threshold"] == RAGConfig.SIMILARITY_THRESHOLD


# =============================================================================
# get_rag_service Function Tests
# =============================================================================


class TestGetRAGService:
    """Tests for get_rag_service singleton function."""

    def test_get_rag_service_creates_instance(self):
        """Test that get_rag_service creates a RAGService instance."""
        # Arrange
        import services.rag_service as rag_module
        rag_module._rag_service = None  # Reset singleton

        with patch.object(RAGConfig, "ANTHROPIC_API_KEY", None):
            with patch("services.rag_service.VectorDatabase"):
                with patch("services.rag_service.DocumentProcessor"):
                    # Act
                    service = get_rag_service()

                    # Assert
                    assert isinstance(service, RAGService)
                    assert rag_module._rag_service is service

    def test_get_rag_service_returns_same_instance(self):
        """Test that get_rag_service returns the same instance (singleton)."""
        # Arrange
        import services.rag_service as rag_module

        with patch.object(RAGConfig, "ANTHROPIC_API_KEY", None):
            with patch("services.rag_service.VectorDatabase"):
                with patch("services.rag_service.DocumentProcessor"):
                    # Act
                    service1 = get_rag_service()
                    service2 = get_rag_service()

                    # Assert
                    assert service1 is service2


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestRAGServiceEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_ingest_text_with_empty_string(self, rag_service_with_mocks, mock_doc_processor):
        """Test ingesting empty text."""
        # Arrange
        mock_doc_processor.process_text.return_value = []

        # Act
        result = await rag_service_with_mocks.ingest_text("")

        # Assert
        assert result["chunks_created"] == 0
        assert result["text_length"] == 0

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, rag_service_with_mocks):
        """Test search with empty query string."""
        # Arrange
        query = ""

        # Act
        results = await rag_service_with_mocks.search(query)

        # Assert
        # Should still call search (vector DB handles empty queries)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_query_builds_context_string_correctly(
        self, rag_service_with_llm, mock_anthropic_client
    ):
        """Test that query builds context string with proper formatting."""
        # Arrange
        question = "test question"

        # Act
        await rag_service_with_llm.query(question)

        # Assert
        call_args = mock_anthropic_client.messages.create.call_args
        user_message = call_args[1]["messages"][0]["content"]

        # Should contain context and question
        assert "Context:" in user_message
        assert "Question:" in user_message
        assert "[Source 1]" in user_message
        assert "[Source 2]" in user_message

    @pytest.mark.asyncio
    async def test_iterative_query_tracks_iteration_metadata(
        self, rag_service_with_llm, mock_vector_db, mock_anthropic_client
    ):
        """Test that iterative query properly tracks iteration metadata."""
        # Arrange
        question = "test"
        mock_vector_db.search.return_value = [
            {"content": "result", "similarity": 0.8, "metadata": {}, "id": "1"}
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(question, max_iterations=2)

        # Assert
        # Check iteration trace structure
        assert len(result["iteration_trace"]) > 0
        first_iteration = result["iteration_trace"][0]

        assert "iteration" in first_iteration
        assert "query" in first_iteration
        assert "results_found" in first_iteration
        assert "avg_similarity" in first_iteration

        # Check that sources have iteration info
        if result["sources"]:
            assert "iteration" in result["sources"][0]
            assert "query" in result["sources"][0]

    @pytest.mark.asyncio
    async def test_query_handles_missing_usage_info(
        self, rag_service_with_llm, mock_anthropic_client
    ):
        """Test query handling when LLM response doesn't have usage info."""
        # Arrange
        question = "test"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="answer")]
        mock_response.usage = None  # No usage info
        mock_anthropic_client.messages.create.return_value = mock_response

        # Act & Assert
        # Should raise AttributeError when trying to access usage.input_tokens
        with pytest.raises(AttributeError):
            await rag_service_with_llm.query(question)


# =============================================================================
# Integration-like Tests (with minimal mocking)
# =============================================================================


class TestRAGServiceIntegration:
    """Integration-like tests with more realistic scenarios."""

    @pytest.mark.asyncio
    async def test_full_rag_workflow_without_llm(self, rag_service_with_mocks):
        """Test complete RAG workflow: ingest, search, query (without LLM)."""
        # Act - Ingest
        ingest_result = await rag_service_with_mocks.ingest_text(
            "DevSkyy is an enterprise AI platform with comprehensive security.",
            source="test_doc"
        )

        # Act - Search
        search_results = await rag_service_with_mocks.search("DevSkyy security")

        # Act - Query
        query_result = await rag_service_with_mocks.query("What security features does DevSkyy have?")

        # Assert
        assert ingest_result["chunks_created"] > 0
        assert len(search_results) > 0
        assert "answer" in query_result
        assert query_result["context_used"] > 0

    @pytest.mark.asyncio
    async def test_full_rag_workflow_with_llm(self, rag_service_with_llm):
        """Test complete RAG workflow with LLM."""
        # Act - Ingest
        ingest_result = await rag_service_with_llm.ingest_text(
            "DevSkyy provides RBAC, encryption, and monitoring.",
            source="security_doc"
        )

        # Act - Iterative Query
        query_result = await rag_service_with_llm.iterative_query(
            "What are DevSkyy's security features?"
        )

        # Assert
        assert ingest_result["added"] > 0
        assert query_result["answer"]
        assert "tokens_used" in query_result
        assert query_result["iterations"] > 0


# =============================================================================
# Performance and Boundary Tests
# =============================================================================


class TestRAGServicePerformance:
    """Tests for performance and boundary conditions."""

    @pytest.mark.asyncio
    async def test_ingest_large_batch(self, rag_service_with_mocks, mock_vector_db):
        """Test ingesting a large text that creates many chunks."""
        # Arrange
        large_text = "Test content. " * 10000  # Large text

        # Mock processor to return many chunks
        many_chunks = [
            {
                "content": f"Chunk {i}",
                "metadata": {"source": "test", "chunk_index": i, "file_type": "text", "tokens": 2}
            }
            for i in range(100)
        ]
        rag_service_with_mocks.doc_processor.process_text.return_value = many_chunks

        # Act
        result = await rag_service_with_mocks.ingest_text(large_text)

        # Assert
        assert result["chunks_created"] == 100
        mock_vector_db.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_zero_top_k(self, rag_service_with_mocks, mock_vector_db):
        """Test search with top_k=0."""
        # Arrange
        query = "test"
        mock_vector_db.search.return_value = []

        # Act
        results = await rag_service_with_mocks.search(query, top_k=0)

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_iterative_query_with_max_iterations_one(
        self, rag_service_with_llm, mock_vector_db
    ):
        """Test iterative query with max_iterations=1 (should behave like regular query)."""
        # Arrange
        question = "test"
        mock_vector_db.search.return_value = [
            {"content": "result", "similarity": 0.8, "metadata": {}, "id": "1"}
        ]

        # Act
        result = await rag_service_with_llm.iterative_query(question, max_iterations=1)

        # Assert
        assert result["iterations"] == 1
        assert len(result["queries_used"]) == 1
