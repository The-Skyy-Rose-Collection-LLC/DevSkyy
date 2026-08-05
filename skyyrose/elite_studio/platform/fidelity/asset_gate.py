"""Fail-closed visual identity gate for generated and 3D product assets.

This module is intentionally stricter than the platform's report-only fidelity
scorer. A model may be used in a storefront only when all of the following are
true:

* the model is bound to the exact SKU;
* every canonical view has a real, approved reference image;
* a provenance attestation binds the model and reference hashes;
* every rendered view clears the calibrated fidelity threshold; and
* a founder approval record is present and signed by a configured trust root.

"Looks close" is not a release state. Missing evidence is a rejection, not a
pass or an inferred success.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .gate import dispose
from .render import BlenderRenderer, RENDER_ANGLES

SKU_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
DEFAULT_THRESHOLD = 0.95
MINIMUM_THRESHOLD = DEFAULT_THRESHOLD
APPROVED_SOURCE_KINDS = frozenset({"approved_sot", "approved_product_media"})


class AssetGateDisposition(StrEnum):
    """Release disposition for a visual product asset."""

    REJECT = "reject"
    HUMAN_REVIEW = "human_review"
    READY_FOR_FOUNDER_APPROVAL = "ready_for_founder_approval"
    APPROVED = "approved"


@dataclass(frozen=True)
class AssetVerificationRequest:
    """Inputs required for a complete visual asset verification."""

    sku: str
    model_path: Path
    reference_root: Path
    provenance_path: Path
    trust_manifest_path: Path
    approval_path: Path | None = None
    policy_attestation_path: Path | None = None
    report_root: Path = Path("renders/fidelity-reports")
    threshold: float = DEFAULT_THRESHOLD


@dataclass
class AssetVerificationReport:
    """Structured evidence emitted by the gate."""

    sku: str
    model_path: str
    disposition: AssetGateDisposition
    reasons: list[str] = field(default_factory=list)
    reference_paths: dict[str, str] = field(default_factory=dict)
    reference_sha256: dict[str, str] = field(default_factory=dict)
    model_sha256: str = ""
    composite_by_angle: dict[str, float] = field(default_factory=dict)
    verified_angles: list[str] = field(default_factory=list)
    missing_angles: list[str] = field(default_factory=list)
    provenance_verified: bool = False
    policy_attestation_verified: bool = False
    founder_approval_verified: bool = False
    render_attempted: bool = False

    def to_dict(self) -> dict[str, Any]:
        output = dict(self.__dict__)
        output["disposition"] = self.disposition.value
        return output

    def persist(self, root: Path) -> Path:
        path = root / self.sku / "visual-asset-verification.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return path


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all at once."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Canonical bytes used by the repository's Ed25519 approval policy."""

    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _reference_for_angle(root: Path, sku: str, angle: str) -> Path | None:
    sku_root = root / sku
    extensions = ("jpg", "jpeg", "png", "webp")
    for extension in extensions:
        candidate = sku_root / f"{angle}.{extension}"
        if candidate.is_file():
            return candidate
    if angle == "front":
        for extension in extensions:
            candidate = sku_root / f"reference.{extension}"
            if candidate.is_file():
                return candidate
    return None


def resolve_references(root: Path, sku: str) -> dict[str, Path]:
    """Resolve only real canonical reference files; never fabricate views."""

    return {
        angle: path
        for angle in RENDER_ANGLES
        if (path := _reference_for_angle(root, sku, angle)) is not None
    }


def _model_contains_sku(model_path: Path, sku: str) -> bool:
    stem = model_path.stem.lower()
    return bool(re.search(rf"(?:^|[-_]){re.escape(sku.lower())}(?:$|[-_])", stem))


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _trust_keys(manifest: dict[str, Any], section: str) -> dict[str, str]:
    if section == "founder":
        # Founder approval is stored under the manifest's authority block;
        # build and policy attestations live under trust_roots.
        section_data = manifest.get("authority", {}).get("approval_verification", {})
    elif section == "policy":
        section_data = manifest.get("trust_roots", {}).get("policy_attestation", {})
    else:
        roots = manifest.get("trust_roots", {})
        section_data = roots.get(section, {})
    return {
        item["id"]: item["public_key_pem"]
        for item in section_data.get("public_keys", [])
        if isinstance(item, dict) and item.get("id") and item.get("public_key_pem")
    }


def _has_configured_policy_root(manifest: dict[str, Any]) -> bool:
    return bool(_trust_keys(manifest, "policy"))


