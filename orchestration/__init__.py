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

from core.runtime.tool_registry import ToolCategory, ToolDefinition, ToolParameter, ToolRegistry

from .asset_pipeline import (
    Asset3DResult,
    AssetPipelineResult,
    PipelineConfig,
    PipelineStage,
    ProductAssetPipeline,
    ProductCategory,
    TryOnAssetResult,
    WordPressAssetResult,
)
from .document_ingestion import (
    ChunkMetadata,
    DocumentIngestionPipeline,
    DocumentLoader,
    DocumentType,
    IngestionConfig,
    IngestionResult,
    TextChunker,
    ingest_docs_directory,
)
from .domain_router import DomainRouter, TaskDomain
from .embedding_engine import (
    BaseEmbeddingEngine,
    EmbeddingConfig,
    EmbeddingProvider,
    OpenAIEmbeddingEngine,
    SentenceTransformerEngine,
    create_embedding_engine,
)
from .langgraph_integration import AgentNode, WorkflowEdge, WorkflowManager, WorkflowState
from .llm_clients import (
    AnthropicClient,
    BaseLLMClient,
    CohereClient,
    GoogleClient,
    GroqClient,
    MistralClient,
    OpenAIClient,
)
from .llm_orchestrator import CompletionResult, LLMOrchestrator, RoutingStrategy, TaskType
from .llm_registry import LLMRegistry, ModelCapability, ModelDefinition, ModelProvider, ModelTier
from .model_config import (
    get_all_model_ids,
    get_claude_sonnet,
    get_gemini_2_flash,
    get_gpt4o,
    get_llama_3_3_70b,
    get_model_id,
    log_model_configuration,
)
from .prompt_engineering import PromptChain, PromptEngineer, PromptTechnique, PromptTemplate
from .query_rewriter import (
    AdvancedQueryRewriter,
    QueryRewriterConfig,
    QueryRewriteStrategy,
    RAGPipelineWithRewriting,
    RewrittenQuery,
)

# RAG Components
from .vector_store import (
    BaseVectorStore,
    ChromaVectorStore,
    Document,
    PineconeVectorStore,
    SearchResult,
    VectorDBType,
    VectorStoreConfig,
    create_vector_store,
)

__all__ = [
    # LLM Registry
    "LLMRegistry",
    "ModelDefinition",
    "ModelCapability",
    "ModelProvider",
    "ModelTier",
    # Model Configuration
    "get_model_id",
    "get_all_model_ids",
    "get_claude_sonnet",
    "get_gpt4o",
    "get_gemini_2_flash",
    "get_llama_3_3_70b",
    "log_model_configuration",
    # LLM Clients
    "BaseLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "GoogleClient",
    "MistralClient",
    "CohereClient",
    "GroqClient",
    # LLM Orchestrator
    "LLMOrchestrator",
    "TaskType",
    "RoutingStrategy",
    "CompletionResult",
    # Domain Router
    "DomainRouter",
    "TaskDomain",
    # Tool Registry
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "ToolParameter",
    # Prompt Engineering
    "PromptEngineer",
    "PromptTechnique",
    "PromptTemplate",
    "PromptChain",
    # LangGraph
    "WorkflowManager",
    "AgentNode",
    "WorkflowState",
    "WorkflowEdge",
    # Asset Pipeline
    "ProductAssetPipeline",
    "PipelineConfig",
    "AssetPipelineResult",
    "Asset3DResult",
    "TryOnAssetResult",
    "WordPressAssetResult",
    "ProductCategory",
    "PipelineStage",
    # RAG - Vector Store
    "BaseVectorStore",
    "ChromaVectorStore",
    "PineconeVectorStore",
    "VectorStoreConfig",
    "VectorDBType",
    "Document",
    "SearchResult",
    "create_vector_store",
    # RAG - Embedding Engine
    "BaseEmbeddingEngine",
    "SentenceTransformerEngine",
    "OpenAIEmbeddingEngine",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "create_embedding_engine",
    # RAG - Query Rewriting (Stage 4.11+)
    "QueryRewriteStrategy",
    "RewrittenQuery",
    "QueryRewriterConfig",
    "AdvancedQueryRewriter",
    "RAGPipelineWithRewriting",
    # RAG - Document Ingestion
    "DocumentIngestionPipeline",
    "DocumentLoader",
    "TextChunker",
    "IngestionConfig",
    "IngestionResult",
    "ChunkMetadata",
    "DocumentType",
    "ingest_docs_directory",
]
