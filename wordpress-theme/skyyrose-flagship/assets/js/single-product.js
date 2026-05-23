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
       Editorial Size Chip → WC Variation Form Binding
       Wires the decorative .sr-ed__size buttons to the WooCommerce variations
       form's size <select>. Without this, customers see selectable-looking
       chips but cannot actually pick a size. (P0 fix, audit 2026-05-23)
       ════════════════════════════════════════ */
    var sizeChips = document.querySelectorAll('.sr-ed__sizes .sr-ed__size');
    if (sizeChips.length) {
        sizeChips.forEach(function(chip) {
            chip.addEventListener('click', function() {
                var size = chip.dataset.size;
                if (!size) return;
                var sizeSelect = document.querySelector('.variations_form select[name="attribute_pa_size"]')
                    || document.querySelector('.variations_form select[name="attribute_size"]');
                if (sizeSelect) {
                    var matched = false;
                    Array.prototype.forEach.call(sizeSelect.options, function(opt) {
                        if (opt.value && opt.value.toLowerCase() === size.toLowerCase()) {
                            sizeSelect.value = opt.value;
                            matched = true;
                        }
                    });
                    if (matched) {
                        $(sizeSelect).trigger('change');
                    }
                }
                sizeChips.forEach(function(c) {
                    c.classList.remove('is-selected');
                    c.setAttribute('aria-checked', 'false');
                });
                chip.classList.add('is-selected');
                chip.setAttribute('aria-checked', 'true');
            });
        });
        // Mirror WC variation form state back to chips when the form changes
        // (covers variation-image URL deep-links and reset).
        $(document).on('woocommerce_variation_has_changed', '.variations_form', function() {
            var sizeSelect = document.querySelector('.variations_form select[name="attribute_pa_size"]')
                || document.querySelector('.variations_form select[name="attribute_size"]');
            if (!sizeSelect || !sizeSelect.value) return;
            var current = sizeSelect.value.toLowerCase();
            sizeChips.forEach(function(c) {
                var isMatch = c.dataset.size && c.dataset.size.toLowerCase() === current;
                c.classList.toggle('is-selected', isMatch);
                c.setAttribute('aria-checked', isMatch ? 'true' : 'false');
            });
        });
    }

    /* ════════════════════════════════════════
       Product Details Accordion
       ════════════════════════════════════════ */
    document.querySelectorAll('[data-accordion]').forEach(function(acc) {
        var trigger = acc.querySelector('.sr-accordion-trigger');
        var content = acc.querySelector('.sr-accordion-content');
        var icon = acc.querySelector('.sr-accordion-icon');
        if (!trigger || !content) return;

        trigger.addEventListener('click', function() {
            var isOpen = content.classList.contains('sr-accordion-open');
            if (isOpen) {
                content.classList.remove('sr-accordion-open');
                content.style.maxHeight = '0';
                content.style.paddingBottom = '0';
                if (icon) icon.textContent = '+';
                trigger.setAttribute('aria-expanded', 'false');
            } else {
                content.classList.add('sr-accordion-open');
                content.style.maxHeight = content.scrollHeight + 'px';
                content.style.paddingBottom = '28px';
                if (icon) icon.textContent = '\u2212';
                trigger.setAttribute('aria-expanded', 'true');
            }
        });

        // Initialize already-open accordions (Description).
        if (content.classList.contains('sr-accordion-open')) {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.style.paddingBottom = '28px';
        }
    });

    /* ════════════════════════════════════════
       Sticky Add-to-Cart Bar
       ════════════════════════════════════════ */
    var stickyBar = document.getElementById('srStickyATC');
    var atcWrap = document.querySelector('.sr-atc-wrap');

    if (stickyBar && atcWrap) {
        var ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                requestAnimationFrame(function() {
                    var show = atcWrap.getBoundingClientRect().bottom < 0;
                    stickyBar.classList.toggle('visible', show);
                    stickyBar.setAttribute('aria-hidden', show ? 'false' : 'true');
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    // Sticky bar "Add to Bag" scrolls to the real form.
    var stickyBtn = document.querySelector('.sr-sticky-btn');
    if (stickyBtn) {
        stickyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var form = document.querySelector('.sr-atc-wrap');
            if (form) {
                form.scrollIntoView({ behavior: 'smooth', block: 'center' });
                var btn = form.querySelector('.single_add_to_cart_button');
                if (btn) {
                    btn.style.transform = 'scale(1.02)';
                    setTimeout(function() { btn.style.transform = ''; }, 800);
                }
            }
        });
    }

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
