"""
DevSkyy Services Package

Business logic services for the DevSkyy platform including:
- Consensus-based multi-agent content review
- RAG (Retrieval-Augmented Generation) service
- Content publishing orchestration
- MCP server integration

Modules:
    consensus_orchestrator: Multi-agent consensus workflows for content review
    rag_service: Vector search and retrieval-augmented generation
    content_publishing_orchestrator: Automated content publishing workflows
    mcp_server: Model Context Protocol server for external tool access

Example:
    from services import ConsensusOrchestrator, RAGService

    # Initialize RAG service
    rag = RAGService()
    results = await rag.query("What products do we offer?")

    # Initialize consensus workflow
    consensus = ConsensusOrchestrator(content_generator, brand_config)
    draft = await consensus.generate_initial_draft(topic="New Collection")
"""

__version__ = "1.0.0"

__all__ = [
    "ConsensusOrchestrator",
    "RAGService",
]


def __getattr__(name: str):
    """
    Lazy import of service modules for performance.

    Args:
        name: The attribute name to import.

    Returns:
        The requested module or class.

    Raises:
        AttributeError: If the attribute is not found.
    """
    if name == "ConsensusOrchestrator":
        from services.consensus_orchestrator import ConsensusOrchestrator
        return ConsensusOrchestrator
    elif name == "RAGService":
        from services.rag_service import RAGService
        return RAGService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
