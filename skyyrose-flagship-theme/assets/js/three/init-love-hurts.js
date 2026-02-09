/**
 * Love Hurts Scene Initialization Script
 * Quick setup helper for integrating the enchanted ballroom
 */

import LoveHurtsScene from './love-hurts-scene.js';
import { sceneManager } from './scene-manager.js';

/**
 * Initialize the Love Hurts experience
 * @param {string|HTMLElement} containerSelector - Container element or selector
 * @param {Object} options - Configuration options
 */
export function initLoveHurtsExperience(containerSelector, options = {}) {
    const defaults = {
        autoStart: true,
        showLoading: true,
        loadingDuration: 3000,
        enableAudio: false,
        audioUrl: null,
        productEndpoint: '/wp-admin/admin-ajax.php',
        onSceneReady: null,
        onProductClick: null,
        onEasterEggFound: null
    };

    const config = { ...defaults, ...options };

    // Get container
    const container = typeof containerSelector === 'string'
        ? document.querySelector(containerSelector)
        : containerSelector;

    if (!container) {
        console.error('Love Hurts: Container not found:', containerSelector);
        return null;
    }

    // Show loading screen
    let loadingScreen;
    if (config.showLoading) {
        loadingScreen = createLoadingScreen();
        container.appendChild(loadingScreen);
    }

    // Initialize scene
    const scene = new LoveHurtsScene(container);

    // Register with scene manager
    sceneManager.registerScene('love-hurts', LoveHurtsScene, container);

    // Setup audio if enabled
    if (config.enableAudio && config.audioUrl) {
        setupAudio(config.audioUrl, scene);
    }

    // Hide loading screen
    if (config.showLoading) {
        setTimeout(() => {
            loadingScreen.classList.add('fade-out');
            setTimeout(() => {
                container.removeChild(loadingScreen);
            }, 500);

            if (config.onSceneReady) {
                config.onSceneReady(scene);
            }
        }, config.loadingDuration);
    } else if (config.onSceneReady) {
        config.onSceneReady(scene);
    }

    // Setup product interaction
    if (config.onProductClick) {
        window.addEventListener('productHotspotClick', (e) => {
            config.onProductClick(e.detail, scene);
        });
    }

    // Setup easter egg tracking
    if (config.onEasterEggFound) {
        scene.onEasterEggFound = (eggName) => {
            config.onEasterEggFound(eggName, scene);
        };
    }

    return scene;
}

/**
 * Create loading screen HTML (using safe DOM methods)
 */
