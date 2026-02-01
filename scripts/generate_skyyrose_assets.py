#!/usr/bin/env python3
"""Generate SkyyRose 3D Clothing Assets.

Uses the DevSkyy ThreeDProviderFactory with multi-provider failover:
- Tripo3D - Primary provider, great for fashion/clothing
- Replicate - Secondary, Wonder3D/Shap-E models
- HuggingFace - Fallback, TripoSR model

Failover chain: Tripo → Replicate → HuggingFace

MANDATORY: All generated models must achieve 95% fidelity score.

Usage:
    python scripts/generate_skyyrose_assets.py --collection BLACK_ROSE
    python scripts/generate_skyyrose_assets.py --all
    python scripts/generate_skyyrose_assets.py --product "Thorn Hoodie"
    python scripts/generate_skyyrose_assets.py --list
    python scripts/generate_skyyrose_assets.py --health  # Check provider health

Author: DevSkyy Platform Team
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from services.three_d.provider_factory import (
    get_provider_factory,
)
from services.three_d.provider_interface import (
    OutputFormat,
    QualityLevel,
    ThreeDRequest,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Product Definitions
# =============================================================================


@dataclass
class SkyyRoseProduct:
    """SkyyRose product definition for 3D generation."""

    name: str
    collection: str
    garment_type: str
    description: str
    price: str
    style_keywords: list[str] = field(default_factory=list)
    color_palette: list[str] = field(default_factory=list)
    reference_image: str | None = None  # Path to reference image for image-to-3D

    def to_prompt(self) -> str:
        """Generate highly detailed prompt for exact replica generation.

        CRITICAL: Prompts must be extremely specific to achieve 95%+ fidelity.
        """
        keywords = ", ".join(self.style_keywords) if self.style_keywords else ""
        colors = ", ".join(self.color_palette) if self.color_palette else ""

        collection_styles = {
            "BLACK_ROSE": "gothic luxury, dark elegance, crimson blood-red accents, matte black fabric, dramatic thorny vine embroidery, silver metallic thread, premium heavyweight construction",
            "LOVE_HURTS": "romantic gothic luxury, hand-stitched broken heart motifs, emotional depth, deep wine burgundy, rose gold hardware, lustrous satin sheen, premium French terry",
            "SIGNATURE": "ultra-premium minimalist luxury, Italian craftsmanship, subtle gold thread accents, timeless sophistication, impeccable tailoring, museum-quality finish",
        }

        garment_details = {
            "hoodie": "heavyweight cotton fleece hoodie, kangaroo pocket, reinforced ribbed cuffs and hem, metal-tipped drawstrings, double-stitched seams, oversized relaxed fit, three-panel hood construction",
            "jacket": "structured outerwear jacket, full lining, quality hardware closures, reinforced shoulder seams, premium quality stitching, adjustable cuffs",
            "tee": "premium cotton t-shirt, enzyme-washed soft hand-feel, dropped shoulder seams, reinforced collar, oversized boxy silhouette, clean hem finish",
            "blazer": "tailored wool blend blazer, canvas interlining, functional buttonholes, notched lapels, dual rear vents, interior pockets, half-canvas construction",
            "trousers": "tailored wool trousers, flat front, tapered leg, side pockets, quality waistband, belt loops, clean pressed creases",
            "pants": "heavy cotton twill cargo pants, multiple utility pockets, reinforced knees, adjustable cuffs, premium hardware, relaxed straight fit",
            "coat": "luxury overcoat, double-faced construction, notched lapel, hidden button placket, center back vent, fully lined, premium cashmere blend",
            "shirt": "oxford cloth button-down shirt, mother-of-pearl buttons, back yoke, barrel cuffs, collar stays, box pleat, curved hem",
        }

        base_style = collection_styles.get(self.collection, "luxury streetwear")
        garment_base = garment_details.get(self.garment_type, f"luxury {self.garment_type}")

        return f"""EXACT REPLICA high-end luxury fashion garment.

PRODUCT: {self.name}
TYPE: {garment_base}

DETAILED DESCRIPTION:
{self.description}

CONSTRUCTION DETAILS:
- Base garment: {garment_base}
- Style elements: {base_style}
- Design keywords: {keywords}
- Color specification: {colors if colors else 'as described'}

