# 3D / Immersive Venture

> Status: **beta** — surface scaffolded, agent wiring deferred.

3D model generation pipeline composing Tripo, Meshy, and TRELLIS via
the round-table tournament orchestrator. Feeds the `/experience-*`
immersive pages and the WordPress product gallery.

## Surface

```python
from skyyrose.elite_studio.ventures.threed import ThreeDPipeline, MANIFEST

pipeline = ThreeDPipeline()
result = pipeline.run_smoke(sku="br-001")
```

## CLI

```bash
python -m skyyrose.elite_studio.ventures.threed info
python -m skyyrose.elite_studio.ventures.threed agents
python -m skyyrose.elite_studio.ventures.threed status
python -m skyyrose.elite_studio.ventures.threed smoke --sku br-001
```

## Agent Roster

| Role              | Agent              | Wired |
| ----------------- | ------------------ | ----- |
| studio_3d         | ThreeDAgent        | no    |
| provider_tripo    | TripoAssetAgent    | no    |
| provider_meshy    | MeshyAgent         | no    |
| provider_trellis  | TrellisAgent       | no    |
| tournament        | threed_round_table | yes   |

## Roadmap

1. Wire `threed_round_table` into a `tournament` node that runs all
   enabled providers in parallel.
2. Wire a `score` node that picks the winning mesh on the round-table's
   composite metric.
3. Wire a `polish` node via Elite Studio's `ThreeDAgent` (texture refine,
   topology pass).
4. Wire an `upload` node that pushes the winning mesh to WordPress media.
5. Add a per-provider quarantine gate honoring the
   `tripo_dispatch.py` branded-SKU guard.
