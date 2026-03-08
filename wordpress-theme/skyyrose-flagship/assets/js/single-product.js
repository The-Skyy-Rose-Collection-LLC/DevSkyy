/**
 * SkyyRose Single Product Page JS — Elite Web Builder v4.0.0
 *
 * Gallery zoom, thumbnail switcher, WC variation image swap,
 * accordion, sticky ATC bar, AJAX cart feedback, scroll reveals.
 *
 * @package SkyyRose_Flagship
 * @since 4.0.0
 */
(function($) {
    'use strict';

    var galleryMain = document.querySelector('.sr-gallery-main');
    var mainImg = document.getElementById('srMainImg');
    var zoomEl = document.getElementById('srZoom');
    var thumbs = document.querySelectorAll('.sr-thumb');

    /* ════════════════════════════════════════
       Gallery Zoom (desktop only)
       ════════════════════════════════════════ */
    if (galleryMain && mainImg && zoomEl) {
        galleryMain.addEventListener('mousemove', function(e) {
            var rect = galleryMain.getBoundingClientRect();
            var x = ((e.clientX - rect.left) / rect.width) * 100;
            var y = ((e.clientY - rect.top) / rect.height) * 100;
            zoomEl.style.backgroundPosition = x + '% ' + y + '%';
        });
        galleryMain.addEventListener('mouseenter', function() {
            zoomEl.style.backgroundImage = 'url("' + (mainImg.src || mainImg.currentSrc) + '")';
        });
        // Disable zoom on touch devices.
        if ('ontouchstart' in window) {
            galleryMain.style.cursor = 'default';
            zoomEl.style.display = 'none';
        }
    }

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
                    if (zoomEl) zoomEl.style.backgroundImage = 'url("' + imgSrc + '")';
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
                if (zoomEl) zoomEl.style.backgroundImage = 'url("' + v.image.full_src + '")';
            }, 250);
        }
    });
    $(document).on('reset_image', '.variations_form', function() {
        var first = document.querySelector('.sr-thumb');
        if (first && mainImg) {
            mainImg.src = first.dataset.img;
            if (zoomEl) zoomEl.style.backgroundImage = 'url("' + first.dataset.img + '")';
            thumbs.forEach(function(t) { t.classList.remove('sr-thumb-active'); });
            first.classList.add('sr-thumb-active');
        }
    });

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
            btn.textContent = '\u2713 ADDED TO BAG';
            btn.style.opacity = '.7';
            setTimeout(function() {
                btn.textContent = orig;
                btn.style.opacity = '1';
            }, 2000);
        }
    });

    /* ════════════════════════════════════════
       Social Share Buttons
       ════════════════════════════════════════ */
    // Web Share API on mobile (native share sheet).
    var nativeBtn = document.querySelector('.sr-share-native');
    if (nativeBtn && navigator.share) {
        nativeBtn.style.display = '';
        nativeBtn.addEventListener('click', function() {
            navigator.share({
                title: nativeBtn.dataset.title,
                text: nativeBtn.dataset.text,
                url: nativeBtn.dataset.url
            }).catch(function() { /* user cancelled — noop */ });
        });
    }

    // Copy link button.
    var copyBtn = document.querySelector('.sr-share-copy');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            var url = copyBtn.dataset.url;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(function() {
                    copyBtn.classList.add('sr-share-copied');
                    setTimeout(function() { copyBtn.classList.remove('sr-share-copied'); }, 2000);
                });
            }
        });
    }

    /* ════════════════════════════════════════
       Recently Viewed Products (localStorage)
       ════════════════════════════════════════ */
    var RV_KEY = 'sr_recently_viewed';
    var RV_MAX = 8;

    // Track current product.
    var rvJson = document.getElementById('sr-rv-product');
    if (rvJson) {
        try {
            var current = JSON.parse(rvJson.textContent);
            var viewed = JSON.parse(localStorage.getItem(RV_KEY) || '[]');

            // Remove duplicate (same product ID).
            viewed = viewed.filter(function(p) { return p.id !== current.id; });

            // Prepend current product.
            viewed.unshift(current);

            // Cap at max.
            if (viewed.length > RV_MAX) viewed = viewed.slice(0, RV_MAX);

            localStorage.setItem(RV_KEY, JSON.stringify(viewed));
        } catch (e) { /* localStorage quota — noop */ }
    }

    // Render recently viewed carousel (exclude current product).
    var rvSection = document.querySelector('.sr-recently-viewed');
    var rvGrid = rvSection ? rvSection.querySelector('.sr-rv-grid') : null;

    if (rvSection && rvGrid) {
        try {
            var items = JSON.parse(localStorage.getItem(RV_KEY) || '[]');
            var currentId = rvJson ? JSON.parse(rvJson.textContent).id : null;

            // Filter out current product.
            var others = items.filter(function(p) { return p.id !== currentId; });

            if (others.length > 0) {
                var html = '';
                others.slice(0, 6).forEach(function(p) {
                    html += '<a href="' + p.url + '" class="sr-rv-card">' +
                        '<div class="sr-rv-img">' +
                            (p.image ?
                                '<img src="' + p.image + '" alt="' + p.name + '" loading="lazy">' :
                                '<span class="sr-rv-letter">' + p.name.charAt(0) + '</span>') +
                            '<span class="sr-rv-badge">' + p.badge + '</span>' +
                        '</div>' +
                        '<div class="sr-rv-body">' +
                            '<h3 class="sr-rv-name">' + p.name + '</h3>' +
                            '<span class="sr-rv-price">' + p.price + '</span>' +
                        '</div>' +
                    '</a>';
                });
                rvGrid.innerHTML = html;
                rvSection.style.display = '';
            }
        } catch (e) { /* parse error — section stays hidden */ }
    }

    /* ════════════════════════════════════════
       Scroll Reveal Animations
       ════════════════════════════════════════ */
    if ('IntersectionObserver' in window &&
        !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {

        var obs = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

        document.querySelectorAll(
            '.sr-related-card, .sr-accordion, .sr-cta-banner, .sr-related-head, .sr-rv-card, .sr-rv-head'
        ).forEach(function(el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'opacity .8s cubic-bezier(.16,1,.3,1), transform .8s cubic-bezier(.16,1,.3,1)';
            obs.observe(el);
        });
    }

})(jQuery);
