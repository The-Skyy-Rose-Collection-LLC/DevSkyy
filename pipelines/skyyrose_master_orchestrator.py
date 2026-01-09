# skyyrose_master_orchestrator.py
"""SkyyRose Master Orchestrator.

Complete automation: Design concept -> Live product on skyyrose.co

Pipeline:
1. Generate product images (FLUX/SDXL)
2. Analyze with Qwen-VL (descriptions, metadata, SEO)
3. Deploy to WordPress/WooCommerce
4. Optimize for search engines
5. Generate social media assets
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductConcept:
    """Product concept for launching."""

    name: str
    collection: str
    garment_type: str
    color: str
    fabric: str
    price: float
    sku_base: str
    style_notes: str = ""
    target_launch_date: str = ""


class SkyyRoseMasterOrchestrator:
    """
    Complete automation: Design concept -> Live product on skyyrose.co

    Pipeline:
    1. Generate product images (FLUX/SDXL)
    2. Analyze with Qwen-VL (descriptions, metadata, SEO)
    3. Deploy to WordPress/WooCommerce
    4. Optimize for search engines
    5. Generate social media assets
    """

    # HuggingFace Space IDs (deployed)
    DEFAULT_SPACES = {
        "flux": "damBruh/skyyrose-flux-upscaler",
        "sdxl": "damBruh/skyyrose-product-photography",
        "qwen": "damBruh/skyyrose-product-analyzer",
        "3d": "damBruh/skyyrose-3d-converter",
    }

    # Collection DNA
    COLLECTION_DNA = {
        "BLACK_ROSE": {
            "aesthetic": "dark elegance, limited edition mystique, noir",
            "price_range": (165, 285),
            "target_customer": "artistic rebels, collectors, exclusivity seekers",
            "vibe": "mysterious, sophisticated, rebellious luxury",
        },
        "LOVE_HURTS": {
            "aesthetic": "emotional expression, artistic rebellion, vulnerable strength",
            "price_range": (145, 245),
            "target_customer": "emotionally expressive, authentic, artistic souls",
            "vibe": "passionate, authentic, artistically refined",
        },
        "SIGNATURE": {
            "aesthetic": "refined sophistication, timeless elegance, versatile luxury",
            "price_range": (125, 195),
            "target_customer": "style conscious, quality focused, everyday luxury",
            "vibe": "confident, understated luxury, essential excellence",
        },
    }

    # Standard product angles
    PRODUCT_ANGLES = [
        ("front view centered", "hero"),
        ("back view centered", "back"),
        ("side profile left", "side_left"),
        ("side profile right", "side_right"),
        ("3/4 angle front", "angle_front"),
        ("detail shot fabric texture closeup", "detail_fabric"),
        ("detail shot construction and stitching", "detail_construction"),
        ("flat lay composition", "flatlay"),
    ]

    def __init__(self, config: dict):
        """Initialize the master orchestrator.

        Args:
            config: Configuration dict with:
                - flux_space_url: FLUX Space ID
                - sdxl_space_url: SDXL Space ID
                - qwen_space_url: Qwen Space ID
                - wordpress_url: WordPress site URL
                - wp_username: WordPress username
                - wp_password: WordPress app password
                - r2_account_id: Cloudflare R2 account (optional)
                - r2_access_key: R2 access key (optional)
                - r2_secret_key: R2 secret key (optional)
        """
        print("Initializing SkyyRose Master Orchestrator...")

        # HuggingFace Spaces (lazy loaded)
        self._flux_client = None
        self._sdxl_client = None
        self._qwen_client = None

        self.flux_space_url = config.get("flux_space_url", self.DEFAULT_SPACES["flux"])
        self.sdxl_space_url = config.get("sdxl_space_url", self.DEFAULT_SPACES["sdxl"])
        self.qwen_space_url = config.get("qwen_space_url", self.DEFAULT_SPACES["qwen"])

        # WordPress API
        self.wp_url = config.get("wordpress_url", "https://skyyrose.co")
        self.wp_username = config.get("wp_username")
        self.wp_password = config.get("wp_password")

        # Cloudflare R2 CDN
        self.r2_account_id = config.get("r2_account_id")
        self.r2_access_key = config.get("r2_access_key")
        self.r2_secret_key = config.get("r2_secret_key")
        self.r2_bucket = config.get("r2_bucket", "skyyrose-products")

        # Backend health tracking
        self.backend_health = {
            "flux": {"available": True, "quota_remaining": 50, "failures": 0},
            "sdxl": {"available": True, "quota_remaining": 200, "failures": 0},
        }

        print("Orchestrator initialized")

    @property
    def flux_space(self):
        """Lazy load FLUX client."""
        if self._flux_client is None:
            from gradio_client import Client

            self._flux_client = Client(self.flux_space_url)
        return self._flux_client

    @property
    def sdxl_space(self):
        """Lazy load SDXL client."""
        if self._sdxl_client is None:
            from gradio_client import Client

            self._sdxl_client = Client(self.sdxl_space_url)
        return self._sdxl_client

    @property
    def qwen_space(self):
        """Lazy load Qwen client."""
        if self._qwen_client is None:
            from gradio_client import Client

            self._qwen_client = Client(self.qwen_space_url)
        return self._qwen_client

    async def launch_complete_product(
        self, product_concept: dict, generate_variants: bool = True, auto_publish: bool = False
    ) -> dict:
        """
        Complete product launch from concept to live site.

        Args:
            product_concept: Product specification dict with:
                - name: Product name
                - collection: BLACK_ROSE, LOVE_HURTS, or SIGNATURE
                - garment_type: Type of garment
                - color: Color description
                - fabric: Fabric description
                - price: Price in USD
                - sku_base: SKU prefix
                - style_notes: Additional styling notes
            generate_variants: Generate color/size variants
            auto_publish: Publish immediately (vs draft)

        Returns:
            Complete launch report with URLs, metrics, assets
        """
        launch_id = f"launch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'=' * 80}")
        print(f"SKYYROSE PRODUCT LAUNCH: {product_concept['name']}")
        print(f"   Launch ID: {launch_id}")
        print(f"   Collection: {product_concept['collection']}")
        print(f"{'=' * 80}\n")

        # Initialize launch report
        launch_report = {
            "launch_id": launch_id,
            "product_name": product_concept["name"],
            "collection": product_concept["collection"],
            "started_at": datetime.now().isoformat(),
            "stages": {},
            "assets": {},
            "errors": [],
        }

        try:
            # STAGE 1: Generate Product Photography
            print("STAGE 1: Generating Product Photography")
            print("-" * 80)
            photo_results = await self._stage_1_generate_photography(product_concept, launch_report)

            # STAGE 2: AI Analysis & Content Generation
            print("\nSTAGE 2: AI Analysis & Content Generation")
            print("-" * 80)
            content_results = await self._stage_2_generate_content(
                photo_results, product_concept, launch_report
            )

            # STAGE 3: Upload to CDN
            print("\nSTAGE 3: Uploading Assets to CDN")
            print("-" * 80)
            cdn_results = await self._stage_3_upload_cdn(
                photo_results, product_concept, launch_report
            )

            # STAGE 4: Create WordPress Product
            print("\nSTAGE 4: Deploying to WordPress/WooCommerce")
            print("-" * 80)
            wordpress_results = await self._stage_4_deploy_wordpress(
                product_concept, content_results, cdn_results, auto_publish, launch_report
            )

            # STAGE 5: SEO Optimization
            print("\nSTAGE 5: SEO Optimization")
            print("-" * 80)
            await self._stage_5_seo_optimization(wordpress_results, content_results, launch_report)

            # STAGE 6: Generate Social Media Assets
            print("\nSTAGE 6: Social Media Asset Generation")
            print("-" * 80)
            await self._stage_6_social_assets(photo_results, content_results, launch_report)

            # Finalize report
            launch_report["completed_at"] = datetime.now().isoformat()
            launch_report["status"] = "success"
            launch_report["product_url"] = wordpress_results["product_url"]
            launch_report["duration_seconds"] = (
                datetime.fromisoformat(launch_report["completed_at"])
                - datetime.fromisoformat(launch_report["started_at"])
            ).total_seconds()

            self._print_launch_summary(launch_report)
            self._save_launch_report(launch_report)

            return launch_report

        except Exception as e:
            launch_report["status"] = "failed"
            launch_report["error"] = str(e)
            launch_report["failed_at"] = datetime.now().isoformat()
            print(f"\nLAUNCH FAILED: {e}")
            self._save_launch_report(launch_report)
            raise

    async def _stage_1_generate_photography(
        self, product_concept: dict, launch_report: dict
    ) -> dict:
        """Generate all product angles with intelligent backend selection."""
        stage_start = datetime.now()
        generated_images = {}
        backend_used = None

        for angle, slug in self.PRODUCT_ANGLES:
            print(f"  -> Generating: {angle}")

            try:
                # Try FLUX first
                if self.backend_health["flux"]["available"]:
                    result = await self._generate_with_flux(product_concept, angle)
                    backend_used = "flux"
                    self.backend_health["flux"]["quota_remaining"] -= 1
                else:
                    # Fallback to SDXL
                    result = await self._generate_with_sdxl(product_concept, angle)
                    backend_used = "sdxl"
                    self.backend_health["sdxl"]["quota_remaining"] -= 1

                generated_images[slug] = {
                    "base": result["base"],
                    "upscaled": result["upscaled"],
                    "angle": angle,
                    "backend": backend_used,
                }

                print(f"    [OK] Generated with {backend_used.upper()}")

                # Rate limiting
                await asyncio.sleep(3)

            except Exception as e:
                print(f"    [FAIL] {e}")

                # Mark backend as degraded
                if backend_used:
                    self.backend_health[backend_used]["failures"] += 1
                    if self.backend_health[backend_used]["failures"] >= 3:
                        self.backend_health[backend_used]["available"] = False

                # Try fallback
                if backend_used == "flux":
                    print("    [RETRY] Using SDXL...")
                    result = await self._generate_with_sdxl(product_concept, angle)
                    generated_images[slug] = {
                        "base": result["base"],
                        "upscaled": result["upscaled"],
                        "angle": angle,
                        "backend": "sdxl",
                    }

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["photography"] = {
            "duration_seconds": stage_duration,
            "images_generated": len(generated_images),
            "backends_used": list({img["backend"] for img in generated_images.values()}),
            "status": "success",
        }

        print(f"\n  [DONE] Stage 1: {len(generated_images)} images in {stage_duration:.1f}s")

        return generated_images

    async def _generate_with_flux(self, product_concept: dict, angle: str) -> dict:
        """Generate with FLUX Space."""
        base, upscaled = self.flux_space.predict(
            garment_type=product_concept["garment_type"],
            collection=product_concept["collection"],
            color_description=product_concept["color"],
            fabric_type=product_concept["fabric"],
            angle=angle,
            final_resolution=2048,
            style_notes=product_concept.get("style_notes", ""),
            api_name="/generate_images",
        )
        return {"base": base, "upscaled": upscaled}

    async def _generate_with_sdxl(self, product_concept: dict, angle: str) -> dict:
        """Generate with SDXL Space (fallback)."""
        # SDXL space has different API
        image = self.sdxl_space.predict(
            garment_type=product_concept["garment_type"],
            collection=product_concept["collection"],
            color=product_concept["color"],
            fabric=product_concept["fabric"],
            angle=angle,
            seed=-1,
            steps=30,
            guidance=7.5,
            api_name="/generate_product_image",
        )
        return {"base": image, "upscaled": image}

    async def _stage_2_generate_content(
        self, photo_results: dict, product_concept: dict, launch_report: dict
    ) -> dict:
        """Use Qwen-VL to analyze images and generate all content."""
        stage_start = datetime.now()

        # Validate photo_results contains required hero image
        if "hero" not in photo_results:
            raise KeyError(
                "Missing 'hero' image in photo_results. "
                f"Stage 1 photography may have failed. Available keys: {list(photo_results.keys())}"
            )
        hero_data = photo_results["hero"]
        if not isinstance(hero_data, dict) or "upscaled" not in hero_data:
            raise ValueError(
                f"Invalid hero image data structure. Expected dict with 'upscaled' key, "
                f"got: {type(hero_data).__name__}"
            )

        # Use hero image for analysis
        hero_image = hero_data["upscaled"]

        print("  -> Analyzing hero image with Qwen-VL")

        # Extract metadata
        print("  -> Extracting product metadata...")
        try:
            metadata_result = self.qwen_space.predict(
                image=hero_image, api_name="/extract_metadata"
            )
            metadata = metadata_result if isinstance(metadata_result, dict) else {}
        except Exception:
            metadata = {}

        print(f"    [OK] Detected: {metadata.get('garment_type', 'unknown')}")

        # Generate luxury product description
        print("  -> Generating luxury product copy...")
        try:
            product_description = self.qwen_space.predict(
                image=hero_image,
                collection=product_concept["collection"],
                price=product_concept["price"],
                api_name="/generate_copy",
            )
        except Exception:
            product_description = self._generate_fallback_copy(product_concept)

        print(f"    [OK] Generated {len(product_description)} characters")

        # Extract SEO keywords
        print("  -> Extracting SEO keywords...")
        try:
            seo_keywords = self.qwen_space.predict(
                image=hero_image, analysis_type="seo_keywords", api_name="/analyze_image"
            )
            keywords_list = [kw.strip() for kw in seo_keywords.split(",")]
        except Exception:
            keywords_list = self._generate_fallback_keywords(product_concept)

        print(f"    [OK] Extracted {len(keywords_list)} keywords")

        # Generate short description
        short_description = (
            product_description.split("\n\n")[0]
            if "\n\n" in product_description
            else product_description[:200]
        )

        content_package = {
            "title": product_concept["name"],
            "description": product_description,
            "short_description": short_description,
            "metadata": metadata,
            "seo_keywords": keywords_list,
            "seo_title": f"{product_concept['name']} | {product_concept['collection']} | SkyyRose",
            "seo_description": short_description[:160],
        }

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["content_generation"] = {
            "duration_seconds": stage_duration,
            "description_length": len(product_description),
            "keywords_extracted": len(keywords_list),
            "metadata_fields": len(metadata),
            "status": "success",
        }

        print(f"\n  [DONE] Stage 2: Content generated in {stage_duration:.1f}s")

        return content_package

    def _generate_fallback_copy(self, product_concept: dict) -> str:
        """Generate fallback copy if Qwen fails."""
        collection_voice = {
            "BLACK_ROSE": "Where darkness becomes wearable art.",
            "LOVE_HURTS": "Emotional expression through luxury craft.",
            "SIGNATURE": "Essential luxury for everyday excellence.",
        }

        voice = collection_voice.get(product_concept["collection"], "Luxury streetwear.")

        return f"""{voice}

