import json

import pytest

from skyyrose.elite_studio.platform.approval import ApprovalQueue
from skyyrose.elite_studio.platform.delivery import NotApprovedError, deliver_approved


def _make_report(tmp_path, mesh):
    rp = tmp_path / "fidelity_report_attempt1.json"
    rp.write_text(json.dumps({"mesh_path": str(mesh)}))
    return rp


def test_delivers_approved_mesh_to_versioned_tree(tmp_path):
    mesh = tmp_path / "m.glb"
    mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    rec = q.enqueue(
        tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh))
    )
    q.approve(rec.id, reviewer="corey")
    products = tmp_path / "products"
    dest = deliver_approved(rec.id, queue=q, products_base=products)
    assert dest == products / "skyyrose" / "br-001" / "v1" / "m.glb"
    assert dest.exists()


def test_second_delivery_bumps_version(tmp_path):
    mesh = tmp_path / "m.glb"
    mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    products = tmp_path / "products"
    dest = None
    for _ in range(2):
        rec = q.enqueue(
            tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh))
        )
        q.approve(rec.id, reviewer="corey")
        dest = deliver_approved(rec.id, queue=q, products_base=products)
    assert dest == products / "skyyrose" / "br-001" / "v2" / "m.glb"


def test_refuses_unapproved_record(tmp_path):
    mesh = tmp_path / "m.glb"
    mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    rec = q.enqueue(
        tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh))
    )
    with pytest.raises(NotApprovedError):
        deliver_approved(rec.id, queue=q, products_base=tmp_path / "products")