CRITICAL REQUIREMENTS FOR EXACT REPLICA:
1. Hyper-realistic fabric texture with visible weave/knit pattern
2. Precise stitch details including seam allowances and reinforcements
3. Accurate hardware (zippers, buttons, grommets) with metallic sheen
4. Correct garment proportions and silhouette
5. Embroidery/print details at maximum resolution
6. Proper fabric drape and fold physics
7. PBR material accuracy: roughness, metallic, normal maps
8. Clean quad-dominant topology suitable for animation
9. 4K texture resolution minimum for close-up viewing
10. Fashion industry production-ready quality

RENDERING SPECIFICATIONS:
- Format: GLB with embedded textures
- Topology: Clean quads, <100k vertices
- Textures: 4096x4096 PBR (albedo, normal, roughness, metallic, AO)
- Pose: A-pose or retail display mannequin presentation
- Quality: Museum/showroom display grade"""


# =============================================================================
# ACTUAL SKYYROSE PRODUCT CATALOG
# Reference images located in: ./assets/reference-images/
# =============================================================================

SKYYROSE_PRODUCTS: list[SkyyRoseProduct] = [
    # ==========================================================================
    # BLACK ROSE Collection - "BLACK IS BEAUTIFUL" Theme
    # ==========================================================================
    SkyyRoseProduct(
        name="BLACK IS BEAUTIFUL Baseball Jersey - Black",
        collection="BLACK_ROSE",
        garment_type="jersey",
        description="Premium black baseball jersey with 'BLACK IS BEAUTIFUL' in white arc lettering across chest. Full button front with silver snap buttons. White piping along button placket and V-neck collar. White stripe bands on sleeves. SkyyRose tag at collar. BLACK ROSE Collection authenticity patch at hem. Mesh athletic fabric.",
        price="$145",
        style_keywords=[
            "baseball jersey",
            "button front",
            "arc lettering",
            "athletic",
            "streetwear",
        ],
        color_palette=["black mesh fabric", "white lettering", "white piping", "silver buttons"],
        reference_image="./assets/reference-images/black-rose/black-jersey.jpg",
    ),
    SkyyRoseProduct(
        name="BLACK IS BEAUTIFUL Giants Jersey - Orange",
        collection="BLACK_ROSE",
        garment_type="jersey",
        description="Premium black baseball jersey with 'BLACK IS BEAUTIFUL' in SF Giants orange arc lettering across chest. Full button front with silver snap buttons. Orange piping along button placket and V-neck collar. Orange stripe bands on sleeves. SkyyRose tag at collar. BLACK ROSE Collection authenticity patch at hem. San Francisco tribute colorway.",
        price="$145",
        style_keywords=[
            "baseball jersey",
            "button front",
            "giants colors",
            "SF tribute",
            "streetwear",
        ],
        color_palette=[
            "black mesh fabric",
            "SF Giants orange lettering",
            "orange piping",
            "silver buttons",
        ],
        reference_image="./assets/reference-images/black-rose/giants-jersey.jpg",
    ),
    SkyyRoseProduct(
        name="Black Rose Sherpa Hooded Jacket",
        collection="BLACK_ROSE",
        garment_type="jacket",
        description="Premium black satin bomber jacket with attached fleece-lined hood. Features embroidered Black Rose logo on left chest - detailed rose emerging from clouds artwork in gray/white thread. Snap button front closure. Ribbed cuffs and hem in black. Satin sheen outer shell. Two side pockets. SkyyRose tag at collar.",
        price="$225",
        style_keywords=[
            "bomber jacket",
            "sherpa hood",
            "satin",
            "embroidered logo",
            "premium outerwear",
        ],
        color_palette=["black satin", "black fleece hood", "gray/white embroidery", "silver snaps"],
        reference_image="./assets/reference-images/black-rose/sherpa-jacket.jpg",
    ),
    SkyyRoseProduct(
        name="Women's Black Rose Hooded Dress",
        collection="BLACK_ROSE",
        garment_type="dress",
        description="Premium black hoodie dress featuring large Black Rose graphic print on front - detailed rose bloom emerging from stylized clouds. Elongated hoodie silhouette with kangaroo pocket. Drawstring hood. Ribbed cuffs. Soft fleece interior. SkyyRose branding. Feminine streetwear.",
        price="$165",
        style_keywords=[
            "hoodie dress",
            "graphic print",
            "feminine streetwear",
            "oversized",
            "rose graphic",
        ],
        color_palette=["black fleece", "gray/white rose print", "black drawstrings"],
        reference_image="./assets/reference-images/black-rose/hooded-dress.jpg",
    ),
    SkyyRoseProduct(
        name="BLACK IS BEAUTIFUL Hockey Hoodie",
        collection="BLACK_ROSE",
        garment_type="hoodie",
        description="Premium black hockey-style hoodie with circular Black Rose logo on chest featuring detailed rose artwork in teal/turquoise accents. 'BLACK IS BEAUTIFUL' text with #0 on front. Teal horizontal stripes at hem and sleeves. Lace-up V-neck detail. Hockey jersey styling with hoodie comfort. Full front and back views shown.",
        price="$195",
        style_keywords=[
            "hockey hoodie",
            "circular logo",
            "teal accents",
            "sports luxe",
            "streetwear",
        ],
        color_palette=["black", "teal/turquoise stripes", "white text", "gray rose artwork"],
        reference_image="./assets/reference-images/black-rose/hockey-hoodie-3d.png",
    ),
    SkyyRoseProduct(
        name="GREEN IS BEAUTIFUL Baseball Jersey",
        collection="BLACK_ROSE",
        garment_type="jersey",
        description="Premium green baseball jersey with 'BLACK IS BEAUTIFUL' in gold/yellow arc lettering. Button front with Oakland A's inspired colorway. Green base with yellow piping and accents. SkyyRose authenticity patch. Oakland tribute piece.",
        price="$145",
        style_keywords=[
            "baseball jersey",
            "oakland colors",
            "A's tribute",
            "green gold",
            "streetwear",
        ],
        color_palette=["green fabric", "gold/yellow lettering", "yellow piping"],
        reference_image="./assets/reference-images/black-rose/green-jersey-crewneck.png",
    ),
    SkyyRoseProduct(
        name="Black Rose Crewneck Sweatshirt",
        collection="BLACK_ROSE",
        garment_type="sweatshirt",
        description="Premium black crewneck sweatshirt with large Black Rose graphic on front - detailed rose bloom with stylized cloud/smoke effect at base. Heavyweight fleece. Ribbed collar, cuffs, and hem. Classic fit. Pairs with shorts.",
        price="$125",
        style_keywords=[
            "crewneck",
            "graphic print",
            "heavyweight fleece",
            "rose artwork",
            "classic fit",
        ],
        color_palette=["black fleece", "gray/white rose print", "cloud effect"],
        reference_image="./assets/reference-images/black-rose/green-jersey-crewneck.png",
    ),
    # ==========================================================================
    # LOVE HURTS Collection - Romantic Streetwear
    # ==========================================================================
    SkyyRoseProduct(
        name="Love Hurts Rose Shorts - Pink",
        collection="LOVE_HURTS",
        garment_type="shorts",
        description="Premium nylon shorts in dusty rose pink with diagonal black panel across front. Embroidered rose patch on left leg - red rose emerging from blue cloud. Elastic waistband with black drawstrings. Lightweight athletic fabric. Relaxed fit.",
        price="$85",
        style_keywords=["athletic shorts", "color block", "rose patch", "nylon", "streetwear"],
        color_palette=["dusty rose pink", "black panel", "red/green rose embroidery"],
        reference_image="./assets/reference-images/love-hurts/pink-shorts.jpg",
    ),
    SkyyRoseProduct(
        name="Love Hurts Rose Shorts - White",
        collection="LOVE_HURTS",
        garment_type="shorts",
        description="Premium nylon shorts in white with diagonal dusty rose panel across front. Embroidered rose patch on left leg - red rose emerging from blue cloud. Elastic waistband with white drawstrings. Lightweight athletic fabric. Relaxed fit.",
        price="$85",
        style_keywords=["athletic shorts", "color block", "rose patch", "nylon", "streetwear"],
        color_palette=["white", "dusty rose panel", "red/green rose embroidery"],
        reference_image="./assets/reference-images/love-hurts/white-shorts.jpg",
    ),
    # ==========================================================================
    # SIGNATURE Collection - Oakland/Bay Area Tribute
    # ==========================================================================
    SkyyRoseProduct(
        name="Bay Bridge Rose T-Shirt - Blue",
        collection="SIGNATURE",
        garment_type="tee",
        description="Premium white t-shirt with Blue Rose graphic on chest - surreal artwork of rose bloom containing Oakland Bay Bridge cityscape. Rose emerges from stylized blue and gray clouds. SR monogram at collar. Relaxed fit premium cotton.",
        price="$95",
        style_keywords=[
            "graphic tee",
            "oakland tribute",
            "bay bridge",
            "blue rose",
            "cityscape art",
        ],
        color_palette=["white tee", "blue rose", "gray/blue clouds", "bay bridge cityscape"],
        reference_image="./assets/reference-images/signature/bay-bridge-set.jpg",
    ),
    SkyyRoseProduct(
        name="Bay Bridge Mesh Shorts - Blue",
        collection="SIGNATURE",
        garment_type="shorts",
        description="Premium mesh athletic shorts with all-over Oakland Bay Bridge cityscape print in blue tones. Elastic waistband with white drawstrings. Blue rose patch on leg. Side mesh panels. Part of Bay Bridge matching set.",
        price="$85",
        style_keywords=[
            "mesh shorts",
            "all-over print",
            "oakland tribute",
            "bay bridge",
            "athletic",
        ],
        color_palette=["blue tones", "bay bridge print", "white drawstrings"],
        reference_image="./assets/reference-images/signature/bay-bridge-set.jpg",
    ),
    SkyyRoseProduct(
        name="Golden Gate Rose T-Shirt - Purple",
        collection="SIGNATURE",
        garment_type="tee",
        description="Premium white t-shirt with Purple/Sunset Rose graphic on chest - surreal artwork of rose bloom containing Golden Gate Bridge at sunset. Rose emerges from stylized dark clouds. SR monogram at collar. Relaxed fit premium cotton.",
        price="$95",
        style_keywords=["graphic tee", "sf tribute", "golden gate", "purple rose", "sunset art"],
        color_palette=["white tee", "purple/orange rose", "dark clouds", "sunset golden gate"],
        reference_image="./assets/reference-images/signature/golden-gate-set.jpg",
    ),
    SkyyRoseProduct(
        name="Golden Gate Mesh Shorts - Purple",
        collection="SIGNATURE",
        garment_type="shorts",
        description="Premium mesh athletic shorts with all-over Golden Gate Bridge sunset print in purple/orange tones. Elastic waistband with white drawstrings. Purple rose patch on leg. Side mesh panels. Part of Golden Gate matching set.",
        price="$85",
        style_keywords=[
            "mesh shorts",
            "all-over print",
            "sf tribute",
            "golden gate",
            "sunset colors",
        ],
        color_palette=["purple/orange tones", "golden gate print", "white drawstrings"],
        reference_image="./assets/reference-images/signature/golden-gate-set.jpg",
    ),
    # ==========================================================================
    # 3D LOGO ASSETS - For Virtual Experiences
    # ==========================================================================
    SkyyRoseProduct(
        name="Love Hurts 3D Logo",
        collection="LOVE_HURTS",
        garment_type="logo",
        description="3D metallic logo featuring cracked/broken red heart wrapped in thorny vines with 'Love Hurts' in elegant script below. Premium metallic finish with depth and shadows. For virtual experience branding.",
        price="N/A",
        style_keywords=["3D logo", "metallic", "broken heart", "thorns", "script lettering"],
        color_palette=["metallic red", "bronze thorns", "dark red script"],
        reference_image="./assets/reference-images/logos/love-hurts-3d.png",
    ),
    SkyyRoseProduct(
        name="SkyyRose SR 3D Logo",
        collection="SIGNATURE",
        garment_type="logo",
        description="3D rose gold metallic logo - elegant SR monogram with decorative rose growing from the letterforms. Premium metallic finish with reflective surfaces. For virtual experience branding.",
        price="N/A",
        style_keywords=["3D logo", "rose gold", "monogram", "SR", "elegant"],
        color_palette=["rose gold metallic"],
        reference_image="./assets/reference-images/logos/skyyrose-sr-3d.png",
    ),
]


# =============================================================================
# Asset Generator
# =============================================================================


class SkyyRoseAssetGenerator:
    """Generates 3D assets for SkyyRose products using multi-provider factory.

    Provider failover chain:
    1. Tripo3D (primary) - Best for fashion/clothing
    2. Replicate (secondary) - Wonder3D, Shap-E models
    3. HuggingFace (fallback) - TripoSR model
    """

    def __init__(self, output_dir: str = "./assets/3d-models-generated") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create collection subdirectories
        for collection in ["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]:
            (self.output_dir / collection.lower().replace("_", "-")).mkdir(exist_ok=True)

        # Use the multi-provider factory with automatic failover
        self.factory = get_provider_factory()
        self.manifest: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "providers": "tripo → replicate → huggingface",
            "output_dir": str(self.output_dir),
            "products": [],
        }

    async def check_health(self) -> dict[str, Any]:
        """Check health of all configured providers."""
        await self.factory.initialize()
        health_results = await self.factory.health_check()

        print("\n" + "=" * 60)
        print("3D Provider Health Status")
        print("=" * 60)

        for name, health in health_results.items():
            status_icon = "✅" if health.is_available else "❌"
            caps = ", ".join(c.value for c in health.capabilities)
            latency = f"{health.latency_ms:.0f}ms" if health.latency_ms else "N/A"

            print(f"\n{status_icon} {name.upper()}")
            print(f"   Status: {health.status.value}")
            print(f"   Capabilities: {caps}")
            print(f"   Latency: {latency}")
            if health.error_message:
                print(f"   Error: {health.error_message}")

        print("\n" + "=" * 60)
        return {name: health.model_dump() for name, health in health_results.items()}

    async def generate_product(
        self,
        product: SkyyRoseProduct,
        reference_image_override: str | None = None,
    ) -> dict[str, Any]:
        """Generate 3D model for a single product using factory with failover.

        Uses image-to-3D when reference image is available (PREFERRED for exact replicas).
        Falls back to text-to-3D when no reference image exists.
        """
        # Check for reference image
        ref_image = reference_image_override or product.reference_image
        has_ref_image = ref_image and Path(ref_image).exists()

        if has_ref_image:
            logger.info(f"🖼️  IMAGE-TO-3D: {product.name} (using reference: {ref_image})")
            generation_mode = "image-to-3d"
        else:
            logger.info(f"📝 TEXT-TO-3D: {product.name} (no reference image)")
            generation_mode = "text-to-3d"

        # Build request - use image_path if reference exists
        request = ThreeDRequest(
            prompt=product.to_prompt(),
            image_path=str(ref_image) if has_ref_image else None,
            product_name=product.name,
            collection=product.collection,
            garment_type=product.garment_type,
            output_format=OutputFormat.GLB,
            quality=QualityLevel.PRODUCTION,
            texture_size=4096,  # Maximum quality for exact replicas
            metadata={
                "description": product.description,
                "price": product.price,
                "style_keywords": product.style_keywords,
                "color_palette": product.color_palette,
                "quality_requirements": "exact_replica_95%_fidelity",
                "generation_mode": generation_mode,
                "reference_image": str(ref_image) if has_ref_image else None,
            },
        )

        try:
            # Use factory.generate() - handles failover automatically
            response = await self.factory.generate(request)

            if response.success:
                # Move file to collection subdirectory
                collection_dir = self.output_dir / product.collection.lower().replace("_", "-")
                if response.model_path:
                    src = Path(response.model_path)
                    if src.exists():
                        dest = collection_dir / f"{product.name.lower().replace(' ', '-')}.glb"
                        src.rename(dest)
                        response.model_path = str(dest)

                result = {
                    "name": product.name,
                    "collection": product.collection,
                    "garment_type": product.garment_type,
                    "price": product.price,
                    "task_id": response.task_id,
                    "model_url": response.model_url,
                    "model_path": response.model_path,
                    "format": response.output_format.value,
                    "provider": response.provider,
                    "duration_seconds": response.duration_seconds,
                    "polycount": response.polycount,
                    "file_size_bytes": response.file_size_bytes,
                    "status": "success",
                    "generated_at": datetime.now(UTC).isoformat(),
                }
                logger.info(f"✅ Generated: {product.name} (provider: {response.provider})")
                return result
            else:
                logger.error(f"❌ Failed: {product.name}: {response.error_message}")
                return {
                    "name": product.name,
                    "collection": product.collection,
                    "status": "failed",
                    "error": response.error_message,
                }

        except Exception as e:
            logger.exception(f"❌ Error generating {product.name}")
            return {
                "name": product.name,
                "collection": product.collection,
                "status": "error",
                "error": str(e),
            }

    async def generate_collection(self, collection: str) -> list[dict[str, Any]]:
        """Generate all products for a collection."""
        products = [p for p in SKYYROSE_PRODUCTS if p.collection == collection]
        logger.info(f"Generating {len(products)} products for {collection}")

        results = []
        for product in products:
            result = await self.generate_product(product)
            results.append(result)
            self.manifest["products"].append(result)

            # Small delay between generations to avoid rate limiting
            await asyncio.sleep(2)

        return results

    async def generate_all(self) -> dict[str, Any]:
        """Generate all products across all collections."""
        logger.info("Generating all SkyyRose products...")
        logger.info("Failover chain: Tripo → Replicate → HuggingFace")

        for collection in ["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]:
            await self.generate_collection(collection)

        return self.manifest

    def save_manifest(self) -> Path:
        """Save the generation manifest."""
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)
        logger.info(f"Saved manifest to {manifest_path}")
        return manifest_path

    async def close(self) -> None:
        """Close provider resources."""
        await self.factory.close()


# =============================================================================
# CLI
# =============================================================================


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate SkyyRose 3D clothing assets with multi-provider failover",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Provider Failover Chain:
  1. Tripo3D (primary) - Best for fashion/clothing
  2. Replicate (secondary) - Wonder3D, Shap-E models
  3. HuggingFace (fallback) - TripoSR model

Environment Variables:
  TRIPO3D_API_KEY      - Tripo3D API token
  REPLICATE_API_TOKEN  - Replicate API token
  HF_TOKEN             - HuggingFace API token

Examples:
  python scripts/generate_skyyrose_assets.py --health
  python scripts/generate_skyyrose_assets.py --collection BLACK_ROSE
  python scripts/generate_skyyrose_assets.py --product "Thorn Hoodie"
  python scripts/generate_skyyrose_assets.py --all
""",
    )
    parser.add_argument(
        "--collection",
        choices=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
        help="Generate products for a specific collection",
    )
    parser.add_argument(
        "--product",
        type=str,
        help="Generate a specific product by name",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all products",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./assets/3d-models-generated",
        help="Output directory for generated models",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available products",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check health of all 3D providers",
    )

    args = parser.parse_args()

    # List products
    if args.list:
        print("\n" + "=" * 60)
        print("SkyyRose Product Catalog - EXACT REPLICA 3D ASSETS")
        print("=" * 60)
        for collection in ["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]:
            print(f"\n🌹 {collection.replace('_', ' ')} Collection:")
            for p in SKYYROSE_PRODUCTS:
                if p.collection == collection:
                    print(f"   • {p.name} ({p.garment_type}) - {p.price}")
        print("\n" + "=" * 60)
        print(f"Total: {len(SKYYROSE_PRODUCTS)} products across 3 collections")
        return 0

    # Check for at least one API key
    has_tripo = bool(os.getenv("TRIPO3D_API_KEY"))
    has_replicate = bool(os.getenv("REPLICATE_API_TOKEN"))
    has_hf = bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY"))

    if not (has_tripo or has_replicate or has_hf):
        logger.error("No 3D provider API keys found!")
        logger.error("Set at least one of: TRIPO3D_API_KEY, REPLICATE_API_TOKEN, HF_TOKEN")
        return 1

    # Show available providers
    print("\n🔑 Available providers:")
    if has_tripo:
        print("   ✅ Tripo3D")
    if has_replicate:
        print("   ✅ Replicate (Wonder3D, Shap-E)")
    if has_hf:
        print("   ✅ HuggingFace (TripoSR)")
    print()

    generator = SkyyRoseAssetGenerator(output_dir=args.output_dir)

    try:
        # Health check
        if args.health:
            await generator.check_health()
            return 0

        if args.all:
            await generator.generate_all()
        elif args.collection:
            await generator.generate_collection(args.collection)
        elif args.product:
            product = next(
                (p for p in SKYYROSE_PRODUCTS if p.name.lower() == args.product.lower()), None
            )
            if not product:
                logger.error(f"Product not found: {args.product}")
                logger.info("Use --list to see all available products")
                return 1
            result = await generator.generate_product(product)
            generator.manifest["products"].append(result)
        else:
            parser.print_help()
            return 0

        generator.save_manifest()

        # Print summary
        successful = len(
            [p for p in generator.manifest["products"] if p.get("status") == "success"]
        )
        total = len(generator.manifest["products"])

        print("\n" + "=" * 60)
        print("GENERATION SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful}/{total}")
        print(f"📁 Output: {generator.output_dir}")
        print(f"📋 Manifest: {generator.output_dir}/manifest.json")

        if successful < total:
            failed = [p for p in generator.manifest["products"] if p.get("status") != "success"]
            print("\n❌ Failed products:")
            for p in failed:
                print(f"   • {p['name']}: {p.get('error', 'unknown error')}")

        print("=" * 60)

        return 0 if successful == total else 1

    finally:
        await generator.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
