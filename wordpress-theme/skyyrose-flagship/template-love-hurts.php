<?php
/**
 * Template Name: Love Hurts Collection - Enchanted Ballroom
 * Description: Beauty and the Beast inspired 3D shopping experience
 *
 * @package SkyyroseTheme
 */

get_header();
?>

<div id="love-hurts-experience" class="three-scene-wrapper">
    <!-- Loading Screen -->
    <div id="loading-screen" class="loading-overlay">
        <div class="loading-content">
            <div class="enchanted-rose-loader">
                <div class="rose-spinner"></div>
                <p class="loading-text">Preparing the enchanted ballroom...</p>
                <div class="loading-progress">
                    <div class="progress-bar"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- 3D Scene Container -->
    <div id="love-hurts-scene-container" class="scene-container"></div>

    <!-- UI Overlay -->
    <div class="scene-ui-overlay">
        <!-- Navigation Menu -->
        <nav class="ballroom-navigation">
            <h1 class="collection-title">Love Hurts Collection</h1>
            <ul class="scene-nav-menu">
                <li><button type="button" class="nav-btn" data-section="ballroom">Grand Ballroom</button></li>
                <li><button type="button" class="nav-btn" data-section="rose">Enchanted Rose</button></li>
                <li><button type="button" class="nav-btn" data-section="mirror">Magic Mirror</button></li>
                <li><button type="button" class="nav-btn" data-section="windows">Stained Glass</button></li>
            </ul>
        </nav>

        <!-- Instructions -->
        <div class="scene-instructions">
            <p>
                <span class="instruction-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 3l3.057-3 11.943 12-11.943 12-3.057-3 9-9z" fill="currentColor"/></svg></span> Click and drag to explore
            </p>
            <p>
                <span class="instruction-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="#D4AF37" aria-hidden="true"><path d="M12 2l2.4 7.2H22l-6 4.8 2.4 7.2L12 16.4l-6.4 4.8 2.4-7.2-6-4.8h7.6z"/></svg></span> Click glowing products to view
            </p>
            <p>
                <span class="instruction-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="#B76E79" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span> Discover Beauty &amp; Beast Easter eggs
            </p>
        </div>

        <!-- Audio Controls -->
        <div class="audio-controls">
            <button type="button" id="toggle-audio" class="audio-btn" aria-label="Toggle Music">
                <span class="audio-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg></span>
            </button>
        </div>

        <!-- Easter Egg Counter -->
        <div class="easter-egg-tracker">
            <h3>Enchanted Objects Found</h3>
            <div class="egg-counter">
                <span id="eggs-found">0</span> / <span id="total-eggs">6</span>
            </div>
            <ul class="egg-list">
                <li data-egg="lumiere"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 2v4M12 18v4M8 6l-2-2M16 6l2-2M12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z"/><path d="M10 18h4l-1 4h-2l-1-4Z"/></svg> Lumi&egrave;re</li>
                <li data-egg="cogsworth"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> Cogsworth</li>
                <li data-egg="potts"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17 8h1a4 4 0 0 1 0 8h-1"/><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/></svg> Mrs. Potts &amp; Chip</li>
                <li data-egg="mirror"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="10" r="7"/><path d="M8 21h8M12 17v4"/></svg> Magic Mirror</li>
                <li data-egg="wardrobe"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="2" width="18" height="20" rx="2"/><path d="M12 2v20M9 12h.01M15 12h.01"/></svg> Wardrobe</li>
                <li data-egg="book"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg> Enchanted Book</li>
            </ul>
        </div>
    </div>

    <!-- Product Modal -->
    <div id="product-modal" class="enchanted-modal" style="display: none;">
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <button type="button" class="modal-close" aria-label="Close">&times;</button>

            <div class="modal-inner">
                <!-- Magic Mirror Frame -->
                <div class="mirror-frame">
                    <div class="mirror-glow"></div>

                    <div class="product-display">
                        <div id="product-image" class="product-image-container">
                            <!-- Product image loaded dynamically -->
                        </div>

                        <div class="product-info">
                            <h2 id="product-title" class="product-title" aria-hidden="true"></h2>
                            <div id="product-price" class="product-price"></div>
                            <div id="product-description" class="product-description"></div>

                            <div class="product-meta">
                                <div class="product-sku"></div>
                                <div class="product-availability"></div>
                            </div>

                            <div class="product-actions">
                                <button type="button" id="add-to-cart-btn" class="btn-enchanted btn-add-cart">
                                    <span class="btn-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="#B76E79" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
                                    Add to Cart
                                </button>
                                <button type="button" class="btn-enchanted btn-view-details">
                                    View Full Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
