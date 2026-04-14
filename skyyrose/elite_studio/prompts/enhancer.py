"""
Prompt Enhancer — the main public interface for prompt intelligence.

Combines analyzer, cache, chain, and history into one call:
  raw prompt → analyze → check cache → enhance via chain → cache result → return
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from skyyrose.elite_studio.prompts.analyzer import PromptAnalysis, PromptAnalyzer
from skyyrose.elite_studio.prompts.cache import PromptCache
from skyyrose.elite_studio.prompts.chain import PromptChain


@dataclass(frozen=True)
class EnhancedPrompt:
    """Immutable result of prompt enhancement."""

    original: str
    enhanced: str
    intent: str
    score_before: float
    score_after: float
    context_added: tuple[str, ...]
    cache_key: str
    template_used: str


def _compute_cache_key(prompt: str, intent: str) -> str:
    """Deterministic cache key from prompt + intent."""
    raw = f"{intent}:{prompt.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PromptEnhancer:
    """Main entry point for prompt intelligence.

    Usage:
        enhancer = PromptEnhancer()
        result = enhancer.enhance("make me a cool hoodie for winter")
        print(result.enhanced)   # fully enriched prompt
        print(result.score_before, "→", result.score_after)
    """

    def __init__(
        self,
        cache: PromptCache | None = None,
        chain: PromptChain | None = None,
        analyzer: PromptAnalyzer | None = None,
    ) -> None:
        self._cache = cache or PromptCache()
        self._chain = chain or PromptChain()
        self._analyzer = analyzer or PromptAnalyzer()

    def enhance(
        self,
        prompt: str,
        intent: str | None = None,
        fashion_context: dict | None = None,
        brand_context: dict | None = None,
    ) -> EnhancedPrompt:
        """Enhance a raw prompt into an expert-level agent brief.

        Args:
            prompt: Raw human-language prompt.
            intent: Creative intent (auto-detected if None).
            fashion_context: Optional fashion vertical context dict.
            brand_context: Optional brand override context dict.

        Returns:
            EnhancedPrompt with original, enhanced text, scores, and metadata.
        """
        # Analyze the raw prompt
        analysis = self._analyzer.analyze(prompt)
        resolved_intent = intent or analysis.intent
        if resolved_intent == "unknown":
            resolved_intent = "product-render"

        cache_key = _compute_cache_key(prompt, resolved_intent)

        # Check cache for semantically similar prompt
        cached = self._cache.check(prompt, resolved_intent)
        if cached is not None:
            return cached

        # Run the enhancement chain
        chain_result = self._chain.enhance(
            prompt=prompt,
            intent=resolved_intent,
            fashion_context=fashion_context,
            brand_context=brand_context,
        )

        # Score the enhanced prompt
        enhanced_analysis = self._analyzer.analyze(chain_result["enhanced"])

        result = EnhancedPrompt(
            original=prompt,
            enhanced=chain_result["enhanced"],
            intent=chain_result["intent"],
            score_before=analysis.score,
            score_after=enhanced_analysis.score,
            context_added=tuple(chain_result["context_added"]),
            cache_key=cache_key,
            template_used=chain_result["template_used"],
        )

        # Store in cache
        self._cache.store(prompt, result)

        return result

    def analyze_only(self, prompt: str) -> PromptAnalysis:
        """Score a prompt without enhancing it."""
        return self._analyzer.analyze(prompt)
