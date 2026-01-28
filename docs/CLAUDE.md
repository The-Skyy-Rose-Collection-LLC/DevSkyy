# DevSkyy Documentation

> Accurate, searchable, up-to-date | 50+ files

## Architecture
```
docs/
├── architecture/           # DEVSKYY_MASTER_PLAN.md
├── api/                    # API reference
├── guides/                 # How-to guides
├── runbooks/               # Operational runbooks
└── security/               # ZERO_TRUST_ARCHITECTURE.md
```

## Pattern
```markdown
# Feature Name
## Overview
Brief description.
## Quick Start
\`\`\`bash
pip install devskyy && devskyy serve
\`\`\`
## API Reference
| Endpoint | Method | Description |
## Troubleshooting
Common issues and solutions.
```

## Documentation Types
| Type | Purpose | Location |
|------|---------|----------|
| Reference | API specs | docs/api/ |
| Guides | How-to | docs/guides/ |
| Runbooks | Operations | docs/runbooks/ |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Update docs | **Agent**: `doc-updater` |
| Generate codemaps | **Command**: `/update-codemaps` |

**"If it's not documented, it doesn't exist."**
