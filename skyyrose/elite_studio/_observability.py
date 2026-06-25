"""Langfuse observability helper for Elite Studio LangGraph pipelines.

Attaches a langfuse.langchain.CallbackHandler to LangGraph invocations when
Langfuse is installed and credentials are present. No-ops cleanly otherwise.
"""

from __future__ import annotations

from typing import Any


def langfuse_config(base: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a LangGraph ``config`` dict with a Langfuse CallbackHandler attached.

    Merges into ``base`` (preserving existing keys like ``configurable``).
    Silently returns ``base`` unchanged if langfuse is not installed.
    """
    cfg: dict[str, Any] = dict(base) if base else {}
    callbacks = list(cfg.get("callbacks") or [])
    try:
        from langfuse.langchain import CallbackHandler

        callbacks.append(CallbackHandler())
    except ImportError:
        return cfg
    cfg["callbacks"] = callbacks
    return cfg
