"""
Query Rewriter Integration Examples for DevSkyy RAG

Shows how to integrate the Advanced Query Rewriting System with DevSkyy's
existing RAG pipeline and agent infrastructure.

Usage Examples:
1. Direct integration with DocumentIngestionPipeline
2. Integration with SuperAgent RAG technique
3. Integration with MCP server
4. Batch query rewriting for multiple queries
"""

import asyncio
from typing import Optional

import structlog

from orchestration.document_ingestion import DocumentIngestionPipeline
from orchestration.embedding_engine import EmbeddingConfig, EmbeddingProvider, create_embedding_engine
from orchestration.query_rewriter import (
    AdvancedQueryRewriter,
    QueryRewriteStrategy,
    QueryRewriterConfig,
    RAGPipelineWithRewriting,
)
from orchestration.vector_store import VectorDBType, VectorStoreConfig, create_vector_store

logger = structlog.get_logger(__name__)


# =============================================================================
# Example 1: Basic Query Rewriting
# =============================================================================


def example_basic_rewriting():
    """Example: Basic query rewriting with different strategies"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Query Rewriting")
    print("=" * 80)

    config = QueryRewriterConfig(cache_enabled=False)
    rewriter = AdvancedQueryRewriter(config)

    # Test various queries
    test_queries = [
        "What is the BLACK ROSE collection?",
        "Hey can you tell me about those dresses your company makes for fancy events?",
        "How do I find out the price of items and can I customize them?",
    ]

    for query in test_queries:
        print(f"\n📝 Original Query: {query}")
        print("-" * 40)

        # Zero-shot rewriting
        result = rewriter.rewrite(
            query,
            QueryRewriteStrategy.ZERO_SHOT,
            num_variations=2,
        )

        print(f"Strategy: {result.strategy_used}")
        print(f"Reasoning: {result.reasoning}")
        print("Rewritten queries:")
        for i, rq in enumerate(result.rewritten_queries, 1):
            print(f"  {i}. {rq}")


# =============================================================================
# Example 2: Integration with DocumentIngestionPipeline
# =============================================================================


async def example_rag_pipeline_integration():
    """Example: Integrate query rewriting with RAG pipeline"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: RAG Pipeline Integration")
    print("=" * 80)

    # Initialize RAG pipeline
    vector_config = VectorStoreConfig(
        db_type=VectorDBType.CHROMADB,
        collection_name="devskyy_docs",
        persist_directory="./data/vectordb",
    )

    embedding_config = EmbeddingConfig(
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
    )

    vector_store = create_vector_store(vector_config)
    embedding_engine = create_embedding_engine(embedding_config)

    pipeline = DocumentIngestionPipeline(
        vector_store=vector_store,
        embedding_engine=embedding_engine,
    )

    await pipeline.initialize()

    # Initialize query rewriter
    rewriter = AdvancedQueryRewriter()

    # Test query
    query = "Tell me about your luxury rose jewelry"

    print(f"\n📝 Original Query: {query}")
    print("-" * 40)

    # Rewrite query
    rewritten = rewriter.rewrite(
        query,
        QueryRewriteStrategy.FEW_SHOT,
        num_variations=3,
    )

    print(f"Strategy: {rewritten.strategy_used}")
    print("Rewritten queries:")
    for i, rq in enumerate(rewritten.rewritten_queries, 1):
        print(f"  {i}. {rq}")

    # Search with original and rewritten queries
    print("\n🔍 Retrieval Results:")
    print("-" * 40)

    # Original query retrieval
    original_results = await pipeline.search(query, top_k=3)
    print(f"\nOriginal query ({len(original_results)} results):")
    for result in original_results[:2]:
        print(f"  - {result.get('document', {}).get('source', 'unknown')}: {result.get('score', 0):.3f}")

    # Rewritten query retrieval
    for rewritten_query in rewritten.rewritten_queries[:1]:
        rewritten_results = await pipeline.search(rewritten_query, top_k=3)
        print(f"\nRewritten query: '{rewritten_query}'")
        print(f"Results ({len(rewritten_results)} found):")
        for result in rewritten_results[:2]:
            print(f"  - {result.get('document', {}).get('source', 'unknown')}: {result.get('score', 0):.3f}")

    await pipeline.close()


# =============================================================================
# Example 3: Integration with SuperAgent RAG Technique
# =============================================================================


def example_super_agent_integration():
    """
    Example: How to integrate with SuperAgent's RAG prompt technique

    In agents/base_super_agent.py, you would use query rewriting like this:

    ```python
    from orchestration.query_rewriter import AdvancedQueryRewriter

    class EnhancedSuperAgent:
        def __init__(self):
            self.query_rewriter = AdvancedQueryRewriter()

        async def use_technique(self, technique: PromptTechnique, **kwargs):
            if technique == PromptTechnique.RAG:
                # Rewrite the question before RAG retrieval
                question = kwargs.get("question", "")
                rewritten = self.query_rewriter.rewrite(
                    question,
                    QueryRewriteStrategy.HYDE,  # HyDE works well for RAG
                    num_variations=2
                )

                # Retrieve context for all variations
                all_context = []
                for rewritten_query in rewritten.rewritten_queries:
                    context = await self.rag_pipeline.search(rewritten_query)
                    all_context.extend(context)

                # Deduplicate and return best context
                unique_context = self._deduplicate(all_context)
                return RAGPrompting.create_prompt(
                    question=question,
                    context=unique_context[:5]
                )
    ```
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: SuperAgent RAG Integration")
    print("=" * 80)
    print(__doc__)


# =============================================================================
# Example 4: Batch Query Rewriting
# =============================================================================


async def example_batch_rewriting():
    """Example: Rewrite multiple queries in parallel"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Batch Query Rewriting")
    print("=" * 80)

    config = QueryRewriterConfig(cache_enabled=False)
    rewriter = AdvancedQueryRewriter(config)

    # Multiple queries to rewrite
    queries = [
        "What's the price of the signature collection?",
        "How do I try on clothes virtually?",
        "Tell me about your 3D product models",
    ]

    print(f"\n📝 Rewriting {len(queries)} queries in parallel...")
    print("-" * 40)

    # Batch rewrite
    results = await rewriter.rewrite_batch(
        queries,
        QueryRewriteStrategy.ZERO_SHOT,
    )

    print(f"\n✅ Completed {len(results)} rewrites")
    for original, result in zip(queries, results):
        print(f"\nOriginal: {original}")
        print(f"Rewritten: {result.rewritten_queries[0]}")