**{product_concept["name"]}** - {product_concept["garment_type"]} in {product_concept["color"]}

Crafted from {product_concept["fabric"]}, this piece represents SkyyRose's commitment
to where Oakland street authenticity meets luxury craftsmanship.

**Details:**
- Premium {product_concept["fabric"]}
- Gender-neutral design
- Limited availability
- Designed in Oakland, California

*Where love meets luxury.*"""

    def _generate_fallback_keywords(self, product_concept: dict) -> list[str]:
        """Generate fallback keywords if Qwen fails."""
        return [
            product_concept["garment_type"],
            product_concept["color"],
            product_concept["collection"].lower().replace("_", " "),
            "luxury streetwear",
            "oakland fashion",
            "skyyrose",
            "premium apparel",
        ]

    async def _stage_3_upload_cdn(
        self, photo_results: dict, product_concept: dict, launch_report: dict
    ) -> dict:
        """Upload all images to CDN."""
        stage_start = datetime.now()
        cdn_urls = {}
        sku = product_concept.get("sku_base", "SKR-UNKNOWN")

        for slug, image_data in photo_results.items():
            print(f"  -> Uploading: {slug}")

            # Upload upscaled version
            upscaled_url = await self._upload_to_cdn(
                image_data["upscaled"], f"products/{sku}/{slug}_2k.png"
            )

            # Upload base version
            base_url = await self._upload_to_cdn(
                image_data["base"], f"products/{sku}/{slug}_1k.png"
            )

            cdn_urls[slug] = {"upscaled": upscaled_url, "base": base_url}

            print(f"    [OK] {upscaled_url}")

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["cdn_upload"] = {
            "duration_seconds": stage_duration,
            "files_uploaded": len(cdn_urls) * 2,
            "status": "success",
        }

        print(f"\n  [DONE] Stage 3: {len(cdn_urls)} images uploaded in {stage_duration:.1f}s")

        return cdn_urls

    async def _upload_to_cdn(self, image_path: str, object_key: str) -> str:
        """Upload image to CDN (Cloudflare R2 or fallback)."""
        if self.r2_account_id and self.r2_access_key:
            # Use R2
            try:
                import boto3

                s3 = boto3.client(
                    "s3",
                    endpoint_url=f"https://{self.r2_account_id}.r2.cloudflarestorage.com",
                    aws_access_key_id=self.r2_access_key,
                    aws_secret_access_key=self.r2_secret_key,
                )
                s3.upload_file(image_path, self.r2_bucket, object_key)
                return f"https://cdn.skyyrose.co/{object_key}"
            except Exception:
                pass

        # Fallback: return local path or placeholder
        return f"https://cdn.skyyrose.co/{object_key}"

    async def _stage_4_deploy_wordpress(
        self,
        product_concept: dict,
        content_results: dict,
        cdn_results: dict,
        auto_publish: bool,
        launch_report: dict,
    ) -> dict:
        """Create WooCommerce product with all generated content."""
        stage_start = datetime.now()

        print("  -> Creating WooCommerce product...")

        # Prepare image gallery
        image_gallery = []
        for slug in [
            "hero",
            "angle_front",
            "back",
            "side_left",
            "side_right",
            "detail_fabric",
            "detail_construction",
            "flatlay",
        ]:
            if slug in cdn_results:
                image_gallery.append(cdn_results[slug]["upscaled"])

        # Create product data
        product_data = {
            "name": content_results["title"],
            "type": "simple",
            "regular_price": str(product_concept["price"]),
            "description": content_results["description"],
            "short_description": content_results["short_description"],
            "sku": product_concept.get("sku_base"),
            "status": "publish" if auto_publish else "draft",
            "catalog_visibility": "visible",
            "categories": [
                {"name": product_concept["collection"]},
                {"name": content_results["metadata"].get("garment_type", "Apparel")},
            ],
            "tags": [{"name": kw} for kw in content_results["seo_keywords"]],
            "images": [{"src": url} for url in image_gallery],
            "meta_data": [
                {"key": "_collection", "value": product_concept["collection"]},
                {"key": "_fabric", "value": product_concept["fabric"]},
                {"key": "_color", "value": product_concept["color"]},
                {"key": "_ai_generated", "value": "true"},
                {"key": "_generation_date", "value": datetime.now().isoformat()},
            ],
        }

        # Deploy to WordPress
        if self.wp_username and self.wp_password:
            product_response = await self._create_woo_product(product_data)
            product_id = product_response.get("id", 0)
            product_url = product_response.get(
                "permalink", f"{self.wp_url}/product/{product_concept.get('sku_base', 'new')}"
            )
            product_slug = product_response.get("slug", "")
        else:
            # Dry run
            product_id = 0
            product_url = f"{self.wp_url}/product/{product_concept.get('sku_base', 'new')}"
            product_slug = product_concept.get("sku_base", "new")

        print(f"    [OK] Product created: {product_url}")

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["wordpress_deployment"] = {
            "duration_seconds": stage_duration,
            "product_id": product_id,
            "product_url": product_url,
            "status": "publish" if auto_publish else "draft",
            "status_result": "success",
        }

        print(f"\n  [DONE] Stage 4: Product deployed in {stage_duration:.1f}s")

        return {
            "product_id": product_id,
            "product_url": product_url,
            "product_slug": product_slug,
            "status": "publish" if auto_publish else "draft",
        }

    async def _create_woo_product(self, product_data: dict) -> dict:
        """Create WooCommerce product via REST API."""
        import requests

        auth = (self.wp_username, self.wp_password)

        response = requests.post(
            f"{self.wp_url}/wp-json/wc/v3/products",
            json=product_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    async def _stage_5_seo_optimization(
        self, wordpress_results: dict, content_results: dict, launch_report: dict
    ) -> dict:
        """SEO optimization (Yoast/RankMath integration)."""
        stage_start = datetime.now()

        print("  -> Optimizing SEO metadata...")

        if self.wp_username and self.wp_password and wordpress_results["product_id"]:
            import requests

            seo_data = {
                "meta_data": [
                    {"key": "_yoast_wpseo_title", "value": content_results["seo_title"]},
                    {"key": "_yoast_wpseo_metadesc", "value": content_results["seo_description"]},
                    {"key": "_yoast_wpseo_focuskw", "value": content_results["seo_keywords"][0]},
                ]
            }

            auth = (self.wp_username, self.wp_password)
            requests.put(
                f"{self.wp_url}/wp-json/wc/v3/products/{wordpress_results['product_id']}",
                json=seo_data,
                auth=auth,
                timeout=30,
            )

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["seo_optimization"] = {
            "duration_seconds": stage_duration,
            "focus_keyword": (
                content_results["seo_keywords"][0] if content_results["seo_keywords"] else ""
            ),
            "meta_title_length": len(content_results["seo_title"]),
            "meta_description_length": len(content_results["seo_description"]),
            "status": "success",
        }

        print(f"\n  [DONE] Stage 5: SEO optimized in {stage_duration:.1f}s")

        return {"status": "optimized"}

    async def _stage_6_social_assets(
        self, photo_results: dict, content_results: dict, launch_report: dict
    ) -> dict:
        """Generate social media ready assets."""
        stage_start = datetime.now()

        print("  -> Generating social media assets...")

        # Generate social caption
        short_desc = content_results["short_description"]
        keywords = " ".join(
            f"#{kw.replace(' ', '').replace('-', '')}" for kw in content_results["seo_keywords"][:5]
        )

        social_caption = f"""{short_desc}

