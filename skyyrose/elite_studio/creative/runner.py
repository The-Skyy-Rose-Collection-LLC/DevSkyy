"""
Creative Operations Hub public API.

run_creative() is the single entry point for all creative intents.

"Luxury Grows from Concrete."
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Module-level compiled graph (lazy init, thread-safe after first compile)
_compiled_graph = None


def _get_graph():  # type: ignore[return]
    """Return the compiled creative graph, building it lazily on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        from .router import build_creative_graph
        _compiled_graph = build_creative_graph()
    return _compiled_graph


def run_creative(
    intent: str,
    params: dict,
    sku: str = "",
    tenant_id: str = "",
) -> dict:
    """Run a creative operation end-to-end.

    Args:
        intent: One of the CreativeIntent enum values (e.g. "product-render").
        params: Operation-specific parameters dict.
        sku: Product SKU (optional — required for render/tryon intents).
        tenant_id: Tenant identifier for multi-tenant contexts.

    Returns:
        Final CreativeOperationState dict with all result fields populated.
        Always contains 'status' (success/error) and 'operation_id'.
        On error, also contains 'error' with a description.
    """
    from .state import create_initial_state

    initial_state = create_initial_state(
        intent=intent,
        params=params,
        sku=sku,
        tenant_id=tenant_id,
    )

    try:
        graph = _get_graph()
        final_state = graph.invoke(initial_state)
        return dict(final_state)
    except Exception as exc:
        logger.exception("run_creative failed for intent=%s sku=%s: %s", intent, sku, exc)
        return {
            **dict(initial_state),
            "status": "error",
            "error": f"Graph execution failed: {exc}",
        }
