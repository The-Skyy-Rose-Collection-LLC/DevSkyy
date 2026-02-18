/**
 * SkyyRose - 3D Immersive Experience
 * Production-quality drakerelated.com-level implementation
 */

class ImmersiveExperience {
  constructor() {
    this.currentCollection = document.documentElement.dataset.collection;
    this.hotspots = [];
    this.modal = null;
    this.loading = true;
    this.touchStartX = 0;
    this.touchEndX = 0;

    // Performance monitoring
    this.performanceMarks = {
      start: performance.now(),
      imageLoaded: null,
      hotspotsRendered: null,
      experienceReady: null
    };
  }

  /**
   * Initialize the experience
   */
  async init() {
    console.log('🎬 Initializing SkyyRose 3D Immersive Experience');

    // Setup loading screen
    this.setupLoadingScreen();

    // Progressive image loading
    await this.loadSceneImage();

    // Setup hotspots
    this.setupHotspots();

    // Setup navigation
    this.setupNavigation();

    // Setup modal
    this.setupModal();

    // Setup keyboard shortcuts
    this.setupKeyboardShortcuts();

    // Setup touch gestures (mobile)
    this.setupTouchGestures();

    // Complete loading
    this.completeLoading();

    // Log performance
    this.logPerformance();
  }

  /**
   * Loading screen with progress simulation
   */
  setupLoadingScreen() {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 90) progress = 90; // Hold at 90% until real load

