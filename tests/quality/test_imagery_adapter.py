from evaluation.domains.imagery import IMAGERY_TOOL, ImageryAdapter
from scripts.oai_render.qc import RenderExpectation


def _exp(sku="br-006"):
    return RenderExpectation(
        sku=sku,
        name="Black Rose Bomber Sherpa",
        style="ghost",
        view="front",
        is_pair=False,
        is_patch=False,
        reference_paths=(),
    )


def test_excluded_sku_hard_fails_deterministically():
    ad = ImageryAdapter()
    tags = ad.deterministic_checks(subject=b"\x89PNG...", ref=_exp("sg-006"))
    assert "excluded_sku" in tags


def test_tool_schema_has_visual_analysis_first_and_six_gates():
    props = list(IMAGERY_TOOL["input_schema"]["properties"].keys())
    assert props[0] == "visual_analysis"
    for gate in (
        "is_single_photograph",
        "garment_matches_reference",
        "view_correct",
        "branding_legible_and_correct",
        "photorealistic_not_flat",
        "all_garments_present",
    ):
        assert gate in props


def test_parse_verdict_maps_gates_to_tags():
    ad = ImageryAdapter()
    judge_output = {
        "visual_analysis": "...",
        "is_single_photograph": True,
        "garment_matches_reference": False,
        "view_correct": True,
        "branding_legible_and_correct": True,
        "photorealistic_not_flat": True,
        "all_garments_present": True,
        "reason": "wrong garment",
    }
    v = ad.parse_verdict(judge_output, det_failures=[])
    assert v.passed is False
    assert "wrong_garment" in v.failure_tags
    assert v.score == 5 / 6
    assert v.domain == "imagery"


def test_build_judge_request_structure():
    ad = ImageryAdapter()
    req = ad.build_judge_request(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, _exp())
    assert "messages" in req and req["tool"]["name"] == "render_qc_verdict"
    content = req["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert any(b["type"] == "image" for b in content)


def test_parse_verdict_missing_gate_is_failure():
    ad = ImageryAdapter()
    # judge omitted 'all_garments_present' → must NOT pass (fail-closed)
    out = {
        "visual_analysis": "x",
        "is_single_photograph": True,
        "garment_matches_reference": True,
        "view_correct": True,
        "branding_legible_and_correct": True,
        "photorealistic_not_flat": True,
        "reason": "truncated",
    }
    v = ad.parse_verdict(out, det_failures=[])
    assert v.passed is False
    assert "missing_pair_garment" in v.failure_tags


def test_load_ground_truth_from_review_state(tmp_path):
    import json

    state = {
        "black-rose-crewneck/ghost.png": {"approved": True, "flagged": False, "comment": ""},
        "black-rose-joggers/ghost.png": {"approved": False, "flagged": True, "comment": "logo"},
    }
    f = tmp_path / "review-state.json"
    f.write_text(json.dumps(state))
    ad = ImageryAdapter(review_state_path=f)
    gt = ad.load_ground_truth()
    by = {g["subject_id"]: g["label_pass"] for g in gt}
    assert by["black-rose-crewneck/ghost.png"] is True
    assert by["black-rose-joggers/ghost.png"] is False
