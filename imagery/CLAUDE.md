# DevSkyy Imagery

> 95% fidelity, brand-consistent visuals | 14 files

## Architecture
```
imagery/
├── sdxl_pipeline.py           # SDXL generation
├── virtual_photoshoot.py      # AI model photography
├── lora_trainer.py            # LoRA fine-tuning
├── quality_gate.py            # Quality assurance
└── luxury_photography.py      # Premium styles
```

## Pattern
```python
class SDXLPipeline:
    async def generate(self, prompt: str, *, quality: ImageQuality = ImageQuality.STANDARD) -> GenerationResult:
        enhanced_prompt = self._apply_brand_style(prompt)
        image = await self._generate_with_retry(enhanced_prompt)
        score = self._calculate_fidelity(image)
        if score < 0.95:
            log.warning("fidelity_below_threshold", score=score)
        return GenerationResult(image_url=..., fidelity_score=score)
```

## Quality Targets
| Metric | Target |
|--------|--------|
| Fidelity | >0.95 |
| Brand Consistency | 100% |
| Time | <15s |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS (MANDATORY)
| Task | Tool |
|------|------|
| Brand context | **MCP**: `brand_context` |
| Model search | **MCP**: HuggingFace `model_search` |
| Visual review | **Agent**: `creative_agent` via orchestrator |

**"Luxury is in the details."**
