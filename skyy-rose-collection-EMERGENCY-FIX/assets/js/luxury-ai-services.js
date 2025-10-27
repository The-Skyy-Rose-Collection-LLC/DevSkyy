/**
 * Luxury AI Services Integration
 * 
 * JavaScript module for integrating with Docker-containerized AI services
 * Handles product analysis, recommendations, and dynamic pricing
 * 
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 1.0.0
 */

(function($) {
    'use strict';

    /**
     * Luxury AI Services Class
     */
    class LuxuryAIServices {
        constructor() {
            this.config = window.luxuryAI || {};
            this.cache = new Map();
            this.processingQueue = new Set();
            this.customerBehavior = {
                viewedProducts: [],
                timeOnPage: 0,
                interactions: [],
                startTime: Date.now()
            };
            
            this.init();
        }

        /**
         * Initialize AI services
         */
        init() {
            console.log('🤖 Initializing Luxury AI Services...');
            
            // Start behavior tracking
            this.initBehaviorTracking();
            
            // Initialize based on page type
            if (this.config.isShop) {
                this.initShopPage();
            } else if (this.config.currentProduct) {
                this.initProductPage();
            }
            
            // Initialize common features
            this.initDynamicPricing();
            this.initRecommendationEngine();
            
            console.log('✅ Luxury AI Services initialized');
        }

        /**
         * Initialize behavior tracking
         */
        initBehaviorTracking() {
            // Track page views
            this.trackProductView();
            
            // Track time on page
            this.trackTimeOnPage();
            
            // Track interactions
            this.trackInteractions();
            
            // Update customer segment periodically
            setInterval(() => {
                this.updateCustomerSegment();
            }, 30000); // Every 30 seconds
        }

        /**
         * Initialize shop page features
         */
        initShopPage() {
            console.log('🛍️ Initializing shop page AI features...');
            
            // Initialize AI filters
            this.initAIFilters();
            
            // Initialize A/B testing
            this.initABTesting();
            
            // Load product analysis for visible products
            this.analyzeVisibleProducts();
        }

        /**
         * Initialize product page features
         */
        initProductPage() {
            console.log('📦 Initializing product page AI features...');
            
            // Analyze current product
            this.analyzeCurrentProduct();
            
            // Initialize advanced gallery
            this.initAdvancedGallery();
            
            // Load recommendations
            this.loadProductRecommendations();
            
            // Initialize dynamic bundles
            this.initDynamicBundles();
        }

        /**
         * Analyze current product with AI
         */
        async analyzeCurrentProduct() {
            const productId = this.config.currentProduct;
            
            if (!productId || this.processingQueue.has(`analyze_${productId}`)) {
                return;
            }
            
            this.processingQueue.add(`analyze_${productId}`);
            this.showProcessingIndicator('Analyzing product...');
            
            try {
                const response = await this.makeAIRequest('luxury_ai_analyze_product', {
                    product_id: productId
                });
                
                if (response.success) {
                    this.displayProductAnalysis(response.data);
                    this.cache.set(`analysis_${productId}`, response.data);
                } else {
                    console.error('Product analysis failed:', response.data);
                }
            } catch (error) {
                console.error('AI analysis error:', error);
            } finally {
                this.processingQueue.delete(`analyze_${productId}`);
                this.hideProcessingIndicator();
            }
        }

        /**
         * Display product analysis results
         */
        displayProductAnalysis(analysis) {
            // Update style category
            const styleElement = document.getElementById('detected-style');
            if (styleElement && analysis.style_category) {
                styleElement.textContent = analysis.style_category;
                styleElement.classList.add('ai-detected');
            }
            
            // Update materials
            const materialsElement = document.getElementById('detected-materials');
            if (materialsElement && analysis.materials) {
                materialsElement.textContent = analysis.materials.join(', ');
                materialsElement.classList.add('ai-detected');
            }
            
            // Update quality score
            const qualityElement = document.getElementById('ai-quality-stars');
            if (qualityElement && analysis.quality_score) {
                this.displayQualityStars(qualityElement, analysis.quality_score);
            }
            
            // Update detailed attributes
            this.updateAIAttributes(analysis);
            
            // Generate AI content
            this.generateAIContent(analysis);
        }

        /**
         * Display quality stars rating
         */
        displayQualityStars(element, score) {
            const maxStars = 5;
            const filledStars = Math.round(score);
            let starsHTML = '';
            
            for (let i = 1; i <= maxStars; i++) {
                if (i <= filledStars) {
                    starsHTML += '<span class="star filled">⭐</span>';
                } else {
                    starsHTML += '<span class="star empty">☆</span>';
                }
            }
            
            element.innerHTML = starsHTML;
            element.setAttribute('data-score', score);
        }

        /**
         * Update AI-enhanced attributes
         */
        updateAIAttributes(analysis) {
            // Style details
            const styleDetails = document.getElementById('ai-style-details');
            if (styleDetails && analysis.style_details) {
                styleDetails.innerHTML = this.formatAttributeList(analysis.style_details);
            }
            
            // Material details
            const materialDetails = document.getElementById('ai-material-details');
            if (materialDetails && analysis.material_details) {
                materialDetails.innerHTML = this.formatAttributeList(analysis.material_details);
            }
            
            // Care instructions
            const careGuide = document.getElementById('ai-care-guide');
            if (careGuide && analysis.care_instructions) {
                careGuide.innerHTML = this.formatCareInstructions(analysis.care_instructions);
            }
        }

        /**
         * Format attribute list for display
         */
        formatAttributeList(attributes) {
            return attributes.map(attr => 
                `<span class="attribute-tag">${attr}</span>`
            ).join('');
        }

        /**
         * Format care instructions
         */
        formatCareInstructions(instructions) {
            return instructions.map(instruction => 
                `<div class="care-instruction">
                    <span class="care-icon">${this.getCareIcon(instruction.type)}</span>
                    <span class="care-text">${instruction.text}</span>
                </div>`
            ).join('');
        }

        /**
         * Get care instruction icon
         */
        getCareIcon(type) {
            const icons = {
                'wash': '🧺',
                'dry': '🌬️',
                'iron': '🔥',
                'bleach': '🚫',
                'dry_clean': '🧽'
            };
            return icons[type] || '📋';
        }

        /**
         * Load product recommendations
         */
        async loadProductRecommendations() {
            const productId = this.config.currentProduct;
            const customerSegment = this.config.customerSegment;
            
            if (!productId) return;
            
            try {
                // Load different types of recommendations
                const recommendationTypes = ['related', 'cross_sell', 'upsell'];
                
                for (const type of recommendationTypes) {
                    const response = await this.makeAIRequest('luxury_ai_get_recommendations', {
                        product_id: productId,
                        customer_segment: customerSegment,
                        type: type
                    });
                    
                    if (response.success) {
                        this.displayRecommendations(type, response.data);
                    }
                }
            } catch (error) {
                console.error('Recommendations loading error:', error);
            }
        }

        /**
         * Display recommendations
         */
        displayRecommendations(type, recommendations) {
            const containers = {
                'related': 'ai-product-recommendations',
                'cross_sell': 'ai-complementary-items',
                'upsell': 'ai-premium-alternatives'
            };
            
            const container = document.getElementById(containers[type]);
            if (!container || !recommendations.length) return;
            
            const html = recommendations.map(product => this.formatProductCard(product)).join('');
            container.innerHTML = html;
            
            // Add interaction tracking
            container.querySelectorAll('.product-card').forEach(card => {
                card.addEventListener('click', () => {
                    this.trackInteraction('recommendation_click', {
                        type: type,
                        product_id: card.dataset.productId
                    });
                });
            });
        }

        /**
         * Format product card HTML
         */
        formatProductCard(product) {
            return `
                <div class="product-card ai-recommended" data-product-id="${product.id}">
                    <div class="product-image">
                        <img src="${product.image}" alt="${product.name}" loading="lazy">
                        ${product.ai_score ? `<div class="ai-score">${product.ai_score}% match</div>` : ''}
                    </div>
                    <div class="product-info">
                        <h4 class="product-title">${product.name}</h4>
                        <div class="product-price">${product.price}</div>
                        ${product.ai_reason ? `<div class="ai-reason">${product.ai_reason}</div>` : ''}
                    </div>
                    <div class="product-actions">
                        <a href="${product.url}" class="btn-luxury-small">View Product</a>
                    </div>
                </div>
            `;
        }

        /**
         * Initialize dynamic pricing
         */
        initDynamicPricing() {
            if (!this.config.currentProduct) return;
            
            // Load dynamic pricing every 5 minutes
            this.loadDynamicPricing();
            setInterval(() => {
                this.loadDynamicPricing();
            }, 300000); // 5 minutes
        }

        /**
         * Load dynamic pricing
         */
        async loadDynamicPricing() {
            try {
                const response = await this.makeAIRequest('luxury_ai_get_dynamic_pricing', {
                    product_id: this.config.currentProduct,
                    customer_segment: this.config.customerSegment
                });
                
                if (response.success) {
                    this.displayDynamicPricing(response.data);
                }
            } catch (error) {
                console.error('Dynamic pricing error:', error);
            }
        }

        /**
         * Display dynamic pricing
         */
        displayDynamicPricing(pricingData) {
            const container = document.getElementById('dynamic-pricing');
            if (!container) return;
            
            let html = '';
            
            // Price trend
            if (pricingData.trend) {
                html += `<div class="price-trend ${pricingData.trend.direction}">
                    <span class="trend-icon">${pricingData.trend.direction === 'up' ? '📈' : '📉'}</span>
                    <span class="trend-text">${pricingData.trend.message}</span>
                </div>`;
            }
            
            // Personalized offers
            if (pricingData.offers && pricingData.offers.length > 0) {
                html += '<div class="personalized-offers">';
                pricingData.offers.forEach(offer => {
                    html += `<div class="offer-badge ${offer.type}">
                        <span class="offer-text">${offer.text}</span>
                        <span class="offer-discount">${offer.discount}</span>
                    </div>`;
                });
                html += '</div>';
            }
            
            container.innerHTML = html;
        }

        /**
         * Track product view
         */
        trackProductView() {
            if (this.config.currentProduct) {
                this.customerBehavior.viewedProducts.push({
                    product_id: this.config.currentProduct,
                    timestamp: Date.now()
                });
                
                // Update view count on server
                this.updateProductViewCount(this.config.currentProduct);
            }
        }

        /**
         * Track time on page
         */
        trackTimeOnPage() {
            setInterval(() => {
                this.customerBehavior.timeOnPage = Date.now() - this.customerBehavior.startTime;
            }, 1000);
        }

        /**
         * Track interactions
         */
        trackInteractions() {
            // Track clicks on product elements
            document.addEventListener('click', (e) => {
                if (e.target.closest('.product-card, .add-to-cart, .product-image, .variation-selector')) {
                    this.trackInteraction('click', {
                        element: e.target.className,
                        timestamp: Date.now()
                    });
                }
            });
            
            // Track scroll depth
            let maxScroll = 0;
            window.addEventListener('scroll', () => {
                const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
                if (scrollPercent > maxScroll) {
                    maxScroll = scrollPercent;
                    this.trackInteraction('scroll', { depth: scrollPercent });
                }
            });
        }

        /**
         * Track specific interaction
         */
        trackInteraction(type, data) {
            this.customerBehavior.interactions.push({
                type: type,
                data: data,
                timestamp: Date.now()
            });
        }

        /**
         * Update customer segment based on behavior
         */
        async updateCustomerSegment() {
            try {
                const response = await this.makeAIRequest('luxury_ai_update_customer_segment', {
                    viewed_products: this.customerBehavior.viewedProducts.map(v => v.product_id),
                    time_on_page: this.customerBehavior.timeOnPage,
                    interactions: JSON.stringify(this.customerBehavior.interactions),
                    price_range: this.detectPriceRangeInterest()
                });
                
                if (response.success && response.data.segment !== this.config.customerSegment) {
                    this.config.customerSegment = response.data.segment;
                    console.log('🎯 Customer segment updated:', response.data.segment);
                    
                    // Refresh recommendations with new segment
                    if (this.config.currentProduct) {
                        this.loadProductRecommendations();
                    }
                }
            } catch (error) {
                console.error('Customer segment update error:', error);
            }
        }

        /**
         * Detect price range interest from behavior
         */
        detectPriceRangeInterest() {
            // Analyze clicked products and their price ranges
            // This is a simplified implementation
            return 'medium'; // Default to medium range
        }

        /**
         * Make AJAX request to AI service
         */
        async makeAIRequest(action, data) {
            const formData = new FormData();
            formData.append('action', action);
            formData.append('nonce', this.config.nonce);
            
            Object.keys(data).forEach(key => {
                formData.append(key, data[key]);
            });
            
            const response = await fetch(this.config.ajaxUrl || luxuryEcommerce.ajax_url, {
                method: 'POST',
                body: formData
            });
            
            return await response.json();
        }

        /**
         * Show processing indicator
         */
        showProcessingIndicator(message = 'Processing...') {
            const indicator = document.getElementById('ai-processing');
            if (indicator) {
                indicator.querySelector('.processing-text').textContent = message;
                indicator.style.display = 'flex';
            }
        }

        /**
         * Hide processing indicator
         */
        hideProcessingIndicator() {
            const indicator = document.getElementById('ai-processing');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }

        /**
         * Update product view count
         */
        async updateProductViewCount(productId) {
            try {
                await fetch(this.config.ajaxUrl || luxuryEcommerce.ajax_url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        action: 'luxury_update_view_count',
                        product_id: productId,
                        nonce: this.config.nonce
                    })
                });
            } catch (error) {
                console.error('View count update error:', error);
            }
        }
    }

    // Initialize when DOM is ready
    $(document).ready(function() {
        window.LuxuryAIServices = new LuxuryAIServices();
    });

})(jQuery);
