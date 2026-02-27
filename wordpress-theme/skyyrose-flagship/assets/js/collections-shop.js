/**
 * Collections Shop — Filter tabs, product count, reveal animations.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.2
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {

    /* ---------------------------------------------------------------
     * Collection filter tabs
     * ------------------------------------------------------------- */
    var tabs     = document.querySelectorAll('.shop-tab');
    var products = document.querySelectorAll('.shop-product');
    var banners  = document.querySelectorAll('.shop-banner');
    var grids    = document.querySelectorAll('.shop-grid-wrap');
    var countEl  = document.getElementById('productCount');

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var col = this.dataset.collection;

        /* -- activate clicked tab --------------------------------- */
        tabs.forEach(function (t) {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        this.classList.add('active');
        this.setAttribute('aria-selected', 'true');

        /* -- show / hide products --------------------------------- */
        var visible = 0;
        products.forEach(function (p) {
          var show = col === 'all' || p.dataset.collection === col;
          p.classList.toggle('hidden', !show);
          if (show) visible++;
        });

        /* -- banner visibility ------------------------------------ */
        banners.forEach(function (b) {
          var section = b.dataset.section;
          b.style.display = (col === 'all' || section === col) ? '' : 'none';
        });

        /* -- grid wrapper visibility ------------------------------ */
        grids.forEach(function (g) {
          var gridProducts = g.querySelectorAll('.shop-product:not(.hidden)');
          g.style.display = gridProducts.length > 0 ? '' : 'none';
        });

        /* -- product count ---------------------------------------- */
        if (countEl) {
          countEl.textContent = visible;
        }
      });
    });

    /* ---------------------------------------------------------------
     * Reveal animations (IntersectionObserver)
     * ------------------------------------------------------------- */
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity   = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.shop-product, .shop-banner').forEach(function (el, i) {
      var delay = Math.min(i * 0.05, 0.4) + 's';

      el.style.opacity    = '0';
      el.style.transform  = 'translateY(30px)';
      el.style.transition = 'opacity .6s ' + delay + ' var(--ease-expo), '
                          + 'transform .6s ' + delay + ' var(--ease-expo)';

      observer.observe(el);
    });

  });
})();
