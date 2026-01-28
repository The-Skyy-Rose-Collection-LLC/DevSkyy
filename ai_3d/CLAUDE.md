# DevSkyy AI 3D

> 95% fidelity, <30s generation | 10 files

## Architecture
```
ai_3d/
├── tripo_pipeline.py       # Tripo3D integration
├── mesh_optimizer.py       # Geometry optimization
├── texture_generator.py    # AI texture synthesis
├── viewer_export.py        # Three.js/glTF export
└── quality_metrics.py      # Fidelity scoring
```

## Pattern
```python
class Tripo3DPipeline:
    async def generate(self, prompt: str, reference_image: str | None = None) -> Model3DResult:
        task = await self.client.create_task(prompt=prompt, image_url=reference_image)
        result = await self._wait_for_task(task.id)
        result = await self._optimize_mesh(result)
        score = await self._calculate_fidelity(result, reference_image)
        return Model3DResult(model_url=result.model_url, fidelity_score=score)
```

## Quality Targets
| Metric | Target |
|--------|--------|
| Fidelity | >0.95 |
| Time | <30s |
| Vertices | <100k |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS (MANDATORY)
| Task | Tool |
|------|------|
| 3D generation | **MCP**: `3d_generate` |
| WordPress sync | **MCP**: `wordpress_sync` |
| Quality review | **Agent**: `code-reviewer` |

**"3D or it didn't happen."**
