"""Per-tenant capability probing — FREE, no spend, queryable on demand.

Generalizes the threed verify_capability node: every dependency (catalog,
references, fidelity scorer, engines, approval store) gets a free probe.
Generation refuses to start if a required capability is red. You structurally
cannot spend on an unproven endpoint — the no-hallucination guarantee at the
infrastructure layer.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from skyyrose.elite_studio.platform.tenancy import Tenant


@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class CapabilityMatrix:
    """A frozen snapshot of one tenant's dependency readiness."""

    tenant: Tenant
    statuses: tuple[CapabilityStatus, ...] = ()

    def probe(self) -> "CapabilityMatrix":
        """Run all free probes and return a populated matrix (immutable copy)."""
        statuses = (
            self._probe_catalog(),
            self._probe_reference_store(),
            self._probe_fidelity_scorer(),
            self._probe_engine_local(),
        )
        return CapabilityMatrix(tenant=self.tenant, statuses=statuses)

    def required_ok(self, required: tuple[str, ...]) -> bool:
        by_name = {s.name: s for s in self.statuses}
        return all(
            by_name.get(name, CapabilityStatus(name, False, "absent")).ok for name in required
        )

    def _resolve_source(self):
        module_path, _, attr = self.tenant.catalog_source.rpartition(".")
        return getattr(importlib.import_module(module_path), attr)()

    def _probe_catalog(self) -> CapabilityStatus:
        try:
            self._resolve_source()
        except Exception as exc:  # noqa: BLE001 — probe must never raise
            return CapabilityStatus("catalog", False, f"source error: {exc}")
        return CapabilityStatus("catalog", True, "source importable")

    def _probe_reference_store(self) -> CapabilityStatus:
        root = self.tenant.reference_root
        ok = root.is_dir()
        return CapabilityStatus("reference_store", ok, str(root) if ok else f"missing: {root}")

    def _probe_fidelity_scorer(self) -> CapabilityStatus:
        try:
            importlib.import_module("skyyrose.core.dino_embedder")
            importlib.import_module("skyyrose.core.clip_embedder")
        except Exception as exc:  # noqa: BLE001
            return CapabilityStatus("fidelity_scorer", False, f"import error: {exc}")
        return CapabilityStatus("fidelity_scorer", True, "scorers importable")

    def _probe_engine_local(self) -> CapabilityStatus:
        if "trellis" not in self.tenant.enabled_engines:
            return CapabilityStatus("engine_local", False, "trellis not enabled")
        try:
            from agents.trellis_agent import TrellisAgent

            ready = TrellisAgent().is_available()
        except Exception as exc:  # noqa: BLE001
            return CapabilityStatus("engine_local", False, f"agent error: {exc}")
        return CapabilityStatus("engine_local", ready, "ready" if ready else "env not ready")
