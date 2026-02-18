# SkyyRose -- Luxury Fashion Virtual Showroom

Vanilla JS single-page showroom: 3 themed rooms (Garden/Ballroom/Runway), full-screen scenes, interactive product hotspots. Static HTML+JS frontend, Node.js Claude assistant API, build-time asset generators.

## Commands

```bash
npm run dev              # serve on localhost:3000
node api/assistant.js    # Claude SSE assistant on :3001
npm run verify           # 82-check production verification (no keys needed)
npm run build            # optimize scenes + images + logos (Sharp)
node build/generate-embeddings.js   # regen product vectors (OPENAI_API_KEY)
```

## Module Globals (assets/js/) -- load order matters

| File | Global | Singleton | Key Methods |
|------|--------|-----------|-------------|
| config.js | `CONFIG` | -- | `.rooms[]`, `.rooms[].hotspots[{x,y,product}]` |
| semantic-search.js | `SemanticSearch` | `window.search` | `search(q)`, `keywordSearch(q)`, `vectorSearch(emb)`, `findSimilar(id)` |
| wordpress-client.js | `WordPressClient` | -- | `getProducts()`, `addToCart()`, `syncProductsToConfig()` |
| accessibility.js | `AccessibilityManager` | `window.a11y` | `trapFocus(el)`, `releaseFocus()`, `setupModal()` |
| gestures.js | `GestureManager` | `window.gestures` | dispatches `swipe-left`/`swipe-right` CustomEvents |
| wishlist.js | `WishlistManager` | `window.wishlist` | `toggle/add/remove/has(id)`, fires `wishlist-change` event |
| analytics.js | `AnalyticsManager` | `window.analytics` | `roomView()`, `productView()`, `addToCart()` (GA4 dataLayer) |
| sharing.js | `SharingManager` | `window.sharing` | Web Share API + fallback modal |
| avatar-assistant.js | `AvatarAssistant` | `window.avatar` | `pointAt(id)`, `celebrate()`, SSE to /api/assistant |
| app.js | -- | -- | `init()`, `renderRoom(i)`, `openModal()`, `goToRoom(i)` |
| 3d-experience.js | `ImmersiveExperience` | `window.skyyRoseExperience` | for explore-*.html only |

## API (api/assistant.js)

- **POST /api/assistant** -- SSE streaming. Body: `{message, history, collection}`. Stream: `data: {"delta":"..."}\n\n`, end: `data: [DONE]\n\n`
- **GET /api/assistant/health** -- JSON health check
- Model: claude-sonnet-4-5-20250929. Rate limit: 10 req/min/IP. Body max: 64KB. Uses `[PRODUCT:id]` markers for avatar pointAt.
- Server injects top-3 semantic search matches into system prompt per request.

## Collections

| Collection | Room | Accent | IDs | SKU |
|------------|------|--------|-----|-----|
| BLACK ROSE | The Garden | `#B76E79` | br-001..008 | SR-BR- |
| LOVE HURTS | The Ballroom | `#8B0000` | lh-001..006 | SR-LH- |
| SIGNATURE | The Runway | `#D4AF37` | sg-001..006 | SR-SIG- |

## Build Scripts (build/)

| Script | Purpose | Requires |
|--------|---------|----------|
| verify.js | 82-check production verification | nothing |
| generate-embeddings.js | OpenAI text-embedding-3-small vectors | `OPENAI_API_KEY` |
| tool-calling.js | 4-provider tool calling demo | any AI key |
| gemini-content.js | AI product descriptions | `GEMINI_API_KEY` |
| generate-fashion-models.js | AI fashion model images | `GEMINI_API_KEY` |
| generate-scenes-gemini.js | AI scene backgrounds | `GEMINI_API_KEY` |
| optimize-images.js | Sharp WebP+JPEG pipeline | `sharp` |
| composite-with-bgs.py / ecommerce-process.py | Python image compositing | `Pillow` |

## Environment Variables (critical)

| Var | Used by |
|-----|---------|
| `ANTHROPIC_API_KEY` | api/assistant.js, build/tool-calling.js |
| `OPENAI_API_KEY` | build/generate-embeddings.js, build/tool-calling.js |
| `GEMINI_API_KEY` | build/gemini-content.js, scene/model generators |
| `WORDPRESS_URL`, `WC_CONSUMER_KEY`, `WC_CONSUMER_SECRET` | wordpress-client.js |
| `ASSISTANT_PORT` (default 3001), `CORS_ORIGIN` | api/assistant.js |

## Key Patterns

- **Module init:** All JS expose constructor on `window`, auto-instantiate singleton. `app.js init()` re-inits with `typeof` guards.
- **Events:** `swipe-left`/`swipe-right` (gestures->nav), `wishlist-change` (wishlist->UI) via CustomEvent on `document`.
- **Degradation:** WP client -> static CONFIG; search -> keyword; SW ensures offline; analytics works without GTM.
- **SSE protocol:** POST sends `{message,history,collection}`, server streams `data: {"delta":"..."}\n\n`, ends `data: [DONE]\n\n`.
- **SW strategies:** cache-first (images), network-first (WP API), stale-while-revalidate (HTML/CSS/JS). Background sync for cart.
- **Data files:** `assets/data/product-content.json` (catalog), `product-embeddings.json` (vectors), `alt-text.json`.
- **Naming:** Product IDs `br-001`, SKUs `SR-BR-001`, scenes `{collection}.webp`, pages `explore-{collection}.html`.