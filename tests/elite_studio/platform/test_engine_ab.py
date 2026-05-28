from scripts.phase0_engine_ab import ABRow, recommend_threshold


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