/* Love Hurts Collection Styles */
.three-scene-wrapper {
    position: relative;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background: #0a0a0a;
}

/* Loading Screen */
.loading-overlay {
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

.loading-overlay.fade-out {
    opacity: 0;
    pointer-events: none;
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

/* Scene Container */
.scene-container {
    width: 100%;
    height: 100%;
}

/* UI Overlay */
.scene-ui-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 10;
}

.scene-ui-overlay > * {
    pointer-events: auto;
}

/* Navigation */
.ballroom-navigation {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(10, 10, 10, 0.8);
    backdrop-filter: blur(10px);
    padding: 20px;
    border-radius: 10px;
    border: 2px solid rgba(255, 215, 0, 0.3);
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.2);
}

.collection-title {
    font-family: 'Cinzel', serif;
    font-size: 1.5rem;
    color: #FFD700;
    margin: 0 0 15px 0;
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}

.scene-nav-menu {
    list-style: none;
    padding: 0;
    margin: 0;
}

.scene-nav-menu li {
    margin-bottom: 10px;
}

.nav-btn {
    background: linear-gradient(135deg, rgba(139, 0, 0, 0.3), rgba(75, 0, 130, 0.3));
    border: 1px solid rgba(255, 215, 0, 0.5);
    color: #FFD700;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-family: 'Cinzel', serif;
    font-size: 0.9rem;
    width: 100%;
    text-align: left;
    transition: all 0.3s ease;
}

.nav-btn:hover {
    background: linear-gradient(135deg, rgba(139, 0, 0, 0.5), rgba(75, 0, 130, 0.5));
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    transform: translateX(5px);
}

/* Instructions */
.scene-instructions {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(10, 10, 10, 0.8);
    backdrop-filter: blur(10px);
    padding: 15px;
    border-radius: 10px;
    border: 2px solid rgba(255, 215, 0, 0.3);
    color: #FFD700;
    font-size: 0.9rem;
}

.scene-instructions p {
    margin: 5px 0;
}

.instruction-icon {
    margin-right: 8px;
}

/* Audio Controls */
.audio-controls {
    position: absolute;
    top: 20px;
    right: 20px;
}

.audio-btn {
    background: rgba(10, 10, 10, 0.8);
    border: 2px solid rgba(255, 215, 0, 0.5);
    color: #FFD700;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.5rem;
    transition: all 0.3s ease;
}

.audio-btn:hover {
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
    transform: scale(1.1);
}

/* Easter Egg Tracker */
.easter-egg-tracker {
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: rgba(10, 10, 10, 0.8);
    backdrop-filter: blur(10px);
    padding: 15px;
    border-radius: 10px;
    border: 2px solid rgba(255, 215, 0, 0.3);
    color: #FFD700;
    max-width: 250px;
}

.easter-egg-tracker h3 {
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    margin: 0 0 10px 0;
}

.egg-counter {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 10px;
    text-align: center;
}

.egg-list {
    list-style: none;
    padding: 0;
    margin: 0;
    font-size: 0.9rem;
}

.egg-list li {
    padding: 5px 0;
    opacity: 0.5;
    transition: opacity 0.3s ease;
}

.egg-list li.found {
    opacity: 1;
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}

/* Product Modal (Magic Mirror) */
.enchanted-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10000;
}

.modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(5px);
}

.modal-content {
    position: relative;
    width: 90%;
    max-width: 900px;
    height: 80%;
    margin: 5% auto;
    z-index: 10001;
}

.modal-close {
    position: absolute;
    top: -40px;
    right: 0;
    background: transparent;
    border: none;
    color: #FFD700;
    font-size: 2rem;
    cursor: pointer;
    z-index: 10002;
    transition: transform 0.3s ease;
}

.modal-close:hover {
    transform: scale(1.2) rotate(90deg);
}

