# Elite Studio — Layer Handoffs

Each layer is a self-contained Claude Code session with its own worktree.

## Dependency Order

```
Layer 1 (Graph Engine)  ← DONE ✓ — merged to wp-theme-work
    ├── Layer 2 (Pipeline Stages) ──────────┐  ← can run in parallel
    ├── Layer 3 (Production Infra) ──────────┤  ← can run in parallel
    │                                         ↓
    │                                    Layer 4 (Quality System)
    │                                         ↓
    │                                    Layer 5 (API & Observability)
    │                                         ↓
    └──────────────────────────────────  Layer 6 (Virtual Try-On)
```

## How to Start a Layer

1. From `/Users/theceo/DevSkyy`, run the setup script:
   ```bash
   bash tasks/handoffs/layer-N-setup.sh
   ```

2. Open a new terminal and navigate to the worktree:
   ```bash
   cd ../elite-layer-N
   claude
   ```

3. Paste the entire contents of `tasks/handoffs/layer-N-prompt.md` as your first message.

## Layer Status

| Layer | Branch | Status | Depends On |
|-------|--------|--------|------------|
| 1 | `elite/layer-1-graph-engine` | **DONE ✓** | — |
| 2 | `elite/layer-2-pipeline-stages` | pending | Layer 1 |
| 3 | `elite/layer-3-production-infra` | pending | Layer 1 |
| 4 | `elite/layer-4-quality-system` | pending | Layers 2+3 |
| 5 | `elite/layer-5-api-observability` | pending | Layers 3+4 |
| 6 | `elite/layer-6-virtual-tryon` | pending | Layers 1+5 |

## Merge Order

After each layer's tests pass (85%+ coverage):
```bash
# From main worktree (/Users/theceo/DevSkyy)
git merge elite/layer-N-<name>
```

Merge Layers 2 and 3 before starting Layer 4.
Merge Layers 3 and 4 before starting Layer 5.
Merge Layers 1 and 5 before starting Layer 6.
