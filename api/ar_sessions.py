"""
AR Sessions API Endpoints
=========================

Manages AR shopping sessions for WebXR and webcam-based try-on.
Handles session lifecycle, product metadata, and analytics.

Features:
- Session creation and management
- AR-ready product metadata
- Real-time session tracking
- Analytics and conversion tracking
- WebXR capability detection

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import functools
import logging
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from skyyrose.core.catalog_loader import read_catalog_rows
from skyyrose.core.sot_images import resolve_image

logger = logging.getLogger(__name__)

# skyyrose_product_image_uri()'s get_theme_file_uri() prefix for the flagship
# theme in production — resolve_image() returns theme-relative paths, this is
# the ONLY place that turns them into public URLs (mirrors inc/product-catalog.php).
_THEME_BASE_URL = "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"

# CSV garment_type_lock -> AR garment_category taxonomy (matches /capabilities
# below). Unmapped/blank values fall back to "tops".
_GARMENT_CATEGORY_MAP: dict[str, str] = {
    "jersey": "tops",
    "shirt": "tops",
    "crewneck": "tops",
    "hoodie": "tops",
    "bomber jacket": "outerwear",
    "jacket": "outerwear",
    "joggers": "bottoms",
    "sweatpants": "bottoms",
    "shorts": "bottoms",
    "set": "tops",
}

ar_sessions_router = APIRouter(prefix="/ar", tags=["AR Sessions"])


# =============================================================================
# Enums
# =============================================================================


class ARMode(StrEnum):
    """AR experience mode."""

    WEBXR = "webxr"  # Native AR (ARCore/ARKit)
    WEBCAM = "webcam"  # Camera-based AR
    PREVIEW = "preview"  # Non-AR 3D preview


class CollectionType(StrEnum):
    """SkyyRose collection types."""

    BLACK_ROSE = "black_rose"
    LOVE_HURTS = "love_hurts"
    SIGNATURE = "signature"
    KIDS_CAPSULE = "kids_capsule"


class SessionStatus(StrEnum):
    """AR session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# =============================================================================
# Models
# =============================================================================


class CreateSessionRequest(BaseModel):
    """Request to create an AR session."""

    collection: CollectionType = Field(..., description="Collection to browse")
    mode: ARMode = Field(default=ARMode.WEBCAM, description="AR mode")
    product_id: str | None = Field(None, description="Initial product to try on")
    user_agent: str | None = Field(None, description="Browser user agent")
    screen_width: int | None = Field(None, description="Screen width")
    screen_height: int | None = Field(None, description="Screen height")


class ARSession(BaseModel):
    """AR session record."""

    session_id: str
    collection: CollectionType
    mode: ARMode
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    try_on_count: int = 0
    products_viewed: list[str] = []
    conversion: bool = False
    metadata: dict[str, Any] = {}


class ARProduct(BaseModel):
    """AR-enabled product metadata."""

    id: str
    name: str
    collection: CollectionType
    price: float
    image_url: str
    ar_enabled: bool = True
    model_url: str | None = None
    garment_category: str = "tops"
    try_on_compatible: bool = True


class SessionAnalytics(BaseModel):
    """Session analytics data."""

    total_sessions: int
    active_sessions: int
    avg_try_on_count: float
    conversion_rate: float
    popular_products: list[dict[str, Any]]
    mode_distribution: dict[str, int]


class TryOnEvent(BaseModel):
    """Try-on event for tracking."""

    session_id: str
    product_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    duration_ms: int | None = None


# =============================================================================
# In-Memory Store (Replace with Redis in production)
# =============================================================================


