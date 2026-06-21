"""Tests for services.personalization.recommender — deterministic per-user reranker.

Contract: deterministic, never-raises, advisory. Content-based + co-purchase + popularity
cold-start. No ML training, no network (an optional similarity backend is a separate port).
"""

from __future__ import annotations

import dataclasses

import pytest
from services.personalization.recommender import (
    Recommendation,
    RecommendationSet,
    Recommender,
    Strategy,
    format_recommendations,
)

CATALOG = [
    {"id": "br-1", "collection": "Black Rose", "price": 200, "tags": ["bomber"], "popularity": 5},
    {"id": "br-2", "collection": "Black Rose", "price": 180, "tags": ["tee"], "popularity": 2},
    {"id": "sig-1", "collection": "Signature", "price": 90, "tags": ["tee"], "popularity": 50},
    {"id": "sig-2", "collection": "Signature", "price": 100, "tags": ["hoodie"], "popularity": 40},
    {"id": "lh-1", "collection": "Love Hurts", "price": 150, "tags": ["bomber"], "popularity": 10},
]


def _ids(rs: RecommendationSet) -> list[str]:
    return [r.item_id for r in rs.items]


# --------------------------------------------------------------------------- #
# Personalization
# --------------------------------------------------------------------------- #


def test_personalized_prefers_same_collection():
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    assert rs.strategy is Strategy.PERSONALIZED
    assert _ids(rs)[0] == "br-2"  # same collection beats popular Signature items
    assert _ids(rs).index("br-2") < _ids(rs).index("sig-1")


def test_excludes_owned_items():
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    assert "br-1" not in _ids(rs)


def test_cold_start_falls_back_to_popularity():
    rs = Recommender().recommend({"id": "u2", "purchased": []}, CATALOG)
    assert rs.strategy is Strategy.POPULARITY_COLD_START
    assert _ids(rs)[0] == "sig-1"  # highest popularity
    assert _ids(rs)[:2] == ["sig-1", "sig-2"]


def test_unknown_purchases_treated_as_cold_start():
    rs = Recommender().recommend({"id": "u3", "purchased": ["does-not-exist"]}, CATALOG)
    assert rs.strategy is Strategy.POPULARITY_COLD_START


def test_copurchase_boost_changes_ranking():
    co = {"br-1": {"sig-2": 1000}}
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG, co_purchase=co)
    assert _ids(rs)[0] == "sig-2"


def test_top_n_limits_results():
    rs = Recommender(top_n=2).recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    assert len(rs.items) == 2


def test_recommendations_have_reasons():
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    assert all(isinstance(r.reasons, tuple) for r in rs.items)
    assert any(r.reasons for r in rs.items)


def test_purchased_as_item_dicts():
    rs = Recommender().recommend(
        {"id": "u1", "purchased": [{"id": "br-1", "collection": "Black Rose"}]}, CATALOG
    )
    assert "br-1" not in _ids(rs)
    assert rs.strategy is Strategy.PERSONALIZED


# --------------------------------------------------------------------------- #
# Robustness
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "user,catalog",
    [
        (None, CATALOG),
        ({}, CATALOG),
        ({"purchased": None}, CATALOG),
        ({"purchased": "nope"}, CATALOG),
        ({"purchased": [None, 5, {"no_id": 1}]}, CATALOG),
        ({"purchased": ["br-1"]}, None),
        ({"purchased": ["br-1"]}, "nope"),
        ({"purchased": ["br-1"]}, [None, "x", {"no_id": 1}]),
        ({"purchased": ["br-1"]}, []),
    ],
)
def test_never_raises_on_garbage(user, catalog):
    rs = Recommender().recommend(user, catalog)
    assert isinstance(rs, RecommendationSet)
    assert all(isinstance(r, Recommendation) for r in rs.items)


# --------------------------------------------------------------------------- #
# Determinism + immutability + serialization
# --------------------------------------------------------------------------- #


def test_deterministic():
    u = {"id": "u1", "purchased": ["br-1"]}
    assert Recommender().recommend(u, CATALOG) == Recommender().recommend(u, CATALOG)


def test_tie_break_is_stable():
    flat = [{"id": f"x-{i}", "collection": "Z", "price": 100, "popularity": 0} for i in range(5)]
    rs = Recommender().recommend({"id": "u", "purchased": []}, flat)
    # All equal score → ordered by id ascending, deterministically.
    assert _ids(rs) == sorted(_ids(rs))


def test_frozen():
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    with pytest.raises(dataclasses.FrozenInstanceError):
        rs.items[0].score = 9.0  # type: ignore[misc]


def test_as_dict_json_safe():
    import json

    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    payload = rs.as_dict()
    json.dumps(payload)
    assert payload["strategy"] == rs.strategy.name
    assert payload["user_id"] == "u1"
    assert isinstance(payload["recommendations"], list)
    assert payload["recommendations"][0]["item_id"] == _ids(rs)[0]


# --------------------------------------------------------------------------- #
# Tunability + reporting + optional similarity port
# --------------------------------------------------------------------------- #


def test_weights_tunable():
    # Crank popularity weight so a popular cross-collection item can outrank same-collection.
    high_pop = Recommender(popularity_weight=10.0)
    rs = high_pop.recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    assert _ids(rs)[0] == "sig-1"


def test_similarity_backend_port_blends_in():
    class FakeBackend:
        def similar(self, item_id, k):
            return [("lh-1", 1.0)] if item_id == "br-1" else []

    rs = Recommender(similarity_weight=1000.0).recommend(
        {"id": "u1", "purchased": ["br-1"]}, CATALOG, similarity_backend=FakeBackend()
    )
    assert _ids(rs)[0] == "lh-1"


def test_format_renders_markdown():
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, CATALOG)
    text = format_recommendations(rs)
    assert "Recommendations" in text
    assert _ids(rs)[0] in text


# --------------------------------------------------------------------------- #
# Regression: adversarial-review fixes
# --------------------------------------------------------------------------- #


def test_popularity_does_not_swamp_personalization():
    """A wildly popular cross-collection item must not outrank a same-collection match
    at default weights — popularity is log-scaled, not raw."""
    catalog = [
        {"id": "br-1", "collection": "Black Rose", "price": 200, "popularity": 1},
        {"id": "br-2", "collection": "Black Rose", "price": 190, "popularity": 1},
        {"id": "sig-hot", "collection": "Signature", "price": 90, "popularity": 100000},
    ]
    rs = Recommender().recommend({"id": "u1", "purchased": ["br-1"]}, catalog)
    assert _ids(rs)[0] == "br-2"  # same collection wins despite sig-hot's huge popularity


def test_price_zero_is_not_dropped():
    from services.personalization.recommender import _price

    assert _price({"price": 0, "regular_price": 999}) == 0.0
    assert _price({"price": None, "regular_price": 999}) == 999.0


def test_dict_purchase_not_in_catalog_is_personalized():
    # A purchase supplied as a dict with attributes builds a profile even if it's not in the
    # catalog — a bare unknown string id does not (that path is cold-start, tested above).
    rs = Recommender().recommend(
        {"id": "u1", "purchased": [{"id": "ghost", "collection": "Black Rose"}]}, CATALOG
    )
    assert rs.strategy is Strategy.PERSONALIZED
    assert _ids(rs)[0] in ("br-1", "br-2")  # Black Rose items surface first
