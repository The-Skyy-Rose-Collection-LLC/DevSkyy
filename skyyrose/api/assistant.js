/**
 * SkyyRose Avatar Assistant — Server-Side API Handler
 *
 * Plain Node.js http-compatible handler (no Express dependency).
 * Also exports a minimal Hono router if hono is available.
 *
 * POST /api/assistant        — chat with Claude (SSE streaming)
 * GET  /api/assistant/health — health check
 *
 * Usage with Node.js http.createServer:
 *   const { assistantHandler } = require('./api/assistant');
 *   http.createServer((req, res) => assistantHandler(req, res)).listen(3001);
 *
 * Usage with Hono:
 *   const { router } = require('./api/assistant');
 *   app.route('/api', router);
 */

'use strict';

const http = require('http');
const fs   = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Anthropic SDK
// ---------------------------------------------------------------------------

const Anthropic = require('@anthropic-ai/sdk');

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const MODEL = 'claude-sonnet-4-6';

// ---------------------------------------------------------------------------
// Semantic search (pre-computed embeddings)
// ---------------------------------------------------------------------------

let SemanticSearch = null;
let semanticSearchInstance = null;

try {
  SemanticSearch = require('../assets/js/semantic-search');
  semanticSearchInstance = new SemanticSearch();
  semanticSearchInstance.init().then(() => {
    console.log('[assistant] SemanticSearch initialised with', semanticSearchInstance.products.length, 'products');
  }).catch(err => {
    console.warn('[assistant] SemanticSearch init error:', err.message);
  });
} catch (err) {
  if (err.code !== 'MODULE_NOT_FOUND') {
    console.warn('[assistant] SemanticSearch load warning:', err.message);
  }
}

/**
 * Run a semantic search against stored embeddings and return a compact
 * markdown snippet listing the top matching products.
 * Falls back to keyword search when full vector embeddings are unavailable.
 *
 * @param {string} query
 * @returns {Promise<string>}  e.g. "Relevant products:
- [br-001] BLACK Rose Crewneck (score: 0.87)
..."
 */
async function getSemanticContext(query) {
  if (!semanticSearchInstance || !query) return '';
  try {
    const results = await semanticSearchInstance.search(query, {
      maxResults: 3,
      minScore:   0.2,
    });
    if (!results.length) return '';
    const lines = results.map(r =>
      `- [${r.id}] ${r.name} (collection: ${r.collection}, score: ${r.score.toFixed(2)})`
    );
    return 'Relevant products for this query:\n' + lines.join('\n');
  } catch (err) {
    console.warn('[assistant] getSemanticContext error:', err.message);
    return '';
  }
}


// ---------------------------------------------------------------------------
// Product catalog (loaded once at startup)
// ---------------------------------------------------------------------------

const CATALOG_PATH = path.join(__dirname, '../assets/data/product-content.json');

let PRODUCT_CATALOG = null;

function loadCatalog() {
  if (PRODUCT_CATALOG) return PRODUCT_CATALOG;
  try {
    const raw = fs.readFileSync(CATALOG_PATH, 'utf8');
    PRODUCT_CATALOG = JSON.parse(raw);
    console.log('[assistant] Loaded product catalog:', Object.keys(PRODUCT_CATALOG).length, 'products');
  } catch (err) {
    console.warn('[assistant] Could not load product catalog:', err.message);
    PRODUCT_CATALOG = FALLBACK_CATALOG;
  }
  return PRODUCT_CATALOG;
}

// Fallback embedded catalog (core 20 products) if file is unavailable
const FALLBACK_CATALOG = {
  'br-001': { name: 'BLACK Rose Crewneck',              collection: 'black-rose', price: null },
  'br-002': { name: 'BLACK Rose Joggers',               collection: 'black-rose', price: null },
  'br-003': { name: 'BLACK is Beautiful Jersey',        collection: 'black-rose', price: null },
  'br-004': { name: 'BLACK Rose Hoodie',                collection: 'black-rose', price: null },
  'br-005': { name: 'BLACK Rose Hoodie — Signature Ed', collection: 'black-rose', price: null },
  'br-006': { name: 'BLACK Rose Sherpa Jacket',         collection: 'black-rose', price: null },
  'br-007': { name: 'BLACK Rose × Love Hurts Shorts',   collection: 'black-rose', price: null },
  'br-008': { name: "Women's BLACK Rose Hooded Dress",  collection: 'black-rose', price: null },
  'lh-001': { name: 'The Fannie',                       collection: 'love-hurts', price: null },
  'lh-002': { name: 'Love Hurts Joggers',               collection: 'love-hurts', price: null },
  'lh-003': { name: 'Love Hurts Basketball Shorts',     collection: 'love-hurts', price: null },
  'lh-004': { name: 'Love Hurts Hoodie',                collection: 'love-hurts', price: null },
  'lh-005': { name: 'Love Hurts Crewneck',              collection: 'love-hurts', price: null },
  'lh-006': { name: 'Love Hurts T-Shirt',               collection: 'love-hurts', price: null },
  'sg-001': { name: 'Signature Rose Hoodie',            collection: 'signature',  price: null },
  'sg-002': { name: 'Signature Rose Crewneck',          collection: 'signature',  price: null },
  'sg-003': { name: 'Signature Joggers',                collection: 'signature',  price: null },
  'sg-004': { name: 'Signature Tee',                    collection: 'signature',  price: null },
  'sg-005': { name: 'Signature Cap',                    collection: 'signature',  price: null },
  'sg-006': { name: 'Signature Zip-Up',                 collection: 'signature',  price: null },
};

