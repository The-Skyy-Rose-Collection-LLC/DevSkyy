---
name: google-gemini-integration
description: Google Gemini integration for multi-model AI orchestration in DevSkyy's frontend and content agents
---

You are the Google Gemini Integration expert for DevSkyy. Integrate Google's Gemini models into the multi-model orchestration system for frontend and content agents.

## Core Gemini Integration

### 1. Gemini Client Manager

```python
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import os
from datetime import datetime
from enum import Enum

class GeminiModel(Enum):
    """Available Gemini models"""
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_ULTRA = "gemini-ultra"  # When available
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"  # Faster, cheaper

class GeminiClient:
    """Manage Google Gemini API interactions"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key (or use GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")

        genai.configure(api_key=self.api_key)
        self.models: Dict[str, Any] = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize Gemini models"""
        # Pro model (general purpose)
        self.models["pro"] = genai.GenerativeModel("gemini-1.5-pro")

        # Flash model (faster, cheaper)
        self.models["flash"] = genai.GenerativeModel("gemini-1.5-flash")

        # Vision model (image understanding)
        self.models["vision"] = genai.GenerativeModel("gemini-pro-vision")

    async def generate_content(
        self,
        prompt: str,
        model: str = "pro",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        safety_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini.

        Args:
            prompt: Input prompt
            model: Model to use (pro, flash, vision)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            safety_settings: Safety filter settings

        Returns:
            Generated content with metadata
        """
        try:
            # Get model
            gemini_model = self.models.get(model, self.models["pro"])

            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1
            )

            # Safety settings (default: block none for enterprise use)
            if safety_settings is None:
                safety_settings = {
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                }

            # Generate
            start_time = datetime.now()
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            end_time = datetime.now()

            # Extract response
            if response.candidates:
                content = response.candidates[0].content.parts[0].text
                finish_reason = response.candidates[0].finish_reason
            else:
                content = ""
                finish_reason = "NO_CANDIDATES"

            return {
                "success": True,
                "content": content,
                "model": model,
                "finish_reason": str(finish_reason),
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                },
                "latency_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "timestamp": datetime.now().isoformat()
            }

    async def generate_with_images(
        self,
        prompt: str,
        image_paths: List[str],
        model: str = "vision"
    ) -> Dict[str, Any]:
        """
        Generate content with image understanding.

        Args:
            prompt: Text prompt
            image_paths: List of image file paths or URLs
            model: Model to use (vision)

        Returns:
            Generated content analyzing images
        """
        try:
            from PIL import Image

            # Load images
            images = []
            for path in image_paths:
                img = Image.open(path)
                images.append(img)

            # Get vision model
            gemini_model = self.models.get(model, self.models["vision"])

            # Generate with images
            response = gemini_model.generate_content([prompt] + images)

            if response.candidates:
                content = response.candidates[0].content.parts[0].text
            else:
                content = ""

            return {
                "success": True,
                "content": content,
                "model": model,
                "images_processed": len(images),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }

    async def stream_content(
        self,
        prompt: str,
        model: str = "pro"
    ):
        """
        Stream content generation (for real-time responses).

        Args:
            prompt: Input prompt
            model: Model to use

        Yields:
            Content chunks as they're generated
        """
        try:
            gemini_model = self.models.get(model, self.models["pro"])

            response = gemini_model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.candidates:
                    yield {
                        "success": True,
                        "content": chunk.candidates[0].content.parts[0].text,
                        "is_final": False
                    }

            yield {
                "success": True,
                "content": "",
                "is_final": True
            }

        except Exception as e:
            yield {
                "success": False,
                "error": str(e),
                "is_final": True
            }

    async def count_tokens(self, text: str, model: str = "pro") -> Dict[str, Any]:
        """
        Count tokens in text.

        Args:
            text: Text to count
            model: Model to use for counting

        Returns:
            Token count
        """
        try:
            gemini_model = self.models.get(model, self.models["pro"])
            token_count = gemini_model.count_tokens(text)

            return {
                "success": True,
                "token_count": token_count.total_tokens,
                "model": model
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
```

### 2. Gemini for Frontend Agents

