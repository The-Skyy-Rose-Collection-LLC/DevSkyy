"""
DevSkyy Orchestration Module
============================

Multi-agent orchestration and LLM management:
- LLM Registry: Model definitions and routing
- LLM Clients: Provider-specific API clients
- LLM Orchestrator: Intelligent model selection
- Tool Registry: Tool definitions and validation
- Prompt Engineering: Advanced prompting techniques
- LangGraph Integration: Multi-agent workflows

Usage:
    from orchestration import LLMOrchestrator, ToolRegistry

    # Get optimal model for task
    orchestrator = LLMOrchestrator()
    response = await orchestrator.complete(
        prompt="Analyze this fashion trend...",
        task_type="analysis",
        requirements={"speed": "fast", "quality": "high"}
    )

    # Register and use tools
    registry = ToolRegistry()
    tool = registry.get_tool("web_search")
    result = await tool.execute(query="luxury streetwear trends")
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import registry: name → (module_path, attribute)
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Tool Registry (from core — lightweight, always available)
    "ToolRegistry": ("core.runtime.tool_registry", "ToolRegistry"),
    "ToolDefinition": ("core.runtime.tool_registry", "ToolDefinition"),
    "ToolCategory": ("core.runtime.tool_registry", "ToolCategory"),
    "ToolParameter": ("core.runtime.tool_registry", "ToolParameter"),
    # Asset Pipeline
    "ProductAssetPipeline": ("orchestration.asset_pipeline", "ProductAssetPipeline"),
    "PipelineConfig": ("orchestration.asset_pipeline", "PipelineConfig"),
    "AssetPipelineResult": ("orchestration.asset_pipeline", "AssetPipelineResult"),
    "Asset3DResult": ("orchestration.asset_pipeline", "Asset3DResult"),
    "TryOnAssetResult": ("orchestration.asset_pipeline", "TryOnAssetResult"),
    "WordPressAssetResult": ("orchestration.asset_pipeline", "WordPressAssetResult"),
    "ProductCategory": ("orchestration.asset_pipeline", "ProductCategory"),
    "PipelineStage": ("orchestration.asset_pipeline", "PipelineStage"),
    # Document Ingestion
    "DocumentIngestionPipeline": ("orchestration.document_ingestion", "DocumentIngestionPipeline"),
    "DocumentLoader": ("orchestration.document_ingestion", "DocumentLoader"),
    "TextChunker": ("orchestration.document_ingestion", "TextChunker"),
    "IngestionConfig": ("orchestration.document_ingestion", "IngestionConfig"),
    "IngestionResult": ("orchestration.document_ingestion", "IngestionResult"),
    "ChunkMetadata": ("orchestration.document_ingestion", "ChunkMetadata"),
    "DocumentType": ("orchestration.document_ingestion", "DocumentType"),
    "ingest_docs_directory": ("orchestration.document_ingestion", "ingest_docs_directory"),
    # Domain Router
    "DomainRouter": ("orchestration.domain_router", "DomainRouter"),
    "TaskDomain": ("orchestration.domain_router", "TaskDomain"),
    # Embedding Engine
    "BaseEmbeddingEngine": ("orchestration.embedding_engine", "BaseEmbeddingEngine"),
    "EmbeddingConfig": ("orchestration.embedding_engine", "EmbeddingConfig"),
    "EmbeddingProvider": ("orchestration.embedding_engine", "EmbeddingProvider"),
    "OpenAIEmbeddingEngine": ("orchestration.embedding_engine", "OpenAIEmbeddingEngine"),
    "SentenceTransformerEngine": ("orchestration.embedding_engine", "SentenceTransformerEngine"),
    "create_embedding_engine": ("orchestration.embedding_engine", "create_embedding_engine"),
    # LangGraph (data types and re-exports — engine is real langgraph library)
    "WorkflowEdge": ("orchestration.langgraph_integration", "WorkflowEdge"),
    "WorkflowState": ("orchestration.langgraph_integration", "WorkflowState"),
    "WorkflowStatus": ("orchestration.langgraph_integration", "WorkflowStatus"),
    "StateGraph": ("orchestration.langgraph_integration", "StateGraph"),
    "END": ("orchestration.langgraph_integration", "END"),
    "START": ("orchestration.langgraph_integration", "START"),
    # LLM Clients
    "AnthropicClient": ("orchestration.llm_clients", "AnthropicClient"),
    "BaseLLMClient": ("orchestration.llm_clients", "BaseLLMClient"),
    "CohereClient": ("orchestration.llm_clients", "CohereClient"),
    "GoogleClient": ("orchestration.llm_clients", "GoogleClient"),
    "GroqClient": ("orchestration.llm_clients", "GroqClient"),
    "MistralClient": ("orchestration.llm_clients", "MistralClient"),
    "OpenAIClient": ("orchestration.llm_clients", "OpenAIClient"),
    # LLM Orchestrator
    "CompletionResult": ("orchestration.llm_orchestrator", "CompletionResult"),
    "LLMOrchestrator": ("orchestration.llm_orchestrator", "LLMOrchestrator"),
    "RoutingStrategy": ("orchestration.llm_orchestrator", "RoutingStrategy"),
    "TaskType": ("orchestration.llm_orchestrator", "TaskType"),
    # LLM Registry
    "LLMRegistry": ("orchestration.llm_registry", "LLMRegistry"),
    "ModelCapability": ("orchestration.llm_registry", "ModelCapability"),
    "ModelDefinition": ("orchestration.llm_registry", "ModelDefinition"),
    "ModelProvider": ("orchestration.llm_registry", "ModelProvider"),
    "ModelTier": ("orchestration.llm_registry", "ModelTier"),
    # Model Configuration
    "get_all_model_ids": ("orchestration.model_config", "get_all_model_ids"),
    "get_claude_sonnet": ("orchestration.model_config", "get_claude_sonnet"),
    "get_gemini_2_flash": ("orchestration.model_config", "get_gemini_2_flash"),
    "get_gpt4o": ("orchestration.model_config", "get_gpt4o"),
    "get_llama_3_3_70b": ("orchestration.model_config", "get_llama_3_3_70b"),
    "get_model_id": ("orchestration.model_config", "get_model_id"),
    "log_model_configuration": ("orchestration.model_config", "log_model_configuration"),
    # Prompt Engineering
    "PromptChain": ("orchestration.prompt_engineering", "PromptChain"),
    "PromptEngineer": ("orchestration.prompt_engineering", "PromptEngineer"),
    "PromptTechnique": ("orchestration.prompt_engineering", "PromptTechnique"),
    "PromptTemplate": ("orchestration.prompt_engineering", "PromptTemplate"),
    # Query Rewriting
    "AdvancedQueryRewriter": ("orchestration.query_rewriter", "AdvancedQueryRewriter"),
    "QueryRewriterConfig": ("orchestration.query_rewriter", "QueryRewriterConfig"),
    "QueryRewriteStrategy": ("orchestration.query_rewriter", "QueryRewriteStrategy"),
    "RAGPipelineWithRewriting": ("orchestration.query_rewriter", "RAGPipelineWithRewriting"),
    "RewrittenQuery": ("orchestration.query_rewriter", "RewrittenQuery"),
    # Vector Store
    "BaseVectorStore": ("orchestration.vector_store", "BaseVectorStore"),
    "ChromaVectorStore": ("orchestration.vector_store", "ChromaVectorStore"),
    "Document": ("orchestration.vector_store", "Document"),
    "PineconeVectorStore": ("orchestration.vector_store", "PineconeVectorStore"),
    "SearchResult": ("orchestration.vector_store", "SearchResult"),
    "VectorDBType": ("orchestration.vector_store", "VectorDBType"),
    "VectorStoreConfig": ("orchestration.vector_store", "VectorStoreConfig"),
    "create_vector_store": ("orchestration.vector_store", "create_vector_store"),
    # Brand Learning
    "BrandLearningLoop": ("orchestration.brand_learning", "BrandLearningLoop"),
    "BrandMemory": ("orchestration.brand_learning", "BrandMemory"),
    "BrandSignal": ("orchestration.brand_learning", "BrandSignal"),
    "BrandInsight": ("orchestration.brand_learning", "BrandInsight"),
    "BrandAdaptation": ("orchestration.brand_learning", "BrandAdaptation"),
    "BrandAdaptor": ("orchestration.brand_learning", "BrandAdaptor"),
    "PatternExtractor": ("orchestration.brand_learning", "PatternExtractor"),
    "InsightCategory": ("orchestration.brand_learning", "InsightCategory"),
    "InsightConfidence": ("orchestration.brand_learning", "InsightConfidence"),
    "SignalType": ("orchestration.brand_learning", "SignalType"),
}

__all__ = list(_LAZY_IMPORTS.keys())


def __getattr__(name: str) -> Any:
    """Lazy-load orchestration components on first access.

    Prevents import-time failures when optional dependencies (mistralai,
    langgraph, chromadb, etc.) are not installed.
    """
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        try:
            mod = importlib.import_module(module_path)
            return getattr(mod, attr)
        except (ImportError, AttributeError) as exc:
            logger.debug("Orchestration lazy import failed for %s.%s: %s", module_path, attr, exc)
            raise ImportError(
                f"Cannot import '{name}' from '{module_path}'. "
                f"Install the required dependencies. Original error: {exc}"
            ) from exc
    raise AttributeError(f"module 'orchestration' has no attribute {name!r}")