// ---------------------------------------------------------------------------
// Build system prompt
// ---------------------------------------------------------------------------

function buildSystemPrompt(collection, productContext, semanticContext) {
  const catalog = loadCatalog();

  // Build a compact product list for the prompt
  const productLines = Object.entries(catalog).map(([id, p]) => {
    const price = p.price ? ` — $${p.price}` : '';
    const desc  = p.short_description
      ? ` | ${p.short_description.slice(0, 100)}`
      : '';
    return `  [${id}] ${p.name} (${p.collection}${price})${desc}`;
  }).join('\n');

  const collectionContext = collection
    ? `\nThe customer is currently browsing the "${collection}" collection.`
    : '';

  const productContextStr = productContext
    ? `\nFocused product: ${productContext.name || ''} (ID: ${productContext.id || ''}). ${productContext.description || ''}`
    : '';

  return `You are a sophisticated, warm, and knowledgeable fashion assistant for SkyyRose — a luxury streetwear brand rooted in Bay Area culture, dark romance, and Gothic beauty.

Your personality:
- Elegant, poetic, and encouraging — you speak with the brand's signature voice
- You celebrate self-expression and empowerment through fashion
- You are deeply knowledgeable about every SkyyRose product, its story, and its styling possibilities
- You use occasional light flourishes ("✦", "🌹") but never overdo it
- You are concise — 2–4 sentences max per response unless the customer asks for more detail

Your capabilities:
- Recommend products by referencing them as [PRODUCT:product-id] when you mention them — the showroom will highlight them automatically
- Suggest complementary pieces and complete looks
- Explain the story and craftsmanship behind each piece
- Help with sizing guidance (S–3XL for most pieces)
- Handle pre-order questions (most pieces are limited pre-order)
- Reflect the tone of the current collection (Black Rose = dark and gothic; Love Hurts = raw street emotion; Signature = refined luxury)
${collectionContext}
${productContextStr}

SkyyRose Product Catalog:
${productLines}

Rules:
- Only recommend products from the catalog above using [PRODUCT:id] format
- Never fabricate prices unless you know them from the catalog
- Keep responses elegant and on-brand
- If you don't know something, say so gracefully and offer to help with what you know
- NEVER break character or discuss anything outside of fashion and the SkyyRose brand${semanticContext ? '\n\n' + semanticContext : ''}`;
}

// ---------------------------------------------------------------------------
// Rate limiting (simple in-memory, per IP, 10 req/min)
// ---------------------------------------------------------------------------

const RATE_LIMIT_MAX      = 10;
const RATE_LIMIT_WINDOW   = 60 * 1000; // 1 minute in ms
const rateLimitStore      = new Map();  // ip -> [timestamps]

/**
 * Returns true if the request from this IP should be blocked.
 * @param {string} ip
 * @returns {boolean}
 */
function isRateLimited(ip) {
  const now    = Date.now();
  const window = now - RATE_LIMIT_WINDOW;

  if (!rateLimitStore.has(ip)) {
    rateLimitStore.set(ip, [now]);
    return false;
  }

  // Prune old timestamps
  const timestamps = rateLimitStore.get(ip).filter(ts => ts > window);
  timestamps.push(now);
  rateLimitStore.set(ip, timestamps);

  return timestamps.length > RATE_LIMIT_MAX;
}

