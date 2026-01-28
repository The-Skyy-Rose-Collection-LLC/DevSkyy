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

## USE THESE TOOLS
| Task | Tool |
|------|------|
| 3D generation | **MCP**: `3d_generate` |
| Brand assets | **MCP**: `brand_context` |
| Pipeline errors | **Agent**: `build-error-resolver` |
| Visual tasks | **Agent**: `creative_agent` via orchestrator |

**"Build pipelines that heal themselves."**
