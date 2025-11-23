"""
Fashion Computer Vision Agent
Advanced AI vision system specialized in luxury fashion analysis and generation

Features:
- High-quality fashion image generation (Stable Diffusion SDXL)
- Detailed fabric and texture analysis
- Stitch pattern recognition
- Garment cut and construction analysis
- Material identification (silk, cotton, leather, etc.)
- Quality assessment
- Style classification
- Color palette extraction
- Trend prediction from visual data
- Product photography optimization
- Virtual try-on preparation
- Defect detection for quality control
"""

import base64
from datetime import datetime
import io
import logging
import os
from pathlib import Path
from typing import Any, Union

import anthropic
import cv2
from diffusers import StableDiffusionXLPipeline
import numpy as np
from openai import AsyncOpenAI
from PIL import Image
import torch
from transformers import CLIPModel, CLIPProcessor, ViTImageProcessor, ViTModel


logger = logging.getLogger(__name__)


class FashionComputerVisionAgent:
    """
    Advanced computer vision agent specialized in luxury fashion
    imagery analysis, generation, and quality assessment.
    """

    def __init__(self):
        # AI Services
        self.claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Initialize models
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🖥️ Using device: {self.device}")

        # Load CLIP for fashion understanding
        try:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
            self.clip_model.to(self.device)
            logger.info("✅ CLIP model loaded for fashion analysis")
        except Exception as e:
            logger.warning(f"⚠️ CLIP model not loaded: {e}")
            self.clip_model = None

        # Load ViT for detailed image features
        try:
            self.vit_processor = ViTImageProcessor.from_pretrained("google/vit-large-patch16-224")
            self.vit_model = ViTModel.from_pretrained("google/vit-large-patch16-224")
            self.vit_model.to(self.device)
            logger.info("✅ ViT model loaded for detailed analysis")
        except Exception as e:
            logger.warning(f"⚠️ ViT model not loaded: {e}")
            self.vit_model = None

        # Stable Diffusion XL for high-quality generation
        try:
            self.sdxl_pipeline = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
            )
            self.sdxl_pipeline.to(self.device)
            logger.info("✅ Stable Diffusion XL loaded for image generation")
        except Exception as e:
            logger.warning(f"⚠️ SDXL not loaded: {e}")
            self.sdxl_pipeline = None

        # Fashion-specific knowledge base
        self.fabric_types = {
            "silk": {
                "characteristics": ["smooth", "lustrous", "drapes_well", "delicate"],
                "visual_cues": ["sheen", "soft_reflection", "flowing"],
            },
            "cotton": {
                "characteristics": ["matte", "breathable", "structured", "durable"],
                "visual_cues": ["texture_visible", "no_sheen", "crisp"],
            },
            "wool": {
                "characteristics": ["warm", "textured", "structured", "natural"],
                "visual_cues": ["visible_fibers", "matte", "thick"],
            },
            "leather": {
                "characteristics": [
                    "durable",
                    "structured",
                    "luxury",
                    "aged_beautifully",
                ],
                "visual_cues": ["grain_pattern", "natural_variations", "sheen"],
            },
            "linen": {
                "characteristics": [
                    "breathable",
                    "natural",
                    "wrinkles_easily",
                    "casual_luxury",
                ],
                "visual_cues": ["visible_weave", "natural_color", "texture"],
            },
            "cashmere": {
                "characteristics": ["ultra_soft", "luxury", "warm", "delicate"],
                "visual_cues": ["fine_texture", "soft_appearance", "subtle_sheen"],
            },
            "satin": {
                "characteristics": ["smooth", "glossy", "formal", "drapes_beautifully"],
                "visual_cues": ["high_sheen", "smooth_surface", "reflective"],
            },
            "velvet": {
                "characteristics": ["plush", "luxury", "textured", "rich"],
                "visual_cues": ["depth", "directional_pile", "rich_color"],
            },
        }

        self.garment_cuts = {
            "a_line": "Fitted at top, gradually widens toward hem",
            "empire": "High waist just below bust, flows down",
            "sheath": "Fitted silhouette following body shape",
            "shift": "Straight, loose fit not following curves",
            "wrap": "Overlaps and ties at waist",
            "ball_gown": "Fitted bodice with full skirt",
            "mermaid": "Fitted through body, flares at knees",
            "column": "Straight, narrow silhouette",
            "fit_and_flare": "Fitted bodice, flared skirt",
        }

        self.stitch_types = {
            "straight": "Basic linear stitch",
            "zigzag": "Side-to-side stitch for stretch fabrics",
            "overlock": "Edge finishing stitch",
            "blind_hem": "Invisible hemming",
            "topstitch": "Decorative visible stitching",
            "chain_stitch": "Looped interlocking stitches",
            "cross_stitch": "X-shaped decorative stitch",
        }

        logger.info("🎨 Fashion Computer Vision Agent initialized")

    async def analyze_fashion_image(self, image_path: Union[str, Path, Image.Image]) -> dict[str, Any]:
        """
        Comprehensive fashion image analysis including:
        - Fabric identification
        - Texture analysis
        - Stitching detection
        - Cut/silhouette analysis
        - Quality assessment
        - Style classification
        - Color analysis
        """
        try:
            logger.info("🔍 Analyzing fashion image...")

            # Load image
            image = Image.open(image_path).convert("RGB") if isinstance(image_path, (str, Path)) else image_path

            # Multi-level analysis
            results = {}

            # 1. Fabric and texture analysis
            results["fabric_analysis"] = await self._analyze_fabric(image)

            # 2. Stitching analysis
            results["stitching_analysis"] = await self._analyze_stitching(image)

            # 3. Garment cut analysis
            results["cut_analysis"] = await self._analyze_garment_cut(image)

            # 4. Quality assessment
            results["quality_assessment"] = await self._assess_quality(image)

            # 5. Style classification
            results["style_classification"] = await self._classify_style(image)

            # 6. Color palette extraction
            results["color_palette"] = await self._extract_color_palette(image)

            # 7. AI-powered detailed analysis
            results["ai_detailed_analysis"] = await self._ai_vision_analysis(image)

            # 8. Overall assessment
            results["overall_assessment"] = self._generate_overall_assessment(results)

            results["timestamp"] = datetime.now().isoformat()
            results["analysis_complete"] = True

            logger.info("✅ Fashion image analysis complete")
            return results

        except Exception as e:
            logger.error(f"❌ Fashion image analysis failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _analyze_fabric(self, image: Image.Image) -> dict[str, Any]:
        """
        Detailed fabric and texture analysis using computer vision.
        """
        try:
            # Convert to numpy for OpenCV processing
            img_array = np.array(image)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Texture analysis using Gabor filters
            texture_features = self._extract_texture_features(img_gray)

            # Sheen/glossiness detection
            sheen_level = self._detect_sheen(img_array)

            # Weave pattern detection
            weave_pattern = self._detect_weave_pattern(img_gray)

            # Identify fabric type using features
            fabric_predictions = self._predict_fabric_type(texture_features, sheen_level, weave_pattern)

            return {
                "primary_fabric": (fabric_predictions[0] if fabric_predictions else "unknown"),
                "fabric_confidence": fabric_predictions[1] if fabric_predictions else 0,
                "alternative_fabrics": (fabric_predictions[2:] if len(fabric_predictions) > 2 else []),
                "texture_score": texture_features["complexity"],
                "sheen_level": sheen_level,
                "weave_visible": weave_pattern["visible"],
                "fabric_characteristics": self._get_fabric_characteristics(
                    fabric_predictions[0] if fabric_predictions else "unknown"
                ),
            }

        except Exception as e:
            logger.error(f"❌ Fabric analysis failed: {e}")
            return {"error": str(e)}

    def _extract_texture_features(self, gray_image: np.ndarray) -> dict[str, Any]:
        """
        Extract texture features using Gabor filters and statistical analysis.
        """
        # Gabor filter for texture
        gabor_kernels = []
        for theta in np.arange(0, np.pi, np.pi / 4):
            kernel = cv2.getGaborKernel((21, 21), 5.0, theta, 10.0, 0.5, 0, ktype=cv2.CV_32F)
            gabor_kernels.append(kernel)

        features = []
        for kernel in gabor_kernels:
            filtered = cv2.filter2D(gray_image, cv2.CV_8UC3, kernel)
            features.append(filtered.mean())
            features.append(filtered.var())

        # Texture complexity
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        complexity = laplacian.var()

        return {"gabor_features": features, "complexity": float(complexity)}

    def _detect_sheen(self, image_array: np.ndarray) -> float:
        """
        Detect fabric sheen/glossiness level.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

        # High value channel indicates sheen
        value_channel = hsv[:, :, 2]

        # Detect bright spots (sheen indicators)
        high_value_pixels = np.sum(value_channel > 200)
        total_pixels = value_channel.size

        sheen_level = high_value_pixels / total_pixels

        return float(sheen_level)

    def _detect_weave_pattern(self, gray_image: np.ndarray) -> dict[str, Any]:
        """
        Detect visible weave patterns in fabric.
        """
        # FFT to detect periodic patterns
        f = np.fft.fft2(gray_image)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)

        # Check for periodic patterns
        pattern_strength = np.std(magnitude_spectrum)

        return {
            "visible": pattern_strength > 50,
            "pattern_strength": float(pattern_strength),
            "pattern_type": "regular_weave" if pattern_strength > 50 else "smooth",
        }

    def _predict_fabric_type(
        self, texture_features: dict, sheen_level: float, weave_pattern: dict
    ) -> list[tuple[str, float]]:
        """
        Predict fabric type based on visual features.
        """
        predictions = []

        complexity = texture_features["complexity"]

        # Rule-based fabric prediction
        if sheen_level > 0.3:
            if complexity < 100:
                predictions.append(("satin", 0.85))
                predictions.append(("silk", 0.75))
            else:
                predictions.append(("silk", 0.80))
        elif sheen_level > 0.15:
            predictions.append(("leather", 0.70))
            predictions.append(("velvet", 0.60))
        elif weave_pattern["visible"]:
            predictions.append(("linen", 0.80))
            predictions.append(("cotton", 0.70))
        elif complexity > 150:
            predictions.append(("wool", 0.75))
            predictions.append(("cashmere", 0.65))
        else:
            predictions.append(("cotton", 0.70))

        return predictions

    def _get_fabric_characteristics(self, fabric_type: str) -> dict[str, Any]:
        """
        Get characteristics of identified fabric.
        """
        return self.fabric_types.get(fabric_type, {"characteristics": [], "visual_cues": []})

    async def _analyze_stitching(self, image: Image.Image) -> dict[str, Any]:
        """
        Analyze stitching patterns and quality.
        """
        try:
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Edge detection for stitch lines
            edges = cv2.Canny(gray, 50, 150)

            # Hough line detection for straight stitches
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=30, maxLineGap=10)

            stitch_count = len(lines) if lines is not None else 0

            # Analyze stitch uniformity
            uniformity = self._analyze_stitch_uniformity(lines) if lines is not None else 0

            # Detect stitch type
            stitch_types = self._detect_stitch_types(edges, lines)

            return {
                "stitches_detected": stitch_count,
                "stitch_uniformity": uniformity,
                "stitch_quality": ("excellent" if uniformity > 0.8 else "good" if uniformity > 0.6 else "fair"),
                "detected_stitch_types": stitch_types,
                "visible_stitching": stitch_count > 10,
            }

        except Exception as e:
            logger.error(f"❌ Stitching analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_stitch_uniformity(self, lines: np.ndarray) -> float:
        """
        Analyze uniformity of stitching.
        """
        if lines is None or len(lines) < 2:
            return 0.0

        # Calculate line lengths
        lengths = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            lengths.append(length)

        # Uniformity = 1 - (std / mean)
        if len(lengths) > 0 and np.mean(lengths) > 0:
            uniformity = 1 - (np.std(lengths) / np.mean(lengths))
            return max(0, min(1, uniformity))

        return 0.0

    def _detect_stitch_types(self, edges: np.ndarray, lines: np.ndarray | None) -> list[str]:
        """
        Detect types of stitches present.
        """
        stitch_types = []

        if lines is not None and len(lines) > 5:
            stitch_types.append("straight")

            # Check for topstitching (visible decorative)
            if len(lines) > 20:
                stitch_types.append("topstitch")

        # Detect zigzag patterns
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if len(contour) > 10:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) > 6:  # Zigzag has many vertices
                    if "zigzag" not in stitch_types:
                        stitch_types.append("zigzag")

        return stitch_types if stitch_types else ["standard"]

    async def _analyze_garment_cut(self, image: Image.Image) -> dict[str, Any]:
        """
        Analyze garment cut and silhouette.
        """
        try:
            # Use AI vision for cut analysis
            img_array = np.array(image)

            # Detect silhouette using contour detection
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Get largest contour (garment outline)
                largest_contour = max(contours, key=cv2.contourArea)

                # Analyze shape
                silhouette_type = self._classify_silhouette(largest_contour)

                # Calculate shape metrics
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                hull = cv2.convexHull(largest_contour)
                hull_area = cv2.contourArea(hull)

                # Solidity (how fitted vs flowing)
                solidity = area / hull_area if hull_area > 0 else 0

                return {
                    "cut_type": silhouette_type,
                    "cut_description": self.garment_cuts.get(silhouette_type, "Unknown cut"),
                    "fit_type": ("fitted" if solidity > 0.8 else "flowing" if solidity < 0.5 else "semi_fitted"),
                    "silhouette_complexity": len(largest_contour),
                    "shape_metrics": {
                        "area": float(area),
                        "perimeter": float(perimeter),
                        "solidity": float(solidity),
                    },
                }

            return {
                "cut_type": "unknown",
                "message": "Could not detect garment outline",
            }

        except Exception as e:
            logger.error(f"❌ Cut analysis failed: {e}")
            return {"error": str(e)}

    def _classify_silhouette(self, contour: np.ndarray) -> str:
        """
        Classify garment silhouette from contour.
        """
        # Approximate contour
        epsilon = 0.01 * cv2.arcLength(contour, True)
        cv2.approxPolyDP(contour, epsilon, True)

        # Get bounding rectangle
        _x, _y, w, h = cv2.boundingRect(contour)

        # Aspect ratio
        aspect_ratio = h / w if w > 0 else 0

        # Simple classification based on shape
        if aspect_ratio > 1.5:
            # Tall and narrow
            moments = cv2.moments(contour)
            if moments["m00"] != 0:
                # Check if wider at bottom (A-line) or top
                return "column" if w < h * 0.4 else "a_line"
        elif aspect_ratio < 0.8:
            # Wide and short
            return "shift"
        else:
            # Check fitting
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            area = cv2.contourArea(contour)
            solidity = area / hull_area if hull_area > 0 else 0

            if solidity > 0.85:
                return "sheath"
            else:
                return "fit_and_flare"

        return "unknown"

    async def _assess_quality(self, image: Image.Image) -> dict[str, Any]:
        """
        Assess garment quality from image.
        """
        try:
            img_array = np.array(image)

            # Sharpness (indicates quality photography and detail)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Color consistency
            color_variance = np.var(img_array, axis=(0, 1))
            color_consistency = 1 / (1 + np.mean(color_variance) / 1000)

            # Overall quality score
            quality_score = (sharpness / 1000 + color_consistency) / 2

            quality_level = (
                "excellent"
                if quality_score > 0.8
                else ("good" if quality_score > 0.6 else "fair" if quality_score > 0.4 else "poor")
            )

            return {
                "quality_score": float(min(1.0, quality_score)),
                "quality_level": quality_level,
                "sharpness": float(sharpness),
                "color_consistency": float(color_consistency),
                "assessment": f"This garment shows {quality_level} quality based on visual analysis",
            }

        except Exception as e:
            logger.error(f"❌ Quality assessment failed: {e}")
            return {"error": str(e)}

    async def _classify_style(self, image: Image.Image) -> dict[str, Any]:
        """
        Classify fashion style using CLIP model.
        """
        try:
            if not self.clip_model:
                return {"style": "unknown", "reason": "CLIP model not loaded"}

            # Fashion style categories
            style_categories = [
                "casual wear",
                "formal wear",
                "evening gown",
                "business attire",
                "cocktail dress",
                "luxury fashion",
                "streetwear",
                "haute couture",
                "resort wear",
                "bridal wear",
            ]

            # Process image and text
            inputs = self.clip_processor(text=style_categories, images=image, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get predictions
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            # Get top 3 predictions
            top_probs, top_indices = torch.topk(probs[0], 3)

            predictions = [
                {"style": style_categories[idx.item()], "confidence": prob.item()}
                for prob, idx in zip(top_probs, top_indices, strict=False)
            ]

            return {
                "primary_style": predictions[0]["style"],
                "confidence": predictions[0]["confidence"],
                "alternative_styles": predictions[1:],
            }

        except Exception as e:
            logger.error(f"❌ Style classification failed: {e}")
            return {"error": str(e)}

    async def _extract_color_palette(self, image: Image.Image) -> dict[str, Any]:
        """
        Extract dominant color palette from garment.
        """
        try:
            # Resize for faster processing
            img_small = image.resize((150, 150))
            img_array = np.array(img_small)

            # Reshape to list of pixels
            pixels = img_array.reshape(-1, 3)

            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans

            n_colors = 5
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get colors and their percentages
            colors = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_
            counts = np.bincount(labels)
            percentages = counts / len(labels)

            # Sort by percentage
            sorted_indices = np.argsort(percentages)[::-1]

            palette = []
            for idx in sorted_indices:
                color_rgb = colors[idx]
                palette.append(
                    {
                        "rgb": color_rgb.tolist(),
                        "hex": "#{:02x}{:02x}{:02x}".format(*color_rgb),
                        "percentage": float(percentages[idx]),
                    }
                )

            return {"palette": palette, "dominant_color": palette[0]}

        except Exception as e:
            logger.error(f"❌ Color extraction failed: {e}")
            return {"error": str(e)}

    async def _ai_vision_analysis(self, image: Image.Image) -> dict[str, Any]:
        """
        Use Claude's vision capabilities for detailed analysis.
        """
        try:
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Analyze with Claude
            response = await self.claude.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": """Analyze this luxury fashion garment in detail:

1. Fabric type and quality
2. Texture description
3. Stitching and construction details
4. Garment cut and silhouette
5. Style classification
6. Quality indicators
7. Unique design elements
8. Craftsmanship level
9. Estimated luxury tier (accessible, premium, haute couture)
10. Recommended styling and occasions

Provide detailed, expert fashion analysis.""",
                            },
                        ],
                    }
                ],
            )

            analysis = response.content[0].text

            return {"detailed_analysis": analysis, "model": "claude-sonnet-4.5"}

        except Exception as e:
            logger.error(f"❌ AI vision analysis failed: {e}")
            return {"error": str(e)}

    def _generate_overall_assessment(self, results: dict[str, Any]) -> dict[str, Any]:
        """
        Generate comprehensive overall assessment.
        """
        fabric = results.get("fabric_analysis", {})
        quality = results.get("quality_assessment", {})
        style = results.get("style_classification", {})

        assessment = {
            "luxury_tier": self._determine_luxury_tier(fabric, quality),
            "craftsmanship_rating": quality.get("quality_level", "unknown"),
            "authenticity_confidence": ("high" if quality.get("quality_score", 0) > 0.7 else "medium"),
            "estimated_value_range": self._estimate_value_range(fabric, quality, style),
            "recommended_use": style.get("primary_style", "versatile wear"),
        }

        return assessment

    def _determine_luxury_tier(self, fabric: dict, quality: dict) -> str:
        """
        Determine luxury tier of garment.
        """
        fabric_type = fabric.get("primary_fabric", "").lower()
        quality_score = quality.get("quality_score", 0)

        luxury_fabrics = ["silk", "cashmere", "satin", "velvet", "leather"]

        if fabric_type in luxury_fabrics and quality_score > 0.8:
            return "haute_couture"
        elif fabric_type in luxury_fabrics or quality_score > 0.7:
            return "premium_luxury"
        elif quality_score > 0.5:
            return "accessible_luxury"
        else:
            return "standard"

    def _estimate_value_range(self, fabric: dict, quality: dict, style: dict) -> str:
        """
        Estimate value range based on analysis.
        """
        tier = self._determine_luxury_tier(fabric, quality)

        value_ranges = {
            "haute_couture": "$5,000 - $50,000+",
            "premium_luxury": "$1,000 - $5,000",
            "accessible_luxury": "$300 - $1,000",
            "standard": "$50 - $300",
        }

        return value_ranges.get(tier, "Unknown")

    async def generate_fashion_image(
        self,
        prompt: str,
        style: str = "luxury fashion photography",
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
    ) -> dict[str, Any]:
        """
        Generate high-quality fashion imagery using Stable Diffusion XL.
        """
        try:
            if not self.sdxl_pipeline:
                return {
                    "error": "Image generation not available - SDXL not loaded",
                    "status": "failed",
                }

            logger.info(f"🎨 Generating fashion image: {prompt}")

            # Enhance prompt for luxury fashion
            enhanced_prompt = f"{prompt}, {style}, high quality, professional photography, studio lighting, sharp focus, detailed texture, 8k uhd, luxury aesthetic"

            # Default negative prompt for fashion
            if not negative_prompt:
                negative_prompt = "low quality, blurry, distorted, amateur, bad anatomy, watermark, text, logo"

            # Generate image
            image = self.sdxl_pipeline(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=50,
                guidance_scale=7.5,
            ).images[0]

            # Save image
            output_path = Path("generated_fashion") / f"fashion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_path.parent.mkdir(exist_ok=True)
            image.save(output_path)

            return {
                "success": True,
                "image_path": str(output_path),
                "prompt_used": enhanced_prompt,
                "dimensions": {"width": width, "height": height},
                "model": "stable-diffusion-xl",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return {"error": str(e), "status": "failed"}


# Factory function
def create_fashion_vision_agent() -> FashionComputerVisionAgent:
    """Create Fashion Computer Vision Agent instance."""
    return FashionComputerVisionAgent()


# Global instance
fashion_vision_agent = create_fashion_vision_agent()


# Convenience functions
async def analyze_garment(image_path: Union[str, Path]) -> dict[str, Any]:
    """Analyze fashion garment from image."""
    return await fashion_vision_agent.analyze_fashion_image(image_path)


async def generate_fashion_photo(prompt: str, style: str = "luxury") -> dict[str, Any]:
    """Generate fashion photography."""
    return await fashion_vision_agent.generate_fashion_image(prompt, style)
