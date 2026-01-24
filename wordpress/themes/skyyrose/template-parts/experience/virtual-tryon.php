<?php
/**
 * Template Part: Virtual Try-On Interface
 *
 * AI-powered virtual try-on using MediaPipe for pose detection
 * and real-time clothing overlay.
 *
 * @package SkyyRose
 * @version 2.0.0
 *
 * Expected variables:
 * @var int    $product_id    - WooCommerce product ID (optional)
 * @var array  $clothing_item - Clothing data array (optional)
 * @var string $collection    - Collection slug for styling
 */

defined('ABSPATH') || exit;

// Get product data if ID provided
$product = null;
$clothing_data = [];

if (!empty($product_id)) {
    $product = wc_get_product($product_id);
    if ($product) {
        $clothing_data = [
            'id'    => $product_id,
            'name'  => $product->get_name(),
            'image' => wp_get_attachment_image_url($product->get_image_id(), 'large'),
            'type'  => get_post_meta($product_id, '_skyyrose_clothing_type', true) ?: 'shirt',
            'sizes' => $product->get_attribute('pa_size') ? explode(', ', $product->get_attribute('pa_size')) : ['XS', 'S', 'M', 'L', 'XL'],
        ];
    }
} elseif (!empty($clothing_item)) {
    $clothing_data = $clothing_item;
}

$collection = $collection ?? 'signature';
?>

<div class="virtual-tryon-section" data-collection="<?php echo esc_attr($collection); ?>">
    <div class="container">
        <header class="section-header gsap-fade-up">
            <span class="section-eyebrow">Virtual Try-On</span>
            <h2 class="section-title">See It On You</h2>
            <p class="section-subtitle">
                Use your camera to virtually try on this piece and find your perfect fit.
            </p>
        </header>

        <!-- Try-On Container -->
        <div class="tryon-container glass-card" id="tryonContainer">
            <!-- Permission Request -->
            <div class="tryon-permission" id="tryonPermission">
                <div class="permission-content">
                    <div class="permission-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                            <circle cx="12" cy="13" r="4"/>
                        </svg>
                    </div>
                    <h3>Enable Camera Access</h3>
                    <p>We need camera access to show how this piece looks on you. Your video stays on your device and is never uploaded.</p>
                    <button type="button" class="btn btn--primary btn--lg" id="enableCameraBtn">
                        Enable Camera
                    </button>
                    <p class="permission-note">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                        Privacy-first: All processing happens locally
                    </p>
                </div>
            </div>

            <!-- Try-On Viewer (hidden until camera enabled) -->
            <div class="tryon-viewer" id="tryonViewer" style="display: none;">
                <!-- Video/Canvas will be injected here by JS -->
            </div>

            <!-- Controls -->
            <div class="tryon-controls" id="tryonControls" style="display: none;">
                <!-- Size Recommendation -->
                <div class="tryon-size-recommendation" id="sizeRecommendation">
                    <span class="size-label">Recommended Size:</span>
                    <span class="size-value" id="recommendedSize">--</span>
                </div>

                <!-- Clothing Selector (if multiple items) -->
                <?php if (!empty($clothing_data['id'])) : ?>
                <div class="tryon-product-info">
                    <img
                        src="<?php echo esc_url($clothing_data['image']); ?>"
                        alt="<?php echo esc_attr($clothing_data['name']); ?>"
                        class="tryon-product-thumb"
                    >
                    <div class="tryon-product-details">
                        <h4><?php echo esc_html($clothing_data['name']); ?></h4>
                        <div class="size-selector">
                            <?php foreach ($clothing_data['sizes'] as $size) : ?>
                                <button type="button" class="size-btn" data-size="<?php echo esc_attr($size); ?>">
                                    <?php echo esc_html($size); ?>
                                </button>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Action Buttons -->
                <div class="tryon-actions">
                    <button type="button" class="btn btn--secondary" id="takeSnapshotBtn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                            <circle cx="12" cy="13" r="4"/>
                        </svg>
                        Take Photo
                    </button>
                    <button type="button" class="btn btn--primary" id="addToCartBtn" data-product-id="<?php echo esc_attr($clothing_data['id'] ?? ''); ?>">
                        Add to Cart
                    </button>
                    <button type="button" class="btn btn--ghost" id="closeTryonBtn">
                        Close
                    </button>
                </div>
            </div>

            <!-- Loading State -->
            <div class="tryon-loading" id="tryonLoading" style="display: none;">
                <div class="loading-spinner loading-spinner--<?php echo esc_attr($collection); ?>"></div>
                <p>Initializing AI pose detection...</p>
            </div>
        </div>

        <!-- Gesture Hints -->
        <div class="tryon-hints gsap-fade-up">
            <h4>Gesture Controls</h4>
            <div class="hints-grid">
                <div class="hint">
                    <span class="hint-icon">&#x1F44C;</span>
                    <span class="hint-text">Pinch to zoom</span>
                </div>
                <div class="hint">
                    <span class="hint-icon">&#x1F44B;</span>
                    <span class="hint-text">Swipe to rotate</span>
                </div>
                <div class="hint">
                    <span class="hint-icon">&#x270B;</span>
                    <span class="hint-text">Open palm to reset</span>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('tryonContainer');
    const permission = document.getElementById('tryonPermission');
    const viewer = document.getElementById('tryonViewer');
    const controls = document.getElementById('tryonControls');
    const loading = document.getElementById('tryonLoading');
    const enableBtn = document.getElementById('enableCameraBtn');
    const snapshotBtn = document.getElementById('takeSnapshotBtn');
    const closeBtn = document.getElementById('closeTryonBtn');
    const sizeDisplay = document.getElementById('recommendedSize');

    // Clothing data from PHP
    const clothingData = <?php echo wp_json_encode($clothing_data); ?>;

    // Enable camera button
    if (enableBtn) {
        enableBtn.addEventListener('click', async function() {
            permission.style.display = 'none';
            loading.style.display = 'flex';

            try {
                // Initialize virtual try-on
                if (typeof window.SkyyRoseVirtualTryOn !== 'undefined') {
                    await window.SkyyRoseVirtualTryOn.init({
                        container: viewer,
                        onPoseUpdate: function(data) {
                            // Update size recommendation
                            if (data.bodyMeasurements && sizeDisplay) {
                                sizeDisplay.textContent = data.bodyMeasurements.estimatedSize;
                                sizeDisplay.parentElement.classList.add('is-visible');
                            }
                        }
                    });

                    // Set clothing item
                    if (clothingData && clothingData.image) {
                        window.SkyyRoseVirtualTryOn.setClothing({
                            image: clothingData.image,
                            type: clothingData.type || 'shirt'
                        });
                    }

                    loading.style.display = 'none';
                    viewer.style.display = 'block';
                    controls.style.display = 'flex';
                } else {
                    throw new Error('Virtual try-on module not loaded');
                }
            } catch (error) {
                console.error('Failed to initialize try-on:', error);
                loading.style.display = 'none';
                permission.style.display = 'flex';
                permission.querySelector('p').textContent = 'Failed to access camera. Please check permissions and try again.';
            }
        });
    }

    // Take snapshot
    if (snapshotBtn) {
        snapshotBtn.addEventListener('click', function() {
            if (typeof window.SkyyRoseVirtualTryOn !== 'undefined') {
                const dataUrl = window.SkyyRoseVirtualTryOn.takeSnapshot();

                // Create download link
                const link = document.createElement('a');
                link.download = 'skyyrose-tryon-' + Date.now() + '.png';
                link.href = dataUrl;
                link.click();
            }
        });
    }

    // Close try-on
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            if (typeof window.SkyyRoseVirtualTryOn !== 'undefined') {
                window.SkyyRoseVirtualTryOn.stop();
            }
            viewer.style.display = 'none';
            controls.style.display = 'none';
            permission.style.display = 'flex';
        });
    }

    // Size button selection
    const sizeBtns = container.querySelectorAll('.size-btn');
    sizeBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            sizeBtns.forEach(function(b) { b.classList.remove('is-active'); });
            this.classList.add('is-active');
        });
    });
});
</script>

