import json
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image

from skyyrose.elite_studio.pipeline3d.replica_pipeline import (
    CostLine,
    ProviderCandidate,
    ProviderRateCard,
    ReplicaBudgetError,
    ReplicaPlanState,
    ReplicaPreflightError,
    ReplicaProviderError,
    build_replica_plan,
    execute_replica_plan,
)
from skyyrose.elite_studio.platform.fidelity.asset_gate import (
    AssetGateDisposition,
    AssetVerificationReport,
)
from skyyrose.elite_studio.platform.fidelity.render import RENDER_ANGLES


def _catalog(path: Path, skus=("br-001", "sg-015")) -> Path:
    rows = ["sku,name,published"]
    rows.extend(f"{sku},{sku} product,1" for sku in skus)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _trust(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "trust_roots": {
                    "build_attestation": {
                        "public_keys": [{"id": "build-1", "public_key_pem": "test-pem"}]
                    },
                    "policy_attestation": {
                        "public_keys": [{"id": "policy-1", "public_key_pem": "test-pem"}]
                    },
                },
                "authority": {
                    "approval_verification": {
                        "public_keys": [{"id": "founder-1", "public_key_pem": "test-pem"}]
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _references(root: Path, sku: str, *, omit: str | None = None) -> None:
    sku_root = root / sku
    sku_root.mkdir(parents=True)
    for index, angle in enumerate(RENDER_ANGLES):
        if angle != omit:
            image = Image.new("RGB", (8, 8), color=(index * 30, len(sku) * 10, 100))
            image.save(sku_root / f"{angle}.jpg")


def _rate(provider="tripo") -> ProviderRateCard:
    return ProviderRateCard(
        provider=provider,
        lines=(
            CostLine("image_to_3d", Decimal("0.4000")),
            CostLine("texture", Decimal("0.2000")),
            CostLine("remesh", Decimal("0.1500")),
        ),
    )


def _plan(tmp_path: Path, *, budget="2.0000", skus=("br-001", "sg-015")):
    catalog = _catalog(tmp_path / "catalog.csv", skus=skus)
    refs = tmp_path / "references"
    for sku in skus:
        _references(refs, sku)
    return build_replica_plan(
        catalog_path=catalog,
        reference_root=refs,
        trust_manifest_path=_trust(tmp_path / "trust.json"),
        rate_card=_rate(),
        budget_ceiling_usd=budget,
        manifest_root=tmp_path / "manifests",
    )


class _Adapter:
    name = "tripo"

    def __init__(self, root: Path, *, fail_sku: str | None = None, result_sku: str | None = None):
        self.root = root
        self.fail_sku = fail_sku
        self.result_sku = result_sku
        self.calls: list[str] = []

    async def create_replica(self, *, plan_id, sku, references, committed_cost_usd):
        self.calls.append(sku)
        assert set(references) == set(RENDER_ANGLES)
        assert committed_cost_usd == Decimal("0.7500")
        if sku == self.fail_sku:
            raise RuntimeError("provider unavailable")
        model = self.root / f"{sku}-candidate.glb"
        provenance = self.root / f"{sku}-provenance.json"
        model.write_bytes(b"glTF")
        provenance.write_text("{}", encoding="utf-8")
        return ProviderCandidate(
            sku=self.result_sku or sku,
            model_path=model,
            provenance_path=provenance,
            provider_job_id=f"job-{sku}",
        )


def _gate(disposition=AssetGateDisposition.APPROVED, calls=None):
    def run(request):
        if calls is not None:
            calls.append(request)
        return AssetVerificationReport(
            sku=request.sku,
            model_path=str(request.model_path),
            disposition=disposition,
        )

    return run


def test_plan_defaults_to_every_exact_catalog_sku_and_is_deterministic(tmp_path):
    first = _plan(tmp_path)
    second = build_replica_plan(
        catalog_path=first.catalog_path,
        reference_root=first.reference_root,
        trust_manifest_path=first.trust_manifest_path,
        rate_card=_rate(),
        budget_ceiling_usd="2.0000",
        manifest_root=tmp_path / "other-manifests",
    )

    assert [job.sku for job in first.jobs] == ["br-001", "sg-015"]
    assert first.planned_cost_usd == Decimal("1.5000")
    assert first.plan_id == second.plan_id
    assert first.dispatchable is True
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    assert manifest["state"] == "planned"
    assert manifest["publishing_authorized"] is False


@pytest.mark.parametrize("sku", ["BR-001", "../br-001", "br_001", "missing-001"])
def test_non_exact_or_unknown_sku_is_rejected(tmp_path, sku):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    with pytest.raises(ReplicaPreflightError):
        build_replica_plan(
            catalog_path=catalog,
            reference_root=tmp_path / "references",
            trust_manifest_path=_trust(tmp_path / "trust.json"),
            rate_card=_rate(),
            budget_ceiling_usd="1.0000",
            manifest_root=tmp_path / "manifests",
            skus=[sku],
        )


def test_string_sku_scope_is_rejected_instead_of_iterated(tmp_path):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    with pytest.raises(ReplicaPreflightError, match="not a string"):
        build_replica_plan(
            catalog_path=catalog,
            reference_root=tmp_path / "references",
            trust_manifest_path=_trust(tmp_path / "trust.json"),
            rate_card=_rate(),
            budget_ceiling_usd="1.0000",
            manifest_root=tmp_path / "manifests",
            skus="br-001",
        )


def test_missing_build_attestor_trust_root_blocks_planning(tmp_path):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    trust = tmp_path / "trust.json"
    trust.write_text('{"trust_roots": [], "authority": {}}', encoding="utf-8")
    with pytest.raises(ReplicaPreflightError, match="build attestor"):
        build_replica_plan(
            catalog_path=catalog,
            reference_root=tmp_path / "references",
            trust_manifest_path=trust,
            rate_card=_rate(),
            budget_ceiling_usd="1.0000",
            manifest_root=tmp_path / "manifests",
        )


@pytest.mark.asyncio
async def test_incomplete_reference_pack_blocks_before_adapter_factory(tmp_path):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    refs = tmp_path / "references"
    _references(refs, "br-001", omit="detail-1")
    plan = build_replica_plan(
        catalog_path=catalog,
        reference_root=refs,
        trust_manifest_path=_trust(tmp_path / "trust.json"),
        rate_card=_rate(),
        budget_ceiling_usd="1.0000",
        manifest_root=tmp_path / "manifests",
    )
    factory_called = False

    def factory(provider):
        nonlocal factory_called
        factory_called = True
        return _Adapter(tmp_path)

    with pytest.raises(ReplicaPreflightError, match="missing canonical references"):
        await execute_replica_plan(
            plan,
            adapter_factory=factory,
            report_root=tmp_path / "reports",
            gate=_gate(),
        )

    assert factory_called is False
    manifest = json.loads(plan.manifest_path.read_text(encoding="utf-8"))
    assert manifest["state"] == "preflight_blocked"


@pytest.mark.asyncio
async def test_duplicate_angle_content_blocks_before_adapter_factory(tmp_path):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    refs = tmp_path / "references"
    _references(refs, "br-001")
    (refs / "br-001" / "back.jpg").write_bytes((refs / "br-001" / "front.jpg").read_bytes())
    plan = build_replica_plan(
        catalog_path=catalog,
        reference_root=refs,
        trust_manifest_path=_trust(tmp_path / "trust.json"),
        rate_card=_rate(),
        budget_ceiling_usd="1.0000",
        manifest_root=tmp_path / "manifests",
    )
    called = False

    def factory(provider):
        nonlocal called
        called = True
        return _Adapter(tmp_path)

    with pytest.raises(ReplicaPreflightError, match="duplicate image content"):
        await execute_replica_plan(
            plan,
            adapter_factory=factory,
            report_root=tmp_path / "reports",
            gate=_gate(),
        )
    assert called is False


@pytest.mark.asyncio
async def test_whole_batch_budget_blocks_before_adapter_factory(tmp_path):
    plan = _plan(tmp_path, budget="1.4999")
    called = False

    def factory(provider):
        nonlocal called
        called = True
        return _Adapter(tmp_path)

    with pytest.raises(ReplicaBudgetError, match="exceeds budget"):
        await execute_replica_plan(
            plan,
            adapter_factory=factory,
            report_root=tmp_path / "reports",
            gate=_gate(),
        )
    assert called is False


@pytest.mark.asyncio
async def test_reference_drift_blocks_before_adapter_factory(tmp_path):
    plan = _plan(tmp_path)
    plan.jobs[0].references[0].path.write_bytes(b"changed after approval")
    called = False

    def factory(provider):
        nonlocal called
        called = True
        return _Adapter(tmp_path)

    with pytest.raises(ReplicaPreflightError, match="changed after planning"):
        await execute_replica_plan(
            plan,
            adapter_factory=factory,
            report_root=tmp_path / "reports",
            gate=_gate(),
        )
    assert called is False


@pytest.mark.asyncio
async def test_provider_adapter_is_created_after_preflight_and_every_result_is_gated(tmp_path):
    plan = _plan(tmp_path)
    events: list[str] = []
    adapter = _Adapter(tmp_path)
    gate_calls = []

    def factory(provider):
        events.append(f"factory:{provider}")
        assert plan.dispatchable
        return adapter

    result = await execute_replica_plan(
        plan,
        adapter_factory=factory,
        report_root=tmp_path / "reports",
        gate=_gate(calls=gate_calls),
    )

    assert events == ["factory:tripo"]
    assert adapter.calls == ["br-001", "sg-015"]
    assert [request.sku for request in gate_calls] == ["br-001", "sg-015"]
    assert result.state is ReplicaPlanState.COMPLETE
    assert result.committed_cost_usd == Decimal("1.5000")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["state"] == "complete"
    assert all(outcome["gate_disposition"] == "approved" for outcome in manifest["outcomes"])
    assert manifest["publishing_authorized"] is False


@pytest.mark.asyncio
async def test_meshy_adapter_uses_the_same_preflight_and_gate_boundary(tmp_path):
    catalog = _catalog(tmp_path / "catalog.csv", skus=("br-001",))
    refs = tmp_path / "references"
    _references(refs, "br-001")
    plan = build_replica_plan(
        catalog_path=catalog,
        reference_root=refs,
        trust_manifest_path=_trust(tmp_path / "trust.json"),
        rate_card=_rate("meshy"),
        budget_ceiling_usd="1.0000",
        manifest_root=tmp_path / "manifests",
    )
    adapter = _Adapter(tmp_path)
    adapter.name = "meshy"

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=_gate(),
    )

    assert adapter.calls == ["br-001"]
    assert result.state is ReplicaPlanState.COMPLETE


@pytest.mark.asyncio
async def test_gate_ready_state_routes_all_jobs_then_awaits_founder(tmp_path):
    plan = _plan(tmp_path)
    adapter = _Adapter(tmp_path)

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=_gate(AssetGateDisposition.READY_FOR_FOUNDER_APPROVAL),
    )

    assert adapter.calls == ["br-001", "sg-015"]
    assert result.state is ReplicaPlanState.AWAITING_APPROVAL
    manifest = json.loads(plan.manifest_path.read_text(encoding="utf-8"))
    assert manifest["state"] == "awaiting_founder_approval"
    assert manifest["publishing_authorized"] is False


@pytest.mark.asyncio
async def test_wrong_provider_adapter_is_rejected_without_dispatch(tmp_path):
    plan = _plan(tmp_path)
    adapter = _Adapter(tmp_path)
    adapter.name = "meshy"

    with pytest.raises(ReplicaProviderError, match="provider mismatch"):
        await execute_replica_plan(
            plan,
            adapter_factory=lambda provider: adapter,
            report_root=tmp_path / "reports",
            gate=_gate(),
        )
    assert adapter.calls == []


@pytest.mark.asyncio
async def test_provider_failure_stops_later_paid_jobs(tmp_path):
    plan = _plan(tmp_path)
    adapter = _Adapter(tmp_path, fail_sku="br-001")

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=_gate(),
    )

    assert adapter.calls == ["br-001"]
    assert result.state is ReplicaPlanState.GATE_BLOCKED
    assert result.committed_cost_usd == Decimal("0.7500")
    assert "provider dispatch failed closed" in result.outcomes[0].error


