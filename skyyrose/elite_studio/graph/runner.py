"""
Graph runner — public API for invoking the Elite Studio pipeline.

``run_single`` and ``run_batch`` are drop-in replacements for
``Coordinator.produce`` and ``Coordinator.produce_batch``.

The graph is compiled once per call to avoid redundant compilation;
for high-throughput use pass a pre-compiled graph via the ``graph``
parameter.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

from ..config import BATCH_DELAY_SECONDS, OUTPUT_DIR
from ..models import ProductionResult
from ..utils import discover_all_skus
from .builder import GraphConfig, build_graph
from .state import create_initial_state, extract_production_result


def run_single(
    sku: str,
    view: str = "front",
    style: str = "flat_lay",
    config: GraphConfig | None = None,
    graph: Any = None,
) -> ProductionResult:
    """Run the graph pipeline for a single SKU.

    Args:
        sku: Product SKU (e.g. "br-001").
        view: Image view angle — "front" or "back".
        style: Photography style — "flat_lay" or "ghost_mannequin".
        config: Graph configuration. Uses defaults if None.
        graph: Pre-compiled graph. Built from config if None.

    Returns:
        ProductionResult matching the schema returned by Coordinator.produce().
    """
    if config is None:
        config = GraphConfig()
    if graph is None:
        graph = build_graph(config)

    state = create_initial_state(
        sku=sku,
        view=view,
        style=style,
        enable_compositor=config.enable_compositor,
        enable_tryon=config.enable_tryon,
        tryon_category=config.tryon_category,
        max_retries=config.max_retries,
    )

    final_state = graph.invoke(state)
    return extract_production_result(final_state)


def run_batch(
    skus: list[str] | None = None,
    view: str = "front",
    style: str = "flat_lay",
    config: GraphConfig | None = None,
    skip_existing: bool = True,
    graph: Any = None,
) -> list[ProductionResult]:
    """Run the graph pipeline for multiple SKUs.

    Args:
        skus: List of SKUs to process. Discovers all SKUs if None.
        view: Image view angle — "front" or "back".
        style: Photography style — "flat_lay" or "ghost_mannequin".
        config: Graph configuration. Uses defaults if None.
        skip_existing: Skip SKUs that already have generated output.
        graph: Pre-compiled graph. Built from config if None.

    Returns:
        List of ProductionResult, one per SKU (including skipped ones).
    """
    if config is None:
        config = GraphConfig()
    if skus is None:
        skus = discover_all_skus()

    # Compile once and reuse across all SKUs
    if graph is None:
        graph = build_graph(config)

    results: list[ProductionResult] = []
    for i, sku in enumerate(skus):
        if skip_existing:
            expected = OUTPUT_DIR / sku / f"{sku}-model-{view}-gemini.jpg"
            if expected.exists():
                results.append(
                    ProductionResult(
                        sku=sku,
                        view=view,
                        status="skipped",
                        output_path=str(expected),
                        vision=None,
                        generation=None,
                        quality=None,
                        compositing=None,
                        error="",
                        step="",
                    )
                )
                continue

        try:
            result = run_single(sku=sku, view=view, style=style, config=config, graph=graph)
        except Exception as exc:
            # Isolate failures so a single bad SKU cannot abort the whole batch.
            logger.exception("run_single failed for sku=%s view=%s: %s", sku, view, exc)
            result = ProductionResult(
                sku=sku,
                view=view,
                status="failed",
                output_path="",
                vision=None,
                generation=None,
                quality=None,
                compositing=None,
                error=str(exc),
                step="runner",
            )
        results.append(result)

        # Respect batch delay between items (not after last)
        if i < len(skus) - 1:
            time.sleep(BATCH_DELAY_SECONDS)

    return results
