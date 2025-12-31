"""
WordPress/Elementor 3D Experience API
=====================================

Backend API for serving 3D experiences to WordPress/Elementor pages.
Provides endpoints for:
- Experience configuration retrieval
- Shortcode generation
- Elementor widget data
- 3D asset serving
- Analytics tracking

Endpoints:
- GET /api/v1/elementor-3d/experiences - List available 3D experiences
- GET /api/v1/elementor-3d/experiences/{collection} - Get experience config
- POST /api/v1/elementor-3d/shortcode - Generate WordPress shortcode
- GET /api/v1/elementor-3d/widget-config - Get Elementor widget config
- POST /api/v1/elementor-3d/analytics - Track experience interactions
"""

import logging
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Types
# =============================================================================


class CollectionType(str, Enum):
    """Available 3D collection experiences."""

    BLACK_ROSE = "black_rose"
    SIGNATURE = "signature"
    LOVE_HURTS = "love_hurts"
    SHOWROOM = "showroom"
    RUNWAY = "runway"


class InteractivitySettings(BaseModel):
    """Interactive feature settings for 3D experiences."""

    enable_product_cards: bool = True
    enable_category_navigation: bool = False
    enable_spatial_audio: bool = False
    enable_ar_preview: bool = False
    cursor_spotlight: bool = True


class FallbackSettings(BaseModel):
    """Responsive/fallback settings for low-performance devices."""

    enable_2d_parallax: bool = True
    low_performance_threshold: int = 24  # FPS


class ExperienceConfig(BaseModel):
    """Configuration for a 3D experience."""

    background_color: str = "#1A1A1A"
    enable_bloom: bool = True
    bloom_strength: float = 0.5
    enable_depth_of_field: bool = False
    particle_count: int = 1000


class ProductData(BaseModel):
    """Product data for 3D experiences."""

    id: str
    name: str
    price: float | None = None
    model_url: str | None = None
    thumbnail_url: str | None = None
    position: tuple[float, float, float] = (0, 0, 0)
    woocommerce_id: int | None = None


class Experience3DSpec(BaseModel):
    """Complete specification for a 3D experience."""

    id: str
    collection: CollectionType
    name: str
    description: str
    config: ExperienceConfig = Field(default_factory=ExperienceConfig)
    products: list[ProductData] = Field(default_factory=list)
    interactivity: InteractivitySettings = Field(default_factory=InteractivitySettings)
    fallback: FallbackSettings = Field(default_factory=FallbackSettings)
    embed_url: str | None = None
    preview_image: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ShortcodeRequest(BaseModel):
    """Request to generate a WordPress shortcode."""

    collection: CollectionType
    width: str = "100%"
    height: str = "600px"
    products: list[str] | None = None
    enable_fullscreen: bool = True
    custom_css: str | None = None


class ShortcodeResponse(BaseModel):
    """Generated shortcode response."""

    shortcode: str
    embed_code: str
    preview_url: str


class AnalyticsEvent(BaseModel):
    """Analytics event for 3D experience interactions."""

    event_type: str
    collection: CollectionType
    session_id: str
    product_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WidgetConfig(BaseModel):
    """Elementor widget configuration."""

    widget_name: str = "skyyrose_3d_experience"
    widget_title: str = "SkyyRose 3D Experience"
    widget_icon: str = "eicon-cube"
    widget_categories: list[str] = Field(default_factory=lambda: ["skyyrose"])
    controls: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Experience Registry
# =============================================================================


# Pre-configured experiences for each collection
EXPERIENCES: dict[CollectionType, Experience3DSpec] = {
    CollectionType.BLACK_ROSE: Experience3DSpec(
        id="exp-black-rose",
        collection=CollectionType.BLACK_ROSE,
        name="BLACK ROSE Collection",
        description="Immersive dark elegance experience with Gothic aesthetics",
        config=ExperienceConfig(
            background_color="#0D0D0D",
            enable_bloom=True,
            bloom_strength=0.8,
            particle_count=2000,
        ),
        interactivity=InteractivitySettings(
            enable_product_cards=True,
            cursor_spotlight=True,
        ),
        preview_image="/assets/previews/black-rose-preview.jpg",
    ),
    CollectionType.SIGNATURE: Experience3DSpec(
        id="exp-signature",
        collection=CollectionType.SIGNATURE,
        name="Signature Collection",
        description="Premium showcase with elegant category navigation",
        config=ExperienceConfig(
            background_color="#1A1A1A",
            enable_bloom=True,
            bloom_strength=0.5,
        ),
        interactivity=InteractivitySettings(
            enable_product_cards=True,
            enable_category_navigation=True,
        ),
        preview_image="/assets/previews/signature-preview.jpg",
    ),
    CollectionType.LOVE_HURTS: Experience3DSpec(
        id="exp-love-hurts",
        collection=CollectionType.LOVE_HURTS,
        name="Love Hurts Collection",
        description="Dramatic theatrical experience with mirror effects",
        config=ExperienceConfig(
            background_color="#1A0010",
            enable_bloom=True,
            bloom_strength=0.7,
            enable_depth_of_field=True,
        ),
        interactivity=InteractivitySettings(
            enable_product_cards=True,
            enable_spatial_audio=True,
        ),
        preview_image="/assets/previews/love-hurts-preview.jpg",
    ),
    CollectionType.SHOWROOM: Experience3DSpec(
        id="exp-showroom",
        collection=CollectionType.SHOWROOM,
        name="Virtual Showroom",
        description="Walk-through experience with product displays",
        config=ExperienceConfig(
            background_color="#FFFFFF",
            enable_bloom=False,
        ),
        interactivity=InteractivitySettings(
            enable_product_cards=True,
            enable_ar_preview=True,
        ),
        preview_image="/assets/previews/showroom-preview.jpg",
    ),
    CollectionType.RUNWAY: Experience3DSpec(
        id="exp-runway",
        collection=CollectionType.RUNWAY,
        name="Fashion Runway",
        description="Cinematic runway experience with model animations",
        config=ExperienceConfig(
            background_color="#0A0A0A",
            enable_bloom=True,
            bloom_strength=0.6,
        ),
        interactivity=InteractivitySettings(
            enable_spatial_audio=True,
        ),
        preview_image="/assets/previews/runway-preview.jpg",
    ),
}


