/**
 * SkyyRose Collection Page — Interactive Logic
 * Product modals, quick view, wishlist, size selector, keyboard nav
 */
(function () {
  'use strict';

  /* ── State ── */
  let currentProduct = null;
  let selectedSize = null;

  /* ── DOM refs (created on init) ── */
  let modalBackdrop, modal;

  /* ── Product data lookup ── */
  function getProductData(productId) {
    if (typeof CONFIG === 'undefined') return null;
    for (const room of CONFIG.rooms) {
      for (const hs of room.hotspots) {
        if (hs.product.id === productId) return hs.product;
      }
    }
    return null;
  }

  /* ── Build modal markup (injected once) ── */
  function createModalDOM() {
    // Backdrop
    modalBackdrop = document.createElement('div');
    modalBackdrop.id = 'product-modal-backdrop';
    modalBackdrop.className = 'pm-backdrop';
    modalBackdrop.setAttribute('aria-hidden', 'true');

    // Modal
    modal = document.createElement('div');
    modal.id = 'product-modal';
    modal.className = 'pm-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', 'Product details');

    modal.innerHTML = `
      <div class="pm-handle"></div>
      <button class="pm-close" aria-label="Close product details">&times;</button>
      <div class="pm-body">
        <div class="pm-image-col">
          <div class="pm-image-wrap">
            <img class="pm-hero-img" src="" alt="" loading="lazy">
          </div>
        </div>
        <div class="pm-info-col">
          <span class="pm-collection-tag"></span>
          <h2 class="pm-name"></h2>
          <p class="pm-tagline"></p>
          <div class="pm-price-row">
            <span class="pm-price"></span>
            <span class="pm-badge"></span>
          </div>
          <div class="pm-divider"></div>
          <p class="pm-description"></p>
          <p class="pm-spec"></p>
          <div class="pm-colors">
            <span class="pm-label">Color</span>
            <div class="pm-color-swatches"></div>
          </div>
          <div class="pm-sizes">
            <span class="pm-label">Size</span>
            <div class="pm-size-btns"></div>
          </div>
          <button class="pm-cta pm-cta-waiting" disabled>Select a size</button>
          <div class="pm-wishlist-row">
            <button class="pm-wishlist-btn" aria-label="Add to wishlist">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              <span>Add to Wishlist</span>
            </button>
          </div>
          <a class="pm-collection-link" href="#">
            <span class="pm-collection-link-text"></span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </a>
        </div>
      </div>
    `;

    document.body.appendChild(modalBackdrop);
    document.body.appendChild(modal);

    // Event listeners
    modalBackdrop.addEventListener('click', closeModal);
    modal.querySelector('.pm-close').addEventListener('click', closeModal);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modal.classList.contains('pm-open')) {
        closeModal();
      }
    });
  }

  /* ── Inject modal styles ── */
  function injectModalStyles() {
    if (document.getElementById('pm-styles')) return;
    const style = document.createElement('style');
    style.id = 'pm-styles';
    style.textContent = `
      .pm-backdrop {
        position: fixed; inset: 0; z-index: 900;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        opacity: 0; pointer-events: none;
        transition: opacity 0.3s ease;
      }
      .pm-backdrop.pm-open { opacity: 1; pointer-events: auto; }

      .pm-modal {
        position: fixed; z-index: 910;
        background: rgba(14,14,14,0.96);
        backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.06);
        overflow-y: auto;
        opacity: 0; pointer-events: none;
        transition: opacity 0.35s ease, transform 0.35s ease;
      }

      /* Desktop: centered card */
      @media (min-width: 769px) {
        .pm-modal {
          top: 50%; left: 50%;
          transform: translate(-50%, -48%);
          width: 90vw; max-width: 960px;
          max-height: 90vh;
          border-radius: 16px;
        }
        .pm-modal.pm-open {
          opacity: 1; pointer-events: auto;
          transform: translate(-50%, -50%);
        }
        .pm-handle { display: none; }
        .pm-body {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0;
        }
      }

      /* Mobile: bottom sheet */
      @media (max-width: 768px) {
        .pm-modal {
          bottom: 0; left: 0; right: 0;
          max-height: 88vh;
          border-radius: 16px 16px 0 0;
          transform: translateY(100%);
        }
        .pm-modal.pm-open {
          opacity: 1; pointer-events: auto;
          transform: translateY(0);
        }
        .pm-handle {
          width: 36px; height: 4px;
          border-radius: 2px;
          background: rgba(255,255,255,0.15);
          margin: 12px auto 8px;
        }
        .pm-body {
          display: flex;
          flex-direction: column;
        }
      }

      .pm-close {
        position: absolute; top: 16px; right: 16px;
        background: rgba(255,255,255,0.06); border: none;
        color: rgba(255,255,255,0.5); font-size: 22px;
        width: 40px; height: 40px; border-radius: 50%;
        cursor: pointer; display: flex; align-items: center; justify-content: center;
        transition: all 0.2s;
        z-index: 5;
      }
      .pm-close:hover { background: rgba(255,255,255,0.12); color: #fff; }

      .pm-image-col {
        position: relative;
        background: #111;
        display: flex; align-items: center; justify-content: center;
        min-height: 280px;
      }
      @media (min-width: 769px) {
        .pm-image-col { border-radius: 16px 0 0 16px; min-height: 400px; }
      }
      .pm-image-wrap { padding: 24px; width: 100%; }
      .pm-hero-img {
        width: 100%; height: auto; max-height: 480px;
        object-fit: contain; border-radius: 8px;
      }

      .pm-info-col { padding: 32px; display: flex; flex-direction: column; gap: 12px; }
      @media (max-width: 768px) { .pm-info-col { padding: 20px 20px 32px; } }

      .pm-collection-tag {
        font-size: 10px; letter-spacing: 0.4em; text-transform: uppercase;
        color: var(--collection-primary, #B76E79);
        font-family: var(--font-body, sans-serif);
        font-weight: 600;
      }
      .pm-name {
        font-family: var(--font-editorial, serif);
        font-size: clamp(1.5rem, 3vw, 2rem);
        color: #fff; font-weight: 600; line-height: 1.2;
        margin: 0;
      }
      .pm-tagline {
        font-family: var(--font-editorial, serif);
        font-style: italic; color: rgba(255,255,255,0.5);
        font-size: 0.95rem; margin: 0;
      }
      .pm-price-row {
        display: flex; align-items: center; gap: 12px;
        margin-top: 4px;
      }
      .pm-price {
        font-size: 1.5rem; font-weight: 700;
        color: var(--collection-accent, #E8A5B2);
      }
      .pm-badge {
        font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
        padding: 4px 12px; border-radius: 999px; font-weight: 700;
        font-family: var(--font-body, sans-serif);
      }
      .pm-badge[data-status="PRE-ORDER"] {
        background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.6);
        border: 1px solid rgba(255,255,255,0.12);
      }
      .pm-badge[data-status="AVAILABLE"] {
        background: rgba(40,167,69,0.15); color: #4ade80;
        border: 1px solid rgba(40,167,69,0.3);
      }
      .pm-divider {
        width: 100%; height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 4px 0;
      }
      .pm-description {
        font-size: 0.9rem; color: rgba(255,255,255,0.65);
        line-height: 1.65; margin: 0;
      }
      .pm-spec {
        font-size: 0.8rem; font-style: italic;
        color: var(--collection-primary, rgba(183,110,121,0.5));
        margin: 0;
      }

      /* Colors */
      .pm-colors, .pm-sizes { display: flex; flex-direction: column; gap: 8px; }
      .pm-label {
        font-size: 10px; letter-spacing: 0.3em; text-transform: uppercase;
        color: rgba(255,255,255,0.4); font-family: var(--font-body, sans-serif);
      }
      .pm-color-swatches { display: flex; gap: 8px; flex-wrap: wrap; }
      .pm-swatch {
        width: 28px; height: 28px; border-radius: 50%;
        border: 2px solid transparent; cursor: pointer;
        transition: border-color 0.2s, transform 0.2s;
        position: relative;
      }
      .pm-swatch:hover { transform: scale(1.15); }
      .pm-swatch.selected { border-color: var(--collection-primary, #B76E79); }
      .pm-swatch-tooltip {
        position: absolute; bottom: calc(100% + 6px); left: 50%;
        transform: translateX(-50%);
        font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase;
        color: rgba(255,255,255,0.6); white-space: nowrap;
        background: rgba(0,0,0,0.8); padding: 3px 8px; border-radius: 3px;
        pointer-events: none; opacity: 0; transition: opacity 0.2s;
      }
      .pm-swatch:hover .pm-swatch-tooltip { opacity: 1; }

      /* Sizes */
      .pm-size-btns { display: flex; gap: 8px; flex-wrap: wrap; }
      .pm-size-btn {
        padding: 8px 16px; font-size: 12px; letter-spacing: 0.06em;
        font-family: var(--font-editorial, serif);
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.5); background: transparent;
        border-radius: 4px; cursor: pointer;
        transition: all 0.2s;
      }
      .pm-size-btn:hover { border-color: rgba(255,255,255,0.3); color: rgba(255,255,255,0.8); }
      .pm-size-btn.selected {
        border-color: var(--collection-primary, #B76E79);
        color: var(--collection-accent, #E8A5B2);
        background: rgba(183,110,121,0.06);
      }

      /* CTA */
      .pm-cta {
        width: 100%; padding: 14px;
        font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase;
        font-family: var(--font-body, sans-serif); font-weight: 700;
        border: none; border-radius: 6px; cursor: pointer;
        transition: all 0.3s; margin-top: 4px;
      }
      .pm-cta-waiting {
        background: rgba(255,255,255,0.04);
        color: rgba(255,255,255,0.25); cursor: not-allowed;
      }
      .pm-cta-ready {
        background: var(--collection-primary, #B76E79);
        color: #fff; cursor: pointer;
      }
      .pm-cta-ready:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px var(--collection-glow, rgba(183,110,121,0.3));
      }

      /* Wishlist row */
      .pm-wishlist-row { display: flex; align-items: center; }
      .pm-wishlist-btn {
        display: flex; align-items: center; gap: 8px;
        background: none; border: none; color: rgba(255,255,255,0.4);
        font-size: 12px; letter-spacing: 0.05em;
        font-family: var(--font-body, sans-serif);
        cursor: pointer; padding: 6px 0; transition: color 0.2s;
      }
      .pm-wishlist-btn:hover { color: var(--collection-primary, #B76E79); }
      .pm-wishlist-btn.active { color: var(--collection-primary, #B76E79); }
      .pm-wishlist-btn.active svg { fill: currentColor; }

      /* Collection link */
      .pm-collection-link {
        display: inline-flex; align-items: center; gap: 8px;
        font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase;
        font-family: var(--font-body, sans-serif); font-weight: 600;
        color: var(--collection-primary, #B76E79);
        text-decoration: none; padding: 8px 0;
        transition: gap 0.2s, color 0.2s;
        border-top: 1px solid rgba(255,255,255,0.04);
        margin-top: 4px; padding-top: 12px;
      }
      .pm-collection-link:hover { gap: 12px; color: var(--collection-accent, #E8A5B2); }
    `;
    document.head.appendChild(style);
  }

  /* ── Collection routing ── */
  const COLLECTION_ROUTES = {
    'BLACK ROSE': { url: 'black-rose.html', label: 'Explore BLACK ROSE' },
    'LOVE HURTS': { url: 'love-hurts.html', label: 'Explore LOVE HURTS' },
    'SIGNATURE':  { url: 'signature.html',  label: 'Explore SIGNATURE' }
  };

  /* ── Open modal ── */
  function openModal(productId) {
    const product = getProductData(productId);
    if (!product) return;

    currentProduct = product;
    selectedSize = null;

    // Populate modal
    modal.querySelector('.pm-collection-tag').textContent = product.collection;
    modal.querySelector('.pm-name').textContent = product.name;
    modal.querySelector('.pm-tagline').textContent = product.tagline || '';
    modal.querySelector('.pm-price').textContent = product.price;

    const badge = modal.querySelector('.pm-badge');
    badge.textContent = product.badge;
    badge.setAttribute('data-status', product.badge);

    modal.querySelector('.pm-description').textContent = product.description || '';
    modal.querySelector('.pm-spec').textContent = product.spec || '';

    // Hero image
    const img = modal.querySelector('.pm-hero-img');
    img.src = product.image || '';
    img.alt = product.name;

    // Colors
    const colorWrap = modal.querySelector('.pm-color-swatches');
    colorWrap.innerHTML = '';
    if (product.variants && product.variants.colors) {
      product.variants.colors.forEach(function (c, i) {
        const swatch = document.createElement('button');
        swatch.className = 'pm-swatch' + (i === 0 ? ' selected' : '');
        swatch.style.background = c.hex;
        swatch.setAttribute('aria-label', c.name);
        swatch.innerHTML = '<span class="pm-swatch-tooltip">' + c.name + '</span>';
        swatch.addEventListener('click', function () {
          colorWrap.querySelectorAll('.pm-swatch').forEach(function (s) { s.classList.remove('selected'); });
          swatch.classList.add('selected');
        });
        colorWrap.appendChild(swatch);
      });
      modal.querySelector('.pm-colors').style.display = '';
    } else {
      modal.querySelector('.pm-colors').style.display = 'none';
    }

    // Sizes
    const sizeWrap = modal.querySelector('.pm-size-btns');
    sizeWrap.innerHTML = '';
    const cta = modal.querySelector('.pm-cta');
    if (product.variants && product.variants.sizes) {
      product.variants.sizes.forEach(function (s) {
        var btn = document.createElement('button');
        btn.className = 'pm-size-btn';
        btn.textContent = s;
        btn.addEventListener('click', function () {
          sizeWrap.querySelectorAll('.pm-size-btn').forEach(function (b) { b.classList.remove('selected'); });
          btn.classList.add('selected');
          selectedSize = s;
          cta.disabled = false;
          cta.className = 'pm-cta pm-cta-ready';
          cta.textContent = product.badge === 'PRE-ORDER' ? 'Pre-Order Now' : 'Add to Cart';
        });
        sizeWrap.appendChild(btn);
      });
      modal.querySelector('.pm-sizes').style.display = '';
    } else {
      modal.querySelector('.pm-sizes').style.display = 'none';
      cta.disabled = false;
      cta.className = 'pm-cta pm-cta-ready';
      cta.textContent = product.badge === 'PRE-ORDER' ? 'Pre-Order Now' : 'Add to Cart';
    }

    // Reset CTA
    if (product.variants && product.variants.sizes && product.variants.sizes.length > 0) {
      cta.disabled = true;
      cta.className = 'pm-cta pm-cta-waiting';
      cta.textContent = 'Select a size';
    }

    // CTA click
    cta.onclick = function () {
      if (cta.disabled) return;
      cta.textContent = '  Added!';
      cta.style.background = '#1e5c35';
      setTimeout(function () {
        cta.textContent = product.badge === 'PRE-ORDER' ? 'Pre-Order Now' : 'Add to Cart';
        cta.style.background = '';
      }, 2000);
    };

    // Collection link
    var route = COLLECTION_ROUTES[product.collection] || {};
    var colLink = modal.querySelector('.pm-collection-link');
    colLink.href = route.url || '#';
    modal.querySelector('.pm-collection-link-text').textContent = route.label || 'View Collection';

    // Wishlist
    var wBtn = modal.querySelector('.pm-wishlist-btn');
    wBtn.classList.remove('active');
    wBtn.querySelector('span').textContent = 'Add to Wishlist';
    wBtn.onclick = function () {
      wBtn.classList.toggle('active');
      wBtn.querySelector('span').textContent = wBtn.classList.contains('active')
        ? 'In Wishlist'
        : 'Add to Wishlist';
    };

    // Show
    modalBackdrop.classList.add('pm-open');
    modal.classList.add('pm-open');
    modalBackdrop.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Focus trap
    setTimeout(function () { modal.querySelector('.pm-close').focus(); }, 100);
  }

  /* ── Close modal ── */
  function closeModal() {
    modalBackdrop.classList.remove('pm-open');
    modal.classList.remove('pm-open');
    modalBackdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    currentProduct = null;
    selectedSize = null;
  }

  /* ── Wire up quick-view buttons ── */
  function wireQuickViews() {
    document.querySelectorAll('.btn-quick-view, [data-quick-view]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var pid = btn.getAttribute('data-product') || btn.getAttribute('data-quick-view');
        if (pid) openModal(pid);
      });
    });

    // Also make product cards clickable
    document.querySelectorAll('.product-card').forEach(function (card) {
      card.style.cursor = 'pointer';
      card.addEventListener('click', function (e) {
        // Don't trigger if clicking a button inside the card
        if (e.target.closest('button') || e.target.closest('a')) return;
        var pid = card.getAttribute('data-product-id');
        if (pid) openModal(pid);
      });
    });
  }

  /* ── Wire up card wishlist buttons ── */
  function wireCardWishlists() {
    document.querySelectorAll('.product-card .wishlist-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        btn.classList.toggle('active');
      });
    });
  }

  /* ── Navbar scroll effect ── */
  function initNavScroll() {
    var nav = document.querySelector('.navbar');
    if (!nav) return;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 60) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  /* ── Scroll-reveal animations ── */
  function initScrollReveal() {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.product-card, .collection-card, .story-content, .story-image').forEach(function (el) {
      el.classList.add('reveal-item');
      observer.observe(el);
    });

    // Inject reveal CSS
    if (!document.getElementById('reveal-styles')) {
      var s = document.createElement('style');
      s.id = 'reveal-styles';
      s.textContent = `
        .reveal-item { opacity: 0; transform: translateY(30px); transition: opacity 0.7s ease, transform 0.7s ease; }
        .reveal-item.revealed { opacity: 1; transform: translateY(0); }
      `;
      document.head.appendChild(s);
    }
  }

  /* ── Init ── */
  function init() {
    injectModalStyles();
    createModalDOM();
    wireQuickViews();
    wireCardWishlists();
    initNavScroll();
    initScrollReveal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
