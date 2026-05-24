# Photo Venture — Editorial Photography

> Status: **beta** — surface scaffolded, agent wiring deferred.

Lifestyle and editorial photography pipeline layered on the Elite
Studio image generation stack.

## Surface

```python
from skyyrose.elite_studio.ventures.photo import PhotoPipeline, MANIFEST

pipeline = PhotoPipeline()
result = pipeline.run_smoke(sku="br-001")  # PipelineResult
```

## CLI

```bash
python -m skyyrose.elite_studio.ventures.photo info
python -m skyyrose.elite_studio.ventures.photo agents
python -m skyyrose.elite_studio.ventures.photo status
python -m skyyrose.elite_studio.ventures.photo smoke --sku br-001
```

## Agent Roster

| Role               | Agent                  | Wired |
| ------------------ | ---------------------- | ----- |
| vision             | VisionAgent            | no    |
| renderer           | GeneratorAgent         | no    |
| quality            | QualityAgent           | no    |
| prompt             | PromptEnrichmentAgent  | no    |
| standards_director | PhotographyDirector    | yes   |

All imports are verified by `tests/test_smoke.py`.

## Roadmap

1. Wire `PromptEnrichmentAgent` into a `prompt_enrich` node that pulls
   the matching `PhotographyStandard` from `fashion.photography`.
2. Wire `VisionAgent` into a `scene_audit` node.
3. Wire `GeneratorAgent` into a `render` node respecting style/lighting.
4. Wire `QualityAgent` into a `qc_gate` with editorial rubric.
5. Add a retouch / variant fan-out node.
6. Add an upload node that pushes selected frames to WordPress media.
