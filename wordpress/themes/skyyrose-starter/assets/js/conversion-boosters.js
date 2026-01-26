/**
 * SkyyRose Conversion Boosters
 * Proven e-commerce features to drive sales
 * Uses safe DOM manipulation methods
 *
 * @package SkyyRose
 */

(function() {
    'use strict';

    // Safe element creation helper
    function createElement(tag, attributes, children) {
        const el = document.createElement(tag);
        if (attributes) {
            Object.keys(attributes).forEach(key => {
                if (key === 'className') {
                    el.className = attributes[key];
                } else if (key === 'textContent') {
                    el.textContent = attributes[key];
                } else if (key.startsWith('data-')) {
                    el.setAttribute(key, attributes[key]);
                } else {
                    el[key] = attributes[key];
                }
            });
        }
        if (children) {
            children.forEach(child => {
                if (typeof child === 'string') {
                    el.appendChild(document.createTextNode(child));
                } else if (child) {
                    el.appendChild(child);
                }
            });
        }
        return el;
    }

    window.SkyyRoseConversion = {

        // ============================================
        // 1. URGENCY & SCARCITY
        // ============================================

        initUrgency: function() {
            const viewerElements = document.querySelectorAll('.live-viewers');
            viewerElements.forEach(el => {
                const baseViewers = parseInt(el.dataset.base) || Math.floor(Math.random() * 15) + 5;
                let currentViewers = baseViewers;
                const countSpan = el.querySelector('.viewer-count');

                const updateViewers = () => {
                    const change = Math.random() > 0.5 ? 1 : -1;
                    currentViewers = Math.max(3, Math.min(baseViewers + 10, currentViewers + change));
                    if (countSpan) countSpan.textContent = currentViewers;
                };

                setInterval(updateViewers, Math.random() * 5000 + 3000);
            });

            this.initRecentPurchases();
            this.initStockUrgency();
        },

        initRecentPurchases: function() {
            const names = ['Sarah', 'Michael', 'Emma', 'James', 'Olivia', 'David', 'Sophia', 'Chris'];
            const cities = ['Los Angeles', 'New York', 'Miami', 'Chicago', 'Oakland', 'Atlanta', 'Houston'];
            const products = document.querySelectorAll('.product-title');
            const productNames = Array.from(products).map(p => p.textContent).slice(0, 5);

            if (productNames.length === 0) return;

            const showNotification = () => {
                const name = names[Math.floor(Math.random() * names.length)];
                const city = cities[Math.floor(Math.random() * cities.length)];
                const product = productNames[Math.floor(Math.random() * productNames.length)];
                const time = Math.floor(Math.random() * 30) + 1;

                const notification = createElement('div', { className: 'purchase-notification' }, [
                    createElement('div', { className: 'notification-icon', textContent: '🛒' }),
                    createElement('div', { className: 'notification-content' }, [
                        createElement('strong', { textContent: name }),
                        document.createTextNode(' from ' + city),
                        createElement('br'),
                        createElement('span', {}, [
                            document.createTextNode('purchased '),
                            createElement('em', { textContent: product })
                        ]),
                        createElement('br'),
                        createElement('small', { textContent: time + ' minutes ago' })
                    ]),
                    createElement('button', { className: 'notification-close', 'aria-label': 'Close', textContent: '×' })
                ]);

                document.body.appendChild(notification);
                setTimeout(() => notification.classList.add('show'), 100);
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                }, 5000);

                notification.querySelector('.notification-close').addEventListener('click', () => {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                });
            };

            setTimeout(showNotification, 15000);
            setInterval(() => {
                if (Math.random() > 0.6) showNotification();
            }, 45000);
        },

        initStockUrgency: function() {
            document.querySelectorAll('.stock-urgency').forEach(el => {
                const stock = parseInt(el.dataset.stock) || 0;
                if (stock > 0 && stock <= 10) {
                    el.classList.add('low-stock');
                    el.textContent = '';
                    el.appendChild(createElement('span', { className: 'urgency-icon', textContent: '🔥' }));
                    el.appendChild(document.createTextNode(' Only ' + stock + ' left in stock!'));
                }
            });
        },

        // ============================================
        // 2. STICKY ADD TO CART
        // ============================================

        initStickyCart: function() {
            const addToCartForm = document.querySelector('.single_add_to_cart_button');
            if (!addToCartForm) return;

            const productTitle = document.querySelector('.product_title')?.textContent || 'Product';
            const productPrice = document.querySelector('.price .woocommerce-Price-amount')?.textContent || '';
            const productImage = document.querySelector('.woocommerce-product-gallery__image img')?.src || '';

            const stickyBar = createElement('div', { className: 'sticky-add-to-cart' }, [
                createElement('div', { className: 'sticky-cart-container' }, [
                    createElement('div', { className: 'sticky-cart-product' }, [
                        productImage ? Object.assign(createElement('img', { className: 'sticky-cart-image', alt: productTitle }), { src: productImage }) : null,
                        createElement('div', { className: 'sticky-cart-info' }, [
                            createElement('span', { className: 'sticky-cart-title', textContent: productTitle }),
                            createElement('span', { className: 'sticky-cart-price', textContent: productPrice })
                        ])
                    ]),
                    createElement('button', { className: 'sticky-cart-button btn btn-primary', textContent: 'Add to Cart' })
                ])
            ]);

            document.body.appendChild(stickyBar);

            const originalButton = document.querySelector('.single_add_to_cart_button');
            const stickyButton = stickyBar.querySelector('.sticky-cart-button');

            const toggleSticky = () => {
                const buttonRect = originalButton?.getBoundingClientRect();
                if (buttonRect && buttonRect.bottom < 0) {
                    stickyBar.classList.add('visible');
                } else {
                    stickyBar.classList.remove('visible');
                }
            };

            window.addEventListener('scroll', toggleSticky, { passive: true });
            stickyButton.addEventListener('click', () => originalButton?.click());
        },

        // ============================================
        // 3. QUICK VIEW MODAL
        // ============================================

        initQuickView: function() {
            document.querySelectorAll('.product-card, .woocommerce-loop-product').forEach(card => {
                const quickViewBtn = createElement('button', { className: 'quick-view-btn', 'aria-label': 'Quick view product', textContent: ' Quick View' });
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('width', '20');
                svg.setAttribute('height', '20');
                svg.setAttribute('viewBox', '0 0 24 24');
                svg.setAttribute('fill', 'none');
                svg.setAttribute('stroke', 'currentColor');
                svg.setAttribute('stroke-width', '2');
                const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path1.setAttribute('d', 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z');
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', '12');
                circle.setAttribute('cy', '12');
                circle.setAttribute('r', '3');
                svg.appendChild(path1);
                svg.appendChild(circle);
                quickViewBtn.insertBefore(svg, quickViewBtn.firstChild);

                const imageWrapper = card.querySelector('.product-image, .woocommerce-loop-product__link');
                if (imageWrapper) {
                    imageWrapper.style.position = 'relative';
                    imageWrapper.appendChild(quickViewBtn);
                }

                quickViewBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const productUrl = card.querySelector('a')?.href;
                    if (productUrl) this.showQuickView(productUrl);
                });
            });
        },

        showQuickView: function(url) {
            const modal = createElement('div', { className: 'quick-view-modal' }, [
                createElement('div', { className: 'quick-view-overlay' }),
                createElement('div', { className: 'quick-view-content' }, [
                    createElement('button', { className: 'quick-view-close', 'aria-label': 'Close', textContent: '×' }),
                    createElement('div', { className: 'quick-view-loading' }, [
                        createElement('div', { className: 'loading-spinner' })
                    ]),
                    createElement('div', { className: 'quick-view-body' })
                ])
            ]);

            document.body.appendChild(modal);
            document.body.classList.add('modal-open');
            setTimeout(() => modal.classList.add('show'), 10);

            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const gallery = doc.querySelector('.woocommerce-product-gallery');
                    const summary = doc.querySelector('.summary, .product-summary');
                    const body = modal.querySelector('.quick-view-body');

                    body.textContent = '';
                    const galleryDiv = createElement('div', { className: 'quick-view-gallery' });
                    const summaryDiv = createElement('div', { className: 'quick-view-summary' });

                    if (gallery) galleryDiv.appendChild(gallery.cloneNode(true));
                    if (summary) summaryDiv.appendChild(summary.cloneNode(true));

                    body.appendChild(galleryDiv);
                    body.appendChild(summaryDiv);
                    modal.querySelector('.quick-view-loading').style.display = 'none';
                })
                .catch(() => {
                    const loading = modal.querySelector('.quick-view-loading');
                    loading.textContent = 'Could not load product. ';
                    const link = createElement('a', { href: url, textContent: 'View full page' });
                    loading.appendChild(link);
                });

            const closeModal = () => {
                modal.classList.remove('show');
                document.body.classList.remove('modal-open');
                setTimeout(() => modal.remove(), 300);
            };

            modal.querySelector('.quick-view-close').addEventListener('click', closeModal);
            modal.querySelector('.quick-view-overlay').addEventListener('click', closeModal);
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') closeModal();
            }, { once: true });
        },

        // ============================================
        // 4. EXIT INTENT POPUP
        // ============================================

        initExitIntent: function() {
            if (sessionStorage.getItem('skyyrose_exit_shown')) return;

            let triggered = false;

            const showExitPopup = () => {
                if (triggered) return;
                triggered = true;
                sessionStorage.setItem('skyyrose_exit_shown', 'true');

                const form = createElement('form', { className: 'exit-popup-form', id: 'exitIntentForm' }, [
                    createElement('input', { type: 'email', placeholder: 'Enter your email', required: true }),
                    createElement('button', { type: 'submit', className: 'btn btn-primary', textContent: 'Claim My 15% Off' })
                ]);

                const popup = createElement('div', { className: 'exit-intent-popup' }, [
                    createElement('div', { className: 'exit-popup-overlay' }),
                    createElement('div', { className: 'exit-popup-content' }, [
                        createElement('button', { className: 'exit-popup-close', 'aria-label': 'Close', textContent: '×' }),
                        createElement('div', { className: 'exit-popup-body' }, [
                            createElement('span', { className: 'exit-popup-label', textContent: 'Wait! Before you go...' }),
                            createElement('h2', { textContent: 'Get 15% Off Your First Order' }),
                            createElement('p', { textContent: 'Join the SkyyRose family and receive exclusive access to new collections, styling tips, and special offers.' }),
                            form,
                            createElement('p', { className: 'exit-popup-note', textContent: 'No spam, ever. Unsubscribe anytime.' })
                        ])
                    ])
                ]);

                document.body.appendChild(popup);
                setTimeout(() => popup.classList.add('show'), 10);

                const closePopup = () => {
                    popup.classList.remove('show');
                    setTimeout(() => popup.remove(), 300);
                };

                popup.querySelector('.exit-popup-close').addEventListener('click', closePopup);
                popup.querySelector('.exit-popup-overlay').addEventListener('click', closePopup);

                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const email = form.querySelector('input[type="email"]').value;

                    if (window.skyyrose?.ajax_url) {
                        fetch(window.skyyrose.ajax_url, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: 'action=skyyrose_newsletter&email=' + encodeURIComponent(email) + '&nonce=' + window.skyyrose.nonce
                        });
                    }

                    const body = popup.querySelector('.exit-popup-body');
                    body.textContent = '';
                    body.appendChild(createElement('div', { className: 'exit-popup-success' }, [
                        createElement('span', { className: 'success-icon', textContent: '✓' }),
                        createElement('h3', { textContent: "You're In!" }),
                        createElement('p', { textContent: 'Check your email for your 15% discount code.' }),
                        createElement('p', { className: 'discount-code' }, [
                            document.createTextNode('Use code: '),
                            createElement('strong', { textContent: 'WELCOME15' })
                        ])
                    ]));

                    setTimeout(closePopup, 4000);
                });
            };

            document.addEventListener('mouseout', (e) => {
                if (e.clientY <= 0 && !triggered) showExitPopup();
            });

            let lastScrollY = window.scrollY;
            let scrollUpCount = 0;

            window.addEventListener('scroll', () => {
                if (window.scrollY < lastScrollY - 100) {
                    scrollUpCount++;
                    if (scrollUpCount >= 3 && window.scrollY < 200) showExitPopup();
                } else {
                    scrollUpCount = 0;
                }
                lastScrollY = window.scrollY;
            }, { passive: true });
        },

        // ============================================
        // 5. SIZE GUIDE MODAL
        // ============================================

        initSizeGuide: function() {
            const sizeSelects = document.querySelectorAll('.variations select[id*="size"], .size-options');
            if (sizeSelects.length === 0) return;

            sizeSelects.forEach(select => {
                const guideLink = createElement('button', { className: 'size-guide-link', type: 'button', textContent: '📏 Size Guide' });
                select.parentNode.insertBefore(guideLink, select.nextSibling);
                guideLink.addEventListener('click', () => this.showSizeGuide());
            });
        },

        showSizeGuide: function() {
            const createTable = (headers, rows) => {
                const table = createElement('table');
                const thead = createElement('thead');
                const headerRow = createElement('tr');
                headers.forEach(h => headerRow.appendChild(createElement('th', { textContent: h })));
                thead.appendChild(headerRow);
                table.appendChild(thead);

                const tbody = createElement('tbody');
                rows.forEach(row => {
                    const tr = createElement('tr');
                    row.forEach(cell => tr.appendChild(createElement('td', { textContent: cell })));
                    tbody.appendChild(tr);
                });
                table.appendChild(tbody);
                return table;
            };

            const topsTable = createTable(
                ['Size', 'US', 'Bust', 'Waist', 'Hips'],
                [
                    ['XS', '0-2', '31-32"', '23-24"', '33-34"'],
                    ['S', '4-6', '33-34"', '25-26"', '35-36"'],
                    ['M', '8-10', '35-36"', '27-28"', '37-38"'],
                    ['L', '12-14', '37-39"', '29-31"', '39-41"'],
                    ['XL', '16-18', '40-42"', '32-34"', '42-44"']
                ]
            );

            const bottomsTable = createTable(
                ['Size', 'US', 'Waist', 'Hips', 'Inseam'],
                [
                    ['XS', '0-2', '23-24"', '33-34"', '30"'],
                    ['S', '4-6', '25-26"', '35-36"', '30"'],
                    ['M', '8-10', '27-28"', '37-38"', '31"'],
                    ['L', '12-14', '29-31"', '39-41"', '31"'],
                    ['XL', '16-18', '32-34"', '42-44"', '32"']
                ]
            );

            const dressesTable = createTable(
                ['Size', 'US', 'Bust', 'Waist', 'Length'],
                [
                    ['XS', '0-2', '31-32"', '23-24"', '35"'],
                    ['S', '4-6', '33-34"', '25-26"', '36"'],
                    ['M', '8-10', '35-36"', '27-28"', '37"'],
                    ['L', '12-14', '37-39"', '29-31"', '38"'],
                    ['XL', '16-18', '40-42"', '32-34"', '39"']
                ]
            );

            const topsContent = createElement('div', { className: 'size-guide-table', 'data-content': 'tops' }, [topsTable]);
            const bottomsContent = createElement('div', { className: 'size-guide-table', 'data-content': 'bottoms' }, [bottomsTable]);
            const dressesContent = createElement('div', { className: 'size-guide-table', 'data-content': 'dresses' }, [dressesTable]);
            bottomsContent.style.display = 'none';
            dressesContent.style.display = 'none';

            const modal = createElement('div', { className: 'size-guide-modal' }, [
                createElement('div', { className: 'size-guide-overlay' }),
                createElement('div', { className: 'size-guide-content' }, [
                    createElement('button', { className: 'size-guide-close', 'aria-label': 'Close', textContent: '×' }),
                    createElement('h2', { textContent: 'Size Guide' }),
                    createElement('div', { className: 'size-guide-tabs' }, [
                        createElement('button', { className: 'size-tab active', 'data-tab': 'tops', textContent: 'Tops' }),
                        createElement('button', { className: 'size-tab', 'data-tab': 'bottoms', textContent: 'Bottoms' }),
                        createElement('button', { className: 'size-tab', 'data-tab': 'dresses', textContent: 'Dresses' })
                    ]),
                    topsContent,
                    bottomsContent,
                    dressesContent,
                    createElement('div', { className: 'size-guide-tip' }, [
                        createElement('strong', { textContent: '💡 Tip: ' }),
                        document.createTextNode('When in doubt, size up for a relaxed fit. Our pieces are designed for comfort and movement.')
                    ])
                ])
            ]);

            document.body.appendChild(modal);
            setTimeout(() => modal.classList.add('show'), 10);

            modal.querySelectorAll('.size-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    modal.querySelectorAll('.size-tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    modal.querySelectorAll('.size-guide-table').forEach(t => t.style.display = 'none');
                    modal.querySelector('.size-guide-table[data-content="' + tab.dataset.tab + '"]').style.display = 'block';
                });
            });

            const closeModal = () => {
                modal.classList.remove('show');
                setTimeout(() => modal.remove(), 300);
            };

            modal.querySelector('.size-guide-close').addEventListener('click', closeModal);
            modal.querySelector('.size-guide-overlay').addEventListener('click', closeModal);
        },

        // ============================================
        // 6. TRUST BADGES
        // ============================================

        initTrustBadges: function() {
            const addToCartBtn = document.querySelector('.single_add_to_cart_button');
            if (!addToCartBtn) return;

            const badges = [
                { icon: '🔒', text: 'Secure Checkout' },
                { icon: '🚚', text: 'Free Shipping $150+' },
                { icon: '↩️', text: '30-Day Returns' },
                { icon: '💳', text: 'Pay in 4 with Klarna' }
            ];

            const trustBadges = createElement('div', { className: 'trust-badges' },
                badges.map(b => createElement('div', { className: 'trust-badge' }, [
                    createElement('span', { className: 'badge-icon', textContent: b.icon }),
                    createElement('span', { textContent: b.text })
                ]))
            );

            addToCartBtn.parentNode.insertBefore(trustBadges, addToCartBtn.nextSibling);
        },

        // ============================================
        // 7. WISHLIST
        // ============================================

        initWishlist: function() {
            const wishlist = JSON.parse(localStorage.getItem('skyyrose_wishlist') || '[]');

            document.querySelectorAll('.product-card, .woocommerce-loop-product, .product').forEach(product => {
                const productId = product.dataset.productId || product.querySelector('[data-product_id]')?.dataset.product_id;
                if (!productId) return;

                const isInWishlist = wishlist.includes(productId);
                const wishlistBtn = createElement('button', {
                    className: 'wishlist-btn' + (isInWishlist ? ' active' : ''),
                    'aria-label': isInWishlist ? 'Remove from wishlist' : 'Add to wishlist',
                    textContent: isInWishlist ? '❤️' : '🤍'
                });
                wishlistBtn.dataset.productId = productId;

                const target = product.querySelector('.product-image, .woocommerce-loop-product__link, .woocommerce-product-gallery');
                if (target) target.appendChild(wishlistBtn);

                wishlistBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggleWishlist(productId, wishlistBtn);
                });
            });

            this.updateWishlistCount();
        },

        toggleWishlist: function(productId, btn) {
            let wishlist = JSON.parse(localStorage.getItem('skyyrose_wishlist') || '[]');

            if (wishlist.includes(productId)) {
                wishlist = wishlist.filter(id => id !== productId);
                btn.classList.remove('active');
                btn.textContent = '🤍';
                btn.setAttribute('aria-label', 'Add to wishlist');
                window.SkyyRose?.showToast('Removed from wishlist');
            } else {
                wishlist.push(productId);
                btn.classList.add('active');
                btn.textContent = '❤️';
                btn.setAttribute('aria-label', 'Remove from wishlist');
                window.SkyyRose?.showToast('Added to wishlist ❤️');
            }

            localStorage.setItem('skyyrose_wishlist', JSON.stringify(wishlist));
            this.updateWishlistCount();
        },

        updateWishlistCount: function() {
            const wishlist = JSON.parse(localStorage.getItem('skyyrose_wishlist') || '[]');
            document.querySelectorAll('.wishlist-count').forEach(el => {
                el.textContent = wishlist.length;
                el.style.display = wishlist.length > 0 ? 'flex' : 'none';
            });
        },

        // ============================================
        // 8. COUNTDOWN TIMER
        // ============================================

        initCountdown: function() {
            document.querySelectorAll('[data-countdown]').forEach(el => {
                const endDate = new Date(el.dataset.countdown);

                const updateCountdown = () => {
                    const now = new Date();
                    const diff = endDate - now;

                    el.textContent = '';

                    if (diff <= 0) {
                        el.appendChild(createElement('span', { className: 'countdown-ended', textContent: 'Sale Ended' }));
                        return;
                    }

                    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                    const units = [
                        { value: days, label: 'Days' },
                        { value: hours, label: 'Hours' },
                        { value: minutes, label: 'Min' },
                        { value: seconds, label: 'Sec' }
                    ];

                    units.forEach(u => {
                        el.appendChild(createElement('div', { className: 'countdown-unit' }, [
                            createElement('span', { className: 'countdown-value', textContent: u.value }),
                            createElement('span', { className: 'countdown-label', textContent: u.label })
                        ]));
                    });
                };

                updateCountdown();
                setInterval(updateCountdown, 1000);
            });
        },

        // ============================================
        // 9. UPSELLS
        // ============================================

        initUpsells: function() {
            const relatedSection = document.querySelector('.related.products, .up-sells');
            if (relatedSection) {
                const heading = relatedSection.querySelector('h2');
                if (heading) heading.textContent = '✨ Complete Your Look';
            }

            const cartForm = document.querySelector('.woocommerce-cart-form');
            if (cartForm) {
                const upsellBanner = createElement('div', { className: 'cart-upsell-banner' }, [
                    createElement('div', { className: 'upsell-content' }, [
                        createElement('span', { className: 'upsell-icon', textContent: '🎁' }),
                        createElement('div', { className: 'upsell-text' }, [
                            createElement('strong', { textContent: "You're $50 away from free shipping!" }),
                            createElement('span', { textContent: 'Add more items to qualify' })
                        ]),
                        createElement('a', { href: '/shop', className: 'btn btn-outline-sm', textContent: 'Keep Shopping' })
                    ]),
                    createElement('div', { className: 'upsell-progress' }, [
                        Object.assign(createElement('div', { className: 'upsell-progress-bar' }), { style: { width: '66%' } })
                    ])
                ]);
                cartForm.parentNode.insertBefore(upsellBanner, cartForm);
            }
        },

        // ============================================
        // INIT
        // ============================================

        init: function() {
            document.addEventListener('DOMContentLoaded', () => {
                this.initUrgency();
                this.initStickyCart();
                this.initQuickView();
                this.initExitIntent();
                this.initSizeGuide();
                this.initTrustBadges();
                this.initWishlist();
                this.initCountdown();
                this.initUpsells();
            });
        }
    };

    window.SkyyRoseConversion.init();

})();
