from skyyrose.elite_studio.platform.approval import ApprovalQueue, ApprovalRecord


def test_enqueue_creates_pending_record(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    assert rec.status == "pending"
    assert q.get(rec.id).status == "pending"


def test_approve_transitions_to_approved(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    q.approve(rec.id, reviewer="corey")
    assert q.get(rec.id).status == "approved"


def test_reject_transitions_to_rejected(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    q.reject(rec.id, reviewer="corey", reason="back panel wrong")
    got = q.get(rec.id)
    assert got.status == "rejected" and got.reason == "back panel wrong"


def test_pending_lists_only_pending(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    a = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/a.json")
    q.enqueue(tenant_id="skyyrose", sku="lh-004", report_path="/r/b.json")
    q.approve(a.id, reviewer="corey")
    pending = q.pending(tenant_id="skyyrose")
    assert {r.sku for r in pending} == {"lh-004"}
