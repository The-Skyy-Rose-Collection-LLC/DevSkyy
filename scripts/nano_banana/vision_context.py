"""Typed container for the dual-role product context object.

Replaces the string-keyed `vision_desc` dict that pipeline.run_single
was mutating to carry both inferred Gemini DNA and canonical-dossier
spec/dossier. The dict-of-everything was a structural smell — the
2026-05-04 code review flagged it as the kind of carrier that grows
keys silently and hides which fields belong to which producer.

VisionContext makes the four sources explicit:

  - `inferred`: Gemini-vision output from describe_product (the
    fabric_appearance, graphics, garment_type guesses).
  - `catalog`: SKU row fields from the canonical CSV (name, collection,
    price). Empty when no catalog merge has run.
  - `spec`: the multi-section judge spec authored from the canonical
    dossier. None when no dossier file exists for the SKU.
  - `dossier`: the full Dossier object — kept for callers that need
    the structured fields (negative_block, branding_block, etc.) rather
    than the synthesized spec text.

Backward-compat shim: `__getitem__` / `__contains__` / `get` proxy to
the merged view in this priority order:
    spec/dossier (special keys) > catalog > inferred

This means existing consumers like `tournament._dna_to_spec` and
`router.route_product` — which read `dna.get("spec")`,
`dna.get("garment_type")`, `dna.get("_dossier")`, etc. — keep working
without modification. Phase 3's blast radius stays at the 2 write
sites in pipeline.run_single.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from skyyrose.core.dossier_loader import Dossier  # noqa: E402

# Special keys that route to dataclass attributes, not the merged dicts.
# `_dossier` keeps the legacy underscore-prefixed key so callers that
# read `dna.get("_dossier")` (spec_builder.augment_prompt) keep working.
_DOSSIER_KEY = "_dossier"
_SPEC_KEY = "spec"


@dataclass
class VisionContext:
    """Typed container for product context flowing through the pipeline.

    Mutable by design: pipeline.run_single populates spec + dossier mid-
    flow after the canonical dossier is loaded. Construction-time
    co-presence is enforced by `__post_init__`; subsequent attribute
    writes are not re-validated (the pipeline always assigns spec and
    dossier together at line ~173-174).
    """

    inferred: dict = field(default_factory=dict)
    catalog: dict = field(default_factory=dict)
    spec: str | None = None
    dossier: Dossier | None = None

    def __post_init__(self) -> None:
        """Enforce: a None dossier means a None spec.

        The reverse (dossier present, spec None) is allowed because
        `build_judge_spec_from_dossier` can legitimately return an
        empty/None spec for a degenerate dossier — but if we have no
        dossier at all, there's nothing to derive a spec from, so spec
        must also be None.
        """
        if self.dossier is None and self.spec is not None:
            raise ValueError(
                f"VisionContext: spec must be None when dossier is None (got spec={self.spec!r})."
            )

    # ── Mapping-style read shim ────────────────────────────────────────

    def __getitem__(self, key: str):
        """Dict-style read: proxy to attributes / catalog / inferred.

        Lookup order:
          1. `spec` → self.spec (raises KeyError if None)
          2. `_dossier` → self.dossier (raises KeyError if None)
          3. catalog dict
          4. inferred dict
          5. KeyError
        """
        if key == _SPEC_KEY:
            if self.spec is None:
                raise KeyError(key)
            return self.spec
        if key == _DOSSIER_KEY:
            if self.dossier is None:
                raise KeyError(key)
            return self.dossier
        if key in self.catalog:
            return self.catalog[key]
        if key in self.inferred:
            return self.inferred[key]
        raise KeyError(key)

    def __contains__(self, key) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        return True

    def get(self, key: str, default=None):
        """Mapping.get equivalent — never raises."""
        try:
            return self[key]
        except KeyError:
            return default

    # ── JSON serialization ─────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Flat dict view suitable for JSON / logging.

        - Drops the `Dossier` object (large, not JSON-safe).
        - Includes `spec` string when populated.
        - Merges `inferred` and `catalog` with catalog winning on key
          collisions (catalog data is more authoritative).
        """
        out: dict = {}
        out.update(self.inferred)
        out.update(self.catalog)
        if self.spec is not None:
            out[_SPEC_KEY] = self.spec
        return out


__all__ = ["VisionContext"]
