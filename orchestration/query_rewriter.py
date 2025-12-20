"""
Advanced RAG Query Rewriting System for DevSkyy
===============================================

Implements multiple query rewriting strategies to improve RAG retrieval performance.

Techniques:
- Zero-shot Query Rewriting: Simple paraphrasing without examples
- Few-shot Query Rewriting: Uses examples to guide rewriting style
- Sub-query Decomposition: Splits complex questions into sub-queries
- Step-back Prompting: Generates higher-level conceptual questions
- HyDE: Generates hypothetical answer passages for semantic matching

Optimizations for DevSkyy:
- Uses Haiku for fast, cost-effective rewriting
- Redis caching for rewritten queries
- Simple query bypass (skips rewriting for short, clear queries)
- Async batch support for multiple queries
- Integration with DocumentIngestionPipeline

Reference: https://medium.com/@rogi23696/build-an-advanced-rag-app-query-rewriting-1cedbfbfbc59
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from anthropic import Anthropic
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class QueryRewriteStrategy(Enum):
    """Available query rewriting strategies"""

    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    SUB_QUERIES = "sub_queries"
    STEP_BACK = "step_back"
    HYDE = "hyde"


class RewrittenQuery(BaseModel):
    """Structured output for rewritten queries"""

    original_query: str = Field(description="The original user query")
    rewritten_queries: list[str] = Field(description="List of rewritten query variations")
    strategy_used: str = Field(description="The rewriting strategy applied")
    reasoning: str | None = Field(default=None, description="Explanation of the rewriting")


@dataclass
class QueryRewriterConfig:
    """Configuration for RAG query rewriting"""

    api_key: str | None = None
    model: str = "claude-haiku-4-5-20251001"  # Optimized for speed/cost
    max_tokens: int = 1000
    temperature: float = 0.7
    # Simple query bypass
    min_query_length_for_rewrite: int = 20
    # Redis caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    redis_url: str | None = None


class AdvancedQueryRewriter:
    """
    Advanced query rewriting system for RAG applications.

    Optimized for DevSkyy with:
    - Haiku model for fast rewriting
    - Redis caching support
    - Simple query bypass
    - Async operations
    """

    def __init__(self, config: QueryRewriterConfig | None = None):
        """
        Initialize the query rewriter.

        Args:
            config: Configuration object. If None, uses environment variables.
        """
        self.config = config or QueryRewriterConfig()
        self.api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable or pass via config."
            )

        self.client = Anthropic(api_key=self.api_key)

        # Optional Redis cache
        self._redis: Any | None = None
        if self.config.cache_enabled and self.config.redis_url:
            self._init_redis()

        logger.info(
            "query_rewriter_initialized",
            model=self.config.model,
            cache_enabled=self.config.cache_enabled,
        )

    def _init_redis(self) -> None:
        """Initialize Redis cache connection"""
        try:
            import redis

            self._redis = redis.Redis.from_url(self.config.redis_url or "redis://localhost")
            self._redis.ping()
            logger.info("redis_cache_connected")
        except Exception as e:
            logger.warning("redis_cache_failed", error=str(e))
            self._redis = None

    def _should_rewrite(self, query: str) -> bool:
        """
        Determine if query should be rewritten.

        Simple queries are skipped to save cost/latency.
        """
        # Skip very short queries
        if len(query) < self.config.min_query_length_for_rewrite:
            return False

        # Skip queries that are already well-formed (contain clear keywords)
        clear_keywords = ["what is", "how do", "explain", "describe", "list"]
        return not any(kw in query.lower() for kw in clear_keywords)

    def _get_cache_key(self, query: str, strategy: str) -> str:
        """Generate cache key for rewritten query"""
        import hashlib

        content = f"{query}:{strategy}"
        return f"devsky_query_rewrite:{hashlib.md5(content.encode()).hexdigest()}"

    def _get_cached_result(self, query: str, strategy: str) -> RewrittenQuery | None:
        """Retrieve cached rewritten query"""
        if not self._redis:
            return None

        try:
            cache_key = self._get_cache_key(query, strategy)
            cached = self._redis.get(cache_key)

            if cached:
                data = json.loads(cached)
                logger.debug("cache_hit", query=query[:50])
                return RewrittenQuery(**data)
        except Exception as e:
            logger.warning("cache_retrieval_failed", error=str(e))

        return None

    def _cache_result(self, result: RewrittenQuery) -> None:
        """Cache rewritten query result"""
        if not self._redis:
            return

        try:
            cache_key = self._get_cache_key(result.original_query, result.strategy_used)
            self._redis.setex(
                cache_key,
                self.config.cache_ttl_seconds,
                result.model_dump_json(),
            )
            logger.debug("cache_stored", query=result.original_query[:50])
        except Exception as e:
            logger.warning("cache_storage_failed", error=str(e))

    def rewrite(
        self,
        query: str,
        strategy: QueryRewriteStrategy = QueryRewriteStrategy.ZERO_SHOT,
        num_variations: int = 3,
    ) -> RewrittenQuery:
        """
        Main method to rewrite a query using the specified strategy.

        Args:
            query: Original user query
            strategy: Rewriting strategy to use
            num_variations: Number of query variations to generate

        Returns:
            RewrittenQuery object with rewritten queries
        """
        # Check cache first
        cached = self._get_cached_result(query, strategy.value)
        if cached:
            return cached

        # Skip rewriting for simple queries
        if not self._should_rewrite(query):
            logger.debug("query_rewrite_skipped", query=query[:50])
            return RewrittenQuery(
                original_query=query,
                rewritten_queries=[query],
                strategy_used="none",
                reasoning="Query is already well-formed",
            )

        strategy_map = {
            QueryRewriteStrategy.ZERO_SHOT: self._zero_shot_rewrite,
            QueryRewriteStrategy.FEW_SHOT: self._few_shot_rewrite,
            QueryRewriteStrategy.SUB_QUERIES: self._sub_query_decomposition,
            QueryRewriteStrategy.STEP_BACK: self._step_back_prompt,
            QueryRewriteStrategy.HYDE: self._hyde_rewrite,
        }

        rewrite_func = strategy_map.get(strategy)
        if not rewrite_func:
            raise ValueError(f"Unknown strategy: {strategy}")

        result = rewrite_func(query, num_variations)

        # Cache the result
        self._cache_result(result)

        return result

    def _zero_shot_rewrite(self, query: str, num_variations: int) -> RewrittenQuery:
        """Zero-shot query rewriting: Simple paraphrasing without examples."""
        prompt = f"""Rewrite the following user query to make it clearer and more suitable for semantic search.

