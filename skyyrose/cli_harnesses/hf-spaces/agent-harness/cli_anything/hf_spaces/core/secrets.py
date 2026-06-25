"""
Dataclasses for Space secrets and variables.

Secrets: write-only via HfApi. Names tracked in local manifest only.
Variables: readable via get_space_variables(), stored as key/value pairs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SecretEntry:
    """
    Represents a secret key tracked in the local manifest.

    The *value* is NEVER stored to disk.  It is held in-memory only during
    the apply cycle and discarded immediately after the HfApi call returns.
    """

    key: str
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialise to manifest-safe dict (no value field)."""
        d: dict = {"key": self.key}
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "SecretEntry":
        if isinstance(data, str):
            # Accept bare string as key shorthand
            return cls(key=data)
        return cls(
            key=data["key"],
            description=data.get("description"),
        )

    def __str__(self) -> str:
        return self.key


@dataclass
class VariableEntry:
    """
    Represents a Space environment variable (non-secret).

    Values ARE readable via HfApi.get_space_variables() and are stored
    in the manifest.
    """

    key: str
    value: str
    description: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"key": self.key, "value": self.value}
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "VariableEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            description=data.get("description"),
        )

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


@dataclass
class SecretsBundle:
    """
    Holds both secrets (name-only) and variables (name+value) for a Space.
    """

    secrets: List[SecretEntry] = field(default_factory=list)
    variables: List[VariableEntry] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def get_variable(self, key: str) -> Optional[VariableEntry]:
        for v in self.variables:
            if v.key == key:
                return v
        return None

    def has_secret(self, key: str) -> bool:
        return any(s.key == key for s in self.secrets)

    # ------------------------------------------------------------------
    # Dict helpers from HfApi response format
    # ------------------------------------------------------------------

    @classmethod
    def variables_from_api(cls, api_response: Dict[str, dict]) -> List[VariableEntry]:
        """
        Convert the dict returned by ``HfApi.get_space_variables`` to a list
        of ``VariableEntry``.

        HfApi response shape: ``{"KEY": {"value": "...", "description": "..."}}``
        """
        entries = []
        for key, meta in api_response.items():
            entries.append(
                VariableEntry(
                    key=key,
                    value=meta.get("value", ""),
                    description=meta.get("description"),
                )
            )
        return entries

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "secrets": [s.to_dict() for s in self.secrets],
            "variables": [v.to_dict() for v in self.variables],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SecretsBundle":
        secrets = [SecretEntry.from_dict(s) for s in data.get("secrets", [])]
        variables = [VariableEntry.from_dict(v) for v in data.get("variables", [])]
        return cls(secrets=secrets, variables=variables)
