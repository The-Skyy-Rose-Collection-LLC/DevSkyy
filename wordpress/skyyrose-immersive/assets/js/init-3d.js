/**
 * SkyyRose 3D Experience Initialization
 *
 * Handles automatic detection and initialization of 3D experiences
 * based on container data attributes and page context
 */

(function() {
    'use strict';

    // Global configuration from WordPress
    const config = window.skyyrose3D || {};

    /**
     * Clean corrupted JSON response by stripping leading junk
     *
     * WordPress AJAX responses can get corrupted by:
     * - Plugin HTML wrappers (<p>, <div>, etc.)
     * - PHP warnings/notices
     * - Stray whitespace or BOM characters
     *
     * This function salvages the JSON by finding the first { or [ and extracting from there.
     *
     * Sources:
     * - Zack Katz (GravityView): https://katz.co/7671/
     * - Mike Jolley (WooCommerce): https://mikejolley.com/2015/11/12/debugging-unexpected-token-in-woocommerce-2-4/
     *
     * @param {string} response - The potentially corrupted response
     * @returns {object|null} - Parsed JSON object or null if unparseable
     */
    function cleanJsonResponse(response) {
        if (typeof response !== 'string') {
            // Already an object, return as-is
            return response;
        }

        const trimmed = response.trim();

        // First, try parsing as-is (fast path for clean responses)
        try {
            return JSON.parse(trimmed);
        } catch (e) {
            // Response is corrupted, attempt to salvage
        }

        // Strip HTML wrapper tags (e.g., <p>...</p>, <div>...</div>)
        const htmlMatch = trimmed.match(/^<[a-z]+[^>]*>([\s\S]*)<\/[a-z]+>$/i);
        if (htmlMatch) {
            try {
                return JSON.parse(htmlMatch[1].trim());
            } catch (e) {
                // Inner content still not valid JSON
            }
        }

        // Strip leading junk before JSON (PHP warnings, notices, etc.)
        const jsonStart = trimmed.search(/[{\[]/);
        if (jsonStart > 0) {
            const cleaned = trimmed.substring(jsonStart);
            try {
                const parsed = JSON.parse(cleaned);
                console.warn('SkyyRose 3D: Cleaned corrupted JSON response (stripped ' + jsonStart + ' leading chars)');
                return parsed;
            } catch (e) {
                // Still couldn't parse
            }
        }

        // Give up - log the corruption for debugging
        console.error('SkyyRose 3D: Could not parse or clean JSON response');
        console.error('Raw response (first 200 chars):', trimmed.substring(0, 200));
        return null;
    }

    /**
     * Initialize all 3D experiences on the page
     */
    function initializeExperiences() {
        // Find all 3D containers
        const containers = document.querySelectorAll('.skyyrose-3d-container[data-config]');

        containers.forEach(container => {
            initializeContainer(container);
        });

        // Also check for collection-specific containers by ID
        initializeCollectionContainers();
    }

    /**
     * Initialize a specific container
     */
    function initializeContainer(container) {
        if (container.dataset.initialized === 'true') {
            return;
        }

        try {
            // Use cleanJsonResponse to handle potentially corrupted data attributes
            const rawConfig = container.dataset.config || '{}';
            const containerConfig = cleanJsonResponse(rawConfig) || {};
            const collection = containerConfig.collection || detectCollection(container);

            if (!collection) {
                console.warn('SkyyRose 3D: No collection specified for container', container.id);
                return;
            }

            const ExperienceClass = getExperienceClass(collection);

            if (!ExperienceClass) {
                console.warn(`SkyyRose 3D: Experience class not found for collection: ${collection}`);
                return;
            }

            // Merge configs
            const finalConfig = {
                ...config,
                ...containerConfig,
                isMobile: config.isMobile || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
            };

            // Create the experience
            const experience = new ExperienceClass(container.id, finalConfig);

            // Store reference for later access
            container.dataset.initialized = 'true';
            container._skyyRoseExperience = experience;

            console.log(`SkyyRose 3D: Initialized ${collection} experience for`, container.id);
        } catch (error) {
            console.error('SkyyRose 3D: Error initializing container', error);
        }
    }

    /**
     * Initialize containers by collection ID pattern
     */
    function initializeCollectionContainers() {
        const collections = ['signature', 'lovehurts', 'blackrose'];

        collections.forEach(collection => {
            const container = document.getElementById(`${collection}-experience`);

            if (container && container.dataset.initialized !== 'true') {
                const ExperienceClass = getExperienceClass(collection);

                if (ExperienceClass && typeof THREE !== 'undefined') {
                    try {
                        new ExperienceClass(`${collection}-experience`);
                        container.dataset.initialized = 'true';
                        console.log(`SkyyRose 3D: Auto-initialized ${collection} experience`);
                    } catch (error) {
                        console.error(`SkyyRose 3D: Failed to initialize ${collection}`, error);
                    }
                }
            }
        });
    }

    /**
     * Get the experience class for a collection
     */
    function getExperienceClass(collection) {
        const classMap = {
            'signature': window.SignatureExperience,
            'lovehurts': window.LoveHurtsExperience,
            'blackrose': window.BlackRoseExperience
        };

        return classMap[collection.toLowerCase()];
    }

    /**
     * Detect collection from container classes or parent elements
     */
    function detectCollection(container) {
        // Check container classes
        if (container.classList.contains('skyyrose-3d-signature')) return 'signature';
        if (container.classList.contains('skyyrose-3d-lovehurts')) return 'lovehurts';
        if (container.classList.contains('skyyrose-3d-blackrose')) return 'blackrose';

        // Check parent page body class
        const body = document.body;
        if (body.classList.contains('collection-signature')) return 'signature';
        if (body.classList.contains('collection-lovehurts')) return 'lovehurts';
        if (body.classList.contains('collection-blackrose')) return 'blackrose';

        return null;
    }

    /**
     * Handle product click events from 3D experiences
     */
    function setupProductClickHandler() {
        window.addEventListener('skyyrose:product-click', function(event) {
            const { index, collection } = event.detail;

            console.log(`Product clicked: Collection=${collection}, Index=${index}`);

            // Dispatch to any registered handlers
            if (window.skyyRoseProductModal) {
                window.skyyRoseProductModal.open(collection, index);
            }

            // Fallback: Navigate to product page if URL is available
            const productData = getProductData(collection, index);
            if (productData && productData.url) {
                window.location.href = productData.url;
            }
        });
    }

    /**
     * Get product data (placeholder - would be populated from WooCommerce)
     */
    function getProductData(collection, index) {
        // This would typically be populated via wp_localize_script
        const products = window.skyyrose3D?.products || {};
        return products[collection]?.[index] || null;
    }

    /**
     * Intersection Observer for lazy loading 3D experiences
     */
    function setupLazyLoading() {
        if (!('IntersectionObserver' in window)) {
            // Fallback for older browsers
            initializeExperiences();
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    initializeContainer(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '100px',
            threshold: 0.1
        });

        // Observe all 3D containers
        document.querySelectorAll('.skyyrose-3d-container').forEach(container => {
            if (container.dataset.initialized !== 'true') {
                observer.observe(container);
            }
        });
    }

    /**
     * Handle visibility changes (pause when tab not visible)
     */
    function setupVisibilityHandler() {
        document.addEventListener('visibilitychange', function() {
            const containers = document.querySelectorAll('.skyyrose-3d-container[data-initialized="true"]');

            containers.forEach(container => {
                const experience = container._skyyRoseExperience;
                if (experience) {
                    if (document.hidden) {
                        // Pause animation when tab is hidden
                        if (experience.clock) {
                            experience.clock.stop();
                        }
                    } else {
                        // Resume animation when tab is visible
                        if (experience.clock) {
                            experience.clock.start();
                        }
                    }
                }
            });
        });
    }

    /**
     * Performance monitoring
     */
    function setupPerformanceMonitoring() {
        if (!window.performance || !window.performance.now) return;

        let frameCount = 0;
        let lastTime = performance.now();

        function measureFPS() {
            frameCount++;
            const now = performance.now();

            if (now - lastTime >= 1000) {
                const fps = Math.round(frameCount * 1000 / (now - lastTime));

                // Log if FPS drops below threshold
                if (fps < 30) {
                    console.warn(`SkyyRose 3D: Low FPS detected (${fps}). Consider reducing quality settings.`);
                }

                frameCount = 0;
                lastTime = now;
            }

            requestAnimationFrame(measureFPS);
        }

        // Only run in development/debug mode
        if (config.debug) {
            requestAnimationFrame(measureFPS);
        }
    }

    /**
     * Cleanup on page unload
     */
    function setupCleanup() {
        window.addEventListener('beforeunload', function() {
            document.querySelectorAll('.skyyrose-3d-container[data-initialized="true"]').forEach(container => {
                const experience = container._skyyRoseExperience;
                if (experience && typeof experience.dispose === 'function') {
                    experience.dispose();
                }
            });
        });
    }

    /**
     * Main initialization
     */
    function init() {
        // Wait for Three.js to be available
        if (typeof THREE === 'undefined') {
            console.log('SkyyRose 3D: Waiting for Three.js...');
            setTimeout(init, 100);
            return;
        }

        console.log('SkyyRose 3D: Initializing...');

        setupProductClickHandler();
        setupVisibilityHandler();
        setupCleanup();

        // Use lazy loading or immediate initialization based on config
        if (config.lazyLoad !== false) {
            setupLazyLoading();
        } else {
            initializeExperiences();
        }

        if (config.debug) {
            setupPerformanceMonitoring();
        }

        console.log('SkyyRose 3D: Ready');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for external access
    window.SkyyRose3D = {
        init: initializeExperiences,
        initContainer: initializeContainer,
        getExperience: function(containerId) {
            const container = document.getElementById(containerId);
            return container?._skyyRoseExperience || null;
        },
        // Expose JSON cleaner for use by other scripts
        cleanJsonResponse: cleanJsonResponse
    };
})();
