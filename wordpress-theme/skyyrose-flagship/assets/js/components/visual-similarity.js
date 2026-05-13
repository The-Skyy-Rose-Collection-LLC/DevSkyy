/**
 * Visual Similarity Search — find SKUs that look like a given SKU.
 *
 * Two payload modes (in priority order):
 *
 *   (A) PRECOMPUTED — data/product-similarities.json (~10KB)
 *       Pre-ranked top-N neighbors per SKU. No math in the browser.
 *       Built by scripts/build_product_similarities.py.
 *
 *   (B) FALLBACK — data/product-embeddings.json (~160KB)
 *       Raw CLIP embeddings. Browser computes cosine in JS.
 *       Used when (A) is missing or stale.
 *
 * The shortcode pre-renders every published SKU as a hidden card. This
 * module's only job is to decide which N cards to reveal and in what
 * order.
 *
 * Why server pre-render: graceful degradation. If JS fails or hasn't
 * loaded yet, the markup is still in the DOM and the layout doesn't
 * collapse. Crawlers also see content.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

const SELECTOR_ROOT = '[data-skyyrose-similar]';
const SELECTOR_CARD = '[data-similar-sku]';

let dataPromise = null;

/**
 * Fetch the similarity payload. Tries the precomputed file first, falls
 * back to raw embeddings if it 404s.
 *
 * Resolves to one of:
 *   { mode: 'precomputed', products: { [sku]: { global: [...], same_collection: [...] } } }
 *   { mode: 'embeddings',  products: { [sku]: { embedding: number[], ... } } }
 *
 * @param {string} url - absolute URL the shortcode passed (embeddings JSON).
 *                       The precomputed URL is derived by replacing the filename.
 * @returns {Promise<object>}
 */
function loadData(url) {
  if (dataPromise) return dataPromise;

  // Derive precomputed URL by swapping the filename, preserving query string
  // (cache-bust). embeddings url like .../data/product-embeddings.json?v=1.1.0
  // becomes                              .../data/product-similarities.json?v=1.1.0
  const precomputedUrl = url.replace('product-embeddings.json', 'product-similarities.json');

  const tryPrecomputed = fetch(precomputedUrl, { credentials: 'same-origin' })
    .then((res) => (res.ok ? res.json() : null))
    .then((json) => {
      if (json && json.products) return { mode: 'precomputed', products: json.products };
      return null;
    })
    .catch(() => null);

  dataPromise = tryPrecomputed.then((pre) => {
    if (pre) return pre;
    // Fallback: raw embeddings.
    return fetch(url, { credentials: 'same-origin' })
      .then((res) => {
        if (!res.ok) throw new Error(`embeddings HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => ({ mode: 'embeddings', products: json.products }));
  }).catch((err) => {
    dataPromise = null;
    throw err;
  });

  return dataPromise;
}

/**
 * Dot product of two equal-length numeric arrays. Both must already be
 * L2-normalized for this to equal cosine similarity.
 */
function dot(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

/**
 * Rank all other SKUs by similarity to source. Handles both payload modes.
 *
 * @param {string} sourceSku
 * @param {object} payload - { mode, products }
 * @param {object} [options]
 * @param {boolean} [options.sameCollection] - true => only same-collection matches
 * @returns {Array<{sku: string, score: number}>}
 */
function rankBySimilarity(sourceSku, payload, options = {}) {
  const products = payload.products;
  const source = products[sourceSku];
  if (!source) return [];

  // Precomputed mode: just read the pre-ranked array.
  if (payload.mode === 'precomputed') {
    return options.sameCollection ? source.same_collection || [] : source.global || [];
  }

  // Embeddings mode: compute cosines on the fly (legacy path).
  const myCollection = source.collection;
  const ranked = [];
  for (const sku of Object.keys(products)) {
    if (sku === sourceSku) continue;
    if (options.sameCollection && products[sku].collection !== myCollection) continue;
    ranked.push({ sku, score: dot(source.embedding, products[sku].embedding) });
  }
  ranked.sort((a, b) => b.score - a.score);
  return ranked;
}

/**
 * Reveal the cards for the top-N SKUs in the order ranked, hide the rest.
 *
 * @param {HTMLElement} root
 * @param {Array<{sku: string, score: number}>} ranked
 * @param {number} count
 */
function applyRanking(root, ranked, count) {
  const cards = root.querySelectorAll(SELECTOR_CARD);
  const cardBySku = new Map();
  cards.forEach((el) => cardBySku.set(el.dataset.similarSku, el));

  const winners = ranked.slice(0, count);
  const winnerSkus = new Set(winners.map((r) => r.sku));

  // Hide non-winners.
  cards.forEach((card) => {
    if (!winnerSkus.has(card.dataset.similarSku)) {
      card.hidden = true;
      card.removeAttribute('data-similar-rank');
    }
  });

  // Reorder winners in DOM and reveal them, top match first.
  winners.forEach((entry, index) => {
    const card = cardBySku.get(entry.sku);
    if (!card) return;
    card.hidden = false;
    card.dataset.similarRank = String(index + 1);
    card.dataset.similarScore = entry.score.toFixed(3);
    root.appendChild(card); // re-attach in winner order
  });

  root.dataset.similarLoaded = '1';
}

/**
 * Initialize one similarity widget.
 *
 * @param {HTMLElement} root
 */
async function initWidget(root) {
  const sourceSku = root.dataset.similarSource;
  const url = root.dataset.similarSrc;
  const count = Math.max(1, parseInt(root.dataset.similarCount || '3', 10));
  const sameCollectionOnly = root.dataset.similarSameCollection === '1';

  if (!sourceSku || !url) {
    console.warn('[skyyrose] similarity widget missing data-similar-source or data-similar-src');
    return;
  }

  try {
    const payload = await loadData(url);
    if (!payload.products || !payload.products[sourceSku]) {
      console.warn(`[skyyrose] no similarity data for ${sourceSku}; using server-rendered defaults`);
      return;
    }
    const ranked = rankBySimilarity(sourceSku, payload, { sameCollection: sameCollectionOnly });
    applyRanking(root, ranked, count);
  } catch (err) {
    console.error('[skyyrose] visual similarity init failed', err);
    // Leave server-rendered fallback in place.
  }
}

function init() {
  document.querySelectorAll(SELECTOR_ROOT).forEach((root) => {
    if (root.dataset.initialized === '1') return;
    root.dataset.initialized = '1';
    initWidget(root);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

export { rankBySimilarity, dot };