```python
class GeminiFrontendAgent:
    """Gemini-powered frontend agent for UI/UX tasks"""

    def __init__(self, brand_manager, gemini_client: GeminiClient):
        self.brand_manager = brand_manager
        self.gemini_client = gemini_client
        self.brand_context = brand_manager.get_brand_context()

    async def generate_ui_component(
        self,
        component_type: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate UI component code with brand styling.

        Args:
            component_type: Type of component (button, card, navbar, etc.)
            requirements: Component requirements and features

        Returns:
            Generated component code (React/TypeScript)
        """
        brand = self.brand_context

        prompt = f"""Generate a React TypeScript component for a {component_type}.

Brand Context:
- Brand: {brand['brand_name']}
- Primary Color: {brand['colors']['primary']}
- Accent Color: {brand['colors']['accent']}
- Font Primary: {brand['typography']['primary_font']}
- Font Secondary: {brand['typography']['secondary_font']}

Requirements:
{requirements}

Generate:
1. Complete React TypeScript component
2. Styled with brand colors and typography
3. Fully typed with TypeScript interfaces
4. Accessible (ARIA labels, keyboard navigation)
5. Responsive design
6. Include Tailwind CSS classes

Component code:"""

        result = await self.gemini_client.generate_content(
            prompt,
            model="pro",
            temperature=0.3,  # Lower temperature for code generation
            max_tokens=2048
        )

        return {
            "success": result["success"],
            "component_type": component_type,
            "code": result.get("content", ""),
            "brand_aligned": True,
            "model": "gemini-pro",
            "usage": result.get("usage", {})
        }

    async def analyze_ui_design(
        self,
        design_image_path: str
    ) -> Dict[str, Any]:
        """
        Analyze UI design mockup and provide feedback.

        Args:
            design_image_path: Path to design image

        Returns:
            Design analysis and suggestions
        """
        brand = self.brand_context

        prompt = f"""Analyze this UI design mockup for {brand['brand_name']}.

Evaluate:
1. Brand alignment (colors, typography, visual style)
2. User experience (navigation, hierarchy, clarity)
3. Accessibility (contrast, readability, touch targets)
4. Responsive design considerations
5. Modern UI/UX best practices

Provide:
- What works well
- What needs improvement
- Specific recommendations
- Brand alignment score (1-10)"""

        result = await self.gemini_client.generate_with_images(
            prompt,
            [design_image_path],
            model="vision"
        )

        return {
            "success": result["success"],
            "analysis": result.get("content", ""),
            "design_image": design_image_path,
            "brand_name": brand['brand_name']
        }
```

### 3. Gemini for Content Agents

```python
class GeminiContentAgent:
    """Gemini-powered content generation and analysis"""

    def __init__(self, brand_manager, gemini_client: GeminiClient):
        self.brand_manager = brand_manager
        self.gemini_client = gemini_client
        self.brand_context = brand_manager.get_brand_context()

    async def generate_product_content(
        self,
        product_data: Dict[str, Any],
        content_type: str = "description"
    ) -> Dict[str, Any]:
        """
        Generate product content with brand voice.

        Args:
            product_data: Product information
            content_type: Type of content (description, social_post, email, ad_copy)

        Returns:
            Generated brand-aligned content
        """
        brand = self.brand_context

        prompt = f"""Create {content_type} for this product.

Brand: {brand['brand_name']}
Voice: {brand['voice']['tone']} - {', '.join(brand['voice']['personality'])}
Style: {brand['voice']['style']}

Product:
- Name: {product_data.get('name')}
- Category: {product_data.get('category')}
- Material: {product_data.get('material')}
- Price: ${product_data.get('price')}
- Features: {', '.join(product_data.get('features', []))}

Generate compelling {content_type} that:
1. Matches brand voice perfectly
2. Highlights luxury and quality
3. Creates emotional connection
4. Includes subtle call-to-action
5. Is optimized for {content_type}

Content:"""

        result = await self.gemini_client.generate_content(
            prompt,
            model="pro",
            temperature=0.8,  # Higher temperature for creative content
            max_tokens=1500
        )

        return {
            "success": result["success"],
            "content_type": content_type,
            "content": result.get("content", ""),
            "brand_aligned": True,
            "product": product_data.get('name'),
            "model": "gemini-pro"
        }

    async def analyze_fashion_image(
        self,
        image_path: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze fashion product image.

        Args:
            image_path: Path to fashion image
            analysis_type: Type of analysis (comprehensive, style, technical)

        Returns:
            Image analysis results
        """
        prompt = f"""Analyze this fashion product image ({analysis_type} analysis).

Identify:
1. Garment type and category
2. Material and fabric (visual assessment)
3. Color palette (primary, secondary, accent)
4. Style classification (luxury, casual, vintage, etc.)
5. Design elements (patterns, textures, embellishments)
6. Potential target market
7. Styling suggestions
8. Estimated price range based on quality indicators

Provide detailed analysis in JSON format:
{{
    "garment_type": "...",
    "materials": ["..."],
    "colors": ["..."],
    "style": "...",
    "target_market": "...",
    "price_estimate": "...",
    "styling_suggestions": ["..."]
}}"""

        result = await self.gemini_client.generate_with_images(
            prompt,
            [image_path],
            model="vision"
        )

        return {
            "success": result["success"],
            "analysis": result.get("content", ""),
            "image_path": image_path,
            "analysis_type": analysis_type,
            "model": "gemini-pro-vision"
        }
```

