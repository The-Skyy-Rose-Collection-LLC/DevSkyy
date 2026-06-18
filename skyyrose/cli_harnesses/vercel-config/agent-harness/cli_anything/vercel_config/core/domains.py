"""Domain dataclass and diff helpers for Vercel custom domains.

Reference: https://vercel.com/docs/rest-api/endpoints/projects#retrieve-project-domains

Identity:  hostname string
Payload:   redirect, gitBranch, verified
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Dataclass ─────────────────────────────────────────────────────────


@dataclass
class Domain:
    """Represents a Vercel project domain record.

    Attributes:
        name:       The hostname (e.g. ``www.example.com``).
        redirect:   Optional redirect target hostname.
        git_branch: Optional branch to scope this domain to.
        verified:   Whether Vercel has verified DNS ownership (read-only from API).
    """

    name: str
    redirect: str | None = field(default=None)
    git_branch: str | None = field(default=None)
    verified: bool = field(default=False)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Domain.name must not be empty.")
        self.name = self.name.strip().lower()
        if self.redirect is not None:
            self.redirect = self.redirect.strip().lower() or None

    @property
    def identity(self) -> str:
        """Identity key: normalized hostname."""
        return self.name

    def to_add_payload(self) -> dict[str, Any]:
        """Build a payload dict for POST /v10/projects/{idOrName}/domains."""
        payload: dict[str, Any] = {"name": self.name}
        if self.redirect:
            payload["redirect"] = self.redirect
        if self.git_branch:
            payload["gitBranch"] = self.git_branch
        return payload

    def to_update_payload(self) -> dict[str, Any]:
        """Build a payload dict for PATCH /v10/projects/{idOrName}/domains/{domain}."""
        payload: dict[str, Any] = {}
        if self.redirect is not None:
            payload["redirect"] = self.redirect
        if self.git_branch is not None:
            payload["gitBranch"] = self.git_branch
        return payload

    @classmethod
    def from_api(cls, record: dict[str, Any]) -> Domain:
        """Construct from a Vercel API domain record dict."""
        return cls(
            name=record.get("name", ""),
            redirect=record.get("redirect") or None,
            git_branch=record.get("gitBranch") or None,
            verified=bool(record.get("verified", False)),
        )


# ── Diff helpers ──────────────────────────────────────────────────────


@dataclass
class DomainDiff:
    """Three-way diff result for a single domain.

    Attributes:
        name:     Hostname (identity).
        action:   ``add`` | ``update`` | ``remove`` | ``unchanged``.
        current:  Current API state (``None`` if not present remotely).
        desired:  Desired state from manifest (``None`` if to be removed).
    """

    name: str
    action: str
    current: Domain | None
    desired: Domain | None


def diff_domains(
    current: list[Domain],
    desired: list[Domain],
) -> list[DomainDiff]:
    """Compute a diff between current (API) and desired (manifest) domains.

    Identity: normalized hostname.

    Args:
        current: List of ``Domain`` instances from the live Vercel API.
        desired: List of ``Domain`` instances declared in the manifest.

    Returns:
        List of ``DomainDiff`` instances describing required changes.
    """
    current_map: dict[str, Domain] = {d.identity: d for d in current}
    desired_map: dict[str, Domain] = {d.identity: d for d in desired}

    results: list[DomainDiff] = []

    for name, des in desired_map.items():
        cur = current_map.get(name)
        if cur is None:
            results.append(DomainDiff(name=name, action="add", current=None, desired=des))
        elif _domain_changed(cur, des):
            results.append(DomainDiff(name=name, action="update", current=cur, desired=des))
        else:
            results.append(DomainDiff(name=name, action="unchanged", current=cur, desired=des))

    for name, cur in current_map.items():
        if name not in desired_map:
            results.append(DomainDiff(name=name, action="remove", current=cur, desired=None))

    results.sort(key=lambda d: (d.action, d.name))
    return results


def _domain_changed(current: Domain, desired: Domain) -> bool:
    """Return True if the domain payload differs."""
    if current.redirect != desired.redirect:
        return True
    return current.git_branch != desired.git_branch
