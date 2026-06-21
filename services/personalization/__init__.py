"""Personalization services (deterministic, advisory-only).

Exposes a per-user catalog reranker. It replaces the global, identical-for-everyone ranking
in ``algorithm_agent.score_products`` with content-based + co-purchase personalization, and
falls back to global popularity for cold-start users. An embedding/Pinecone backend is an
optional injected port — the no-LLM, no-network path ships by default.
"""

from __future__ import annotations

from services.personalization.recommender import (
    Recommendation,
    RecommendationSet,
    Recommender,
    SimilarityBackend,
    Strategy,
    format_recommendations,
)

__all__ = [
    "Recommendation",
    "RecommendationSet",
    "Recommender",
    "SimilarityBackend",
    "Strategy",
    "format_recommendations",
]
