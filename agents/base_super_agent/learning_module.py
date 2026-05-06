"""
Self-Learning Module
=====================

Performance tracking, prompt optimization, tool usage analysis,
model selection optimization, and knowledge base updates with
RAG integration for continuous improvement.
"""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from orchestration.prompt_engineering import PromptTechnique

from .types import ROUND_TABLE_QUALITY_THRESHOLD, LearningRecord, SuperAgentType

logger = logging.getLogger(__name__)


# =============================================================================
# Self-Learning Module
# =============================================================================


class SelfLearningModule:
    """
    Self-learning module for continuous improvement.

    Capabilities:
    1. Performance tracking (success rate, latency, cost)
    2. Prompt optimization (A/B test prompts)
    3. Tool usage analysis (which tools work best)
    4. Model selection optimization (best LLM per task)
    5. Knowledge base updates (learn from interactions)
    """

    def __init__(self, agent_type: SuperAgentType):
        self.agent_type = agent_type
        self._records: list[LearningRecord] = []
        self._optimizations: dict[str, Any] = {}
        self._knowledge_base: dict[str, Any] = {}

    def record_execution(
        self,
        task_id: str,
        task_type: str,
        prompt: str,
        technique: PromptTechnique,
        llm_provider: str,
        success: bool,
        latency_ms: float,
        cost_usd: float,
        user_feedback: float | None = None,
    ):
        """Record execution for learning"""
        record = LearningRecord(
            task_id=task_id,
            task_type=task_type,
            prompt_hash=hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()[:16],
            technique_used=technique,
            llm_provider=llm_provider,
            success=success,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            user_feedback=user_feedback,
        )
        self._records.append(record)

        # Update optimizations
        self._update_optimizations(record)

    def _update_optimizations(self, record: LearningRecord):
        """Update optimization data based on new record"""
        task_type = record.task_type

        if task_type not in self._optimizations:
            self._optimizations[task_type] = {
                "techniques": {},
                "providers": {},
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_cost_usd": 0.0,
            }

        opt = self._optimizations[task_type]
        opt["total_executions"] += 1

        # Update technique stats
        tech = record.technique_used.value
        if tech not in opt["techniques"]:
            opt["techniques"][tech] = {"uses": 0, "successes": 0}
        opt["techniques"][tech]["uses"] += 1
        if record.success:
            opt["techniques"][tech]["successes"] += 1

        # Update provider stats
        prov = record.llm_provider
        if prov not in opt["providers"]:
            opt["providers"][prov] = {"uses": 0, "successes": 0, "avg_latency": 0}
        opt["providers"][prov]["uses"] += 1
        if record.success:
            opt["providers"][prov]["successes"] += 1
        n = opt["providers"][prov]["uses"]
        opt["providers"][prov]["avg_latency"] = (
            opt["providers"][prov]["avg_latency"] * (n - 1) + record.latency_ms
        ) / n

        # Update aggregates
        total = opt["total_executions"]
        success_count = sum(t["successes"] for t in opt["techniques"].values())
        opt["success_rate"] = success_count / total if total > 0 else 0

        # Running averages
        opt["avg_latency_ms"] = (opt["avg_latency_ms"] * (total - 1) + record.latency_ms) / total
        opt["avg_cost_usd"] = (opt["avg_cost_usd"] * (total - 1) + record.cost_usd) / total

    def get_best_technique(self, task_type: str) -> PromptTechnique | None:
        """Get the best performing technique for a task type"""
        opt = self._optimizations.get(task_type)
        if not opt or not opt["techniques"]:
            return None

        best = max(
            opt["techniques"].items(), key=lambda x: x[1]["successes"] / max(x[1]["uses"], 1)
        )

        try:
            return PromptTechnique(best[0])
        except ValueError:
            return None

    def get_best_provider(self, task_type: str) -> str | None:
        """Get the best performing LLM provider for a task type"""
        opt = self._optimizations.get(task_type)
        if not opt or not opt["providers"]:
            return None

        # Balance success rate and latency
        def score(item):
            name, stats = item
            success_rate = stats["successes"] / max(stats["uses"], 1)
            latency_score = 1 / (1 + stats["avg_latency"] / 1000)
            return success_rate * 0.7 + latency_score * 0.3

        best = max(opt["providers"].items(), key=score)
        return best[0]

    def get_optimization_report(self) -> dict[str, Any]:
        """Get full optimization report"""
        return {
            "agent_type": self.agent_type.value,
            "total_records": len(self._records),
            "task_optimizations": self._optimizations,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate optimization recommendations"""
        recommendations = []

        for task_type, opt in self._optimizations.items():
            if opt["success_rate"] < 0.8:
                recommendations.append(
                    f"Task '{task_type}' has low success rate ({opt['success_rate']:.1%}). "
                    f"Consider using different techniques or providers."
                )

            if opt["avg_latency_ms"] > 5000:
                recommendations.append(
                    f"Task '{task_type}' has high latency ({opt['avg_latency_ms']:.0f}ms). "
                    f"Consider using faster models or caching."
                )

            if opt["avg_cost_usd"] > 0.1:
                recommendations.append(
                    f"Task '{task_type}' is expensive (${opt['avg_cost_usd']:.4f}/request). "
                    f"Consider using more cost-effective providers."
                )

        return recommendations

    def add_to_knowledge_base(self, key: str, value: Any):
        """Add knowledge to the agent's knowledge base"""
        self._knowledge_base[key] = {"value": value, "added_at": datetime.now(UTC).isoformat()}

    def query_knowledge_base(self, key: str) -> Any:
        """Query the knowledge base"""
        entry = self._knowledge_base.get(key)
        return entry["value"] if entry else None

    # -------------------------------------------------------------------------
    # RAG Integration for Self-Learning
    # -------------------------------------------------------------------------

    async def ingest_successful_response(
        self,
        prompt: str,
        response: str,
        task_type: str,
        technique: PromptTechnique,
        score: float,
        provider: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Auto-ingest successful responses (score > threshold) to RAG for future retrieval.

        Args:
            prompt: The original prompt
            response: The successful response
            task_type: Type of task
            technique: Technique used
            score: Quality score (0-1)
            provider: LLM provider that generated the response
            metadata: Optional additional metadata

        Returns:
            True if ingestion was successful
        """
        # Only ingest high-quality responses
        if score < ROUND_TABLE_QUALITY_THRESHOLD:
            return False

        try:
            # Build document content for RAG
            doc_content = f"""## Successful Response Record

**Task Type:** {task_type}
**Technique Used:** {technique.value}
**Quality Score:** {score:.2f}
**Provider:** {provider}
**Timestamp:** {datetime.now(UTC).isoformat()}

### Original Prompt
{prompt}

### Successful Response
{response}
"""
            # Store in knowledge base
            doc_key = f"learning:{task_type}:{hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()[:12]}"
            self._knowledge_base[doc_key] = {
                "value": {
                    "prompt": prompt,
                    "response": response,
                    "task_type": task_type,
                    "technique": technique.value,
                    "score": score,
                    "provider": provider,
                    "metadata": metadata or {},
                },
                "added_at": datetime.now(UTC).isoformat(),
                "doc_content": doc_content,
            }

            # Queue for RAG ingestion (async batch processing)
            self._queue_rag_ingestion(
                doc_key,
                doc_content,
                {
                    "source": f"learning/{self.agent_type.value}/{task_type}",
                    "task_type": task_type,
                    "technique": technique.value,
                    "score": score,
                    "provider": provider,
                },
            )

            logger.info(f"Queued successful response for RAG ingestion: {doc_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to ingest successful response: {e}")
            return False

    def _queue_rag_ingestion(self, key: str, content: str, metadata: dict[str, Any]):
        """Queue content for RAG ingestion (batch processing)"""
        if not hasattr(self, "_rag_ingestion_queue"):
            self._rag_ingestion_queue: list[dict] = []

        self._rag_ingestion_queue.append(
            {
                "key": key,
                "content": content,
                "metadata": metadata,
                "queued_at": datetime.now(UTC).isoformat(),
            }
        )

        # Log queue size for monitoring
        if len(self._rag_ingestion_queue) % 10 == 0:
            logger.info(f"RAG ingestion queue size: {len(self._rag_ingestion_queue)}")

    async def flush_rag_queue(self) -> int:
        """
        Flush RAG ingestion queue to vector store.

        WARNING (P1 #9): this method does NOT write to a vector store. Items
        are merely copied into an in-memory dict (`self._knowledge_base`) and
        lost on process restart. The method name promises persistence the
        implementation does not deliver. Callers depending on durable RAG
        retrieval will silently see empty results after restart.

        TODO: wire to Pinecone (`skyyrose-catalog` index, us-west-2, 1024-dim,
        cosine similarity) OR remove this method and update callers. Until then
        the warning below fires once per process to make the lie auditable.

        Returns:
            Number of items processed (into the in-memory dict, NOT a vector store)
        """
        if not hasattr(self, "_rag_ingestion_queue"):
            return 0

        if not getattr(self.__class__, "_flush_rag_queue_stub_warned", False):
            logger.warning(
                "flush_rag_queue is a stub: items are stored in an in-memory dict, "
                "NOT a vector store. Lost on restart. Wire to Pinecone before relying "
                "on RAG retrieval persistence. (P1 #9)"
            )
            self.__class__._flush_rag_queue_stub_warned = True

        queue = self._rag_ingestion_queue
        self._rag_ingestion_queue = []

        processed = 0
        try:
            # In-memory only — see WARNING above
            for item in queue:
                self._knowledge_base[f"rag:{item['key']}"] = item
                processed += 1

            logger.info(
                f"Processed {processed} items into in-memory knowledge_base "
                f"(NOT vector store — see WARNING)"
            )

        except ImportError:
            logger.warning("RAG components not available for queue flush")
            # Store back in queue for retry
            self._rag_ingestion_queue.extend(queue)

        return processed

    def query_similar_prompts(
        self, prompt: str, task_type: str | None = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Query knowledge base for similar prompts and their successful responses.

        Uses simple keyword matching. For semantic search, use RAG pipeline directly.

        Args:
            prompt: The prompt to find similar entries for
            task_type: Optional filter by task type
            top_k: Maximum number of results

        Returns:
            List of similar prompt records with scores
        """
        results = []
        prompt_words = set(prompt.lower().split())

        for key, entry in self._knowledge_base.items():
            if not key.startswith("learning:"):
                continue

            value = entry.get("value", {})

            # Filter by task type if specified
            if task_type and value.get("task_type") != task_type:
                continue

            # Calculate simple word overlap score
            stored_prompt = value.get("prompt", "")
            stored_words = set(stored_prompt.lower().split())

            if not stored_words:
                continue

            overlap = len(prompt_words & stored_words)
            union = len(prompt_words | stored_words)
            similarity = overlap / union if union > 0 else 0

            if similarity > 0.1:  # Minimum threshold
                results.append(
                    {
                        "key": key,
                        "similarity": similarity,
                        "prompt": stored_prompt,
                        "response": value.get("response", "")[:500],  # Truncate
                        "technique": value.get("technique"),
                        "score": value.get("score", 0),
                        "provider": value.get("provider"),
                        "task_type": value.get("task_type"),
                    }
                )

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_technique_recommendation(
        self, prompt: str, task_type: str | None = None
    ) -> tuple[PromptTechnique | None, float]:
        """
        Get technique recommendation based on similar prompts in knowledge base.

        Args:
            prompt: The prompt to get recommendation for
            task_type: Optional task type filter

        Returns:
            Tuple of (recommended technique, confidence score)
        """
        similar = self.query_similar_prompts(prompt, task_type, top_k=10)

        if not similar:
            return None, 0.0

        # Count technique successes weighted by similarity and score
        technique_scores: dict[str, float] = {}
        for item in similar:
            technique = item.get("technique")
            if not technique:
                continue

            # Weight by both similarity and quality score
            weight = item["similarity"] * item.get("score", 0.5)
            technique_scores[technique] = technique_scores.get(technique, 0) + weight

        if not technique_scores:
            return None, 0.0

        # Get best technique
        best_technique = max(technique_scores.items(), key=lambda x: x[1])
        total_weight = sum(technique_scores.values())
        confidence = best_technique[1] / total_weight if total_weight > 0 else 0

        try:
            return PromptTechnique(best_technique[0]), confidence
        except ValueError:
            return None, 0.0

    def get_learning_stats_for_rag(self) -> dict[str, Any]:
        """
        Get learning statistics formatted for RAG metadata.

        Returns:
            Dict with technique success rates and provider performance
        """
        stats = {
            "agent_type": self.agent_type.value,
            "total_records": len(self._records),
            "knowledge_base_size": len(self._knowledge_base),
            "technique_stats": {},
            "provider_stats": {},
        }

        # Aggregate technique stats across all task types
        for _task_type, opt in self._optimizations.items():
            for tech, tech_stats in opt.get("techniques", {}).items():
                if tech not in stats["technique_stats"]:
                    stats["technique_stats"][tech] = {"uses": 0, "successes": 0}
                stats["technique_stats"][tech]["uses"] += tech_stats.get("uses", 0)
                stats["technique_stats"][tech]["successes"] += tech_stats.get("successes", 0)

            for prov, prov_stats in opt.get("providers", {}).items():
                if prov not in stats["provider_stats"]:
                    stats["provider_stats"][prov] = {"uses": 0, "successes": 0, "total_latency": 0}
                stats["provider_stats"][prov]["uses"] += prov_stats.get("uses", 0)
                stats["provider_stats"][prov]["successes"] += prov_stats.get("successes", 0)

        # Calculate success rates
        for _tech, s in stats["technique_stats"].items():
            s["success_rate"] = s["successes"] / s["uses"] if s["uses"] > 0 else 0

        for _prov, s in stats["provider_stats"].items():
            s["success_rate"] = s["successes"] / s["uses"] if s["uses"] > 0 else 0

        return stats


__all__ = [
    "SelfLearningModule",
]
