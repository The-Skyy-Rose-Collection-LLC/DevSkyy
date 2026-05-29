import pytest

from skyyrose.elite_studio.platform.tenancy import (
    FidelityThresholds,
    Tenant,
    TenantRegistry,
    UnknownTenantError,
)


def test_default_thresholds_are_report_only():
    t = FidelityThresholds()
    assert t.visible_composite_min == 0.0  # report-only until Phase 0 calibrates


def test_registry_resolves_seeded_skyyrose():
    reg = TenantRegistry.default()
    tenant = reg.get("skyyrose")
    assert tenant.id == "skyyrose"
    assert "trellis" in tenant.enabled_engines


def test_registry_unknown_tenant_raises():
    reg = TenantRegistry.default()
    with pytest.raises(UnknownTenantError):
        reg.get("acme")


def test_tenant_output_root_is_namespaced(tmp_path):
    reg = TenantRegistry.default()
    tenant = reg.get("skyyrose")
    root = tenant.product_root(base=tmp_path, sku="br-001", version=2)
    assert root == tmp_path / "skyyrose" / "br-001" / "v2"
