"""ProjectRef dataclass — lightweight identity for a Vercel project.

A project is identified by either its numeric/alphanumeric ID
(``prj_xxxxxxxxx``) or its slug name.  This module provides helpers for
parsing user-supplied strings into a canonical ``ProjectRef`` and for
constructing the minimal payload used by PATCH /v9/projects/{idOrName}.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────

_PROJECT_ID_RE = re.compile(r"^prj_[A-Za-z0-9]+$")

# Fields that may be patched via PATCH /v9/projects/{idOrName}
# Reference: https://vercel.com/docs/rest-api/endpoints/projects#update-a-project
_PATCHABLE_FIELDS = frozenset(
    {
        "name",
        "buildCommand",
        "devCommand",
        "framework",
        "installCommand",
        "outputDirectory",
        "publicSource",
        "rootDirectory",
        "serverlessFunctionRegion",
        "skipGitConnectDuringLink",
        "nodeVersion",
        "commandForIgnoringBuildStep",
        "autoExposeSystemEnvs",
        "enablePreviewFeedback",
        "gitForkProtection",
    }
)


# ── Dataclass ─────────────────────────────────────────────────────────


@dataclass
class ProjectRef:
    """Lightweight reference to a Vercel project.

    Attributes:
        id_or_name: Either a ``prj_*`` project ID or a slug name.
        team_id: Optional team ID (``teamId``) for team-scoped projects.
    """

    id_or_name: str
    team_id: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.id_or_name or not self.id_or_name.strip():
            raise ValueError("ProjectRef.id_or_name must not be empty.")
        self.id_or_name = self.id_or_name.strip()

    @property
    def is_id(self) -> bool:
        """True if ``id_or_name`` looks like a ``prj_*`` project ID."""
        return bool(_PROJECT_ID_RE.match(self.id_or_name))

    @property
    def is_slug(self) -> bool:
        """True if ``id_or_name`` looks like a slug (name), not a raw ID."""
        return not self.is_id

    def __str__(self) -> str:
        return self.id_or_name


# ── Parsers ───────────────────────────────────────────────────────────


def parse_project_ref(spec: str) -> ProjectRef:
    """Parse a user-supplied project specifier into a ``ProjectRef``.

    Accepts the following forms:
      - ``prj_abc123``          → ProjectRef(id_or_name="prj_abc123")
      - ``my-project``          → ProjectRef(id_or_name="my-project")
      - ``team_id/project``     → NOT supported by this parser — pass team_id
                                    separately via ``ProjectRef(id_or_name, team_id=...)``

    Args:
        spec: A project ID or slug string from the user.

    Returns:
        A ``ProjectRef`` instance.

    Raises:
        ValueError: If ``spec`` is empty or contains only whitespace.
    """
    return ProjectRef(id_or_name=spec.strip())


# ── Payload builder ───────────────────────────────────────────────────


def build_patch_payload(updates: dict[str, Any]) -> dict[str, Any]:
    """Build a validated PATCH payload for /v9/projects/{idOrName}.

    Filters out unknown fields and returns only the keys present in
    ``_PATCHABLE_FIELDS``.

    Args:
        updates: Raw dict of field → value pairs to apply.

    Returns:
        Filtered dict safe to send as JSON body.

    Raises:
        ValueError: If ``updates`` is empty after filtering.
    """
    filtered = {k: v for k, v in updates.items() if k in _PATCHABLE_FIELDS}
    if not filtered:
        unknown = list(updates.keys())
        raise ValueError(
            f"No patchable fields found in update dict. Unknown keys: {unknown!r}. "
            f"Valid fields: {sorted(_PATCHABLE_FIELDS)}"
        )
    return filtered


def patchable_fields() -> list[str]:
    """Return sorted list of patchable project fields."""
    return sorted(_PATCHABLE_FIELDS)
