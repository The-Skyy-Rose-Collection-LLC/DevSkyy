from dataclasses import dataclass

from skyyrose.elite_studio.platform.capability import CapabilityMatrix, CapabilityStatus
from skyyrose.elite_studio.platform.service import GenerationResult, generate_3d
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


class _FakeMatrix(CapabilityMatrix):
    def probe(self):
        return self


def _green_matrix(tenant):
    statuses = tuple(
        CapabilityStatus(n, True, "ok")
        for n in ("catalog", "reference_store", "fidelity_scorer", "engine_local")
    )
    return _FakeMatrix(tenant=tenant, statuses=statuses)


@dataclass
class _FakeOutcome:
    status: str = "queued_for_human"
    report_path: str = "/r/skyyrose/br-001/fidelity_report_attempt1.json"
    approval_id: str = "ap123"


def test_refuses_when_required_capability_red():
    tenant = TenantRegistry.default().get("skyyrose")
    red = _FakeMatrix(tenant=tenant, statuses=(CapabilityStatus("engine_local", False, "no gpu"),))
    res = generate_3d("skyyrose", "br-001", source_image="/g/front.jpg", generate=True, matrix=red)
    assert res.status == "capability_unavailable"
    assert res.report_path == ""


def test_does_not_generate_when_gate_off():
    tenant = TenantRegistry.default().get("skyyrose")
    res = generate_3d("skyyrose", "br-001", generate=False, matrix=_green_matrix(tenant))
    assert res.status == "not_requested"


def test_unknown_tenant_is_error():
    res = generate_3d("acme", "br-001", generate=True)
    assert res.status == "unknown_tenant"


def test_missing_source_image_is_error():
    tenant = TenantRegistry.default().get("skyyrose")
    res = generate_3d("skyyrose", "br-001", generate=True, matrix=_green_matrix(tenant))
    assert res.status == "missing_source_image"


def test_delegates_to_replica_runner_on_green():
    tenant = TenantRegistry.default().get("skyyrose")
    captured = {}

    def fake_runner(*, tenant, sku, source_image):
        captured["sku"] = sku
        return _FakeOutcome()

    res = generate_3d(
        "skyyrose",
        "br-001",
        source_image="/g/front.jpg",
        generate=True,
        matrix=_green_matrix(tenant),
        replica_runner=fake_runner,
    )
    assert captured["sku"] == "br-001"
    assert res.status == "queued_for_human"
    assert res.approval_id == "ap123"
    assert res.report_path.endswith("fidelity_report_attempt1.json")