class ARSessionStore:
    """In-memory AR session storage."""

    def __init__(self):
        self._sessions: dict[str, ARSession] = {}
        self._events: list[TryOnEvent] = []
        self._active_websockets: dict[str, WebSocket] = {}

    def create_session(self, request: CreateSessionRequest) -> ARSession:
        """Create a new AR session."""
        session_id = f"ar_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        session = ARSession(
            session_id=session_id,
            collection=request.collection,
            mode=request.mode,
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            metadata={
                "user_agent": request.user_agent,
                "screen": f"{request.screen_width}x{request.screen_height}",
                "initial_product": request.product_id,
            },
        )
        self._sessions[session_id] = session
        logger.info(f"AR session created: {session_id} ({request.collection}, {request.mode})")
        return session

    def get_session(self, session_id: str) -> ARSession | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        status: SessionStatus | None = None,
        try_on_count_increment: int = 0,
        product_viewed: str | None = None,
        conversion: bool | None = None,
    ) -> ARSession | None:
        """Update session state."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        if status:
            session.status = status
        session.try_on_count += try_on_count_increment
        if product_viewed and product_viewed not in session.products_viewed:
            session.products_viewed.append(product_viewed)
        if conversion is not None:
            session.conversion = conversion
        session.updated_at = datetime.now(UTC)
        return session

    def record_tryon_event(self, event: TryOnEvent) -> None:
        """Record a try-on event."""
        self._events.append(event)
        self.update_session(
            event.session_id,
            try_on_count_increment=1,
            product_viewed=event.product_id,
        )

    def get_analytics(self) -> SessionAnalytics:
        """Get session analytics."""
        sessions = list(self._sessions.values())
        if not sessions:
            return SessionAnalytics(
                total_sessions=0,
                active_sessions=0,
                avg_try_on_count=0.0,
                conversion_rate=0.0,
                popular_products=[],
                mode_distribution={},
            )

        active = sum(1 for s in sessions if s.status == SessionStatus.ACTIVE)
        avg_tryon = sum(s.try_on_count for s in sessions) / len(sessions)
        conversions = sum(1 for s in sessions if s.conversion)
        conversion_rate = conversions / len(sessions) if sessions else 0.0

        # Count product views
        product_counts: dict[str, int] = {}
        for s in sessions:
            for p in s.products_viewed:
                product_counts[p] = product_counts.get(p, 0) + 1
        popular = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Mode distribution
        mode_dist: dict[str, int] = {}
        for s in sessions:
            mode_dist[s.mode.value] = mode_dist.get(s.mode.value, 0) + 1

        return SessionAnalytics(
            total_sessions=len(sessions),
            active_sessions=active,
            avg_try_on_count=avg_tryon,
            conversion_rate=conversion_rate,
            popular_products=[{"product_id": p, "views": c} for p, c in popular],
            mode_distribution=mode_dist,
        )


# Global store
session_store = ARSessionStore()


# =============================================================================
# AR Products — sourced from the canonical catalog CSV via the SOT resolver
# =============================================================================


def _collection_type_from_slug(slug: str) -> CollectionType | None:
    """Map the CSV's hyphenated collection slug to :class:`CollectionType`.

    Returns ``None`` (never raises) for an unrecognized slug so a future
    catalog addition degrades to a logged skip instead of a 500 on a live
    endpoint.
    """
    try:
        return CollectionType(slug.replace("-", "_"))
    except ValueError:
        return None


def _garment_category_from_row(row: dict[str, str]) -> str:
    """Map the CSV's ``garment_type_lock`` to the AR garment_category taxonomy.

    Falls back to "tops" for blank or unmapped values — no new CSV column.
    """
    garment_type = (row.get("garment_type_lock") or "").strip().lower()
    return _GARMENT_CATEGORY_MAP.get(garment_type, "tops")


_TRUTHY_CSV_FLAGS = frozenset({"1", "true", "yes"})


def _csv_flag(value: str | None) -> bool:
    """Truthiness of a catalog CSV boolean cell.

    The catalog writes ``"1"``/``"0"`` today, but sibling consumers
    (scripts/batch_flux_collections.py) also accept ``"true"``/``"false"`` —
    handle both spellings. Anything blank or unrecognized is False, so an
    unexpected value fails CLOSED (row treated as unpublished) rather than
    leaking a SKU onto the public AR surface.
    """
    return (value or "").strip().lower() in _TRUTHY_CSV_FLAGS


def _ar_product_from_row(row: dict[str, str]) -> ARProduct | None:
    """Map one catalog CSV row to an :class:`ARProduct`, or ``None`` when skipped.

    Skips rows that are unpublished (and not pre-order) — same semantics as
    ``skyyrose_format_price()`` in inc/product-catalog.php ("Coming Soon" =
    excluded from the AR surface). Skips rows with no resolvable SOT image
    rather than emitting a fabricated URL.
    """
    sku = (row.get("sku") or "").strip()
    published = _csv_flag(row.get("published"))
    is_preorder = _csv_flag(row.get("is_preorder"))
    if not published and not is_preorder:
        logger.info("AR catalog: skipping unpublished, non-preorder SKU %s", sku)
        return None

    collection = _collection_type_from_slug((row.get("collection") or "").strip())
    if collection is None:
        logger.warning(
            "AR catalog: skipping SKU %s — unrecognized collection slug %r",
            sku,
            row.get("collection"),
        )
        return None

    relative_image = resolve_image(sku, "front")
    if relative_image is None:
        logger.warning("AR catalog: skipping SKU %s — no resolvable SOT image", sku)
        return None

    try:
        price = float(row.get("price") or 0)
    except ValueError:
        logger.warning(
            "AR catalog: unparsable price %r for SKU %s — defaulting to 0.0",
            row.get("price"),
            sku,
        )
        price = 0.0

    return ARProduct(
        id=sku,
        name=row.get("name") or sku,
        collection=collection,
        price=price,
        image_url=_THEME_BASE_URL + relative_image,
        garment_category=_garment_category_from_row(row),
    )


@functools.lru_cache(maxsize=1)
def get_ar_products_from_catalog() -> list[ARProduct]:
    """Build the AR product list from the canonical catalog CSV + SOT imagery.

    Row policy (publication filter, SOT image resolution, price parsing) lives
    in :func:`_ar_product_from_row`.

    Cached (I/O: one CSV read + per-SKU resolve_image), matching
    ``skyyrose.core.catalog_loader.read_catalog_rows``'s own ``@cache``.
    """
    return [
        product for row in read_catalog_rows() if (product := _ar_product_from_row(row)) is not None
    ]


# =============================================================================
# Endpoints
# =============================================================================


@ar_sessions_router.post("/sessions", response_model=ARSession)
async def create_ar_session(request: CreateSessionRequest) -> ARSession:
    """
    Create a new AR shopping session.

    Called when user enters a collection experience or starts AR try-on.
    """
    return session_store.create_session(request)


@ar_sessions_router.get("/sessions/{session_id}", response_model=ARSession)
async def get_ar_session(session_id: str) -> ARSession:
    """Get AR session by ID."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@ar_sessions_router.patch("/sessions/{session_id}", response_model=ARSession)
