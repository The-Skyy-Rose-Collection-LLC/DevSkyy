"""
DevSkyy Multimodal Capabilities Module
========================================

LlamaIndex-powered multimodal LLM integration for vision and image understanding.

Provides:
- Vision capabilities via Anthropic Claude (multimodal)
- Image analysis and understanding
- Visual reasoning
- Product image analysis for e-commerce
- Brand compliance checking

Architecture:
    MultimodalCapabilities
    ├── AnthropicMultiModal (Claude with vision)
    ├── HuggingFaceMultiModal (OSS models)
    └── OpenAI (GPT-4o vision)

Integration with DevSkyy SuperAgents:
- CreativeAgent: Visual asset analysis, quality checks
- CommerceAgent: Product image analysis, compliance
- MarketingAgent: Visual content analysis, brand consistency
"""

import base64
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.multi_modal_llms import MultiModalLLM
from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal
from llama_index.multi_modal_llms.huggingface import HuggingFaceMultiModal

logger = logging.getLogger(__name__)


class MultimodalProvider(str, Enum):
    """Supported multimodal providers"""

    ANTHROPIC = "anthropic"  # Claude with vision (default)
    OPENAI = "openai"  # GPT-4o vision
    HUGGINGFACE = "huggingface"  # OSS models


class AnalysisType(str, Enum):
    """Types of visual analysis"""

    PRODUCT_DESCRIPTION = "product_description"  # Generate product descriptions from images
    QUALITY_CHECK = "quality_check"  # Check image quality and technical specs
    BRAND_COMPLIANCE = "brand_compliance"  # Check brand guidelines compliance
    COLOR_ANALYSIS = "color_analysis"  # Analyze color palette
    STYLE_ANALYSIS = "style_analysis"  # Analyze style and aesthetics
    OBJECT_DETECTION = "object_detection"  # Detect objects in image
    TEXT_EXTRACTION = "text_extraction"  # Extract text from image (OCR)
    VISUAL_REASONING = "visual_reasoning"  # General visual Q&A


@dataclass
class ImageAnalysisResult:
    """Result of multimodal image analysis"""

    analysis_type: AnalysisType
    provider: MultimodalProvider
    text_response: str
    confidence: float
    metadata: dict[str, Any]
    image_url: str | None = None
    processing_time_ms: float = 0.0


