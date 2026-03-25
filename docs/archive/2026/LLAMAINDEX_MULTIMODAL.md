# LlamaIndex Multimodal Integration

**Vision Capabilities for DevSkyy SuperAgents**

## Overview

DevSkyy now includes **LlamaIndex-powered multimodal capabilities** that enable vision and image understanding across all SuperAgents. This integration adds powerful visual analysis features for e-commerce, brand compliance, and content creation.

## Features

### 🔍 Image Analysis

- **Product Descriptions**: Auto-generate detailed e-commerce descriptions from product images
- **Brand Compliance**: Check images against SkyyRose brand guidelines
- **Color Extraction**: Analyze color palettes and dominant colors
- **Quality Analysis**: Assess image resolution, quality, and technical specs
- **Visual Reasoning**: General-purpose visual Q&A

### 🎯 Supported Providers

- **Anthropic Claude** (claude-3-5-sonnet) - Primary, best for detailed analysis
- **OpenAI GPT-4o** - Fallback option
- **HuggingFace** - Open-source models (optional, requires GPU)

### 🤖 Agent Integration

- **CreativeAgent**: Visual asset analysis, quality checks, brand compliance
- **CommerceAgent**: Product image analysis, listing generation
- **MarketingAgent**: Visual content analysis, brand consistency

## Installation

Already installed! The following packages are included:

```bash
pip install llama-index-llms-openai
pip install llama-index-multi-modal-llms-anthropic
pip install llama-index-multi-modal-llms-huggingface
```

## Configuration

### Environment Variables

Set at least **one** of these API keys:

```bash
# Required: At least one provider
export ANTHROPIC_API_KEY="sk-ant-..."  # Recommended
export OPENAI_API_KEY="sk-..."         # Fallback

# Optional: For OSS models
export HUGGINGFACE_TOKEN="hf_..."
```

### Default Provider

By default, the system uses **Anthropic Claude** as the primary multimodal provider. You can override this:

```python
from agents.multimodal_capabilities import MultimodalProvider, get_multimodal_capabilities

capabilities = get_multimodal_capabilities(provider=MultimodalProvider.OPENAI)
```

## Usage

### Quick Start

```python
from agents.multimodal_capabilities import get_multimodal_capabilities

# Initialize
capabilities = get_multimodal_capabilities()
await capabilities.initialize()

# Analyze product image
result = await capabilities.analyze_product_image(
    image_path="product.jpg",
    product_type="clothing"
)

print(result.text_response)  # Detailed product description
```

### CreativeAgent Integration

The **CreativeAgent** has built-in multimodal tools:

```python
from agents.creative_agent import CreativeAgent

agent = CreativeAgent()
await agent.initialize()

# Analyze product
result = await agent.analyze_product_image_tool(
    image_path="bomber-jacket.jpg",
    product_type="clothing",
    include_technical=True
)

# Check brand compliance
compliance = await agent.check_brand_compliance_tool(
    image_path="marketing-photo.jpg",
    check_colors=True,
    check_quality=True
)

# Extract colors
colors = await agent.extract_image_colors_tool(
    image_path="product-photo.jpg"
)
```

### MCP Tool Access

All multimodal capabilities are exposed as MCP tools:

```json
{
  "tool": "analyze_product_image",
  "parameters": {
    "image_path": "assets/rose-gold-hoodie.jpg",
    "product_type": "clothing",
    "include_technical": true
  }
}
```

## API Reference

### MultimodalCapabilities

#### Core Methods

**`analyze_image(image_path, analysis_type, prompt, provider=None)`**

- General-purpose image analysis
- Custom prompts supported
- Returns: `ImageAnalysisResult`

**`analyze_product_image(image_path, product_type="clothing", include_technical=True)`**

- Generate e-commerce product descriptions
- Includes styling suggestions, material analysis
- Returns: `ImageAnalysisResult`

**`check_brand_compliance(image_path, brand_colors, brand_style)`**

- Verify alignment with brand guidelines
- Checks colors, style, quality
- Returns: `ImageAnalysisResult` with PASS/FAIL

**`extract_colors(image_path)`**

- Extract dominant color palette
- Includes hex codes and color harmony analysis
- Returns: `ImageAnalysisResult`

### ImageAnalysisResult

```python
@dataclass
class ImageAnalysisResult:
    analysis_type: AnalysisType          # Type of analysis performed
    provider: MultimodalProvider         # LLM provider used
    text_response: str                   # Analysis text
    confidence: float                    # Confidence score (0-1)
    metadata: dict[str, Any]             # Additional metadata
    image_url: str | None                # Base64 data URL
    processing_time_ms: float            # Processing time
```

### Analysis Types

```python
class AnalysisType(Enum):
    PRODUCT_DESCRIPTION = "product_description"
    QUALITY_CHECK = "quality_check"
    BRAND_COMPLIANCE = "brand_compliance"
    COLOR_ANALYSIS = "color_analysis"
    STYLE_ANALYSIS = "style_analysis"
    OBJECT_DETECTION = "object_detection"
    TEXT_EXTRACTION = "text_extraction"
    VISUAL_REASONING = "visual_reasoning"
```

## Examples

### 1. Product Listing Generation

```python
from agents.creative_agent import CreativeAgent

agent = CreativeAgent()
await agent.initialize()

result = await agent.analyze_product_image_tool(
    image_path="new-product.jpg",
    product_type="clothing",
    include_technical=True
)

if result["success"]:
    print(f"Product Description:\n{result['description']}")
    print(f"\nConfidence: {result['confidence']}")
    print(f"Provider: {result['provider']}")
```