async def update_ar_session(
    session_id: str,
    status: SessionStatus | None = None,
    conversion: bool | None = None,
) -> ARSession:
    """Update AR session status."""
    session = session_store.update_session(session_id, status=status, conversion=conversion)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@ar_sessions_router.post("/sessions/{session_id}/tryon", response_model=TryOnEvent)
async def record_tryon(
    session_id: str, product_id: str, success: bool = True, duration_ms: int | None = None
) -> TryOnEvent:
    """Record a try-on event for analytics."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    event = TryOnEvent(
        session_id=session_id,
        product_id=product_id,
        success=success,
        duration_ms=duration_ms,
    )
    session_store.record_tryon_event(event)
    return event


@ar_sessions_router.get("/products/{collection}", response_model=list[ARProduct])
async def get_ar_products(
    collection: CollectionType,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ARProduct]:
    """
    Get AR-enabled products for a collection.

    Returns products with AR metadata for the collection experiences.
    """
    products = [p for p in get_ar_products_from_catalog() if p.collection == collection]
    return products[:limit]


@ar_sessions_router.get("/products", response_model=list[ARProduct])
async def get_all_ar_products(
    limit: int = Query(default=50, ge=1, le=200),
    ar_enabled_only: bool = Query(default=True),
) -> list[ARProduct]:
    """Get all AR-enabled products."""
    products = get_ar_products_from_catalog()
    if ar_enabled_only:
        products = [p for p in products if p.ar_enabled]
    return products[:limit]


@ar_sessions_router.get("/analytics", response_model=SessionAnalytics)
async def get_ar_analytics() -> SessionAnalytics:
    """Get AR session analytics for dashboard."""
    return session_store.get_analytics()


@ar_sessions_router.get("/capabilities")
async def get_ar_capabilities() -> dict[str, Any]:
    """
    Get AR system capabilities for frontend feature detection.

    Returns info about supported features and recommended modes.
    """
    return {
        "webxr_supported": True,
        "webcam_supported": True,
        "supported_collections": [c.value for c in CollectionType],
        "supported_modes": [m.value for m in ARMode],
        "try_on_provider": "fashn",
        "max_batch_size": 10,
        "garment_categories": ["tops", "bottoms", "outerwear", "dresses", "accessories"],
        "recommended_resolution": {"width": 512, "height": 512},
        "api_version": "1.0.0",
    }


@ar_sessions_router.websocket("/ws/{session_id}")
async def ar_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time AR session updates.

    Used for live try-on status, product placement confirmation, etc.
    """
    session = session_store.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    session_store._active_websockets[session_id] = websocket
    logger.info(f"WebSocket connected for session: {session_id}")

    try:
        # Send initial session state
        await websocket.send_json(
            {
                "type": "session_state",
                "session": session.model_dump(mode="json"),
            }
        )

        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "tryon_start":
                await websocket.send_json(
                    {
                        "type": "tryon_status",
                        "status": "processing",
                        "product_id": data.get("product_id"),
                    }
                )
            elif msg_type == "tryon_complete":
                await websocket.send_json(
                    {
                        "type": "tryon_status",
                        "status": "complete",
                        "product_id": data.get("product_id"),
                        "result_url": data.get("result_url"),
                    }
                )
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        session_store._active_websockets.pop(session_id, None)
