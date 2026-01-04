"""Enhanced SkyyRose Product Pipeline.

Complete pipeline with vision intelligence:
FLUX/SDXL Generation -> Qwen Analysis -> WordPress Deployment

This integrates:
- Image generation (FLUX.1-dev or SDXL)
- AI vision analysis (Qwen-VL)
- Automated product deployment
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DesignSpecs:
    """Product design specifications."""

    name: str
    sku: str
    collection: str
    price: float
    garment_type: str = ""
    color: str = ""
    fabric: str = ""
    style_notes: str = ""


class EnhancedSkyyRosePipeline:
    """
    Complete pipeline with vision intelligence.
    FLUX/SDXL -> Qwen Analysis -> WordPress
    """

    def __init__(
        self,
        flux_space_id: str = "damBruh/skyyrose-flux-upscaler",
        analyzer_space_id: str = "damBruh/skyyrose-product-analyzer",
        wp_api: Any | None = None,
    ):
        """Initialize pipeline components.

        Args:
            flux_space_id: HuggingFace Space for FLUX generation
            analyzer_space_id: HuggingFace Space for Qwen analysis
            wp_api: WordPress API client
        """
        self.flux_space_id = flux_space_id
        self.analyzer_space_id = analyzer_space_id
        self.wp_api = wp_api
        self._flux_client = None
        self._qwen_client = None

    @property
    def flux_generator(self):
        """Lazy load FLUX client."""
        if self._flux_client is None:
            from gradio_client import Client

            self._flux_client = Client(self.flux_space_id)
        return self._flux_client

    @property
    def qwen_analyzer(self):
        """Lazy load Qwen client."""
        if self._qwen_client is None:
            from gradio_client import Client

            self._qwen_client = Client(self.analyzer_space_id)
        return self._qwen_client

    async def generate_product_image(
        self, design_specs: DesignSpecs, resolution: int = 2048
    ) -> dict[str, Any]:
        """
        Generate product image with FLUX.

        Args:
            design_specs: Product design specifications
            resolution: Target resolution

        Returns:
            Dict with base and upscaled images
        """
        base, upscaled = self.flux_generator.predict(
            garment_type=design_specs.garment_type,
            collection=design_specs.collection,
            color_description=design_specs.color,
            fabric_type=design_specs.fabric,
            angle="front view centered",
            final_resolution=resolution,
            style_notes=design_specs.style_notes,
            api_name="/generate_images",
        )

        return {"base": base, "upscaled": upscaled}

    def analyze_product(self, image_path: str, analysis_type: str = "detailed_description") -> str:
        """
        Analyze product image with Qwen-VL.

        Args:
            image_path: Path to product image
            analysis_type: Type of analysis

        Returns:
            Analysis result text
        """
        result = self.qwen_analyzer.predict(
            image=image_path, analysis_type=analysis_type, api_name="/analyze_image"
        )
        return result

    def extract_metadata(self, image_path: str) -> dict[str, Any]:
        """Extract structured metadata from product image."""
        result = self.qwen_analyzer.predict(image=image_path, api_name="/extract_metadata")
        return result

    def generate_copy(self, image_path: str, collection: str, price: float) -> str:
        """Generate luxury product copy."""
        result = self.qwen_analyzer.predict(
            image=image_path, collection=collection, price=price, api_name="/generate_copy"
        )
        return result

    async def intelligent_product_launch(self, design_specs: DesignSpecs) -> dict[str, Any]:
        """
        Enhanced pipeline with AI-generated content.

        Full flow:
        1. Generate product images with FLUX
        2. Analyze images with Qwen-VL
        3. Generate AI copy and metadata
        4. Deploy to WordPress

        Args:
            design_specs: Product design specifications

        Returns:
            Dict with URL, metadata, SEO keywords, and copy length
        """
        print(f"Launching: {design_specs.name}")

        # STAGE 1: Generate product images
        print("Generating product photography...")
        images = await self.generate_product_image(design_specs)
        hero_image = images["upscaled"]

        # STAGE 2: Analyze generated images with Qwen
        print("Analyzing product with AI...")

        # Extract metadata
        metadata = self.extract_metadata(hero_image)
        print(f"   Detected: {metadata.get('garment_type', 'Unknown')}")
        print(f"   Material: {metadata.get('fabric_type', 'Unknown')}")

        # Generate luxury copy
        product_copy = self.generate_copy(
            image_path=hero_image, collection=design_specs.collection, price=design_specs.price
        )
        print(f"   Generated {len(product_copy)} characters of copy")

        # Extract SEO keywords
        seo_keywords = self.analyze_product(hero_image, "seo_keywords")

        # STAGE 3: Deploy to WordPress with AI-enhanced content
        if self.wp_api is None:
            print("WordPress API not configured - skipping deployment")
            product_url = f"https://skyyrose.co/product/{design_specs.sku}"
        else:
            print("Deploying to WordPress...")
            product_url = await self.wp_api.create_product(
                name=design_specs.name,
                sku=design_specs.sku,
                price=design_specs.price,
                images=[hero_image],
                description=product_copy,
                short_description=(
                    product_copy.split("\n\n")[0] if "\n\n" in product_copy else product_copy[:200]
                ),
                tags=seo_keywords.split(", ") if isinstance(seo_keywords, str) else [],
                meta_data=[
                    {"key": "_collection", "value": design_specs.collection},
                    {"key": "_ai_analyzed", "value": "true"},
                    {"key": "_fabric_detected", "value": metadata.get("fabric_type", "")},
                    {"key": "_fit_detected", "value": metadata.get("fit", "")},
                ],
            )

        print(f"Product live: {product_url}")

        return {
            "url": product_url,
            "metadata": metadata,
            "seo_keywords": seo_keywords,
            "ai_copy_length": len(product_copy),
            "images": images,
        }


# Convenience function
async def launch_product(
    name: str,
    sku: str,
    collection: str,
    price: float,
    garment_type: str = "",
    color: str = "",
    fabric: str = "",
    style_notes: str = "",
    wp_api: Any | None = None,
) -> dict[str, Any]:
    """
    Quick launch a product through the enhanced pipeline.

    Example:
        result = await launch_product(
            name='Essential Black Hoodie',
            sku='SRS-SIG-001',
            collection='SIGNATURE',
            price=145.00,
            garment_type='oversized hoodie',
            color='midnight black',
            fabric='heavyweight brushed cotton fleece'
        )
    """
    specs = DesignSpecs(
        name=name,
        sku=sku,
        collection=collection,
        price=price,
        garment_type=garment_type,
        color=color,
        fabric=fabric,
        style_notes=style_notes,
    )

    pipeline = EnhancedSkyyRosePipeline(wp_api=wp_api)
    return await pipeline.intelligent_product_launch(specs)
