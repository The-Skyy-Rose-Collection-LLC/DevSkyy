/**
 * Vault Enhanced JavaScript
 * SkyyRose Vault V3.0 - Multi-Collection Pre-Order Experience
 */

(function() {
    'use strict';

    // === Rotating Collection Logos ===
    const logos = [
        {
            name: 'BLACK ROSE',
            img: null,
            theme: 'theme-black-rose'
        },
        {
            name: 'LOVE HURTS',
            img: null,
            theme: 'theme-love-hurts'
        },
        {
            name: 'SIGNATURE',
            img: null,
            theme: 'theme-signature'
        }
    ];

    function initLogoRotation() {
        const container = document.getElementById('logoContainer');
        if (!container) return;

        let currentIndex = 0;

        function renderLogos() {
            container.textContent = ''; // Clear safely
            const logoImages = {
                'BLACK ROSE': (vaultData.themeUrl || '') + '/assets/images/BLACK-Rose-LOGO.PNG',
                'LOVE HURTS': (vaultData.themeUrl || '') + '/assets/images/Love-Hurts-LOGO.PNG',
                'SIGNATURE': (vaultData.themeUrl || '') + '/assets/images/Signature-LOGO.PNG'
            };

            logos.forEach((logo, index) => {
                const el = document.createElement('div');
                el.className = 'collection-logo ' + logo.theme;
                if (index === 0) el.classList.add('active');

                const img = document.createElement('img');
                img.src = logoImages[logo.name] || '';
                img.alt = logo.name;
                img.onerror = function() { this.style.display = 'none'; };

                el.appendChild(img);
                container.appendChild(el);
            });
        }

        function rotateLogo() {
            const children = container.children;
            if (children.length === 0) return;

            const current = children[currentIndex];
            const nextIndex = (currentIndex + 1) % logos.length;
            const next = children[nextIndex];

            current.classList.remove('active');
            current.classList.add('exit');

            setTimeout(() => {
                current.classList.remove('exit');
            }, 800);

            next.classList.add('active');
            currentIndex = nextIndex;
        }

        renderLogos();
        setInterval(rotateLogo, 3000);
    }

    // === Countdown Timer ===
    function initCountdown() {
        const countdownEl = document.getElementById('launchCountdown');
        if (!countdownEl) return;

        const launchDate = new Date(countdownEl.dataset.launch).getTime();

        function updateCountdown() {
            const now = new Date().getTime();
            const distance = launchDate - now;

            if (distance < 0) {
                // Safely update countdown for launched state
                const countValue = document.createElement('div');
                countValue.className = 'count-value';
                countValue.textContent = 'LAUNCHED';
                countdownEl.textContent = '';
                countdownEl.appendChild(countValue);
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            const daysEl = document.getElementById('days');
            const hoursEl = document.getElementById('hours');
            const minutesEl = document.getElementById('minutes');
            const secondsEl = document.getElementById('seconds');

            if (daysEl) daysEl.textContent = String(days).padStart(2, '0');
            if (hoursEl) hoursEl.textContent = String(hours).padStart(2, '0');
            if (minutesEl) minutesEl.textContent = String(minutes).padStart(2, '0');
            if (secondsEl) secondsEl.textContent = String(seconds).padStart(2, '0');
        }

        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

    // === Collection Tab Filtering ===
    function initCollectionTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        const products = document.querySelectorAll('.vault-card');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const collection = tab.dataset.collection;

                // Update active tab
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');

                // Filter products
                products.forEach(product => {
                    if (collection === 'all') {
                        product.classList.remove('hidden');
                    } else {
                        if (product.dataset.collection === collection) {
                            product.classList.remove('hidden');
                        } else {
                            product.classList.add('hidden');
                        }
                    }
                });

                // Animate filtered products
                requestAnimationFrame(() => {
                    const visibleProducts = document.querySelectorAll('.vault-card:not(.hidden)');
                    visibleProducts.forEach((product, index) => {
                        product.style.animation = 'none';
                        product.offsetHeight; // Trigger reflow
                        product.style.animation = `fadeInUp 0.5s ease ${index * 0.1}s both`;
                    });
                });
            });
        });
    }

    // === Live Viewer Count ===
    function initViewerTracking() {
        const viewerCountEl = document.getElementById('viewerCount');
        if (!viewerCountEl) return;

        // Register this viewer
        fetch(vaultData.ajaxUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                action: 'skyyrose_register_viewer',
                session_id: vaultData.sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                viewerCountEl.textContent = data.data.count;
            }
        });

        // Poll for updates every 30 seconds
        function updateViewerCount() {
            fetch(`${vaultData.ajaxUrl}?action=skyyrose_get_viewer_count`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const newCount = data.data.count;
                        const currentCount = parseInt(viewerCountEl.textContent);

                        if (newCount !== currentCount) {
                            // Animate count change
                            viewerCountEl.style.transform = 'scale(1.2)';
                            viewerCountEl.textContent = newCount;
                            setTimeout(() => {
                                viewerCountEl.style.transform = 'scale(1)';
                            }, 300);
                        }
                    }
                })
                .catch(error => console.error('Viewer count update error:', error));
        }

        setInterval(updateViewerCount, 30000);

        // Unregister on page unload
        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon(vaultData.ajaxUrl, new URLSearchParams({
                action: 'skyyrose_unregister_viewer',
                session_id: vaultData.sessionId
            }));
        });
    }

    // === 3D Viewer Initialization ===
    function init3DViewers() {
        if (typeof LuxuryProductViewer === 'undefined') {
            console.warn('LuxuryProductViewer not loaded');
            return;
        }

        const viewerContainers = document.querySelectorAll('.vault-3d-viewer[data-model]');

        // Lazy load viewers on scroll
        const viewerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.hasAttribute('data-initialized')) {
                    const container = entry.target;
                    const modelUrl = container.dataset.model;
                    const productName = container.dataset.name;
                    const collection = container.dataset.collection;

                    // Get collection theme color
                    const theme = vaultData.themes[collection];
                    const lightingColor = theme ? parseInt(theme.color.replace('#', '0x'), 16) : 0xB76E79;

                    try {
                        const viewer = new LuxuryProductViewer(container, {
                            modelUrl: modelUrl,
                            productName: productName,
                            autoRotate: true,
                            showEffects: !isMobile(),
                            enableAR: true
                        });

                        container.setAttribute('data-initialized', 'true');
                    } catch (error) {
                        console.error('3D Viewer init error:', error);
                        // Create fallback message safely
                        const fallback = document.createElement('div');
                        fallback.style.cssText = 'display: flex; align-items: center; justify-content: center; height: 100%; color: rgba(255,255,255,0.5); text-align: center;';
                        const message = document.createElement('p');
                        message.textContent = '3D Model Unavailable';
                        fallback.appendChild(message);
                        container.textContent = '';
                        container.appendChild(fallback);
                    }
                }
            });
        }, { rootMargin: '200px' });

        viewerContainers.forEach(container => viewerObserver.observe(container));
    }

    // === Add to Cart ===
    window.addToVaultCart = function(productId, collection) {
        const button = event.target;
        const card = button.closest('.vault-card');

        // Check for variation selection
        const variationSelect = card.querySelector('.variation-select');
        let variationId = 0;

        if (variationSelect && variationSelect.value === '') {
            alert('Please select product options');
            variationSelect.focus();
            return;
        }

        if (variationSelect) {
            variationId = parseInt(variationSelect.value);
        }

        button.disabled = true;
        button.textContent = 'PROCESSING...';

        fetch(vaultData.ajaxUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                action: 'skyyrose_submit_preorder',
                nonce: vaultData.nonce,
                product_id: productId,
                variation_id: variationId,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.textContent = 'SECURED ✓';
                button.style.background = 'var(--vault-neon-green)';
                button.style.color = '#000';

                // Track event
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'add_to_cart', {
                        items: [{
                            item_id: productId,
                            item_name: card.querySelector('.item-name').textContent,
                            item_category: collection
                        }]
                    });
                }

                // Redirect to cart after 1.5 seconds
                setTimeout(() => {
                    window.location.href = data.data.cart_url || vaultData.cartUrl;
                }, 1500);
            } else {
                button.textContent = 'ERROR - TRY AGAIN';
                button.style.background = '#DC143C';
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = 'SECURE PRE-ORDER';
                    button.style.background = '';
                    button.style.color = '';
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Add to cart error:', error);
            button.textContent = 'ERROR - TRY AGAIN';
            button.style.background = '#DC143C';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'SECURE PRE-ORDER';
                button.style.background = '';
                button.style.color = '';
            }, 3000);
        });
    };

    // === Utility Functions ===
    function isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth < 768;
    }

    // === Fade In Animation ===
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);

    // === Initialize Everything ===
    document.addEventListener('DOMContentLoaded', () => {
        initLogoRotation();
        initCountdown();
        initCollectionTabs();
        initViewerTracking();
        init3DViewers();

        // Add theme URL to vaultData if not present
        if (!vaultData.themeUrl) {
            const styleLink = document.querySelector('link[rel="stylesheet"]');
            if (styleLink && styleLink.href) {
                const match = styleLink.href.match(/(.+)\/assets\//);
                vaultData.themeUrl = match ? match[1] : '';
            }
        }
    });

})();