**Output Example:**

```
Product Description:
## Rose Gold Bomber Jacket

**Product Type**: Premium bomber jacket with modern silhouette

**Visual Description**:
- Color: Distinctive rose gold (#B76E79) with subtle metallic sheen
- Pattern: Solid with tonal stitching details
- Style: Contemporary streetwear with luxury finishing

**Key Features**:
- Ribbed collar, cuffs, and hem
- Front zip closure with branded pull
- Side entry pockets
- Quilted interior lining

**Material/Fabric**: Appears to be premium nylon/polyester blend with
satin-like finish, fully lined for warmth

**Fit & Silhouette**: Relaxed fit, cropped length, dropped shoulders

**Styling Suggestions**:
- Pair with black joggers for casual luxury
- Layer over graphic tee for streetwear edge
- Style with tailored pants for elevated casual

Confidence: 0.95
Provider: anthropic
```

### 2. Brand Compliance Check

```python
compliance = await agent.check_brand_compliance_tool(
    image_path="campaign-photo.jpg",
    check_colors=True,
    check_quality=True
)

if compliance["compliant"]:
    print("✓ Image passes brand compliance")
else:
    print("✗ Brand compliance issues detected:")
    print(compliance["analysis"])
```

### 3. Color Palette Extraction

```python
colors = await agent.extract_image_colors_tool(
    image_path="product-photo.jpg"
)

print(f"Dominant Colors:\n{colors['colors']}")
```

**Output Example:**

```
Dominant Colors:
1. **Rose Gold** - #B76E79 (primary accent, 45% coverage)
2. **Obsidian Black** - #1A1A1A (secondary, 30% coverage)
3. **Soft Ivory** - #F5F5F5 (background, 20% coverage)

Color Harmony: Complementary with neutral base
Mood: Luxurious, sophisticated, warm
Recommendations: Excellent brand alignment, consider adding more white
for contrast
```

## Performance

### Processing Times

- **Product Analysis**: ~2-5 seconds
- **Brand Compliance**: ~2-4 seconds
- **Color Extraction**: ~1-3 seconds
- **Quality Analysis**: ~2-4 seconds

### Cost Estimates

- **Anthropic Claude**: ~$0.003 per image analysis
- **OpenAI GPT-4o**: ~$0.002 per image analysis

## Best Practices

### 1. Image Requirements

- **Format**: JPG, PNG, WebP, GIF
- **Size**: Max 20MB (base64 encoded)
- **Resolution**: Minimum 512x512 for quality analysis
- **Quality**: Clear, well-lit images for best results

### 2. Error Handling

```python
try:
    result = await capabilities.analyze_image(...)
    if result.confidence < 0.7:
        logger.warning("Low confidence result")
except FileNotFoundError:
    logger.error("Image file not found")
except Exception as e:
    logger.error(f"Analysis failed: {e}")
```

### 3. Performance Optimization

```python
# Initialize once, reuse
capabilities = get_multimodal_capabilities()
await capabilities.initialize()

# Process multiple images
results = await asyncio.gather(
    capabilities.analyze_product_image("img1.jpg", "clothing"),
    capabilities.analyze_product_image("img2.jpg", "jewelry"),
    capabilities.analyze_product_image("img3.jpg", "accessory")
)
```

## Troubleshooting

### No multimodal providers available

**Error**: `RuntimeError: No multimodal providers initialized`

**Solution**: Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variable

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Image not found

**Error**: `FileNotFoundError: Image not found: path/to/image.jpg`

**Solution**: Verify image path is correct and file exists

```python
from pathlib import Path

if not Path("image.jpg").exists():
    print("Image not found!")
```

### Low confidence results

**Issue**: Analysis confidence score below 0.7

**Solutions**:

- Use higher quality images
- Ensure image is well-lit and clear
- Try different provider (Anthropic vs OpenAI)
- Add more context in custom prompts

## Integration Points

### SkyyRose Brand DNA

The multimodal capabilities are pre-configured with SkyyRose brand guidelines:

```python
SKYYROSE_BRAND_DNA = {
    "primary_colors": ["#B76E79", "#1A1A1A", "#FFFFFF"],
    "color_names": ["rose_gold", "obsidian_black", "ivory"],
    "aesthetic": "luxury streetwear",
    "style": "bold, sophisticated, emotionally resonant",
    "quality": "premium, high-resolution, editorial",
}
```

### Prometheus Metrics

All multimodal operations emit metrics:

- `multimodal_analysis_total{type, provider}`
- `multimodal_processing_time_seconds{type, provider}`
- `multimodal_confidence_score{type, provider}`

## Roadmap

### Planned Features

- [ ] Video analysis support (via LlamaIndex video capabilities)
- [ ] Batch processing optimization
- [ ] Fine-tuned models for fashion/e-commerce
- [ ] Real-time image annotation
- [ ] Integration with WordPress media library

### Future Providers

- [ ] Google Gemini Vision
- [ ] Mistral Vision (when available)
- [ ] Local LLaVA models for privacy-sensitive applications

## Support

For issues or questions:

- **GitHub Issues**: <https://github.com/devskyy/devskyy/issues>
- **Email**: <dev@devskyy.com>
- **Docs**: <https://docs.devskyy.com/multimodal>

## License

MIT License - See LICENSE file for details

---

**Last Updated**: 2026-01-04
**Version**: 1.0.0
**Status**: Production Ready ✅
