/**
 * SkyyRose Main JavaScript
 *
 * Navbar scroll, mobile menu, search, cart, newsletter
 */

(function() {
    'use strict';

    // ========================================
    // DOM Ready
    // ========================================

    document.addEventListener('DOMContentLoaded', function() {
        initNavbar();
        initMobileMenu();
        initSearch();
        initNewsletter();
        initAddToCart();
        initSmoothScroll();
        initFadeInAnimations();
    });

    // ========================================
    // Navbar Scroll Effect
    // ========================================

    function initNavbar() {
        var navbar = document.getElementById('navbar');
        if (!navbar) return;

        var lastScroll = 0;

        window.addEventListener('scroll', function() {
            var currentScroll = window.scrollY;

            // Add scrolled class
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        });
    }

    // ========================================
    // Mobile Menu
    // ========================================

    function initMobileMenu() {
        var toggleBtn = document.getElementById('mobileMenuToggle');
        var closeBtn = document.getElementById('mobileMenuClose');
        var menu = document.getElementById('mobileMenu');

        if (!toggleBtn || !menu) return;

        toggleBtn.addEventListener('click', function() {
            menu.classList.add('is-open');
            document.body.style.overflow = 'hidden';
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                menu.classList.remove('is-open');
                document.body.style.overflow = '';
            });
        }

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menu.classList.contains('is-open')) {
                menu.classList.remove('is-open');
                document.body.style.overflow = '';
            }
        });
    }

    // ========================================
    // Search Overlay
    // ========================================

    function initSearch() {
        var toggleBtn = document.getElementById('searchToggle');
        var closeBtn = document.getElementById('searchClose');
        var overlay = document.getElementById('searchOverlay');
        var searchInput = overlay ? overlay.querySelector('.search-input') : null;

        if (!toggleBtn || !overlay) return;

        toggleBtn.addEventListener('click', function() {
            overlay.classList.add('is-open');
            if (searchInput) {
                setTimeout(function() {
                    searchInput.focus();
                }, 100);
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                overlay.classList.remove('is-open');
            });
        }

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && overlay.classList.contains('is-open')) {
                overlay.classList.remove('is-open');
            }
        });
    }

    // ========================================
    // Newsletter Signup
    // ========================================

    function initNewsletter() {
        var form = document.getElementById('newsletterForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();

            var emailInput = form.querySelector('input[name="email"]');
            var submitBtn = form.querySelector('button[type="submit"]');

            if (!emailInput || !emailInput.value) return;

            // Disable form
            submitBtn.disabled = true;
            submitBtn.textContent = 'Subscribing...';

            // Send AJAX request
            var formData = new FormData();
            formData.append('action', 'skyyrose_newsletter');
            formData.append('email', emailInput.value);
            formData.append('nonce', window.skyyrose ? window.skyyrose.nonce : '');

            fetch(window.skyyrose ? window.skyyrose.ajax_url : '/wp-admin/admin-ajax.php', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    showToast(data.data.message || 'Welcome to the SkyyRose family!');
                    form.reset();
                } else {
                    showToast(data.data.message || 'Please try again.', 'error');
                }
            })
            .catch(function() {
                showToast('Something went wrong. Please try again.', 'error');
            })
            .finally(function() {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Subscribe';
            });
        });
    }

    // ========================================
    // Add to Cart
    // ========================================

    function initAddToCart() {
        document.addEventListener('click', function(e) {
            var addToCartBtn = e.target.closest('[data-add-to-cart]');
            if (!addToCartBtn) return;

            e.preventDefault();

            var productId = addToCartBtn.dataset.addToCart;
            var quantity = addToCartBtn.dataset.quantity || 1;

            if (!productId) return;

            // Disable button
            addToCartBtn.disabled = true;
            var originalText = addToCartBtn.textContent;
            addToCartBtn.textContent = 'Adding...';

            // Send AJAX request
            var formData = new FormData();
            formData.append('action', 'skyyrose_add_to_cart');
            formData.append('product_id', productId);
            formData.append('quantity', quantity);
            formData.append('nonce', window.skyyrose ? window.skyyrose.nonce : '');

            fetch(window.skyyrose ? window.skyyrose.ajax_url : '/wp-admin/admin-ajax.php', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    showToast(data.data.message || 'Added to cart!');
                    updateCartCount(data.data.cart_count);
                } else {
                    showToast(data.data.message || 'Could not add to cart.', 'error');
                }
            })
            .catch(function() {
                showToast('Something went wrong.', 'error');
            })
            .finally(function() {
                addToCartBtn.disabled = false;
                addToCartBtn.textContent = originalText;
            });
        });
    }

    // ========================================
    // Update Cart Count
    // ========================================

    function updateCartCount(count) {
        var cartCountEl = document.getElementById('cartCount');
        if (cartCountEl) {
            cartCountEl.textContent = count || 0;
        }
    }

    // ========================================
    // Toast Notification
    // ========================================

    function showToast(message, type) {
        var toast = document.getElementById('toast');
        if (!toast) {
            // Create toast safely using DOM methods
            toast = document.createElement('div');
            toast.className = 'toast';
            toast.id = 'toast';

            var toastMessage = document.createElement('span');
            toastMessage.className = 'toast-message';
            toast.appendChild(toastMessage);

            document.body.appendChild(toast);
        }

        var toastMessage = toast.querySelector('.toast-message');
        if (toastMessage) {
            toastMessage.textContent = message;
        } else {
            toast.textContent = message;
        }

        // Set type class
        toast.classList.remove('toast-error', 'toast-success');
        if (type === 'error') {
            toast.classList.add('toast-error');
        }

        // Show toast
        toast.classList.add('show');

        // Hide after 3 seconds
        setTimeout(function() {
            toast.classList.remove('show');
        }, 3000);
    }

    // ========================================
    // Smooth Scroll
    // ========================================

    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                var targetId = this.getAttribute('href');
                if (targetId === '#') return;

                var target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // ========================================
    // Fade In Animations
    // ========================================

    function initFadeInAnimations() {
        var fadeElements = document.querySelectorAll('.fade-in');
        if (!fadeElements.length) return;

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        fadeElements.forEach(function(el) {
            observer.observe(el);
        });
    }

    // ========================================
    // Expose functions globally
    // ========================================

    window.SkyyRose = {
        showToast: showToast,
        updateCartCount: updateCartCount
    };

})();