.mirror-frame {
    position: relative;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #1a1a1a, #2a2a1a);
    border: 10px solid #FFD700;
    border-radius: 20px;
    box-shadow:
        0 0 50px rgba(255, 215, 0, 0.5),
        inset 0 0 50px rgba(255, 215, 0, 0.1);
    padding: 30px;
    overflow: auto;
}

.mirror-glow {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, rgba(255, 215, 0, 0.1), transparent);
    pointer-events: none;
    animation: mirrorPulse 3s ease-in-out infinite;
}

@keyframes mirrorPulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

.product-display {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    height: 100%;
}

.product-image-container {
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
    overflow: hidden;
}

.product-image-container img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.product-info {
    color: #FFD700;
}

.product-title {
    font-family: 'Cinzel', serif;
    font-size: 2rem;
    margin-bottom: 20px;
    text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}

.product-price {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 20px;
    color: #FF69B4;
}

.product-description {
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 20px;
    color: #e0e0e0;
}

.product-actions {
    display: flex;
    gap: 15px;
    margin-top: 30px;
}

.btn-enchanted {
    padding: 15px 30px;
    border-radius: 8px;
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid;
}

.btn-add-cart {
    background: linear-gradient(135deg, #8B0000, #4B0082);
    border-color: #FFD700;
    color: #FFD700;
}

.btn-add-cart:hover {
    background: linear-gradient(135deg, #B00000, #6B00B2);
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
    transform: translateY(-2px);
}

.btn-view-details {
    background: transparent;
    border-color: #FFD700;
    color: #FFD700;
}

.btn-view-details:hover {
    background: rgba(255, 215, 0, 0.1);
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
    .product-display {
        grid-template-columns: 1fr;
    }

    .ballroom-navigation,
    .easter-egg-tracker {
        font-size: 0.8rem;
        padding: 10px;
    }

    .collection-title {
        font-size: 1.2rem;
    }
}
</style>

<script type="module">
import LoveHurtsScene from '<?php echo get_template_directory_uri(); ?>/assets/js/three/love-hurts-scene.js';

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('love-hurts-scene-container');
    const loadingScreen = document.getElementById('loading-screen');

    // Initialize scene
    const scene = new LoveHurtsScene(container);

    // Hide loading screen after initialization
    setTimeout(() => {
        loadingScreen.classList.add('fade-out');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }, 3000);

    // Navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const section = e.target.dataset.section;
            scene.navigateToSection(section);
        });
    });

    // Product hotspot click handler
    window.addEventListener('productHotspotClick', (e) => {
        const { productId, productName } = e.detail;
        openProductModal(productId, productName);
    });

    // Modal controls
    const modal = document.getElementById('product-modal');
    const modalClose = modal.querySelector('.modal-close');
    const modalOverlay = modal.querySelector('.modal-overlay');

    modalClose.addEventListener('click', closeProductModal);
    modalOverlay.addEventListener('click', closeProductModal);

    function openProductModal(productId, productName) {
        // Fetch product data via AJAX
        fetch(`<?php echo admin_url('admin-ajax.php'); ?>?action=get_product_data&product_id=${productId}`)
            .then(res => res.json())
            .then(data => {
                // Safely set text content
                var titleEl = document.getElementById('product-title');
                titleEl.textContent = data.title || productName;
                titleEl.removeAttribute('aria-hidden');
                document.getElementById('product-price').textContent = data.price || '';
                document.getElementById('product-description').textContent = data.description || '';

                // Safely create image element
                const productImage = document.getElementById('product-image');
                productImage.textContent = ''; // Clear previous content
                if (data.image) {
                    const img = document.createElement('img');
                    img.src = data.image;
                    img.alt = data.title || productName;
                    productImage.appendChild(img);
                }

                modal.style.display = 'block';
            })
            .catch(() => {
                // Product load failed — panel remains in loading state.
            });
    }

    function closeProductModal() {
        modal.style.display = 'none';
        document.getElementById('product-title').setAttribute('aria-hidden', 'true');
    }

    // Audio toggle
    document.getElementById('toggle-audio').addEventListener('click', function() {
        var icon = this.querySelector('.audio-icon');
        var isMuted = icon.getAttribute('data-muted') === 'true';
        icon.setAttribute('data-muted', isMuted ? 'false' : 'true');
        icon.innerHTML = isMuted
            ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>'
            : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>';
    });
});
</script>

<?php get_footer(); ?>
