"""ComfyUI REST backend client.

Covers every endpoint in the ComfyUI HTTP API:
  GET  /system_stats
  GET  /object_info
  GET  /object_info/{node_class}
  GET  /history
  GET  /history/{prompt_id}
  POST /history          (clear — body: {"clear": true} or {"delete": [id, ...]})
  GET  /prompt           (queue + exec info)
  POST /prompt           (submit workflow)
  GET  /queue
  POST /queue            (clear pending — body: {"clear": true})
  POST /interrupt
  GET  /view             (download output file)
  GET  /embeddings
  GET  /models/{model_type}

Retry policy: 429 responses are retried up to _MAX_RETRIES times with
exponential backoff, honouring the Retry-After header when present.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Typed exception hierarchy
# ---------------------------------------------------------------------------


class ComfyUIBackendError(Exception):
    """Base class for all ComfyUI backend errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ComfyUIAuthError(ComfyUIBackendError):
    """HTTP 401 or 403 from ComfyUI."""


class ComfyUINotFoundError(ComfyUIBackendError):
    """HTTP 404 — resource not found."""


class ComfyUIValidationError(ComfyUIBackendError):
    """HTTP 422 — invalid request payload."""


class ComfyUIRateLimitError(ComfyUIBackendError):
    """HTTP 429 — rate limited (after exhausting retries)."""


class ComfyUIServerError(ComfyUIBackendError):
    """HTTP 5xx — server-side error."""


# ---------------------------------------------------------------------------
# Retry config
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BASE_BACKOFF = 1.0  # seconds


def _backoff(attempt: int) -> float:
    return _BASE_BACKOFF * (2**attempt)


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class ComfyUIBackend:
    """Thin httpx-based client for the ComfyUI REST API.

    Args:
        base_url: ComfyUI server URL (e.g. ``"http://127.0.0.1:8188"``).
        auth_headers: Optional dict of extra headers (e.g. Bearer token).
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        auth_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._auth = auth_headers or {}
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {**self._auth}
        if extra:
            h.update(extra)
        return h

    def _translate_status(self, response: httpx.Response) -> None:
        """Raise a typed exception for non-2xx responses."""
        code = response.status_code
        if code < 400:
            return
        text = response.text[:200]
        if code in (401, 403):
            raise ComfyUIAuthError(f"HTTP {code}: {text}", status_code=code)
        if code == 404:
            raise ComfyUINotFoundError(f"HTTP 404: {text}", status_code=404)
        if code == 422:
            raise ComfyUIValidationError(f"HTTP 422: {text}", status_code=422)
        if code == 429:
            raise ComfyUIRateLimitError(f"HTTP 429: {text}", status_code=429)
        if code >= 500:
            raise ComfyUIServerError(f"HTTP {code}: {text}", status_code=code)
        raise ComfyUIBackendError(f"HTTP {code}: {text}", status_code=code)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Any = None) -> httpx.Response:
        return self._request("POST", path, json=json)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> httpx.Response:
        url = self._url(path)
        headers = self._headers({"Content-Type": "application/json"} if json is not None else None)
        last_exc: ComfyUIRateLimitError | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = httpx.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=self._timeout,
                )
            except httpx.RequestError as exc:
                raise ComfyUIBackendError(f"Connection error: {exc}") from exc

            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                retry_after = float(resp.headers.get("Retry-After", _backoff(attempt)))
                time.sleep(retry_after)
                last_exc = ComfyUIRateLimitError(
                    f"HTTP 429 (retry {attempt + 1}/{_MAX_RETRIES})", status_code=429
                )
                continue

            self._translate_status(resp)
            return resp

        raise last_exc or ComfyUIRateLimitError("Rate limit exceeded", status_code=429)

    # ------------------------------------------------------------------
    # System / server info
    # ------------------------------------------------------------------

    def system_stats(self) -> dict[str, Any]:
        """GET /system_stats — CPU, RAM, VRAM usage."""
        return self._get("/system_stats").json()

    def embeddings(self) -> list[str]:
        """GET /embeddings — list of embedding model names."""
        return self._get("/embeddings").json()

    # ------------------------------------------------------------------
    # Object info / node registry
    # ------------------------------------------------------------------

    def object_info(self) -> dict[str, Any]:
        """GET /object_info — full node registry."""
        return self._get("/object_info").json()

    def object_info_node(self, node_class: str) -> dict[str, Any]:
        """GET /object_info/{node_class} — single node spec."""
        return self._get(f"/object_info/{node_class}").json()

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def history(self, max_items: int | None = None) -> dict[str, Any]:
        """GET /history — all completed prompts."""
        params = {"max_items": max_items} if max_items is not None else None
        return self._get("/history", params=params).json()

    def history_prompt(self, prompt_id: str) -> dict[str, Any]:
        """GET /history/{prompt_id} — single prompt history entry."""
        return self._get(f"/history/{prompt_id}").json()

    def clear_history(self, prompt_id: str | None = None) -> dict[str, Any]:
        """POST /history — clear all history or a specific prompt.

        ComfyUI uses POST with ``{"clear": true}`` for full clear or
        ``{"delete": [prompt_id]}`` to remove a specific entry.
        """
        if prompt_id:
            body: dict[str, Any] = {"delete": [prompt_id]}
        else:
            body = {"clear": True}
        return self._post("/history", json=body).json()

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------

    def queue(self) -> dict[str, Any]:
        """GET /queue — running + pending queue items."""
        return self._get("/queue").json()

    def queue_clear(self) -> dict[str, Any]:
        """POST /queue with body ``{"clear": true}`` — clear pending queue."""
        return self._post("/queue", json={"clear": True}).json()

    # ------------------------------------------------------------------
    # Prompt submission
    # ------------------------------------------------------------------

    def prompt_status(self) -> dict[str, Any]:
        """GET /prompt — current execution state and queue info."""
        return self._get("/prompt").json()

    def submit_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /prompt — submit a workflow for execution.

        Args:
            payload: Dict with keys ``"prompt"`` (workflow), ``"client_id"``,
                and optionally ``"extra_data"``.

        Returns:
            Response dict containing ``"prompt_id"``, ``"number"``,
            and ``"node_errors"``.
        """
        return self._post("/prompt", json=payload).json()

    # ------------------------------------------------------------------
    # Interrupt
    # ------------------------------------------------------------------

    def interrupt(self) -> dict[str, Any]:
        """POST /interrupt — stop the currently running prompt."""
        return self._post("/interrupt").json()

    # ------------------------------------------------------------------
    # File download
    # ------------------------------------------------------------------

    def view(
        self,
        filename: str,
        subfolder: str = "",
        file_type: str = "output",
    ) -> bytes:
        """GET /view — download an output file as raw bytes.

        Args:
            filename: File name (e.g. ``"ComfyUI_00001_.png"``).
            subfolder: Subfolder within the output directory.
            file_type: One of ``"output"``, ``"input"``, ``"temp"``.

        Returns:
            Raw bytes of the file content.
        """
        params: dict[str, Any] = {"filename": filename, "type": file_type}
        if subfolder:
            params["subfolder"] = subfolder
        return self._get("/view", params=params).content

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def models(self, model_type: str) -> list[str]:
        """GET /models/{model_type} — list models of a given type.

        Common types: ``"checkpoints"``, ``"loras"``, ``"vae"``,
        ``"controlnet"``, ``"embeddings"``, ``"hypernetworks"``,
        ``"upscale_models"``.
        """
        return self._get(f"/models/{model_type}").json()
