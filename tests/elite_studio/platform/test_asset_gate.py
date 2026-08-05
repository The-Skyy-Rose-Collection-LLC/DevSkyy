import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from skyyrose.elite_studio.platform.fidelity.asset_gate import (
    AssetGateDisposition,
    AssetVerificationRequest,
    canonical_json,
    sha256_file,
    verify_visual_asset,
)
from skyyrose.elite_studio.platform.fidelity.render import RENDER_ANGLES


class _FakeScore:
    composite = 0.98

    def passes(self, threshold):
        return self.composite >= threshold


class _FailingScore(_FakeScore):
    composite = 0.94


class _FakeViews:
    def __init__(self, paths: dict[str, Path]):
        self.angle_paths = paths

    def verified_angles(self):
        return tuple(RENDER_ANGLES)

    def inferred_angles(self):
        return ()


class _FakeRenderer:
    def __init__(self, paths: dict[str, Path]):
        self.paths = paths

    def render(self, model_path, references):
        return _FakeViews(self.paths)


def _write_trust_manifest(path: Path, build_key, founder_key) -> None:
    def pem(key):
        return key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    path.write_text(
        json.dumps(
            {
                "trust_roots": {
                    "build_attestation": {
                        "public_keys": [{"id": "build-test", "public_key_pem": pem(build_key)}]
                    },
                },
                "authority": {
                    "approval_verification": {
                        "public_keys": [{"id": "founder-test", "public_key_pem": pem(founder_key)}]
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path):
    model = tmp_path / "sg-015-candidate.glb"
    model.write_bytes(b"glTF-test-model")
    references = tmp_path / "references"
    reference_dir = references / "sg-015"
    reference_dir.mkdir(parents=True)
    for angle in RENDER_ANGLES:
        (reference_dir / f"{angle}.jpg").write_bytes(f"approved-{angle}".encode())
    reference_hashes = {
        angle: sha256_file(reference_dir / f"{angle}.jpg") for angle in RENDER_ANGLES
    }
    build_key = Ed25519PrivateKey.generate()
    founder_key = Ed25519PrivateKey.generate()
    trust_manifest = tmp_path / "trust.json"
    _write_trust_manifest(trust_manifest, build_key, founder_key)
    provenance = {
        "sku": "sg-015",
        "source_kind": "approved_sot",
        "model_sha256": sha256_file(model),
        "reference_sha256": reference_hashes,
        "key_id": "build-test",
    }
    provenance["signature"] = base64.b64encode(build_key.sign(canonical_json(provenance))).decode()
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    return model, references, trust_manifest, provenance_path, founder_key, reference_dir


def _request(tmp_path, model, refs, trust, provenance, approval=None):
    return AssetVerificationRequest(
        sku="sg-015",
        model_path=model,
        reference_root=refs,
        provenance_path=provenance,
        trust_manifest_path=trust,
        approval_path=approval,
        report_root=tmp_path / "reports",
    )


def test_missing_canonical_references_reject_before_render(tmp_path):
    model = tmp_path / "sg-015-candidate.glb"
    model.write_bytes(b"model")
    refs = tmp_path / "references" / "sg-015"
    refs.mkdir(parents=True)
    (refs / "front.jpg").write_bytes(b"front")
    provenance = tmp_path / "provenance.json"
    provenance.write_text("{}", encoding="utf-8")
    trust = tmp_path / "trust.json"
    trust.write_text('{"trust_roots": {}}', encoding="utf-8")

    report = verify_visual_asset(
        _request(tmp_path, model, tmp_path / "references", trust, provenance)
    )

    assert report.disposition is AssetGateDisposition.REJECT
    assert report.render_attempted is False
    assert "back" in report.missing_angles


def test_model_must_be_bound_to_exact_sku(tmp_path):
    model, refs, trust, provenance, _, _ = _fixture(tmp_path)
    wrong_model = tmp_path / "br-006-candidate.glb"
    wrong_model.write_bytes(model.read_bytes())

    report = verify_visual_asset(
        _request(tmp_path, wrong_model, refs, trust, provenance)
    )

    assert report.disposition is AssetGateDisposition.REJECT
    assert any("exact SKU" in reason for reason in report.reasons)


def test_complete_visual_gate_requires_founder_approval(tmp_path):
    model, refs, trust, provenance, founder_key, ref_dir = _fixture(tmp_path)
    rendered = {angle: ref_dir / f"{angle}.jpg" for angle in RENDER_ANGLES}
    request = _request(tmp_path, model, refs, trust, provenance)

    pending = verify_visual_asset(
        request,
        renderer=_FakeRenderer(rendered),
        scorer=lambda *args, **kwargs: _FakeScore(),
    )

    assert pending.disposition is AssetGateDisposition.READY_FOR_FOUNDER_APPROVAL
    assert pending.founder_approval_verified is False
    assert set(pending.verified_angles) == set(RENDER_ANGLES)

    approval_payload = {
        "decision": "approve",
        "sku": "sg-015",
        "model_sha256": pending.model_sha256,
        "approved_by": "Corey Foster",
        "authority": "Founder",
        "approved_at": "2026-08-04",
        "key_id": "founder-test",
    }
    approval_payload["signature"] = base64.b64encode(
        founder_key.sign(canonical_json(approval_payload))
    ).decode()
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps(approval_payload), encoding="utf-8")

    approved = verify_visual_asset(
        _request(tmp_path, model, refs, trust, provenance, approval),
        renderer=_FakeRenderer(rendered),
        scorer=lambda *args, **kwargs: _FakeScore(),
    )

    assert approved.disposition is AssetGateDisposition.APPROVED
    assert approved.founder_approval_verified is True


def test_visual_threshold_failure_is_reject(tmp_path):
    model, refs, trust, provenance, _, ref_dir = _fixture(tmp_path)
    rendered = {angle: ref_dir / f"{angle}.jpg" for angle in RENDER_ANGLES}
    report = verify_visual_asset(
        _request(tmp_path, model, refs, trust, provenance),
        renderer=_FakeRenderer(rendered),
        scorer=lambda *args, **kwargs: _FailingScore(),
    )

    assert report.disposition is AssetGateDisposition.REJECT
    assert report.render_attempted is True
    assert any("fidelity threshold" in reason for reason in report.reasons)
