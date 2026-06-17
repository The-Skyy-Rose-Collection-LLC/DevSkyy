/**
 * Micro-Interactions — Cart Fly-To & Wishlist Burst
 *
 * Part of the SkyyRose Experience Engine, Phase 3.
 *
 * Cart fly-to: When a product is added to the bag, the front thumbnail image
 * clones itself and flies in an arc to the cart icon, then the cart badge
 * pulses with a brief scale bounce.
 *
 * Wishlist burst: When the wishlist heart button is clicked, 8 mini-heart SVG
 * particles radiate outward from the click point and fade out.
 *
 * Both animations:
 *   - Skip entirely if SkyyPerformance.isThrottled() is true
 *   - Skip if prefers-reduced-motion is set
 *   - Are fire-and-forget (no promise chains, no blocking)
 *
 * @module micro-interactions
 * @since  6.4.0
 */
(function () {
  'use strict';

  var motionOk = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function isThrottled() {
    return window.SkyyPerformance && window.SkyyPerformance.isThrottled();
  }

  // -------------------------------------------------------------------------
  // Cart fly-to
  // -------------------------------------------------------------------------

  function getCartIcon() {
    return (
      document.querySelector('.cart-icon') ||
      document.querySelector('.skyy-cart-icon') ||
      document.querySelector('[aria-label*="cart"]') ||
      document.querySelector('.header__cart') ||
      document.querySelector('.nav-cart') ||
      null
    );
  }

  function flyToCart(card) {
    if (!motionOk || isThrottled()) return;

    var imgEl = card.querySelector('.holo__img--front');
    var cartEl = getCartIcon();
    if (!imgEl || !cartEl) return;

    var imgRect = imgEl.getBoundingClientRect();
    var cartRect = cartEl.getBoundingClientRect();

    // Clone the image as a flying element.
    var clone = imgEl.cloneNode(false);
    clone.style.cssText = [
      'position:fixed',
      'z-index:99999',
      'pointer-events:none',
      'width:' + imgRect.width * 0.4 + 'px',
      'height:' + imgRect.height * 0.4 + 'px',
      'object-fit:cover',
      'border-radius:8px',
      'top:' + imgRect.top + 'px',
      'left:' + imgRect.left + 'px',
      'transition:none',
      'will-change:transform,opacity',
      'opacity:1',
    ].join(';');

    document.body.appendChild(clone);

    // Target center of cart icon.
    var targetX = cartRect.left + cartRect.width / 2 - imgRect.left - imgRect.width * 0.2;
    var targetY = cartRect.top + cartRect.height / 2 - imgRect.top - imgRect.height * 0.2;

    // Kick off the animation on the next frame so the initial position renders.
    requestAnimationFrame(function () {
      clone.style.transition = 'transform 0.65s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.65s ease';
      clone.style.transform = 'translate(' + targetX + 'px,' + targetY + 'px) scale(0.15)';
      clone.style.opacity = '0';
    });

    // Bounce the cart badge once the clone arrives.
    setTimeout(function () {
      document.body.removeChild(clone);
      bounceCart(cartEl);
    }, 680);
  }

  function bounceCart(cartEl) {
    cartEl.classList.add('skyy-cart-bounce');
    cartEl.addEventListener('animationend', function handler() {
      cartEl.classList.remove('skyy-cart-bounce');
      cartEl.removeEventListener('animationend', handler);
    });
  }

  // -------------------------------------------------------------------------
  // Wishlist burst
  // -------------------------------------------------------------------------

  /**
   * Build a heart SVG element via DOM API — no innerHTML.
   * Matches the visual output of the former HEART_SVG string constant.
   * @returns {SVGElement}
   */
  function createHeartSVG() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'currentColor');
    svg.setAttribute('aria-hidden', 'true');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute(
      'd',
      'M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z'
    );
    svg.appendChild(path);
    return svg;
  }

  function burstWishlist(btn) {
    if (!motionOk || isThrottled()) return;

    var rect = btn.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;
    var count = 8;
    var colors = ['#DC143C', '#B76E79', '#FF69B4', '#FFB6C1'];

    for (var i = 0; i < count; i++) {
      (function (index) {
        var angle = (index / count) * Math.PI * 2;
        var dist = 28 + Math.random() * 18;
        var dx = Math.cos(angle) * dist;
        var dy = Math.sin(angle) * dist;
        var size = 10 + Math.random() * 6;
        var color = colors[Math.floor(Math.random() * colors.length)];
        var delay = Math.random() * 80;

        var particle = document.createElement('span');
        particle.appendChild(createHeartSVG());
        particle.style.cssText = [
          'position:fixed',
          'z-index:99999',
          'pointer-events:none',
          'width:' + size + 'px',
          'height:' + size + 'px',
          'color:' + color,
          'top:' + (cy - size / 2) + 'px',
          'left:' + (cx - size / 2) + 'px',
          'opacity:1',
          'transition:none',
          'will-change:transform,opacity',
        ].join(';');

        document.body.appendChild(particle);

        setTimeout(function () {
          particle.style.transition = 'transform 0.55s ease-out, opacity 0.55s ease-out';
          particle.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(0.4)';
          particle.style.opacity = '0';
        }, delay);

        setTimeout(function () {
          if (particle.parentNode) particle.parentNode.removeChild(particle);
        }, delay + 600);
      })(i);
    }
  }

  // -------------------------------------------------------------------------
  // Init
  // -------------------------------------------------------------------------

  function init() {
    // Cart fly-to: triggered after a successful add-to-cart click.
    document.addEventListener('click', function (e) {
      var buyBtn = e.target.closest('.holo__buy');
      if (!buyBtn) return;
      var card = buyBtn.closest('[data-product-id]');
      if (!card) return;

      // Delay slightly so WC can process the click first.
      setTimeout(function () {
        flyToCart(card);
      }, 120);
    });

    // Also respond to WC AJAX add-to-cart event for non-holo contexts.
    document.body.addEventListener('adding_to_cart', function (e) {
      var btn = e.detail && e.detail.$button;
      if (!btn) return;
      var card = btn[0] ? btn[0].closest('[data-product-id]') : null;
      if (card) flyToCart(card);
    });

    // Wishlist burst: on any wishlist button click.
    document.addEventListener('click', function (e) {
      var wishBtn = e.target.closest('.holo__wishlist');
      if (wishBtn) burstWishlist(wishBtn);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