Generate {num_variations} different variations that:
1. Remove unnecessary context and focus on the core question
2. Use clear, standard terminology
3. Restructure for better semantic matching
4. Maintain the original intent

Original query: "{query}"

Provide {num_variations} rewritten versions as a JSON array of strings.
Return ONLY the JSON array, no other text."""

        response = self._call_claude(prompt)
        rewritten_queries = self._extract_queries_from_response(response, num_variations)

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=rewritten_queries,
            strategy_used="zero_shot",
            reasoning="Applied zero-shot rewriting to clarify and optimize for semantic search",
        )

    def _few_shot_rewrite(self, query: str, num_variations: int) -> RewrittenQuery:
        """Few-shot query rewriting: Uses examples to guide the rewriting style."""
        prompt = f"""Rewrite user queries to be clearer and more suitable for semantic search.

Example rewrites:
- "can you tell me about that thing where companies use AI to talk to customers?" → "What is AI-powered customer service automation?"
- "how to make websites load faster, especially the images" → "What are techniques for optimizing website image loading?"
- "tools for keeping track of team work on projects" → "What are project management tools for team task tracking?"

Rewrite this query following the same pattern:
Original: "{query}"

Generate {num_variations} clear, focused rewrites as a JSON array of strings.
Return ONLY the JSON array, no other text."""

        response = self._call_claude(prompt)
        rewritten_queries = self._extract_queries_from_response(response, num_variations)

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=rewritten_queries,
            strategy_used="few_shot",
            reasoning="Applied few-shot rewriting with examples for consistent style",
        )

    def _sub_query_decomposition(self, query: str, num_variations: int) -> RewrittenQuery:
        """Sub-query decomposition: Splits complex questions into simpler sub-queries."""
        prompt = f"""Analyze this query and decompose it into simpler sub-questions if needed.

Original query: "{query}"

If complex, break into {num_variations} or fewer focused sub-questions.
If simple, provide original plus {num_variations-1} rephrased versions.

Return JSON object:
{{"sub_queries": ["question 1", "question 2", ...]}}

Return ONLY the JSON, no other text."""

        response = self._call_claude(prompt)

        try:
            parsed = json.loads(response)
            sub_queries = parsed.get("sub_queries", [query])
        except Exception:
            sub_queries = self._extract_queries_from_response(response, num_variations)

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=sub_queries,
            strategy_used="sub_queries",
            reasoning="Decomposed into focused sub-questions for targeted retrieval",
        )

    def _step_back_prompt(self, query: str, num_variations: int) -> RewrittenQuery:
        """Step-back prompting: Generates higher-level conceptual questions."""
        prompt = f"""Given this specific query, generate a "step-back" question about the broader concept.

Original query: "{query}"

Generate:
1. A step-back question (more generic, broader topic)
2. {num_variations-1} variations of the step-back question

Return JSON:
{{"step_back_question": "broader question", "variations": ["var1", "var2", ...]}}