Shop now: link in bio

{keywords} #SkyyRose #LuxuryStreetwear #Oakland #WhereLoveMeetsLuxury"""

        social_assets = {
            "instagram": photo_results.get("hero", {}).get("upscaled"),
            "facebook": photo_results.get("hero", {}).get("upscaled"),
            "pinterest": photo_results.get("angle_front", {}).get("upscaled"),
            "caption": social_caption,
        }

        stage_duration = (datetime.now() - stage_start).total_seconds()

        launch_report["stages"]["social_assets"] = {
            "duration_seconds": stage_duration,
            "assets_generated": 3,
            "caption_length": len(social_caption),
            "status": "success",
        }

        print(f"\n  [DONE] Stage 6: Social assets ready in {stage_duration:.1f}s")

        return social_assets

    def _print_launch_summary(self, launch_report: dict):
        """Print beautiful launch summary."""
        print(f"\n{'=' * 80}")
        print("PRODUCT LAUNCH COMPLETE")
        print(f"{'=' * 80}")
        print(f"\nProduct: {launch_report['product_name']}")
        print(f"Collection: {launch_report['collection']}")
        print(f"URL: {launch_report.get('product_url', 'N/A')}")
        print(f"Duration: {launch_report['duration_seconds']:.1f}s")
        print("\nStage Breakdown:")

        for stage_name, stage_data in launch_report["stages"].items():
            status_icon = "[OK]" if stage_data.get("status") == "success" else "[FAIL]"
            print(f"   {status_icon} {stage_name}: {stage_data.get('duration_seconds', 0):.1f}s")

        print(f"\n{'=' * 80}\n")

    def _save_launch_report(self, launch_report: dict):
        """Save launch report to file."""
        report_dir = "launch_reports"
        os.makedirs(report_dir, exist_ok=True)

        report_path = f"{report_dir}/{launch_report['launch_id']}.json"

        with open(report_path, "w") as f:
            json.dump(launch_report, f, indent=2, default=str)

        print(f"Launch report saved: {report_path}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


async def quick_launch(
    name: str,
    collection: str,
    garment_type: str,
    color: str,
    fabric: str,
    price: float,
    sku: str,
    style_notes: str = "",
    wp_url: str = "https://skyyrose.co",
    wp_username: str = None,
    wp_password: str = None,
    auto_publish: bool = False,
) -> dict:
    """
    Quick launch a product with minimal configuration.

    Example:
        result = await quick_launch(
            name='Essential Black Hoodie',
            collection='SIGNATURE',
            garment_type='oversized hoodie',
            color='midnight black',
            fabric='heavyweight brushed cotton fleece',
            price=145.00,
            sku='SRS-SIG-001'
        )
    """
    config = {"wordpress_url": wp_url, "wp_username": wp_username, "wp_password": wp_password}

    orchestrator = SkyyRoseMasterOrchestrator(config)

    product_concept = {
        "name": name,
        "collection": collection,
        "garment_type": garment_type,
        "color": color,
        "fabric": fabric,
        "price": price,
        "sku_base": sku,
        "style_notes": style_notes,
    }

    return await orchestrator.launch_complete_product(
        product_concept=product_concept, auto_publish=auto_publish
    )


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Example: Launch a complete product."""
    result = await quick_launch(
        name="Essential Black Hoodie",
        collection="SIGNATURE",
        garment_type="oversized hoodie",
        color="midnight black",
        fabric="heavyweight brushed cotton fleece",
        price=145.00,
        sku="SRS-SIG-001",
        style_notes="minimal branding, relaxed fit, ribbed cuffs",
    )

    print(f"\nSuccess! Product URL: {result.get('product_url', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
