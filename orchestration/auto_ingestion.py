"""
DevSkyy Auto-Ingestion Module
==============================

Automatic document ingestion for RAG pipeline at application startup.

Features:
- Scans docs/ directory for markdown and text files
- Generates embeddings using sentence-transformers
- Ingests into vector store
- Supports incremental updates (skip already-indexed files)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from orchestration.vector_store import BaseVectorStore, Document, DocumentStatus

logger = structlog.get_logger(__name__)


# =============================================================================
# Document Ingestion
# =============================================================================


class AutoDocumentIngestion:
    """
    Automatic document ingestion for RAG.

    Scans specified directories and ingests documents into vector store.
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst", ".html", ".pdf"}

    # Default directories to scan
    DEFAULT_SCAN_DIRS = [
        "docs",
        "README.md",
        "CLAUDE.md",
        ".claude",
    ]

    def __init__(
        self,
        vector_store: BaseVectorStore,
        scan_directories: list[str] | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize auto-ingestion.

        Args:
            vector_store: Initialized vector store
            scan_directories: Directories to scan (relative to project root)
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.vector_store = vector_store
        self.scan_directories = scan_directories or self.DEFAULT_SCAN_DIRS
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Track ingested files (to avoid duplicates)
        self._ingested_hashes: set[str] = set()

    async def ingest_all(
        self,
        project_root: str | Path = ".",
        force_reindex: bool = False,
    ) -> dict[str, Any]:
        """
        Ingest all documents from configured directories.

        Args:
            project_root: Root directory of the project
            force_reindex: Force re-indexing of all files

        Returns:
            Dictionary with ingestion statistics
        """
        project_root = Path(project_root).resolve()
        logger.info(f"Starting auto-ingestion from {project_root}")

        stats = {
            "files_scanned": 0,
            "files_ingested": 0,
            "files_skipped": 0,
            "documents_created": 0,
            "errors": 0,
            "start_time": datetime.now(UTC).isoformat(),
        }

        # Scan each directory
        for scan_dir in self.scan_directories:
            dir_path = project_root / scan_dir

            if not dir_path.exists():
                logger.debug(f"Directory not found: {dir_path}")
                continue

            # Check if it's a file or directory
            if dir_path.is_file():
                # Single file
                await self._ingest_file(dir_path, stats, force_reindex)
            else:
                # Directory - scan recursively
                await self._ingest_directory(dir_path, stats, force_reindex)

        stats["end_time"] = datetime.now(UTC).isoformat()
        logger.info(
            f"Auto-ingestion complete: "
            f"{stats['files_ingested']} files ingested, "
            f"{stats['documents_created']} documents created, "
            f"{stats['errors']} errors"
        )

        return stats

    async def _ingest_directory(
        self,
        directory: Path,
        stats: dict[str, Any],
        force_reindex: bool,
    ) -> None:
        """Recursively ingest all files in a directory."""
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix in self.SUPPORTED_EXTENSIONS:
                    await self._ingest_file(file_path, stats, force_reindex)
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            stats["errors"] += 1

    async def _ingest_file(
        self,
        file_path: Path,
        stats: dict[str, Any],
        force_reindex: bool,
    ) -> None:
        """Ingest a single file."""
        stats["files_scanned"] += 1

        try:
            # Read file content
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Try with latin-1 fallback
                content = file_path.read_text(encoding="latin-1")

            # Skip empty files
            if not content.strip():
                logger.debug(f"Skipping empty file: {file_path}")
                stats["files_skipped"] += 1
                return

            # Check if already ingested (unless force_reindex)
            file_hash = self._compute_file_hash(content)
            if not force_reindex and file_hash in self._ingested_hashes:
                logger.debug(f"Skipping already-ingested file: {file_path}")
                stats["files_skipped"] += 1
                return

            # Split into chunks
            chunks = self._split_into_chunks(content)

            # Create documents
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    content=chunk,
                    metadata={
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_hash": file_hash,
                    },
                    source=str(file_path.relative_to(file_path.parents[len(file_path.parts) - 1])),
                    created_at=datetime.now(UTC),
                    status=DocumentStatus.PENDING,
                )
                documents.append(doc)

            # Generate embeddings
            embeddings = await self._generate_embeddings([doc.content for doc in documents])

            # Ingest into vector store
            await self.vector_store.add_documents(documents, embeddings)

            # Mark as ingested
            self._ingested_hashes.add(file_hash)

            stats["files_ingested"] += 1
            stats["documents_created"] += len(documents)

            logger.info(f"Ingested {file_path.name}: {len(chunks)} chunks, {len(content)} chars")

        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            stats["errors"] += 1

    def _compute_file_hash(self, content: str) -> str:
        """Compute hash of file content for duplicate detection."""
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _split_into_chunks(self, text: str) -> list[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find a good break point (end of sentence or paragraph)
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind("\n\n", start, end)
                if para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind(". ", start, end),
                        text.rfind(".\n", start, end),
                        text.rfind("! ", start, end),
                        text.rfind("? ", start, end),
                    )
                    if sentence_break > start:
                        end = sentence_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap
            if start <= 0:
                start = end

        return chunks

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            from sentence_transformers import SentenceTransformer

            # Use same model as RAG context manager
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(texts).tolist()

            return embeddings

        except ImportError:
            logger.error(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


# =============================================================================
# Convenience Functions
# =============================================================================


async def auto_ingest_documents(
    vector_store: BaseVectorStore,
    project_root: str | Path = ".",
    scan_directories: list[str] | None = None,
    force_reindex: bool = False,
) -> dict[str, Any]:
    """
    Convenience function to auto-ingest documents.

    Args:
        vector_store: Initialized vector store
        project_root: Root directory of the project
        scan_directories: Directories to scan
        force_reindex: Force re-indexing of all files

    Returns:
        Dictionary with ingestion statistics
    """
    ingestion = AutoDocumentIngestion(
        vector_store=vector_store,
        scan_directories=scan_directories,
    )

    return await ingestion.ingest_all(
        project_root=project_root,
        force_reindex=force_reindex,
    )


__all__ = [
    "AutoDocumentIngestion",
    "auto_ingest_documents",
]
