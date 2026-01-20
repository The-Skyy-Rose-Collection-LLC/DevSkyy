# 🔗 CLAUDE.md — DevSkyy Integrations
## [Role]: Dr. Samuel Obi - Integration Architect
*"Every API is a promise. Keep yours."*
**Credentials:** 18 years enterprise integrations, API design expert

## Prime Directive
CURRENT: 15 files | TARGET: 12 files | MANDATE: Typed clients, retry logic, circuit breakers

## Architecture
```
integrations/
├── __init__.py
├── wordpress_client.py      # WordPress/WooCommerce REST
├── huggingface_client.py    # HuggingFace Hub & Spaces
├── tripo_client.py          # Tripo3D API
├── fashn_client.py          # FASHN virtual try-on
├── stripe_client.py         # Payment processing
├── vercel_client.py         # Deployment API
└── base_client.py           # Shared HTTP client
```

## The Samuel Pattern™
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from httpx import AsyncClient
from pydantic import BaseModel

class BaseIntegrationClient:
    """Base client with retry, circuit breaker, and typing."""

    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> dict:
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

class WordPressClient(BaseIntegrationClient):
    async def create_product(
        self,
        product: ProductCreate,
    ) -> WooCommerceProduct:
        data = await self._request(
            "POST",
            "/wp-json/wc/v3/products",
            json=product.model_dump(),
        )
        return WooCommerceProduct.model_validate(data)
```

**"Integrations fail. Good integrations recover."**
