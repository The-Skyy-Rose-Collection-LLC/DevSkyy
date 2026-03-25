/**
 * AnalyticsManager
 * Thin wrapper around Google Tag Manager / GA4 dataLayer pushes.
 * Tracks SkyyRose-specific events with Enhanced Ecommerce support.
 */
class AnalyticsManager {
  constructor(config = {}) {
    this.gtmId  = config.gtmId  ?? null;
    this.ga4Id  = config.ga4Id  ?? null;
    this.debug  = config.debug  ?? false;
  }

  // ---------------------------------------------------------------------------
  // Bootstrap
  // ---------------------------------------------------------------------------
  init() {
    // Ensure dataLayer exists before GTM script loads
    window.dataLayer = window.dataLayer || [];

    if (this.gtmId) {
      this._injectGTM(this.gtmId);
    }

    // Fire session start automatically
    this.sessionStart();
  }

  _injectGTM(id) {
    if (document.getElementById('gtm-script')) return; // already injected

    window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });

    const script = document.createElement('script');
    script.id    = 'gtm-script';
    script.async = true;
    script.src   = `https://www.googletagmanager.com/gtm.js?id=${id}`;
    document.head.appendChild(script);

    if (this.debug) {
      console.log(`[Analytics] GTM injected: ${id}`);
    }
  }

  // ---------------------------------------------------------------------------
  // Core push
  // ---------------------------------------------------------------------------
  _push(event) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(event);

    if (this.debug) {
      console.log('[Analytics] dataLayer push:', event);
    }
  }

  /**
   * Generic event tracker.
   * @param {string} eventName
   * @param {Object} params
   */
  track(eventName, params = {}) {
    this._push({
      event:     eventName,
      timestamp: Date.now(),
      ...params,
    });
  }

  // ---------------------------------------------------------------------------
  // Standard events
  // ---------------------------------------------------------------------------

  /** Fire once per page/session load. */
  sessionStart() {
    const w = window.innerWidth;
    const device_type =
      w < 768 ? 'mobile' : w < 1024 ? 'tablet' : 'desktop';

    this.track('session_start', {
      device_type,
      screen: {
        w: screen.width,
        h: screen.height,
      },
      referrer: document.referrer || null,
    });
  }

  /**
   * Track a room being viewed in the 3D experience.
   * @param {string} roomId
   * @param {string} roomName
   * @param {string} collection
   */
  roomView(roomId, roomName, collection) {
    this.track('room_view', { roomId, roomName, collection });
  }

  /**
   * Track a product hotspot being clicked inside a room.
   * @param {string} productId
   * @param {string} productName
   * @param {string} collection
   */
  hotspotClick(productId, productName, collection) {
    this.track('hotspot_click', { productId, productName, collection });
  }

  /**
   * GA4 Enhanced Ecommerce — view_item.
   * @param {{id:string, name:string, brand:string, category:string, price:number, collection:string}} product
   */
  productView(product) {
    this._push({
      event: 'view_item',
      timestamp: Date.now(),
      ecommerce: {
        currency: 'USD',
        value: product.price ?? 0,
        items: [this._mapProduct(product, 1)],
      },
    });
  }

  /**
   * GA4 Enhanced Ecommerce — add_to_cart.
   * @param {{id:string, name:string, brand:string, category:string, price:number, collection:string}} product
   * @param {number} quantity
   * @param {string|null} variation
   */
  addToCart(product, quantity = 1, variation = null) {
    const item = this._mapProduct(product, quantity);
    if (variation) item.item_variant = variation;

    this._push({
      event: 'add_to_cart',
      timestamp: Date.now(),
      ecommerce: {
        currency: 'USD',
        value: (product.price ?? 0) * quantity,
        items: [item],
      },
    });
  }

  /**
   * Track a product being added to the wishlist.
   * @param {string} productId
   * @param {string} productName
   */
  wishlistAdd(productId, productName) {
    this.track('wishlist_add', { productId, productName });
  }

  /**
   * Track a product being removed from the wishlist.
   * @param {string} productId
   * @param {string} productName
   */
  wishlistRemove(productId, productName) {
    this.track('wishlist_remove', { productId, productName });
  }

  /**
   * Track a product share action.
   * @param {string} productId
   * @param {'native'|'twitter'|'facebook'|'pinterest'|'copy'} method
   */
  productShare(productId, method) {
    this.track('product_share', { productId, method });
  }

  /** Track the AI style assistant being opened. */
  assistantOpen() {
    this.track('assistant_open');
  }

  /**
   * Track a message sent to the AI style assistant.
   * Only logs the query length for privacy — never the content itself.
   * @param {string} query
   */
  assistantMessage(query) {
    this.track('assistant_message', {
      query_length: typeof query === 'string' ? query.length : 0,
    });
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  _mapProduct(product, quantity) {
    return {
      item_id:         product.id         ?? '',
      item_name:       product.name       ?? '',
      item_brand:      product.brand      ?? 'SkyyRose',
      item_category:   product.category   ?? '',
      item_list_name:  product.collection ?? '',
      price:           product.price      ?? 0,
      quantity,
    };
  }
}

// ---------------------------------------------------------------------------
// Export & auto-init
// ---------------------------------------------------------------------------
window.AnalyticsManager = AnalyticsManager;
window.analytics = new AnalyticsManager({ debug: true });
