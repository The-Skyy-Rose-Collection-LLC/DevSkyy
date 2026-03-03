# DevSkyy API

> Versioned, documented, secure | FastAPI + GraphQL + WebSockets

## Structure

```
api/
├── versioning.py              # Version management
├── graphql_server.py          # GraphQL endpoint (/graphql)
├── graphql/                   # Strawberry schema, types, resolvers, dataloaders
├── v1/                        # Versioned REST endpoints (30 modules)
│   ├── agents.py              # Agent endpoints
│   ├── analytics.py           # Metrics
│   ├── gdpr.py                # Privacy
│   ├── health.py              # Health checks
│   ├── products.py            # Product CRUD
│   └── wordpress.py           # WP integration
├── admin_dashboard.py         # Admin API
├── webhooks.py                # Webhook handlers
├── websocket.py               # WebSocket connections
└── image-processing/          # Image pipeline API
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

## Verification

```bash
pytest tests/api/ -v
pytest tests/integration/ -v
```

**"Document every endpoint. Type every response."**
