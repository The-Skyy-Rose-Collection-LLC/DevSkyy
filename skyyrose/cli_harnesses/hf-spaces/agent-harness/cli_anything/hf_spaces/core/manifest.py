"""
Manifest plan/apply model for cli-anything-hf-spaces.

A manifest declares the *desired* state of a HuggingFace Space.
plan() diffs desired vs actual and returns a list of ChangeItem objects.
apply() executes the changes after STOP-AND-SHOW confirmation.

Token is never stored in the manifest file.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from cli_anything.hf_spaces.core.hardware import (HARDWARE_SLUGS,
                                                  validate_hardware_slug)

MANIFEST_SCHEMA = "1"
DEFAULT_MANIFEST_NAME = "hf-space-manifest.json"


# ---------------------------------------------------------------------------
# Change model
# ---------------------------------------------------------------------------


class ChangeKind(str, Enum):
    HARDWARE = "hardware"
    SLEEP_TIME = "sleep_time"
    VARIABLE_SET = "variable_set"
    VARIABLE_DELETE = "variable_delete"
    SECRET_SET = "secret_set"  # value never logged
    README_SYNC = "readme_sync"


@dataclass
class ChangeItem:
    kind: ChangeKind
    key: Optional[str]  # variable/secret key, or None for hardware/sleep/readme
    current: Optional[str]  # current value (None for secrets — unreadable)
    desired: Optional[str]  # desired value (None for secret deletes)
    destructive: bool = False  # True → requires --confirm

    def summary(self) -> str:
        """Human-readable one-liner for STOP-AND-SHOW display."""
        if self.kind == ChangeKind.HARDWARE:
            return f"  hardware : {self.current or '?'} → {self.desired}"
        if self.kind == ChangeKind.SLEEP_TIME:
            return f"  sleep_time : {self.current or '?'} → {self.desired}"
        if self.kind == ChangeKind.VARIABLE_SET:
            return f"  var set  : {self.key} = {self.desired!r}"
        if self.kind == ChangeKind.VARIABLE_DELETE:
            return f"  var del  : {self.key}  [destructive]"
        if self.kind == ChangeKind.SECRET_SET:
            return f"  secret   : {self.key} = <value hidden>"
        if self.kind == ChangeKind.README_SYNC:
            return f"  readme   : {self.current or 'remote'} → {self.desired or 'local file'}"
        return f"  {self.kind} : {self.key}"

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "key": self.key,
            "current": self.current,
            "desired": self.desired,
            "destructive": self.destructive,
        }


# ---------------------------------------------------------------------------
# ManifestSpec dataclass
# ---------------------------------------------------------------------------


@dataclass
class ManifestSpec:
    """Desired state for a HuggingFace Space."""

    space_id: str  # owner/name
    hardware: Optional[str] = None  # SpaceHardware slug
    sleep_time: Optional[int] = None  # seconds; -1 = never
    variables: Dict[str, str] = field(default_factory=dict)
    # Secrets: list of key names only. Values supplied interactively at apply time.
    secrets: List[str] = field(default_factory=list)
    readme_path: Optional[str] = None  # local path to README.md

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Raise ValueError if the manifest contains invalid values.
        """
        if not self.space_id or "/" not in self.space_id:
            raise ValueError(f"space_id must be 'owner/name', got: {self.space_id!r}")
        if self.hardware is not None:
            validate_hardware_slug(self.hardware)
        if self.sleep_time is not None:
            if not isinstance(self.sleep_time, int) or (self.sleep_time < -1):
                raise ValueError(
                    f"sleep_time must be -1 (never) or a non-negative integer, got: {self.sleep_time!r}"
                )
        if self.readme_path is not None:
            p = Path(self.readme_path)
            if not p.exists():
                raise ValueError(f"readme_path does not exist: {self.readme_path!r}")

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema_version": MANIFEST_SCHEMA,
            "space_id": self.space_id,
        }
        if self.hardware is not None:
            d["hardware"] = self.hardware
        if self.sleep_time is not None:
            d["sleep_time"] = self.sleep_time
        if self.variables:
            d["variables"] = self.variables
        if self.secrets:
            d["secrets"] = self.secrets
        if self.readme_path is not None:
            d["readme_path"] = self.readme_path
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManifestSpec":
        schema = data.get("schema_version", "1")
        if schema != MANIFEST_SCHEMA:
            raise ValueError(
                f"Unsupported manifest schema_version: {schema!r}. Expected: {MANIFEST_SCHEMA!r}"
            )
        return cls(
            space_id=data["space_id"],
            hardware=data.get("hardware"),
            sleep_time=data.get("sleep_time"),
            variables=data.get("variables", {}),
            secrets=data.get("secrets", []),
            readme_path=data.get("readme_path"),
        )

    @classmethod
    def load(cls, path: Path) -> "ManifestSpec":
        """Load and parse a manifest JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        spec = cls.from_dict(raw)
        spec.validate()
        return spec

    def save(self, path: Path) -> None:
        """Atomically write the manifest to *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent), prefix=".manifest-", suffix=".json"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                try:
                    import fcntl

                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                except (ImportError, OSError):
                    pass
                json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise


