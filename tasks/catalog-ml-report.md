# Catalog ML Audit Report

- SKUs analysed: **33**
- Collections: black-rose, kids-capsule, love-hurts, signature
- Embedding model: `openai/clip-vit-base-patch32` (512-d)

## 1. Visual clustering vs collections (k=4)

- **Silhouette score:** 0.1645 (higher = clusters more separable; >0.5 is strong)
- **Disagreements:** 5 SKUs land in a cluster whose dominant collection is NOT the SKU's collection.

| sku | name | tagged | ML guess |
|-----|------|--------|----------|
| `kids-001` | Kids Colorblock Hoodie Set — Red/Black | kids-capsule | **love-hurts** |
| `kids-002` | Kids Colorblock Hoodie Set — Purple/Black | kids-capsule | **black-rose** |
| `sg-001` | The Bridge Series 'The Bay Bridge' Shorts | signature | **black-rose** |
| `sg-002` | The Bridge Series 'Stay Golden' Shirt | signature | **black-rose** |
| `sg-007` | The Signature Beanie | signature | **black-rose** |

## 2. Per-collection visual outliers

Lowest cosine to its collection centroid = most visually unlike its peers.

| collection | size | outlier sku | name | cosine | best |
|-----------|-----:|-------------|------|-------:|-----:|
| black-rose | 14 | `br-012` | BLACK is Beautiful Jersey Series: 5. Baseball Classic (Last Oakland) | 0.661 | 0.941 |
| signature | 12 | `sg-007` | The Signature Beanie | 0.704 | 0.927 |
| love-hurts | 5 | `lh-005` | The Fannie | 0.804 | 0.942 |
| kids-capsule | 2 | `kids-002` | Kids Colorblock Hoodie Set — Purple/Black | 0.919 | 0.919 |

## 3. Name vs image alignment (lowest = potential mis-attached image)

CLIP cosine between the product NAME (text) and its IMAGE (vision).
Low score = name and image are about different things.

| sku | collection | name | cosine |
|-----|-----------|------|-------:|
| `lh-006` | love-hurts | Love Hurts Joggers (White) | 0.234 |
| `lh-003` | love-hurts | Love Hurts Basketball Shorts | 0.240 |
| `sg-011` | signature | Original Label Tee (White) | 0.242 |
| `lh-005` | love-hurts | The Fannie | 0.247 |
| `lh-002` | love-hurts | Love Hurts Joggers (Black) | 0.247 |
| `br-006` | black-rose | BLACK Rose Sherpa Jacket | 0.247 |
| `kids-001` | kids-capsule | Kids Colorblock Hoodie Set — Red/Black | 0.250 |
| `br-004` | black-rose | BLACK Rose Hoodie | 0.253 |
| `sg-012` | signature | Original Label Tee (Orchid) | 0.255 |
| `lh-004` | love-hurts | Love Hurts Bomber Jacket | 0.264 |
| `br-001` | black-rose | BLACK Rose Crewneck | 0.266 |
| `sg-009` | signature | The Sherpa Jacket | 0.269 |
| `sg-015` | signature | The Windbreaker Set | 0.269 |
| `sg-002` | signature | The Bridge Series 'Stay Golden' Shirt | 0.270 |
| `br-010` | black-rose | BLACK is Beautiful Jersey Series: 3. The Bay (Basketball) | 0.270 |

_(showing 15 lowest of 33 total)_

## 4. Cross-collection nearest-neighbor anomalies

SKUs whose nearest visual neighbor is in a *different* collection.
Could be intentional (cross-collection callbacks) or a tagging error.

| sku | tagged | nearest sku | nearest collection | score |
|-----|--------|-------------|--------------------|------:|
| `br-005` | black-rose | `kids-002` | **kids-capsule** | 0.851 |
| `kids-002` | kids-capsule | `br-005` | **black-rose** | 0.851 |
| `sg-002` | signature | `br-005` | **black-rose** | 0.814 |
| `sg-007` | signature | `br-005` | **black-rose** | 0.814 |
| `kids-001` | kids-capsule | `lh-002` | **love-hurts** | 0.813 |
| `sg-001` | signature | `br-002` | **black-rose** | 0.765 |

## 5. Top-5 visually similar SKUs (drives the /shortcode widget)

Sample (first 6 SKUs, full set in JSON):

- **`br-001`** → `br-004` (0.87), `br-010` (0.87), `br-006` (0.85)
- **`br-002`** → `br-005` (0.78), `kids-002` (0.77), `sg-007` (0.77)
- **`br-003`** → `br-006` (0.87), `br-009` (0.87), `br-015` (0.84)
- **`br-004`** → `br-001` (0.87), `br-009` (0.86), `br-006` (0.85)
- **`br-005`** → `kids-002` (0.85), `sg-002` (0.81), `sg-007` (0.81)
- **`br-006`** → `br-009` (0.88), `br-003` (0.87), `br-001` (0.85)
