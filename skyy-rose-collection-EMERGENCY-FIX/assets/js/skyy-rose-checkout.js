/**
 * Skyy Rose Collection Checkout Experience
 * 
 * Advanced multi-step checkout with AI-powered features
 * Authentic brand integration with luxury user experience
 * 
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 1.0.0
 */

(function($) {
    'use strict';

    /**
     * Skyy Rose Checkout Experience Class
     */
    class SkyyRoseCheckout {
        constructor() {
            this.currentStep = 1;
            this.totalSteps = 4;
            this.checkoutData = {};
            this.aiInsights = {};
            this.validationRules = {};
            
            this.init();
        }

        /**
         * Initialize checkout experience
         */
        init() {
            console.log('🌹 Initializing Skyy Rose Collection Checkout Experience...');
            
            // Initialize multi-step functionality
            this.initMultiStepCheckout();
            
            // Initialize AI features
            this.initAIFeatures();
            
            // Initialize form validation
            this.initFormValidation();
            
            // Initialize analytics tracking
            this.initAnalyticsTracking();
            
            // Initialize cart features
            this.initCartFeatures();
            
            console.log('✅ Skyy Rose Checkout Experience initialized');
        }

        /**
         * Initialize multi-step checkout
         */
        initMultiStepCheckout() {
            // Handle step navigation
            $('.step-next').on('click', (e) => {
                e.preventDefault();
                const nextStep = parseInt($(e.target).data('next-step'));
                this.goToStep(nextStep);
            });

            $('.step-back').on('click', (e) => {
                e.preventDefault();
                const prevStep = parseInt($(e.target).data('prev-step'));
                this.goToStep(prevStep);
            });

            // Initialize progress bar
            this.updateProgressBar();
        }

        /**
         * Navigate to specific step
         */
        goToStep(stepNumber) {
            if (stepNumber < 1 || stepNumber > this.totalSteps) {
                return;
            }

            // Validate current step before proceeding
            if (stepNumber > this.currentStep && !this.validateCurrentStep()) {
                return;
            }

            // Hide current step
            $(`#checkout-step-${this.currentStep}`).fadeOut(300, () => {
                // Show new step
                $(`#checkout-step-${stepNumber}`).fadeIn(300);
                
                // Update current step
                this.currentStep = stepNumber;
                
                // Update progress bar
                this.updateProgressBar();
                
                // Track step change
                this.trackStepChange(stepNumber);
                
                // Load step-specific AI features
                this.loadStepAIFeatures(stepNumber);
                
                // Scroll to top
                $('html, body').animate({
                    scrollTop: $('.checkout-progress-wrapper').offset().top - 100
                }, 500);
            });
        }

        /**
         * Update progress bar
         */
        updateProgressBar() {
            $('.progress-step').each((index, element) => {
                const stepNum = index + 1;
                const $step = $(element);
                
                $step.removeClass('active completed');
                
                if (stepNum < this.currentStep) {
                    $step.addClass('completed');
                } else if (stepNum === this.currentStep) {
                    $step.addClass('active');
                }
            });
        }

        /**
         * Validate current step
         */
        validateCurrentStep() {
            const stepId = `#checkout-step-${this.currentStep}`;
            let isValid = true;
            let errors = [];

            // Clear previous errors
            $(stepId).find('.field-error').remove();
            $(stepId).find('.error').removeClass('error');

            // Step-specific validation
            switch (this.currentStep) {
                case 1: // Customer Information
                    isValid = this.validateCustomerInfo();
                    break;
                case 2: // Shipping
                    isValid = this.validateShipping();
                    break;
                case 3: // Payment
                    isValid = this.validatePayment();
                    break;
                case 4: // Review
                    isValid = true; // Review step doesn't need validation
                    break;
            }

            if (!isValid) {
                this.showValidationErrors(stepId);
            }

            return isValid;
        }

        /**
         * Validate customer information
         */
        validateCustomerInfo() {
            let isValid = true;
            const requiredFields = [
                'billing_first_name',
                'billing_last_name',
                'billing_email',
                'billing_phone',
                'billing_address_1',
                'billing_city',
                'billing_postcode'
            ];

            requiredFields.forEach(fieldName => {
                const $field = $(`[name="${fieldName}"]`);
                if ($field.length && !$field.val().trim()) {
                    $field.addClass('error');
                    isValid = false;
                }
            });

            // Email validation
            const email = $('[name="billing_email"]').val();
            if (email && !this.isValidEmail(email)) {
                $('[name="billing_email"]').addClass('error');
                isValid = false;
            }

            return isValid;
        }

        /**
         * Validate shipping information
         */
        validateShipping() {
            // Check if shipping method is selected
            const selectedShipping = $('input[name^="shipping_method"]:checked');
            if (selectedShipping.length === 0) {
                this.showError('Please select a shipping method');
                return false;
            }

            return true;
        }

        /**
         * Validate payment information
         */
        validatePayment() {
            // Check if payment method is selected
            const selectedPayment = $('input[name="payment_method"]:checked');
            if (selectedPayment.length === 0) {
                this.showError('Please select a payment method');
                return false;
            }

            // Terms and conditions
            const termsAccepted = $('#terms').is(':checked');
            if (!termsAccepted) {
                this.showError('Please accept the terms and conditions');
                return false;
            }

            return true;
        }

        /**
         * Initialize AI features
         */
        initAIFeatures() {
            // Load cart analysis
            this.loadCartAnalysis();
            
            // Initialize address validation
            this.initAddressValidation();
            
            // Initialize shipping optimization
            this.initShippingOptimization();
            
            // Initialize checkout recommendations
            this.initCheckoutRecommendations();
            
            // Initialize dynamic pricing
            this.initDynamicPricing();
        }

        /**
         * Load cart analysis
         */
        async loadCartAnalysis() {
            try {
                const cartData = this.getCartData();
                
                const response = await this.makeAIRequest('luxury_ai_analyze_cart', {
                    cart_items: cartData.items,
                    cart_total: cartData.total,
                    customer_segment: luxuryEcommerce.customerSegment || 'new_visitor'
                });
                
                if (response.success) {
                    this.displayCartAnalysis(response.data);
                }
            } catch (error) {
                console.error('Cart analysis error:', error);
            }
        }

        /**
         * Display cart analysis
         */
        displayCartAnalysis(analysis) {
            // Update style analysis
            if (analysis.style_category) {
                $('#cart-style-analysis').text(`Your style: ${analysis.style_category}`);
            }
            
            // Update value analysis
            if (analysis.luxury_index) {
                $('#cart-value-analysis').text(`Luxury Index: ${analysis.luxury_index}/10`);
            }
            
            // Update product insights
            if (analysis.product_insights) {
                analysis.product_insights.forEach(insight => {
                    const $insightContainer = $(`#insights-${insight.product_id} .insight-tags`);
                    if ($insightContainer.length) {
                        const tags = insight.tags.map(tag => 
                            `<span class="insight-tag">${tag}</span>`
                        ).join('');
                        $insightContainer.html(tags);
                    }
                });
            }
        }

        /**
         * Initialize address validation
         */
        initAddressValidation() {
            // Real-time address validation
            const addressFields = [
                'billing_address_1',
                'billing_city',
                'billing_postcode',
                'billing_country'
            ];

            addressFields.forEach(fieldName => {
                $(`[name="${fieldName}"]`).on('blur', () => {
                    this.validateAddress();
                });
            });
        }

        /**
         * Validate address with AI
         */
        async validateAddress() {
            const addressData = {
                address_1: $('[name="billing_address_1"]').val(),
                city: $('[name="billing_city"]').val(),
                postcode: $('[name="billing_postcode"]').val(),
                country: $('[name="billing_country"]').val()
            };

            if (!addressData.address_1 || !addressData.city) {
                return;
            }

            try {
                const response = await this.makeAIRequest('luxury_ai_validate_address', addressData);
                
                if (response.success) {
                    this.displayAddressValidation(response.data);
                }
            } catch (error) {
                console.error('Address validation error:', error);
            }
        }

        /**
         * Display address validation results
         */
        displayAddressValidation(validation) {
            const $statusPanel = $('#address-validation-status');
            
            if (validation.is_valid) {
                $statusPanel.html(`
                    <div class="validation-success">
                        <span class="validation-icon">✅</span>
                        <span class="validation-text">Address verified</span>
                    </div>
                `);
            } else {
                $statusPanel.html(`
                    <div class="validation-warning">
                        <span class="validation-icon">⚠️</span>
                        <span class="validation-text">Address needs verification</span>
                        ${validation.suggestions ? `<div class="address-suggestions">${validation.suggestions}</div>` : ''}
                    </div>
                `);
            }
        }

        /**
         * Initialize checkout recommendations
         */
        initCheckoutRecommendations() {
            this.loadLastMinuteRecommendations();
        }

        /**
         * Load last-minute recommendations
         */
        async loadLastMinuteRecommendations() {
            try {
                const cartData = this.getCartData();
                
                const response = await this.makeAIRequest('luxury_ai_get_checkout_recommendations', {
                    cart_items: cartData.items,
                    customer_segment: luxuryEcommerce.customerSegment || 'new_visitor',
                    checkout_stage: 'pre_payment'
                });
                
                if (response.success && response.data.length > 0) {
                    this.displayCheckoutRecommendations(response.data);
                }
            } catch (error) {
                console.error('Checkout recommendations error:', error);
            }
        }

        /**
         * Display checkout recommendations
         */
        displayCheckoutRecommendations(recommendations) {
            const $container = $('#last-minute-suggestions');
            
            const html = recommendations.map(product => `
                <div class="checkout-recommendation-item" data-product-id="${product.id}">
                    <div class="recommendation-image">
                        <img src="${product.image}" alt="${product.name}" loading="lazy">
                    </div>
                    <div class="recommendation-info">
                        <h4 class="recommendation-title">${product.name}</h4>
                        <div class="recommendation-price">${product.price}</div>
                        <button class="btn-luxury-small add-to-cart-checkout" data-product-id="${product.id}">
                            Add to Order
                        </button>
                    </div>
                </div>
            `).join('');
            
            $container.html(html);
            
            // Handle add to cart from checkout
            $('.add-to-cart-checkout').on('click', (e) => {
                e.preventDefault();
                const productId = $(e.target).data('product-id');
                this.addToCartFromCheckout(productId);
            });
        }

        /**
         * Initialize form validation
         */
        initFormValidation() {
            // Real-time validation
            $('.checkout input, .checkout select, .checkout textarea').on('blur', function() {
                const $field = $(this);
                if ($field.hasClass('error')) {
                    if ($field.val().trim()) {
                        $field.removeClass('error');
                        $field.siblings('.field-error').remove();
                    }
                }
            });
        }

        /**
         * Initialize analytics tracking
         */
        initAnalyticsTracking() {
            // Track checkout start
            this.trackEvent('checkout_started', {
                cart_value: this.getCartTotal(),
                item_count: this.getCartItemCount()
            });
            
            // Track step completion
            this.trackStepCompletion();
            
            // Track abandonment risk
            this.trackAbandonmentRisk();
        }

        /**
         * Initialize cart features
         */
        initCartFeatures() {
            // Update cart totals dynamically
            this.initDynamicTotals();
            
            // Handle quantity changes
            $('.luxury-quantity-selector input').on('change', (e) => {
                this.updateCartQuantity(e.target);
            });
            
            // Handle coupon application
            $('.coupon-section button').on('click', (e) => {
                e.preventDefault();
                this.applyCoupon();
            });
        }

        /**
         * Utility functions
         */
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }

        getCartData() {
            return {
                items: this.getCartItems(),
                total: this.getCartTotal(),
                count: this.getCartItemCount()
            };
        }

        getCartItems() {
            const items = [];
            $('.luxury-cart-item').each(function() {
                const $item = $(this);
                items.push({
                    product_id: $item.data('product-id'),
                    quantity: $item.find('input[type="number"]').val(),
                    price: $item.find('.luxury-price').text()
                });
            });
            return items;
        }

        getCartTotal() {
            return $('#cart-total-value').val() || '0';
        }

        getCartItemCount() {
            return $('#cart-item-count').val() || '0';
        }

        async makeAIRequest(action, data) {
            const formData = new FormData();
            formData.append('action', action);
            formData.append('nonce', luxuryEcommerce.nonce);
            
            Object.keys(data).forEach(key => {
                formData.append(key, typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key]);
            });
            
            const response = await fetch(luxuryEcommerce.ajax_url, {
                method: 'POST',
                body: formData
            });
            
            return await response.json();
        }

        showError(message) {
            // Create or update error display
            let $errorContainer = $('.checkout-errors');
            if (!$errorContainer.length) {
                $errorContainer = $('<div class="checkout-errors"></div>');
                $('.checkout-main-content').prepend($errorContainer);
            }
            
            $errorContainer.html(`
                <div class="error-message">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text">${message}</span>
                </div>
            `).show();
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                $errorContainer.fadeOut();
            }, 5000);
        }

        trackEvent(eventName, data) {
            // Track events for analytics
            console.log(`📊 Tracking: ${eventName}`, data);
            
            // Send to analytics service
            if (typeof gtag !== 'undefined') {
                gtag('event', eventName, data);
            }
        }

        trackStepChange(stepNumber) {
            this.trackEvent('checkout_step_viewed', {
                step: stepNumber,
                step_name: this.getStepName(stepNumber)
            });
        }

        getStepName(stepNumber) {
            const stepNames = {
                1: 'Customer Information',
                2: 'Shipping Options',
                3: 'Payment Information',
                4: 'Order Review'
            };
            return stepNames[stepNumber] || 'Unknown';
        }
    }

    // Initialize when DOM is ready
    $(document).ready(function() {
        // Initialize for checkout pages
        if ($('.skyy-rose-checkout-wrapper').length || $('.skyy-rose-cart-wrapper').length) {
            window.SkyyRoseCheckout = new SkyyRoseCheckout();
        }
    });

})(jQuery);
