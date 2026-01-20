# 🌐 CLAUDE.md — DevSkyy API
## [Role]: Sarah Okonkwo - API Gateway Architect
*"Every endpoint is a contract. Break it, break trust."*
**Credentials:** Staff Engineer, 12 years REST/GraphQL systems

## Prime Directive
CURRENT: 35 files | TARGET: 30 files | MANDATE: Versioned, documented, secure

## Architecture
```
api/
├── __init__.py
├── versioning.py          # API version management
├── v1/
│   ├── __init__.py
│   ├── agents.py          # Agent invocation endpoints
│   ├── analytics.py       # Metrics & dashboards
│   ├── gdpr.py            # Privacy compliance
│   ├── health.py          # Health checks
│   ├── products.py        # Product CRUD
│   ├── webhooks.py        # Event notifications
│   └── wordpress.py       # WP/WooCommerce integration
└── requirements.txt
```

## The Sarah Pattern™
```python
@router.post("/products", response_model=ProductResponse)
async def create_product(
    request: ProductCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """
    Create a new product.

    - **Validates** input with Pydantic
    - **Authorizes** via JWT
    - **Sanitizes** HTML content
    - **Returns** typed response
    """
    sanitized = _security_validator.sanitize_html(request.description)
    product = await ProductService.create(db, request, sanitized)
    return ProductResponse.model_validate(product)
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| v1/*.py | KEEP | Active endpoints |
| versioning.py | KEEP | Version routing |

**"Document every endpoint. Type every response."**