# =============================================================================
# Router
# =============================================================================

elementor_3d_router = APIRouter(prefix="/elementor-3d", tags=["Elementor 3D"])


@elementor_3d_router.get("/experiences", response_model=list[Experience3DSpec])
async def list_experiences():
    """List all available 3D experiences."""
    return list(EXPERIENCES.values())


@elementor_3d_router.get("/experiences/{collection}", response_model=Experience3DSpec)
async def get_experience(collection: CollectionType):
    """Get configuration for a specific 3D experience."""
    if collection not in EXPERIENCES:
        raise HTTPException(status_code=404, detail=f"Experience not found: {collection}")
    return EXPERIENCES[collection]


@elementor_3d_router.post("/shortcode", response_model=ShortcodeResponse)
async def generate_shortcode(request: ShortcodeRequest):
    """Generate WordPress shortcode for embedding 3D experience."""
    experience = EXPERIENCES.get(request.collection)
    if not experience:
        raise HTTPException(status_code=404, detail=f"Experience not found: {request.collection}")

    # Build shortcode attributes
    attrs = [
        f'collection="{request.collection.value}"',
        f'width="{request.width}"',
        f'height="{request.height}"',
        f'fullscreen="{str(request.enable_fullscreen).lower()}"',
    ]

    if request.products:
        attrs.append(f'products="{",".join(request.products)}"')

    shortcode = f'[skyyrose_3d {" ".join(attrs)}]'

    # Generate iframe embed code
    embed_url = f"/3d-experience/{request.collection.value}"
    embed_code = f"""<iframe
    src="{embed_url}"
    width="{request.width}"
    height="{request.height}"
    frameborder="0"
    allowfullscreen
    loading="lazy"
    title="{experience.name}"
></iframe>"""

    if request.custom_css:
        embed_code = f"<style>{request.custom_css}</style>\n{embed_code}"

    preview_url = f"/api/v1/elementor-3d/preview/{request.collection.value}"

    logger.info(f"Generated shortcode for {request.collection.value}")

    return ShortcodeResponse(
        shortcode=shortcode,
        embed_code=embed_code,
        preview_url=preview_url,
    )


@elementor_3d_router.get("/widget-config", response_model=WidgetConfig)
async def get_widget_config():
    """Get Elementor widget configuration for PHP integration."""

    controls = [
        {
            "name": "collection",
            "label": "Collection",
            "type": "select",
            "default": "black_rose",
            "options": {c.value: EXPERIENCES[c].name for c in CollectionType},
        },
        {
            "name": "height",
            "label": "Height",
            "type": "slider",
            "default": {"size": 600, "unit": "px"},
            "range": {"px": {"min": 300, "max": 1200, "step": 50}},
        },
        {
            "name": "enable_fullscreen",
            "label": "Enable Fullscreen",
            "type": "switcher",
            "default": "yes",
        },
        {
            "name": "enable_bloom",
            "label": "Bloom Effect",
            "type": "switcher",
            "default": "yes",
        },
        {
            "name": "background_color",
            "label": "Background Color",
            "type": "color",
            "default": "#1A1A1A",
        },
        {
            "name": "enable_product_cards",
            "label": "Show Product Cards",
            "type": "switcher",
            "default": "yes",
        },
        {
            "name": "enable_ar",
            "label": "Enable AR Preview",
            "type": "switcher",
            "default": "no",
        },
    ]

    return WidgetConfig(controls=controls)


@elementor_3d_router.post("/analytics")
async def track_analytics(event: AnalyticsEvent):
    """Track 3D experience analytics events."""
    logger.info(
        f"3D Analytics: {event.event_type} - {event.collection.value} - {event.product_id or 'N/A'}"
    )

    # In production, send to analytics service
    return {
        "success": True,
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "timestamp": event.timestamp.isoformat(),
    }