@pytest.mark.asyncio
async def test_gate_rejection_stops_later_paid_jobs(tmp_path):
    plan = _plan(tmp_path)
    adapter = _Adapter(tmp_path)

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=_gate(AssetGateDisposition.REJECT),
    )

    assert adapter.calls == ["br-001"]
    assert result.state is ReplicaPlanState.GATE_BLOCKED
    assert result.outcomes[0].gate_disposition == "reject"


@pytest.mark.asyncio
async def test_provider_sku_mismatch_is_still_routed_to_gate_then_blocked(tmp_path):
    plan = _plan(tmp_path, skus=("br-001",))
    adapter = _Adapter(tmp_path, result_sku="sg-015")
    gate_calls = []

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=_gate(calls=gate_calls),
    )

    assert len(gate_calls) == 1
    assert gate_calls[0].sku == "br-001"
    assert result.state is ReplicaPlanState.GATE_BLOCKED
    assert result.outcomes[0].gate_disposition == "reject"
    assert "SKU mismatch" in result.outcomes[0].error


@pytest.mark.asyncio
async def test_gate_exception_fails_closed_and_is_persisted(tmp_path):
    plan = _plan(tmp_path, skus=("br-001",))
    adapter = _Adapter(tmp_path)

    def dead_gate(request):
        raise RuntimeError("blender unavailable")

    result = await execute_replica_plan(
        plan,
        adapter_factory=lambda provider: adapter,
        report_root=tmp_path / "reports",
        gate=dead_gate,
    )

    assert result.state is ReplicaPlanState.GATE_BLOCKED
    assert result.outcomes[0].gate_disposition == "reject"
    assert "asset gate failed closed" in result.outcomes[0].error
    manifest = json.loads(plan.manifest_path.read_text(encoding="utf-8"))
    assert manifest["outcomes"][0]["model_path"].endswith("br-001-candidate.glb")
    assert "publish" not in manifest["outcomes"][0]


def test_rate_card_rejects_unknown_provider_and_negative_cost():
    with pytest.raises(ValueError, match="unsupported"):
        _rate("unknown")
    with pytest.raises(ValueError, match="non-negative"):
        CostLine("image_to_3d", Decimal("-0.01"))
