"""
SpaceRef — canonical reference to a HuggingFace Space.

Accepts owner/name slugs or full HF URLs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Matches: https://huggingface.co/spaces/owner/name
_HF_URL_RE = re.compile(r"^https?://huggingface\.co/spaces/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$")

# Matches: owner/name
_SLUG_RE = re.compile(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$")


@dataclass(frozen=True)
class SpaceRef:
    """Immutable reference to a HuggingFace Space."""

    owner: str
    name: str

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, value: str) -> "SpaceRef":
        """
        Parse owner/name from a slug or a full HuggingFace Spaces URL.

        Accepted forms:
          - ``owner/name``
          - ``https://huggingface.co/spaces/owner/name``
          - ``https://huggingface.co/spaces/owner/name/``

        Raises:
            ValueError: if the string cannot be parsed.
        """
        value = value.strip()

        m = _HF_URL_RE.match(value)
        if m:
            return cls(owner=m.group(1), name=m.group(2))

        m = _SLUG_RE.match(value)
        if m:
            return cls(owner=m.group(1), name=m.group(2))

        raise ValueError(
            f"Cannot parse Space reference '{value}'. "
            "Expected 'owner/name' or 'https://huggingface.co/spaces/owner/name'."
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def repo_id(self) -> str:
        """Return the canonical ``owner/name`` repo_id used by HfApi."""
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        """Return the canonical HuggingFace Spaces URL."""
        return f"https://huggingface.co/spaces/{self.owner}/{self.name}"

    @property
    def embed_url(self) -> str:
        """Return the embed URL for the Space."""
        return f"https://{self.owner}-{self.name}.hf.space"

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {"owner": self.owner, "name": self.name, "repo_id": self.repo_id}

    @classmethod
    def from_dict(cls, data: dict) -> "SpaceRef":
        """Reconstruct from a dict produced by ``to_dict``."""
        if "owner" in data and "name" in data:
            return cls(owner=data["owner"], name=data["name"])
        if "repo_id" in data:
            return cls.parse(data["repo_id"])
        raise ValueError(f"Cannot reconstruct SpaceRef from dict: {data!r}")

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self.repo_id

    def __repr__(self) -> str:
        return f"SpaceRef(owner={self.owner!r}, name={self.name!r})"


def parse_space_ref(value: str) -> SpaceRef:
    """Module-level convenience wrapper around ``SpaceRef.parse``."""
    return SpaceRef.parse(value)


def optional_space_ref(value: Optional[str]) -> Optional[SpaceRef]:
    """Return ``SpaceRef.parse(value)`` or ``None`` if *value* is falsy."""
    if not value:
        return None
    return SpaceRef.parse(value)
