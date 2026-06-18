"""Manifest model for vercel-config — declarative project settings.

A manifest is a JSON file (``vercel-config.json`` by default) that declares
the desired state of a Vercel project's settings.  The CLI can:

  - ``manifest plan``  — show a three-way diff: actual (API) vs declared (file)
  - ``manifest apply`` — apply the diff (with STOP-AND-SHOW confirmation)

Schema
------
::

    {
      "schema": "cli-anything-vercel-config/manifest/v1",
      "project": "my-project",
      "teamId": "team_xxxxxx",          // optional
      "projectPatch": {                  // optional PATCH /v9/projects/{id} fields
        "framework": "nextjs",
        "nodeVersion": "20.x"
      },
      "envVars": [                       // optional env var declarations
        {
          "key": "DATABASE_URL",
          "value": "postgres://...",
          "type": "plain",
          "target": ["production", "preview"]
        }
      ],
      "domains": [                       // optional domain declarations
        {
          "name": "www.example.com",
          "redirect": null
        }
      ]
    }

Three-way diff model
--------------------
For each resource type the diff compares:

  actual    — live state fetched from Vercel API
  declared  — state written in ``vercel-config.json``
  changes   — what the CLI will do to reconcile actual → declared

If a resource is in ``actual`` but not in ``declared``, it is left alone
(the manifest is *additive-only* for unlisted resources, unless
``removeUnlisted: true`` is set per section).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from cli_anything.vercel_config.core.domains import Domain, DomainDiff, diff_domains
from cli_anything.vercel_config.core.env_vars import EnvVar, EnvVarDiff, diff_env_vars

# ── Constants ─────────────────────────────────────────────────────────

MANIFEST_SCHEMA = "cli-anything-vercel-config/manifest/v1"
DEFAULT_MANIFEST_FILENAME = "vercel-config.json"


# ── Dataclass ─────────────────────────────────────────────────────────


@dataclass
class Manifest:
    """In-memory representation of a vercel-config.json manifest.

    Attributes:
        project:          Project ID or slug (required).
        team_id:          Optional Vercel team ID.
        project_patch:    Dict of fields to PATCH on the project.
        env_vars:         Declared env vars.
        domains:          Declared domains.
        remove_unlisted_env:     If True, env vars not in manifest are removed.
        remove_unlisted_domains: If True, domains not in manifest are removed.
        source_path:      Path the manifest was loaded from (or ``None``).
    """

    project: str
    team_id: Optional[str] = field(default=None)
    project_patch: Dict[str, Any] = field(default_factory=dict)
    env_vars: List[EnvVar] = field(default_factory=list)
    domains: List[Domain] = field(default_factory=list)
    remove_unlisted_env: bool = field(default=False)
    remove_unlisted_domains: bool = field(default=False)
    source_path: Optional[Path] = field(default=None)

    def __post_init__(self) -> None:
        if not self.project or not self.project.strip():
            raise ValueError("Manifest.project must not be empty.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-serializable dict."""
        d: Dict[str, Any] = {
            "schema": MANIFEST_SCHEMA,
            "project": self.project,
        }
        if self.team_id:
            d["teamId"] = self.team_id
        if self.project_patch:
            d["projectPatch"] = self.project_patch
        if self.env_vars:
            d["envVars"] = [
                {
                    "key": ev.key,
                    "value": ev.value,
                    "type": ev.env_type,
                    "target": ev.targets,
                    **({"gitBranch": ev.git_branch} if ev.git_branch else {}),
                }
                for ev in self.env_vars
            ]
        if self.domains:
            d["domains"] = [
                {
                    "name": dom.name,
                    **({"redirect": dom.redirect} if dom.redirect else {}),
                    **({"gitBranch": dom.git_branch} if dom.git_branch else {}),
                }
                for dom in self.domains
            ]
        if self.remove_unlisted_env:
            d["removeUnlistedEnv"] = True
        if self.remove_unlisted_domains:
            d["removeUnlistedDomains"] = True
        return d

    def save(self, path: Optional[Path] = None) -> Path:
        """Write manifest to disk atomically.

        Args:
            path: Target path.  Defaults to ``source_path`` or
                  ``./vercel-config.json``.

        Returns:
            The path written.
        """
        target = path or self.source_path or Path(DEFAULT_MANIFEST_FILENAME)
        _atomic_write_json(target, self.to_dict())
        return target


# ── Plan result ───────────────────────────────────────────────────────


