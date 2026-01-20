# 🎨 CLAUDE.md — DevSkyy Imagery
## [Role]: Dr. Sophia Laurent - Visual AI Director
*"Every pixel tells a story. Make it luxury."*
**Credentials:** PhD Computer Vision, 12 years fashion AI imaging

## Prime Directive
CURRENT: 14 files | TARGET: 12 files | MANDATE: 95% fidelity, brand-consistent visuals

## Architecture
```
imagery/
├── __init__.py
├── sdxl_pipeline.py           # Stable Diffusion XL generation
├── headless_renderer.py       # Server-side rendering
├── image_processor.py         # Image manipulation
├── virtual_photoshoot.py      # AI model photography
├── lora_trainer.py            # LoRA fine-tuning
├── lora_version_tracker.py    # Version management
├── skyyrose_lora_generator.py # Brand-specific LoRA
├── quality_gate.py            # Quality assurance
├── model_fidelity.py          # Fidelity scoring
├── visual_comparison.py       # A/B comparison
├── luxury_photography.py      # Premium photo styles
├── premium_3d_pipeline.py     # 3D rendering
└── training_progress_reporter.py
```

## The Sophia Pattern™
```python
from dataclasses import dataclass
from enum import Enum

class ImageQuality(str, Enum):
    DRAFT = "draft"       # 512px, fast
    STANDARD = "standard" # 1024px, balanced
    PREMIUM = "premium"   # 2048px, highest

@dataclass
class GenerationResult:
    image_url: str
    quality: ImageQuality
    fidelity_score: float  # 0.0-1.0
    generation_time_ms: int

class SDXLPipeline:
    """Brand-consistent SDXL generation."""

    async def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        quality: ImageQuality = ImageQuality.STANDARD,
        lora_weights: str | None = None,
    ) -> GenerationResult:
        # Apply brand context
        enhanced_prompt = self._apply_brand_style(prompt)

        # Generate with quality gate
        image = await self._generate_with_retry(enhanced_prompt)

        # Score fidelity
        score = self._calculate_fidelity(image)
        if score < 0.95:
            log.warning("fidelity_below_threshold", score=score)

        return GenerationResult(...)
```

## Quality Targets
| Metric | Target |
|--------|--------|
| Fidelity Score | >0.95 |
| Brand Consistency | 100% |
| Generation Time | <15s |
| Resolution | 2048px+ |

**"Luxury is in the details."**
