/**
 * WishlistManager
 * Persists a customer's wishlist in localStorage and dispatches
 * 'wishlist-change' events so any UI can react without tight coupling.
 */
class WishlistManager {
  static STORAGE_KEY = 'skyyrose_wishlist';

  constructor() {
    this._items = this._load();
  }

  // ---------------------------------------------------------------------------
  // Storage
  // ---------------------------------------------------------------------------
  _load() {
    try {
      const raw = localStorage.getItem(WishlistManager.STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  _save() {
    try {
      localStorage.setItem(WishlistManager.STORAGE_KEY, JSON.stringify(this._items));
    } catch (err) {
      console.warn('[WishlistManager] Could not save to localStorage:', err);
    }
  }

  _dispatch() {
    document.dispatchEvent(
      new CustomEvent('wishlist-change', {
        bubbles: true,
        detail: { count: this.count(), items: this.getAll() },
      })
    );
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Add a product to the wishlist.
   * @param {string} productId
   * @param {{name:string, price:number, image:string}} productData
   * @returns {boolean} true if added, false if already present
   */
  add(productId, productData = {}) {
    if (this.has(productId)) return false;

    this._items.push({
      id:      productId,
      name:    productData.name    ?? '',
      price:   productData.price   ?? 0,
      image:   productData.image   ?? '',
      addedAt: Date.now(),
    });

    this._save();
    this._dispatch();
    return true;
  }

  /**
   * Remove a product from the wishlist.
   * @param {string} productId
   * @returns {boolean} true if removed, false if not found
   */
  remove(productId) {
    const before = this._items.length;
    this._items  = this._items.filter((item) => item.id !== productId);

    if (this._items.length === before) return false;

    this._save();
    this._dispatch();
    return true;
  }

  /**
   * Toggle a product — add it if absent, remove if present.
   * @param {string} productId
   * @param {{name:string, price:number, image:string}} productData
   * @returns {{added: boolean}}
   */
  toggle(productId, productData = {}) {
    if (this.has(productId)) {
      this.remove(productId);
      return { added: false };
    }
    this.add(productId, productData);
    return { added: true };
  }

  /**
   * Check whether a product is in the wishlist.
   * @param {string} productId
   * @returns {boolean}
   */
  has(productId) {
    return this._items.some((item) => item.id === productId);
  }

  /**
   * Return all wishlist items sorted by addedAt descending (newest first).
   * @returns {Array}
   */
  getAll() {
    return [...this._items].sort((a, b) => b.addedAt - a.addedAt);
  }

  /**
   * Total number of items in the wishlist.
   * @returns {number}
   */
  count() {
    return this._items.length;
  }

  /**
   * Clear the entire wishlist.
   */
  clear() {
    this._items = [];
    this._save();
    this._dispatch();
  }

  /**
   * Update an element's text content (and optional data attribute) to reflect
   * the current wishlist count.
   * @param {HTMLElement} el
   */
  renderBadge(el) {
    if (!el) return;
    const n = this.count();
    el.textContent = n;
    el.dataset.count = n;
    el.setAttribute('aria-label', `${n} item${n !== 1 ? 's' : ''} in wishlist`);
    el.hidden = n === 0;
  }
}

// ---------------------------------------------------------------------------
// Export & auto-init
// ---------------------------------------------------------------------------
window.WishlistManager = WishlistManager;
window.wishlist = new WishlistManager();
