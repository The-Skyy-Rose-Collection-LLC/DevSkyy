/**
 * SkyyRose — WordPressClient
 * REST API client for WordPress + WooCommerce with rate limiting,
 * TTL cache, retry with exponential backoff, and graceful degradation.
 */

class WordPressClient {
  /**
   * @param {Object} config
   * @param {string} [config.baseURL]         - defaults to window.location.origin
   * @param {string} [config.consumerKey]     - WC REST API consumer key
   * @param {string} [config.consumerSecret]  - WC REST API consumer secret
   * @param {number} [config.cacheTTL]        - ms to keep cached responses (default 1 hr)
   * @param {number} [config.rateLimit]       - min ms between requests (default 100 ms)
   */
  constructor(config = {}) {
    this.baseURL =
      config.baseURL ||
      (typeof window !== 'undefined' ? window.location.origin : '');

    // Consumer credentials — check config, then localStorage, then env-injected globals
    this.consumerKey =
      config.consumerKey ||
      (typeof localStorage !== 'undefined'
        ? localStorage.getItem('wc_consumer_key')
        : null) ||
      (typeof window !== 'undefined' ? window.WC_CONSUMER_KEY : null) ||
      null;

    this.consumerSecret =
      config.consumerSecret ||
      (typeof localStorage !== 'undefined'
        ? localStorage.getItem('wc_consumer_secret')
        : null) ||
      (typeof window !== 'undefined' ? window.WC_CONSUMER_SECRET : null) ||
      null;

    // Cache TTL: default 1 hour
    this.cacheTTL =
      typeof config.cacheTTL === 'number' ? config.cacheTTL : 3_600_000;

    // Rate limit: minimum ms between requests
    this.rateLimit =
      typeof config.rateLimit === 'number' ? config.rateLimit : 100;

    // Internal state
    this._cache = new Map();           // key -> { data, expiresAt }
    this._requestQueue = Promise.resolve();
    this._lastRequestTime = 0;

    console.log('[WordPressClient] Initialised —', this.baseURL);
  }

  // -------------------------------------------------------------------------
  // Internal — cache helpers
  // -------------------------------------------------------------------------

  _cacheKey(endpoint, params) {
    return endpoint + (params ? '?' + new URLSearchParams(params).toString() : '');
  }

