/**
 * SkyyRose Single Product Page JS — Elite Web Builder v4.0.0
 *
 * Thumbnail switcher, WC variation image swap, AJAX cart feedback.
 * Hero reveals (.rv-clip-left/.rv-clip-right) are served by the
 * global observer in premium-interactions.js — no parallel observer here.
 *
 * @package SkyyRose
 * @since 4.0.0
 */
(function($) {
    'use strict';

    var mainImg = document.getElementById('srMainImg');
    var thumbs = document.querySelectorAll('.sr-thumb');

    /* ════════════════════════════════════════
       Thumbnail Switcher
       ════════════════════════════════════════ */
    if (thumbs.length) {
        thumbs.forEach(function(thumb) {
            thumb.addEventListener('click', function() {
                var imgSrc = thumb.dataset.img;
                if (!imgSrc || !mainImg) return;
                mainImg.style.opacity = '0';
                setTimeout(function() {
                    mainImg.src = imgSrc;
                    mainImg.style.opacity = '1';
                }, 250);
                thumbs.forEach(function(t) { t.classList.remove('sr-thumb-active'); });
                thumb.classList.add('sr-thumb-active');
            });
        });
    }

    /* ════════════════════════════════════════
       WooCommerce Variation Image Swap
       ════════════════════════════════════════ */
    $(document).on('found_variation', '.variations_form', function(e, v) {
        if (v.image && v.image.full_src && mainImg) {
            mainImg.style.opacity = '0';
            setTimeout(function() {
                mainImg.src = v.image.full_src;
                mainImg.style.opacity = '1';
            }, 250);
        }
    });
    $(document).on('reset_image', '.variations_form', function() {
        var first = document.querySelector('.sr-thumb');
        if (first && mainImg) {
            mainImg.src = first.dataset.img;
            thumbs.forEach(function(t) { t.classList.remove('sr-thumb-active'); });
            first.classList.add('sr-thumb-active');
        }
    });

    /* ════════════════════════════════════════
       AJAX Add-to-Cart Feedback
       ════════════════════════════════════════ */
    $(document.body).on('added_to_cart', function() {
        var btn = document.querySelector('.sr-atc-wrap .single_add_to_cart_button');
        if (btn) {
            var orig = btn.textContent;
            btn.textContent = '✓ ADDED TO BAG';
            btn.style.opacity = '.7';
            setTimeout(function() {
                btn.textContent = orig;
                btn.style.opacity = '1';
            }, 2000);
        }
    });

})(jQuery);
