# api/ -- Claude Assistant SSE Streaming API

Single file: `assistant.js`. Plain Node.js `http.createServer` (no Express). Optionally exports a Hono router.

## Run

```bash
node api/assistant.js              # starts on ASSISTANT_PORT (default 3001)
ANTHROPIC_API_KEY=sk-... node api/assistant.js  # explicit key
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/assistant | SSE streaming chat with Claude |
| GET | /api/assistant/health | JSON health check (model, catalog size) |
| OPTIONS | * | CORS preflight |

## SSE Protocol

Request body: `{ message: string, history: Array, collection?: string, product?: object }`

Response: `Content-Type: text/event-stream`
- Each chunk: `data: {"delta": "partial text"}\n\n`
- Terminal: `data: [DONE]\n\n`
- Product references: `[PRODUCT:br-001]` markers in response text (avatar client parses for pointAt)

## Architecture

```
POST /api/assistant
  -> parse body (64KB max)
  -> rate limit check (10 req/min/IP, in-memory)
  -> getSemanticContext(message) -- top-3 product matches from embeddings
  -> buildSystemPrompt(collection, product, semanticContext)
  -> anthropic.messages.stream() with claude-sonnet-4-5-20250929
  -> pipe SSE deltas to response
```

## Key Functions

| Function | Purpose |
|----------|---------|
| `assistantHandler(req, res)` | Main request handler (export for custom servers) |
| `getSemanticContext(query)` | Semantic search -> markdown snippet of matching products |
| `buildSystemPrompt(collection, product, semantic)` | Dynamic system prompt with catalog + context |
| `loadCatalog()` | Lazy-load product-content.json (falls back to 20-product embedded catalog) |

## Dependencies

- `@anthropic-ai/sdk` -- Claude API (required)
- `../assets/js/semantic-search` -- UMD module, reused server-side (optional, graceful if missing)
- `../assets/data/product-content.json` -- Product catalog (optional, has fallback)

## Env Vars

| Var | Required | Default |
|-----|----------|---------|
| `ANTHROPIC_API_KEY` | yes | -- |
| `ASSISTANT_PORT` | no | 3001 |
| `CORS_ORIGIN` | no | http://localhost:3000 |

## Exports

```javascript
const { assistantHandler } = require('./api/assistant');  // for http.createServer
const { router } = require('./api/assistant');             // for Hono app.route()
```
