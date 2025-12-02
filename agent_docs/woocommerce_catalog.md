# WooCommerce Catalog Management

**Purpose**: Standard procedures for inventory, pricing, and product CRUD operations.

---

## Product Structure

### Product Types
| Type | Use Case | Example |
|------|----------|---------|
| Simple | Single item, no variations | Accessories |
| Variable | Multiple options | Apparel with sizes/colors |
| Grouped | Related products | Outfit bundles |
| External | Affiliate products | Partner items |

### Required Fields
Every product must have:
- SKU (format: `SR-{CATEGORY}-{SEQUENCE}`)
- Title (brand voice compliant)
- Description (see templates below)
- Price
- At least 3 product images
- Category assignment
- Stock status

---

## SKU Format

```
SR-{CAT}-{SEQ}

Categories:
- TOP = Tops (hoodies, t-shirts, jackets)
- BTM = Bottoms (pants, shorts)
- ACC = Accessories (hats, bags, jewelry)
- FTW = Footwear
- SET = Sets/Bundles

Examples:
- SR-TOP-001 = First hoodie
- SR-BTM-042 = 42nd bottom item
- SR-ACC-015 = 15th accessory
```

---

## Pricing Guidelines

### Standard Markup
| Category | Cost Multiplier | Example |
|----------|-----------------|---------|
| Tops | 3.5x | $40 cost → $140 retail |
| Bottoms | 3.2x | $35 cost → $112 retail |
| Accessories | 4.0x | $15 cost → $60 retail |
| Limited Edition | 4.5x | Premium pricing |

### Price Change Boundaries

| Change | Action Required |
|--------|-----------------|
| < 10% | Execute autonomously |
| 10-20% | Log and notify |
| > 20% | **CEO approval required** |

```python
# Price change validation
def validate_price_change(old_price: float, new_price: float) -> str:
    change_pct = abs(new_price - old_price) / old_price * 100

    if change_pct < 10:
        return "EXECUTE"
    elif change_pct <= 20:
        return "LOG_AND_NOTIFY"
    else:
        return "REQUIRES_APPROVAL"
```

---

## Product CRUD Operations

### Create Product

```python
# API endpoint
POST /wp-json/wc/v3/products

# Required payload
{
    "name": "Oakland Skyline Hoodie",
    "type": "variable",
    "status": "draft",  # Always create as draft first
    "sku": "SR-TOP-045",
    "description": "...",  # See brand_voice.md
    "short_description": "...",
    "regular_price": "140.00",
    "categories": [{"id": 15}],
    "images": [
        {"src": "https://skyyrose.co/wp-content/uploads/..."}
    ],
    "attributes": [
        {
            "name": "Size",
            "options": ["S", "M", "L", "XL", "2XL"],
            "visible": true,
            "variation": true
        },
        {
            "name": "Color",
            "options": ["Black", "Navy", "Heather Grey"],
            "visible": true,
            "variation": true
        }
    ]
}
```

### Update Product

```python
# API endpoint
PUT /wp-json/wc/v3/products/{id}

# Log all updates
{
    "timestamp": "2025-12-02T10:30:00Z",
    "product_id": 123,
    "sku": "SR-TOP-045",
    "changes": {
        "regular_price": {"old": "140.00", "new": "150.00"},
        "stock_quantity": {"old": 50, "new": 45}
    },
    "agent": "inventory_agent"
}
```

### Delete Product

⚠️ **REQUIRES CEO APPROVAL**

Never hard-delete products. Instead:
1. Set status to "private"
2. Add `[ARCHIVED]` prefix to title
3. Log the archival action
4. Escalate per `escalation_protocol.md`

---

## Inventory Management

### Stock Status Rules
| Quantity | Status | Action |
|----------|--------|--------|
| > 10 | In Stock | Normal display |
| 5-10 | Low Stock | Add "Only X left" badge |
| 1-4 | Very Low | Add urgency messaging |
| 0 | Out of Stock | Hide from catalog, notify team |

### Reorder Points
```python
REORDER_THRESHOLDS = {
    "tops": 15,
    "bottoms": 10,
    "accessories": 20,
    "limited_edition": 5  # No reorder, notify only
}
```

### Inventory Sync
- Sync frequency: Every 15 minutes
- Source of truth: WooCommerce database
- Conflict resolution: See `conflict_resolution.md`

---

## Category Structure

```
Shop
├── New Arrivals
├── Collections
│   ├── Oakland Heritage
│   ├── Elevated Essentials
│   └── Limited Drops
├── Tops
│   ├── Hoodies
│   ├── T-Shirts
│   └── Jackets
├── Bottoms
│   ├── Pants
│   └── Shorts
├── Accessories
│   ├── Hats
│   ├── Bags
│   └── Jewelry
└── Sale  # Use sparingly, see brand_voice.md
```

---

## Product Images

### Requirements
| Position | Purpose | Specs |
|----------|---------|-------|
| Main | Hero shot | 1000x1000, white/neutral bg |
| Alt 1 | Detail shot | 1000x1000, texture/stitching |
| Alt 2 | Lifestyle | 1000x1000, model/context |
| Alt 3+ | Additional angles | 1000x1000, as needed |

### Image Naming Convention
```
{sku}_{position}_{color}.{ext}

Examples:
- SR-TOP-045_main_black.webp
- SR-TOP-045_detail_black.webp
- SR-TOP-045_lifestyle_black.webp
```

---

## Bulk Operations

### Import Format (CSV)
```csv
sku,name,regular_price,stock_quantity,categories
SR-TOP-046,Urban Night Tee,65.00,100,"Tops > T-Shirts"
SR-TOP-047,Skyline Crewneck,95.00,75,"Tops > Hoodies"
```

### Export Schedule
- Full catalog: Weekly (Sunday 2 AM)
- Inventory only: Daily (6 AM)
- Price changes: On-demand

---

## Prohibited Actions

🚫 **Never do these without escalation**:
- Delete products (archive instead)
- Change prices > 20%
- Create "sale" or "clearance" categories
- Modify SKU format
- Bulk update > 50 products at once

---

## Logging Requirements

All catalog operations must be logged:

```json
{
    "timestamp": "2025-12-02T10:30:00Z",
    "operation": "product_update",
    "product_id": 123,
    "sku": "SR-TOP-045",
    "agent": "catalog_agent",
    "changes": {
        "field": "stock_quantity",
        "old_value": 50,
        "new_value": 45
    },
    "status": "success"
}
```

Log location: `/logs/woocommerce_catalog.log`

---

## API Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Products | 100 | per minute |
| Orders | 50 | per minute |
| Customers | 50 | per minute |
| Reports | 25 | per minute |

Implement exponential backoff on 429 responses.

---

**Last Updated**: 2025-12-02
**Owner**: E-commerce Team
**Review Cycle**: Monthly
