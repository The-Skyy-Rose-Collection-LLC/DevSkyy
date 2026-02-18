/**
 * SharingManager
 * Handles native Web Share API and a custom fallback modal for
 * Twitter, Facebook, Pinterest, and clipboard copy sharing.
 */
class SharingManager {
  constructor() {
    this._modal   = null;
    this._overlay = null;
    this._product = null;
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Share a product via the Web Share API, or the fallback modal.
   * @param {{id:string, name:string, image:string}} product
   */
  async share(product) {
    this._product = product;

    const url  = this.getShareURL(product);
    const text = this.getShareText(product);

    // Attempt native Web Share API first
    if (navigator.share) {
      try {
        await navigator.share({
          title: product.name ?? 'SkyyRose',
          text,
          url,
        });
        this._trackShare('native');
        return;
      } catch (err) {
        // User cancelled (AbortError) or API failed — fall through to modal
        if (err.name === 'AbortError') return; // user explicitly cancelled
      }
    }

    // Fallback modal
    this._showFallbackModal(product);
  }

  /**
   * Build the canonical share URL for a product.
   * @param {{id:string}} product
   * @returns {string}
   */
  getShareURL(product) {
    return `${window.location.origin}/?product=${encodeURIComponent(product.id)}`;
  }

  /**
   * Build the share text for a product.
   * @param {{name:string}} product
   * @returns {string}
   */
  getShareText(product) {
    return `Check out the ${product.name ?? 'this piece'} from SkyyRose — luxury fashion`;
  }

  // ---------------------------------------------------------------------------
  // Fallback modal
  // ---------------------------------------------------------------------------

  _showFallbackModal(product) {
    if (!this._modal) {
      this._buildFallbackModal();
    }

    // Update links with current product data
    this._populateModal(product);
    this._modal.removeAttribute('hidden');
    this._overlay.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';

    // Trap focus if a11y manager is available
    if (window.a11y && typeof window.a11y.trapFocus === 'function') {
      window.a11y.trapFocus(this._modal);
    }
  }

  _hideModal() {
    if (!this._modal) return;
    this._modal.setAttribute('hidden', '');
    this._overlay.setAttribute('hidden', '');
    document.body.style.overflow = '';

    if (window.a11y && typeof window.a11y.releaseFocus === 'function') {
      window.a11y.releaseFocus();
    }
  }

  /**
   * Create the fallback share modal DOM once and cache it.
   */
  buildFallbackModal() {
    this._buildFallbackModal();
  }

  _buildFallbackModal() {
    // Overlay
    this._overlay = document.createElement('div');
    this._overlay.className = 'share-overlay';
    this._overlay.setAttribute('aria-hidden', 'true');
    this._overlay.style.cssText =
      'position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9998;';
    this._overlay.setAttribute('hidden', '');
    this._overlay.addEventListener('click', () => this._hideModal());

    // Modal container
    this._modal = document.createElement('div');
    this._modal.className = 'share-modal';
    this._modal.setAttribute('role', 'dialog');
    this._modal.setAttribute('aria-modal', 'true');
    this._modal.setAttribute('aria-label', 'Share this product');
    this._modal.setAttribute('hidden', '');
    this._modal.style.cssText = [
      'position:fixed',
      'top:50%',
      'left:50%',
      'transform:translate(-50%,-50%)',
      'background:#fff',
      'padding:2rem',
      'border-radius:8px',
      'z-index:9999',
      'min-width:280px',
      'max-width:90vw',
      'box-shadow:0 8px 32px rgba(0,0,0,.2)',
    ].join(';');

    // --- Header ---
    const heading = document.createElement('h2');
    heading.textContent = 'Share this product';
    heading.style.cssText = 'margin:0 0 1.25rem;font-size:1.125rem;';

    // --- Buttons ---
    const btnWrap = document.createElement('div');
    btnWrap.style.cssText = 'display:flex;flex-direction:column;gap:.75rem;';

    // Twitter
    this._twitterBtn = this._makeShareButton('Share on Twitter', '#1DA1F2', () => {
      const url  = this.getShareURL(this._product);
      const text = this.getShareText(this._product);
      window.open(
        `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
        '_blank',
        'noopener,noreferrer,width=600,height=400'
      );
      this._trackShare('twitter');
    });

    // Facebook
    this._facebookBtn = this._makeShareButton('Share on Facebook', '#1877F2', () => {
      const url = this.getShareURL(this._product);
      window.open(
        `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
        '_blank',
        'noopener,noreferrer,width=600,height=400'
      );
      this._trackShare('facebook');
    });

    // Pinterest
    this._pinterestBtn = this._makeShareButton('Pin on Pinterest', '#E60023', () => {
      const url   = this.getShareURL(this._product);
      const media = this._product?.image ?? '';
      const desc  = this.getShareText(this._product);
      window.open(
        `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(url)}&media=${encodeURIComponent(media)}&description=${encodeURIComponent(desc)}`,
        '_blank',
        'noopener,noreferrer,width=750,height=550'
      );
      this._trackShare('pinterest');
    });

    // Copy link
    this._copyBtn = this._makeShareButton('Copy Link', '#333', async () => {
      try {
        await navigator.clipboard.writeText(this.getShareURL(this._product));
        this._showToast('Link copied!');
        this._trackShare('copy');
      } catch {
        // Fallback: select a temporary input
        const tmp = document.createElement('input');
        tmp.value = this.getShareURL(this._product);
        document.body.appendChild(tmp);
        tmp.select();
        document.execCommand('copy');
        document.body.removeChild(tmp);
        this._showToast('Link copied!');
        this._trackShare('copy');
      }
    });

    btnWrap.append(this._twitterBtn, this._facebookBtn, this._pinterestBtn, this._copyBtn);

    // --- Close button ---
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.setAttribute('aria-label', 'Close share dialog');
    closeBtn.style.cssText =
      'margin-top:1rem;background:none;border:1px solid #ccc;padding:.5rem 1rem;border-radius:4px;cursor:pointer;width:100%;';
    closeBtn.addEventListener('click', () => this._hideModal());

    // Escape key
    this._modal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this._hideModal();
    });

