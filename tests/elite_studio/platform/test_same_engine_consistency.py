from scripts.phase0_same_engine_consistency import consistency_verdict


def test_high_similarity_allows_transparent_overflow():
    v = consistency_verdict(local_vs_hosted_score=0.97, bar=0.95)
    assert v["transparent_overflow_allowed"] is True


def test_below_bar_requires_human_signoff():
    v = consistency_verdict(local_vs_hosted_score=0.80, bar=0.95)
    assert v["transparent_overflow_allowed"] is False
    assert "human sign-off" in v["policy"]
