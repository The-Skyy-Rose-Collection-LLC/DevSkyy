/**
 * Personalization — Curated For You
 *
 * Part of the SkyyRose Experience Engine, Phase 4.
 *
 * Fetches personalized product recommendations from the Experience Engine
 * REST endpoint (/skyyrose/v1/personalization/{hash}) and injects a
 * "Curated For You" product grid after the main product grid on
 * collection pages and after the summary on single product pages.
 *
 * Requires SkyyCurated global (localized by personalization.php):
 *   { visitorHash, collection, restBase, restNonce, limit }
 *
 * Rendering flow:
 *   1. Find insertion point (after .product-grid__items or product summary)
 *   2. Build skeleton section and inject
 *   3. Fetch recommendations from REST
 *   4. Replace skeletons with product cards
 *
 * @module personalization
 * @since  6.4.0
 */
(function () {
  'use strict';

  var cfg = window.SkyyCurated;
  if (!cfg || !cfg.visitorHash) return;

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'className') {
        node.className = attrs[k];
      } else if (k === 'textContent') {
        node.textContent = attrs[k];
      } else {
        node.setAttribute(k, attrs[k]);
      }
    });
    (children || []).forEach(function (c) {
      if (c) node.appendChild(c);
    });
    return node;
  }

  // -------------------------------------------------------------------------
  // Build skeleton section
  // -------------------------------------------------------------------------

  function buildSection() {
    var skeletons = [];
    for (var i = 0; i < cfg.limit; i++) {
      skeletons.push(
        el('div', { className: 'skyy-curated__skeleton', 'aria-hidden': 'true' }, [
          el('div', { className: 'skyy-curated__skeleton-img' }),
          el('div', { className: 'skyy-curated__skeleton-text' }),
          el('div', {
            className: 'skyy-curated__skeleton-text skyy-curated__skeleton-text--short',
          }),
        ])
      );
    }

    var grid = el(
      'div',
      {
        className: 'skyy-curated__grid',
        id: 'skyy-curated-grid',
        role: 'list',
        'aria-live': 'polite',
        'aria-busy': 'true',
      },
      skeletons
    );

    var heading = el('h2', {
      className: 'skyy-curated__heading',
      id: 'skyy-curated-heading',
      textContent: 'Curated For You',
    });
    var sub = el('p', {
      className: 'skyy-curated__sub',
      textContent: 'Based on your style',
    });

    var header = el('div', { className: 'skyy-curated__header' }, [heading, sub]);
    var inner = el('div', { className: 'skyy-curated__inner' }, [header, grid]);
    var section = el(
      'section',
      {
        className: 'skyy-curated',
        'aria-labelledby': 'skyy-curated-heading',
        'data-module': 'personalization',
      },
      [inner]
    );

    return { section: section, grid: grid };
  }

  // -------------------------------------------------------------------------
  // Find insertion point
  // -------------------------------------------------------------------------

  function findInsertionPoint() {
    // After main product grid on collection/shop pages.
    var grid =
      document.querySelector('.product-grid__items') ||
      document.querySelector('.br-product-grid__items') ||
      document.querySelector('.col-product-grid') ||
      document.querySelector('ul.products');

    if (grid) {
      var parent = grid.parentElement;
      return { parent: parent, before: grid.nextSibling };
    }

    // After product summary on single product pages.
    var summary =
      document.querySelector('.woocommerce-product-details__short-description') ||
      document.querySelector('.entry-summary');
    if (summary) {
      return { parent: summary.parentElement, before: summary.nextSibling };
    }

    return null;
  }

  // -------------------------------------------------------------------------
  // Build product card from recommendation data
  // -------------------------------------------------------------------------

  function buildCard(product) {
    var img = el('img', {
      className: 'skyy-curated__card-img',
      src: product.image || '',
      alt: product.name || '',
      loading: 'lazy',
    });

    var imgWrap = el(
      'a',
      {
        className: 'skyy-curated__card-img-wrap',
        href: product.url || '#',
      },
      [img]
    );

    var coll = product.collection
      ? el('span', {
          className: 'skyy-curated__card-collection',
          textContent: product.collection.replace(/-/g, ' ').toUpperCase(),
        })
      : null;

    var name = el('h3', { className: 'skyy-curated__card-name' }, [
      el('a', { href: product.url || '#', textContent: product.name || '' }),
    ]);

    var price = el('p', {
      className: 'skyy-curated__card-price',
      textContent: product.price || '',
    });

    var cta = el('a', {
      className: 'skyy-curated__card-cta',
      href: product.url || '#',
      textContent: product.is_preorder ? 'Pre-Order' : 'View',
    });

    var info = el('div', { className: 'skyy-curated__card-info' }, [coll, name, price, cta]);

    return el(
      'article',
      {
        className: 'skyy-curated__card',
        role: 'listitem',
      },
      [imgWrap, info]
    );
  }

  // -------------------------------------------------------------------------
  // Fetch and render
  // -------------------------------------------------------------------------

  function fetchAndRender(gridEl) {
    var url = cfg.restBase + '/personalization/' + cfg.visitorHash;
    var params = new URLSearchParams({
      collection: cfg.collection || '',
      limit: cfg.limit || 4,
    });

    fetch(url + '?' + params.toString(), {
      method: 'GET',
      headers: { 'X-WP-Nonce': cfg.restNonce || '' },
      credentials: 'same-origin',
    })
      .then(function (res) {
        return res.ok ? res.json() : Promise.reject(res.status);
      })
      .then(function (data) {
        var products = data.products || data.recommendations || data || [];
        if (!Array.isArray(products) || products.length === 0) {
          // No recommendations — hide the section.
          var section = gridEl.closest('.skyy-curated');
          if (section) section.hidden = true;
          return;
        }

        gridEl.innerHTML = '';
        gridEl.setAttribute('aria-busy', 'false');

        products.forEach(function (product) {
          gridEl.appendChild(buildCard(product));
        });
      })
      .catch(function () {
        // Failed — hide section silently.
        var section = gridEl.closest('.skyy-curated');
        if (section) section.hidden = true;
      });
  }

  // -------------------------------------------------------------------------
  // Init
  // -------------------------------------------------------------------------

  function init() {
    var point = findInsertionPoint();
    if (!point) return;

    var built = buildSection();
    point.parent.insertBefore(built.section, point.before);

    fetchAndRender(built.grid);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
