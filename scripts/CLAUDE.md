# DevSkyy Scripts

> Consolidate, document, automate | 138→50 files

## Target Architecture
```
scripts/
├── deployment/           # deploy_wordpress, deploy_vercel, deploy_hf
├── maintenance/          # cleanup, validate, backup
├── generation/           # 3d_assets, images, content
├── data/                 # upload_datasets, sync_products
└── smoke-test.sh         # Production tests
```

## Pattern
```python
@app.command()
def deploy(target: Target, env: str = "production", dry_run: bool = False):
    """Deploy to specified target (wordpress, vercel, huggingface)."""
    DEPLOYERS[target].deploy(env=env, dry_run=dry_run)
```

## Consolidation
| Current | Merge Into |
|---------|------------|
| deploy_*.py (8) | deployment/deploy.py |
| cleanup_*.py (5) | maintenance/cleanup.py |
| generate_*_3d*.py (6) | generation/3d_assets.py |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| WordPress deploy | **MCP**: `generate_wordpress_theme` |
| Vercel deploy | **MCP** (Vercel): `deploy_to_vercel` |
| 3D generation | **MCP**: `generate_3d_from_description` |

**"138 scripts is chaos. 50 is a toolkit."**
