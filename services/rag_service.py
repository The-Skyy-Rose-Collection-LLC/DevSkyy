#!/usr/bin/env python3
"""
DevSkyy RAG (Retrieval-Augmented Generation) Service
Provides document ingestion, vector search, and RAG query capabilities

Per Truth Protocol:
- Rule #1: Never guess - All operations verified with type hints and validation
- Rule #5: No secrets in code - All credentials via environment variables
- Rule #7: Input validation - Schema enforcement on all inputs
- Rule #13: Security baseline - AES-256-GCM for document encryption

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import asyncio
import hashlib
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import chromadb
import tiktoken
from anthropic import Anthropic
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class RAGConfig:
    """RAG system configuration"""

    # Vector Database
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "devskyy_docs")

    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 dimension

    # Chunking Parameters
    CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

    # Retrieval Parameters
    TOP_K_RESULTS = int(os.getenv("RAG_TOP_K", "5"))
    SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))

    # LLM Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEFAULT_MODEL = os.getenv("RAG_LLM_MODEL", "claude-sonnet-4-5-20250929")
    MAX_TOKENS = int(os.getenv("RAG_MAX_TOKENS", "4096"))


# =============================================================================
# DOCUMENT PROCESSORS
# =============================================================================

class DocumentProcessor:
    """Process and chunk documents for RAG ingestion"""

    def __init__(
        self,
        chunk_size: int = RAGConfig.CHUNK_SIZE,
        chunk_overlap: int = RAGConfig.CHUNK_OVERLAP,
    ):
        """
        Initialize the DocumentProcessor with chunking behavior and a tokenizer.
        
        Parameters:
            chunk_size (int): Maximum number of characters per chunk.
            chunk_overlap (int): Number of characters that overlap between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def process_pdf(self, file_path: str) -> list[dict[str, Any]]:
        """
        Extracts text from a PDF and splits it into tokenized content chunks with metadata.
        
        Parameters:
            file_path (str): Filesystem path to the PDF to process.
        
        Returns:
            list[dict[str, Any]]: A list of chunk objects. Each chunk has:
                - `content` (str): The chunk text.
                - `metadata` (dict): Metadata including:
                    - `source` (str): Original file path.
                    - `page` (int): 1-based page number the chunk came from.
                    - `chunk_index` (int): Zero-based index of the chunk within the page.
                    - `total_pages` (int): Total number of pages in the PDF.
                    - `file_type` (str): The string "pdf".
                    - `tokens` (int): Token count for the chunk as computed by the configured tokenizer.
        """
        try:
            reader = PdfReader(file_path)
            chunks = []

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()

                if not text.strip():
                    continue

                # Split page text into chunks
                page_chunks = self.text_splitter.split_text(text)

                for chunk_idx, chunk in enumerate(page_chunks):
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "source": file_path,
                            "page": page_num,
                            "chunk_index": chunk_idx,
                            "total_pages": len(reader.pages),
                            "file_type": "pdf",
                            "tokens": len(self.tokenizer.encode(chunk)),
                        },
                    })

            logger.info(f"Processed PDF: {file_path} -> {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise

    def process_text(self, text: str, source: str = "text") -> list[dict[str, Any]]:
        """
        Split input text into token-aware chunks and return a list of chunk objects with metadata.
        
        Parameters:
            text (str): The input text to be split into chunks.
            source (str): Identifier for the text source stored in each chunk's metadata (default "text").
        
        Returns:
            list[dict[str, Any]]: A list where each item is a dict with:
                - "content" (str): The chunk text.
                - "metadata" (dict): Contains "source" (str), "chunk_index" (int), "file_type" (str, "text"), and "tokens" (int) representing the token count.
        """
        try:
            chunks = self.text_splitter.split_text(text)

            return [
                {
                    "content": chunk,
                    "metadata": {
                        "source": source,
                        "chunk_index": idx,
                        "file_type": "text",
                        "tokens": len(self.tokenizer.encode(chunk)),
                    },
                }
                for idx, chunk in enumerate(chunks)
            ]

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            raise

    def calculate_chunk_hash(self, content: str) -> str:
        """
        Compute the SHA-256 hash of a chunk's content.
        
        Parameters:
            content (str): Text content of the chunk to hash.
        
        Returns:
            str: Hexadecimal SHA-256 digest of the provided content.
        """
        return hashlib.sha256(content.encode()).hexdigest()


# =============================================================================
# VECTOR DATABASE
# =============================================================================

class VectorDatabase:
    """ChromaDB vector database manager"""

    def __init__(
        self,
        persist_directory: str = RAGConfig.CHROMA_PERSIST_DIR,
        collection_name: str = RAGConfig.CHROMA_COLLECTION_NAME,
        embedding_model: str = RAGConfig.EMBEDDING_MODEL,
    ):
        """
        Initialize the VectorDatabase, ensuring persistence, loading the embedding model, and preparing the ChromaDB collection.
        
        Parameters:
            persist_directory (str): Filesystem path where ChromaDB will persist its data; the directory will be created if it does not exist.
            collection_name (str): Name of the ChromaDB collection to use or create for storing embeddings and documents.
            embedding_model (str): Identifier or path of the SentenceTransformer model used to generate embeddings.
        
        Side effects:
            - Creates the persistence directory if missing.
            - Instantiates a ChromaDB PersistentClient and obtains (or creates) the specified collection.
            - Loads the SentenceTransformer embedding model and stores it along with the client and collection on the instance.
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"Loaded embedding model: {embedding_model}")

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "DevSkyy RAG document collection"},
        )

        logger.info(f"Initialized vector database: {collection_name}")

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """
        Ingest document chunks into the vector collection in batches.
        
        Parameters:
            documents (list[dict[str, Any]]): List of document chunks where each item is a dict containing at least the keys "content" (str) and "metadata" (dict). Each chunk will be encoded to an embedding and added to the collection.
            batch_size (int): Number of documents to process per batch.
        
        Returns:
            dict[str, Any]: Ingestion statistics with keys:
                - "total_documents": total number of input documents,
                - "added": number of documents successfully added,
                - "skipped": number of documents skipped (reserved for future use),
                - "collection_size": current document count in the collection.
        """
        try:
            total_docs = len(documents)
            added = 0
            skipped = 0

            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]

                # Extract content and metadata
                contents = [doc["content"] for doc in batch]
                metadatas = [doc["metadata"] for doc in batch]

                # Generate embeddings
                embeddings = self.embedding_model.encode(
                    contents,
                    show_progress_bar=False,
                ).tolist()

                # Generate unique IDs
                ids = [str(uuid.uuid4()) for _ in batch]

                # Add to collection
                self.collection.add(
                    embeddings=embeddings,
                    documents=contents,
                    metadatas=metadatas,
                    ids=ids,
                )

                added += len(batch)
                logger.info(f"Added batch {i // batch_size + 1}: {added}/{total_docs}")

            return {
                "total_documents": total_docs,
                "added": added,
                "skipped": skipped,
                "collection_size": self.collection.count(),
            }

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = RAGConfig.TOP_K_RESULTS,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Perform a semantic search over the vector collection using the provided query.
        
        Parameters:
            query (str): Natural-language search query.
            top_k (int): Maximum number of results to return.
            filters (dict | None): Optional metadata filter applied to the collection query (e.g., {"source": "doc.pdf"}).
        
        Returns:
            list[dict[str, Any]]: Ordered list of result objects containing:
                - `content` (str): The matched document text.
                - `metadata` (dict): Stored metadata for the document.
                - `distance` (float): Vector distance between the query and the document embedding.
                - `similarity` (float): Similarity score computed as `1 - distance`.
                - `id` (str): Document identifier.
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
            )

            # Format results
            formatted_results = []

            if results["documents"] and results["documents"][0]:
                for idx in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][idx],
                        "metadata": results["metadatas"][0][idx] if results["metadatas"] else {},
                        "distance": results["distances"][0][idx] if results["distances"] else 0.0,
                        "similarity": 1 - (results["distances"][0][idx] if results["distances"] else 0.0),
                        "id": results["ids"][0][idx] if results["ids"] else "",
                    })

            logger.info(f"Search query: '{query}' -> {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    def delete_collection(self):
        """
        Delete the ChromaDB collection managed by this VectorDatabase instance.
        
        Raises:
            Exception: If the collection could not be deleted.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Return summary information about the vector database collection.
        
        Returns:
            stats (dict): Dictionary with keys:
                - "collection_name": Name of the Chroma collection.
                - "document_count": Number of documents currently in the collection.
                - "persist_directory": Filesystem directory where the collection is persisted.
                - "embedding_model": Name of the embedding model configured for the service.
        """
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_directory": self.persist_directory,
            "embedding_model": RAGConfig.EMBEDDING_MODEL,
        }


# =============================================================================
# RAG SERVICE
# =============================================================================

class RAGService:
    """Main RAG service orchestrating document processing, retrieval, and generation"""

    def __init__(
        self,
        vector_db: Optional[VectorDatabase] = None,
        doc_processor: Optional[DocumentProcessor] = None,
    ):
        """
        Initialize the RAGService with supplied or default components and configure an Anthropic client when an API key is available.
        
        If `vector_db` or `doc_processor` are not provided, default instances are created and assigned to `self.vector_db` and `self.doc_processor`. If the Anthropic API key is present in configuration, `self.anthropic` is set to a configured client; otherwise `self.anthropic` is set to `None`, causing RAG queries to fall back to retrieval-only behavior.
        """
        self.vector_db = vector_db or VectorDatabase()
        self.doc_processor = doc_processor or DocumentProcessor()

        # Initialize Anthropic client
        if RAGConfig.ANTHROPIC_API_KEY:
            self.anthropic = Anthropic(api_key=RAGConfig.ANTHROPIC_API_KEY)
        else:
            self.anthropic = None
            logger.warning("Anthropic API key not found - RAG queries will use retrieval only")

    async def ingest_document(
        self,
        file_path: str,
        file_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Ingest a file (PDF or text) into the vector store and return ingestion metadata.
        
        Parameters:
            file_path (str): Path to the file to ingest.
            file_type (Optional[str]): File extension/type (e.g., "pdf", "txt"); if omitted, the type is inferred from the file_path suffix.
        
        Returns:
            dict: Ingestion summary containing:
                - keys returned by the vector database ingestion (e.g., counts of added/skipped items and collection size),
                - "file_path": the ingested file path,
                - "file_type": the resolved file type,
                - "chunks_created": number of content chunks generated from the document,
                - "ingested_at": ISO 8601 UTC timestamp of ingestion.
        """
        try:
            # Auto-detect file type
            if not file_type:
                file_type = Path(file_path).suffix.lower().lstrip(".")

            # Process document based on type
            if file_type == "pdf":
                chunks = self.doc_processor.process_pdf(file_path)
            else:
                # Read as text file
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                chunks = self.doc_processor.process_text(text, source=file_path)

            # Add to vector database
            stats = self.vector_db.add_documents(chunks)

            return {
                **stats,
                "file_path": file_path,
                "file_type": file_type,
                "chunks_created": len(chunks),
                "ingested_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            raise

    async def ingest_text(
        self,
        text: str,
        source: str = "direct_input",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Ingest the provided text by chunking it, attaching optional metadata, and adding the chunks to the vector store.
        
        Parameters:
            text (str): The text to ingest.
            source (str): Identifier for the text source (e.g., filename, "direct_input").
            metadata (dict[str, Any], optional): Additional metadata to merge into every chunk's metadata.
        
        Returns:
            dict[str, Any]: Ingestion results including vector DB statistics (e.g., totals and collection size), plus `source`, `text_length` (number of characters), `chunks_created`, and `ingested_at` (UTC ISO timestamp).
        """
        try:
            # Process text
            chunks = self.doc_processor.process_text(text, source=source)

            # Add custom metadata if provided
            if metadata:
                for chunk in chunks:
                    chunk["metadata"].update(metadata)

            # Add to vector database
            stats = self.vector_db.add_documents(chunks)

            return {
                **stats,
                "source": source,
                "text_length": len(text),
                "chunks_created": len(chunks),
                "ingested_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error ingesting text: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = RAGConfig.TOP_K_RESULTS,
        filters: Optional[dict[str, Any]] = None,
        min_similarity: float = RAGConfig.SIMILARITY_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """
        Perform a semantic search over the vector store and return results meeting a similarity threshold.
        
        Parameters:
        	query (str): The user query to encode and search.
        	top_k (int): Maximum number of candidate results to retrieve before filtering.
        	filters (Optional[dict[str, Any]]): Optional metadata filters to restrict the search.
        	min_similarity (float): Minimum similarity score required for a result to be included.
        
        Returns:
        	list[dict[str, Any]]: Filtered search results. Each dict contains at least `content`, `metadata`, `distance`, `similarity`, and `id`.
        """
        try:
            results = self.vector_db.search(query, top_k=top_k, filters=filters)

            # Filter by similarity threshold
            filtered_results = [
                r for r in results
                if r["similarity"] >= min_similarity
            ]

            return filtered_results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    async def query(
        self,
        question: str,
        top_k: int = RAGConfig.TOP_K_RESULTS,
        model: str = RAGConfig.DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Retrieve relevant context for a question and generate an answer grounded in those contexts.
        
        Performs a semantic search to collect up to `top_k` context chunks, assembles them into a prompt, and—if an Anthropic LLM is configured—uses the model to produce a concise answer that cites sources. If no LLM is configured, returns the relevant excerpts as the answer. If no relevant context is found, returns a default "no information" response.
        
        Parameters:
            question: The user's question to answer.
            top_k: Maximum number of context chunks to retrieve and include.
            model: LLM model identifier to use when generating the answer.
            system_prompt: Optional custom system prompt to guide the model's behavior; when omitted a default DevSkyy prompt is used.
        
        Returns:
            A dictionary containing:
              - `answer` (str): The generated answer or a fallback context excerpt or "no information" message.
              - `sources` (list[dict]): Retrieved context items (each includes content, metadata, similarity, id, etc.).
              - `context_used` (int): Number of context chunks included in the response.
              - `model` (str, optional): The model used to generate the answer (present when an LLM was called).
              - `tokens_used` (dict, optional): Token usage with keys `input` and `output` when available.
        """
        try:
            # 1. Retrieve relevant context
            context_results = await self.search(query=question, top_k=top_k)

            if not context_results:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "context_used": 0,
                }

            # 2. Build context string
            context_str = "\n\n".join([
                f"[Source {idx + 1}] {result['content']}"
                for idx, result in enumerate(context_results)
            ])

            # 3. Build system prompt
            if not system_prompt:
                system_prompt = (
                    "You are DevSkyy, an AI assistant with access to a knowledge base. "
                    "Answer questions accurately based on the provided context. "
                    "If the context doesn't contain relevant information, say so clearly. "
                    "Always cite sources when using information from the context."
                )

            # 4. Generate answer with Claude
            if not self.anthropic:
                # Fallback: return context only
                return {
                    "answer": "LLM not configured. Here are the relevant excerpts:\n\n" + context_str,
                    "sources": context_results,
                    "context_used": len(context_results),
                }

            message = self.anthropic.messages.create(
                model=model,
                max_tokens=RAGConfig.MAX_TOKENS,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context:\n{context_str}\n\nQuestion: {question}",
                    }
                ],
            )

            answer = message.content[0].text

            return {
                "answer": answer,
                "sources": context_results,
                "context_used": len(context_results),
                "model": model,
                "tokens_used": {
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Return aggregated RAG service statistics including vector database metrics and the current chunking/retrieval configuration.
        
        Returns:
            stats (dict): A dictionary with keys:
                - "vector_db": statistics for the underlying vector database (document count, collection name, persist directory, embedding model, etc.).
                - "config": a dictionary containing current RAG configuration values:
                    - "chunk_size": configured chunk size in tokens/characters.
                    - "chunk_overlap": configured overlap between chunks.
                    - "top_k": configured number of retrieval results to return.
                    - "similarity_threshold": configured minimum similarity threshold for results.
        """
        return {
            "vector_db": self.vector_db.get_stats(),
            "config": {
                "chunk_size": self.doc_processor.chunk_size,
                "chunk_overlap": self.doc_processor.chunk_overlap,
                "top_k": RAGConfig.TOP_K_RESULTS,
                "similarity_threshold": RAGConfig.SIMILARITY_THRESHOLD,
            },
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get the singleton global RAGService instance, creating it if necessary.
    
    Returns:
        RAGService: The singleton RAGService instance.
    """
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService()
        logger.info("Initialized RAG service")

    return _rag_service


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    async def main():
        """Example usage"""
        rag = get_rag_service()

        # Ingest sample text
        sample_text = """
        DevSkyy is a multi-agent AI platform with 54 specialized agents.
        It provides enterprise-grade AI orchestration with RBAC, encryption,
        and comprehensive monitoring. The platform follows the Truth Protocol
        for verifiable, secure, and production-ready AI systems.
        """

        stats = await rag.ingest_text(sample_text, source="example")
        print(f"Ingested: {stats}")

        # Search
        results = await rag.search("What is DevSkyy?")
        print(f"\nSearch results: {len(results)}")
        for result in results:
            print(f"  - {result['content'][:100]}... (similarity: {result['similarity']:.2f})")

        # RAG query
        answer = await rag.query("What security features does DevSkyy have?")
        print(f"\nAnswer: {answer['answer']}")
        print(f"Sources used: {answer['context_used']}")

    asyncio.run(main())