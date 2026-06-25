"""Cost estimation + STOP-AND-SHOW manifest + hard cap.

Every paid generation must surface an explicit per-image cost manifest and be
approved before any API call. The dollar figures are ESTIMATES (see
``config.EST_COST_PER_IMAGE_USD``) for budgeting; actual spend is billed by
OpenAI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config


class CostCapExceeded(RuntimeError):
    """Raised when a run's estimated cost exceeds the hard cap."""


@dataclass(frozen=True)
class ManifestEntry:
    sku: str
    name: str
    n_images: int
    ref_count: int
    note: str = ""


@dataclass(frozen=True)
class CostManifest:
    entries: list[ManifestEntry] = field(default_factory=list)

    @property
    def n_images(self) -> int:
        return sum(e.n_images for e in self.entries)

    @property
    def est_total_usd(self) -> float:
        return round(self.n_images * config.EST_COST_PER_IMAGE_USD, 2)

    @property
    def over_cap(self) -> bool:
        return self.est_total_usd > config.HARD_COST_CAP_USD


@dataclass
class SpendTracker:
    """Runtime ACTUAL-spend accounting against the hard cap.

    The manifest cap above guards the pre-run ESTIMATE; this guards accumulated
    real spend (renders + QC-gated re-renders + judge calls) during the run, so
    a retry storm can never blow past the cap. Check ``can_afford`` BEFORE every
    paid call; ``add`` after it fires.
    """

    cap_usd: float = config.HARD_COST_CAP_USD
    spent_usd: float = 0.0

    def can_afford(self, next_cost_usd: float) -> bool:
        return (self.spent_usd + next_cost_usd) <= self.cap_usd

    def add(self, cost_usd: float) -> None:
        self.spent_usd = round(self.spent_usd + cost_usd, 6)

    @property
    def remaining_usd(self) -> float:
        return max(0.0, round(self.cap_usd - self.spent_usd, 6))


def enforce_cap(manifest: CostManifest) -> None:
    """Raise CostCapExceeded if the manifest estimate exceeds the hard cap."""
    if manifest.over_cap:
        raise CostCapExceeded(
            f"Estimated ${manifest.est_total_usd:.2f} exceeds hard cap "
            f"${config.HARD_COST_CAP_USD:.2f}. Reduce scope or raise HARD_COST_CAP_USD."
        )


def format_manifest(manifest: CostManifest) -> str:
    """Render the STOP-AND-SHOW cost manifest as a human-readable block."""
    lines = [
        "STOP — Confirm before proceeding (paid OpenAI gpt-image-2 generation):",
        "",
        f"  Model       : {config.MODEL} (quality={config.QUALITY}, size={config.SIZE})",
        f"  Products    : {len(manifest.entries)}",
        f"  Images      : {manifest.n_images}",
        f"  Est. cost   : ~${manifest.est_total_usd:.2f}  "
        f"(ESTIMATE @ ${config.EST_COST_PER_IMAGE_USD:.2f}/image — a FLOOR; verify live pricing)",
        f"  Worst case  : ${config.HARD_COST_CAP_USD:.2f}  "
        f"(runtime SpendTracker hard-stops ACTUAL spend — renders, QC re-renders, judge calls — "
        f"at the cap)",
        f"  Hard cap    : ${config.HARD_COST_CAP_USD:.2f}"
        + ("  ⚠ EXCEEDED" if manifest.over_cap else ""),
        "",
        "  SKU         Images  Refs  Product",
        "  " + "-" * 60,
    ]
    for e in manifest.entries:
        note = f"  [{e.note}]" if e.note else ""
        lines.append(f"  {e.sku:<11} {e.n_images:>6}  {e.ref_count:>4}  {e.name}{note}")
    lines.append("")
    lines.append("Proceed? [y/N]")
    return "\n".join(lines)
