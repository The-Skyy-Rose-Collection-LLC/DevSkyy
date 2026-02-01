# SkyyRose WordPress Site Structure

**Final Structure (As Per Original Plan)**

## Page Flow

```
Homepage (/)
    ↓
Immersive Experience (storytelling)
    ↓
Dedicated Catalog (shopping)
```

## Complete Site Map

### 1. Homepage
- **URL:** `/`
- **Template:** template-home.php
- **Page ID:** 12
- **Content:** Hero, 3 collection previews, featured products, brand story, newsletter

### 2. Black Rose Journey
- **Immersive:** `/black-rose/` (ID: 13, template-immersive.php)
  - Gothic elegance storytelling
  - 6 product previews
  - Manifesto: "For the ones who bloom in darkness"
  - CTA → Black Rose Catalog

- **Catalog:** `/black-rose-catalog/` (ID: 24, template-collection.php)
  - Full product grid (Black Rose collection only)
  - Shopping functionality
  - WooCommerce integration

### 3. Love Hurts Journey
- **Immersive:** `/love-hurts/` (ID: 14, template-immersive.php)
  - Romantic rebellion storytelling
  - 6 product previews
  - Manifesto: "Love is fierce"
  - CTA → Love Hurts Catalog

- **Catalog:** `/love-hurts-catalog/` (ID: 25, template-collection.php)
  - Full product grid (Love Hurts collection only)
  - Shopping functionality
  - WooCommerce integration

### 4. Signature Journey
- **Immersive:** `/signature/` (ID: 15, template-immersive.php)
  - Timeless luxury storytelling
  - 6 product previews
  - Manifesto: "Luxury is certain"
  - CTA → Signature Catalog

- **Catalog:** `/signature-catalog/` (ID: 26, template-collection.php)
  - Full product grid (Signature collection only)
  - Shopping functionality
  - WooCommerce integration

### 5. The Vault
- **URL:** `/the-vault/`
- **Template:** template-vault.php
- **Page ID:** 17
- **Content:** Pre-order page, 3 exclusive drops, countdown, signup form

### 6. General Collections Page
- **URL:** `/collections/`
- **Page ID:** 16
- **Template:** template-collection.php
- **Purpose:** General catalog view (all collections)

## Template System

### template-home.php
Full homepage with hero, collections grid, products, brand story

### template-immersive.php
Collection-specific immersive experience. Reads `_collection_type` meta:
- `black-rose` → Black Rose theming
- `love-hurts` → Love Hurts theming
- `signature` → Signature theming

Links to: `/{collection}-catalog/`

### template-collection.php
Product catalog grid. Reads `_collection_type` meta:
- `black-rose` → Shows only Black Rose products
- `love-hurts` → Shows only Love Hurts products
- `signature` → Shows only Signature products
- None → Shows all products

### template-vault.php
Exclusive pre-order page with limited edition drops

## User Journey Example

1. User lands on **Homepage** → Sees all 3 collections
2. Clicks "Black Rose" → **Black Rose Immersive** (storytelling experience)
3. Clicks "Explore Full Black Rose Catalog" → **Black Rose Catalog** (shopping)
4. Adds products to cart → WooCommerce checkout

## Page IDs Reference

```
HOME=12
BLACK_ROSE_IMMERSIVE=13
LOVE_HURTS_IMMERSIVE=14
SIGNATURE_IMMERSIVE=15
COLLECTIONS=16
THE_VAULT=17
BLACK_ROSE_CATALOG=24
LOVE_HURTS_CATALOG=25
SIGNATURE_CATALOG=26
```

## Key Design Principles

1. **Immersive = Storytelling** - Atmospheric, emotional, brand-focused
2. **Catalog = Shopping** - Grid view, filters, add to cart
3. **Each collection gets dedicated pages** - Not a general catch-all
4. **Clear CTAs** - Every immersive page leads to its catalog
5. **WooCommerce Integration** - Catalogs query products by collection meta

---

**This structure follows the original plan: 3 immersive experiences linking to 3 dedicated catalog pages.**
