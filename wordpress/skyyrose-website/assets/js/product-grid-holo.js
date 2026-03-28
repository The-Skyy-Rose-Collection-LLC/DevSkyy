/**
 * Holo Product Grid — Interactive Layer
 *
 * Ported from wordpress-theme/skyyrose-flagship/assets/js/product-card-holo.js
 * Magnetic tilt, holographic shimmer tracking, IntersectionObserver entrance,
 * wishlist toggle, filter buttons.
 *
 * No dependencies — vanilla JS. GSAP optional for stagger entrance.
 *
 * @package SkyyRose
 * @since   4.1.0
 */

(function () {
    'use strict';

    var MAX_TILT = 8;
    var TOUCH = matchMedia('(hover: none)').matches;
    var REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ──────────────────────────────────────────────
       1. SCROLL ENTRANCE — IntersectionObserver
       ────────────────────────────────────────────── */

    function initEntrance() {
        var cards = document.querySelectorAll('.holo:not(.holo--visible)');
        if (!cards.length) return;

        if (!('IntersectionObserver' in window)) {
            cards.forEach(function (c) { c.classList.add('holo--visible'); });
            return;
        }

        var staggerIndex = 0;
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.setProperty('--holo-delay', (staggerIndex * 80) + 'ms');
                    entry.target.classList.add('holo--visible');
                    staggerIndex++;
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        cards.forEach(function (card) { observer.observe(card); });
    }

    /* ──────────────────────────────────────────────
       2. MAGNETIC TILT + HOLOGRAPHIC TRACKING
       ────────────────────────────────────────────── */

    function initTilt() {
        if (TOUCH || REDUCED) return;

        document.querySelectorAll('.holo').forEach(function (card) {
            var body = card.querySelector('.holo__body');
            if (!body) return;

            card.addEventListener('mousemove', function (e) {
                var rect = card.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width;
                var y = (e.clientY - rect.top) / rect.height;

                var tiltX = ((y - 0.5) * -2 * MAX_TILT).toFixed(2);
                var tiltY = ((x - 0.5) * 2 * MAX_TILT).toFixed(2);
                var angle = (Math.atan2(y - 0.5, x - 0.5) * (180 / Math.PI) + 180).toFixed(1);

                body.style.setProperty('--tilt-x', tiltX + 'deg');
                body.style.setProperty('--tilt-y', tiltY + 'deg');
                body.style.setProperty('--holo-x', (x * 100).toFixed(1) + '%');
                body.style.setProperty('--holo-y', (y * 100).toFixed(1) + '%');
                body.style.setProperty('--holo-angle', angle + 'deg');
            });

            card.addEventListener('mouseleave', function () {
                body.style.setProperty('--tilt-x', '0deg');
                body.style.setProperty('--tilt-y', '0deg');
            });
        });
    }

    /* ──────────────────────────────────────────────
       3. WISHLIST TOGGLE (localStorage)
       ────────────────────────────────────────────── */

    var WISHLIST_KEY = 'skyyrose_wishlist';

    function getWishlist() {
        try {
            return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || [];
        } catch (e) {
            return [];
        }
    }

    function saveWishlist(list) {
        try {
            localStorage.setItem(WISHLIST_KEY, JSON.stringify(list));
        } catch (e) { /* quota exceeded */ }
    }

    function initWishlist() {
        var list = getWishlist();

        document.querySelectorAll('.holo__wishlist').forEach(function (btn) {
            var id = btn.getAttribute('data-wishlist-id');
            if (!id) return;

            if (list.indexOf(id) !== -1) {
                btn.setAttribute('aria-pressed', 'true');
            }

            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var current = getWishlist();
                var idx = current.indexOf(id);

                if (idx === -1) {
                    current = current.concat([id]);
                    btn.setAttribute('aria-pressed', 'true');
                } else {
                    current.splice(idx, 1);
                    btn.setAttribute('aria-pressed', 'false');
                }

                saveWishlist(current);
            });
        });
    }

    /* ──────────────────────────────────────────────
       4. FILTER BUTTONS
       ────────────────────────────────────────────── */

    function initFilters() {
        document.querySelectorAll('.product-grid__filters').forEach(function (filterBar) {
            var buttons = filterBar.querySelectorAll('.filter-btn');
            var grid = filterBar.closest('.product-grid');
            if (!grid) return;

            buttons.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var filter = btn.getAttribute('data-filter');

                    buttons.forEach(function (b) { b.classList.remove('active'); });
                    btn.classList.add('active');

                    grid.querySelectorAll('.holo').forEach(function (card) {
                        if (filter === 'all' || card.getAttribute('data-category') === filter) {
                            card.style.display = '';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                });
            });
        });
    }

    /* ──────────────────────────────────────────────
       5. INIT
       ────────────────────────────────────────────── */

    function init() {
        initEntrance();
        initTilt();
        initWishlist();
        initFilters();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