# =============================================================================
# Example 5: Query Rewriting Pipeline (Complete Flow)
# =============================================================================


async def example_complete_rag_flow():
    """Example: Complete RAG flow with query rewriting"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Complete RAG Flow with Query Rewriting")
    print("=" * 80)

    # Initialize RAG pipeline with rewriting
    vector_config = VectorStoreConfig(
        db_type=VectorDBType.CHROMADB,
        collection_name="devskyy_docs",
        persist_directory="./data/vectordb",
    )

    embedding_config = EmbeddingConfig(
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
    )

    vector_store = create_vector_store(vector_config)
    embedding_engine = create_embedding_engine(embedding_config)

    pipeline = DocumentIngestionPipeline(
        vector_store=vector_store,
        embedding_engine=embedding_engine,
    )

    await pipeline.initialize()

    # Create RAG pipeline with rewriting
    rag_with_rewrite = RAGPipelineWithRewriting(
        vector_search_func=lambda q: asyncio.run(pipeline.search(q, top_k=5))
    )

    # Test complex query
    complex_query = "I want to know what options I have for customizing my purchase and what's the process?"

    print(f"\n🎯 Complex Query: {complex_query}")
    print("-" * 40)

    # Execute with query rewriting
    result = rag_with_rewrite.retrieve_with_rewrite(
        query=complex_query,
        strategy=QueryRewriteStrategy.SUB_QUERIES,
        num_variations=3,
        top_k_total=5,
    )

    print(f"\nStrategy: {result['strategy']}")
    print(f"Reasoning: {result['reasoning']}")

    print(f"\n📋 Rewritten Queries ({len(result['rewritten_queries'])} total):")
    for i, rq in enumerate(result["rewritten_queries"], 1):
        print(f"  {i}. {rq}")

    print(f"\n📚 Retrieved Context ({len(result['contexts'])} documents):")
    for i, ctx in enumerate(result["contexts"][:2], 1):
        ctx_str = str(ctx)[:100] + "..." if len(str(ctx)) > 100 else str(ctx)
        print(f"  {i}. {ctx_str}")

    await pipeline.close()


# =============================================================================
# Example 6: Strategy Selection Guide
# =============================================================================


def example_strategy_guide():
    """
    Guide for choosing the right query rewriting strategy

    **Zero-shot**: Use when you need simple clarification
    - Good for: Poorly written, rambling queries
    - Cost: Low (single rewrite)
    - Best for: General Q&A, product searches

    **Few-shot**: Use when you want consistent domain terminology
    - Good for: Domain-specific queries that need standardization
    - Cost: Low (single rewrite with examples)
    - Best for: Technical documentation, specialized domains

    **Sub-queries**: Use when query has multiple parts
    - Good for: Complex questions with multiple aspects
    - Cost: Medium (breaks into parts)
    - Best for: "Compare X and Y", "How do I do A and B?"

    **Step-back**: Use when background knowledge is needed
    - Good for: Specialized queries needing broader context
    - Cost: Medium (asks broader question first)
    - Best for: "Why does X work?", technical explanations

    **HyDE**: Use when question↔answer semantic gap is large
    - Good for: Improving relevance of retrieved documents
    - Cost: Medium-High (generates hypothetical documents)
    - Best for: FAQ sections, answer-based retrieval

    RECOMMENDATION FOR DEVSKYY:
    - Product queries: ZERO_SHOT (fast, cheap)
    - Collection questions: FEW_SHOT (consistent terminology)
    - Customization process: SUB_QUERIES (multiple steps)
    - Complex requests: STEP_BACK (needs context)
    - FAQ retrieval: HYDE (answer-like matching)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Strategy Selection Guide")
    print("=" * 80)
    print(__doc__)


# =============================================================================
# Main
# =============================================================================


async def main():
    """Run all examples"""
    print("\n🚀 Advanced Query Rewriter Integration Examples")
    print("=" * 80)

    # Example 1: Basic rewriting (no async needed)
    example_basic_rewriting()

    # Example 3: Integration pattern
    example_super_agent_integration()

    # Example 6: Strategy guide
    example_strategy_guide()

    # Examples 2, 4, 5 require async (and initialized vector DB)
    print("\n" + "=" * 80)
    print("ASYNC EXAMPLES (require initialized RAG pipeline)")
    print("=" * 80)
    print("To run async examples (2, 4, 5), ensure your RAG pipeline is initialized.")
    print("Uncomment the async calls below.")

    # Uncomment to test async examples:
    # await example_rag_pipeline_integration()
    # await example_batch_rewriting()
    # await example_complete_rag_flow()


if __name__ == "__main__":
    asyncio.run(main())
