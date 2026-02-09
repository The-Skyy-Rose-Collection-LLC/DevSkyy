# Love Hurts Collection - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Three.js
```bash
npm install three
```

### Step 2: Files Already Created
All files are ready in your theme:
- `/assets/js/three/love-hurts-scene.js` - Main scene
- `/assets/js/three/scene-manager.js` - Scene lifecycle manager
- `/assets/js/three/hotspot-system.js` - Product interaction system
- `/assets/js/three/init-love-hurts.js` - Quick setup helper
- `/template-love-hurts.php` - WordPress template

### Step 3: Enqueue Three.js in WordPress
Add to `functions.php`:

```php
function skyyrose_enqueue_threejs() {
    // Three.js core
    wp_enqueue_script(
        'three-js',
        get_template_directory_uri() . '/node_modules/three/build/three.module.js',
        [],
        null,
        true
    );

    // Only load on Love Hurts page
    if (is_page_template('template-love-hurts.php')) {
        wp_enqueue_script(
            'love-hurts-scene',
            get_template_directory_uri() . '/assets/js/three/love-hurts-scene.js',
            ['three-js'],
            null,
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_threejs');
```

### Step 4: Create WordPress Page
1. Go to WordPress Admin → Pages → Add New
2. Give it a title: "Love Hurts Collection"
3. In the Template dropdown (right sidebar), select: **"Love Hurts Collection - Enchanted Ballroom"**
4. Publish!

---

## Usage

### Basic Setup (Automatic)
The template file handles everything automatically! Just visit the page.

### Custom Setup (Manual Control)
If you want more control, use the init helper:

```javascript
import { quickStart } from './assets/js/three/init-love-hurts.js';

// One line to start everything
const { scene, modal, tracker } = quickStart('my-container-id');

// Now you have access to:
// - scene: The Three.js scene instance
// - modal: Product modal controller
// - tracker: Easter egg tracker
```

### Advanced Setup (Full Control)

```javascript
import { initLoveHurtsExperience, createProductModal, createEasterEggTracker }
    from './assets/js/three/init-love-hurts.js';

// Initialize scene with options
const scene = initLoveHurtsExperience('#my-container', {
    autoStart: true,
    showLoading: true,
    loadingDuration: 3000,
    enableAudio: true,
    audioUrl: '/path/to/beauty-beast-waltz.mp3',
    onSceneReady: (scene) => {
        console.log('Scene is ready!');
        // Navigate to rose on load
        scene.navigateToSection('rose');
    },
    onProductClick: (detail, scene) => {
        console.log('Product clicked:', detail);
    }
});

// Create product modal
const modal = createProductModal({
    endpoint: '/wp-admin/admin-ajax.php',
    onAddToCart: (productData) => {
        // Add to WooCommerce cart
        addToCart(productData.productId);
    },
    onViewDetails: (productData) => {
        // Navigate to product page
        window.location.href = `/product/${productData.productId}`;
    }
});

// Listen for product clicks
window.addEventListener('productHotspotClick', (e) => {
    modal.open(e.detail.productId, e.detail.productName);
});
```

---

## Integrating WooCommerce Products

### Method 1: AJAX Handler (Add to functions.php)

```php
add_action('wp_ajax_get_product_data', 'skyyrose_get_product_data');
add_action('wp_ajax_nopriv_get_product_data', 'skyyrose_get_product_data');

function skyyrose_get_product_data() {
    if (!isset($_GET['product_id'])) {
        wp_send_json_error('No product ID provided');
    }

    $product_id = intval($_GET['product_id']);
    $product = wc_get_product($product_id);

    if (!$product) {
        wp_send_json_error('Product not found');
    }

    wp_send_json([
        'title' => $product->get_name(),
        'price' => $product->get_price_html(),
        'description' => $product->get_short_description(),
        'image' => wp_get_attachment_url($product->get_image_id()),
        'url' => get_permalink($product_id),
        'in_stock' => $product->is_in_stock()
    ]);
}
```

### Method 2: Update Product Hotspots
Edit line ~1121 in `love-hurts-scene.js`:

```javascript
createProductHotspots() {
    // Replace with your actual WooCommerce product IDs
    const productData = [
        { name: 'Gothic Rose Necklace', pos: [-20, 2, -10], id: '123' },
        { name: 'Enchanted Earrings', pos: [-20, 2, 0], id: '124' },
        { name: 'Midnight Ring', pos: [-20, 2, 10], id: '125' },
        { name: 'Royal Bracelet', pos: [20, 2, -10], id: '126' },
        { name: 'Crimson Pendant', pos: [20, 2, 0], id: '127' },
        { name: 'Belle\'s Rose Ring', pos: [20, 2, 10], id: '128' }
    ];
    // ... rest of function
}
```

---

## Camera Navigation

Navigate between ballroom sections programmatically:

```javascript
// Get the scene instance
const scene = document.querySelector('#love-hurts-scene-container').__loveHurtsScene;

// Navigate to different sections
scene.navigateToSection('ballroom');  // Overview
scene.navigateToSection('rose');      // Close-up of rose
scene.navigateToSection('mirror');    // Magic mirror view
scene.navigateToSection('windows');   // Stained glass windows
```

Or add navigation buttons in your template:

```html
<button onclick="navigateTo('rose')">View Rose</button>

<script>
function navigateTo(section) {
    const container = document.getElementById('love-hurts-scene-container');
    if (container.__loveHurtsScene) {
        container.__loveHurtsScene.navigateToSection(section);
    }
}
</script>
```

---

## Adding Background Music

### Option 1: In Template
```javascript
import LoveHurtsScene from '...';

const scene = new LoveHurtsScene(container);

// Create audio
const audio = new Audio('/wp-content/themes/skyyrose/assets/audio/beauty-beast.mp3');
audio.loop = true;
audio.volume = 0.3;

document.getElementById('toggle-audio').addEventListener('click', () => {
    if (audio.paused) {
        audio.play();
    } else {
        audio.pause();
    }
});
```

### Option 2: Using Init Helper
```javascript
import { initLoveHurtsExperience } from './init-love-hurts.js';

const scene = initLoveHurtsExperience('#container', {
    enableAudio: true,
    audioUrl: '/path/to/music.mp3'
});

// Control audio
scene.audioManager.play();
scene.audioManager.pause();
scene.audioManager.toggle();
scene.audioManager.setVolume(0.5);
```

---

## Easter Egg System

### Track Easter Eggs
The template includes an easter egg tracker. To mark eggs as found:

```javascript
// In your scene interaction logic
scene.onEasterEggClick = (eggName) => {
    const tracker = document.querySelector('.easter-egg-tracker');
    const eggItem = tracker.querySelector(`[data-egg="${eggName}"]`);

    if (eggItem && !eggItem.classList.contains('found')) {
        eggItem.classList.add('found');

        const foundCount = tracker.querySelectorAll('.found').length;
        tracker.querySelector('#eggs-found').textContent = foundCount;

        // Show celebration
        if (foundCount === 6) {
            alert('You found all the enchanted objects!');
        }
    }
};
```

---

## Customization

### Change Colors
Edit the `colors` object in `love-hurts-scene.js` (line ~42):

```javascript
this.colors = {
    deepCrimson: 0xFF0000,    // Brighter red
    royalGold: 0xFFD700,      // Keep gold
    richPurple: 0x800080,     // Different purple
    // ... etc
};
```

### Adjust Particle Count
For better mobile performance:

```javascript
// In createFloatingCandles() - line ~413
const candleCount = window.innerWidth < 768 ? 30 : 100;

// In createRosePetalParticles() - line ~1007
const particleCount = window.innerWidth < 768 ? 50 : 200;
```

### Modify Hotspot Positions
```javascript
// In createProductHotspots() - line ~1121
const productData = [
    { name: 'Product', pos: [x, y, z], id: 'ID' },
    // x: left/right (-25 to 25)
    // y: height (0 to 10)
    // z: front/back (-15 to 15)
];
```

---

## Performance Optimization

### For Mobile Devices
Add to `love-hurts-scene.js` constructor:

```javascript
const isMobile = window.innerWidth < 768;

// Reduce quality on mobile
this.renderer.setPixelRatio(isMobile ? 1 : Math.min(window.devicePixelRatio, 2));

// Disable shadows on mobile
this.renderer.shadowMap.enabled = !isMobile;

// Reduce particles
this.particleMultiplier = isMobile ? 0.3 : 1;
```

### Disable Post-Processing
Comment out bloom pass in `setupPostProcessing()`:

```javascript
// const bloomPass = new UnrealBloomPass(...);
// this.composer.addPass(bloomPass);
```

---

## Troubleshooting

### Scene is Black
- Check browser console for errors
- Verify Three.js is loaded: `console.log(typeof THREE)`
- Check that lights are added to scene

### Products Don't Click
- Verify AJAX endpoint is correct
- Check product IDs exist in WooCommerce
- Look for JavaScript errors in console

### Performance Issues
- Reduce particle counts
- Lower shadow map sizes (line ~69, 411, etc.)
- Disable bloom effect
- Reduce candle count

### Modal Won't Open
- Check that product endpoint returns valid JSON
- Verify modal HTML exists in DOM
- Check for console errors

---

## Next Steps

1. **Add Real Products**: Replace placeholder product IDs with your WooCommerce products
2. **Customize Colors**: Match your brand colors
3. **Add Music**: Find a Beauty & Beast inspired instrumental
4. **Mobile Optimize**: Test on phones and adjust particle counts
5. **Analytics**: Track user interactions and product clicks
6. **A/B Test**: Compare 3D experience vs traditional product pages

---

## Support

For issues:
1. Check browser console for errors
2. Verify Three.js version (r150+)
3. Test in different browsers
4. Check this documentation

**This is your FLAGSHIP experience - make it shine!** ✨🌹