function createLoadingScreen() {
    const loading = document.createElement('div');
    loading.className = 'love-hurts-loading';

    const content = document.createElement('div');
    content.className = 'loading-content';

    const spinner = document.createElement('div');
    spinner.className = 'rose-spinner';

    const text = document.createElement('p');
    text.className = 'loading-text';
    text.textContent = 'Entering the enchanted ballroom...';

    const progressContainer = document.createElement('div');
    progressContainer.className = 'loading-progress';

    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';

    progressContainer.appendChild(progressBar);
    content.appendChild(spinner);
    content.appendChild(text);
    content.appendChild(progressContainer);
    loading.appendChild(content);

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .love-hurts-loading {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a0a0a 50%, #0a0a1a 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            transition: opacity 0.5s ease-out;
        }
        .love-hurts-loading.fade-out {
            opacity: 0;
        }
        .loading-content {
            text-align: center;
            color: #FFD700;
        }
        .rose-spinner {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            border: 4px solid rgba(255, 215, 0, 0.2);
            border-top: 4px solid #FFD700;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .loading-text {
            font-family: 'Cinzel', serif;
            font-size: 1.2rem;
            margin: 20px 0;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }
        .loading-progress {
            width: 300px;
            height: 4px;
            background: rgba(255, 215, 0, 0.2);
            border-radius: 2px;
            overflow: hidden;
            margin: 20px auto 0;
        }
        .progress-bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #FFD700, #FF69B4);
            animation: loadProgress 3s ease-out forwards;
        }
        @keyframes loadProgress {
            to { width: 100%; }
        }
    `;
    document.head.appendChild(style);

    return loading;
}

/**
 * Setup background audio
 */
function setupAudio(audioUrl, scene) {
    const audio = new Audio(audioUrl);
    audio.loop = true;
    audio.volume = 0.3;

    // Create audio manager
    const audioManager = {
        audio,
        isPlaying: false,
        toggle() {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        },
        play() {
            this.audio.play().then(() => {
                this.isPlaying = true;
            }).catch(err => {
                console.warn('Audio autoplay blocked:', err);
            });
        },
        pause() {
            this.audio.pause();
            this.isPlaying = false;
        },
        setVolume(volume) {
            this.audio.volume = Math.max(0, Math.min(1, volume));
        }
    };

    // Attach to scene
    scene.audioManager = audioManager;

    return audioManager;
}

/**
 * Create product modal (using safe DOM methods)
 */
export function createProductModal(options = {}) {
    const defaults = {
        onAddToCart: null,
        onViewDetails: null,
        endpoint: '/wp-admin/admin-ajax.php'
    };

    const config = { ...defaults, ...options };

    // Create modal structure
    const modal = document.createElement('div');
    modal.id = 'love-hurts-product-modal';
    modal.className = 'enchanted-modal';
    modal.style.display = 'none';

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'modal-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.textContent = '×';

    const modalInner = document.createElement('div');
    modalInner.className = 'modal-inner';

    const mirrorFrame = document.createElement('div');
    mirrorFrame.className = 'mirror-frame';

    const mirrorGlow = document.createElement('div');
    mirrorGlow.className = 'mirror-glow';

    const productDisplay = document.createElement('div');
    productDisplay.className = 'product-display';

    const imageContainer = document.createElement('div');
    imageContainer.id = 'product-image';
    imageContainer.className = 'product-image-container';

    const productInfo = document.createElement('div');
    productInfo.className = 'product-info';

    const title = document.createElement('h2');
    title.id = 'product-title';
    title.className = 'product-title';

    const price = document.createElement('div');
    price.id = 'product-price';
    price.className = 'product-price';

    const description = document.createElement('div');
    description.id = 'product-description';
    description.className = 'product-description';

    const actions = document.createElement('div');
    actions.className = 'product-actions';

    const addToCartBtn = document.createElement('button');
    addToCartBtn.id = 'add-to-cart-btn';
    addToCartBtn.className = 'btn-enchanted btn-add-cart';

    const btnIcon = document.createElement('span');
    btnIcon.className = 'btn-icon';
    btnIcon.textContent = '🌹';
    addToCartBtn.appendChild(btnIcon);
    addToCartBtn.appendChild(document.createTextNode(' Add to Cart'));

    const viewDetailsBtn = document.createElement('button');
    viewDetailsBtn.id = 'view-details-btn';
    viewDetailsBtn.className = 'btn-enchanted btn-view-details';
    viewDetailsBtn.textContent = 'View Full Details';

    // Build DOM tree
    actions.appendChild(addToCartBtn);
    actions.appendChild(viewDetailsBtn);

    productInfo.appendChild(title);
    productInfo.appendChild(price);
    productInfo.appendChild(description);
    productInfo.appendChild(actions);

    productDisplay.appendChild(imageContainer);
    productDisplay.appendChild(productInfo);

    mirrorFrame.appendChild(mirrorGlow);
    mirrorFrame.appendChild(productDisplay);

    modalInner.appendChild(mirrorFrame);
    modalContent.appendChild(closeBtn);
    modalContent.appendChild(modalInner);

    modal.appendChild(overlay);
    modal.appendChild(modalContent);

    document.body.appendChild(modal);

    // Event handlers
    const close = () => {
        modal.style.display = 'none';
    };

    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', close);

    if (config.onAddToCart) {
        addToCartBtn.addEventListener('click', () => {
            const productData = modal.dataset;
            config.onAddToCart(productData);
        });
    }

    if (config.onViewDetails) {
        viewDetailsBtn.addEventListener('click', () => {
            const productData = modal.dataset;
            config.onViewDetails(productData);
        });
    }

    // Return modal controller
    return {
        element: modal,
        open(productId, productName) {
            fetch(`${config.endpoint}?action=get_product_data&product_id=${productId}`)
                .then(res => res.json())
                .then(data => {
                    modal.dataset.productId = productId;
                    modal.dataset.productName = data.title || productName;

                    title.textContent = data.title || productName;
                    price.textContent = data.price || '';
                    description.textContent = data.description || '';

                    imageContainer.textContent = '';
                    if (data.image) {
                        const img = document.createElement('img');
                        img.src = data.image;
                        img.alt = data.title || productName;
                        imageContainer.appendChild(img);
                    }

                    modal.style.display = 'block';
                })
                .catch(err => {
                    console.error('Failed to load product:', err);
                });
        },
        close
    };
}

/**
 * Easter egg tracker (using safe DOM methods)
 */
export function createEasterEggTracker(eggs = []) {
    const tracker = document.createElement('div');
    tracker.className = 'easter-egg-tracker';

    const heading = document.createElement('h3');
    heading.textContent = 'Enchanted Objects Found';

    const counter = document.createElement('div');
    counter.className = 'egg-counter';

    const foundSpan = document.createElement('span');
    foundSpan.id = 'eggs-found';
    foundSpan.textContent = '0';

    const totalSpan = document.createElement('span');
    totalSpan.id = 'total-eggs';
    totalSpan.textContent = eggs.length.toString();

    counter.appendChild(foundSpan);
    counter.appendChild(document.createTextNode(' / '));
    counter.appendChild(totalSpan);

    const list = document.createElement('ul');
    list.className = 'egg-list';

    eggs.forEach(egg => {
        const item = document.createElement('li');
        item.setAttribute('data-egg', egg.id);
        item.textContent = `${egg.icon} ${egg.name}`;
        list.appendChild(item);
    });

    tracker.appendChild(heading);
    tracker.appendChild(counter);
    tracker.appendChild(list);

    const found = new Set();

    return {
        element: tracker,
        markFound(eggId) {
            if (!found.has(eggId)) {
                found.add(eggId);
                const item = tracker.querySelector(`[data-egg="${eggId}"]`);
                if (item) {
                    item.classList.add('found');
                }
                foundSpan.textContent = found.size.toString();
            }
        },
        reset() {
            found.clear();
            tracker.querySelectorAll('.egg-list li').forEach(item => {
                item.classList.remove('found');
            });
            foundSpan.textContent = '0';
        },
        getProgress() {
            return {
                found: found.size,
                total: eggs.length,
                percentage: (found.size / eggs.length) * 100
            };
        }
    };
}

/**
 * Quick start helper
 */
export function quickStart(containerId = 'love-hurts-scene-container') {
    const scene = initLoveHurtsExperience(`#${containerId}`, {
        autoStart: true,
        showLoading: true,
        onSceneReady: (scene) => {
            console.log('Love Hurts scene ready!', scene);
        }
    });

    const modal = createProductModal({
        onAddToCart: (productData) => {
            console.log('Add to cart:', productData);
            // Implement WooCommerce add to cart
        }
    });

    const easterEggs = [
        { id: 'lumiere', name: 'Lumière', icon: '🕯️' },
        { id: 'cogsworth', name: 'Cogsworth', icon: '🕐' },
        { id: 'potts', name: 'Mrs. Potts & Chip', icon: '🫖' },
        { id: 'mirror', name: 'Magic Mirror', icon: '🪞' },
        { id: 'wardrobe', name: 'Wardrobe', icon: '🚪' },
        { id: 'book', name: 'Enchanted Book', icon: '📖' }
    ];

    const tracker = createEasterEggTracker(easterEggs);
    document.body.appendChild(tracker.element);

    window.addEventListener('productHotspotClick', (e) => {
        modal.open(e.detail.productId, e.detail.productName);
    });

    return { scene, modal, tracker };
}

export default {
    initLoveHurtsExperience,
    createProductModal,
    createEasterEggTracker,
    quickStart
};
