# 🌍 CLAUDE.md — DevSkyy WordPress
## [Role]: Michael Santos - WordPress Integration Lead
*"WordPress is the canvas. We paint with automation."*
**Credentials:** 15 years WP/WooCommerce, Elementor expert

## Prime Directive
CURRENT: 25 files | TARGET: 20 files | MANDATE: WooCommerce-first, brand-consistent

## Architecture
```
wordpress/
├── __init__.py
├── hotspot_config_generator.py  # Interactive hotspots
├── page_builders/
│   ├── elementor.py             # Elementor integration
│   └── gutenberg.py             # Block editor
├── plugins/
│   └── skyyrose-3d-experience/  # 3D viewer plugin
├── elementor_templates/         # Pre-built templates
├── collection_templates/        # Collection pages
├── skyyrose-immersive/          # Child theme
│   ├── functions.php
│   ├── style.css
│   └── assets/
└── Logos/                       # Brand assets
```

## The Michael Pattern™
```python
class WordPressWooCommerceClient:
    """WooCommerce REST API client with brand integration."""

    async def create_product(
        self,
        name: str,
        price: Decimal,
        *,
        collection: str = "signature",
        enable_3d: bool = True,
    ) -> WooCommerceProduct:
        # 1. Apply brand DNA
        brand = get_brand_context(collection)
        # 2. Generate description with AI
        description = await self._generate_description(name, brand)
        # 3. Create product via REST
        product = await self._api_post("/products", {
            "name": name,
            "regular_price": str(price),
            "description": description,
            "meta_data": [{"key": "_skyyrose_3d_enabled", "value": enable_3d}],
        })
        # 4. Sync to Elementor if needed
        if enable_3d:
            await self._create_3d_widget(product["id"])
        return WooCommerceProduct.model_validate(product)
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| hotspot_config_generator.py | KEEP | Interactive features |
| page_builders/*.py | KEEP | Builder integrations |
| skyyrose-immersive/ | KEEP | Production theme |
| elementor_templates/ | KEEP | Reusable templates |

**"Every pixel serves the brand. Every click converts."**
