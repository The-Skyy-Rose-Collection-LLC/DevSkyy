# services/ml/image_description_pipeline.py
"""Image-to-description pipeline using vision models.

Implements US-029: Image-to-description pipeline.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from services.ml.prompts.vision_prompts import (
    BULLET_POINTS_PROMPT,
    SEO_PROMPT,
    TAGS_PROMPT,
    get_description_prompt,
    get_feature_prompt,
)
from services.ml.schemas.description import (
    BatchDescriptionOutput,
    BatchDescriptionRequest,
    BulletPoint,
    ColorInfo,
    DescriptionOutput,
    DescriptionRequest,
    ExtractedFeatures,
    FeatureExtractionRequest,
    MaterialInfo,
    SEOContent,
    StyleAttributes,
    VisionModel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Vision Model Client
# =============================================================================


class VisionModelClient:
    """Client for calling vision models via Replicate."""

    # Model endpoints on Replicate
    MODEL_ENDPOINTS = {
        VisionModel.LLAVA_34B: "yorickvp/llava-v1.6-34b:41ecfbfb261e6c1adf3ad896c9066ca98346996d7c4045c5bc944a79d430f174",
        VisionModel.LLAVA_13B: "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddce3f3ed7ee5ad76f7be1c8b0a6c9c5db2e4",
        VisionModel.BLIP2: "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
    }

    def __init__(self, replicate_api_token: str | None = None) -> None:
        """Initialize vision model client.

        Args:
            replicate_api_token: Replicate API token (uses env var if not provided)
        """
        self._api_token = replicate_api_token
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Replicate client."""
        if self._client is None:
            try:
                import replicate

                self._client = replicate
            except ImportError as e:
                raise ImportError(
                    "replicate package required. Install with: pip install replicate"
                ) from e
        return self._client

    async def generate(
        self,
        model: VisionModel,
        image_url: str,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from image using vision model.

        Args:
            model: Vision model to use
            image_url: URL of image to analyze
            prompt: Text prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        client = await self._get_client()

        model_version = self.MODEL_ENDPOINTS.get(model)
        if not model_version:
            raise ValueError(f"Unknown model: {model}")

        try:
            # Run model with image and prompt
            output = await asyncio.to_thread(
                client.run,
                model_version,
                input={
                    "image": image_url,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            # Handle different output formats
            if isinstance(output, list):
                return "".join(output)
            return str(output)

        except Exception as e:
            logger.error(f"Vision model error: {e}")
            raise

    async def health_check(self, model: VisionModel) -> bool:
        """Check if model is available.

        Args:
            model: Model to check

        Returns:
            True if model is available
        """
        try:
            client = await self._get_client()
            model_version = self.MODEL_ENDPOINTS.get(model)
            if not model_version:
                return False

            # Check model exists (doesn't actually run it)
            model_id = model_version.split(":")[0]
            await asyncio.to_thread(client.models.get, model_id)
            return True
        except Exception:
            return False


# =============================================================================
# Image Description Pipeline
# =============================================================================


class ImageDescriptionPipeline:
    """Pipeline for generating product descriptions from images."""

    def __init__(
        self,
        vision_client: VisionModelClient | None = None,
        default_model: VisionModel = VisionModel.LLAVA_34B,
        fallback_model: VisionModel = VisionModel.BLIP2,
    ) -> None:
        """Initialize pipeline.

        Args:
            vision_client: Vision model client (creates default if not provided)
            default_model: Primary model to use
            fallback_model: Fallback model if primary fails
        """
        self._vision_client = vision_client or VisionModelClient()
        self._default_model = default_model
        self._fallback_model = fallback_model

    async def generate_description(
        self,
        request: DescriptionRequest,
    ) -> DescriptionOutput:
        """Generate complete description from image.

        Args:
            request: Description request parameters

        Returns:
            Complete description output
        """
        start_time = time.time()
        model_used = request.model

        try:
            # Convert HttpUrl to string for API calls
            image_url = str(request.image_url)

            # Step 1: Extract features (parallel with description)
            features_task = None
            if request.include_bullets or request.include_tags:
                features_task = asyncio.create_task(
                    self._extract_features(image_url, request.model)
                )

            # Step 2: Generate main description
            description_prompt = get_description_prompt(
                style=request.style,
                product_type=request.product_type,
                word_count=request.target_word_count,
                brand_context=request.brand_context,
            )

            description = await self._generate_with_fallback(
                image_url,
                description_prompt,
                request.model,
            )

            # Step 3: Generate short description
            short_description = await self._generate_short_description(
                image_url,
                request.model,
            )

            # Step 4: Get features result
            features = None
            if features_task:
                features = await features_task

            # Step 5: Generate bullet points
            bullet_points: list[BulletPoint] = []
            if request.include_bullets:
                bullet_points = await self._generate_bullet_points(
                    image_url,
                    request.model,
                )

            # Step 6: Generate SEO content
            seo = None
            if request.include_seo:
                seo = await self._generate_seo_content(
                    image_url,
                    request.product_type,
                    request.brand_context,
                    request.model,
                )

            # Step 7: Generate tags
            tags: list[str] = []
            if request.include_tags:
                tags = await self._generate_tags(
                    image_url,
                    request.model,
                )

            processing_time = int((time.time() - start_time) * 1000)

            return DescriptionOutput(
                image_url=image_url,
                product_name=request.product_name,
                description=description,
                short_description=short_description,
                bullet_points=bullet_points,
                suggested_tags=tags,
                seo=seo,
                features=features,
                model_used=model_used.value,
                word_count=len(description.split()),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            raise

    async def generate_batch(
        self,
        request: BatchDescriptionRequest,
        *,
        max_concurrent: int = 5,
    ) -> BatchDescriptionOutput:
        """Generate descriptions for multiple images.

        Args:
            request: Batch request with multiple images
            max_concurrent: Maximum concurrent requests

        Returns:
            Batch output with results and errors
        """
        output = BatchDescriptionOutput(total=len(request.requests))

        # Process in batches with semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_one(req: DescriptionRequest, index: int) -> None:
            async with semaphore:
                try:
                    result = await self.generate_description(req)
                    output.results.append(result)
                    output.completed += 1
                except Exception as e:
                    output.errors.append({
                        "index": index,
                        "image_url": req.image_url,
                        "error": str(e),
                    })
                    output.failed += 1

        # Run all tasks
        tasks = [
            process_one(req, i)
            for i, req in enumerate(request.requests)
        ]
        await asyncio.gather(*tasks)

        return output

    async def extract_features(
        self,
        request: FeatureExtractionRequest,
    ) -> ExtractedFeatures:
        """Extract visual features from image.

        Args:
            request: Feature extraction request

        Returns:
            Extracted features
        """
        return await self._extract_features(
            str(request.image_url),
            request.model,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _generate_with_fallback(
        self,
        image_url: str,
        prompt: str,
        model: VisionModel,
    ) -> str:
        """Generate with automatic fallback on failure.

        Args:
            image_url: Image URL
            prompt: Prompt to use
            model: Primary model

        Returns:
            Generated text
        """
        try:
            return await self._vision_client.generate(
                model=model,
                image_url=image_url,
                prompt=prompt,
            )
        except Exception as e:
            logger.warning(f"Primary model {model} failed: {e}, trying fallback")
            return await self._vision_client.generate(
                model=self._fallback_model,
                image_url=image_url,
                prompt=prompt,
            )

    async def _generate_short_description(
        self,
        image_url: str,
        model: VisionModel,
    ) -> str:
        """Generate short description.

        Args:
            image_url: Image URL
            model: Vision model

        Returns:
            Short description (< 50 words)
        """
        prompt = """Analyze this product image and write a short, compelling description in under 50 words.
Focus on the key selling point and overall aesthetic.
Be concise and impactful."""

        return await self._generate_with_fallback(image_url, prompt, model)

    async def _extract_features(
        self,
        image_url: str,
        model: VisionModel,
    ) -> ExtractedFeatures:
        """Extract visual features from image.

        Args:
            image_url: Image URL
            model: Vision model

        Returns:
            Extracted features
        """
        prompt = get_feature_prompt()
        response = await self._generate_with_fallback(image_url, prompt, model)

        try:
            # Parse JSON response
            data = json.loads(response)

            colors = [
                ColorInfo(
                    name=c.get("name", ""),
                    category=c.get("category", "neutral"),
                    prominence=float(c.get("prominence", 0.0)),
                    hex=c.get("hex"),
                )
                for c in data.get("colors", [])
            ]

            materials = [
                MaterialInfo(
                    name=m.get("name", ""),
                    texture=m.get("texture"),
                    quality_indicator=m.get("quality_indicator"),
                )
                for m in data.get("materials", [])
            ]

            style_data = data.get("style", {})
            style = StyleAttributes(
                aesthetic=style_data.get("aesthetic", ""),
                mood=style_data.get("mood", ""),
                occasion=style_data.get("occasion", []),
                season=style_data.get("season", []),
            )

            return ExtractedFeatures(
                colors=colors,
                materials=materials,
                style=style,
                detected_elements=data.get("detected_elements", []),
                confidence_score=0.85,  # Default confidence
            )

        except json.JSONDecodeError:
            logger.warning("Failed to parse features JSON, using defaults")
            return ExtractedFeatures(
                colors=[],
                materials=[],
                style=None,
                detected_elements=[],
                confidence_score=0.0,
            )

    async def _generate_bullet_points(
        self,
        image_url: str,
        model: VisionModel,
    ) -> list[BulletPoint]:
        """Generate bullet points for product.

        Args:
            image_url: Image URL
            model: Vision model

        Returns:
            List of bullet points
        """
        response = await self._generate_with_fallback(
            image_url, BULLET_POINTS_PROMPT, model
        )

        bullet_points = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse "CATEGORY: text" format
            if ":" in line:
                parts = line.split(":", 1)
                category = parts[0].strip().lower()
                text = parts[1].strip()

                # Normalize category
                category_map = {
                    "material": "material",
                    "fabric": "material",
                    "fit": "fit",
                    "silhouette": "fit",
                    "feature": "feature",
                    "detail": "feature",
                    "care": "care",
                    "style": "feature",
                    "styling": "feature",
                }
                normalized_category = category_map.get(category, "feature")

                bullet_points.append(
                    BulletPoint(text=text, category=normalized_category)
                )
            else:
                # No category prefix
                bullet_points.append(BulletPoint(text=line, category="feature"))

        return bullet_points[:7]  # Max 7 bullet points

    async def _generate_seo_content(
        self,
        image_url: str,
        product_type: Any,
        brand_context: str | None,
        model: VisionModel,
    ) -> SEOContent:
        """Generate SEO content.

        Args:
            image_url: Image URL
            product_type: Product type
            brand_context: Brand context
            model: Vision model

        Returns:
            SEO content
        """
        prompt = SEO_PROMPT.format(
            product_type=product_type.value if hasattr(product_type, "value") else str(product_type),
            brand_context=f"Brand context: {brand_context}" if brand_context else "",
        )

        response = await self._generate_with_fallback(image_url, prompt, model)

        try:
            data = json.loads(response)
            return SEOContent(
                title=data.get("title", "")[:60],
                meta_description=data.get("meta_description", "")[:160],
                focus_keyword=data.get("focus_keyword", ""),
                secondary_keywords=data.get("secondary_keywords", []),
            )
        except json.JSONDecodeError:
            logger.warning("Failed to parse SEO JSON, using defaults")
            return SEOContent(
                title="Product",
                meta_description="Shop our collection",
                focus_keyword="fashion",
                secondary_keywords=[],
            )

    async def _generate_tags(
        self,
        image_url: str,
        model: VisionModel,
    ) -> list[str]:
        """Generate tags for product.

        Args:
            image_url: Image URL
            model: Vision model

        Returns:
            List of tags
        """
        response = await self._generate_with_fallback(image_url, TAGS_PROMPT, model)

        # Parse comma-separated tags
        tags = [
            tag.strip().lower()
            for tag in response.split(",")
            if tag.strip()
        ]

        return tags[:15]  # Max 15 tags
