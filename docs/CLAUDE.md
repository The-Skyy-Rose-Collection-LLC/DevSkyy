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

## USE THESE TOOLS (MANDATORY)
| Task | Tool |
|------|------|
| Update docs | **Agent**: `doc-updater` |
| Generate codemaps | **Command**: `/update-codemaps` |
| API docs | **MCP**: `tool_catalog` |

**"If it's not documented, it doesn't exist."**
