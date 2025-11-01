/**
 * Skyy Rose Collection Theme JavaScript
 * Luxury Fashion Theme - Core Functionality
 */

(function($) {
    'use strict';

    // Theme object
    const SkyRoseTheme = {
        
        // Initialize all functions
        init: function() {
            this.mobileMenu();
            this.searchModal();
            this.backToTop();
            this.animations();
            this.newsletter();
            this.productGallery();
            this.stickyHeader();
            this.lazyLoading();
            this.wishlist();
            this.quickView();
        },

        // Mobile menu functionality
        mobileMenu: function() {
            const $menuToggle = $('.mobile-menu-toggle');
            const $navMenu = $('.nav-menu');
            
            $menuToggle.on('click', function() {
                $(this).toggleClass('active');
                $navMenu.toggleClass('active');
                $('body').toggleClass('menu-open');
            });

            // Close menu when clicking outside
            $(document).on('click', function(e) {
                if (!$(e.target).closest('.main-navigation').length) {
                    $menuToggle.removeClass('active');
                    $navMenu.removeClass('active');
                    $('body').removeClass('menu-open');
                }
            });
        },

        // Search modal functionality
        searchModal: function() {
            const $searchBtn = $('.header-search');
            const $searchModal = $('.search-modal');
            const $searchClose = $('.search-modal-close');
            
            $searchBtn.on('click', function() {
                $searchModal.addClass('active');
                $searchModal.find('.search-field').focus();
                $('body').addClass('modal-open');
            });

            $searchClose.on('click', function() {
                $searchModal.removeClass('active');
                $('body').removeClass('modal-open');
            });

            // Close on escape key
            $(document).on('keydown', function(e) {
                if (e.keyCode === 27 && $searchModal.hasClass('active')) {
                    $searchModal.removeClass('active');
                    $('body').removeClass('modal-open');
                }
            });

            // Live search functionality
            let searchTimeout;
            $('.search-field[data-live-search="true"]').on('input', function() {
                const $input = $(this);
                const query = $input.val();
                const minChars = parseInt($input.data('min-chars')) || 2;
                const delay = parseInt($input.data('search-delay')) || 300;
                
                clearTimeout(searchTimeout);
                
                if (query.length >= minChars) {
                    searchTimeout = setTimeout(() => {
                        SkyRoseTheme.performLiveSearch(query, $input);
                    }, delay);
                } else {
                    $input.siblings('.search-suggestions').hide();
                }
            });
        },

        // Live search AJAX
        performLiveSearch: function(query, $input) {
            const $suggestions = $input.siblings('.search-suggestions');
            const $liveResults = $suggestions.find('.live-results-list');
            
            // Show loading state
            $liveResults.html('<div class="search-loading">Searching...</div>');
            $suggestions.show();
            
            // Simulate AJAX search (replace with actual endpoint)
            setTimeout(() => {
                const mockResults = [
                    { title: 'Silk Evening Dress', price: '$299', image: '/path/to/image1.jpg' },
                    { title: 'Designer Handbag', price: '$199', image: '/path/to/image2.jpg' },
                    { title: 'Luxury Scarf', price: '$89', image: '/path/to/image3.jpg' }
                ];
                
                let resultsHtml = '';
                mockResults.forEach(result => {
                    resultsHtml += `
                        <div class="search-result-item">
                            <img src="${result.image}" alt="${result.title}" class="result-image">
                            <div class="result-content">
                                <h6 class="result-title">${result.title}</h6>
                                <span class="result-price">${result.price}</span>
                            </div>
                        </div>
                    `;
                });
                
                $liveResults.html(resultsHtml);
            }, 500);
        },

        // Back to top functionality
        backToTop: function() {
            const $backToTop = $('.back-to-top');
            
            $(window).on('scroll', function() {
                if ($(this).scrollTop() > 300) {
                    $backToTop.addClass('visible');
                } else {
                    $backToTop.removeClass('visible');
                }
            });

            $backToTop.on('click', function(e) {
                e.preventDefault();
                $('html, body').animate({
                    scrollTop: 0
                }, 800);
            });
        },

        // Sticky header
        stickyHeader: function() {
            const $header = $('.site-header');
            let lastScrollTop = 0;
            
            $(window).on('scroll', function() {
                const scrollTop = $(this).scrollTop();
                
                if (scrollTop > 100) {
                    $header.addClass('scrolled');
                } else {
                    $header.removeClass('scrolled');
                }
                
                lastScrollTop = scrollTop;
            });
        },

        // Scroll animations
        animations: function() {
            // Intersection Observer for scroll animations
            if ('IntersectionObserver' in window) {
                const animateElements = document.querySelectorAll('[data-animate]');
                
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const element = entry.target;
                            const animation = element.dataset.animate;
                            const delay = element.dataset.delay || 0;
                            
                            setTimeout(() => {
                                element.classList.add('animate-' + animation);
                            }, delay);
                            
                            observer.unobserve(element);
                        }
                    });
                }, {
                    threshold: 0.1,
                    rootMargin: '0px 0px -50px 0px'
                });
                
                animateElements.forEach(el => observer.observe(el));
            }
        },

        // Newsletter signup
        newsletter: function() {
            $('.newsletter-form').on('submit', function(e) {
                e.preventDefault();
                
                const $form = $(this);
                const $submitBtn = $form.find('button[type="submit"]');
                const $email = $form.find('input[type="email"]');
                const email = $email.val();
                
                // Basic email validation
                if (!email || !email.includes('@')) {
                    $form.find('.error-message').show();
                    return;
                }
                
                // Show loading state
                $submitBtn.addClass('loading');
                $form.find('.form-messages div').hide();
                
                // Simulate AJAX request (replace with actual endpoint)
                setTimeout(() => {
                    $submitBtn.removeClass('loading').addClass('success');
                    $form.find('.success-message').show();
                    $email.val('');
                    
                    // Reset after 3 seconds
                    setTimeout(() => {
                        $submitBtn.removeClass('success');
                        $form.find('.success-message').hide();
                    }, 3000);
                }, 1500);
            });
        },

        // Product gallery functionality
        productGallery: function() {
            // Product image zoom
            $('.woocommerce-product-gallery__image').on('mouseenter', function() {
                $(this).find('img').addClass('zoomed');
            }).on('mouseleave', function() {
                $(this).find('img').removeClass('zoomed');
            });

            // Product gallery thumbnails
            $('.flex-control-thumbs img').on('click', function() {
                $('.flex-control-thumbs img').removeClass('active');
                $(this).addClass('active');
            });
        },

        // Wishlist functionality
        wishlist: function() {
            $('.wishlist-btn').on('click', function(e) {
                e.preventDefault();
                
                const $btn = $(this);
                const productId = $btn.data('product-id');
                const action = $btn.data('wishlist-action');
                
                // Toggle wishlist state
                if (action === 'add') {
                    $btn.addClass('added').data('wishlist-action', 'remove');
                    $btn.find('.wishlist-text').text('Remove from Wishlist');
                    
                    // Add bounce animation
                    $btn.addClass('bounce');
                    setTimeout(() => $btn.removeClass('bounce'), 600);
                    
                } else {
                    $btn.removeClass('added').data('wishlist-action', 'add');
                    $btn.find('.wishlist-text').text('Add to Wishlist');
                }
                
                // Here you would make an AJAX call to save/remove from wishlist
                console.log(`Wishlist ${action} for product ${productId}`);
            });
        },

        // Quick view functionality
        quickView: function() {
            $('.quick-view-btn').on('click', function(e) {
                e.preventDefault();
                
                const productId = $(this).data('product-id');
                const $modal = $('#quick-view-modal');
                
                // Show modal with loading state
                $modal.addClass('active');
                $modal.find('.modal-content').html('<div class="loading">Loading...</div>');
                $('body').addClass('modal-open');
                
                // Simulate AJAX load (replace with actual endpoint)
                setTimeout(() => {
                    const mockContent = `
                        <div class="quick-view-content">
                            <h3>Product Name</h3>
                            <div class="product-price">$299</div>
                            <p>Product description goes here...</p>
                            <button class="add-to-cart-btn">Add to Cart</button>
                        </div>
                    `;
                    $modal.find('.modal-content').html(mockContent);
                }, 1000);
            });
            
            // Close modal
            $(document).on('click', '.modal-close, .modal-backdrop', function() {
                $('.modal').removeClass('active');
                $('body').removeClass('modal-open');
            });
        },

        // Lazy loading for images
        lazyLoading: function() {
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            imageObserver.unobserve(img);
                        }
                    });
                });

                document.querySelectorAll('img[data-src]').forEach(img => {
                    imageObserver.observe(img);
                });
            }
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        SkyRoseTheme.init();
    });

})(jQuery);
