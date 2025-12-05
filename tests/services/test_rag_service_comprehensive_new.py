"""
Comprehensive Test Suite for RAG Service
Tests document ingestion, vector search, and query capabilities

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #1: Never guess - All behaviors verified
- Rule #12: Performance SLOs - P95 < 500ms for search operations
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data"""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model"""
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1] * 384]  # 384-dim embeddings
    return mock_model


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


class TestRAGConfig:
    """Test RAG configuration"""

    @pytest.mark.unit
    def test_rag_config_has_all_required_fields(self):
        """Test RAGConfig has all required configuration fields"""
        from services.rag_service import RAGConfig

        assert hasattr(RAGConfig, "CHROMA_PERSIST_DIR")
        assert hasattr(RAGConfig, "CHROMA_COLLECTION_NAME")
        assert hasattr(RAGConfig, "EMBEDDING_MODEL")
        assert hasattr(RAGConfig, "CHUNK_SIZE")
        assert hasattr(RAGConfig, "CHUNK_OVERLAP")
        assert hasattr(RAGConfig, "TOP_K_RESULTS")

    @pytest.mark.unit
    def test_rag_config_chunk_size_valid(self):
        """Test chunk size is reasonable"""
        from services.rag_service import RAGConfig

        assert 500 <= RAGConfig.CHUNK_SIZE <= 2000
        assert 0 < RAGConfig.CHUNK_OVERLAP < RAGConfig.CHUNK_SIZE

    @pytest.mark.unit
    def test_rag_config_top_k_valid(self):
        """Test TOP_K is in reasonable range"""
        from services.rag_service import RAGConfig

        assert 1 <= RAGConfig.TOP_K_RESULTS <= 20


class TestDocumentProcessor:
    """Test document processing and chunking"""

    @pytest.mark.unit
    def test_document_processor_initializes(self):
        """Test DocumentProcessor initializes correctly"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor()
        assert processor.chunk_size > 0
        assert processor.chunk_overlap >= 0
        assert processor.text_splitter is not None

    @pytest.mark.unit
    def test_process_text_creates_chunks(self):
        """Test text processing creates proper chunks"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "Test content. " * 50  # Create long text

        chunks = processor.process_text(text, source="test.txt")

        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all(chunk["metadata"]["source"] == "test.txt" for chunk in chunks)

    @pytest.mark.unit
    def test_process_text_single_chunk_for_short_text(self):
        """Test short text creates single chunk"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        text = "Short test content."

        chunks = processor.process_text(text)

        assert len(chunks) == 1
        assert chunks[0]["content"] == text

    @pytest.mark.unit
    def test_process_text_includes_metadata(self):
        """Test chunks include metadata"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor()
        chunks = processor.process_text("Test", source="test.txt")

        assert "metadata" in chunks[0]
        assert "source" in chunks[0]["metadata"]
        assert "chunk_index" in chunks[0]["metadata"]
        assert "total_chunks" in chunks[0]["metadata"]

    @pytest.mark.unit
    def test_calculate_chunk_hash_deterministic(self):
        """Test chunk hash is deterministic"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor()
        content = "Test content for hashing"

        hash1 = processor.calculate_chunk_hash(content)
        hash2 = processor.calculate_chunk_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    @pytest.mark.unit
    def test_calculate_chunk_hash_different_for_different_content(self):
        """Test different content produces different hashes"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor()

        hash1 = processor.calculate_chunk_hash("Content A")
        hash2 = processor.calculate_chunk_hash("Content B")

        assert hash1 != hash2

    @pytest.mark.unit
    @patch("services.rag_service.PdfReader")
    def test_process_pdf_extracts_text(self, mock_pdf_reader, temp_dir):
        """Test PDF processing extracts text"""
        from services.rag_service import DocumentProcessor

        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content text"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf_reader.return_value = mock_pdf

        processor = DocumentProcessor()
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_text("fake pdf")  # Create fake file

        chunks = processor.process_pdf(str(pdf_path))

        assert len(chunks) > 0
        assert any("PDF content text" in chunk["content"] for chunk in chunks)

    @pytest.mark.unit
    def test_process_empty_text_returns_empty_list(self):
        """Test processing empty text returns empty list"""
        from services.rag_service import DocumentProcessor

        processor = DocumentProcessor()
        chunks = processor.process_text("")

        assert len(chunks) == 0


class TestVectorDatabase:
    """Test vector database operations"""

    @pytest.mark.unit
    @patch("services.rag_service.chromadb")
    @patch("services.rag_service.SentenceTransformer")
    def test_vector_db_initializes(self, mock_transformer, mock_chromadb, temp_dir):
        """Test VectorDatabase initializes correctly"""
        from services.rag_service import VectorDatabase

        mock_chromadb.PersistentClient.return_value = MagicMock()
        mock_transformer.return_value = MagicMock()

        db = VectorDatabase(persist_dir=str(temp_dir))

        assert db.client is not None
        assert db.embedding_model is not None

    @pytest.mark.unit
    @patch("services.rag_service.chromadb")
    @patch("services.rag_service.SentenceTransformer")
    def test_add_documents_stores_chunks(self, mock_transformer, mock_chromadb, temp_dir):
        """Test adding documents to vector store"""
        from services.rag_service import VectorDatabase

        # Setup mocks
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        db = VectorDatabase(persist_dir=str(temp_dir))

        chunks = [
            {"content": "Test content", "metadata": {"source": "test.txt", "chunk_index": 0}},
        ]

        result = db.add_documents(chunks, "test-doc")

        assert result["status"] == "success"
        assert result["chunks_added"] == 1
        mock_collection.add.assert_called_once()

    @pytest.mark.unit
    @patch("services.rag_service.chromadb")
    @patch("services.rag_service.SentenceTransformer")
    def test_search_returns_relevant_results(self, mock_transformer, mock_chromadb, temp_dir):
        """Test search returns relevant documents"""
        from services.rag_service import VectorDatabase

        # Setup mocks
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Content 1", "Content 2"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"source": "test.txt"}, {"source": "test2.txt"}]],
        }

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        db = VectorDatabase(persist_dir=str(temp_dir))

        results = db.search("test query", top_k=2)

        assert len(results) == 2
        assert results[0]["content"] == "Content 1"
        assert results[1]["content"] == "Content 2"
        assert results[0]["similarity_score"] >= results[1]["similarity_score"]

    @pytest.mark.unit
    @patch("services.rag_service.chromadb")
    @patch("services.rag_service.SentenceTransformer")
    def test_search_filters_by_similarity_threshold(self, mock_transformer, mock_chromadb, temp_dir):
        """Test search filters results by similarity threshold"""
        from services.rag_service import VectorDatabase

        # Setup mocks - distances are 1 - similarity_score in ChromaDB
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [["High similarity", "Medium similarity", "Low similarity"]],
            "distances": [[0.1, 0.4, 0.8]],  # distances: 0.1, 0.4, 0.8 -> similarities: 0.9, 0.6, 0.2
            "metadatas": [[{"source": "test.txt"}] * 3],
        }

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        db = VectorDatabase(persist_dir=str(temp_dir))

        # Filter with threshold 0.7 - should only return first result
        results = db.search("test query", top_k=10, similarity_threshold=0.7)

        # Only results with similarity >= 0.7 should be returned
        assert all(r["similarity_score"] >= 0.7 for r in results)

    @pytest.mark.unit
    @patch("services.rag_service.chromadb")
    @patch("services.rag_service.SentenceTransformer")
    def test_get_stats_returns_collection_stats(self, mock_transformer, mock_chromadb, temp_dir):
        """Test getting collection statistics"""
        from services.rag_service import VectorDatabase

        mock_collection = MagicMock()
        mock_collection.count.return_value = 100

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        mock_transformer.return_value = MagicMock()

        db = VectorDatabase(persist_dir=str(temp_dir))

        stats = db.get_stats()

        assert "total_documents" in stats
        assert stats["total_documents"] == 100
        assert "collection_name" in stats


class TestRAGService:
    """Test RAG service integration"""

    @pytest.mark.unit
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    def test_rag_service_initializes(self, mock_anthropic, mock_processor, mock_vector_db):
        """Test RAGService initializes correctly"""
        from services.rag_service import RAGService

        service = RAGService()

        assert service.processor is not None
        assert service.vector_db is not None

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_ingest_text_processes_and_stores(self, mock_anthropic, mock_processor_class, mock_vector_db_class):
        """Test ingesting text document"""
        from services.rag_service import RAGService

        # Setup mocks
        mock_processor = MagicMock()
        mock_processor.process_text.return_value = [{"content": "chunk", "metadata": {}}]
        mock_processor_class.return_value = mock_processor

        mock_db = MagicMock()
        mock_db.add_documents.return_value = {"status": "success", "chunks_added": 1}
        mock_vector_db_class.return_value = mock_db

        service = RAGService()

        result = await service.ingest_text("Test content", source="test.txt")

        assert result["status"] == "success"
        assert result["chunks_added"] >= 1
        mock_processor.process_text.assert_called_once()
        mock_db.add_documents.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_search_returns_relevant_documents(self, mock_anthropic, mock_processor, mock_vector_db_class):
        """Test searching for documents"""
        from services.rag_service import RAGService

        mock_db = MagicMock()
        mock_db.search.return_value = [
            {"content": "Result 1", "similarity_score": 0.9, "metadata": {}},
            {"content": "Result 2", "similarity_score": 0.8, "metadata": {}},
        ]
        mock_vector_db_class.return_value = mock_db

        service = RAGService()

        results = await service.search("test query", top_k=2)

        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.9
        mock_db.search.assert_called_once_with("test query", top_k=2, similarity_threshold=0.7)

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_query_generates_answer_with_context(self, mock_anthropic_class, mock_processor, mock_vector_db_class):
        """Test RAG query generates answer with retrieved context"""
        from services.rag_service import RAGService

        # Setup vector DB mock
        mock_db = MagicMock()
        mock_db.search.return_value = [
            {"content": "Context 1", "similarity_score": 0.9, "metadata": {"source": "doc1"}},
            {"content": "Context 2", "similarity_score": 0.8, "metadata": {"source": "doc2"}},
        ]
        mock_vector_db_class.return_value = mock_db

        # Setup Anthropic mock
        mock_anthropic = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Generated answer based on context")]
        mock_anthropic.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_anthropic

        service = RAGService()

        result = await service.query("What is the answer?")

        assert result["status"] == "success"
        assert "answer" in result
        assert result["answer"] == "Generated answer based on context"
        assert "sources" in result
        assert len(result["sources"]) == 2

        # Verify Anthropic was called with proper context
        mock_anthropic.messages.create.assert_called_once()
        call_args = mock_anthropic.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert any("Context 1" in str(msg) for msg in messages)
        assert any("Context 2" in str(msg) for msg in messages)

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_query_handles_no_context_found(self, mock_anthropic_class, mock_processor, mock_vector_db_class):
        """Test query handles case when no relevant context is found"""
        from services.rag_service import RAGService

        mock_db = MagicMock()
        mock_db.search.return_value = []  # No results found
        mock_vector_db_class.return_value = mock_db

        mock_anthropic = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="I don't have enough context to answer")]
        mock_anthropic.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_anthropic

        service = RAGService()

        result = await service.query("Obscure question?")

        assert result["status"] == "success"
        assert len(result["sources"]) == 0

    @pytest.mark.unit
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    def test_get_stats_returns_service_stats(self, mock_anthropic, mock_processor, mock_vector_db_class):
        """Test getting service statistics"""
        from services.rag_service import RAGService

        mock_db = MagicMock()
        mock_db.get_stats.return_value = {"total_documents": 100}
        mock_vector_db_class.return_value = mock_db

        service = RAGService()

        stats = service.get_stats()

        assert "vector_db" in stats
        assert stats["vector_db"]["total_documents"] == 100


class TestRAGServicePerformance:
    """Test RAG service performance requirements"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_search_performance_under_500ms(self, mock_anthropic, mock_processor, mock_vector_db_class):
        """Test search completes in < 500ms (P95 SLO)"""
        import time

        from services.rag_service import RAGService

        mock_db = MagicMock()
        mock_db.search.return_value = [
            {"content": "Result", "similarity_score": 0.9, "metadata": {}}
        ]
        mock_vector_db_class.return_value = mock_db

        service = RAGService()

        start = time.time()
        await service.search("test query")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 500, f"Search took {duration}ms, exceeds 500ms SLO"

    @pytest.mark.performance
    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_ingest_text_completes_quickly(self, mock_anthropic, mock_processor_class, mock_vector_db_class):
        """Test text ingestion completes in reasonable time"""
        import time

        from services.rag_service import RAGService

        mock_processor = MagicMock()
        mock_processor.process_text.return_value = [{"content": "chunk", "metadata": {}}]
        mock_processor_class.return_value = mock_processor

        mock_db = MagicMock()
        mock_db.add_documents.return_value = {"status": "success", "chunks_added": 1}
        mock_vector_db_class.return_value = mock_db

        service = RAGService()

        start = time.time()
        await service.ingest_text("Test content" * 100)
        duration = (time.time() - start) * 1000

        assert duration < 2000, f"Ingestion took {duration}ms, too slow"


class TestRAGServiceErrorHandling:
    """Test RAG service error handling"""

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_query_handles_anthropic_error(self, mock_anthropic_class, mock_processor, mock_vector_db_class):
        """Test query handles Anthropic API errors gracefully"""
        from services.rag_service import RAGService

        mock_db = MagicMock()
        mock_db.search.return_value = [{"content": "Context", "similarity_score": 0.9, "metadata": {}}]
        mock_vector_db_class.return_value = mock_db

        mock_anthropic = MagicMock()
        mock_anthropic.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_anthropic

        service = RAGService()

        result = await service.query("test question")

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    @patch("services.rag_service.VectorDatabase")
    @patch("services.rag_service.DocumentProcessor")
    @patch("services.rag_service.Anthropic")
    async def test_ingest_handles_processing_error(self, mock_anthropic, mock_processor_class, mock_vector_db_class):
        """Test ingestion handles document processing errors"""
        from services.rag_service import RAGService

        mock_processor = MagicMock()
        mock_processor.process_text.side_effect = Exception("Processing failed")
        mock_processor_class.return_value = mock_processor

        service = RAGService()

        result = await service.ingest_text("test content")

        assert result["status"] == "error"
        assert "error" in result