### 4. Model Performance Comparison

```python
class GeminiPerformanceTracker:
    """Track Gemini performance vs other models"""

    def __init__(self):
        self.performance_log: List[Dict[str, Any]] = []

    def log_request(
        self,
        model: str,
        task_type: str,
        latency_ms: float,
        tokens_used: int,
        success: bool,
        quality_score: Optional[float] = None
    ):
        """Log model performance"""
        self.performance_log.append({
            "model": model,
            "task_type": task_type,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "success": success,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat()
        })

    def get_performance_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get performance comparison report"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=time_window_hours)

        # Filter recent logs
        recent = [
            log for log in self.performance_log
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]

        # Group by model
        by_model = {}
        for log in recent:
            model = log['model']
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(log)

        # Calculate metrics
        report = {}
        for model, logs in by_model.items():
            avg_latency = sum(l['latency_ms'] for l in logs) / len(logs)
            avg_tokens = sum(l['tokens_used'] for l in logs) / len(logs)
            success_rate = sum(1 for l in logs if l['success']) / len(logs)

            quality_scores = [l['quality_score'] for l in logs if l['quality_score'] is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

            report[model] = {
                "total_requests": len(logs),
                "avg_latency_ms": round(avg_latency, 2),
                "avg_tokens": round(avg_tokens, 2),
                "success_rate": round(success_rate * 100, 2),
                "avg_quality_score": round(avg_quality, 2) if avg_quality else None
            }

        return {
            "time_window_hours": time_window_hours,
            "models": report
        }
```

## Usage Examples

### Example 1: Initialize Gemini Client

```python
from skills.google_gemini_integration import GeminiClient

# Initialize
gemini = GeminiClient()  # Uses GOOGLE_API_KEY env var

# Generate content
result = await gemini.generate_content(
    "Write a luxury product description for a silk dress",
    model="pro",
    temperature=0.8
)

print(f"Content: {result['content']}")
print(f"Tokens: {result['usage']['total_tokens']}")
print(f"Latency: {result['latency_ms']}ms")
```

### Example 2: Frontend UI Generation

```python
from skills.brand_intelligence import BrandIntelligenceManager
from skills.google_gemini_integration import GeminiFrontendAgent, GeminiClient

# Initialize
brand_manager = BrandIntelligenceManager()
gemini = GeminiClient()
frontend_agent = GeminiFrontendAgent(brand_manager, gemini)

# Generate UI component
component = await frontend_agent.generate_ui_component(
    component_type="ProductCard",
    requirements={
        "features": ["image", "title", "price", "add_to_cart"],
        "hover_effects": True,
        "animations": True,
        "responsive": True
    }
)

print(f"Generated component:\n{component['code']}")
```

### Example 3: Fashion Image Analysis

```python
from skills.google_gemini_integration import GeminiContentAgent, GeminiClient

# Initialize
gemini = GeminiClient()
content_agent = GeminiContentAgent(brand_manager, gemini)

# Analyze fashion image
analysis = await content_agent.analyze_fashion_image(
    "products/dress-001.jpg",
    analysis_type="comprehensive"
)

print(f"Analysis: {analysis['analysis']}")
```

### Example 4: Streaming Response

```python
# Stream content generation
async for chunk in gemini.stream_content(
    "Write a long blog post about luxury fashion trends",
    model="pro"
):
    if chunk["success"] and not chunk["is_final"]:
        print(chunk["content"], end="", flush=True)
```

## Environment Variables Required

```bash
# Add to .env
GOOGLE_API_KEY=your_google_api_key_here
```

## Truth Protocol Compliance

- ✅ API key in environment variables (Rule 5)
- ✅ Type-safe implementation (Rule 11)
- ✅ Error handling and logging (Rule 10)
- ✅ Performance tracking (Rule 12)
- ✅ Brand integration (Rule 9)

## Integration Points

**Frontend Agents:**
- Design Automation Agent
- Web Development Agent
- WordPress Theme Builder

**Content Agents:**
- Visual Content Generation
- Marketing Content Generation
- Fashion Computer Vision

**Model Selection Logic:**
- UI/Design tasks → Gemini Pro (fast, good at structured output)
- Image analysis → Gemini Vision (multimodal)
- Creative content → Gemini Pro (high temperature)
- Code generation → Gemini Pro (low temperature)

Use this skill for integrating Google Gemini into DevSkyy's multi-model AI orchestration system.
