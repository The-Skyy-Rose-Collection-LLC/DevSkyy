# Shopify Knowledge Base

## Theme Architecture (Dawn 2.0 / Online Store 2.0)

### Directory Structure
```
theme/
├── assets/            # CSS, JS, images (compiled)
├── config/
│   ├── settings_schema.json   # Theme settings UI definition
│   └── settings_data.json     # Current settings values
├── layout/
│   └── theme.liquid           # Main layout wrapper
├── locales/           # Translation files (en.default.json)
├── sections/          # Reusable section files
├── snippets/          # Reusable partial templates
├── blocks/            # App blocks and theme blocks
└── templates/
    ├── index.json     # Homepage (JSON template)
    ├── product.json   # Product page
    ├── collection.json # Collection page
    ├── page.json      # Generic page
    ├── cart.json       # Cart page
    └── customers/     # Account pages
```

## Liquid Fundamentals

### Objects (Output)
```liquid
{{ product.title }}
{{ product.price | money }}
{{ product.featured_image | img_url: '400x' }}
{{ collection.description }}
{{ shop.name }}
```

### Tags (Logic)
```liquid
{% if product.available %}
  <button>Add to Cart</button>
{% else %}
  <span>Sold Out</span>
{% endif %}

{% for product in collection.products %}
  {{ product.title }}
{% endfor %}

{% assign featured = collections['featured'] %}
{% capture greeting %}Hello {{ customer.first_name }}{% endcapture %}
```

### Filters
```liquid
{{ product.price | money }}
{{ product.title | downcase | replace: ' ', '-' }}
{{ 'style.css' | asset_url | stylesheet_tag }}
{{ product.featured_image | img_url: '800x' | image_tag }}
{{ 'now' | date: '%Y-%m-%d' }}
{{ product.description | strip_html | truncate: 150 }}
```

## settings_schema.json

Defines theme settings UI in Shopify admin:
```json
[
  {
    "name": "theme_info",
    "theme_name": "SkyyRose",
    "theme_version": "1.0.0"
  },
  {
    "name": "Colors",
    "settings": [
      {
        "type": "color",
        "id": "color_primary",
        "label": "Primary color",
        "default": "#B76E79"
      },
      {
        "type": "color",
        "id": "color_secondary",
        "label": "Secondary color",
        "default": "#D4AF37"
      }
    ]
  },
  {
    "name": "Typography",
    "settings": [
      {
        "type": "font_picker",
        "id": "heading_font",
        "label": "Heading font",
        "default": "playfair_display_n4"
      }
    ]
  }
]
```

## Online Store 2.0

### JSON Templates
Templates reference sections by ID, enabling drag-and-drop customization:
```json
{
  "sections": {
    "main": {
      "type": "main-product",
      "settings": {}
    },
    "recommendations": {
      "type": "product-recommendations",
      "settings": { "heading": "You may also like" }
    }
  },
  "order": ["main", "recommendations"]
}
```

### Metafields and Metaobjects
- Product metafields: `product.metafields.custom.care_instructions`
- Metaobjects: Custom content types (lookbooks, size guides)
- Access via Liquid: `{{ product.metafields.namespace.key }}`

## Storefront API (GraphQL)

### Product Query
```graphql
query ProductByHandle($handle: String!) {
  productByHandle(handle: $handle) {
    id
    title
    description
    priceRange { minVariantPrice { amount currencyCode } }
    images(first: 5) { edges { node { url altText } } }
    variants(first: 10) { edges { node { id title price { amount } } } }
  }
}
```

### Cart Mutations
```graphql
mutation CartCreate($input: CartInput!) {
  cartCreate(input: $input) {
    cart { id checkoutUrl lines(first: 10) { edges { node { quantity } } } }
  }
}
```

## Admin API

### Product CRUD
- `POST /admin/api/2024-01/products.json` — Create product
- `GET /admin/api/2024-01/products/{id}.json` — Get product
- `PUT /admin/api/2024-01/products/{id}.json` — Update product
- Authentication: `X-Shopify-Access-Token` header

### Webhooks
- `orders/create`, `orders/paid`, `orders/fulfilled`
- `products/create`, `products/update`, `products/delete`
- `carts/create`, `carts/update`

## Shopify Functions
- Custom discounts: `shopify.function.discount`
- Payment customizations: `shopify.function.payment_customization`
- Delivery customizations: `shopify.function.delivery_customization`
- Written in Rust/Wasm or JavaScript

## Compliance Rules
- **Legal pages required**: Privacy Policy, Refund Policy, Terms of Service, Shipping Policy
- **GDPR**: Cookie consent banner, data deletion request support
- **PCI DSS**: Shopify handles PCI compliance for checkout
- **ADA/WCAG**: Minimum AA contrast, alt text, keyboard nav

## Performance Best Practices
- Use `asset_url` for theme assets (Shopify CDN)
- Lazy load images below the fold
- Critical CSS inline in `<head>`
- Avoid `document.write` and synchronous scripts
- Use section rendering API for dynamic updates
- Preconnect to `cdn.shopify.com`

## Common Mistakes
- Hardcoding prices (use `| money` filter)
- Missing `alt` on images (`| image_tag` includes alt)
- Blocking scripts in `<head>` (use `defer` attribute)
- Not using `| escape` on user-generated content
- Assuming product.available without checking variants
- Using `asset_url` for external resources (use full URL)
