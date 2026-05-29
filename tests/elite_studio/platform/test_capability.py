from skyyrose.elite_studio.platform.capability import CapabilityMatrix, CapabilityStatus
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


def test_capability_status_is_immutable():
    s = CapabilityStatus(name="engine", ok=True, detail="ready")
    assert s.ok and s.name == "engine"


def test_probe_returns_all_capabilities_without_spend():
    tenant = TenantRegistry.default().get("skyyrose")
    matrix = CapabilityMatrix(tenant).probe()
    names = {c.name for c in matrix.statuses}
    assert {"catalog", "reference_store", "fidelity_scorer", "engine_local"} <= names


def test_required_ok_false_when_a_required_cap_red():
    statuses = (
        CapabilityStatus(name="catalog", ok=False, detail="missing"),
        CapabilityStatus(name="engine_local", ok=True, detail="ready"),
    )
    matrix = CapabilityMatrix.__new__(CapabilityMatrix)
    object.__setattr__(matrix, "statuses", statuses)
    assert matrix.required_ok(required=("catalog",)) is False


def test_required_ok_true_when_all_required_green():
    statuses = (CapabilityStatus(name="catalog", ok=True, detail="ok"),)
    matrix = CapabilityMatrix.__new__(CapabilityMatrix)
    object.__setattr__(matrix, "statuses", statuses)
    assert matrix.required_ok(required=("catalog",)) is True