// Periodic cleanup to prevent memory leak
setInterval(() => {
  const cutoff = Date.now() - RATE_LIMIT_WINDOW;
  for (const [ip, timestamps] of rateLimitStore.entries()) {
    const pruned = timestamps.filter(ts => ts > cutoff);
    if (pruned.length === 0) {
      rateLimitStore.delete(ip);
    } else {
      rateLimitStore.set(ip, pruned);
    }
  }
}, 5 * 60 * 1000).unref(); // every 5 minutes, non-blocking

// ---------------------------------------------------------------------------
// CORS headers
// ---------------------------------------------------------------------------

const CORS_HEADERS = {
  'Access-Control-Allow-Origin':  process.env.CORS_ORIGIN || '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age':       '86400',
};

function setCORSHeaders(res) {
  Object.entries(CORS_HEADERS).forEach(([k, v]) => res.setHeader(k, v));
}

// ---------------------------------------------------------------------------
// Body parsing helper
// ---------------------------------------------------------------------------

/**
 * Parse the request body as JSON.
 * @param {http.IncomingMessage} req
 * @returns {Promise<Object>}
 */
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
      if (body.length > 1024 * 64) { // 64KB max
        reject(new Error('Request body too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

// ---------------------------------------------------------------------------
// GET /api/assistant/health
// ---------------------------------------------------------------------------

function handleHealth(req, res) {
  setCORSHeaders(res);
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    ok:        true,
    model:     MODEL,
    timestamp: new Date().toISOString(),
    catalog:   Object.keys(loadCatalog()).length,
  }));
}

// ---------------------------------------------------------------------------
// POST /api/assistant  — SSE streaming chat
// ---------------------------------------------------------------------------

async function handleChat(req, res) {
  setCORSHeaders(res);

  // IP extraction (works behind proxies)
  const ip = (
    req.headers['x-forwarded-for'] ||
    req.headers['x-real-ip'] ||
    req.socket.remoteAddress ||
    '0.0.0.0'
  ).split(',')[0].trim();

  // Rate limit check
  if (isRateLimited(ip)) {
    res.writeHead(429, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      error: 'Too many requests. Please wait a moment before asking again.',
    }));
    return;
  }

  // Parse request body
  let body;
  try {
    body = await parseBody(req);
  } catch (err) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: err.message }));
    return;
  }

  const {
    message,
    history        = [],
    collection     = null,
    productContext = null,
  } = body;

  // Validate
  if (!message || typeof message !== 'string' || !message.trim()) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'message is required' }));
    return;
  }

  // Build messages array (cap history at 40 to control token usage)
  // Semantic enrichment: find closely related products before building the prompt
  const semanticContext = await getSemanticContext(message);

  const systemPrompt = buildSystemPrompt(collection, productContext, semanticContext);

  const messages = [
    ...history.slice(-40).map(h => ({
      role:    h.role === 'assistant' ? 'assistant' : 'user',
      content: String(h.content || '').slice(0, 2000), // clamp individual messages
    })),
    { role: 'user', content: message.trim().slice(0, 2000) },
  ];

  // Set up SSE response
  res.writeHead(200, {
    'Content-Type':      'text/event-stream',
    'Cache-Control':     'no-cache',
    'Connection':        'keep-alive',
    'X-Accel-Buffering': 'no', // disable nginx buffering
  });

  // Helper: send SSE event
  const sendEvent = (data) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  const sendDone = () => {
    res.write('data: [DONE]\n\n');
    res.end();
  };

  // Stream from Anthropic
  try {
    const stream = await anthropic.messages.stream({
      model:      MODEL,
      max_tokens: 1024,
      system:     systemPrompt,
      messages,
    });

    for await (const event of stream) {
      // Handle connection close mid-stream
      if (res.destroyed) break;

      if (event.type === 'content_block_delta') {
        const delta = event.delta;
        if (delta && delta.type === 'text_delta' && delta.text) {
          sendEvent({ delta: delta.text });
        }
      }
    }

    sendDone();

  } catch (err) {
    console.error('[assistant] Anthropic API error:', err.message || err);

    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Assistant temporarily unavailable.' }));
    } else {
      // Headers already sent — send error as SSE event before closing
      sendEvent({ error: 'Assistant temporarily unavailable.' });
      sendDone();
    }
  }
}

// ---------------------------------------------------------------------------
// Main handler (Node.js http-compatible)
// ---------------------------------------------------------------------------

/**
 * Primary export — works as a Node.js http.createServer callback.
 *
 * Route dispatch:
 *   OPTIONS *                    → CORS preflight
 *   GET  /api/assistant/health   → health check JSON
 *   POST /api/assistant          → streaming chat (SSE)
 *
 * @param {http.IncomingMessage} req
 * @param {http.ServerResponse}  res
 */
