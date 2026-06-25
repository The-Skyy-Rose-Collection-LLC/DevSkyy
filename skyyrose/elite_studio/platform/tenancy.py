"""Tenant identity + per-tenant config. Phase 1 = logical isolation.

`tenant_id` namespaces every persisted artifact. SkyyRose is seeded as
tenant #1; adding tenant #2 = implement a CatalogSource + register a Tenant,
no core rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class UnknownTenantError(KeyError):
    """Raised when a tenant_id is not registered."""


@dataclass(frozen=True)
class FidelityThresholds:
    """Per-tenant fidelity gate tuning. Default = report-only (0.0).

    Phase 0 calibration replaces `visible_composite_min` with a real number.
    Until then the gate scores everything and auto-rejects nothing.
    """

    visible_composite_min: float = 0.0


@dataclass(frozen=True)
class Tenant:
    """A brand served by the platform. SkyyRose = tenant #1."""

    id: str
    display_name: str
    catalog_source: str  # dotted import path to a CatalogSource impl
    reference_root: Path
    enabled_engines: frozenset[str]
    thresholds: FidelityThresholds = field(default_factory=FidelityThresholds)

    def product_root(self, base: Path, sku: str, version: int) -> Path:
        """Canonical delivered-asset path: <base>/<tenant>/<sku>/v<version>/."""
        return base / self.id / sku / f"v{version}"


@dataclass(frozen=True)
class TenantRegistry:
    """Resolves tenant_id -> Tenant. Phase 1 seeds SkyyRose only."""

    _tenants: dict[str, Tenant]

    @classmethod
    def default(cls) -> TenantRegistry:
        from skyyrose.core.paths import GOLDEN_DIR

        skyyrose = Tenant(
            id="skyyrose",
            display_name="SkyyRose",
            catalog_source="skyyrose.elite_studio.platform.catalog_source.SkyyRoseCatalogSource",
            reference_root=Path(GOLDEN_DIR),
            enabled_engines=frozenset({"trellis"}),
        )
        return cls(_tenants={skyyrose.id: skyyrose})

    def get(self, tenant_id: str) -> Tenant:
        try:
            return self._tenants[tenant_id]
        except KeyError as exc:
            raise UnknownTenantError(f"Unknown tenant: {tenant_id!r}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._tenants.keys())
