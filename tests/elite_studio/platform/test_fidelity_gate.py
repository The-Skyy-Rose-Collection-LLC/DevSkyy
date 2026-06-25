from skyyrose.elite_studio.platform.fidelity.gate import dispose
from skyyrose.elite_studio.platform.fidelity.metrics import VisibleScore
from skyyrose.elite_studio.platform.fidelity.report import FidelityVerdict


def _vs(angle, composite):
    return VisibleScore(
        angle=angle, dino=composite, clip=composite, ssim=composite, composite=composite
    )


def test_visible_fail_is_reject():
    v = dispose(
        visible=[_vs("front", 0.50)], inferred_angles=("back",), violations=(), threshold=0.85
    )
    assert v is FidelityVerdict.REJECT


def test_visible_pass_with_violation_is_human_queue():
    v = dispose(
        visible=[_vs("front", 0.92)],
        inferred_angles=("back",),
        violations=("off-brand color on back",),
        threshold=0.85,
    )
    assert v is FidelityVerdict.HUMAN_QUEUE


def test_visible_pass_inferred_present_is_human_queue():
    # ANY inferred angle forces human review even with no explicit violation
    v = dispose(
        visible=[_vs("front", 0.92)], inferred_angles=("back",), violations=(), threshold=0.85
    )
    assert v is FidelityVerdict.HUMAN_QUEUE


def test_full_coverage_clean_is_pass_pending_human():
    v = dispose(
        visible=[_vs("front", 0.92), _vs("back", 0.90)],
        inferred_angles=(),
        violations=(),
        threshold=0.85,
    )
    assert v is FidelityVerdict.PASS_PENDING_HUMAN


def test_report_only_threshold_zero_never_rejects_on_score():
    v = dispose(visible=[_vs("front", 0.10)], inferred_angles=(), violations=(), threshold=0.0)
    assert v is FidelityVerdict.PASS_PENDING_HUMAN