async function assistantHandler(req, res) {
  const url    = req.url  ? req.url.split('?')[0] : '/';
  const method = req.method ? req.method.toUpperCase() : 'GET';

  // CORS preflight
  if (method === 'OPTIONS') {
    setCORSHeaders(res);
    res.writeHead(204);
    res.end();
    return;
  }

  // Route dispatch
  if (method === 'GET' && (url === '/api/assistant/health' || url === '/health')) {
    handleHealth(req, res);
    return;
  }

  if (method === 'POST' && (url === '/api/assistant' || url === '/')) {
    await handleChat(req, res);
    return;
  }

  // 404
  setCORSHeaders(res);
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
}

// ---------------------------------------------------------------------------
// Hono router (if hono is available in the project)
// ---------------------------------------------------------------------------

let router = null;

try {
  const { Hono } = require('hono');

  router = new Hono();

  // CORS middleware
  router.use('*', async (c, next) => {
    await next();
    Object.entries(CORS_HEADERS).forEach(([k, v]) => c.header(k, v));
  });

  // Health
  router.get('/assistant/health', (c) => {
    return c.json({
      ok:        true,
      model:     MODEL,
      timestamp: new Date().toISOString(),
      catalog:   Object.keys(loadCatalog()).length,
    });
  });

  // Chat — Hono handler wraps the SSE logic using Node response object
  router.post('/assistant', async (c) => {
    const ip = (
      c.req.header('x-forwarded-for') ||
      c.req.header('x-real-ip') ||
      '0.0.0.0'
    ).split(',')[0].trim();

    if (isRateLimited(ip)) {
      return c.json(
        { error: 'Too many requests. Please wait a moment.' },
        429
      );
    }

    let body;
    try {
      body = await c.req.json();
    } catch {
      return c.json({ error: 'Invalid JSON' }, 400);
    }

    const {
      message,
      history        = [],
      collection     = null,
      productContext = null,
    } = body;

    if (!message || typeof message !== 'string' || !message.trim()) {
      return c.json({ error: 'message is required' }, 400);
    }

    // Semantic enrichment for Hono path
    const semanticContextHono = await getSemanticContext(message);

    const systemPrompt = buildSystemPrompt(collection, productContext, semanticContextHono);

    const messages = [
      ...history.slice(-40).map(h => ({
        role:    h.role === 'assistant' ? 'assistant' : 'user',
        content: String(h.content || '').slice(0, 2000),
      })),
      { role: 'user', content: message.trim().slice(0, 2000) },
    ];

    // Use Hono's streaming response
    return c.streamText(async (stream) => {
      try {
        const anthropicStream = await anthropic.messages.stream({
          model:      MODEL,
          max_tokens: 1024,
          system:     systemPrompt,
          messages,
        });

        for await (const event of anthropicStream) {
          if (event.type === 'content_block_delta') {
            const delta = event.delta;
            if (delta && delta.type === 'text_delta' && delta.text) {
              await stream.write(`data: ${JSON.stringify({ delta: delta.text })}\n\n`);
            }
          }
        }

        await stream.write('data: [DONE]\n\n');
      } catch (err) {
        console.error('[assistant/hono] Anthropic error:', err.message);
        await stream.write(`data: ${JSON.stringify({ error: 'Assistant unavailable.' })}\n\n`);
        await stream.write('data: [DONE]\n\n');
      }
    }, 'text/event-stream');
  });

  console.log('[assistant] Hono router initialised.');

} catch (err) {
  // Hono not available or failed — router stays null, use assistantHandler directly
  if (err.code !== 'MODULE_NOT_FOUND') {
    console.warn('[assistant] Hono router init warning:', err.message);
  }
}

// ---------------------------------------------------------------------------
// Standalone server entrypoint (node api/assistant.js)
// ---------------------------------------------------------------------------

if (require.main === module) {
  const PORT = process.env.ASSISTANT_PORT || process.env.PORT || 3001;
  const server = http.createServer(assistantHandler);

  server.listen(PORT, () => {
    console.log(`[assistant] SkyyRose assistant API running on port ${PORT}`);
    console.log(`[assistant] Health: http://localhost:${PORT}/api/assistant/health`);
    loadCatalog(); // pre-warm
  });

  // Graceful shutdown
  process.on('SIGTERM', () => server.close(() => process.exit(0)));
  process.on('SIGINT',  () => server.close(() => process.exit(0)));
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  assistantHandler,
  router,              // Hono router (or null if hono unavailable)
  loadCatalog,
  buildSystemPrompt,
  getSemanticContext,
  isRateLimited,
  MODEL,
};
