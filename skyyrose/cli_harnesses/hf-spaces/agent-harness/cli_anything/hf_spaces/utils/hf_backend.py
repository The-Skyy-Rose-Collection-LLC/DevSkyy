"""
HfApi wrapper for cli-anything-hf-spaces.

Provides:
- Auth resolution (--token > HF_TOKEN > ~/.cache/huggingface/token)
- Typed exceptions for common HF API errors
- Thin wrappers around HfApi methods with consistent error handling
- Raw httpx SSE log streaming (logs run/build — bypasses HfApi public surface)

Token is NEVER written to disk by this module.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional

# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class HfBackendError(Exception):
    """Base class for all HF backend errors."""


class HfAuthError(HfBackendError):
    """Raised when authentication fails or no token is available."""


class HfSpaceNotFoundError(HfBackendError):
    """Raised when the requested Space does not exist or is not accessible."""


class HfHardwareError(HfBackendError):
    """Raised when a hardware tier change fails."""


class HfRateLimitError(HfBackendError):
    """Raised when the HF API rate limit is exceeded."""


class HfLogsUnavailableError(HfBackendError):
    """Raised when log streaming is not available (httpx missing or API error)."""


# ---------------------------------------------------------------------------
# Auth resolution
# ---------------------------------------------------------------------------

_HF_TOKEN_CACHE = Path.home() / ".cache" / "huggingface" / "token"


def resolve_token(token: Optional[str] = None) -> Optional[str]:
    """
    Resolve a HuggingFace token in priority order:
      1. Explicit *token* argument (in-memory, never written to disk)
      2. ``HF_TOKEN`` environment variable
      3. ``~/.cache/huggingface/token`` (written by ``huggingface-cli login``)
      4. ``None`` (unauthenticated — public spaces only)

    The returned token is never written to disk by this function.
    """
    if token:
        return token
    env_token = os.environ.get("HF_TOKEN", "").strip()
    if env_token:
        return env_token
    if _HF_TOKEN_CACHE.exists():
        cached = _HF_TOKEN_CACHE.read_text(encoding="utf-8").strip()
        if cached:
            return cached
    return None


def require_token(token: Optional[str] = None) -> str:
    """
    Like ``resolve_token`` but raises ``HfAuthError`` if no token is found.
    """
    resolved = resolve_token(token)
    if not resolved:
        raise HfAuthError(
            "No HuggingFace token found. Provide via:\n"
            "  --token <token>\n"
            "  HF_TOKEN env var\n"
            "  huggingface-cli login"
        )
    return resolved


# ---------------------------------------------------------------------------
# HfApi factory
# ---------------------------------------------------------------------------


def _get_api(token: Optional[str] = None):
    """
    Return an authenticated HfApi instance.

    Raises:
        ImportError: if huggingface_hub is not installed.
    """
    try:
        from huggingface_hub import HfApi  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "huggingface_hub is required. Install with:\n  pip install 'cli-anything-hf-spaces[hf]'"
        ) from exc
    return HfApi(token=token)


# ---------------------------------------------------------------------------
# Space info
# ---------------------------------------------------------------------------


def get_space_info(repo_id: str, token: Optional[str] = None) -> Any:
    """
    Return SpaceInfo for *repo_id*.

    Raises:
        HfSpaceNotFoundError: if the Space does not exist.
        HfAuthError: on 401/403.
    """
    api = _get_api(token)
    try:
        return api.space_info(repo_id=repo_id, token=token)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def get_space_runtime(repo_id: str, token: Optional[str] = None) -> Any:
    """Return the SpaceRuntime for *repo_id*."""
    api = _get_api(token)
    try:
        return api.get_space_runtime(repo_id=repo_id, token=token)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def list_spaces(
    author: Optional[str] = None,
    search: Optional[str] = None,
    token: Optional[str] = None,
    limit: int = 50,
) -> List[Any]:
    """
    List spaces, optionally filtered by *author* and/or *search* query.

    Returns a list (materialised from the HfApi generator).
    """
    api = _get_api(token)
    try:
        gen = api.list_spaces(author=author, search=search, token=token, limit=limit)
        return list(gen)
    except Exception as exc:
        _translate_exc(exc)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def pause_space(repo_id: str, token: Optional[str] = None) -> None:
    """Pause a Space (sets stage → PAUSED)."""
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.pause_space(repo_id=repo_id, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def restart_space(repo_id: str, token: Optional[str] = None) -> None:
    """Warm-restart a Space."""
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.restart_space(repo_id=repo_id, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------


def get_hardware(repo_id: str, token: Optional[str] = None) -> Optional[str]:
    """
    Return the current hardware slug for *repo_id*, or None if unknown.
    """
    api = _get_api(token)
    try:
        runtime = api.get_space_runtime(repo_id=repo_id, token=token)
        hw = getattr(runtime, "hardware", None)
        if hw is None:
            return None
        # SpaceHardware enum — return .value (the slug string)
        return str(hw.value) if hasattr(hw, "value") else str(hw)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def set_hardware(
    repo_id: str,
    hardware_slug: str,
    token: Optional[str] = None,
) -> None:
    """
    Request a hardware tier change for *repo_id*.

    *hardware_slug* must be a valid ``SpaceHardware`` value.
    This is a destructive/billing operation — callers must STOP-AND-SHOW before invoking.
    """
    from cli_anything.hf_spaces.core.hardware import hardware_to_sdk_enum

    tok = require_token(token)
    api = _get_api(tok)
    hw_enum = hardware_to_sdk_enum(hardware_slug)
    try:
        api.request_space_hardware(repo_id=repo_id, hardware=hw_enum, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def set_sleep_time(
    repo_id: str,
    sleep_time: int,
    token: Optional[str] = None,
) -> None:
    """Set the sleep time for *repo_id* in seconds (-1 = never sleep)."""
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.set_space_sleep_time(repo_id=repo_id, sleep_time=sleep_time, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


# ---------------------------------------------------------------------------
# Secrets (write-only)
# ---------------------------------------------------------------------------


def set_secret(
    repo_id: str,
    key: str,
    value: str,
    token: Optional[str] = None,
) -> None:
    """
    Write a secret to the Space.

    The *value* is sent directly to HfApi and is never written to disk.
    """
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.add_space_secret(repo_id=repo_id, key=key, value=value, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def delete_secret(
    repo_id: str,
    key: str,
    token: Optional[str] = None,
) -> None:
    """
    Delete a secret from the Space.

    Destructive — callers must STOP-AND-SHOW before invoking.
    """
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.delete_space_secret(repo_id=repo_id, key=key, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


# ---------------------------------------------------------------------------
# Variables (readable)
# ---------------------------------------------------------------------------


def get_variables(
    repo_id: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return the variables dict for *repo_id*.

    Shape: ``{"KEY": {"value": "...", "description": "..."}}``
    """
    api = _get_api(token)
    try:
        return api.get_space_variables(repo_id=repo_id, token=token)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def set_variable(
    repo_id: str,
    key: str,
    value: str,
    token: Optional[str] = None,
) -> None:
    """Set or update a Space environment variable."""
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.add_space_variable(repo_id=repo_id, key=key, value=value, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


def delete_variable(
    repo_id: str,
    key: str,
    token: Optional[str] = None,
) -> None:
    """Delete a Space environment variable."""
    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.delete_space_variable(repo_id=repo_id, key=key, token=tok)
    except Exception as exc:
        _translate_exc(exc, repo_id)


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------


def get_readme(repo_id: str, token: Optional[str] = None) -> Optional[str]:
    """
    Fetch the raw content of README.md from the Space repo.

    Returns None if the file does not exist.
    """
    try:
        import tempfile

        from huggingface_hub import \
            hf_hub_download  # type: ignore[import-untyped]

        path = hf_hub_download(
            repo_id=repo_id,
            filename="README.md",
            repo_type="space",
            token=token,
        )
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return None


def upload_readme(
    repo_id: str,
    content: str,
    token: Optional[str] = None,
    commit_message: str = "Update README.md via cli-anything-hf-spaces",
) -> None:
    """
    Upload README.md content to the Space repo.

    Uses ``HfApi.upload_file`` — ``Repository`` class is deprecated and not used.
    """
    import io

    tok = require_token(token)
    api = _get_api(tok)
    try:
        api.upload_file(
            path_or_fileobj=io.BytesIO(content.encode("utf-8")),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="space",
            token=tok,
            commit_message=commit_message,
        )
    except Exception as exc:
        _translate_exc(exc, repo_id)


# ---------------------------------------------------------------------------
# Space duplication
# ---------------------------------------------------------------------------


def duplicate_space(
    from_id: str,
    to_id: str,
    private: bool = True,
    exist_ok: bool = False,
    token: Optional[str] = None,
) -> Any:
    """
    Duplicate a Space from *from_id* to *to_id*.

    Returns the new SpaceInfo.
    """
    tok = require_token(token)
    api = _get_api(tok)
    try:
        return api.duplicate_space(
            from_id=from_id,
            to_id=to_id,
            private=private,
            exist_ok=exist_ok,
            token=tok,
        )
    except Exception as exc:
        _translate_exc(exc, from_id)


# ---------------------------------------------------------------------------
# Log streaming (bypasses HfApi — raw httpx SSE)
# ---------------------------------------------------------------------------

_HF_LOGS_RUN_URL = "https://huggingface.co/api/spaces/{owner}/{name}/logs/run"
_HF_LOGS_BUILD_URL = "https://huggingface.co/api/spaces/{owner}/{name}/logs/build"


def stream_logs(
    owner: str,
    name: str,
    log_type: str = "run",
    token: Optional[str] = None,
    max_lines: int = 200,
) -> Generator[str, None, None]:
    """
    Stream Space logs via the HuggingFace SSE log endpoint.

    NOTE: This bypasses the public HfApi surface and calls the raw REST
    endpoint directly, as HfApi does not expose a log-streaming method.

    Args:
        owner: Space owner (user or org).
        name: Space name.
        log_type: ``"run"`` or ``"build"``.
        token: Auth token (required for private spaces).
        max_lines: Stop after this many log lines.

    Yields:
        Log line strings (text/event-stream ``data:`` payloads, decoded).

    Raises:
        HfLogsUnavailableError: if httpx is not installed or the endpoint
            returns a non-200 status.
    """
    try:
        import httpx
    except ImportError as exc:
        raise HfLogsUnavailableError(
            "httpx is required for log streaming. Install with:\n"
            "  pip install 'cli-anything-hf-spaces[logs]'"
        ) from exc

    if log_type == "build":
        url = _HF_LOGS_BUILD_URL.format(owner=owner, name=name)
    else:
        url = _HF_LOGS_RUN_URL.format(owner=owner, name=name)

    headers: Dict[str, str] = {"Accept": "text/event-stream"}
    resolved = resolve_token(token)
    if resolved:
        headers["Authorization"] = f"Bearer {resolved}"

    count = 0
    try:
        with httpx.stream("GET", url, headers=headers, timeout=30.0) as resp:
            if resp.status_code == 401:
                raise HfLogsUnavailableError(
                    "Authentication required for log streaming. Provide a token via "
                    "--token or HF_TOKEN."
                )
            if resp.status_code == 404:
                raise HfLogsUnavailableError(
                    f"Space not found or logs endpoint unavailable: {owner}/{name}"
                )
            if resp.status_code != 200:
                raise HfLogsUnavailableError(
                    f"Log endpoint returned HTTP {resp.status_code} for {owner}/{name}"
                )
            for line in resp.iter_lines():
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload and payload != "[DONE]":
                        yield payload
                        count += 1
                        if count >= max_lines:
                            return
    except HfLogsUnavailableError:
        raise
    except Exception as exc:
        raise HfLogsUnavailableError(f"Log streaming failed for {owner}/{name}: {exc}") from exc


# ---------------------------------------------------------------------------
# Exception translation
# ---------------------------------------------------------------------------


def _translate_exc(exc: Exception, repo_id: Optional[str] = None) -> None:
    """
    Convert huggingface_hub exceptions to typed HfBackendError subclasses.

    Always re-raises — never returns normally.
    """
    msg = str(exc)
    lower = msg.lower()

    # Try to classify by message content (hub exceptions vary by version)
    if "401" in msg or "unauthorized" in lower or "invalid token" in lower:
        raise HfAuthError(f"Authentication failed. Check your token. ({msg})") from exc
    if "403" in msg or "forbidden" in lower:
        raise HfAuthError(f"Access forbidden for {repo_id or 'resource'}. ({msg})") from exc
    if "404" in msg or "not found" in lower or "repository not found" in lower:
        label = f" '{repo_id}'" if repo_id else ""
        raise HfSpaceNotFoundError(f"Space{label} not found or not accessible. ({msg})") from exc
    if "429" in msg or "rate limit" in lower:
        raise HfRateLimitError(
            f"HuggingFace API rate limit exceeded. Retry after a moment. ({msg})"
        ) from exc
    # Default: re-wrap as HfBackendError
    raise HfBackendError(f"HuggingFace API error: {msg}") from exc
