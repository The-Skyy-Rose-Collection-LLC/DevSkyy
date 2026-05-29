import pytest

from scripts.phase0_engine_ab import (
    ABRow,
    build_manifest,
    manifest_total,
    recommend_threshold,
    run_ab,
)
from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget


def test_recommend_threshold_is_min_passing_minus_margin():
    rows = [
        ABRow(sku="br-001", engine="trellis", visible_score=0.91),
        ABRow(sku="lh-004", engine="trellis", visible_score=0.88),
        ABRow(sku="br-001", engine="meshy", visible_score=0.74),
    ]
    # threshold = lowest TRELLIS score (0.88) minus a 0.03 safety margin
    assert recommend_threshold(rows, engine="trellis", margin=0.03) == 0.85


def test_recommend_threshold_ignores_other_engines():
    rows = [ABRow(sku="br-001", engine="meshy", visible_score=0.50)]
    assert recommend_threshold(rows, engine="trellis", margin=0.03) is None


def test_build_manifest_pairs_every_sku_with_every_engine():
    manifest = build_manifest(("br-001", "lh-004"), ("tripo", "meshy"), lambda s: f"/g/{s}.jpg")
    assert len(manifest) == 4
    tripo = next(m for m in manifest if m.sku == "br-001" and m.engine == "tripo")
    assert tripo.cost_usd == 0.25
    assert tripo.source_image == "/g/br-001.jpg"


def test_manifest_total_sums_costs():
    manifest = build_manifest(("br-001",), ("tripo", "meshy"), lambda s: "/g/x.jpg")
    assert manifest_total(manifest) == 0.45  # 0.25 + 0.20


def test_run_ab_dispatches_each_pair_and_records_spend():
    calls = []

    def dispatch(sku, engine, src):
        calls.append((sku, engine, src))
        return f"/tmp/{sku}_{engine}.glb"

    budget = RunBudget(ceiling_usd=100.0)
    rows = run_ab(
        skus=("br-001",),
        engines=("tripo", "meshy"),
        source_for=lambda s: "/g/front.jpg",
        dispatch_fn=dispatch,
        score_fn=lambda sku, mesh: 0.9,
        budget=budget,
    )
    assert [(r.engine, r.visible_score) for r in rows] == [("tripo", 0.9), ("meshy", 0.9)]
    assert len(calls) == 2
    assert budget.spent_usd == pytest.approx(0.45)


def test_run_ab_halts_on_budget_before_dispatch():
    dispatched = []

    def dispatch(sku, engine, src):
        dispatched.append(engine)
        return "/tmp/x.glb"

    budget = RunBudget(ceiling_usd=0.10)  # below tripo's $0.25
    with pytest.raises(BudgetExceededError):
        run_ab(
            skus=("br-001",),
            engines=("tripo",),
            source_for=lambda s: "/g/front.jpg",
            dispatch_fn=dispatch,
            score_fn=lambda sku, mesh: 0.9,
            budget=budget,
        )
    assert dispatched == []  # never dispatched — gated before spend