  _cacheGet(key) {
    const entry = this._cache.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this._cache.delete(key);
      return null;
    }
    return entry.data;
  }

  _cacheSet(key, data) {
    this._cache.set(key, { data, expiresAt: Date.now() + this.cacheTTL });
  }

  // -------------------------------------------------------------------------
  // Internal — rate limiter (serialises requests, enforces min gap)
  // -------------------------------------------------------------------------

  _enqueue(fn) {
    this._requestQueue = this._requestQueue.then(async () => {
      const elapsed = Date.now() - this._lastRequestTime;
      if (elapsed < this.rateLimit) {
        await new Promise((r) => setTimeout(r, this.rateLimit - elapsed));
      }
      this._lastRequestTime = Date.now();
      return fn();
    });
    return this._requestQueue;
  }

  // -------------------------------------------------------------------------
  // Internal — build auth header
  // -------------------------------------------------------------------------

  _authHeaders() {
    if (!this.consumerKey || !this.consumerSecret) return {};
    const credentials = btoa(`${this.consumerKey}:${this.consumerSecret}`);
    return { Authorization: `Basic ${credentials}` };
  }

  // -------------------------------------------------------------------------
  // async request(endpoint, options) — core fetch with cache + retry
  // -------------------------------------------------------------------------

  async request(endpoint, options = {}) {
    const {
      method = 'GET',
      params = null,
      body = null,
      skipCache = false,
      retries = 3,
    } = options;

    const cacheKey = this._cacheKey(endpoint, params);

    // Return cached data for GET requests
    if (method === 'GET' && !skipCache) {
      const cached = this._cacheGet(cacheKey);
      if (cached !== null) {
        return cached;
      }
    }

    // Build URL
    let url = `${this.baseURL}${endpoint}`;
    if (params) {
      url += (url.includes('?') ? '&' : '?') + new URLSearchParams(params).toString();
    }

    const fetchOptions = {
      method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...this._authHeaders(),
        ...(options.headers || {}),
      },
    };

    if (body) {
      fetchOptions.body =
        typeof body === 'string' ? body : JSON.stringify(body);
    }

    // Retry loop with exponential backoff: 1s, 2s, 4s
    const delays = [1000, 2000, 4000];

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await this._enqueue(() => fetch(url, fetchOptions));

        if (!response.ok) {
          const errText = await response.text().catch(() => '');
          throw new Error(
            `[WordPressClient] HTTP ${response.status} ${response.statusText} — ${url}\n${errText}`
          );
        }

        const data = await response.json();

        if (method === 'GET' && !skipCache) {
          this._cacheSet(cacheKey, data);
        }

        return data;
      } catch (err) {
        if (attempt < retries) {
          const delay = delays[attempt] ?? 4000;
          console.warn(
            `[WordPressClient] Attempt ${attempt + 1} failed. Retrying in ${delay}ms…`,
            err.message
          );
          await new Promise((r) => setTimeout(r, delay));
        } else {
          throw err;
        }
      }
    }
  }

  // -------------------------------------------------------------------------
  // getProducts(params) — list products with optional filters
  // -------------------------------------------------------------------------

  async getProducts(params = {}) {
    try {
      return await this.request('/wp-json/wc/v3/products', { params });
    } catch (err) {
      console.warn('[WordPressClient] getProducts failed — using static CONFIG', err.message);
      return this._staticProductsFallback();
    }
  }

  // -------------------------------------------------------------------------
  // getProductsByCollection(collection) — filter by category slug
  // -------------------------------------------------------------------------

  async getProductsByCollection(collection) {
    try {
      return await this.request('/wp-json/wc/v3/products', {
        params: { category: collection, per_page: 100 },
      });
    } catch (err) {
      console.warn(
        '[WordPressClient] getProductsByCollection failed — using static CONFIG',
        err.message
      );
      return this._staticProductsFallback(collection);
    }
  }

  // -------------------------------------------------------------------------
  // getProduct(id) — single product
  // -------------------------------------------------------------------------

  async getProduct(id) {
    try {
      return await this.request(`/wp-json/wc/v3/products/${id}`);
    } catch (err) {
      console.warn('[WordPressClient] getProduct failed — graceful degradation', err.message);
      return null;
    }
  }

  // -------------------------------------------------------------------------
  // getProductVariations(productId)
  // -------------------------------------------------------------------------

  async getProductVariations(productId) {
    try {
      return await this.request(`/wp-json/wc/v3/products/${productId}/variations`);
    } catch (err) {
      console.warn('[WordPressClient] getProductVariations failed', err.message);
      return [];
    }
  }

  // -------------------------------------------------------------------------
  // addToCart(productId, quantity, variationId)
  // Uses WC ajax endpoint; queues via service worker background sync on failure
  // -------------------------------------------------------------------------

  async addToCart(productId, quantity = 1, variationId = null) {
    const nonce =
      (typeof window !== 'undefined' &&
        (window.wcData?.nonce || window._wc_cart_nonce)) ||
      '';

    const formData = new URLSearchParams({
      product_id: String(productId),
      quantity: String(quantity),
      ...(variationId ? { variation_id: String(variationId) } : {}),
      ...(nonce ? { nonce } : {}),
    });

    const url = `${this.baseURL}/?wc-ajax=add_to_cart`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[WordPressClient] Added to cart:', data);
      return data;
    } catch (err) {
      console.warn('[WordPressClient] addToCart failed — queuing for background sync', err.message);

      // Attempt to queue via service worker background sync
      if (navigator.serviceWorker && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'QUEUE_CART_SYNC',
          payload: Object.fromEntries(formData),
        });
      }

      throw err;
    }
  }

  // -------------------------------------------------------------------------
  // getCart() — fetch current cart via WC Store API or ajax fragments
  // -------------------------------------------------------------------------

  async getCart() {
    // Try WC Store API (WC 5+) first
    try {
      return await this.request('/wp-json/wc/store/v1/cart', { skipCache: true });
    } catch (_storeErr) {
      // Fallback: legacy ajax fragments
      try {
        const response = await fetch(
          `${this.baseURL}/?wc-ajax=get_refreshed_fragments`,
          { method: 'POST' }
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (err) {
        console.warn('[WordPressClient] getCart failed', err.message);
        return null;
      }
    }
  }

  // -------------------------------------------------------------------------
  // getCartCount() — returns number of items in cart
  // -------------------------------------------------------------------------

  async getCartCount() {
    try {
      const cart = await this.getCart();
      if (!cart) return 0;

      // WC Store API shape
      if (typeof cart.items_count === 'number') return cart.items_count;

      // Legacy fragments shape
      if (cart.fragments) {
        const countEl = cart.fragments['.cart-contents-count'] ||
          cart.fragments['.widget_shopping_cart_item_count'];
        if (countEl) {
          const match = String(countEl).match(/\d+/);
          return match ? parseInt(match[0], 10) : 0;
        }
      }

      return 0;
    } catch (err) {
      console.warn('[WordPressClient] getCartCount failed', err.message);
      return 0;
    }
  }

  // -------------------------------------------------------------------------
  // syncProductsToConfig() — hydrate CONFIG.rooms hotspots with live WP data
  // Maps by product SKU pattern: SR-BR-001, SR-LH-001, SR-SIG-001
  // -------------------------------------------------------------------------

  async syncProductsToConfig() {
    const CONFIG =
      typeof window !== 'undefined' ? window.CONFIG : null;

    if (!CONFIG || !CONFIG.rooms) {
      console.warn('[WordPressClient] syncProductsToConfig: CONFIG.rooms not found');
      return;
    }

    let products;
    try {
      products = await this.getProducts({ per_page: 100, status: 'publish' });
    } catch (err) {
      console.warn(
        '[WordPressClient] syncProductsToConfig: WP unavailable — keeping static CONFIG data',
        err.message
      );
      return;
    }

    if (!Array.isArray(products) || products.length === 0) {
      console.warn('[WordPressClient] syncProductsToConfig: no products returned');
      return;
    }

    // Build SKU map for O(1) lookup
    const skuMap = new Map(
      products.map((p) => [p.sku, p])
    );

    // Collection prefix -> room key mapping (extend as needed)
    const COLLECTION_PREFIX_MAP = {
      'SR-BR': 'blackRose',
      'SR-LH': 'loveHurts',
      'SR-SIG': 'signature',
    };

    let updatedCount = 0;

    for (const [roomKey, room] of Object.entries(CONFIG.rooms)) {
      if (!Array.isArray(room.hotspots)) continue;

      for (const hotspot of room.hotspots) {
        const sku = hotspot.sku || hotspot.productSKU;
        if (!sku) continue;

        const product = skuMap.get(sku);
        if (!product) continue;

        // Hydrate hotspot with live WP product data
        hotspot.productId = product.id;
        hotspot.name = product.name || hotspot.name;
        hotspot.price = product.price || hotspot.price;
        hotspot.regularPrice = product.regular_price || hotspot.regularPrice;
        hotspot.salePrice = product.sale_price || hotspot.salePrice;
        hotspot.onSale = product.on_sale ?? hotspot.onSale;
        hotspot.permalink = product.permalink || hotspot.permalink;
        hotspot.images =
          Array.isArray(product.images) && product.images.length
            ? product.images.map((img) => img.src)
            : hotspot.images;
        hotspot.description = product.short_description || hotspot.description;
        hotspot.stockStatus = product.stock_status || hotspot.stockStatus;
        hotspot.manageStock = product.manage_stock ?? hotspot.manageStock;
        hotspot.stockQuantity =
          product.stock_quantity != null
            ? product.stock_quantity
            : hotspot.stockQuantity;

        updatedCount++;
      }
    }

    console.log(
      `[WordPressClient] syncProductsToConfig: updated ${updatedCount} hotspot(s) from ${products.length} product(s)`
    );
  }

  // -------------------------------------------------------------------------
  // Internal — static fallback when WP is unavailable
  // -------------------------------------------------------------------------

  _staticProductsFallback(collection = null) {
    const CONFIG =
      typeof window !== 'undefined' ? window.CONFIG : null;

    if (!CONFIG || !CONFIG.rooms) {
      console.warn('[WordPressClient] No static CONFIG available');
      return [];
    }

    // Flatten all hotspots from all rooms into a product-like array
    const all = [];
    for (const [roomKey, room] of Object.entries(CONFIG.rooms)) {
      if (!Array.isArray(room.hotspots)) continue;

      for (const hotspot of room.hotspots) {
        // Filter by collection if requested
        if (collection) {
          const collectionKey = collection.toLowerCase().replace(/-/g, '');
          if (!roomKey.toLowerCase().includes(collectionKey) &&
              !(hotspot.sku || '').toLowerCase().includes(collectionKey)) {
            continue;
          }
        }

        all.push({
          id: hotspot.productId || null,
          name: hotspot.name,
          sku: hotspot.sku || hotspot.productSKU || '',
          price: hotspot.price,
          regular_price: hotspot.regularPrice || hotspot.price,
          sale_price: hotspot.salePrice || '',
          on_sale: hotspot.onSale || false,
          images: (hotspot.images || []).map((src) => ({ src })),
          short_description: hotspot.description || '',
          stock_status: hotspot.stockStatus || 'instock',
          permalink: hotspot.permalink || '',
          _source: 'static-config',
        });
      }
    }

    return all;
  }

  // -------------------------------------------------------------------------
  // Utility — clear the in-memory cache
  // -------------------------------------------------------------------------

  clearCache() {
    this._cache.clear();
    console.log('[WordPressClient] Cache cleared');
  }
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------
if (typeof window !== 'undefined') {
  window.WordPressClient = WordPressClient;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = WordPressClient;
}
