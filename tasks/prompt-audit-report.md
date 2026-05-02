# Prompt Audit Report

- SKUs scored: **11**

## Mean alignment per prompt template

| template | length | mean cosine |
|---------|-------:|------------:|
| `front_full` | 2388 chars | 0.2276 |
| `front_simplified` | 2331 chars | 0.2323 |
| `flux_compact` | 401 chars | 0.2610 |
| `minimal_baseline` | 38 chars | 0.2831 |

**Read:** lower mean cosine = template carries more signal CLIP doesn't ground.
If `minimal_baseline` mean is highest, the production prompts are too brand-heavy.

## ⚠️  Underperforming production prompts (9 SKUs)

Production `front_full` prompt scores at least 0.02 BELOW the minimal baseline.
These prompts are likely hurting render quality — the renderer can't extract
the core garment description through the brand language.

| sku | name | full | minimal | gap |
|-----|------|-----:|--------:|----:|
| `sg-013` | Mint & Lavender Crewneck | 0.206 | 0.311 | +0.105 |
| `sg-006` | Mint & Lavender Hoodie | 0.202 | 0.294 | +0.091 |
| `sg-014` | Mint & Lavender Sweatpants | 0.235 | 0.322 | +0.087 |
| `sg-012` | Original Label Tee (Orchid) | 0.225 | 0.302 | +0.078 |
| `lh-002` | Love Hurts Joggers | 0.228 | 0.293 | +0.066 |
| `lh-003` | Love Hurts Basketball Shorts | 0.212 | 0.265 | +0.053 |
| `sg-011` | Original Label Tee (White) | 0.243 | 0.286 | +0.043 |
| `br-004` | BLACK Rose Hoodie | 0.225 | 0.262 | +0.037 |
| `br-006` | BLACK Rose Sherpa Jacket | 0.237 | 0.259 | +0.022 |

## Per-SKU prompt alignment (sorted by full-prompt score, low first)

| sku | name | full | simpl | flux | minim |
|-----|------|-----:|------:|-----:|------:|
| `sg-006` | Mint & Lavender Hoodie | 0.202 | 0.211 | 0.231 | 0.294 |
| `sg-013` | Mint & Lavender Crewneck | 0.206 | 0.206 | 0.231 | 0.311 |
| `lh-003` | Love Hurts Basketball Shorts | 0.212 | 0.216 | 0.232 | 0.265 |
| `sg-012` | Original Label Tee (Orchid) | 0.225 | 0.225 | 0.265 | 0.302 |
| `br-004` | BLACK Rose Hoodie | 0.225 | 0.227 | 0.257 | 0.262 |
| `lh-002` | Love Hurts Joggers | 0.228 | 0.234 | 0.258 | 0.293 |
| `sg-014` | Mint & Lavender Sweatpants | 0.235 | 0.238 | 0.291 | 0.322 |
| `br-006` | BLACK Rose Sherpa Jacket | 0.237 | 0.249 | 0.279 | 0.259 |
| `lh-005` | The Fannie | 0.240 | 0.244 | 0.279 | 0.259 |
| `sg-011` | Original Label Tee (White) | 0.243 | 0.246 | 0.294 | 0.286 |
| `sg-009` | The Sherpa Jacket | 0.252 | 0.259 | 0.254 | 0.262 |
