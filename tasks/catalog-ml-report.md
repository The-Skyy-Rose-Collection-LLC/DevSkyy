# Catalog ML Audit Report

- SKUs analysed: **33**
- Collections: black-rose, kids-capsule, love-hurts, signature
- Embedding model: `openai/clip-vit-base-patch32` (512-d)

## 1. Visual clustering vs collections (k=4)

- **Silhouette score:** 0.1410 (higher = clusters more separable; >0.5 is strong)
- **Disagreements:** 11 SKUs land in a cluster whose dominant collection is NOT the SKU's collection.

| sku | name | tagged | ML guess |
|-----|------|--------|----------|
| `br-001` | BLACK Rose Crewneck | black-rose | **signature** |
| `br-002` | BLACK Rose Joggers | black-rose | **signature** |
| `br-004` | BLACK Rose Hoodie | black-rose | **signature** |
| `br-005` | BLACK Rose Hoodie — Signature Edition | black-rose | **signature** |
| `br-006` | BLACK Rose Sherpa Jacket | black-rose | **signature** |
| `kids-001` | Kids Colorblock Hoodie Set — Red/Black | kids-capsule | **signature** |
| `kids-002` | Kids Colorblock Hoodie Set — Purple/Black | kids-capsule | **signature** |
| `lh-002` | Love Hurts Joggers | love-hurts | **signature** |
| `lh-003` | Love Hurts Basketball Shorts | love-hurts | **signature** |
| `lh-004` | Love Hurts Bomber Jacket | love-hurts | **signature** |
| `lh-005` | The Fannie | love-hurts | **signature** |

## 2. Per-collection visual outliers

Lowest cosine to its collection centroid = most visually unlike its peers.

| collection | size | outlier sku | name | cosine | best |
|-----------|-----:|-------------|------|-------:|-----:|
| signature | 12 | `sg-015` | The Windbreaker Set | 0.759 | 0.916 |
| black-rose | 15 | `br-010` | BLACK is Beautiful Jersey Series: 3. The Bay (Basketball) | 0.768 | 0.910 |
| love-hurts | 4 | `lh-005` | The Fannie | 0.855 | 0.927 |
| kids-capsule | 2 | `kids-001` | Kids Colorblock Hoodie Set — Red/Black | 0.967 | 0.967 |

## 3. Name vs image alignment (lowest = potential mis-attached image)

CLIP cosine between the product NAME (text) and its IMAGE (vision).
Low score = name and image are about different things.

| sku | collection | name | cosine |
|-----|-----------|------|-------:|
| `lh-005` | love-hurts | The Fannie | 0.264 |
| `lh-003` | love-hurts | Love Hurts Basketball Shorts | 0.264 |
| `sg-009` | signature | The Sherpa Jacket | 0.266 |
| `sg-002` | signature | The Bridge Series 'Stay Golden' Shirt | 0.268 |
| `br-011` | black-rose | BLACK is Beautiful Jersey Series: 4. The Rose (Hockey) | 0.269 |
| `lh-002` | love-hurts | Love Hurts Joggers | 0.274 |
| `lh-004` | love-hurts | Love Hurts Bomber Jacket | 0.282 |
| `sg-005` | signature | The Bridge Series 'The Bay Bridge' Shirt | 0.285 |
| `br-007` | black-rose | BLACK Rose x Love Hurts Basketball Shorts | 0.288 |
| `sg-003` | signature | The Bridge Series 'Stay Golden' Shorts | 0.289 |
| `kids-001` | kids-capsule | Kids Colorblock Hoodie Set — Red/Black | 0.289 |
| `br-006` | black-rose | BLACK Rose Sherpa Jacket | 0.290 |
| `sg-015` | signature | The Windbreaker Set | 0.292 |
| `br-005` | black-rose | BLACK Rose Hoodie — Signature Edition | 0.295 |
| `br-010` | black-rose | BLACK is Beautiful Jersey Series: 3. The Bay (Basketball) | 0.301 |

_(showing 15 lowest of 33 total)_

## 4. Cross-collection nearest-neighbor anomalies

SKUs whose nearest visual neighbor is in a *different* collection.
Could be intentional (cross-collection callbacks) or a tagging error.

| sku | tagged | nearest sku | nearest collection | score |
|-----|--------|-------------|--------------------|------:|
| `br-002` | black-rose | `lh-002` | **love-hurts** | 0.902 |
| `lh-002` | love-hurts | `br-002` | **black-rose** | 0.902 |
| `br-004` | black-rose | `sg-006` | **signature** | 0.898 |
| `sg-006` | signature | `br-004` | **black-rose** | 0.898 |
| `sg-007` | signature | `br-004` | **black-rose** | 0.819 |
| `lh-004` | love-hurts | `br-004` | **black-rose** | 0.817 |
| `sg-009` | signature | `br-005` | **black-rose** | 0.816 |
| `lh-005` | love-hurts | `br-002` | **black-rose** | 0.722 |
| `br-007` | black-rose | `lh-003` | **love-hurts** | 0.720 |
| `sg-015` | signature | `kids-002` | **kids-capsule** | 0.699 |

## 5. Top-5 visually similar SKUs (drives the /shortcode widget)

Sample (first 6 SKUs, full set in JSON):

- **`br-001`** → `br-004` (0.84), `br-006` (0.83), `br-005` (0.83)
- **`br-002`** → `lh-002` (0.90), `br-006` (0.85), `kids-001` (0.83)
- **`br-003`** → `br-003-giants` (1.00), `br-003-oakland` (1.00), `br-003-white` (1.00)
- **`br-003-giants`** → `br-003` (1.00), `br-003-oakland` (1.00), `br-003-white` (1.00)
- **`br-003-oakland`** → `br-003` (1.00), `br-003-giants` (1.00), `br-003-white` (1.00)
- **`br-003-white`** → `br-003` (1.00), `br-003-giants` (1.00), `br-003-oakland` (1.00)
