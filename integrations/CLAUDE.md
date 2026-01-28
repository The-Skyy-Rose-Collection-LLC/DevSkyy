# DevSkyy Integrations

> Typed clients, retry logic, circuit breakers | 15 files

## Clients
```
integrations/
├── wordpress_client.py      # WordPress/WooCommerce
├── huggingface_client.py    # HuggingFace Hub
├── tripo_client.py          # Tripo3D
├── fashn_client.py          # FASHN try-on
├── stripe_client.py         # Payments
└── base_client.py           # Shared HTTP client
```

## Pattern
```python
class BaseIntegrationClient:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(self, method: str, path: str, **kwargs) -> dict:
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

class WordPressClient(BaseIntegrationClient):
    async def create_product(self, product: ProductCreate) -> WooCommerceProduct:
        return WooCommerceProduct.model_validate(await self._request("POST", "/wp-json/wc/v3/products", json=product.model_dump()))
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| WordPress | **MCP**: `generate_wordpress_theme`, `wpcom-mcp-*` |
| HuggingFace | **MCP** (HF): `model_search`, `dataset_search` |
| 3D | **MCP**: `generate_3d_from_image`, `generate_3d_from_description` |
| Try-on | **MCP**: `virtual_tryon` |

**"Integrations fail. Good integrations recover."**
