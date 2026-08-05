"""Fail-closed planning and execution boundary for catalog-wide 3D replicas.

The existing ``pipeline3d`` executor knows how to run provider stages. This
module governs whether a paid provider may be constructed at all and what may
happen to its result:

* every requested SKU must exist exactly once in the catalog;
* every SKU must have the complete canonical reference pack;
* reference and trust-root hashes are frozen into a deterministic manifest;
* the whole batch must fit a caller-supplied, deterministic rate card;
* the provider adapter factory is called only after those checks pass; and
* every provider result is sent to ``asset_gate`` and is never published here.

No Tripo or Meshy SDK is imported. Provider calls live behind the injected
``ReplicaProviderAdapter`` protocol, which also keeps unit tests free of paid
or network activity.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from skyyrose.elite_studio.platform.fidelity.asset_gate import (
    AssetGateDisposition,
    AssetVerificationReport,
    AssetVerificationRequest,
    resolve_references,
    sha256_file,
    verify_visual_asset,
)
from skyyrose.elite_studio.platform.fidelity.render import RENDER_ANGLES

_SKU_RE = re.compile(r"^[a-z]{2,4}-\d{3}$")
_SUPPORTED_PROVIDERS = frozenset({"tripo", "meshy"})
_MONEY_QUANTUM = Decimal("0.0001")
_MANIFEST_SCHEMA = "skyyrose.replica-production.v1"


class ReplicaPipelineError(RuntimeError):
    """Base exception for replica planning and execution failures."""


class ReplicaPreflightError(ReplicaPipelineError):
    """Preflight evidence is incomplete or changed; no provider may run."""


class ReplicaBudgetError(ReplicaPipelineError):
    """The complete requested batch exceeds its deterministic budget."""


class ReplicaProviderError(ReplicaPipelineError):
    """The injected provider does not satisfy the approved plan."""


class ReplicaPlanState(StrEnum):
    """Persisted lifecycle states for the orchestration manifest."""

    PLANNED = "planned"
    PREFLIGHT_BLOCKED = "preflight_blocked"
    RUNNING = "running"
    GATE_BLOCKED = "gate_blocked"
    AWAITING_APPROVAL = "awaiting_founder_approval"
    COMPLETE = "complete"


@dataclass(frozen=True)
class CostLine:
    """One immutable line in a provider rate card."""

    operation: str
    usd: Decimal

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("cost operation cannot be blank")
        object.__setattr__(self, "usd", _money(self.usd))


@dataclass(frozen=True)
class ProviderRateCard:
    """Caller-supplied pricing snapshot used for deterministic planning."""

    provider: str
    lines: tuple[CostLine, ...]

    def __post_init__(self) -> None:
        normalized = self.provider.strip().lower()
        if normalized not in _SUPPORTED_PROVIDERS:
            raise ValueError(f"unsupported replica provider: {self.provider!r}")
        lines = tuple(self.lines)
        if not lines:
            raise ValueError("provider rate card must contain at least one cost line")
        if not all(isinstance(line, CostLine) for line in lines):
            raise TypeError("provider rate card lines must be CostLine values")
        names = [line.operation for line in lines]
        if len(names) != len(set(names)):
            raise ValueError("provider rate card operations must be unique")
        object.__setattr__(self, "provider", normalized)
        object.__setattr__(self, "lines", lines)

    @property
    def per_sku_usd(self) -> Decimal:
        """Exact planned cost for one SKU under this pricing snapshot."""

        return _money(sum((line.usd for line in self.lines), start=Decimal("0")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "lines": [
                {"operation": line.operation, "usd": _money_text(line.usd)} for line in self.lines
            ],
            "per_sku_usd": _money_text(self.per_sku_usd),
        }


@dataclass(frozen=True)
class ReferenceAsset:
    """A canonical reference frozen by path and content hash."""

    angle: str
    path: Path
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {"angle": self.angle, "path": str(self.path), "sha256": self.sha256}


@dataclass(frozen=True)
class ReplicaJobPlan:
    """Preflight result for one exact catalog SKU."""

    sku: str
    name: str
    references: tuple[ReferenceAsset, ...]
    missing_angles: tuple[str, ...]
    reference_errors: tuple[str, ...]
    cost_usd: Decimal

    @property
    def ready(self) -> bool:
        return (
            not self.missing_angles
            and not self.reference_errors
            and len(self.references) == len(RENDER_ANGLES)
        )

    def reference_map(self) -> dict[str, Path]:
        return {reference.angle: reference.path for reference in self.references}

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "ready": self.ready,
            "missing_angles": list(self.missing_angles),
            "reference_errors": list(self.reference_errors),
            "cost_usd": _money_text(self.cost_usd),
            "references": [reference.to_dict() for reference in self.references],
        }


@dataclass(frozen=True)
class ReplicaBatchPlan:
    """Deterministic, persisted plan for a requested catalog scope."""

    plan_id: str
    catalog_path: Path
    catalog_sha256: str
    reference_root: Path
    trust_manifest_path: Path
    trust_manifest_sha256: str
    rate_card: ProviderRateCard
    budget_ceiling_usd: Decimal
    jobs: tuple[ReplicaJobPlan, ...]
    manifest_path: Path

    @property
    def planned_cost_usd(self) -> Decimal:
        return _money(sum((job.cost_usd for job in self.jobs), start=Decimal("0")))

    @property
    def blocked_skus(self) -> tuple[str, ...]:
        return tuple(job.sku for job in self.jobs if not job.ready)

    @property
    def budget_ok(self) -> bool:
        return self.planned_cost_usd <= self.budget_ceiling_usd

    @property
    def dispatchable(self) -> bool:
        return bool(self.jobs) and not self.blocked_skus and self.budget_ok

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": _MANIFEST_SCHEMA,
            "plan_id": self.plan_id,
            "catalog": {
                "path": str(self.catalog_path),
                "sha256": self.catalog_sha256,
            },
            "reference_root": str(self.reference_root),
            "trust_manifest": {
                "path": str(self.trust_manifest_path),
                "sha256": self.trust_manifest_sha256,
            },
            "rate_card": self.rate_card.to_dict(),
            "budget": {
                "ceiling_usd": _money_text(self.budget_ceiling_usd),
                "planned_usd": _money_text(self.planned_cost_usd),
                "within_budget": self.budget_ok,
            },
            "dispatchable": self.dispatchable,
            "blocked_skus": list(self.blocked_skus),
            "jobs": [job.to_dict() for job in self.jobs],
        }


@dataclass(frozen=True)
class ProviderCandidate:
    """Untrusted provider output; it is a gate input, never a publishable asset."""

    sku: str
    model_path: Path
    provenance_path: Path
    provider_job_id: str


@runtime_checkable
class ReplicaProviderAdapter(Protocol):
    """Port implemented by a paid Tripo or Meshy adapter outside this module."""

    name: str

    async def create_replica(
        self,
        *,
        plan_id: str,
        sku: str,
        references: dict[str, Path],
        committed_cost_usd: Decimal,
    ) -> ProviderCandidate:
        """Create one candidate without publishing it."""
        ...


@dataclass(frozen=True)
class ReplicaJobOutcome:
    """Provider and gate outcome for one SKU."""

    sku: str
    provider_job_id: str | None
    committed_cost_usd: Decimal
    model_path: str | None = None
    provenance_path: str | None = None
    gate_disposition: str | None = None
    gate_report: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "provider_job_id": self.provider_job_id,
            "committed_cost_usd": _money_text(self.committed_cost_usd),
            "model_path": self.model_path,
            "provenance_path": self.provenance_path,
            "gate_disposition": self.gate_disposition,
            "gate_report": self.gate_report,
            "error": self.error,
        }


@dataclass(frozen=True)
class ReplicaExecutionResult:
    """Final state of a bounded replica run."""

    plan_id: str
    state: ReplicaPlanState
    outcomes: tuple[ReplicaJobOutcome, ...]
    committed_cost_usd: Decimal
    manifest_path: Path


def _money(value: Decimal | str | int | float) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(_MONEY_QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid USD amount: {value!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"USD amount must be finite and non-negative: {value!r}")
    return amount


def _money_text(value: Decimal) -> str:
    return f"{_money(value):.4f}"


def _load_catalog(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise ReplicaPreflightError(f"catalog does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "sku" not in rows[0]:
        raise ReplicaPreflightError("catalog is empty or has no sku column")

    catalog: dict[str, dict[str, str]] = {}
    for row in rows:
        sku = row.get("sku", "").strip()
        if not _SKU_RE.fullmatch(sku):
            raise ReplicaPreflightError(f"catalog contains invalid canonical SKU: {sku!r}")
        if sku in catalog:
            raise ReplicaPreflightError(f"catalog contains duplicate SKU: {sku}")
        catalog[sku] = row
    return catalog


def _validate_json_object(path: Path, label: str) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise ReplicaPreflightError(f"{label} does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplicaPreflightError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ReplicaPreflightError(f"{label} must contain a JSON object")
    return value, sha256_file(path)


def _validate_trust_manifest(path: Path) -> str:
    """Require the trust roots needed to attest and approve a paid candidate."""

    value, digest = _validate_json_object(path, "trust manifest")

    def public_keys(*sections: str) -> list[Any]:
        current: Any = value
        for section in sections:
            if not isinstance(current, dict):
                return []
            current = current.get(section)
        return current if isinstance(current, list) else []

    build_keys = public_keys("trust_roots", "build_attestation", "public_keys")
    policy_keys = public_keys("trust_roots", "policy_attestation", "public_keys")
    founder_keys = public_keys("authority", "approval_verification", "public_keys")
    for label, keys in (
        ("build attestor", build_keys),
        ("policy collector", policy_keys),
        ("founder", founder_keys),
    ):
        configured = any(
            isinstance(item, dict) and item.get("id") and item.get("public_key_pem")
            for item in keys
        )
        if not configured:
            raise ReplicaPreflightError(
                f"trust manifest has no configured {label} public key; paid dispatch is blocked"
            )
    return digest


def _reference_integrity_error(path: Path) -> str | None:
    """Return an image-integrity error without transforming the approved source."""

    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
        if width <= 0 or height <= 0:
            return "image has invalid dimensions"
    except Exception as exc:  # noqa: BLE001 - corrupt images must fail preflight
        return f"image decode failed: {type(exc).__name__}: {exc}"
    return None


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _manifest_payload(
    plan: ReplicaBatchPlan,
    *,
    state: ReplicaPlanState,
    outcomes: Sequence[ReplicaJobOutcome] = (),
    committed_cost_usd: Decimal = Decimal("0"),
    reasons: Sequence[str] = (),
) -> dict[str, Any]:
    payload = plan.to_dict()
    payload.update(
        {
            "state": state.value,
            "committed_cost_usd": _money_text(committed_cost_usd),
            "outcomes": [outcome.to_dict() for outcome in outcomes],
            "reasons": list(reasons),
            "publishing_authorized": False,
        }
    )
    return payload


def build_replica_plan(
    *,
    catalog_path: str | Path,
    reference_root: str | Path,
    trust_manifest_path: str | Path,
    rate_card: ProviderRateCard,
    budget_ceiling_usd: Decimal | str | int | float,
    manifest_root: str | Path,
    skus: Sequence[str] | None = None,
) -> ReplicaBatchPlan:
    """Validate a catalog scope, price it, and persist a deterministic plan.

    ``skus=None`` means every catalog row. A requested subset is matched by
    exact SKU only; aliases, filename inference, and case folding are forbidden.
    Missing canonical angles remain visible in the plan and make the entire
    requested batch non-dispatchable.
    """

    catalog_path = Path(catalog_path).resolve()
    reference_root = Path(reference_root).resolve()
    trust_manifest_path = Path(trust_manifest_path).resolve()
    manifest_root = Path(manifest_root).resolve()
    budget = _money(budget_ceiling_usd)

    catalog = _load_catalog(catalog_path)
    trust_sha256 = _validate_trust_manifest(trust_manifest_path)

    if isinstance(skus, (str, bytes)):
        raise ReplicaPreflightError("skus must be a sequence of exact SKU values, not a string")
    requested = sorted(catalog) if skus is None else list(skus)
    if not requested:
        raise ReplicaPreflightError("replica plan must contain at least one SKU")
    if len(requested) != len(set(requested)):
        raise ReplicaPreflightError("requested SKU list contains duplicates")
    for sku in requested:
        if not _SKU_RE.fullmatch(sku):
            raise ReplicaPreflightError(f"invalid canonical SKU: {sku!r}")
        if sku not in catalog:
            raise ReplicaPreflightError(f"SKU is not an exact catalog record: {sku}")

    jobs: list[ReplicaJobPlan] = []
    for sku in sorted(requested):
        resolved = resolve_references(reference_root, sku)
        references = tuple(
            ReferenceAsset(
                angle=angle,
                path=resolved[angle].resolve(),
                sha256=sha256_file(resolved[angle]),
            )
            for angle in RENDER_ANGLES
            if angle in resolved
        )
        missing = tuple(angle for angle in RENDER_ANGLES if angle not in resolved)
        reference_errors = [
            f"{reference.angle}: {error}"
            for reference in references
            if (error := _reference_integrity_error(reference.path)) is not None
        ]
        hashes_to_angles: dict[str, list[str]] = {}
        for reference in references:
            hashes_to_angles.setdefault(reference.sha256, []).append(reference.angle)
        reference_errors.extend(
            "duplicate image content across angles: " + ", ".join(angles)
            for angles in hashes_to_angles.values()
            if len(angles) > 1
        )
        jobs.append(
            ReplicaJobPlan(
                sku=sku,
                name=catalog[sku].get("name", "").strip(),
                references=references,
                missing_angles=missing,
                reference_errors=tuple(reference_errors),
                cost_usd=rate_card.per_sku_usd,
            )
        )

    identity_payload = {
        "schema": _MANIFEST_SCHEMA,
        "catalog_sha256": sha256_file(catalog_path),
        "trust_manifest_sha256": trust_sha256,
        "reference_root": str(reference_root),
        "rate_card": rate_card.to_dict(),
        "budget_ceiling_usd": _money_text(budget),
        "jobs": [job.to_dict() for job in jobs],
    }
    plan_id = hashlib.sha256(_canonical_bytes(identity_payload)).hexdigest()[:20]
    manifest_path = manifest_root / f"{plan_id}.json"
    plan = ReplicaBatchPlan(
        plan_id=plan_id,
        catalog_path=catalog_path,
        catalog_sha256=identity_payload["catalog_sha256"],
        reference_root=reference_root,
        trust_manifest_path=trust_manifest_path,
        trust_manifest_sha256=trust_sha256,
        rate_card=rate_card,
        budget_ceiling_usd=budget,
        jobs=tuple(jobs),
        manifest_path=manifest_path,
    )
    _atomic_write_json(manifest_path, _manifest_payload(plan, state=ReplicaPlanState.PLANNED))
    return plan


def _revalidate_plan(plan: ReplicaBatchPlan) -> list[str]:
    reasons: list[str] = []
    if not plan.catalog_path.is_file():
        reasons.append("catalog disappeared after planning")
    elif sha256_file(plan.catalog_path) != plan.catalog_sha256:
        reasons.append("catalog changed after planning")
    if not plan.trust_manifest_path.is_file():
        reasons.append("trust manifest disappeared after planning")
    elif sha256_file(plan.trust_manifest_path) != plan.trust_manifest_sha256:
        reasons.append("trust manifest changed after planning")
    for job in plan.jobs:
        if not job.ready:
            if job.missing_angles:
                reasons.append(
                    f"{job.sku} is missing canonical references: {', '.join(job.missing_angles)}"
                )
            reasons.extend(f"{job.sku} reference error: {error}" for error in job.reference_errors)
            continue
        for reference in job.references:
            if not reference.path.is_file():
                reasons.append(f"{job.sku}/{reference.angle} reference disappeared")
            elif sha256_file(reference.path) != reference.sha256:
                reasons.append(f"{job.sku}/{reference.angle} reference changed after planning")
    return reasons


async def execute_replica_plan(
    plan: ReplicaBatchPlan,
    *,
    adapter_factory: Callable[[str], ReplicaProviderAdapter],
    report_root: str | Path,
    approval_root: str | Path | None = None,
    policy_attestation_root: str | Path | None = None,
    gate: Callable[[AssetVerificationRequest], AssetVerificationReport] = verify_visual_asset,
) -> ReplicaExecutionResult:
    """Dispatch a preflighted batch and route every candidate into ``asset_gate``.

    The adapter factory is deliberately invoked *after* the complete-batch
    preflight and budget checks. Provider failures and gate rejections stop the
    batch immediately to cap avoidable spend. This function does not copy,
    publish, or register any candidate in a storefront.
    """

    if not plan.budget_ok:
        reason = (
            f"planned cost {_money_text(plan.planned_cost_usd)} exceeds budget "
            f"{_money_text(plan.budget_ceiling_usd)}"
        )
        _atomic_write_json(
            plan.manifest_path,
            _manifest_payload(plan, state=ReplicaPlanState.PREFLIGHT_BLOCKED, reasons=[reason]),
        )
        raise ReplicaBudgetError(reason)

    reasons = _revalidate_plan(plan)
    if reasons:
        _atomic_write_json(
            plan.manifest_path,
            _manifest_payload(plan, state=ReplicaPlanState.PREFLIGHT_BLOCKED, reasons=reasons),
        )
        raise ReplicaPreflightError("; ".join(reasons))

    try:
        adapter = adapter_factory(plan.rate_card.provider)
    except Exception as exc:
        reason = f"adapter initialization failed closed: {type(exc).__name__}: {exc}"
        _atomic_write_json(
            plan.manifest_path,
            _manifest_payload(plan, state=ReplicaPlanState.PREFLIGHT_BLOCKED, reasons=[reason]),
        )
        raise ReplicaProviderError(reason) from exc
    adapter_name = getattr(adapter, "name", "").strip().lower()
    if adapter_name != plan.rate_card.provider:
        reason = (
            f"adapter provider mismatch: planned={plan.rate_card.provider!r}, "
            f"received={adapter_name!r}"
        )
        _atomic_write_json(
            plan.manifest_path,
            _manifest_payload(plan, state=ReplicaPlanState.PREFLIGHT_BLOCKED, reasons=[reason]),
        )
        raise ReplicaProviderError(reason)

    report_root = Path(report_root).resolve()
    approval_root_path = Path(approval_root).resolve() if approval_root is not None else None
    policy_attestation_root_path = (
        Path(policy_attestation_root).resolve() if policy_attestation_root is not None else None
    )
    outcomes: list[ReplicaJobOutcome] = []
    committed = Decimal("0")
    final_state = ReplicaPlanState.COMPLETE
    awaiting_approval = False
    _atomic_write_json(
        plan.manifest_path,
        _manifest_payload(plan, state=ReplicaPlanState.RUNNING),
    )

    for job in plan.jobs:
        committed = _money(committed + job.cost_usd)
        try:
            candidate = await adapter.create_replica(
                plan_id=plan.plan_id,
                sku=job.sku,
                references=job.reference_map(),
                committed_cost_usd=job.cost_usd,
            )
        except Exception as exc:  # noqa: BLE001 - provider boundary must persist failure
            outcomes.append(
                ReplicaJobOutcome(
                    sku=job.sku,
                    provider_job_id=None,
                    committed_cost_usd=job.cost_usd,
                    error=f"provider dispatch failed closed: {type(exc).__name__}: {exc}",
                )
            )
            final_state = ReplicaPlanState.GATE_BLOCKED
            break

        approval_path = None
        if approval_root_path is not None:
            candidate_approval = approval_root_path / f"{job.sku}.json"
            approval_path = candidate_approval if candidate_approval.is_file() else None

        policy_attestation_path = None
        if policy_attestation_root_path is not None:
            candidate_policy_attestation = policy_attestation_root_path / f"{job.sku}.json"
            policy_attestation_path = (
                candidate_policy_attestation if candidate_policy_attestation.is_file() else None
            )

        request = AssetVerificationRequest(
            sku=job.sku,
            model_path=Path(candidate.model_path),
            reference_root=plan.reference_root,
            provenance_path=Path(candidate.provenance_path),
            trust_manifest_path=plan.trust_manifest_path,
            approval_path=approval_path,
            policy_attestation_path=policy_attestation_path,
            report_root=report_root,
        )
        try:
            gate_report = gate(request)
            disposition = gate_report.disposition.value
            error = None
        except Exception as exc:  # noqa: BLE001 - a dead gate is a blocked gate
            gate_report = None
            disposition = AssetGateDisposition.REJECT.value
            error = f"asset gate failed closed: {type(exc).__name__}: {exc}"

        if candidate.sku != job.sku:
            error = (
                f"provider result SKU mismatch: expected={job.sku!r}, "
                f"received={candidate.sku!r}"
            )
            disposition = AssetGateDisposition.REJECT.value

        outcomes.append(
            ReplicaJobOutcome(
                sku=job.sku,
                provider_job_id=candidate.provider_job_id,
                committed_cost_usd=job.cost_usd,
                model_path=str(candidate.model_path),
                provenance_path=str(candidate.provenance_path),
                gate_disposition=disposition,
                gate_report=gate_report.to_dict() if gate_report is not None else None,
                error=error,
            )
        )

        allowed_dispositions = {
            AssetGateDisposition.APPROVED.value,
            AssetGateDisposition.READY_FOR_FOUNDER_APPROVAL.value,
        }
        if disposition not in allowed_dispositions:
            final_state = ReplicaPlanState.GATE_BLOCKED
            break
        if disposition == AssetGateDisposition.READY_FOR_FOUNDER_APPROVAL.value:
            awaiting_approval = True

        _atomic_write_json(
            plan.manifest_path,
            _manifest_payload(
                plan,
                state=ReplicaPlanState.RUNNING,
                outcomes=outcomes,
                committed_cost_usd=committed,
            ),
        )

    if len(outcomes) != len(plan.jobs) and final_state is ReplicaPlanState.COMPLETE:
        final_state = ReplicaPlanState.GATE_BLOCKED
    if awaiting_approval and final_state is not ReplicaPlanState.GATE_BLOCKED:
        final_state = ReplicaPlanState.AWAITING_APPROVAL

    _atomic_write_json(
        plan.manifest_path,
        _manifest_payload(
            plan,
            state=final_state,
            outcomes=outcomes,
            committed_cost_usd=committed,
        ),
    )
    return ReplicaExecutionResult(
        plan_id=plan.plan_id,
        state=final_state,
        outcomes=tuple(outcomes),
        committed_cost_usd=committed,
        manifest_path=plan.manifest_path,
    )


__all__ = [
    "CostLine",
    "ProviderCandidate",
    "ProviderRateCard",
    "ReplicaBatchPlan",
    "ReplicaBudgetError",
    "ReplicaExecutionResult",
    "ReplicaJobOutcome",
    "ReplicaJobPlan",
    "ReplicaPipelineError",
    "ReplicaPlanState",
    "ReplicaPreflightError",
    "ReplicaProviderAdapter",
    "ReplicaProviderError",
    "build_replica_plan",
    "execute_replica_plan",
]