      progressFill.style.width = `${progress}%`;
      progressText.textContent = `Loading experience... ${Math.round(progress)}%`;
    }, 100);

    // Clear interval after 3 seconds max
    setTimeout(() => clearInterval(interval), 3000);

    this.loadingInterval = interval;
  }

  /**
   * Progressive image loading with blur-up technique
   */
  async loadSceneImage() {
    return new Promise((resolve) => {
      const sceneImage = document.getElementById('scene-image');
      const placeholder = document.querySelector('.scene-placeholder');

      if (!sceneImage) {
        console.warn('Scene image element not found');
        resolve();
        return;
      }

      // Check if image is already loaded (cached)
      if (sceneImage.complete && sceneImage.naturalHeight !== 0) {
        sceneImage.classList.add('loaded');
        this.performanceMarks.imageLoaded = performance.now();
        resolve();
        return;
      }

      // Load image
      sceneImage.addEventListener('load', () => {
        setTimeout(() => {
          sceneImage.classList.add('loaded');
          this.performanceMarks.imageLoaded = performance.now();
          console.log('✓ Scene image loaded');
          resolve();
        }, 100); // Small delay for smooth transition
      });

      sceneImage.addEventListener('error', () => {
        console.error('✗ Failed to load scene image');
        // Remove placeholder even on error
        if (placeholder) {
          placeholder.style.opacity = '0';
        }
        resolve();
      });

      // Force load if not already loading
      if (!sceneImage.complete) {
        sceneImage.src = sceneImage.src;
      }
    });
  }

  /**
   * Setup interactive hotspots
   */
  setupHotspots() {
    const hotspotElements = document.querySelectorAll('.hotspot');

    hotspotElements.forEach((hotspot, index) => {
      const productId = hotspot.dataset.product;

      // Click handler
      hotspot.addEventListener('click', () => {
        this.openProductModal(productId);

        // Analytics
        if (window.gtag) {
          gtag('event', 'hotspot_click', {
            product_id: productId,
            collection: this.currentCollection,
            position: index + 1
          });
        }

        // Screen reader announcement
        this.announce(`Opening product: ${hotspot.getAttribute('aria-label')}`);
      });

      // Keyboard accessibility
      hotspot.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          hotspot.click();
        }
      });

      this.hotspots.push({
        element: hotspot,
        productId: productId,
        index: index
      });
    });

    this.performanceMarks.hotspotsRendered = performance.now();
    console.log(`✓ ${hotspotElements.length} hotspots initialized`);
  }

  /**
   * Open product modal
   */
  openProductModal(productId) {
    const product = this.getProduct(productId);
    if (!product) {
      console.error(`Product not found: ${productId}`);
      return;
    }

    const modal = document.getElementById('product-modal');
    const modalBody = document.getElementById('modal-body');

    if (!modal || !modalBody) return;

    // Build modal content
    modalBody.innerHTML = `
      <div class="product-modal-grid">
        <div class="product-modal-image">
          <img src="../assets/images/products/${productId}.jpg" alt="${product.name}" loading="lazy">
        </div>
        <div class="product-modal-details">
          <span class="product-collection">${product.collection}</span>
          <h2 id="modal-title" class="product-modal-title">${product.name}</h2>
          <p class="product-modal-tagline">${product.tagline || ''}</p>
          <p class="product-modal-price">${product.price}</p>

          ${product.description ? `
            <div class="product-modal-description">
              <h3>Description</h3>
              <p>${product.description}</p>
            </div>
          ` : ''}

          ${product.specs ? `
            <div class="product-modal-specs">
              <h3>Specifications</h3>
              <ul>
                ${product.specs.map(spec => `<li>${spec}</li>`).join('')}
              </ul>
            </div>
          ` : ''}

          <div class="product-modal-actions">
            <button class="btn btn-primary add-to-cart-btn" data-product="${productId}">
              Add to Cart
            </button>
            <a href="../collections/${this.currentCollection}.html#${productId}" class="btn btn-secondary">
              View in Grid
            </a>
          </div>
        </div>
      </div>
    `;

    // Show modal
    modal.removeAttribute('hidden');
    setTimeout(() => modal.classList.add('show'), 10);

    // Focus trap
    this.trapFocus(modal);

    // Analytics
    if (window.gtag) {
      gtag('event', 'product_view_3d', {
        product_id: productId,
        product_name: product.name,
        collection: this.currentCollection
      });
    }

    this.modal = { element: modal, productId: productId };
  }

  /**
   * Close product modal
   */
  closeProductModal() {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    modal.classList.remove('show');

    setTimeout(() => {
      modal.setAttribute('hidden', '');
      this.modal = null;
    }, 500);

    // Return focus to hotspot
    const hotspot = document.querySelector(`[data-product="${this.modal?.productId}"]`);
    if (hotspot) {
      hotspot.focus();
    }
  }

  /**
   * Setup modal interactions
   */
  setupModal() {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    // Close button
    const closeBtn = modal.querySelector('.modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeProductModal());
    }

    // Backdrop click
    const backdrop = modal.querySelector('.modal-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', () => this.closeProductModal());
    }

    // ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal) {
        this.closeProductModal();
      }
    });

    // Add to cart button (delegated event)
    modal.addEventListener('click', (e) => {
      if (e.target.classList.contains('add-to-cart-btn')) {
        const productId = e.target.dataset.product;
        this.addToCart(productId);
      }
    });
  }

  /**
   * Add product to cart (placeholder - integrate with WooCommerce)
   */
  addToCart(productId) {
    console.log(`Adding to cart: ${productId}`);

    // TODO: Integrate with WooCommerce API
    // For now, just show feedback
    this.announce(`Product added to cart`);

    // Analytics
    if (window.gtag) {
      gtag('event', 'add_to_cart', {
        product_id: productId,
        collection: this.currentCollection,
        source: '3d_experience'
      });
    }

    // Visual feedback
    const btn = document.querySelector(`.add-to-cart-btn[data-product="${productId}"]`);
    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = 'Added!';
      btn.disabled = true;

      setTimeout(() => {
        btn.textContent = originalText;
        btn.disabled = false;
      }, 2000);
    }
  }

  /**
   * Setup scene navigation (prev/next, dots)
   */
  setupNavigation() {
    const prevBtn = document.querySelector('.scene-nav-prev');
    const nextBtn = document.querySelector('.scene-nav-next');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.navigateToPrevious());
    }

    if (nextBtn) {
      prevBtn.addEventListener('click', () => this.navigateToNext());
    }
  }

  /**
   * Navigate to previous collection
   */
  navigateToPrevious() {
    const collections = ['signature', 'black-rose', 'love-hurts'];
    const currentIndex = collections.indexOf(this.currentCollection);
    const prevIndex = currentIndex === 0 ? collections.length - 1 : currentIndex - 1;

    window.location.href = `${collections[prevIndex]}.html`;
  }

  /**
   * Navigate to next collection
   */
  navigateToNext() {
    const collections = ['signature', 'black-rose', 'love-hurts'];
    const currentIndex = collections.indexOf(this.currentCollection);
    const nextIndex = (currentIndex + 1) % collections.length;

    window.location.href = `${collections[nextIndex]}.html`;
  }

  /**
   * Setup keyboard shortcuts
   */
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ignore if modal is open
      if (this.modal) return;

      // Ignore if typing in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          this.navigateToPrevious();
          break;

        case 'ArrowRight':
          e.preventDefault();
          this.navigateToNext();
          break;

        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
          e.preventDefault();
          const hotspot = this.hotspots[parseInt(e.key) - 1];
          if (hotspot) {
            hotspot.element.click();
          }
          break;

        case 'g':
          // Go to grid view
          e.preventDefault();
          window.location.href = `../collections/${this.currentCollection}.html`;
          break;
      }
    });

    console.log('✓ Keyboard shortcuts enabled');
  }

  /**
   * Setup touch gestures for mobile
   */
  setupTouchGestures() {
    const sceneContainer = document.getElementById('scene-container');
    if (!sceneContainer) return;

    sceneContainer.addEventListener('touchstart', (e) => {
      this.touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sceneContainer.addEventListener('touchend', (e) => {
      this.touchEndX = e.changedTouches[0].screenX;
      this.handleSwipe();
    }, { passive: true });
  }

  /**
   * Handle swipe gesture
   */
  handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = this.touchEndX - this.touchStartX;

    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0) {
        // Swipe right (previous)
        this.navigateToPrevious();
      } else {
        // Swipe left (next)
        this.navigateToNext();
      }
    }
  }

  /**
   * Complete loading sequence
   */
  completeLoading() {
    // Clear loading interval
    if (this.loadingInterval) {
      clearInterval(this.loadingInterval);
    }

    // Set progress to 100%
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    if (progressFill) progressFill.style.width = '100%';
    if (progressText) progressText.textContent = 'Experience ready!';

    // Remove loading state
    setTimeout(() => {
      document.body.classList.remove('loading');
      this.loading = false;
      this.performanceMarks.experienceReady = performance.now();

      // Analytics
      if (window.gtag) {
        gtag('event', 'experience_ready', {
          collection: this.currentCollection,
          load_time: this.performanceMarks.experienceReady - this.performanceMarks.start
        });
      }

      console.log('✨ Experience ready!');
    }, 800);
  }

  /**
   * Get product by ID
   */
  getProduct(productId) {
    // Get from global PRODUCTS config
    if (typeof PRODUCTS !== 'undefined') {
      return PRODUCTS.find(p => p.id === productId);
    }

    // Fallback to hardcoded data (if config.js not loaded)
    const fallbackProducts = {
      'br-001': { id: 'br-001', name: 'Black Rose Tee', collection: 'BLACK ROSE', price: '$85', tagline: 'Gothic elegance meets street style' },
      'br-002': { id: 'br-002', name: 'Rose Garden Dress', collection: 'BLACK ROSE', price: '$245', tagline: 'Hand-embroidered silk elegance' },
      'br-003': { id: 'br-003', name: 'Thorn Leather Jacket', collection: 'BLACK ROSE', price: '$595', tagline: 'Edgy luxury with rose gold details' },
      'br-004': { id: 'br-004', name: 'Midnight Bloom Pants', collection: 'BLACK ROSE', price: '$165', tagline: 'Casual luxury with flowing silhouette' },
      'br-005': { id: 'br-005', name: 'Gothic Rose Boots', collection: 'BLACK ROSE', price: '$425', tagline: 'Combat boots meet romantic details' },
      'br-006': { id: 'br-006', name: 'Rose Petal Scarf', collection: 'BLACK ROSE', price: '$135', tagline: 'Hand-painted silk accessory' }
    };

    return fallbackProducts[productId];
  }

  /**
   * Focus trap for modal accessibility
   */
  trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    modal.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    });

    // Focus first element
    setTimeout(() => firstElement.focus(), 100);
  }

  /**
   * Screen reader announcements
   */
  announce(message) {
    const announcer = document.getElementById('sr-announcements');
    if (!announcer) return;

    announcer.textContent = message;

    // Clear after 3 seconds
    setTimeout(() => {
      announcer.textContent = '';
    }, 3000);
  }

  /**
   * Log performance metrics
   */
  logPerformance() {
    const metrics = {
      totalLoadTime: this.performanceMarks.experienceReady - this.performanceMarks.start,
      imageLoadTime: this.performanceMarks.imageLoaded - this.performanceMarks.start,
      hotspotsRenderTime: this.performanceMarks.hotspotsRendered - this.performanceMarks.start
    };

    console.log('📊 Performance Metrics:');
    console.log(`  Total Load: ${metrics.totalLoadTime.toFixed(0)}ms`);
    console.log(`  Image Load: ${metrics.imageLoadTime.toFixed(0)}ms`);
    console.log(`  Hotspots: ${metrics.hotspotsRenderTime.toFixed(0)}ms`);

    // Send to analytics (if available)
    if (window.gtag) {
      gtag('event', 'timing_complete', {
        name: 'immersive_experience_load',
        value: Math.round(metrics.totalLoadTime),
        event_category: 'Performance',
        event_label: this.currentCollection
      });
    }
  }
}

// Initialize experience when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const experience = new ImmersiveExperience();
    experience.init();

    // Expose globally for debugging
    window.skyyRoseExperience = experience;
  });
} else {
  const experience = new ImmersiveExperience();
  experience.init();
  window.skyyRoseExperience = experience;
}