    this._modal.append(heading, btnWrap, closeBtn);
    document.body.append(this._overlay, this._modal);
  }

  _populateModal(product) {
    // Nothing dynamic needs re-wiring since buttons read this._product at click time
    const heading = this._modal.querySelector('h2');
    if (heading) heading.textContent = `Share: ${product.name ?? 'this product'}`;
  }

  _makeShareButton(label, bgColor, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.style.cssText = [
      `background:${bgColor}`,
      'color:#fff',
      'border:none',
      'padding:.65rem 1.25rem',
      'border-radius:4px',
      'cursor:pointer',
      'font-size:.95rem',
      'text-align:left',
    ].join(';');
    btn.addEventListener('click', onClick);
    return btn;
  }

  // ---------------------------------------------------------------------------
  // Toast notification
  // ---------------------------------------------------------------------------
  _showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.style.cssText = [
      'position:fixed',
      'bottom:1.5rem',
      'left:50%',
      'transform:translateX(-50%)',
      'background:#333',
      'color:#fff',
      'padding:.6rem 1.2rem',
      'border-radius:4px',
      'z-index:10000',
      'font-size:.875rem',
      'opacity:0',
      'transition:opacity .2s ease',
    ].join(';');

    document.body.appendChild(toast);

    // Fade in
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { toast.style.opacity = '1'; });
    });

    // Auto-remove after 2.5 s
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }, 2500);
  }

  // ---------------------------------------------------------------------------
  // Analytics helper
  // ---------------------------------------------------------------------------
  _trackShare(method) {
    if (window.analytics && typeof window.analytics.productShare === 'function') {
      window.analytics.productShare(this._product?.id ?? '', method);
    }
  }
}

// ---------------------------------------------------------------------------
// Export & auto-init
// ---------------------------------------------------------------------------
window.SharingManager = SharingManager;
window.sharing = new SharingManager();
