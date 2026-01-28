# DevSkyy Pipelines

> Idempotent, observable, recoverable | 4 files

## Architecture
```
pipelines/
├── flux_orchestrator.py          # FLUX model orchestration
├── skyyrose_luxury_pipeline.py   # Brand pipeline
└── skyyrose_master_orchestrator.py # Multi-stage
```

## Pattern
```python
class PipelineStage(str, Enum):
    INGEST = "ingest"
    TRANSFORM = "transform"
    GENERATE = "generate"
    VALIDATE = "validate"
    EXPORT = "export"

class LuxuryPipeline:
    async def execute(self, input_data: dict) -> list[PipelineResult]:
        for stage in PipelineStage:
            result = await self._execute_stage(stage, input_data)
            if not result.success:
                break  # Fail fast
        return results
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| 3D generation | **MCP**: `generate_3d_from_description` |
| LoRA generation | **MCP**: `lora_generate` |
| Pipeline errors | **Agent**: `build-error-resolver` |

**"Build pipelines that heal themselves."**
