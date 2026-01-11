/**
 * Luxury Scroll Animations for SkyyRose.
 *
 * Uses IntersectionObserver API for performant scroll-triggered animations.
 * Adds fade-in-up effect to luxury product cards and editorial sections.
 *
 * @package SkyyRose_Immersive
 * @version 2.0.0
 */

(function() {
    'use strict';

    /**
     * Initialize scroll animations when DOM is ready.
     */
    document.addEventListener('DOMContentLoaded', function() {
        // Target elements for animation
        const fadeInElements = document.querySelectorAll(
            '.luxury-product-card, .editorial-section, .woocommerce ul.products li.product'
        );

        // Skip if no elements found or IntersectionObserver not supported
        if (!fadeInElements.length || !('IntersectionObserver' in window)) {
            return;
        }

        /**
         * Intersection Observer configuration.
         * - threshold: 0.1 = trigger when 10% of element is visible
         * - rootMargin: Start animation 50px before element enters viewport
         */
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '50px 0px'
        };

        /**
         * Observer callback: Add animation class when element enters viewport.
         *
         * @param {IntersectionObserverEntry[]} entries - Observed elements
         * @param {IntersectionObserver} observer - Observer instance
         */
        const observerCallback = function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    // Element is visible, add animation class
                    entry.target.classList.add('fade-in-up');

                    // Stop observing this element (animation only runs once)
                    observer.unobserve(entry.target);
                }
            });
        };

        // Create observer instance
        const observer = new IntersectionObserver(observerCallback, observerOptions);

        // Observe all target elements
        fadeInElements.forEach(function(element) {
            // Add initial state (hidden, below viewport)
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';

            // Start observing
            observer.observe(element);
        });
    });
})();
