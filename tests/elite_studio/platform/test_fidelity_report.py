import json

from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict


def test_verdict_enum_values():
    assert FidelityVerdict.PASS_PENDING_HUMAN.value == "pass_pending_human"
    assert FidelityVerdict.REJECT.value == "reject"
    assert FidelityVerdict.HUMAN_QUEUE.value == "human_queue"


def test_report_roundtrips_to_json(tmp_path):
    rep = FidelityReport(
        tenant_id="skyyrose",
        sku="br-001",
        mesh_path="/r/x.glb",
        verdict=FidelityVerdict.HUMAN_QUEUE,
        composite_by_angle={"front": 0.91},
        verified_angles=("front",),
        inferred_angles=("back",),
        violations=(),
        attempts=1,
    )
    path = rep.persist(base=tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["verdict"] == "human_queue"
    assert loaded["sku"] == "br-001"
    assert loaded["inferred_angles"] == ["back"]
