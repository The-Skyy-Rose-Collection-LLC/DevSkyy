"""
Brand Integration Layer
========================

Wires the autonomous brand learning loop into the agent ecosystem.

This module connects:
    - BrandLearningLoop ↔ EventBus (auto-observe domain events)
    - BrandLearningLoop ↔ BrandContextInjector (adaptive brand DNA)
    - BrandLearningLoop ↔ FeedbackTracker (import LLM quality signals)
    - BrandLearningLoop ↔ SocialMediaSubAgent (engagement → insights)
    - BrandLearningLoop ↔ Orchestrator (brand health in routing decisions)

Usage:
    from orchestration.brand_integration import wire_brand_learning

    # During app startup (main_enterprise.py)
    loop = wire_brand_learning()

    # Or with explicit dependencies
    loop = wire_brand_learning(
        event_bus=event_bus,
        signal_threshold=15,
    )

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def wire_brand_learning(
    *,
    event_bus: Any | None = None,
    signal_threshold: int = 10,
    lookback_hours: int = 168,
) -> Any:
    """
    Create and wire the brand learning loop into the platform.

    Connects:
    1. EventBus → Loop (auto-observe ContentGenerated, etc.)
    2. SKYYROSE_BRAND dict → Loop (live brand context mutation)
    3. FeedbackTracker → Loop (import existing LLM quality data)

    Args:
        event_bus: Override event bus instance (default: core singleton)
        signal_threshold: Signals before auto-triggering learning cycle
        lookback_hours: Analysis window (default: 7 days)

    Returns:
        Configured BrandLearningLoop instance
    """
    from orchestration.brand_context import SKYYROSE_BRAND
    from orchestration.brand_learning import BrandLearningLoop

    loop = BrandLearningLoop(
        signal_threshold=signal_threshold,
        lookback_hours=lookback_hours,
    )

    # 1. Connect to live brand dict
    connect_kwargs: dict[str, Any] = {"brand_dict": SKYYROSE_BRAND}

    # 2. Connect to event bus
    if event_bus is None:
        try:
            from core.events import event_bus as default_bus

            connect_kwargs["event_bus"] = default_bus
        except ImportError:
            logger.info("[brand_integration] Event bus unavailable, running without auto-observe")
    else:
        connect_kwargs["event_bus"] = event_bus

    loop.connect(**connect_kwargs)

    # 3. Import signals from feedback tracker (if data exists)
    _import_feedback_tracker_signals(loop)

    logger.info(
        "[brand_integration] Brand learning loop wired (threshold=%d, lookback=%dh)",
        signal_threshold,
        lookback_hours,
    )

    return loop


def _import_feedback_tracker_signals(loop: Any) -> int:
    """
    Import existing LLM quality data from FeedbackTracker into the learning loop.

    This seeds the loop with historical data so it doesn't start from zero.
    Only runs once (checks if signals already exist).

    Returns:
        Number of signals imported
    """
    from orchestration.brand_learning import BrandSignal, SignalType

    # Skip if loop already has data
    if loop._memory.count_signals() > 0:
        return 0

    try:
        from orchestration.feedback_tracker import FeedbackTracker

        tracker = FeedbackTracker()
    except Exception:
        logger.debug("[brand_integration] FeedbackTracker unavailable, skipping import")
        return 0

    imported = 0
    try:
        import sqlite3

        with sqlite3.connect(tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM response_metrics ORDER BY created_at DESC LIMIT 500"
            ).fetchall()

        for row in rows:
            accepted_raw = row["user_accepted"]
            accepted = True if accepted_raw == 1 else (False if accepted_raw == 0 else None)

            # Map task types to signal types
            task_type = row["task_type"] or "general"
            signal_type_map = {
                "product_description": SignalType.PRODUCT_DESCRIPTION,
                "marketing_copy": SignalType.MARKETING_COPY,
                "social_media": SignalType.SOCIAL_POST,
                "visual_generation": SignalType.VISUAL_ASSET,
            }
            signal_type = signal_type_map.get(task_type, SignalType.CONTENT_GENERATED)

            loop.observe(
                BrandSignal(
                    signal_type=signal_type,
                    provider=row["provider"] or "",
                    model=row["model"] or "",
                    accepted=accepted,
                    quality_score=row["quality_score"] or 0.0,
                    timestamp=row["created_at"] or "",
                )
            )
            imported += 1

        if imported:
            logger.info(
                "[brand_integration] Imported %d signals from FeedbackTracker",
                imported,
            )

    except Exception as exc:
        logger.debug("[brand_integration] FeedbackTracker import failed: %s", exc)

    return imported


def get_brand_context_with_learning(
    collection: str | None = None,
    loop: Any | None = None,
) -> str:
    """
    Get brand system prompt enhanced with learning loop insights.

    Augments the static BrandContextInjector prompt with:
    - Active high-confidence insights
    - Brand drift warnings
    - Collection-specific reinforcement notes

    Args:
        collection: Optional collection to contextualize
        loop: Brand learning loop instance (lazy-creates if None)

    Returns:
        Enhanced brand system prompt string
    """
    from orchestration.brand_context import BrandContextInjector, Collection

    injector = BrandContextInjector()

    # Map string to Collection enum
    collection_enum = None
    if collection:
        collection_map = {
            "BLACK_ROSE": Collection.BLACK_ROSE,
            "black-rose": Collection.BLACK_ROSE,
            "LOVE_HURTS": Collection.LOVE_HURTS,
            "love-hurts": Collection.LOVE_HURTS,
            "SIGNATURE": Collection.SIGNATURE,
            "signature": Collection.SIGNATURE,
        }
        collection_enum = collection_map.get(collection)

    base_prompt = injector.get_system_prompt(collection_enum)

    # Augment with learning insights
    if loop is None:
        try:
            from orchestration.brand_learning import create_brand_learning_loop

            loop = create_brand_learning_loop(auto_connect=False)
        except ImportError:
            return base_prompt

    insights = loop.get_active_insights(min_confidence=_medium_confidence())
    if not insights:
        return base_prompt

    # Build augmentation section
    augmentation_parts = ["\n\n## Learned Brand Insights (auto-updated)"]

    for insight in insights[:5]:  # Top 5 active insights
        if insight.recommendations:
            augmentation_parts.append(f"- {insight.title}: {insight.recommendations[0]}")

    # Check for drift warnings
    drift_insights = [i for i in insights if i.category.value == "brand_drift"]
    if drift_insights:
        augmentation_parts.append("\n### Brand Drift Warnings")
        for di in drift_insights[:3]:
            augmentation_parts.append(f"- {di.description}")

    # Check for collection reinforcement
    if collection:
        from orchestration.brand_context import SKYYROSE_BRAND

        reinforcement = SKYYROSE_BRAND.get("_reinforcement_needed", [])
        collection_upper = collection.upper().replace("-", "_")
        if collection_upper in reinforcement:
            augmentation_parts.append(
                f"\n### NOTE: {collection} collection needs extra brand voice attention. "
                f"Use full descriptors, not compact mode."
            )

    return base_prompt + "\n".join(augmentation_parts)


def _medium_confidence():
    """Helper to avoid import at module level."""
    from orchestration.brand_learning import InsightConfidence

    return InsightConfidence.MEDIUM


# =============================================================================
# App Lifecycle Hooks
# =============================================================================


async def on_startup(app: Any = None) -> Any:
    """
    Call during FastAPI startup to initialize brand learning.

    Usage in main_enterprise.py:
        from orchestration.brand_integration import on_startup

        @app.on_event("startup")
        async def startup():
            app.state.brand_loop = await on_startup(app)
    """
    loop = wire_brand_learning()

    if app is not None:
        app.state.brand_learning_loop = loop

    logger.info("[brand_integration] Brand learning loop initialized on startup")
    return loop


async def on_cycle_check(loop: Any) -> list[Any]:
    """
    Check if a learning cycle should run and execute it if so.

    Call this periodically (e.g., from a background task or cron).

    Returns:
        List of new insights (empty if no cycle ran)
    """
    if loop.should_run_cycle():
        return await loop.run_cycle()
    return []


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "get_brand_context_with_learning",
    "on_cycle_check",
    "on_startup",
    "wire_brand_learning",
]
