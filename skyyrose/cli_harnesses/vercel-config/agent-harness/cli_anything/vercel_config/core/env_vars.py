"""EnvVar dataclass and diff helpers for Vercel environment variables.

Reference: https://vercel.com/docs/rest-api/endpoints/projects#list-environment-variables-of-a-project

Identity tuple: (key, target) — same key name can exist for different targets
                (production, preview, development) with distinct IDs.
Payload:        (value, type, gitBranch)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

# ── Constants ─────────────────────────────────────────────────────────

VALID_TARGETS: FrozenSet[str] = frozenset({"production", "preview", "development"})
VALID_TYPES: FrozenSet[str] = frozenset({"plain", "secret", "encrypted", "sensitive"})

_MASKED = "***"


# ── Dataclass ─────────────────────────────────────────────────────────


@dataclass
class EnvVar:
    """Represents a single Vercel environment variable record.

    Attributes:
        key:        Variable name (e.g. ``DATABASE_URL``).
        value:      Variable value. May be empty string when masked by API.
        env_type:   One of ``plain``, ``secret``, ``encrypted``, ``sensitive``.
        targets:    List of deployment targets this var applies to.
        id:         Vercel-assigned ID (``None`` for locally-declared vars).
        git_branch: Branch name for branch-specific preview vars.
    """

    key: str
    value: str
    env_type: str = "plain"
    targets: List[str] = field(default_factory=lambda: ["production"])
    id: Optional[str] = field(default=None)
    git_branch: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("EnvVar.key must not be empty.")
        for t in self.targets:
            if t not in VALID_TARGETS:
                raise ValueError(f"Invalid target {t!r}. Valid targets: {sorted(VALID_TARGETS)}")
        if self.env_type not in VALID_TYPES:
            raise ValueError(f"Invalid type {self.env_type!r}. Valid types: {sorted(VALID_TYPES)}")

    @property
    def identity(self) -> Tuple[str, Tuple[str, ...]]:
        """Identity tuple: (key, sorted_targets)."""
        return (self.key, tuple(sorted(self.targets)))

    def masked_value(self) -> str:
        """Return masked representation for safe display."""
        return _MASKED

    def display_value(self, reveal: bool = False) -> str:
        """Return value for display; masked unless ``reveal=True``."""
        return self.value if reveal else _MASKED

    def to_create_payload(self) -> Dict[str, Any]:
        """Build a payload dict for POST /v9/projects/{idOrName}/env."""
        payload: Dict[str, Any] = {
            "key": self.key,
            "value": self.value,
            "type": self.env_type,
            "target": self.targets,
        }
        if self.git_branch:
            payload["gitBranch"] = self.git_branch
        return payload

    def to_update_payload(self) -> Dict[str, Any]:
        """Build a payload dict for PATCH /v9/projects/{idOrName}/env/{id}."""
        payload: Dict[str, Any] = {
            "value": self.value,
            "type": self.env_type,
            "target": self.targets,
        }
        if self.git_branch:
            payload["gitBranch"] = self.git_branch
        return payload

    @classmethod
    def from_api(cls, record: Dict[str, Any]) -> "EnvVar":
        """Construct from a Vercel API env record dict."""
        target_raw = record.get("target", ["production"])
        if isinstance(target_raw, str):
            targets = [target_raw]
        else:
            targets = list(target_raw)

        env_type = record.get("type", "plain")
        if env_type not in VALID_TYPES:
            env_type = "plain"

        return cls(
            key=record.get("key", ""),
            value=record.get("value", ""),
            env_type=env_type,
            targets=targets,
            id=record.get("id"),
            git_branch=record.get("gitBranch"),
        )


# ── Diff helpers ──────────────────────────────────────────────────────


@dataclass
class EnvVarDiff:
    """Three-way diff result for a single env var.

    Attributes:
        key:        Variable name.
        targets:    Sorted target list (part of identity).
        action:     ``add`` | ``update`` | ``remove`` | ``unchanged``.
        current:    Current API state (``None`` if not present remotely).
        desired:    Desired state from manifest (``None`` if to be removed).
    """

    key: str
    targets: Tuple[str, ...]
    action: str
    current: Optional[EnvVar]
    desired: Optional[EnvVar]


def diff_env_vars(
    current: List[EnvVar],
    desired: List[EnvVar],
) -> List[EnvVarDiff]:
    """Compute a diff between current (API) and desired (manifest) env vars.

    Identity: (key, sorted_targets) tuple.

    Args:
        current: List of ``EnvVar`` instances from the live Vercel API.
        desired: List of ``EnvVar`` instances declared in the manifest.

    Returns:
        List of ``EnvVarDiff`` instances describing required changes.
        Items with ``action == "unchanged"`` indicate no change needed.
    """
    current_map: Dict[Tuple[str, Tuple[str, ...]], EnvVar] = {ev.identity: ev for ev in current}
    desired_map: Dict[Tuple[str, Tuple[str, ...]], EnvVar] = {ev.identity: ev for ev in desired}

    results: List[EnvVarDiff] = []

    # desired vars — may be add or update
    for identity, des in desired_map.items():
        cur = current_map.get(identity)
        if cur is None:
            results.append(
                EnvVarDiff(
                    key=identity[0],
                    targets=identity[1],
                    action="add",
                    current=None,
                    desired=des,
                )
            )
        elif _env_var_changed(cur, des):
            results.append(
                EnvVarDiff(
                    key=identity[0],
                    targets=identity[1],
                    action="update",
                    current=cur,
                    desired=des,
                )
            )
        else:
            results.append(
                EnvVarDiff(
                    key=identity[0],
                    targets=identity[1],
                    action="unchanged",
                    current=cur,
                    desired=des,
                )
            )

    # current vars not in desired → remove
    for identity, cur in current_map.items():
        if identity not in desired_map:
            results.append(
                EnvVarDiff(
                    key=identity[0],
                    targets=identity[1],
                    action="remove",
                    current=cur,
                    desired=None,
                )
            )

    results.sort(key=lambda d: (d.action, d.key))
    return results


def _env_var_changed(current: EnvVar, desired: EnvVar) -> bool:
    """Return True if the env var payload differs (value, type, or gitBranch)."""
    if current.value and desired.value and current.value != desired.value:
        return True
    if current.env_type != desired.env_type:
        return True
    if current.git_branch != desired.git_branch:
        return True
    return False
