/**
 * Smart Showcase — Quick-View Dialog
 *
 * Part of the SkyyRose Experience Engine, Phase 3.
 *
 * Opens a native <dialog> element with full product details when the user
 * clicks the "Quick View" button on any holo product card. All data is read
 * directly from the card's existing DOM — no AJAX or network round-trip.
 *
 * Features:
 *   - Front/back image toggle (if product has back image)
 *   - Size selection mirrored from the card's size pills
 *   - Add-to-cart via the card's existing add-to-cart URL
 *   - Focus trapping and Escape key close
 *   - Collection-themed accent color via CSS custom properties
 *
 * @module smart-showcase
 * @since  6.4.0
 */
(function () {
  'use strict';

  var DIALOG_ID = 'skyy-quickview-dialog';

  // -------------------------------------------------------------------------
  // Dialog shell (created once, reused)
  // -------------------------------------------------------------------------

  function buildShell() {
    var dialog = document.createElement('dialog');
    dialog.id = DIALOG_ID;
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'skyy-qv-title');
    dialog.innerHTML = [
      '<div class="skyy-qv__backdrop" aria-hidden="true"></div>',
      '<div class="skyy-qv__panel" role="document">',
      '  <button class="skyy-qv__close" aria-label="Close quick view">',
      '    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
      '  </button>',
      '  <div class="skyy-qv__gallery">',
      '    <img class="skyy-qv__img skyy-qv__img--active" id="skyy-qv-img-front" src="" alt="">',
      '    <img class="skyy-qv__img" id="skyy-qv-img-back" src="" alt="">',
      '    <div class="skyy-qv__img-toggle" id="skyy-qv-toggle" hidden>',
      '      <button class="skyy-qv__toggle-btn skyy-qv__toggle-btn--active" data-view="front">Front</button>',
      '      <button class="skyy-qv__toggle-btn" data-view="back">Back</button>',
      '    </div>',
      '  </div>',
      '  <div class="skyy-qv__info">',
      '    <span class="skyy-qv__collection" id="skyy-qv-collection"></span>',
      '    <h2 class="skyy-qv__title" id="skyy-qv-title"></h2>',
      '    <p class="skyy-qv__price" id="skyy-qv-price"></p>',
      '    <div class="skyy-qv__sizes" id="skyy-qv-sizes" role="radiogroup" aria-label="Select size"></div>',
      '    <button class="skyy-qv__buy" id="skyy-qv-buy" type="button"></button>',
      '    <a class="skyy-qv__full-link" id="skyy-qv-link" href="#">View full details</a>',
      '  </div>',
      '</div>',
    ].join('');
    document.body.appendChild(dialog);
    return dialog;
  }

  // -------------------------------------------------------------------------
  // Populate dialog from card DOM
  // -------------------------------------------------------------------------

  function populate(dialog, card) {
    var frontImg = card.querySelector('.holo__img--front');
    var backImg = card.querySelector('.holo__img--back');
    var priceEl = card.querySelector('.holo__price');
    var linkEl = card.querySelector('.holo__img-link');
    var buyBtn = card.querySelector('.holo__buy');
    var sizePills = card.querySelectorAll('.holo__size-pill');

    var name = card.dataset.name || '';
    var collection = card.dataset.collection || '';
    var productId = card.dataset.productId || '';

    // Gallery
    var qvFront = dialog.querySelector('#skyy-qv-img-front');
    var qvBack = dialog.querySelector('#skyy-qv-img-back');
    var toggle = dialog.querySelector('#skyy-qv-toggle');

    qvFront.src = frontImg ? frontImg.src : '';
    qvFront.alt = name;
    qvFront.classList.add('skyy-qv__img--active');

    if (backImg && backImg.src) {
      qvBack.src = backImg.src;
      qvBack.alt = name + ' (back)';
      qvBack.classList.remove('skyy-qv__img--active');
      toggle.hidden = false;
    } else {
      qvBack.src = '';
      toggle.hidden = true;
    }

    // Reset toggle buttons
    var toggleBtns = toggle.querySelectorAll('.skyy-qv__toggle-btn');
    toggleBtns[0] && toggleBtns[0].classList.add('skyy-qv__toggle-btn--active');
    toggleBtns[1] && toggleBtns[1].classList.remove('skyy-qv__toggle-btn--active');

    // Text
    dialog.querySelector('#skyy-qv-collection').textContent = collection
      ? collection.replace(/-/g, ' ').toUpperCase()
      : '';
    dialog.querySelector('#skyy-qv-title').textContent = name;
    dialog.querySelector('#skyy-qv-price').innerHTML = priceEl ? priceEl.innerHTML : '';

    // Full details link
    var fullLink = dialog.querySelector('#skyy-qv-link');
    fullLink.href = linkEl ? linkEl.href : '#';

    // Size pills — clone from card
    var sizesContainer = dialog.querySelector('#skyy-qv-sizes');
    sizesContainer.innerHTML = '';
    var selectedSize = '';
    sizePills.forEach(function (pill) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'skyy-qv__size-pill';
      btn.textContent = pill.textContent.trim();
      btn.dataset.size = pill.dataset.size;
      btn.setAttribute('role', 'radio');
      btn.setAttribute('aria-checked', 'false');
      btn.addEventListener('click', function () {
        sizesContainer.querySelectorAll('.skyy-qv__size-pill').forEach(function (b) {
          b.setAttribute('aria-checked', 'false');
          b.classList.remove('skyy-qv__size-pill--selected');
        });
        btn.setAttribute('aria-checked', 'true');
        btn.classList.add('skyy-qv__size-pill--selected');
        selectedSize = btn.dataset.size;
        dialog.querySelector('#skyy-qv-buy').disabled = false;
      });
      sizesContainer.appendChild(btn);
    });

    // Buy button
    var qvBuy = dialog.querySelector('#skyy-qv-buy');
    var isPreorder = card.classList.contains('holo--preorder');
    qvBuy.textContent = isPreorder ? 'Pre-Order Now' : 'Add to Bag';
    qvBuy.disabled = sizePills.length > 0; // disabled until size selected
    qvBuy.dataset.productId = productId;
    qvBuy.dataset.addToCartUrl = buyBtn ? buyBtn.dataset.addToCartUrl || '' : '';

    // Collection accent
    var accentVar = card.style.getPropertyValue('--holo-accent');
    dialog.style.setProperty('--qv-accent', accentVar || '#B76E79');
  }

  // -------------------------------------------------------------------------
  // Focus trap
  // -------------------------------------------------------------------------

  function getFocusable(dialog) {
    return Array.from(
      dialog.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    );
  }

  function trapFocus(dialog, e) {
    if (e.key !== 'Tab') return;
    var focusable = getFocusable(dialog);
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  // -------------------------------------------------------------------------
  // Add-to-cart from dialog
  // -------------------------------------------------------------------------

  function handleBuy(dialog) {
    var btn = dialog.querySelector('#skyy-qv-buy');
    var url = btn.dataset.addToCartUrl;
    var id = btn.dataset.productId;
    var size = dialog.querySelector('.skyy-qv__size-pill--selected');

    if (!url || !id) return;

    var params = new URLSearchParams({ quantity: 1, 'add-to-cart': id });
    if (size) params.set('size', size.dataset.size);

    btn.disabled = true;
    btn.textContent = 'Adding…';

    fetch(url + (url.includes('?') ? '&' : '?') + params.toString(), {
      method: 'GET',
      credentials: 'same-origin',
    })
      .then(function (res) {
        if (res.ok) {
          btn.textContent = 'Added!';
          // Dispatch WC add-to-cart event so fragments update.
          document.body.dispatchEvent(new CustomEvent('wc_fragment_refresh', { bubbles: true }));
          setTimeout(function () {
            dialog.close();
          }, 800);
        } else {
          btn.textContent = 'Try again';
          btn.disabled = false;
        }
      })
      .catch(function () {
        btn.textContent = 'Try again';
        btn.disabled = false;
      });
  }

  // -------------------------------------------------------------------------
  // Init
  // -------------------------------------------------------------------------

  function init() {
    var dialog = null;
    var previousFocus = null;
    var boundKeydown = null;

    function open(card) {
      if (!dialog) {
        dialog = buildShell();

        // Close on backdrop click
        dialog.querySelector('.skyy-qv__backdrop').addEventListener('click', function () {
          dialog.close();
        });

        // Close button
        dialog.querySelector('.skyy-qv__close').addEventListener('click', function () {
          dialog.close();
        });

        // Image toggle
        dialog.querySelector('#skyy-qv-toggle').addEventListener('click', function (e) {
          var btn = e.target.closest('.skyy-qv__toggle-btn');
          if (!btn) return;
          var view = btn.dataset.view;
          dialog.querySelectorAll('.skyy-qv__toggle-btn').forEach(function (b) {
            b.classList.toggle('skyy-qv__toggle-btn--active', b.dataset.view === view);
          });
          dialog
            .querySelector('#skyy-qv-img-front')
            .classList.toggle('skyy-qv__img--active', view === 'front');
          dialog
            .querySelector('#skyy-qv-img-back')
            .classList.toggle('skyy-qv__img--active', view === 'back');
        });

        // Buy
        dialog.querySelector('#skyy-qv-buy').addEventListener('click', function () {
          handleBuy(dialog);
        });

        // Close on Escape (native dialog does this, but also restore focus)
        dialog.addEventListener('close', function () {
          if (boundKeydown) {
            document.removeEventListener('keydown', boundKeydown);
            boundKeydown = null;
          }
          if (previousFocus) {
            previousFocus.focus();
            previousFocus = null;
          }
        });
      }

      previousFocus = document.activeElement;
      populate(dialog, card);
      dialog.showModal();

      // Move focus to close button
      var closeBtn = dialog.querySelector('.skyy-qv__close');
      closeBtn && closeBtn.focus();

      boundKeydown = function (e) {
        trapFocus(dialog, e);
      };
      document.addEventListener('keydown', boundKeydown);
    }

    // Delegate click on any quick-view trigger
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('.holo__quickview');
      if (!trigger) return;
      var card = trigger.closest('[data-product-id]');
      if (card) open(card);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
