"""Q-fusion: centroid gate fused into the oai_render QC decision layer.

Model-free — the centroid signal is injected via ``centroid_fn`` (a duck-typed
GateVerdict: ``accepted``/``score``/``threshold``), so no CLIP/DINO cold-start.
The judge is the existing ``judge_fn`` seam.

Modes:
- ``off`` (default): centroid never runs; verdict carries no centroid fields. Back-compat.
- ``advisory``: centroid runs and is RECORDED, but never rejects — ``passed`` = judge only.
                Produces the centroid-vs-judge disagreement data calibration needs.
- ``hard``:     ``passed = on_brand AND judge.pass`` (the post-calibration promotion).
"""

from types import SimpleNamespace

from scripts.oai_render import config
from scripts.oai_render.qc import QCGate, RenderExpectation


def _exp():
    return RenderExpectation(
        sku="br-001",
        name="X",
        style="ghost",
        view="front",
        is_pair=False,
        is_patch=False,
        reference_paths=(),
    )


def _judge_pass(req):
    return (
        {
            "visual_analysis": "v",
            "is_single_photograph": True,
            "garment_matches_reference": True,
            "view_correct": True,
            "branding_legible_and_correct": True,
            "photorealistic_not_flat": True,
            "all_garments_present": True,
            "reason": "pass",
        },
        0.02,
    )


def _judge_fail(req):
    out, cost = _judge_pass(req)
    return ({**out, "garment_matches_reference": False, "reason": "wrong garment"}, cost)


def _centroid(accepted, score, threshold=0.70):
    seen = {"called": False}

    def fn(data):
        seen["called"] = True
        return SimpleNamespace(
            accepted=accepted, score=score, threshold=threshold, reason="centroid"
        )

    fn.seen = seen
    return fn


def _gate(monkeypatch, *, judge_fn, centroid_fn, mode):
    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    monkeypatch.setattr("scripts.oai_render.qc.deterministic_checks", lambda data: [])
    return QCGate(use_judge=True, judge_fn=judge_fn, centroid_fn=centroid_fn, centroid_mode=mode)


def test_advisory_records_centroid_but_does_not_reject(monkeypatch):
    # judge PASSES, centroid REJECTS — advisory must NOT flip passed; only record.
    cfn = _centroid(accepted=False, score=0.55)
    gate = _gate(monkeypatch, judge_fn=_judge_pass, centroid_fn=cfn, mode="advisory")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is True  # judge-only decision; centroid advisory
    assert "off_brand_centroid" not in v.failure_tags
    assert v.on_brand is False
    assert v.centroid_score == 0.55
    assert v.centroid_threshold == 0.70
    assert cfn.seen["called"] is True


def test_advisory_records_on_pass(monkeypatch):
    cfn = _centroid(accepted=True, score=0.82)
    gate = _gate(monkeypatch, judge_fn=_judge_pass, centroid_fn=cfn, mode="advisory")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is True and v.on_brand is True and v.centroid_score == 0.82


def test_hard_mode_rejects_off_brand(monkeypatch):
    # The promotion target: judge passes but centroid rejects -> overall fail.
    cfn = _centroid(accepted=False, score=0.40)
    gate = _gate(monkeypatch, judge_fn=_judge_pass, centroid_fn=cfn, mode="hard")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is False
    assert "off_brand_centroid" in v.failure_tags
    assert v.on_brand is False and v.centroid_score == 0.40


def test_hard_mode_judge_fail_still_fails(monkeypatch):
    # AND semantics: judge fail -> fail even when on-brand.
    cfn = _centroid(accepted=True, score=0.90)
    gate = _gate(monkeypatch, judge_fn=_judge_fail, centroid_fn=cfn, mode="hard")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is False
    assert "garment_mismatch" in v.failure_tags or v.failure_tags  # judge tag present
    assert v.on_brand is True  # both signals recorded


def test_off_mode_default_no_centroid_and_not_called(monkeypatch):
    # Default off: centroid_fn never invoked (no cold-start), no centroid fields.
    cfn = _centroid(accepted=False, score=0.10)
    gate = _gate(monkeypatch, judge_fn=_judge_pass, centroid_fn=cfn, mode="off")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is True
    assert v.centroid_score is None and v.on_brand is None
    assert cfn.seen["called"] is False


def test_malformed_centroid_verdict_degrades_to_none(monkeypatch):
    # A centroid backend returning a bad-typed verdict must NOT raise into the gate:
    # the signal is dropped (fields None) and the judge decision stands.
    def bad(data):
        return SimpleNamespace(accepted="yes", score="not-a-number", threshold=0.7, reason="x")

    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    monkeypatch.setattr("scripts.oai_render.qc.deterministic_checks", lambda data: [])
    gate = QCGate(use_judge=True, judge_fn=_judge_pass, centroid_fn=bad, centroid_mode="advisory")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is True
    assert v.centroid_score is None and v.on_brand is None


def test_centroid_fn_exception_degrades_to_none(monkeypatch):
    # A centroid_fn that raises must be swallowed (advisory signal never breaks the gate).
    def boom(data):
        raise RuntimeError("centroid backend down")

    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    monkeypatch.setattr("scripts.oai_render.qc.deterministic_checks", lambda data: [])
    gate = QCGate(use_judge=True, judge_fn=_judge_pass, centroid_fn=boom, centroid_mode="hard")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is True  # judge passed; down centroid does not reject even in hard mode
    assert v.centroid_score is None and v.on_brand is None


def test_centroid_skipped_on_deterministic_reject(monkeypatch):
    # A corrupt image fails deterministic checks -> centroid never runs.
    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    monkeypatch.setattr(
        "scripts.oai_render.qc.deterministic_checks", lambda data: ["corrupt_image"]
    )
    cfn = _centroid(accepted=True, score=0.99)
    gate = QCGate(use_judge=True, judge_fn=_judge_pass, centroid_fn=cfn, centroid_mode="advisory")
    v = gate.check(b"\x89PNG", _exp())
    assert v.passed is False and "corrupt_image" in v.failure_tags
    assert v.centroid_score is None and cfn.seen["called"] is False
