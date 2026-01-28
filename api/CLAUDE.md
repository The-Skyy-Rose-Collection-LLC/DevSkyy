# DevSkyy API

> Versioned, documented, secure | 35 files

## Architecture
```
api/
├── versioning.py          # Version management
└── v1/
    ├── agents.py          # Agent endpoints
    ├── analytics.py       # Metrics
    ├── gdpr.py            # Privacy
    ├── health.py          # Health checks
    ├── products.py        # Product CRUD
    └── wordpress.py       # WP integration
```

## Pattern
```python
@router.post("/products", response_model=ProductResponse)
async def create_product(
    request: ProductCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    sanitized = _security_validator.sanitize_html(request.description)
    product = await ProductService.create(db, request, sanitized)
    return ProductResponse.model_validate(product)
```

## USE THESE TOOLS (MANDATORY)
| Task | Tool |
|------|------|
| New endpoints | **Agent**: `tdd-guide` (tests first) |
| Auth/security | **Agent**: `security-reviewer` (ALWAYS) |
| API docs | **MCP**: `tool_catalog` |
| WordPress | **MCP**: `wordpress_sync` |

**"Document every endpoint. Type every response."**
