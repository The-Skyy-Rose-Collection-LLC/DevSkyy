<?php
/**
 * Shop Scripts - SkyyRose Luxury Experience
 *
 * GSAP animations, add-to-cart, and quick view functionality.
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;
?>

<!-- GSAP CDN -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>

<!-- Quick View Modal -->
<div class="quickview-modal" id="quickviewModal" aria-hidden="true">
    <div class="quickview-modal__overlay" data-close-modal></div>
    <div class="quickview-modal__content" role="dialog" aria-modal="true">
        <button type="button" class="quickview-modal__close" data-close-modal aria-label="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
        <div class="quickview-modal__inner">
            <div class="quickview-modal__image">
                <img src="" alt="" id="quickviewImage">
            </div>
            <div class="quickview-modal__details">
                <h2 class="quickview-modal__title" id="quickviewTitle"></h2>
                <div class="quickview-modal__price" id="quickviewPrice"></div>
                <div class="quickview-modal__description" id="quickviewDescription"></div>
                <div class="quickview-modal__actions">
                    <a href="#" class="btn btn--primary" id="quickviewViewProduct">View Product</a>
                    <button type="button" class="btn btn--outline" id="quickviewAddToCart" data-product-id="">Add to Cart</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Cart Feedback Toast -->
<div class="cart-feedback" id="cartFeedback">
    <span id="cartFeedbackMessage">Added to cart</span>
</div>

<script>
(function() {
    'use strict';

    // ========================================
    // GSAP ANIMATIONS
    // ========================================

    gsap.registerPlugin(ScrollTrigger);

    // Fade up animations
    function initAnimations() {
        var fadeUpElements = document.querySelectorAll('.gsap-fade-up');

        fadeUpElements.forEach(function(el, index) {
            gsap.to(el, {
                opacity: 1,
                y: 0,
                duration: 0.8,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: el,
                    start: 'top 90%',
                    toggleActions: 'play none none none'
                },
                delay: el.dataset.index ? el.dataset.index * 0.1 : index * 0.05
            });
        });

        // Ambient orb parallax
        var orbs = document.querySelectorAll('.ambient-orb');
        orbs.forEach(function(orb, i) {
            gsap.to(orb, {
                y: function() { return (i + 1) * -100; },
                scrollTrigger: {
                    trigger: '.skyyrose-shop',
                    start: 'top top',
                    end: 'bottom bottom',
                    scrub: 1
                }
            });
        });
    }

    // ========================================
    // QUICK VIEW MODAL
    // ========================================

    var quickviewModal = document.getElementById('quickviewModal');
    var quickviewImage = document.getElementById('quickviewImage');
    var quickviewTitle = document.getElementById('quickviewTitle');
    var quickviewPrice = document.getElementById('quickviewPrice');
    var quickviewDescription = document.getElementById('quickviewDescription');
    var quickviewViewProduct = document.getElementById('quickviewViewProduct');
    var quickviewAddToCart = document.getElementById('quickviewAddToCart');

    function stripHtmlTags(html) {
        var tempDiv = document.createElement('div');
        tempDiv.textContent = html;
        var text = tempDiv.textContent;
        // Also handle &nbsp; and other entities
        text = text.replace(/&nbsp;/g, ' ');
        text = text.replace(/&amp;/g, '&');
        text = text.replace(/&lt;/g, '<');
        text = text.replace(/&gt;/g, '>');
        return text;
    }

    function openQuickView(productId, productUrl) {
        // Fetch product data via AJAX
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '<?php echo esc_url(rest_url('wc/v3/products/')); ?>' + productId + '?consumer_key=<?php echo esc_attr(defined("WOOCOMMERCE_KEY") ? WOOCOMMERCE_KEY : ""); ?>&consumer_secret=<?php echo esc_attr(defined("WOOCOMMERCE_SECRET") ? WOOCOMMERCE_SECRET : ""); ?>', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var product = JSON.parse(xhr.responseText);

                    // Set image
                    if (product.images && product.images.length > 0) {
                        quickviewImage.src = product.images[0].src;
                        quickviewImage.alt = product.name;
                    }

                    // Set content safely using textContent
                    quickviewTitle.textContent = product.name;
                    quickviewPrice.textContent = '$' + parseFloat(product.price).toFixed(2);

                    // Strip HTML from description safely
                    var rawDesc = product.short_description || product.description || '';
                    var cleanDesc = stripHtmlTags(rawDesc);
                    quickviewDescription.textContent = cleanDesc.substring(0, 200) + (cleanDesc.length > 200 ? '...' : '');

                    quickviewViewProduct.href = product.permalink;
                    quickviewAddToCart.dataset.productId = product.id;

                    // Show modal
                    quickviewModal.classList.add('is-active');
                    document.body.style.overflow = 'hidden';
                } else {
                    // Fallback: redirect to product page
                    window.location.href = productUrl;
                }
            }
        };
        xhr.send();
    }

    function closeQuickView() {
        quickviewModal.classList.remove('is-active');
        document.body.style.overflow = '';
    }

    // Close modal handlers
    document.querySelectorAll('[data-close-modal]').forEach(function(el) {
        el.addEventListener('click', closeQuickView);
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && quickviewModal.classList.contains('is-active')) {
            closeQuickView();
        }
    });

    // Quick view button click
    document.addEventListener('click', function(e) {
        var quickviewBtn = e.target.closest('[data-action="quickview"]');
        if (quickviewBtn) {
            e.preventDefault();
            e.stopPropagation();
            var productId = quickviewBtn.dataset.productId;
            var productUrl = quickviewBtn.dataset.productUrl;
            openQuickView(productId, productUrl);
        }
    });

    // ========================================
    // ADD TO CART
    // ========================================

    var cartFeedback = document.getElementById('cartFeedback');
    var cartFeedbackMessage = document.getElementById('cartFeedbackMessage');

    function showCartFeedback(message) {
        cartFeedbackMessage.textContent = message;
        cartFeedback.classList.add('is-visible');
        setTimeout(function() {
            cartFeedback.classList.remove('is-visible');
        }, 3000);
    }

    function createSpinnerIcon() {
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '20');
        svg.setAttribute('height', '20');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        svg.classList.add('spin');

        var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '12');
        circle.setAttribute('cy', '12');
        circle.setAttribute('r', '10');
        svg.appendChild(circle);

        var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M12 6v6l4 2');
        svg.appendChild(path);

        return svg;
    }

    function addToCart(productId, button) {
        if (!productId) return;

        // Save original content
        var originalChildren = [];
        while (button.firstChild) {
            originalChildren.push(button.removeChild(button.firstChild));
        }

        // Disable button and show spinner
        button.disabled = true;
        button.appendChild(createSpinnerIcon());

        // Add spinning animation
        var style = document.createElement('style');
        style.textContent = '@keyframes spin { to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }';
        document.head.appendChild(style);

        // WooCommerce AJAX add to cart
        var formData = new FormData();
        formData.append('action', 'woocommerce_ajax_add_to_cart');
        formData.append('product_id', productId);
        formData.append('quantity', 1);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '<?php echo esc_url(admin_url("admin-ajax.php")); ?>', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                button.disabled = false;

                // Clear spinner and restore original content
                while (button.firstChild) {
                    button.removeChild(button.firstChild);
                }
                originalChildren.forEach(function(child) {
                    button.appendChild(child);
                });

                style.remove();

                if (xhr.status === 200) {
                    var response;
                    try {
                        response = JSON.parse(xhr.responseText);
                    } catch (e) {
                        response = { success: true };
                    }

                    if (response.success !== false) {
                        showCartFeedback('Added to cart!');

                        // Update cart count in header if exists
                        var cartCount = document.querySelector('.cart-count, .cart-contents-count');
                        if (cartCount) {
                            var count = parseInt(cartCount.textContent) || 0;
                            cartCount.textContent = count + 1;
                        }

                        // Trigger WooCommerce events
                        document.body.dispatchEvent(new CustomEvent('added_to_cart', {
                            detail: { product_id: productId }
                        }));
                    } else {
                        showCartFeedback('Could not add to cart');
                    }
                } else {
                    showCartFeedback('Could not add to cart');
                }
            }
        };
        xhr.send(formData);
    }

    // Add to cart button click
    document.addEventListener('click', function(e) {
        var addToCartBtn = e.target.closest('[data-action="addtocart"]');
        if (addToCartBtn) {
            e.preventDefault();
            e.stopPropagation();
            var productId = addToCartBtn.dataset.productId;
            addToCart(productId, addToCartBtn);
        }
    });

    // Quick view add to cart
    if (quickviewAddToCart) {
        quickviewAddToCart.addEventListener('click', function() {
            var productId = this.dataset.productId;
            addToCart(productId, this);
        });
    }

    // ========================================
    // LOAD MORE (AJAX Pagination)
    // ========================================

    var loadMoreBtn = document.getElementById('loadMoreProducts');
    var productsGrid = document.querySelector('.products-grid');
    var currentPage = 1;

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            currentPage++;
            var collection = document.querySelector('.skyyrose-shop').dataset.collection;

            loadMoreBtn.disabled = true;
            var btnText = loadMoreBtn.querySelector('span');
            var originalText = btnText.textContent;
            btnText.textContent = 'Loading...';

            var xhr = new XMLHttpRequest();
            var url = '<?php echo esc_url(admin_url("admin-ajax.php")); ?>?action=skyyrose_load_more_products&page=' + currentPage + '&collection=' + encodeURIComponent(collection);

            xhr.open('GET', url, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    loadMoreBtn.disabled = false;
                    btnText.textContent = originalText;

                    if (xhr.status === 200) {
                        var response;
                        try {
                            response = JSON.parse(xhr.responseText);
                        } catch (e) {
                            return;
                        }

                        if (response.success && response.data.products) {
                            // Create product cards from JSON data (no HTML injection)
                            response.data.products.forEach(function(product, index) {
                                var card = createProductCard(product, currentPage * 12 + index);
                                productsGrid.appendChild(card);

                                // Animate new product
                                gsap.from(card, {
                                    opacity: 0,
                                    y: 40,
                                    duration: 0.6,
                                    ease: 'power3.out',
                                    delay: index * 0.1
                                });
                            });

                            // Hide load more if no more pages
                            if (!response.data.has_more) {
                                loadMoreBtn.parentElement.style.display = 'none';
                            }
                        }
                    }
                }
            };
            xhr.send();
        });
    }

    function createProductCard(product, index) {
        var article = document.createElement('article');
        article.className = 'product-card gsap-fade-up';
        article.dataset.index = index;
        article.dataset.collection = product.collection || 'signature';

        var link = document.createElement('a');
        link.href = product.permalink;
        link.className = 'product-card__link';

        // Image wrapper
        var imageWrapper = document.createElement('div');
        imageWrapper.className = 'product-card__image-wrapper';

        var imageDiv = document.createElement('div');
        imageDiv.className = 'product-card__image';

        if (product.image) {
            var img = document.createElement('img');
            img.src = product.image;
            img.alt = product.name;
            img.className = 'product-card__img product-card__img--primary';
            img.loading = 'lazy';
            imageDiv.appendChild(img);
        }

        imageWrapper.appendChild(imageDiv);

        // Badge
        var badge = document.createElement('span');
        badge.className = 'product-card__badge';
        badge.style.cssText = '--badge-color: ' + (product.badge_color || '#B76E79');
        badge.textContent = product.collection_name || 'Signature';
        imageWrapper.appendChild(badge);

        link.appendChild(imageWrapper);

        // Product info
        var info = document.createElement('div');
        info.className = 'product-card__info';

        var title = document.createElement('h3');
        title.className = 'product-card__title';
        title.textContent = product.name;
        info.appendChild(title);

        var price = document.createElement('div');
        price.className = 'product-card__price';
        price.textContent = '$' + parseFloat(product.price).toFixed(2);
        info.appendChild(price);

        link.appendChild(info);
        article.appendChild(link);

        return article;
    }

    // ========================================
    // COLLECTION FILTER (Smooth Transition)
    // ========================================

    document.querySelectorAll('.filter-tab').forEach(function(tab) {
        tab.addEventListener('click', function(e) {
            // Let the link work normally, but add a fade transition
            var products = document.querySelectorAll('.product-card');
            gsap.to(products, {
                opacity: 0,
                y: 20,
                stagger: 0.02,
                duration: 0.3,
                ease: 'power2.in'
            });
        });
    });

    // ========================================
    // INITIALIZE
    // ========================================

    document.addEventListener('DOMContentLoaded', function() {
        initAnimations();
    });

    // Reinit on AJAX load
    if (typeof jQuery !== 'undefined') {
        jQuery(document.body).on('post-load', initAnimations);
    }

})();
</script>
