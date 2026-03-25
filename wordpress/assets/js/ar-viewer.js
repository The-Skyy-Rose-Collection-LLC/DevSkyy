/**
 * SkyyRose AR Quick Look - Client-side JavaScript
 * Handles AR button interactions, device detection, and analytics tracking
 */

(function($) {
    'use strict';

    /**
     * AR Viewer class
     */
    class SkyyRoseARViewer {
        constructor() {
            this.supportsAR = this.detectARSupport();
            this.init();
        }

        /**
         * Initialize AR viewer functionality
         */
        init() {
            // Handle AR button clicks
            this.bindARButtons();

            // Handle fallback 3D viewer modal
            this.bindModalButtons();

            // Track AR views
            if (window.skyyRoseAR && window.skyyRoseAR.analytics === '1') {
                this.bindAnalytics();
            }

            // Update buttons based on AR support
            this.updateButtonState();
        }

        /**
         * Detect AR Quick Look support
         * @returns {boolean}
         */
        detectARSupport() {
            // Check for iOS 12+ with AR Quick Look support
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            const iOSVersion = this.getIOSVersion();

            // Check for AR Quick Look support via anchor[rel=ar]
            const supportsRelAR = document.createElement('a').relList.supports('ar');

            // WebXR support for Android
            const supportsWebXR = 'xr' in navigator;

            return (isIOS && iOSVersion >= 12) || supportsRelAR || supportsWebXR;
        }

        /**
         * Get iOS version
         * @returns {number|null}
         */
        getIOSVersion() {
            const match = navigator.userAgent.match(/OS (\d+)_(\d+)_?(\d+)?/);
            if (match) {
                return parseInt(match[1], 10);
            }
            return null;
        }

        /**
         * Bind AR button click handlers
         */
        bindARButtons() {
            const self = this;

            $(document).on('click', '.skyyrose-ar-button', function(e) {
                const $button = $(this);

                // If it's a real AR link (iOS), let it work natively
                if ($button.is('a[rel="ar"]')) {
                    // Track AR view
                    self.trackAREvent($button.data('product-id'), 'ar_view');
                    return true;
                }

                // Otherwise, it's a fallback button - open modal
                e.preventDefault();
                const buttonId = $button.attr('id');
                const $modal = $('#' + buttonId + '-modal');

                if ($modal.length) {
                    self.openModal($modal);
                    self.trackAREvent($button.data('product-id'), '3d_view');
                }
            });
        }

        /**
         * Bind modal close handlers
         */
        bindModalButtons() {
            const self = this;

            // Close button
            $(document).on('click', '.skyyrose-ar-modal__close', function() {
                const $modal = $(this).closest('.skyyrose-ar-modal');
                self.closeModal($modal);
            });

            // Overlay click
            $(document).on('click', '.skyyrose-ar-modal__overlay', function() {
                const $modal = $(this).closest('.skyyrose-ar-modal');
                self.closeModal($modal);
            });

            // Escape key
            $(document).on('keydown', function(e) {
                if (e.key === 'Escape' || e.keyCode === 27) {
                    const $openModal = $('.skyyrose-ar-modal:visible');
                    if ($openModal.length) {
                        self.closeModal($openModal);
                    }
                }
            });
        }

        /**
         * Open 3D viewer modal
         * @param {jQuery} $modal
         */
        openModal($modal) {
            $modal.fadeIn(300);
            $('body').css('overflow', 'hidden');

            // Initialize model-viewer if not already loaded
            const $modelViewer = $modal.find('model-viewer');
            if ($modelViewer.length && !$modelViewer.data('initialized')) {
                $modelViewer.data('initialized', true);

                // Handle model load events
                $modelViewer[0].addEventListener('load', function() {
                    console.log('3D model loaded successfully');
                });

                $modelViewer[0].addEventListener('error', function(e) {
                    console.error('Error loading 3D model:', e);
                    alert(window.skyyRoseAR.i18n.error);
                });
            }
        }

        /**
         * Close 3D viewer modal
         * @param {jQuery} $modal
         */
        closeModal($modal) {
            $modal.fadeOut(300);
            $('body').css('overflow', '');

            // Pause model viewer to save resources
            const $modelViewer = $modal.find('model-viewer');
            if ($modelViewer.length && $modelViewer[0].pause) {
                $modelViewer[0].pause();
            }
        }

        /**
         * Update button states based on AR support
         */
        updateButtonState() {
            const self = this;

            $('.skyyrose-ar-button').each(function() {
                const $button = $(this);

                // Add device capability class
                if (self.supportsAR) {
                    $button.addClass('skyyrose-ar-button--ar-capable');
                } else {
                    $button.addClass('skyyrose-ar-button--ar-fallback');
                }

                // Add loading state handler
                if ($button.is('a[rel="ar"]')) {
                    $button.on('click', function() {
                        $button.addClass('skyyrose-ar-button--loading');
                    });
                }
            });
        }

        /**
         * Bind analytics tracking
         */
        bindAnalytics() {
            const self = this;

            // Track button impressions
            $('.skyyrose-ar-button').each(function() {
                const $button = $(this);
                const productId = $button.data('product-id');

                if (productId) {
                    // Use Intersection Observer for visibility tracking
                    if ('IntersectionObserver' in window) {
                        const observer = new IntersectionObserver(function(entries) {
                            entries.forEach(function(entry) {
                                if (entry.isIntersecting && !$button.data('impression-tracked')) {
                                    $button.data('impression-tracked', true);
                                    self.trackAREvent(productId, 'impression');
                                }
                            });
                        }, {
                            threshold: 0.5
                        });

                        observer.observe($button[0]);
                    }
                }
            });

            // Track engagement time
            let engagementStart = null;

            $(document).on('mouseenter', '.skyyrose-ar-button', function() {
                engagementStart = Date.now();
            });

            $(document).on('mouseleave', '.skyyrose-ar-button', function() {
                if (engagementStart) {
                    const duration = Date.now() - engagementStart;
                    const productId = $(this).data('product-id');

                    if (duration > 1000 && productId) { // Only track if hovered for >1s
                        self.trackAREvent(productId, 'engagement', { duration: duration });
                    }
                    engagementStart = null;
                }
            });
        }

        /**
         * Track AR event via AJAX
         * @param {number} productId
         * @param {string} eventType
         * @param {object} extraData
         */
        trackAREvent(productId, eventType, extraData = {}) {
            if (!window.skyyRoseAR || window.skyyRoseAR.analytics !== '1') {
                return;
            }

            $.ajax({
                url: window.skyyRoseAR.ajaxUrl,
                type: 'POST',
                data: {
                    action: 'skyyrose_ar_track',
                    nonce: window.skyyRoseAR.nonce,
                    product_id: productId,
                    event_type: eventType,
                    extra_data: JSON.stringify(extraData)
                },
                success: function(response) {
                    if (response.success) {
                        console.log('AR event tracked:', eventType, productId);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Failed to track AR event:', error);
                }
            });
        }

        /**
         * Preload USDZ file for faster AR experience
         * @param {string} usdzUrl
         */
        preloadUSDZ(usdzUrl) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = usdzUrl;
            link.as = 'fetch';
            document.head.appendChild(link);
        }

        /**
         * Check if device is in landscape mode
         * @returns {boolean}
         */
        isLandscape() {
            return window.innerWidth > window.innerHeight;
        }

        /**
         * Show AR not supported message
         */
        showNotSupportedMessage() {
            alert(window.skyyRoseAR.i18n.notSupported);
        }
    }

    /**
     * Initialize when document is ready
     */
    $(document).ready(function() {
        // Initialize AR viewer
        const arViewer = new SkyyRoseARViewer();

        // Make globally accessible
        window.skyyRoseARViewer = arViewer;

        // Trigger custom event for extensibility
        $(document).trigger('skyyrose:ar:initialized', [arViewer]);

        // Log initialization
        console.log('SkyyRose AR Quick Look initialized', {
            supportsAR: arViewer.supportsAR,
            buttons: $('.skyyrose-ar-button').length
        });
    });

    /**
     * Handle page visibility changes to pause/resume 3D viewers
     */
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            // Pause all active model viewers
            $('model-viewer').each(function() {
                if (this.pause) {
                    this.pause();
                }
            });
        }
    });

    /**
     * Expose utility functions globally
     */
    window.SkyyRoseAR = window.SkyyRoseAR || {};
    window.SkyyRoseAR.openARViewer = function(productId) {
        const $button = $('.skyyrose-ar-button[data-product-id="' + productId + '"]').first();
        if ($button.length) {
            $button.trigger('click');
            return true;
        }
        return false;
    };

    window.SkyyRoseAR.preloadModel = function(productId) {
        const $button = $('.skyyrose-ar-button[data-product-id="' + productId + '"]').first();
        if ($button.length && window.skyyRoseARViewer) {
            const usdzUrl = $button.data('usdz-url');
            if (usdzUrl) {
                window.skyyRoseARViewer.preloadUSDZ(usdzUrl);
                return true;
            }
        }
        return false;
    };

})(jQuery);
