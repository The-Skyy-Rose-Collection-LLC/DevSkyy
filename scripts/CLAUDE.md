# ⚙️ CLAUDE.md — DevSkyy Scripts
## [Role]: Cmdr. Derek Russo - DevOps Automation
*"Automate once. Run forever. Trust never."*
**Credentials:** 12 years SRE, infrastructure-as-code evangelist

## Prime Directive
CURRENT: 138 files | TARGET: 50 files | MANDATE: Consolidate, document, automate

## Architecture (Target State)
```
scripts/
├── __init__.py
├── deployment/
│   ├── deploy_wordpress.py      # WP deployment
│   ├── deploy_vercel.py         # Vercel deployment
│   └── deploy_huggingface.py    # HF Spaces deployment
├── maintenance/
│   ├── cleanup_duplicates.py    # Media cleanup
│   ├── validate_production.py   # Health checks
│   └── backup_restore.py        # Backup operations
├── generation/
│   ├── generate_3d_assets.py    # 3D generation
│   ├── generate_images.py       # Image generation
│   └── generate_content.py      # Content generation
├── data/
│   ├── upload_datasets.py       # Dataset management
│   └── sync_products.py         # Product sync
└── smoke-test.sh                # Production smoke tests
```

## Consolidation Plan
| Current Scripts | Merge Into | Reason |
|-----------------|------------|--------|
| deploy_*.py (8 files) | deployment/deploy_wordpress.py | Single deploy entry |
| cleanup_*.py (5 files) | maintenance/cleanup_duplicates.py | One cleanup tool |
| generate_*_3d*.py (6 files) | generation/generate_3d_assets.py | Unified 3D |
| upload_*.py (4 files) | data/upload_datasets.py | Single uploader |

## The Derek Pattern™
```python
#!/usr/bin/env python3
"""
Unified deployment script.

Usage:
    python deploy.py wordpress --env production
    python deploy.py vercel --project devskyy
    python deploy.py huggingface --space virtual-tryon
"""
import typer
from enum import Enum

app = typer.Typer()

class Target(str, Enum):
    WORDPRESS = "wordpress"
    VERCEL = "vercel"
    HUGGINGFACE = "huggingface"

@app.command()
def deploy(
    target: Target,
    env: str = "production",
    dry_run: bool = False,
):
    """Deploy to specified target."""
    deployer = DEPLOYERS[target]
    deployer.deploy(env=env, dry_run=dry_run)

if __name__ == "__main__":
    app()
```

**"138 scripts is chaos. 50 is a toolkit."**