@elementor_3d_router.get("/preview/{collection}")
async def get_preview(collection: CollectionType, format: str = Query("json")):
    """Get preview data for a collection experience."""
    if collection not in EXPERIENCES:
        raise HTTPException(status_code=404, detail=f"Experience not found: {collection}")

    experience = EXPERIENCES[collection]

    if format == "html":
        # Return simple HTML preview
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{experience.name} - Preview</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: {experience.config.background_color};
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .preview-container {{
            text-align: center;
            padding: 2rem;
        }}
        h1 {{
            color: #B76E79;
            margin-bottom: 1rem;
        }}
        p {{
            color: #888;
        }}
        .loader {{
            width: 50px;
            height: 50px;
            border: 3px solid #333;
            border-top-color: #B76E79;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>{experience.name}</h1>
        <p>{experience.description}</p>
        <div class="loader"></div>
        <p>Loading 3D Experience...</p>
    </div>
    <script>
        // Initialize 3D experience
        window.SKYYROSE_3D_CONFIG = {experience.model_dump_json()};
    </script>
</body>
</html>
"""
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=html)

    return experience


@elementor_3d_router.get("/js-bundle")
async def get_js_bundle():
    """Get the JavaScript bundle URL for 3D experiences."""
    return {
        "bundle_url": "/assets/js/skyyrose-3d-experiences.min.js",
        "version": "2.0.0",
        "dependencies": [
            {
                "name": "three",
                "version": "0.160.0",
                "url": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js",
            },
        ],
        "init_function": "SkyyRose3D.createCollectionExperience",
    }


# =============================================================================
# Model Fidelity Validation
# =============================================================================

MINIMUM_FIDELITY_SCORE = 95.0


class ModelValidationRequest(BaseModel):
    """Request to validate a 3D model's fidelity."""

    model_url: str = Field(..., description="URL of the 3D model to validate")


class ModelValidationResponse(BaseModel):
    """Response from model fidelity validation."""

    model_url: str
    fidelity_score: float
    passed: bool
    minimum_required: float = MINIMUM_FIDELITY_SCORE
    report: dict[str, Any] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@elementor_3d_router.post("/validate", response_model=ModelValidationResponse)
async def validate_model_fidelity(request: ModelValidationRequest):
    """
    Validate a 3D model's fidelity score.

    Models must achieve 95% fidelity to be displayed.
    This ensures only authentic, high-quality models are shown to users.
    """
    try:
        # Import fidelity validator
        from imagery.model_fidelity import ModelFidelityValidator

        validator = ModelFidelityValidator()

        # Download and validate model
        # In production, this would fetch the model from the URL
        # For now, check if it's a local path or remote
        model_path = request.model_url

        if model_path.startswith(("http://", "https://")):
            # Remote model - would need to download first
            # For security, validate against known asset locations
            if not any(
                model_path.startswith(domain)
                for domain in [
                    "https://skyyrose.com/",
                    "https://cdn.skyyrose.com/",
                    "https://api.skyyrose.com/",
                ]
            ):
                logger.warning(f"Attempted to validate model from untrusted source: {model_path}")
                return ModelValidationResponse(
                    model_url=request.model_url,
                    fidelity_score=0.0,
                    passed=False,
                    report={"error": "Model URL not from trusted source"},
                )

        # Validate the model
        report = await validator.validate(model_path)

        logger.info(
            f"Model validation: {request.model_url} - "
            f"Score: {report.overall_score:.1f}% - "
            f"Passed: {report.passed}"
        )

        return ModelValidationResponse(
            model_url=request.model_url,
            fidelity_score=report.overall_score,
            passed=report.passed,
            report={
                "geometry_score": report.geometry.overall_score if report.geometry else 0,
                "texture_score": report.textures.overall_score if report.textures else 0,
                "material_score": report.materials.overall_score if report.materials else 0,
                "issues": report.issues,
                "suggestions": report.suggestions,
            },
        )

    except ImportError:
        logger.error("ModelFidelityValidator not available")
        return ModelValidationResponse(
            model_url=request.model_url,
            fidelity_score=0.0,
            passed=False,
            report={"error": "Fidelity validator not available"},
        )
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return ModelValidationResponse(
            model_url=request.model_url,
            fidelity_score=0.0,
            passed=False,
            report={"error": str(e)},
        )


@elementor_3d_router.get("/fidelity-threshold")
async def get_fidelity_threshold():
    """Get the minimum fidelity threshold for 3D models."""
    return {
        "minimum_fidelity_score": MINIMUM_FIDELITY_SCORE,
        "description": "All 3D models must achieve this fidelity score to be displayed",
        "enforcement": "strict",
    }


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "elementor_3d_router",
    "Experience3DSpec",
    "CollectionType",
    "ShortcodeRequest",
    "ShortcodeResponse",
    "ModelValidationRequest",
    "ModelValidationResponse",
    "MINIMUM_FIDELITY_SCORE",
]
