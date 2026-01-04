"""FLUX Production Orchestrator.

Production orchestrator for FLUX-powered product generation.
Integrates with HuggingFace Spaces, WordPress, and CDN.
"""

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class ProductSpecs:
    """Product specification for generation."""

    garment_type: str
    collection: str
    color: str
    fabric: str
    sku: str
    name: str
    slug: str
    price: float
    style_notes: str = ""


class FluxProductionPipeline:
    """
    Production orchestrator for FLUX-powered product generation.

    Connects to deployed HuggingFace Spaces for GPU inference,
    then uploads results to WordPress via CDN.
    """

    ANGLES = [
        "front view centered",
        "back view centered",
        "side profile left",
        "side profile right",
        "detail shot fabric texture closeup",
        "detail shot construction and stitching",
    ]

    COLLECTION_VOICE = {
        "BLACK_ROSE": (
            "Where darkness becomes wearable art. This limited edition piece "
            "embodies the mystery and sophistication of our most exclusive collection."
        ),
        "LOVE_HURTS": (
            "Emotional expression through luxury craft. Each detail tells a story "
            "of vulnerable strength and authentic rebellion."
        ),
        "SIGNATURE": (
            "Essential luxury for everyday excellence. Refined, versatile, "
            "and built to become a wardrobe foundation."
        ),
    }

    def __init__(
        self,
        flux_space_id: str = "damBruh/skyyrose-flux-upscaler",
        wp_api: Any | None = None,
        cdn: Any | None = None,
    ):
        """Initialize the pipeline.

        Args:
            flux_space_id: HuggingFace Space ID for FLUX generation
            wp_api: WordPress API client instance
            cdn: CDN client (e.g., Cloudflare R2) instance
        """
        self.flux_space_id = flux_space_id
        self.wp_api = wp_api
        self.cdn = cdn
        self._client = None

    @property
    def flux_client(self):
        """Lazy-load Gradio client."""
        if self._client is None:
            try:
                from gradio_client import Client

                self._client = Client(self.flux_space_id)
            except ImportError:
                raise ImportError("gradio_client required: pip install gradio_client")
        return self._client

    async def generate_complete_product_set(
        self, product_specs: ProductSpecs, resolution: int = 2048, rate_limit_seconds: float = 10.0
    ) -> dict[str, dict[str, Any]]:
        """
        Generate all product angles with FLUX quality.

        Args:
            product_specs: Product specification
            resolution: Target resolution (1024, 2048, 3072, or 4096)
            rate_limit_seconds: Delay between API calls (for free tier)

        Returns:
            Dict mapping angle names to base and upscaled images
        """
        product_images = {}

        for angle in self.ANGLES:
            print(f"Generating: {angle}...")

            # Call FLUX Space
            base, upscaled = self.flux_client.predict(
                garment_type=product_specs.garment_type,
                collection=product_specs.collection,
                color_description=product_specs.color,
                fabric_type=product_specs.fabric,
                angle=angle,
                final_resolution=resolution,
                style_notes=product_specs.style_notes,
                api_name="/generate_images",
            )

            product_images[angle] = {"base": base, "upscaled": upscaled}

            # Rate limiting for free tier
            await asyncio.sleep(rate_limit_seconds)

        return product_images

    async def upload_to_cdn(
        self, product_specs: ProductSpecs, images: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        """
        Upload high-res images to CDN.

        Args:
            product_specs: Product specification
            images: Generated images from generate_complete_product_set

        Returns:
            Dict mapping angle names to CDN URLs
        """
        if self.cdn is None:
            raise ValueError("CDN client not configured")

        cdn_urls = {}
        for angle, img_data in images.items():
            # Sanitize angle name for path
            angle_slug = angle.replace(" ", "_").replace("/", "-")

            # Upload high-res version to CDN
            cdn_url = await self.cdn.upload(
                file=img_data["upscaled"],
                path=f"products/{product_specs.sku}/{angle_slug}_2k.png",
                public=True,
            )
            cdn_urls[angle] = cdn_url

        return cdn_urls

    def generate_luxury_copy(self, specs: ProductSpecs) -> str:
        """
        Generate luxury product description.

        Args:
            specs: Product specification

        Returns:
            Formatted product description HTML
        """
        voice = self.COLLECTION_VOICE.get(
            specs.collection, "Luxury streetwear where love meets fashion."
        )

        return f"""
{voice}

**{specs.name}** - {specs.garment_type} in {specs.color}

Crafted from {specs.fabric}, this piece represents SkyyRose's commitment
to where Oakland street authenticity meets luxury craftsmanship.

**Details:**
- Premium {specs.fabric}
- Gender-neutral design
- Limited availability
- Designed in Oakland, California
- Professional finishing

*Where love meets luxury.*
        """.strip()

    async def deploy_to_wordpress(
        self, product_specs: ProductSpecs, cdn_urls: dict[str, str]
    ) -> str:
        """
        Create WordPress/WooCommerce product with CDN images.

        Args:
            product_specs: Product specification
            cdn_urls: CDN URLs from upload_to_cdn

        Returns:
            Product URL
        """
        if self.wp_api is None:
            raise ValueError("WordPress API client not configured")

        product_id = await self.wp_api.create_product(
            name=product_specs.name,
            sku=product_specs.sku,
            price=product_specs.price,
            images=list(cdn_urls.values()),
            description=self.generate_luxury_copy(product_specs),
            meta_data=[
                {"key": "_collection", "value": product_specs.collection},
                {"key": "_fabric", "value": product_specs.fabric},
                {"key": "_image_quality", "value": "2K_flux_upscaled"},
            ],
        )

        return f"https://skyyrose.co/product/{product_specs.slug}"

    async def run_full_pipeline(self, product_specs: ProductSpecs, resolution: int = 2048) -> str:
        """
        Run complete pipeline: Generate -> Upload -> Deploy.

        Args:
            product_specs: Product specification
            resolution: Target image resolution

        Returns:
            Product URL on WordPress
        """
        # Generate images
        images = await self.generate_complete_product_set(product_specs, resolution=resolution)

        # Upload to CDN
        cdn_urls = await self.upload_to_cdn(product_specs, images)

        # Deploy to WordPress
        product_url = await self.deploy_to_wordpress(product_specs, cdn_urls)

        return product_url


# Convenience function for quick usage
async def launch_product(
    garment_type: str,
    collection: str,
    color: str,
    fabric: str,
    sku: str,
    name: str,
    slug: str,
    price: float,
    style_notes: str = "",
) -> str:
    """
    Quick launch a product through the FLUX pipeline.

    Example:
        url = await launch_product(
            garment_type='oversized hoodie',
            collection='SIGNATURE',
            color='midnight black',
            fabric='heavyweight brushed cotton fleece',
            sku='SRS-SIG-001',
            name='Essential Black Hoodie',
            slug='essential-black-hoodie',
            price=145.00
        )
    """
    specs = ProductSpecs(
        garment_type=garment_type,
        collection=collection,
        color=color,
        fabric=fabric,
        sku=sku,
        name=name,
        slug=slug,
        price=price,
        style_notes=style_notes,
    )

    pipeline = FluxProductionPipeline()
    return await pipeline.run_full_pipeline(specs)