<style>
.virtual-tryon-section {
    padding: 4rem 0;
    background: var(--bg-darker, #050505);
}

.tryon-container {
    position: relative;
    max-width: 1000px;
    margin: 2rem auto 0;
    min-height: 500px;
    border-radius: 20px;
    overflow: hidden;
}

.tryon-permission {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 500px;
    padding: 3rem;
    text-align: center;
}

.permission-content {
    max-width: 400px;
}

.permission-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100px;
    height: 100px;
    margin-bottom: 1.5rem;
    background: rgba(183, 110, 121, 0.1);
    border-radius: 50%;
    color: var(--love-hurts, #B76E79);
}

.permission-content h3 {
    margin: 0 0 1rem;
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
}

.permission-content p {
    margin: 0 0 1.5rem;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.6;
}

.permission-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 1rem;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
}

.tryon-viewer {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #0A0A0A;
}

.tryon-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.5rem;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
}

.tryon-size-recommendation {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    background: var(--signature-gold, #D4AF37);
    border-radius: 30px;
    color: #0A0A0A;
    font-weight: 600;
    opacity: 0;
    transition: opacity 0.3s;
}

.tryon-size-recommendation.is-visible {
    opacity: 1;
}

.tryon-product-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.tryon-product-thumb {
    width: 60px;
    height: 75px;
    object-fit: cover;
    border-radius: 8px;
}

.tryon-product-details h4 {
    margin: 0 0 0.5rem;
    font-size: 0.9rem;
}

.size-selector {
    display: flex;
    gap: 6px;
}

.size-btn {
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: white;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
}

.size-btn:hover,
.size-btn.is-active {
    background: var(--love-hurts, #B76E79);
    border-color: var(--love-hurts, #B76E79);
}

.tryon-actions {
    display: flex;
    gap: 10px;
}

.tryon-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 500px;
}

.tryon-loading p {
    margin-top: 1rem;
    color: rgba(255, 255, 255, 0.6);
}

.tryon-hints {
    max-width: 600px;
    margin: 2rem auto 0;
    text-align: center;
}

.tryon-hints h4 {
    margin: 0 0 1rem;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 2px;
}

.hints-grid {
    display: flex;
    justify-content: center;
    gap: 2rem;
}

.hint {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.hint-icon {
    font-size: 2rem;
}

.hint-text {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
}

@media (max-width: 768px) {
    .tryon-controls {
        flex-direction: column;
        text-align: center;
    }

    .tryon-actions {
        width: 100%;
        flex-direction: column;
    }

    .hints-grid {
        flex-direction: column;
        gap: 1rem;
    }
}
</style>