def _verify_signature(payload: dict[str, Any], signature: str, key_pem: str) -> tuple[bool, str]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        key = load_pem_public_key(key_pem.encode("utf-8"))
        if not isinstance(key, Ed25519PublicKey):
            return False, "approval key is not Ed25519"
        key.verify(base64.b64decode(signature, validate=True), canonical_json(payload))
    except Exception as exc:  # cryptography and malformed signatures are gate failures
        return False, f"signature verification failed: {type(exc).__name__}"
    return True, "signature verified"


def _verify_provenance(
    request: AssetVerificationRequest,
    report: AssetVerificationReport,
    references: dict[str, Path],
) -> None:
    if not request.provenance_path.is_file():
        report.reasons.append(f"missing provenance attestation: {request.provenance_path}")
        return
    try:
        provenance = _load_json(request.provenance_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.reasons.append(f"invalid provenance attestation: {exc}")
        return

    if provenance.get("sku") != request.sku:
        report.reasons.append("provenance SKU does not match requested SKU")
    if provenance.get("source_kind") not in APPROVED_SOURCE_KINDS:
        report.reasons.append("provenance source_kind is not an approved SOT source")
    if provenance.get("model_sha256") != report.model_sha256:
        report.reasons.append("provenance model SHA-256 does not match the supplied model")

    expected_refs = provenance.get("reference_sha256")
    if not isinstance(expected_refs, dict):
        report.reasons.append("provenance has no reference_sha256 map")
    else:
        for angle, path in references.items():
            if expected_refs.get(angle) != report.reference_sha256[angle]:
                report.reasons.append(f"provenance reference SHA-256 mismatch: {angle}")

    # A build-attestor signature is required for a generated model. The signed
    # payload excludes only the signature field, matching the trust-root policy.
    signature = provenance.get("signature")
    key_id = provenance.get("key_id")
    try:
        manifest = _load_json(request.trust_manifest_path)
        key_pem = _trust_keys(manifest, "build_attestation").get(key_id)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.reasons.append(f"invalid trust-root manifest: {exc}")
        return
    if not signature or not key_pem:
        report.reasons.append("provenance is not signed by a configured build attestor")
        return
    signed_payload = dict(provenance)
    signed_payload.pop("signature", None)
    ok, reason = _verify_signature(signed_payload, signature, key_pem)
    if not ok:
        report.reasons.append(reason)
    else:
        report.provenance_verified = True


def _verify_policy_attestation(
    request: AssetVerificationRequest,
    report: AssetVerificationReport,
) -> None:
    """Require a signed policy-collector record when the manifest configures one."""

    try:
        manifest = _load_json(request.trust_manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.reasons.append(f"invalid trust-root manifest: {exc}")
        return
    if not _has_configured_policy_root(manifest):
        return
    if request.policy_attestation_path is None:
        report.reasons.append("missing policy-collector attestation")
        return
    try:
        attestation = _load_json(request.policy_attestation_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.reasons.append(f"invalid policy-collector attestation: {exc}")
        return

    if attestation.get("decision") != "allow":
        report.reasons.append("policy-collector decision is not allow")
    if attestation.get("sku") != request.sku:
        report.reasons.append("policy-collector SKU does not match requested SKU")
    if attestation.get("model_sha256") != report.model_sha256:
        report.reasons.append("policy-collector model SHA-256 does not match supplied model")
    expected_refs = attestation.get("reference_sha256")
    if not isinstance(expected_refs, dict):
        report.reasons.append("policy-collector attestation has no reference_sha256 map")
    else:
        for angle, digest in report.reference_sha256.items():
            if expected_refs.get(angle) != digest:
                report.reasons.append(f"policy-collector reference SHA-256 mismatch: {angle}")

    key_pem = _trust_keys(manifest, "policy").get(attestation.get("key_id"))
    signature = attestation.get("signature")
    if not key_pem or not signature:
        report.reasons.append("policy-collector attestation is not signed by a configured root")
        return
    signed_payload = dict(attestation)
    signed_payload.pop("signature", None)
    ok, reason = _verify_signature(signed_payload, signature, key_pem)
    if not ok:
        report.reasons.append(reason)
    else:
        report.policy_attestation_verified = True


def _verify_founder_approval(
    request: AssetVerificationRequest, report: AssetVerificationReport
) -> None:
    if request.approval_path is None:
        return
    try:
        approval = _load_json(request.approval_path)
        manifest = _load_json(request.trust_manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report.reasons.append(f"invalid founder approval record: {exc}")
        return

    if approval.get("decision") != "approve":
        report.reasons.append("founder approval decision is not approve")
    if approval.get("sku") != request.sku:
        report.reasons.append("founder approval SKU does not match requested SKU")
    if approval.get("model_sha256") != report.model_sha256:
        report.reasons.append("founder approval model SHA-256 does not match supplied model")
    key_pem = _trust_keys(manifest, "founder").get(approval.get("key_id"))
    signature = approval.get("signature")
    if not key_pem or not signature:
        report.reasons.append("founder approval is not signed by a configured founder root")
        return
    signed_payload = dict(approval)
    signed_payload.pop("signature", None)
    ok, reason = _verify_signature(signed_payload, signature, key_pem)
    if not ok:
        report.reasons.append(reason)
    elif not report.reasons:
        report.founder_approval_verified = True


def verify_visual_asset(
    request: AssetVerificationRequest,
    *,
    renderer: BlenderRenderer | None = None,
    scorer: Any | None = None,
) -> AssetVerificationReport:
    """Run the complete visual identity gate.

    ``scorer`` is injectable for unit tests and for the existing Elite Studio
    scorer. Production runs use ``score_view`` from ``metrics``.
    """

    report = AssetVerificationReport(
        sku=request.sku,
        model_path=str(request.model_path),
        disposition=AssetGateDisposition.REJECT,
    )

    if not math.isfinite(request.threshold) or not (MINIMUM_THRESHOLD <= request.threshold <= 1.0):
        report.reasons.append(
            f"fidelity threshold must be between {MINIMUM_THRESHOLD:.2f} and 1.00"
        )

    if not SKU_RE.fullmatch(request.sku):
        report.reasons.append("SKU is not a canonical lowercase hyphenated SKU")
    if not request.model_path.is_file():
        report.reasons.append(f"model does not exist: {request.model_path}")
    elif request.model_path.suffix.lower() != ".glb":
        report.reasons.append("visual product assets must be GLB files")
    elif not _model_contains_sku(request.model_path, request.sku):
        report.reasons.append("model filename is not bound to the exact SKU")

    if report.reasons:
        report.persist(request.report_root)
        return report

    report.model_sha256 = sha256_file(request.model_path)
    references = resolve_references(request.reference_root, request.sku)
    report.reference_paths = {angle: str(path) for angle, path in references.items()}
    report.reference_sha256 = {angle: sha256_file(path) for angle, path in references.items()}
    report.missing_angles = [angle for angle in RENDER_ANGLES if angle not in references]
    if report.missing_angles:
        report.reasons.append(
            "missing canonical approved references: " + ", ".join(report.missing_angles)
        )

    _verify_provenance(request, report, references)
    _verify_policy_attestation(request, report)
    if report.reasons:
        report.persist(request.report_root)
        return report

    renderer = renderer or BlenderRenderer(output_dir=request.report_root / "renders")
    scorer = scorer
    if scorer is None:
        from .metrics import score_view

        scorer = score_view
    try:
        views = renderer.render(str(request.model_path), references)
        report.render_attempted = True
        report.verified_angles = list(views.verified_angles())
        report.missing_angles = list(views.inferred_angles())
        visible = []
        for angle in views.verified_angles():
            score = scorer(
                views.angle_paths[angle], references[angle], sku=request.sku, angle=angle
            )
            visible.append(score)
            report.composite_by_angle[angle] = float(score.composite)
        verdict = dispose(
            visible=visible,
            inferred_angles=views.inferred_angles(),
            violations=(),
            threshold=request.threshold,
        )
        if verdict.value == "reject":
            report.reasons.append("one or more canonical views failed the fidelity threshold")
        elif verdict.value != "pass_pending_human":
            report.reasons.append("render coverage is incomplete; human review is mandatory")
    except Exception as exc:
        report.reasons.append(f"visual render/score failed closed: {type(exc).__name__}: {exc}")

    if report.reasons:
        report.disposition = AssetGateDisposition.REJECT
    elif request.approval_path is None:
        report.disposition = AssetGateDisposition.READY_FOR_FOUNDER_APPROVAL
    else:
        _verify_founder_approval(request, report)
        report.disposition = (
            AssetGateDisposition.APPROVED
            if report.founder_approval_verified and not report.reasons
            else AssetGateDisposition.HUMAN_REVIEW
        )
    report.persist(request.report_root)
    return report


__all__ = [
    "AssetGateDisposition",
    "AssetVerificationReport",
    "AssetVerificationRequest",
    "DEFAULT_THRESHOLD",
    "MINIMUM_THRESHOLD",
    "canonical_json",
    "resolve_references",
    "sha256_file",
    "verify_visual_asset",
]