# ---------------------------------------------------------------------------
# Plan helpers
# ---------------------------------------------------------------------------


def plan_hardware(
    desired: Optional[str],
    current_hardware: Optional[str],
) -> Optional[ChangeItem]:
    """Return a ChangeItem if hardware needs to change, else None."""
    if desired is None:
        return None
    if desired == current_hardware:
        return None
    return ChangeItem(
        kind=ChangeKind.HARDWARE,
        key=None,
        current=current_hardware,
        desired=desired,
        destructive=True,  # billing impact — always STOP-AND-SHOW
    )


def plan_sleep_time(
    desired: Optional[int],
    current_sleep_time: Optional[int],
) -> Optional[ChangeItem]:
    """Return a ChangeItem if sleep_time needs to change, else None."""
    if desired is None:
        return None
    if desired == current_sleep_time:
        return None
    return ChangeItem(
        kind=ChangeKind.SLEEP_TIME,
        key=None,
        current=str(current_sleep_time) if current_sleep_time is not None else None,
        desired=str(desired),
        destructive=False,
    )


def plan_variables(
    desired: Dict[str, str],
    current: Dict[str, str],
) -> List[ChangeItem]:
    """
    Return ChangeItems for variable additions/updates and deletions.

    Variables present in *current* but absent in *desired* are flagged for
    deletion (destructive=True).
    """
    changes: List[ChangeItem] = []
    for key, value in desired.items():
        if current.get(key) != value:
            changes.append(
                ChangeItem(
                    kind=ChangeKind.VARIABLE_SET,
                    key=key,
                    current=current.get(key),
                    desired=value,
                    destructive=False,
                )
            )
    for key in current:
        if key not in desired:
            changes.append(
                ChangeItem(
                    kind=ChangeKind.VARIABLE_DELETE,
                    key=key,
                    current=current[key],
                    desired=None,
                    destructive=True,
                )
            )
    return changes


def plan_secrets(desired_keys: List[str]) -> List[ChangeItem]:
    """
    Return ChangeItems for all desired secret keys.

    Because HfApi cannot enumerate existing secrets, we always mark them as
    needing re-apply. The value is never stored or logged.
    """
    return [
        ChangeItem(
            kind=ChangeKind.SECRET_SET,
            key=key,
            current=None,  # unreadable by design
            desired="<provided at apply time>",
            destructive=False,
        )
        for key in desired_keys
    ]


def plan_readme(
    desired_path: Optional[str],
    current_readme: Optional[str],
) -> Optional[ChangeItem]:
    """Return a ChangeItem if the local README differs from remote, else None."""
    if desired_path is None:
        return None
    p = Path(desired_path)
    if not p.exists():
        return None
    local_content = p.read_text(encoding="utf-8")
    if local_content == current_readme:
        return None
    return ChangeItem(
        kind=ChangeKind.README_SYNC,
        key=None,
        current="remote",
        desired=str(p),
        destructive=False,
    )


def build_plan(
    spec: ManifestSpec,
    current_hardware: Optional[str],
    current_sleep_time: Optional[int],
    current_variables: Dict[str, str],
    current_readme: Optional[str],
) -> List[ChangeItem]:
    """
    Diff *spec* (desired) against current state and return ordered ChangeItems.
    """
    changes: List[ChangeItem] = []

    hw = plan_hardware(spec.hardware, current_hardware)
    if hw:
        changes.append(hw)

    st = plan_sleep_time(spec.sleep_time, current_sleep_time)
    if st:
        changes.append(st)

    changes.extend(plan_variables(spec.variables, current_variables))
    changes.extend(plan_secrets(spec.secrets))

    readme = plan_readme(spec.readme_path, current_readme)
    if readme:
        changes.append(readme)

    return changes
