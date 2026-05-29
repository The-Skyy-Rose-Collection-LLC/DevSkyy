from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict
from skyyrose.elite_studio.platform.tenancy import TenantRegistry
from skyyrose.elite_studio.ventures.threed.service import (
    ReplicaOutcome,
    default_replica_runner,
    run_replica,
)


def _fake_generate(image_path, sku):
    return {"local_path": "/tmp/mesh.glb", "status": "completed"}


def _fake_evaluate(tenant_id, sku, mesh_path):
    return FidelityReport(
        tenant_id=tenant_id,
        sku=sku,
        mesh_path=mesh_path,
        verdict=FidelityVerdict.HUMAN_QUEUE,
        composite_by_angle={"front": 0.91},
        verified_angles=("front",),
        inferred_angles=("back",),
        violations=(),
        attempts=1,
    )


def test_human_queue_verdict_enqueues_not_delivers(tmp_path):
    outcome = run_replica(
        tenant_id="skyyrose",
        sku="br-001",
        source_image="/g/front.jpg",
        generate_fn=_fake_generate,
        evaluate_fn=_fake_evaluate,
        report_base=tmp_path,
        approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "queued_for_human"
    assert outcome.approval_id
    assert outcome.delivered_path == ""


def test_reject_verdict_does_not_enqueue(tmp_path):
    def _reject_eval(tenant_id, sku, mesh_path):
        return FidelityReport(
            tenant_id=tenant_id,
            sku=sku,
            mesh_path=mesh_path,
            verdict=FidelityVerdict.REJECT,
            composite_by_angle={"front": 0.4},
            verified_angles=("front",),
            inferred_angles=(),
            violations=(),
            attempts=1,
        )

    outcome = run_replica(
        tenant_id="skyyrose",
        sku="br-001",
        source_image="/g/front.jpg",
        generate_fn=_fake_generate,
        evaluate_fn=_reject_eval,
        report_base=tmp_path,
        approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "rejected"
    assert outcome.approval_id == ""


def test_default_replica_runner_wires_engine_and_gate_into_run_replica(tmp_path):
    tenant = TenantRegistry.default().get("skyyrose")
    outcome = default_replica_runner(
        tenant=tenant,
        sku="br-001",
        source_image="/g/front.jpg",
        generate_fn=_fake_generate,
        evaluate_fn=_fake_evaluate,
        report_base=tmp_path,
        approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "queued_for_human"
    assert outcome.approval_id
