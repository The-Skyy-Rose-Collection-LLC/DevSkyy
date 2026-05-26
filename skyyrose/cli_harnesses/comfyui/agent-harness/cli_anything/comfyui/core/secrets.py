"""ComfyUI credential resolution.

Priority chain for host:
  1. explicit --host CLI flag  (caller passes override)
  2. COMFYUI_HOST env var
  3. default http://127.0.0.1:8188

Optional bearer token:
  1. explicit --token CLI flag (caller passes override)
  2. COMFYUI_AUTH_TOKEN env var
  3. None (unauthenticated)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_HOST = "http://127.0.0.1:8188"


@dataclass(frozen=True)
class ComfyUISecrets:
    """Resolved connection credentials for a ComfyUI instance."""

    host: str
    token: str | None

    @property
    def base_url(self) -> str:
        return self.host.rstrip("/")

    def auth_headers(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


def resolve_secrets(
    host_override: str | None = None,
    token_override: str | None = None,
) -> ComfyUISecrets:
    """Return resolved :class:`ComfyUISecrets` using the priority chain."""
    host = host_override or os.environ.get("COMFYUI_HOST") or _DEFAULT_HOST
    token = token_override or os.environ.get("COMFYUI_AUTH_TOKEN") or None
    return ComfyUISecrets(host=host.rstrip("/"), token=token)
