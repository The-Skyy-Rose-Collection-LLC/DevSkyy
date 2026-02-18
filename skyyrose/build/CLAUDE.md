# build/ -- Asset Generation and Production Verification

Build-time scripts for embeddings, AI content, image optimization, and production checks. All Node.js unless noted. No test framework needed.

## Key Commands

```bash
npm run verify                      # 82-check production verification (no API keys)
node build/generate-embeddings.js   # regen product vectors (OPENAI_API_KEY)
npm run build                       # optimize scenes + images + logos
npm run build:images                # product image optimization only
npm run build:scenes                # scene optimization only
```

## Scripts Reference

### Verification
| Script | Purpose | Keys needed |
|--------|---------|-------------|
| verify.js | 82 checks: file existence, HTML structure, JS syntax, asset paths, config integrity | none |

### AI Content Generation
| Script | Purpose | Keys needed |
|--------|---------|-------------|
| generate-embeddings.js | OpenAI text-embedding-3-small (1536-dim) -> product-embeddings.json | `OPENAI_API_KEY` |
| gemini-content.js | AI product descriptions from product-content.json | `GEMINI_API_KEY` |
| generate-fashion-models.js | AI fashion model images | `GEMINI_API_KEY` |
| generate-scenes-gemini.js | AI scene background images | `GEMINI_API_KEY` |
| generate-collection-bgs.js | Collection background images | `GEMINI_API_KEY` |
| tool-calling.js | 4-provider tool calling demo (OpenAI/Vercel AI/Gemini/Claude) | any AI key |
| nanobanana-brand-system.js | Full brand content generation system | `GEMINI_API_KEY` |

### Image Optimization (Sharp)
| Script | Purpose |
|--------|---------|
| optimize-images.js | WebP + JPEG fallback, mobile variants |
| optimize-scenes-production.js | Production scene processing |
| optimize-source-photos.js | Source photo processing |
| optimize-logos.js | Logo optimization |
| sharp-exports.js | Shared Sharp utility functions (imported by other scripts) |

### Python Scripts (require Pillow)
| Script | Purpose |
|--------|---------|
| composite-with-bgs.py | PIL image compositing with backgrounds |
| ecommerce-process.py | E-commerce image processing pipeline |
| watch-pipeline.py | File watcher for automatic rebuilds |

### WooCommerce
| Script | Purpose |
|--------|---------|
| generate-woocommerce-csv.js | Bulk product import CSV from product-content.json |

## Data Flow

```
product-content.json (source of truth)
  -> generate-embeddings.js -> product-embeddings.json (vectors)
  -> gemini-content.js -> product descriptions (back into product-content.json)
  -> generate-woocommerce-csv.js -> woocommerce-import.csv

source-products/ (photos)
  -> optimize-source-photos.js -> products/ (optimized)
  -> ecommerce-process.py -> products-ecom/ (e-commerce ready)
  -> composite-with-bgs.py -> final composited images
```

## generate-embeddings.js Details

- Reads `assets/data/product-content.json`, builds text from name+description+collection
- Calls OpenAI text-embedding-3-small for each product (1536-dim vectors)
- Resume support: skips products already in output file
- Rate limit retry: 429 -> 5s wait
- Single-product mode: `node build/generate-embeddings.js br-001`
- Output: `assets/data/product-embeddings.json`

## verify.js Details

- 82 checks across 8 categories: files, HTML, JS, assets, config, SW, CSS, accessibility
- ANSI color output with pass/fail/warn indicators
- Exit code 0 on all pass, 1 on any failure
- No dependencies beyond Node.js built-ins
