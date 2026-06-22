"""Deterministic per-user product recommender (advisory only).

Closes agent gap #6 (Personalization / Recommendation). ``algorithm_agent.score_products``
ranked the catalog GLOBALLY — the same list for every user. This adds real personalization:

- **Content-based**: score each candidate by how well it matches the user's purchase profile
  (collection affinity, shared tags, price-tier proximity).
- **Co-purchase**: boost items frequently bought together with what the user owns (item-item).
- **Popularity cold-start**: a user with no usable history falls back to global popularity —
  a strict superset of the old global ranking.
- **Optional similarity port**: an embedding backend (e.g. the Pinecone ``skyyrose-catalog``
  index) can be injected via ``similarity_backend``; it is blended in when present. The
  default path uses NO LLM and NO network.

Design (mirrors the other services/ scorers): deterministic, never-raises, advisory,
founder-tunable weights, stable tie-break (by score then id).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class SimilarityBackend(Protocol):
    """Optional embedding/vector-similarity port. The Pinecone adapter implements this."""

    def similar(self, item_id: str, k: int) -> list[tuple[str, float]]:
        """Return up to ``k`` (item_id, similarity_score) pairs most similar to ``item_id``."""
        ...


class Strategy(StrEnum):
    PERSONALIZED = "personalized"
    POPULARITY_COLD_START = "popularity_cold_start"


@dataclass(frozen=True)
class Recommendation:
    item_id: str
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RecommendationSet:
    user_id: str | None
    strategy: Strategy
    items: tuple[Recommendation, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "strategy": self.strategy.name,
            "recommendations": [
                {"item_id": r.item_id, "score": r.score, "reasons": list(r.reasons)}
                for r in self.items
            ],
        }


# --------------------------------------------------------------------------- #
# Defensive normalizers (never raise)
# --------------------------------------------------------------------------- #


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value.strip())
        except (ValueError, AttributeError):
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _item_id(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("id") or item.get("sku") or "").strip()
    if isinstance(item, str):
        return item.strip()
    return ""


def _collection(item: dict) -> str:
    return str(item.get("collection") or "").strip().lower()


def _price(item: dict) -> float | None:
    # Explicit None check — a price of 0.0 is a real value, not a reason to fall through.
    price = _to_float(item.get("price"))
    return price if price is not None else _to_float(item.get("regular_price"))


def _tags(item: dict) -> set[str]:
    raw = item.get("tags")
    out: set[str] = set()
    if isinstance(raw, list):
        for t in raw:
            if isinstance(t, str):
                out.add(t.strip().lower())
            elif isinstance(t, dict):
                name = t.get("name") or t.get("slug")
                if name:
                    out.add(str(name).strip().lower())
    return out


def _popularity(item: dict) -> float:
    val = _to_float(item.get("popularity"))
    if val is None:
        val = _to_float(item.get("total_sales"))
    return val if val is not None and val >= 0 else 0.0


# --------------------------------------------------------------------------- #
# Recommender
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _Profile:
    collections: frozenset[str]
    tags: frozenset[str]
    avg_price: float | None
    owned_ids: frozenset[str]

    @property
    def empty(self) -> bool:
        return not (self.collections or self.tags or self.avg_price)


class Recommender:
    """Rank a catalog for one user (read-only, advisory)."""

    def __init__(
        self,
        *,
        top_n: int = 10,
        collection_match_weight: float = 10.0,
        tag_overlap_weight: float = 3.0,
        price_proximity_weight: float = 5.0,
        copurchase_weight: float = 0.5,
        popularity_weight: float = 0.1,
        similarity_weight: float = 8.0,
        similarity_k: int = 50,  # fanout per owned item when a similarity backend is wired
    ) -> None:
        self.top_n = top_n
        self.similarity_k = max(1, similarity_k)
        self.collection_match_weight = collection_match_weight
        self.tag_overlap_weight = tag_overlap_weight
        self.price_proximity_weight = price_proximity_weight
        self.copurchase_weight = copurchase_weight
        self.popularity_weight = popularity_weight
        self.similarity_weight = similarity_weight

    def recommend(
        self,
        user: dict[str, Any],
        catalog: list[dict[str, Any]],
        *,
        co_purchase: dict[str, dict[str, Any]] | None = None,
        similarity_backend: SimilarityBackend | None = None,
    ) -> RecommendationSet:
        """Return a ranked :class:`RecommendationSet` for ``user``. Never raises."""
        user_dict = user if isinstance(user, dict) else {}
        uid = user_dict.get("id")
        uid_str = str(uid) if uid is not None else None

        try:
            return self._recommend(uid_str, user_dict, catalog, co_purchase, similarity_backend)
        except Exception:  # defense-in-depth — recommendations must never break a page render
            return RecommendationSet(uid_str, Strategy.POPULARITY_COLD_START, ())

    def _recommend(
        self,
        uid: str | None,
        user: dict,
        catalog: Any,
        co_purchase: dict[str, dict[str, Any]] | None,
        backend: SimilarityBackend | None,
    ) -> RecommendationSet:
        items = [c for c in catalog if isinstance(c, dict)] if isinstance(catalog, list) else []
        by_id = {_item_id(c): c for c in items if _item_id(c)}

        profile = self._build_profile(user, by_id)
        strategy = Strategy.POPULARITY_COLD_START if profile.empty else Strategy.PERSONALIZED
        co = co_purchase if isinstance(co_purchase, dict) else {}

        # Precompute similarity contributions per candidate from the user's owned items.
        sim_scores = self._similarity_scores(profile.owned_ids, backend) if backend else {}

        scored: list[Recommendation] = []
        for c in items:
            cid = _item_id(c)
            if not cid or cid in profile.owned_ids:
                continue
            score, reasons = self._score(c, cid, profile, co, sim_scores)
            scored.append(
                Recommendation(item_id=cid, score=round(score, 4), reasons=tuple(reasons))
            )

        # Stable, deterministic ordering: score desc, then id asc.
        scored.sort(key=lambda r: (-r.score, r.item_id))
        return RecommendationSet(uid, strategy, tuple(scored[: self.top_n]))

    def _build_profile(self, user: dict, by_id: dict[str, dict]) -> _Profile:
        purchased = user.get("purchased")
        owned_ids: set[str] = set()
        profile_items: list[dict] = []
        if isinstance(purchased, list):
            for entry in purchased:
                pid = _item_id(entry)
                if pid:
                    owned_ids.add(pid)
                source = by_id.get(pid) or (entry if isinstance(entry, dict) else None)
                if source is not None:
                    profile_items.append(source)

        collections = {_collection(i) for i in profile_items if _collection(i)}
        tags: set[str] = set()
        for i in profile_items:
            tags |= _tags(i)
        prices = [p for p in (_price(i) for i in profile_items) if p is not None and p > 0]
        avg_price = (sum(prices) / len(prices)) if prices else None

        return _Profile(
            collections=frozenset(collections),
            tags=frozenset(tags),
            avg_price=avg_price,
            owned_ids=frozenset(owned_ids),
        )

    def _similarity_scores(
        self, owned_ids: frozenset[str], backend: SimilarityBackend
    ) -> dict[str, float]:
        out: dict[str, float] = {}
        for oid in owned_ids:
            try:
                pairs = backend.similar(oid, self.similarity_k)
            except Exception:
                continue
            for cand_id, sim in pairs or []:
                val = _to_float(sim)
                if val is not None:
                    out[str(cand_id)] = out.get(str(cand_id), 0.0) + val
        return out

    def _score(
        self,
        item: dict,
        cid: str,
        profile: _Profile,
        co: dict[str, dict[str, Any]],
        sim_scores: dict[str, float],
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        if not profile.empty:
            if _collection(item) and _collection(item) in profile.collections:
                score += self.collection_match_weight
                reasons.append(f"same collection: {item.get('collection')}")

            shared = _tags(item) & profile.tags
            if shared:
                score += self.tag_overlap_weight * len(shared)
                reasons.append(f"shares tag: {', '.join(sorted(shared))}")

            price = _price(item)
            if profile.avg_price and price is not None:
                closeness = max(0.0, 1.0 - abs(price - profile.avg_price) / profile.avg_price)
                if closeness > 0:
                    score += self.price_proximity_weight * closeness
                    reasons.append("matches your price range")

            co_count = sum(
                _to_float((co.get(oid) or {}).get(cid)) or 0.0 for oid in profile.owned_ids
            )
            if co_count > 0:
                score += self.copurchase_weight * co_count
                reasons.append("frequently bought together")

            sim = sim_scores.get(cid, 0.0)
            if sim > 0:
                score += self.similarity_weight * sim
                reasons.append("similar to items you bought")

        pop = _popularity(item)
        if pop > 0:
            # log-scale so a runaway bestseller can't swamp personalized signals; monotonic,
            # so cold-start popularity ordering is preserved.
            score += self.popularity_weight * math.log1p(pop)
            if profile.empty:
                reasons.append("popular")

        return score, reasons


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def format_recommendations(rs: RecommendationSet) -> str:
    """Render a :class:`RecommendationSet` as a markdown summary."""
    lines = [
        f"## Recommendations — user {rs.user_id or 'n/a'} ({rs.strategy.name})",
        "",
    ]
    if not rs.items:
        lines.append("No recommendations available.")
        return "\n".join(lines)
    lines.append("| # | Item | Score | Why |")
    lines.append("|---|------|-------|-----|")
    for i, r in enumerate(rs.items, 1):
        why = "; ".join(r.reasons) if r.reasons else "—"
        lines.append(f"| {i} | {r.item_id} | {r.score:.2f} | {why} |")
    return "\n".join(lines)


__all__ = [
    "Recommendation",
    "RecommendationSet",
    "Recommender",
    "SimilarityBackend",
    "Strategy",
    "format_recommendations",
]
