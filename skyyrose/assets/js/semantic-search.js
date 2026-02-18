/**
 * SkyyRose — Semantic Search Engine
 *
 * Provides keyword-based search (client-side) and full vector cosine-similarity
 * search (server-side) against precomputed OpenAI embeddings.
 *
 * Browser usage (auto-init):
 *   <script src="/assets/js/semantic-search.js"></script>
 *   const results = await window.search.search('cozy hoodie black');
 *
 * Node.js / server-side usage:
 *   const { SemanticSearch } = require('./assets/js/semantic-search');
 *   const search = new SemanticSearch();
 *   await search.init();
 *   const results = await search.vectorSearch(queryEmbedding, { maxResults: 3 });
 */

(function (root, factory) {
  'use strict';
  if (typeof module !== 'undefined' && module.exports) {
    // CommonJS (Node.js)
    module.exports = factory(require);
  } else {
    // Browser — expose as global
    root.SemanticSearch = factory(null);
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (nodeRequire) {
  'use strict';

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  const EMBEDDINGS_URL  = '/assets/data/product-embeddings.json';
  const EMBEDDINGS_PATH = (function () {
    if (typeof __dirname !== 'undefined') {
      const path = nodeRequire('path');
      return path.join(__dirname, '../../assets/data/product-embeddings.json');
    }
    return null;
  }());

  // ---------------------------------------------------------------------------
  // SemanticSearch class
  // ---------------------------------------------------------------------------

  class SemanticSearch {
    constructor() {
      /** @type {Array<{id:string, name:string, collection:string, text:string, embedding:number[]}>} */
      this.products = [];
      /** @type {string|null} */
      this.model = null;
      /** @type {boolean} */
      this.ready = false;
    }

    // -------------------------------------------------------------------------
    // init — load and parse the embeddings file
    // -------------------------------------------------------------------------

    /**
     * Load the precomputed embeddings. Must be called before searching.
     * @returns {Promise<void>}
     */
    async init() {
      try {
        let data;

        if (typeof window === 'undefined' && nodeRequire) {
          // --- Node.js path ---
          const fs   = nodeRequire('fs');
          const path = nodeRequire('path');
          const filePath = EMBEDDINGS_PATH || path.join(process.cwd(), 'assets/data/product-embeddings.json');

          if (!fs.existsSync(filePath)) {
            console.warn('[SemanticSearch] Embeddings file not found at', filePath, '— search degraded to keyword-only');
            this.ready = true;
            return;
          }

          const raw = fs.readFileSync(filePath, 'utf8');
          data = JSON.parse(raw);
        } else {
          // --- Browser path ---
          const response = await fetch(EMBEDDINGS_URL);
          if (!response.ok) {
            console.warn('[SemanticSearch] Could not load embeddings (' + response.status + ') — keyword search only');
            this.ready = true;
            return;
          }
          data = await response.json();
        }

        this.model    = data.model    || null;
        this.products = Array.isArray(data.products) ? data.products : [];
        this.ready    = true;

        console.log('[SemanticSearch] Loaded', this.products.length, 'product embeddings (model:', this.model + ')');
      } catch (err) {
        console.error('[SemanticSearch] init error:', err.message || err);
        this.ready = true; // degrade gracefully
      }
    }

    // -------------------------------------------------------------------------
    // _cosineSimilarity — core vector math
    // -------------------------------------------------------------------------

    /**
     * Compute cosine similarity between two equal-length numeric vectors.
     * Returns a value in [-1, 1] where 1 = identical direction.
     *
     * @param {number[]} a
     * @param {number[]} b
     * @returns {number}
     */
    _cosineSimilarity(a, b) {
      if (!a || !b || a.length !== b.length) return 0;

      let dot = 0;
      let magA = 0;
      let magB = 0;

      for (let i = 0; i < a.length; i++) {
        dot  += a[i] * b[i];
        magA += a[i] * a[i];
        magB += b[i] * b[i];
      }

      const denom = Math.sqrt(magA) * Math.sqrt(magB);
      return denom === 0 ? 0 : dot / denom;
    }

    // -------------------------------------------------------------------------
    // keywordSearch — tf-idf-like fallback for client-side use
    // -------------------------------------------------------------------------

    /**
     * Score products by token matching against their stored text.
     * Scoring rules:
     *   - Exact phrase match in text: +3 pts
     *   - Each query token found in text: +1 pt
     *   - Collection name matches a query token: +2 pts
     *
     * @param {string} query
     * @param {{ maxResults?: number, collection?: string|null, minScore?: number }} options
     * @returns {Array<{id, name, collection, score, text}>}
     */
    keywordSearch(query, options = {}) {
      const { maxResults = 5, collection = null, minScore = 0 } = options;

      if (!query || !query.trim()) return [];

      const queryLower  = query.toLowerCase().trim();
      const queryTokens = queryLower.split(/[\s\W]+/).filter(Boolean);

      const scored = this.products
        .filter(p => !collection || p.collection === collection)
        .map(p => {
          const textLower       = (p.text || '').toLowerCase();
          const collectionLower = (p.collection || '').toLowerCase();
          const nameLower       = (p.name || '').toLowerCase();

          let score = 0;

          // Exact phrase match
          if (textLower.includes(queryLower)) score += 3;

          // Token-level match
          for (const token of queryTokens) {
            if (token.length < 2) continue; // skip single-char tokens
            if (textLower.includes(token)) score += 1;
            if (collectionLower.includes(token)) score += 2;
            if (nameLower.includes(token)) score += 1;
          }

          return { id: p.id, name: p.name, collection: p.collection, score, text: p.text };
        })
        .filter(r => r.score > 0);

      if (scored.length === 0) return [];

      // Normalize scores to [0, 1]
      const maxScore = Math.max(...scored.map(r => r.score));
      const normalized = scored.map(r => ({
        ...r,
        score: maxScore > 0 ? r.score / maxScore : 0,
      }));

      return normalized
        .filter(r => r.score >= minScore)
        .sort((a, b) => b.score - a.score)
        .slice(0, maxResults);
    }

    // -------------------------------------------------------------------------
    // vectorSearch — full cosine similarity search (server-side)
    // -------------------------------------------------------------------------

    /**
     * Rank all stored products by cosine similarity to the given query embedding.
     * Call this server-side after obtaining a query embedding from OpenAI.
     *
     * @param {number[]} queryEmbedding  1536-dim float array from text-embedding-3-small
     * @param {{ maxResults?: number, collection?: string|null, minScore?: number }} options
     * @returns {Array<{id, name, collection, score}>}
     */
    vectorSearch(queryEmbedding, options = {}) {
      const { maxResults = 5, collection = null, minScore = 0.3 } = options;

      if (!queryEmbedding || !Array.isArray(queryEmbedding)) return [];

      const scored = this.products
        .filter(p => !collection || p.collection === collection)
        .filter(p => Array.isArray(p.embedding) && p.embedding.length > 0)
        .map(p => ({
          id:         p.id,
          name:       p.name,
          collection: p.collection,
          score:      this._cosineSimilarity(queryEmbedding, p.embedding),
        }))
        .filter(r => r.score >= minScore);

      return scored
        .sort((a, b) => b.score - a.score)
        .slice(0, maxResults);
    }

    // -------------------------------------------------------------------------
    // search — unified entry point
    // -------------------------------------------------------------------------

    /**
     * Search for products matching the query.
     *
     * In a browser context (or when no queryEmbedding is provided), this falls
     * back to keywordSearch. Pass a pre-computed queryEmbedding (from the
     * server-side OpenAI call in api/assistant.js) to use full vector search.
     *
     * @param {string} query                  Natural-language query
     * @param {{ maxResults?: number, collection?: string|null, minScore?: number, queryEmbedding?: number[]|null }} options
     * @returns {Promise<Array<{id, name, collection, score, product}>>}
     */
    async search(query, options = {}) {
      if (!this.ready) await this.init();

      const { maxResults = 5, collection = null, minScore = 0.3, queryEmbedding = null } = options;

      let raw;

      if (queryEmbedding && Array.isArray(queryEmbedding) && queryEmbedding.length > 0) {
        // Full vector search — server-side path
        raw = this.vectorSearch(queryEmbedding, { maxResults, collection, minScore });
      } else {
        // Keyword fallback — client-side path
        raw = this.keywordSearch(query, { maxResults, collection, minScore });
      }

      // Attach full product record if available (products array has all fields)
      return raw.map(r => {
        const full = this.products.find(p => p.id === r.id) || null;
        return { ...r, product: full };
      });
    }

    // -------------------------------------------------------------------------
    // findSimilar — product-to-product similarity
    // -------------------------------------------------------------------------

    /**
     * Find products similar to a given product (by its stored embedding).
     * Useful for "You might also like..." recommendations.
     *
     * @param {string} productId
     * @param {number} [maxResults=4]
     * @returns {Array<{id, name, collection, score}>}
     */
    findSimilar(productId, maxResults = 4) {
      const source = this.products.find(p => p.id === productId);
      if (!source || !Array.isArray(source.embedding)) {
        console.warn('[SemanticSearch] findSimilar: no embedding for', productId);
        return [];
      }

      return this.products
        .filter(p => p.id !== productId && Array.isArray(p.embedding) && p.embedding.length > 0)
        .map(p => ({
          id:         p.id,
          name:       p.name,
          collection: p.collection,
          score:      this._cosineSimilarity(source.embedding, p.embedding),
        }))
        .sort((a, b) => b.score - a.score)
        .slice(0, maxResults);
    }

    // -------------------------------------------------------------------------
    // getCollectionProducts — all products in a collection by quality order
    // -------------------------------------------------------------------------

    /**
     * Return all products in the given collection.
     * "Quality" order here means sorted by how many fields are populated
     * (richer products rank higher — useful as a proxy for feature completeness).
     *
     * @param {string} collection  e.g. 'black-rose', 'love-hurts', 'signature'
     * @returns {Array<{id, name, collection, text, embedding}>}
     */
    getCollectionProducts(collection) {
      return this.products
        .filter(p => p.collection === collection)
        .map(p => ({
          ...p,
          _quality: [p.name, p.text, p.embedding].filter(Boolean).length,
        }))
        .sort((a, b) => b._quality - a._quality)
        .map(({ _quality, ...rest }) => rest); // strip internal key
    }
  }

  return SemanticSearch;
}));

// ---------------------------------------------------------------------------
// Browser auto-init
// ---------------------------------------------------------------------------

if (typeof window !== 'undefined' && window.SemanticSearch) {
  // Auto-init a shared instance on window.search
  window.search = new window.SemanticSearch();
  window.search.init().catch(err => {
    console.warn('[SemanticSearch] Auto-init failed:', err.message || err);
  });
}