Return ONLY the JSON, no other text."""

        response = self._call_claude(prompt)

        try:
            parsed = json.loads(response)
            step_back = parsed.get("step_back_question", query)
            variations = parsed.get("variations", [])
            queries = [query, step_back] + variations
        except Exception:
            queries = [query] + self._extract_queries_from_response(
                response, num_variations - 1
            )

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=queries[:num_variations],
            strategy_used="step_back",
            reasoning="Generated step-back questions for multi-level conceptual retrieval",
        )

    def _hyde_rewrite(self, query: str, num_variations: int) -> RewrittenQuery:
        """HyDE: Generates hypothetical answer passages for semantic matching."""
        prompt = f"""Generate {num_variations} hypothetical document passages that would answer this query.
These are NOT real answers, but examples of answer-like passages for semantic matching.

Query: "{query}"

For each passage:
- Write 2-3 sentences
- Use typical knowledge base article terminology
- Focus on semantic similarity to real answer passages
- Make them diverse

Return JSON array of strings:
["passage 1", "passage 2", ...]

Return ONLY the JSON array, no other text."""

        response = self._call_claude(prompt)
        hypothetical_docs = self._extract_queries_from_response(response, num_variations)

        return RewrittenQuery(
            original_query=query,
            rewritten_queries=hypothetical_docs,
            strategy_used="hyde",
            reasoning="Generated hypothetical passages for semantic document matching",
        )

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        message = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def _extract_queries_from_response(
        self, response: str, expected_count: int
    ) -> list[str]:
        """Extract query strings from Claude's response."""
        # Try parsing as JSON first
        try:
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                if isinstance(queries, list):
                    return [str(q).strip() for q in queries if q][:expected_count]
        except Exception:
            pass

        # Fallback: extract quoted strings
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            return quoted[:expected_count]

        # Last resort: split by newlines
        lines = [
            line.strip().lstrip("0123456789.-) ").strip("\"'")
            for line in response.split("\n")
            if line.strip() and len(line.strip()) > 10
        ]

        return lines[:expected_count] if lines else [response.strip()]

    async def rewrite_batch(
        self,
        queries: list[str],
        strategy: QueryRewriteStrategy = QueryRewriteStrategy.ZERO_SHOT,
    ) -> list[RewrittenQuery]:
        """
        Rewrite multiple queries in parallel.

        Args:
            queries: List of queries to rewrite
            strategy: Strategy to use for all queries

        Returns:
            List of RewrittenQuery objects
        """
        tasks = [
            asyncio.to_thread(
                self.rewrite,
                query,
                strategy,
                3,
            )
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if isinstance(r, RewrittenQuery)]


class RAGPipelineWithRewriting:
    """
    Complete RAG pipeline with query rewriting integration.

    Flow: Query → Rewrite → Retrieve → Generate
    """

    def __init__(
        self,
        rewriter_config: QueryRewriterConfig | None = None,
        vector_search_func=None,
    ):
        """
        Initialize RAG pipeline with query rewriter.

        Args:
            rewriter_config: Configuration for query rewriter
            vector_search_func: Function that takes query and returns relevant documents
        """
        self.rewriter = AdvancedQueryRewriter(rewriter_config)
        self.vector_search_func = vector_search_func

    def retrieve_with_rewrite(
        self,
        query: str,
        strategy: QueryRewriteStrategy = QueryRewriteStrategy.ZERO_SHOT,
        num_variations: int = 3,
        top_k_total: int = 5,
    ) -> dict[str, Any]:
        """
        Execute RAG pipeline with query rewriting.

        Args:
            query: Original user query
            strategy: Query rewriting strategy
            num_variations: Number of query variations
            top_k_total: Total number of unique results to return

        Returns:
            Dictionary with rewritten queries and retrieved contexts
        """
        # Step 1: Rewrite query
        rewritten = self.rewriter.rewrite(query, strategy, num_variations)

        # Step 2: Retrieve context for each rewritten query
        all_contexts = []
        if self.vector_search_func:
            for rewritten_query in rewritten.rewritten_queries:
                contexts = self.vector_search_func(rewritten_query)
                all_contexts.extend(contexts)

            # Step 3: Deduplicate contexts
            unique_contexts = self._deduplicate_contexts(all_contexts)
        else:
            unique_contexts = []

        return {
            "original_query": query,
            "rewritten_queries": rewritten.rewritten_queries,
            "strategy": rewritten.strategy_used,
            "contexts": unique_contexts[:top_k_total],
            "reasoning": rewritten.reasoning,
        }

    def _deduplicate_contexts(self, contexts: list[str]) -> list[str]:
        """Remove duplicate contexts based on exact match."""
        seen = set()
        unique = []

        for ctx in contexts:
            ctx_clean = ctx.strip() if isinstance(ctx, str) else str(ctx)
            if ctx_clean and ctx_clean not in seen:
                seen.add(ctx_clean)
                unique.append(ctx)

        return unique


__all__ = [
    "QueryRewriteStrategy",
    "RewrittenQuery",
    "QueryRewriterConfig",
    "AdvancedQueryRewriter",
    "RAGPipelineWithRewriting",
]
