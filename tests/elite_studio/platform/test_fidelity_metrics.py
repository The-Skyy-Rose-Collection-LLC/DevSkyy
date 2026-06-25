from skyyrose.elite_studio.platform.fidelity.metrics import VisibleScore, composite_score


def test_composite_is_weighted_mean_of_components():
    s = composite_score(dino=0.90, clip=0.80, ssim=0.70)
    # default weights dino .5 / clip .2 / ssim .3 -> .45+.16+.21 = .82
    assert round(s, 4) == 0.82


def test_visible_score_passes_above_threshold():
    vs = VisibleScore(angle="front", dino=0.9, clip=0.85, ssim=0.88, composite=0.886)
    assert vs.passes(threshold=0.85) is True


def test_visible_score_fails_below_threshold():
    vs = VisibleScore(angle="front", dino=0.5, clip=0.5, ssim=0.5, composite=0.5)
    assert vs.passes(threshold=0.85) is False
