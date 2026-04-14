"""
Prompt Cache — Redis-backed caching with token-based similarity matching.

Caches enhanced prompts so similar future requests skip the chain.
Uses Jaccard similarity on token sets for fast matching without ML models.
Graceful degradation: if Redis is unavailable, operates as a passthrough.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skyyrose.elite_studio.prompts.enhancer import EnhancedPrompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token-based similarity (no ML dependency required)
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "and", "but", "or", "nor", "not", "so", "yet", "both",
    "each", "all", "any", "few", "more", "most", "other", "some", "such",
    "no", "only", "own", "same", "than", "too", "very", "just", "because",
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "this", "that",
    "make", "create", "generate", "give", "want", "something",
})


def _tokenize(text: str) -> frozenset[str]:
    """Extract meaningful tokens from text, excluding stop words."""
    words = re.findall(r"[a-z0-9#]+", text.lower())
    return frozenset(w for w in words if w not in _STOP_WORDS and len(w) > 1)


def _jaccard_similarity(a: frozenset[str], b: frozenset[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


def _prompt_hash(prompt: str, intent: str) -> str:
    """Deterministic hash for exact-match cache lookup."""
    raw = f"{intent}:{prompt.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PromptCache:
    """Redis-backed prompt cache with similarity matching.

    Graceful degradation: all methods return None / 0 if Redis is unavailable.
    """

    CACHE_PREFIX = "elite_studio:prompt_cache"
    INDEX_KEY = "elite_studio:prompt_cache:index"
    STATS_KEY = "elite_studio:prompt_cache:stats"
    DEFAULT_TTL = 86400  # 24 hours

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis = self._connect(redis_url)
        self._hits = 0
        self._misses = 0

    def _connect(self, redis_url: str | None) -> Any:
        """Connect to Redis. Returns None on failure."""
        try:
            import redis as redis_lib

            url = redis_url or "redis://localhost:6379/0"
            client = redis_lib.Redis.from_url(url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            logger.warning("PromptCache: Redis unavailable — operating in passthrough mode")
            return None

    def check(
        self, prompt: str, intent: str, threshold: float = 0.75
    ) -> EnhancedPrompt | None:
        """Find a cached enhancement for a similar prompt.

        First checks exact hash match, then falls back to similarity search.
        """
        if self._redis is None:
            return None

        try:
            # Exact match first
            key = f"{self.CACHE_PREFIX}:{_prompt_hash(prompt, intent)}"
            cached_json = self._redis.get(key)
            if cached_json:
                self._hits += 1
                self._record_stat("hits")
                return self._deserialize(cached_json)

            # Similarity search via index
            index_data = self._redis.hgetall(self.INDEX_KEY)
            if not index_data:
                self._misses += 1
                self._record_stat("misses")
                return None

            query_tokens = _tokenize(prompt)
            best_match: str | None = None
            best_score = 0.0

            for cache_key, meta_json in index_data.items():
                meta = json.loads(meta_json)
                if meta.get("intent") != intent:
                    continue
                stored_tokens = frozenset(meta.get("tokens", []))
                sim = _jaccard_similarity(query_tokens, stored_tokens)
                if sim > best_score and sim >= threshold:
                    best_score = sim
                    best_match = cache_key

            if best_match:
                cached_json = self._redis.get(best_match)
                if cached_json:
                    self._hits += 1
                    self._record_stat("hits")
                    return self._deserialize(cached_json)

            self._misses += 1
            self._record_stat("misses")
            return None

        except Exception:
            logger.warning("PromptCache: check failed", exc_info=True)
            return None

    def store(
        self, original: str, enhanced: Any, ttl: int | None = None
    ) -> None:
        """Cache an enhanced prompt result."""
        if self._redis is None:
            return

        try:
            intent = enhanced.intent
            key = f"{self.CACHE_PREFIX}:{_prompt_hash(original, intent)}"
            ttl = ttl or self.DEFAULT_TTL

            # Store the full result
            self._redis.setex(key, ttl, self._serialize(enhanced))

            # Store in similarity index
            tokens = list(_tokenize(original))
            index_meta = json.dumps({"intent": intent, "tokens": tokens})
            self._redis.hset(self.INDEX_KEY, key, index_meta)

            self._record_stat("stores")
        except Exception:
            logger.warning("PromptCache: store failed", exc_info=True)

    def invalidate_by_intent(self, intent: str) -> int:
        """Remove all cached prompts for a given intent."""
        if self._redis is None:
            return 0

        try:
            index_data = self._redis.hgetall(self.INDEX_KEY)
            removed = 0
            for cache_key, meta_json in index_data.items():
                meta = json.loads(meta_json)
                if meta.get("intent") == intent:
                    self._redis.delete(cache_key)
                    self._redis.hdel(self.INDEX_KEY, cache_key)
                    removed += 1
            return removed
        except Exception:
            logger.warning("PromptCache: invalidate failed", exc_info=True)
            return 0

    def get_stats(self) -> dict:
        """Return cache hit/miss/store statistics."""
        if self._redis is None:
            return {"hits": self._hits, "misses": self._misses, "stores": 0, "redis": False}

        try:
            stats = self._redis.hgetall(self.STATS_KEY)
            return {
                "hits": int(stats.get("hits", 0)),
                "misses": int(stats.get("misses", 0)),
                "stores": int(stats.get("stores", 0)),
                "redis": True,
            }
        except Exception:
            return {"hits": self._hits, "misses": self._misses, "stores": 0, "redis": False}

    def _record_stat(self, field: str) -> None:
        """Increment a stats counter in Redis."""
        if self._redis is None:
            return
        try:
            self._redis.hincrby(self.STATS_KEY, field, 1)
        except Exception:
            pass

    def _serialize(self, enhanced: Any) -> str:
        """Serialize an EnhancedPrompt to JSON."""
        return json.dumps({
            "original": enhanced.original,
            "enhanced": enhanced.enhanced,
            "intent": enhanced.intent,
            "score_before": enhanced.score_before,
            "score_after": enhanced.score_after,
            "context_added": list(enhanced.context_added),
            "cache_key": enhanced.cache_key,
            "template_used": enhanced.template_used,
            "cached_at": time.time(),
        })

    def _deserialize(self, json_str: str) -> Any:
        """Deserialize JSON back to EnhancedPrompt."""
        from skyyrose.elite_studio.prompts.enhancer import EnhancedPrompt

        data = json.loads(json_str)
        return EnhancedPrompt(
            original=data["original"],
            enhanced=data["enhanced"],
            intent=data["intent"],
            score_before=data["score_before"],
            score_after=data["score_after"],
            context_added=tuple(data.get("context_added", [])),
            cache_key=data.get("cache_key", ""),
            template_used=data.get("template_used", ""),
        )