@dataclass
class ManifestPlan:
    """Result of a three-way diff between live API state and a manifest.

    Attributes:
        project_patch:  Non-empty dict of fields to patch, or empty dict.
        env_diffs:      List of ``EnvVarDiff`` items (all actions, incl. unchanged).
        domain_diffs:   List of ``DomainDiff`` items.
        has_changes:    True if any add/update/remove actions exist.
    """

    project_patch: Dict[str, Any]
    env_diffs: List[EnvVarDiff]
    domain_diffs: List[DomainDiff]

    @property
    def has_changes(self) -> bool:
        """True if any actionable diffs exist."""
        for d in self.env_diffs:
            if d.action != "unchanged":
                return True
        for d in self.domain_diffs:
            if d.action != "unchanged":
                return True
        if self.project_patch:
            return True
        return False

    @property
    def env_changes(self) -> List[EnvVarDiff]:
        return [d for d in self.env_diffs if d.action != "unchanged"]

    @property
    def domain_changes(self) -> List[DomainDiff]:
        return [d for d in self.domain_diffs if d.action != "unchanged"]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize plan to a JSON-safe dict."""
        return {
            "projectPatch": self.project_patch,
            "envChanges": [
                {
                    "key": d.key,
                    "targets": list(d.targets),
                    "action": d.action,
                }
                for d in self.env_changes
            ],
            "domainChanges": [
                {
                    "name": d.name,
                    "action": d.action,
                }
                for d in self.domain_changes
            ],
            "hasChanges": self.has_changes,
        }


# ── Plan builder ──────────────────────────────────────────────────────


def build_plan(
    manifest: Manifest,
    actual_project: Dict[str, Any],
    actual_env_vars: List[EnvVar],
    actual_domains: List[Domain],
) -> ManifestPlan:
    """Compute a plan by diffing manifest declared state against live API state.

    Args:
        manifest:        Parsed manifest.
        actual_project:  Raw project dict from GET /v9/projects/{idOrName}.
        actual_env_vars: List of ``EnvVar`` from GET /v9/projects/{id}/env.
        actual_domains:  List of ``Domain`` from GET /v10/projects/{id}/domains.

    Returns:
        ``ManifestPlan`` describing what changes would be applied.
    """
    # Project patch: only fields that differ from live state
    project_patch: Dict[str, Any] = {}
    for k, v in manifest.project_patch.items():
        if actual_project.get(k) != v:
            project_patch[k] = v

    # Env var diff — if remove_unlisted is False, exclude removes from plan
    all_env_diffs = diff_env_vars(actual_env_vars, manifest.env_vars)
    if not manifest.remove_unlisted_env:
        env_diffs = [d for d in all_env_diffs if d.action != "remove"]
    else:
        env_diffs = all_env_diffs

    # Domain diff
    all_domain_diffs = diff_domains(actual_domains, manifest.domains)
    if not manifest.remove_unlisted_domains:
        domain_diffs = [d for d in all_domain_diffs if d.action != "remove"]
    else:
        domain_diffs = all_domain_diffs

    return ManifestPlan(
        project_patch=project_patch,
        env_diffs=env_diffs,
        domain_diffs=domain_diffs,
    )


# ── Loader ────────────────────────────────────────────────────────────


def load_manifest(path: Path) -> Manifest:
    """Load and parse a vercel-config.json manifest from disk.

    Args:
        path: Path to the manifest JSON file.

    Returns:
        Parsed ``Manifest`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Manifest not found: {path}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest JSON parse error in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a JSON object, got {type(data).__name__}")

    project = data.get("project", "").strip()
    if not project:
        raise ValueError("Manifest missing required field 'project'.")

    env_vars: List[EnvVar] = []
    for record in data.get("envVars", []):
        target = record.get("target", ["production"])
        if isinstance(target, str):
            target = [target]
        env_vars.append(
            EnvVar(
                key=record["key"],
                value=record.get("value", ""),
                env_type=record.get("type", "plain"),
                targets=list(target),
                git_branch=record.get("gitBranch"),
            )
        )

    domains: List[Domain] = []
    for record in data.get("domains", []):
        domains.append(
            Domain(
                name=record["name"],
                redirect=record.get("redirect") or None,
                git_branch=record.get("gitBranch") or None,
            )
        )

    return Manifest(
        project=project,
        team_id=data.get("teamId") or None,
        project_patch=data.get("projectPatch", {}),
        env_vars=env_vars,
        domains=domains,
        remove_unlisted_env=bool(data.get("removeUnlistedEnv", False)),
        remove_unlisted_domains=bool(data.get("removeUnlistedDomains", False)),
        source_path=path,
    )


# ── Atomic write ──────────────────────────────────────────────────────


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON to ``path`` atomically using a temp file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".manifest-", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            try:
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
