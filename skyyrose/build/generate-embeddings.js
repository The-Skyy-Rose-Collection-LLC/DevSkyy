/**
 * SkyyRose — OpenAI Embeddings Generator
 *
 * Generates text-embedding-3-small embeddings for all 20 SkyyRose products
 * and saves them to assets/data/product-embeddings.json for semantic search.
 *
 * Usage:
 *   node build/generate-embeddings.js           # embed all products
 *   node build/generate-embeddings.js br-001    # embed a single product
 *
 * Requires: OPENAI_API_KEY env var
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// OpenAI client (openai@6.22.0 — CommonJS)
// ---------------------------------------------------------------------------

const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const EMBEDDING_MODEL = 'text-embedding-3-small';

// ---------------------------------------------------------------------------
// File paths
// ---------------------------------------------------------------------------

const ROOT            = path.join(__dirname, '..');
const CATALOG_PATH    = path.join(ROOT, 'assets/data/product-content.json');
const EMBEDDINGS_PATH = path.join(ROOT, 'assets/data/product-embeddings.json');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build the combined text string used to create an embedding for a product.
 * Joins: name + collection + description + short_description + seo_meta
 * @param {Object} product
 * @returns {string}
 */
function buildEmbeddingText(product) {
  const parts = [
    product.name            || '',
    product.collection      || '',
    product.description     || '',
    product.short_description || '',
  ];

  // seo_meta may be an object { title, description, keywords } or a string
  if (product.seo_meta) {
    if (typeof product.seo_meta === 'string') {
      parts.push(product.seo_meta);
    } else {
      if (product.seo_meta.title)       parts.push(product.seo_meta.title);
      if (product.seo_meta.description) parts.push(product.seo_meta.description);
      if (product.seo_meta.keywords)    parts.push(product.seo_meta.keywords);
    }
  }

  return parts
    .map(s => String(s).trim())
    .filter(Boolean)
    .join(' | ');
}

/**
 * Sleep for `ms` milliseconds.
 * @param {number} ms
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Call the OpenAI embeddings API with one retry on rate-limit (429).
 * @param {string} text
 * @returns {Promise<number[]>} 1536-dimensional vector
 */
async function createEmbedding(text) {
  const call = async () => {
    const response = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: text,
    });
    return response.data[0].embedding;
  };

  try {
    return await call();
  } catch (err) {
    // Retry once on rate limit
    const status = err?.status || err?.statusCode || (err?.response?.status);
    if (status === 429) {
      console.warn('  [rate limit] Waiting 5 s before retry...');
      await sleep(5000);
      return await call(); // throws on second failure — caller handles it
    }
    throw err;
  }
}

/**
 * Load the existing embeddings file, or return a fresh shell.
 * @returns {{ model: string, generated: string, products: Array }}
 */
function loadExistingEmbeddings() {
  if (!fs.existsSync(EMBEDDINGS_PATH)) {
    return { model: EMBEDDING_MODEL, generated: null, products: [] };
  }
  try {
    const raw = fs.readFileSync(EMBEDDINGS_PATH, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn('[generate-embeddings] Could not parse existing file:', err.message);
    return { model: EMBEDDING_MODEL, generated: null, products: [] };
  }
}

/**
 * Save the embeddings data to disk as formatted JSON.
 * @param {Object} data
 */
function saveEmbeddings(data) {
  const dir = path.dirname(EMBEDDINGS_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(EMBEDDINGS_PATH, JSON.stringify(data, null, 2), 'utf8');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error('[generate-embeddings] Error: OPENAI_API_KEY environment variable is not set.');
    process.exit(1);
  }

  // Optional single-product filter from CLI arg
  const targetId = process.argv[2] || null;

  // Load product catalog
  if (!fs.existsSync(CATALOG_PATH)) {
    console.error('[generate-embeddings] Error: product catalog not found at', CATALOG_PATH);
    process.exit(1);
  }

  let catalog;
  try {
    catalog = JSON.parse(fs.readFileSync(CATALOG_PATH, 'utf8'));
  } catch (err) {
    console.error('[generate-embeddings] Error parsing catalog:', err.message);
    process.exit(1);
  }

  // Load existing embeddings for resume support
  const existing     = loadExistingEmbeddings();
  const embeddedById = new Map(existing.products.map(p => [p.id, p]));

  // Determine which products to process
  const allIds = Object.keys(catalog);
  const toProcess = allIds.filter(id => {
    if (targetId && id !== targetId) return false;    // filter by CLI arg
    if (embeddedById.has(id)) {
      console.log(`[skip] ${id} already embedded — skipping (use targetId to force)`);
      return false;
    }
    return true;
  });

  if (toProcess.length === 0) {
    console.log('[generate-embeddings] Nothing to do — all products already embedded.');
    return;
  }

  console.log(`[generate-embeddings] Embedding ${toProcess.length} product(s) with model: ${EMBEDDING_MODEL}`);
  console.log('─'.repeat(60));

  let successCount = 0;
  let errorCount   = 0;

  for (let i = 0; i < toProcess.length; i++) {
    const id      = toProcess[i];
    const product = catalog[id];
    const text    = buildEmbeddingText(product);

    console.log(`[${i + 1}/${toProcess.length}] Embedding: ${id} — ${product.name}`);
    console.log(`  text (${text.length} chars): ${text.slice(0, 100)}...`);

    try {
      const embedding = await createEmbedding(text);

      embeddedById.set(id, {
        id,
        name:       product.name       || id,
        collection: product.collection || 'unknown',
        text,
        embedding,
      });

      console.log(`  Done — vector dims: ${embedding.length}`);
      successCount++;
    } catch (err) {
      console.error(`  ERROR embedding ${id}:`, err.message || err);
      errorCount++;
    }

    // Rate-limit guard: 500 ms between calls (skip after last item)
    if (i < toProcess.length - 1) {
      await sleep(500);
    }
  }

  // Reconstruct output preserving original ordering from the catalog
  const orderedProducts = allIds
    .filter(id => embeddedById.has(id))
    .map(id => embeddedById.get(id));

  const output = {
    model:     EMBEDDING_MODEL,
    generated: new Date().toISOString(),
    products:  orderedProducts,
  };

  saveEmbeddings(output);

  console.log('─'.repeat(60));
  console.log(`[generate-embeddings] Done.`);
  console.log(`  Embedded: ${successCount} new product(s)`);
  if (errorCount > 0) console.warn(`  Errors:   ${errorCount} product(s) failed`);
  console.log(`  Total in file: ${orderedProducts.length} product(s)`);
  console.log(`  Saved to: ${EMBEDDINGS_PATH}`);
}

main().catch(err => {
  console.error('[generate-embeddings] Fatal error:', err);
  process.exit(1);
});
