"""Vercel REST API backend client.

Auth resolution priority (in order, first wins):
  1. ``--token`` CLI flag  → passed as ``token`` argument
  2. ``VERCEL_TOKEN`` env var
  3. ``~/Library/Application Support/com.vercel.cli/auth.json``  (macOS)
  4. ``~/.local/share/com.vercel.cli/auth.json``  (Linux XDG)
  5. ``~/.config/com.vercel.cli/auth.json``  (Linux alt)
  6. Raises ``VercelAuthError`` with install instructions

Security contract:
  - Token is in-memory only; never logged, never written to disk.
  - ``requests`` calls always specify ``timeout=``.
  - HTTP 429 → exponential backoff, max 3 retries, honors ``Retry-After``.
  - STOP-AND-SHOW gate: all destructive ops must call ``_confirm()`` before
    executing; never default to executing without ``--confirm``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests as requests_lib

# ── Typed exceptions ──────────────────────────────────────────────────


class VercelAuthError(Exception):
    """Raised when no valid Vercel auth token can be found."""


class VercelNotFoundError(Exception):
    """Raised when the Vercel API returns HTTP 404."""

    def __init__(self, msg: str, path: str = "") -> None:
        super().__init__(msg)
        self.path = path


class VercelRateLimitedError(Exception):
    """Raised when the Vercel API returns HTTP 429 after max retries."""

    def __init__(self, msg: str, retry_after: int | None = None) -> None:
        super().__init__(msg)
        self.retry_after = retry_after


class VercelBackendError(Exception):
    """Raised for unexpected HTTP 5xx responses from the Vercel API."""

    def __init__(self, msg: str, status_code: int = 0) -> None:
        super().__init__(msg)
        self.status_code = status_code


class VercelValidationError(Exception):
    """Raised for HTTP 400/422 validation failures."""

    def __init__(self, msg: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(msg)
        self.errors = errors or []


# ── Constants ─────────────────────────────────────────────────────────

_BASE_URL = "https://api.vercel.com"
_DEFAULT_TIMEOUT = 30  # seconds
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds; doubled each retry

_AUTH_JSON_PATHS = [
    # macOS — checked first; Vercel CLI on macOS writes here
    Path.home() / "Library" / "Application Support" / "com.vercel.cli" / "auth.json",
    # Linux XDG
    Path.home() / ".local" / "share" / "com.vercel.cli" / "auth.json",
    # Linux alt config dir
    Path.home() / ".config" / "com.vercel.cli" / "auth.json",
]


# ── Auth resolution ───────────────────────────────────────────────────


def _confirm(action: str, target: str, payload: dict[str, Any] | None = None) -> bool:
    """STOP-AND-SHOW confirmation gate for destructive operations.

    Prints a structured summary of the action, target, and payload, then
    prompts the user for ``y`` / ``yes`` confirmation.  Returns True only
    when the user explicitly confirms.

    Args:
        action:  Human-readable action label (e.g. ``"DELETE env var"``)
        target:  The resource being affected (e.g. ``"DATABASE_URL [production]"``)
        payload: Optional dict of additional details to display.

    Returns:
        True if the user confirmed, False otherwise.
    """
    import sys

    lines = [
        "",
        "  STOP — Confirm before proceeding:",
        "",
        f"  Action : {action}",
        f"  Target : {target}",
    ]
    if payload:
        for k, v in payload.items():
            lines.append(f"  {k:<8}: {v}")
    lines += ["", "  Proceed? [y/N] "]
    sys.stdout.write("\n".join(lines))
    sys.stdout.flush()
    try:
        answer = input("").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


def resolve_token(explicit_token: str | None = None) -> str:
    """Resolve a Vercel bearer token.

    Priority:
      1. ``explicit_token`` argument (from ``--token`` flag)
      2. ``VERCEL_TOKEN`` environment variable
      3. ``~/Library/Application Support/com.vercel.cli/auth.json``  (macOS)
      4. ``~/.local/share/com.vercel.cli/auth.json``  (Linux XDG)
      5. Raises ``VercelAuthError``

    Returns:
        The raw token string (never empty).

    Raises:
        VercelAuthError: If no token can be resolved.
    """
    # 1. Explicit flag
    if explicit_token:
        return explicit_token

    # 2. Environment variable
    env_token = os.environ.get("VERCEL_TOKEN", "").strip()
    if env_token:
        return env_token

    # 3. Vercel CLI auth.json
    for auth_path in _AUTH_JSON_PATHS:
        try:
            raw = auth_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            # Handle {"token":"..."} and nested structures defensively
            if isinstance(data, dict):
                token = data.get("token") or data.get("access_token") or _dig_nested_token(data)
                if token and isinstance(token, str) and token.strip():
                    return token.strip()
        except FileNotFoundError:
            continue
        except (json.JSONDecodeError, OSError):
            continue

    raise VercelAuthError(
        "No Vercel token found.\n\n"
        "Provide a token via one of:\n"
        "  • --token <token>  CLI flag\n"
        "  • VERCEL_TOKEN=<token>  environment variable\n"
        "  • Install the Vercel CLI and run: vercel login\n"
        "    (https://vercel.com/docs/cli)\n"
    )


def _dig_nested_token(data: dict[str, Any]) -> str | None:
    """Search one level deep in a dict for a token value."""
    for v in data.values():
        if isinstance(v, dict):
            token = v.get("token") or v.get("access_token")
            if token and isinstance(token, str):
                return token
    return None


# ── HTTP backend client ───────────────────────────────────────────────


class VercelBackend:
    """Low-level Vercel REST API client.

    Args:
        token: Bearer token string (already resolved by ``resolve_token``).
        team_id: Optional Vercel team ID (``teamId`` query param).
        timeout: HTTP request timeout in seconds.
        _session: Injectable ``requests.Session`` for unit test mocking.
    """

    def __init__(
        self,
        token: str,
        team_id: str | None = None,
        timeout: int = _DEFAULT_TIMEOUT,
        _session: requests_lib.Session | None = None,
    ) -> None:
        self._token = token  # never expose via __repr__ or logs
        self._team_id = team_id
        self._timeout = timeout
        self._session = _session or requests_lib.Session()

    def __repr__(self) -> str:
        return f"VercelBackend(team_id={self._team_id!r}, timeout={self._timeout})"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _base_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self._team_id:
            params["teamId"] = self._team_id
        return params

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute an authenticated request with retry on 429.

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            VercelAuthError: HTTP 401/403.
            VercelNotFoundError: HTTP 404.
            VercelRateLimitedError: HTTP 429 after max retries.
            VercelBackendError: HTTP 5xx.
            VercelValidationError: HTTP 400/422.
        """
        url = f"{_BASE_URL}{path}"
        merged_params: dict[str, Any] = {**self._base_params(), **(params or {})}
        effective_timeout = timeout if timeout is not None else self._timeout

        last_429_after: int | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            resp = self._session.request(
                method=method.upper(),
                url=url,
                headers=self._headers(),
                params=merged_params or None,
                json=json_body,
                timeout=effective_timeout,
            )

            if resp.status_code == 429:
                last_429_after = _parse_retry_after(resp)
                if attempt < _MAX_RETRIES:
                    delay = _retry_delay(attempt, last_429_after)
                    time.sleep(delay)
                    continue
                raise VercelRateLimitedError(
                    f"Rate limited by Vercel API after {_MAX_RETRIES} attempts. "
                    f"Retry-After: {last_429_after}s",
                    retry_after=last_429_after,
                )

            # Non-429 — don't retry
            return _raise_for_status(resp, path)

        # Should never reach here; loop exhausted above
        raise VercelRateLimitedError(
            "Rate limited by Vercel API",
            retry_after=last_429_after,
        )

    # ── Project API ───────────────────────────────────────────────────

    def get_project(self, id_or_name: str) -> dict[str, Any]:
        """GET /v9/projects/{idOrName}"""
        return self._request("GET", f"/v9/projects/{id_or_name}")

    def patch_project(self, id_or_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """PATCH /v9/projects/{idOrName}"""
        return self._request("PATCH", f"/v9/projects/{id_or_name}", json_body=payload)

    # ── Env var API ───────────────────────────────────────────────────

    def list_env_vars(self, id_or_name: str) -> list[dict[str, Any]]:
        """GET /v9/projects/{idOrName}/env — returns all env var records.

        Note: Secret values are masked by the API (``value`` may be empty or
        omitted for sensitive vars). Use ``decrypt_env_var`` to reveal a specific
        var's value (requires the env var ID).
        """
        resp = self._request("GET", f"/v9/projects/{id_or_name}/env")
        return resp.get("envs", [])

    def decrypt_env_var(self, id_or_name: str, env_var_id: str) -> dict[str, Any]:
        """GET /v9/projects/{idOrName}/env/{id} — retrieve decrypted value."""
        return self._request("GET", f"/v9/projects/{id_or_name}/env/{env_var_id}")

    def create_env_var(self, id_or_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v9/projects/{idOrName}/env — create a single env var."""
        return self._request("POST", f"/v9/projects/{id_or_name}/env", json_body=payload)

    def update_env_var(
        self, id_or_name: str, env_var_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """PATCH /v9/projects/{idOrName}/env/{id}"""
        return self._request(
            "PATCH",
            f"/v9/projects/{id_or_name}/env/{env_var_id}",
            json_body=payload,
        )

    def delete_env_var(self, id_or_name: str, env_var_id: str) -> None:
        """DELETE /v9/projects/{idOrName}/env/{id}"""
        self._request("DELETE", f"/v9/projects/{id_or_name}/env/{env_var_id}")

    # ── Domain API ────────────────────────────────────────────────────

    def list_domains(self, id_or_name: str) -> list[dict[str, Any]]:
        """GET /v10/projects/{idOrName}/domains"""
        resp = self._request("GET", f"/v10/projects/{id_or_name}/domains")
        return resp.get("domains", [])

    def add_domain(self, id_or_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /v10/projects/{idOrName}/domains"""
        return self._request("POST", f"/v10/projects/{id_or_name}/domains", json_body=payload)

    def update_domain(
        self, id_or_name: str, domain: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """PATCH /v10/projects/{idOrName}/domains/{domain}"""
        return self._request(
            "PATCH",
            f"/v10/projects/{id_or_name}/domains/{domain}",
            json_body=payload,
        )

    def remove_domain(self, id_or_name: str, domain: str) -> None:
        """DELETE /v10/projects/{idOrName}/domains/{domain}"""
        self._request("DELETE", f"/v10/projects/{id_or_name}/domains/{domain}")

    # ── Deployment API ────────────────────────────────────────────────

    def list_deployments(
        self,
        project_id: str | None = None,
        limit: int = 20,
        extra_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """GET /v6/deployments"""
        params: dict[str, Any] = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        if extra_params:
            params.update(extra_params)
        resp = self._request("GET", "/v6/deployments", params=params)
        return resp.get("deployments", [])

    def get_deployment_events(self, deployment_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """GET /v3/deployments/{id}/events"""
        params = {"limit": limit}
        resp = self._request("GET", f"/v3/deployments/{deployment_id}/events", params=params)
        # Events may be returned as a list directly or under a key
        if isinstance(resp, list):
            return resp
        return resp.get("events", [])

    # ── Integration API ───────────────────────────────────────────────

    def list_integrations(self) -> list[dict[str, Any]]:
        """GET /v1/integrations/configurations"""
        resp = self._request("GET", "/v1/integrations/configurations")
        return resp.get("configurations", [])


# ── Internal helpers ──────────────────────────────────────────────────


def _parse_retry_after(resp: requests_lib.Response) -> int | None:
    """Parse Retry-After header; return seconds as int or None."""
    header = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    if header is None:
        return None
    try:
        return int(header)
    except (ValueError, TypeError):
        return None


def _retry_delay(attempt: int, retry_after: int | None) -> float:
    """Compute sleep duration for attempt N (1-indexed)."""
    if retry_after is not None:
        return float(retry_after)
    return _RETRY_BASE_DELAY * (2 ** (attempt - 1))


def _raise_for_status(resp: requests_lib.Response, path: str) -> dict[str, Any]:
    """Parse response or raise a typed exception."""
    if resp.status_code in (200, 201, 204):
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # Try to parse error body
    error_body: dict[str, Any] = {}
    try:
        error_body = resp.json()
    except Exception:
        pass

    err_msg = _extract_error_message(error_body, resp.status_code, path)
    errors = error_body.get("errors", [])

    if resp.status_code in (401, 403):
        raise VercelAuthError(f"Authentication failed ({resp.status_code}): {err_msg}")
    if resp.status_code == 404:
        raise VercelNotFoundError(err_msg, path=path)
    if resp.status_code in (400, 422):
        raise VercelValidationError(err_msg, errors=errors)
    if resp.status_code >= 500:
        raise VercelBackendError(err_msg, status_code=resp.status_code)

    # Unexpected 2xx variant or unhandled 4xx
    raise VercelBackendError(
        f"Unexpected status {resp.status_code}: {err_msg}",
        status_code=resp.status_code,
    )


def _extract_error_message(body: dict[str, Any], status_code: int, path: str) -> str:
    """Extract a human-readable message from a Vercel error response."""
    if body.get("error", {}).get("message"):
        return body["error"]["message"]
    if body.get("message"):
        return body["message"]
    return f"HTTP {status_code} from {path}"