class MultimodalCapabilities:
    """
    Multimodal LLM capabilities using LlamaIndex.

    Provides vision and image understanding for DevSkyy SuperAgents.

    Example:
        capabilities = MultimodalCapabilities()
        await capabilities.initialize()

        # Analyze product image
        result = await capabilities.analyze_image(
            image_path="product.jpg",
            analysis_type=AnalysisType.PRODUCT_DESCRIPTION,
            prompt="Describe this product for e-commerce"
        )

        # Check brand compliance
        result = await capabilities.check_brand_compliance(
            image_path="marketing.jpg",
            brand_colors=["#B76E79", "#1A1A1A"]
        )
    """

    def __init__(
        self,
        default_provider: MultimodalProvider = MultimodalProvider.ANTHROPIC,
        anthropic_model: str = "claude-3-5-sonnet-20241022",
        openai_model: str = "gpt-4o",
        max_tokens: int = 2048,
    ):
        """
        Initialize multimodal capabilities.

        Args:
            default_provider: Default provider to use
            anthropic_model: Anthropic model name
            openai_model: OpenAI model name
            max_tokens: Max tokens for responses
        """
        self.default_provider = default_provider
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model
        self.max_tokens = max_tokens

        # LLM instances
        self._anthropic: AnthropicMultiModal | None = None
        self._openai: OpenAI | None = None
        self._huggingface: HuggingFaceMultiModal | None = None

        # Cache for performance
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize multimodal LLM providers"""
        if self._initialized:
            return

        logger.info("Initializing multimodal capabilities...")

        # Initialize Anthropic (Claude with vision)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                self._anthropic = AnthropicMultiModal(
                    model=self.anthropic_model,
                    api_key=anthropic_key,
                    max_tokens=self.max_tokens,
                )
                logger.info(f"✓ Anthropic Claude initialized ({self.anthropic_model})")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")

        # Initialize OpenAI (GPT-4o vision)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self._openai = OpenAI(
                    model=self.openai_model,
                    api_key=openai_key,
                    max_tokens=self.max_tokens,
                )
                logger.info(f"✓ OpenAI GPT-4o initialized ({self.openai_model})")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # HuggingFace initialization (optional - requires GPU)
        # Commented out by default as it requires significant resources
        # hf_token = os.getenv("HUGGINGFACE_TOKEN")
        # if hf_token:
        #     try:
        #         self._huggingface = HuggingFaceMultiModal(
        #             model_name="llava-hf/llava-1.5-7b-hf",
        #             token=hf_token
        #         )
        #         logger.info("✓ HuggingFace multimodal initialized")
        #     except Exception as e:
        #         logger.warning(f"Failed to initialize HuggingFace: {e}")

        if not any([self._anthropic, self._openai]):
            raise RuntimeError(
                "No multimodal providers initialized. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
            )

        self._initialized = True
        logger.info("Multimodal capabilities ready")

    def _get_provider(self, provider: MultimodalProvider | None = None) -> MultiModalLLM:
        """Get the appropriate multimodal LLM provider"""
        provider = provider or self.default_provider

        if provider == MultimodalProvider.ANTHROPIC and self._anthropic:
            return self._anthropic
        elif provider == MultimodalProvider.OPENAI and self._openai:
            return self._openai
        elif provider == MultimodalProvider.HUGGINGFACE and self._huggingface:
            return self._huggingface

        # Fallback to any available provider
        if self._anthropic:
            logger.warning(f"Provider {provider} not available, falling back to Anthropic")
            return self._anthropic
        elif self._openai:
            logger.warning(f"Provider {provider} not available, falling back to OpenAI")
            return self._openai

        raise RuntimeError("No multimodal providers available")

    def _load_image(self, image_path: str) -> tuple[str, str]:
        """
        Load image and convert to base64.

        Returns:
            tuple: (mime_type, base64_data)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine MIME type
        suffix = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/jpeg")

        # Read and encode
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return mime_type, image_data

    async def analyze_image(
        self,
        image_path: str,
        analysis_type: AnalysisType,
        prompt: str,
        provider: MultimodalProvider | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> ImageAnalysisResult:
        """
        Analyze an image with a custom prompt.

        Args:
            image_path: Path to image file
            analysis_type: Type of analysis to perform
            prompt: Custom prompt for the analysis
            provider: Optional provider override
            additional_context: Additional context for the analysis

        Returns:
            ImageAnalysisResult with analysis text and metadata
        """
        import time

        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        # Get provider
        llm = self._get_provider(provider)
        provider_name = provider or self.default_provider  # Track which provider was used

        # Load image
        mime_type, image_data = self._load_image(image_path)
        image_url = f"data:{mime_type};base64,{image_data}"

        # Build messages
        messages = [
            ChatMessage(
                role=MessageRole.USER,
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            )
        ]

        # Add context if provided
        if additional_context:
            context_text = "\n\nAdditional Context:\n" + "\n".join(
                f"- {k}: {v}" for k, v in additional_context.items()
            )
            messages[0].content[0]["text"] += context_text

        # Call multimodal LLM
        try:
            response = await llm.achat(messages)
            text_response = str(response.message.content)

            processing_time = (time.time() - start_time) * 1000

            return ImageAnalysisResult(
                analysis_type=analysis_type,
                provider=provider_name,
                text_response=text_response,
                confidence=0.95,  # TODO: Extract from provider if available
                metadata={
                    "model": llm.model if hasattr(llm, "model") else "unknown",
                    "image_path": image_path,
                    "mime_type": mime_type,
                    "prompt_length": len(prompt),
                },
                image_url=image_url,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Image analysis failed: {e}", exc_info=True)
            raise

    async def analyze_product_image(
        self,
        image_path: str,
        product_type: str = "clothing",
        include_technical: bool = True,
    ) -> ImageAnalysisResult:
        """
        Generate a detailed product description from an image.

        Args:
            image_path: Path to product image
            product_type: Type of product (clothing, jewelry, accessory)
            include_technical: Include technical details (fabric, dimensions)

        Returns:
            ImageAnalysisResult with product description
        """
        prompt = f"""Analyze this {product_type} product image and provide a detailed e-commerce description.

Include:
1. **Product Type**: What is this item?
2. **Visual Description**: Colors, patterns, style, aesthetics
3. **Key Features**: Notable design elements, unique characteristics
4. **Material/Fabric**: What materials appear to be used? (if visible)
5. **Fit & Silhouette**: How does it fit? What's the silhouette?
6. **Styling Suggestions**: How could this be worn/styled?

Format as clear, structured markdown suitable for e-commerce listing.
Focus on luxury streetwear aesthetic - be descriptive but concise."""

        if include_technical:
            prompt += (
                "\n7. **Technical Details**: Estimated dimensions, weight, construction details"
            )

        return await self.analyze_image(
            image_path=image_path,
            analysis_type=AnalysisType.PRODUCT_DESCRIPTION,
            prompt=prompt,
            additional_context={"product_type": product_type},
        )

    async def check_brand_compliance(
        self,
        image_path: str,
        brand_colors: list[str],
        brand_style: str = "luxury streetwear",
    ) -> ImageAnalysisResult:
        """
        Check if an image complies with brand guidelines.

        Args:
            image_path: Path to image to check
            brand_colors: List of brand hex colors
            brand_style: Brand style description

        Returns:
            ImageAnalysisResult with compliance analysis
        """
        colors_str = ", ".join(brand_colors)

        prompt = f"""Analyze this image for brand compliance.

**Brand Guidelines:**
- **Primary Colors**: {colors_str}
- **Style**: {brand_style}
- **Aesthetic**: Bold, sophisticated, emotionally resonant
- **Quality**: Premium, high-resolution, editorial

**Analysis Required:**
1. **Color Compliance**: Does it use the brand color palette? Are colors accurate?
2. **Style Alignment**: Does it match the brand aesthetic?
3. **Quality Check**: Is it high-resolution? Professional quality?
4. **Brand Consistency**: Does it feel on-brand?

Provide:
- ✓ PASS or ✗ FAIL for each criterion
- Specific issues if any
- Recommendations for improvement"""

        return await self.analyze_image(
            image_path=image_path,
            analysis_type=AnalysisType.BRAND_COMPLIANCE,
            prompt=prompt,
            additional_context={
                "brand_colors": brand_colors,
                "brand_style": brand_style,
            },
        )

    async def extract_colors(self, image_path: str) -> ImageAnalysisResult:
        """
        Extract dominant colors from an image.

        Args:
            image_path: Path to image

        Returns:
            ImageAnalysisResult with color palette
        """
        prompt = """Analyze the colors in this image.

Provide:
1. **Dominant Colors**: Top 3-5 colors in the image (describe with common names)
2. **Estimated Hex Codes**: Best guess at hex codes for each color
3. **Color Harmony**: Is the color palette harmonious? What type of harmony?
4. **Mood**: What mood/emotion do these colors evoke?
5. **Recommendations**: Color adjustments to improve harmony/brand alignment

Format as structured JSON-compatible text."""

        return await self.analyze_image(
            image_path=image_path,
            analysis_type=AnalysisType.COLOR_ANALYSIS,
            prompt=prompt,
        )

    async def close(self) -> None:
        """Clean up resources"""
        # LlamaIndex LLMs don't require explicit cleanup
        self._initialized = False
        logger.info("Multimodal capabilities closed")


# Singleton instance
_multimodal_capabilities: MultimodalCapabilities | None = None


def get_multimodal_capabilities(
    provider: MultimodalProvider = MultimodalProvider.ANTHROPIC,
) -> MultimodalCapabilities:
    """
    Get singleton multimodal capabilities instance.

    Args:
        provider: Default provider to use

    Returns:
        MultimodalCapabilities instance
    """
    global _multimodal_capabilities
    if _multimodal_capabilities is None:
        _multimodal_capabilities = MultimodalCapabilities(default_provider=provider)
    return _multimodal_capabilities
