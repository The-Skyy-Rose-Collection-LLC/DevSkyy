# Ralph Loop Handoff - Immersive WordPress Features

**Date**: 2026-02-02
**Status**: Ready for Ralph Loop Execution

---

## ✅ COMPLETED (Manual Build)

### Foundation (Phase 1)
- ✅ Task #18: Header with mega menu, search modal, icons
- ✅ Task #19: Footer with newsletter, comprehensive links
- ✅ Base collection template with product catalog

---

## 🎯 REFERENCE SITE: drakerelated.com

**CRITICAL**: Use drakerelated.com as the quality/execution benchmark!

### Key Learnings from Drake Related:

**Room-Based Navigation**:
- Multiple interconnected 3D spaces (Studio, Bedroom, Lounge, Pool, Kitchen)
- React Router with lazy-loaded route modules
- NOT a continuous space, but distinct environments
- Smooth transitions between rooms

**Interactive Hotspots**:
- Beacon-based markers with x/y percentage coordinates
- Directional indicators ("left", "right")
- Contextual labels ("Enter Studio")
- Click-away modality system
- Navigation arrows guide between rooms

**Product Integration** (Drake uses Shopify - WE USE WOOCOMMERCE):
- Products tied to collections by album/project
- **Backend: WooCommerce (NOT Shopify)**
- **Use WooCommerce REST API for product data**
- **Cart: WooCommerce cart system (wc_get_cart_url, WC()->cart)**
- Gallery components with configurable timing
- Cart state management throughout experience
- **Integration via WordPress + WooCommerce hooks**

**Performance**:
- Code splitting for route-specific loading
- Lazy route discovery with manifest architecture
- Optimized image delivery (Shopify CDN, WebP)
- Desktop vs. mobile gallery systems

**UX Flow**:
- Guided spatial exploration model
- Visual storytelling over traditional categorization
- Thematic rooms with products, hotspots, media
- Immersive brand environment

**APPLY THIS LEVEL OF DETAIL TO SKYYROSE COLLECTIONS!**

---

## ⚠️ CRITICAL: WooCommerce Integration (NOT Shopify)

**Platform**: WordPress + WooCommerce (NOT Shopify)

### Product Data Fetching:
```php
// WooCommerce Query
$args = [
    'post_type' => 'product',
    'posts_per_page' => -1,
    'meta_query' => [
        [
            'key' => '_skyyrose_collection',
            'value' => 'black-rose', // or 'love-hurts', 'signature'
            'compare' => '='
        ]
    ]
];
$products = new WP_Query($args);
```

### Cart Integration:
```javascript
// Add to cart via AJAX
fetch(ajaxurl, {
    method: 'POST',
    body: formData // action: woocommerce_ajax_add_to_cart
})
```

### Product Hotspots in 3D:
- Fetch WooCommerce products on page load
- Create 3D hotspots with product data (ID, name, price, image)
- Click hotspot → WooCommerce add to cart
- Cart badge updates via WooCommerce hooks

**Reference for WooCommerce patterns**: `/wordpress-ops` skill and Context7

---

## 🚀 READY FOR RALPH LOOP

### Complex Immersive Features

Ralph Loop should execute these tasks using the specified tools AND drakerelated.com execution quality:

#### **Task #1: BLACK ROSE Interactive Experience**
**Location**: `wordpress-theme/skyyrose-2025/template-collection.php`

**CRITICAL**: This is an INTERACTIVE IMMERSIVE PAGE, not just a 3D viewer!

**Instructions**:
1. Add full-page interactive section ABOVE `.collection-hero` div
2. **Interactive Three.js Scene**:
   - Gothic rose garden with clickable roses
   - **INTERACTIVE**: Click roses to view products
   - **INTERACTIVE**: Drag to explore garden
   - **INTERACTIVE**: Hover roses for glow effects
   - Night sky with moving clouds (shader/particles)
   - Falling petals respond to mouse movement
   - Rotating BLACK ROSE logo (clickable to return to start)
   - Product hotspots throughout the garden
   - Height: 100vh, full-width
   - OrbitControls for free camera movement
3. **Interactive Elements**:
   - Clickable product pedestals in the garden
   - Product popup cards on click (name, price, quick view)
   - Minimap showing garden layout
   - "Explore Mode" toggle (free roam vs guided tour)
   - Sound effects (optional, with mute toggle)
   - Progress indicator (X of Y products discovered)
4. **User Interactions**:
   - Mouse: Click roses, drag to rotate camera, scroll to zoom
   - Touch: Tap products, pinch to zoom, swipe to rotate
   - Keyboard: Arrow keys to navigate
5. Use existing `src/collections/BlackRoseExperience.ts` as reference but ADD interactivity
6. Mobile: Touch-optimized, reduced particles, larger hitboxes

**Colors**: #1a1a1a, #ffffff, #8b0000, metallic silver

**Files to Modify**:
- `wordpress-theme/skyyrose-2025/template-collection.php` (add 3D container)
- `wordpress-theme/skyyrose-2025/assets/js/black-rose-scene.js` (create)
- `wordpress-theme/skyyrose-2025/functions.php` (enqueue scripts)

**Tools**: Use `/3d-generation` for models, Context7 for Three.js docs, Serena for file ops

---

#### **Task #2: LOVE HURTS Interactive Castle Experience**
**Location**: Same template, conditional based on collection

**CRITICAL**: Fully INTERACTIVE castle exploration!

**Instructions**:
1. **Interactive Enchanted Castle Scene**:
   - Gothic castle interior with multiple rooms
   - **INTERACTIVE**: Click to explore different rooms
   - **INTERACTIVE**: Walk through castle (WASD or click to move)
   - **INTERACTIVE**: Click candelabras to light/dim rooms
   - Enchanted rose under glass dome (centerpiece)
2. **Central Rose Interaction**:
   - Click rose to see petal animation
   - Each fallen petal reveals a product
   - Hover petals for product preview
   - Click petal to view full product details
3. **Castle Rooms** (explorable):
   - Grand Hall (main products)
   - Gallery (lookbook images)
   - Chamber (exclusive items)
   - Courtyard (outdoor products)
4. **Interactive Elements**:
   - Clickable mirrors show product try-on
   - Torches/candles toggle lighting
   - Castle doors open with animations
   - Product mannequins throughout castle
   - Hidden easter eggs (click secret doors)
5. **User Interactions**:
   - First-person camera controls
   - Click to teleport to rooms
   - Product hotspots with info cards
   - Atmospheric audio (castle ambience, with mute)
6. Use existing `src/collections/LoveHurtsExperience.ts` as reference but ADD full interactivity

**Colors**: #b76e79, #1a0a0a, #dc143c, gold accents

**Files to Create**:
- `wordpress-theme/skyyrose-2025/assets/js/love-hurts-scene.js`

---

#### **Task #3: SIGNATURE Interactive Oakland/SF Tour**
**Location**: Same template

**CRITICAL**: Fully INTERACTIVE city exploration experience!

**Instructions**:
1. **Interactive Oakland/SF Landmarks Tour**:
   - 3D map of Oakland and San Francisco
   - **INTERACTIVE**: Click landmarks to visit them
   - **INTERACTIVE**: Fly camera between locations
   - **INTERACTIVE**: Rotate view, zoom in/out
   - Day/night cycle toggle
2. **Interactive Landmarks** (8 locations):
   - Golden Gate Bridge (product hotspots on bridge)
   - Bay Bridge (products along the span)
   - Lake Merritt (lakeside products)
   - Fox Theater (marquee shows product names)
   - Jack London Square (waterfront products)
   - Alcatraz (island exploration)
   - Coit Tower (panoramic view with products)
   - Painted Ladies (Victorian house products)
3. **Interactive Elements**:
   - Click landmarks to "teleport" there
   - Product billboards at each location
   - Clickable product displays
   - "Tour Guide" mode (auto-play with narration)
   - "Free Roam" mode (explore at your own pace)
   - Minimap with landmark icons
   - Time-of-day slider (golden hour, sunset, night)
4. **User Interactions**:
   - Click landmarks on map
   - Drag to rotate camera
   - Scroll to zoom
   - Arrow keys to fly between locations
   - Product hotspots open detail modals
   - Landmark info cards on hover
5. **Story Integration**:
   - Each landmark has SkyyRose story
   - Product placement tells brand narrative
   - Oakland/SF pride throughout
6. Golden hour lighting with interactive fog slider
7. Minimalist geometric style (low poly)
8. Use existing `src/collections/SignatureExperience.ts` as reference but ADD full interactivity

**Colors**: #d4af37 (gold), #f5f5f0 (cream), #8b7355 (bronze)

**Files to Create**:
- `wordpress-theme/skyyrose-2025/assets/js/signature-scene.js`

---

#### **Task #4: Vault Pre-Order Page**
**Location**: `wordpress-theme/skyyrose-2025/template-vault.php`

**CRITICAL**: Vault combines ALL 3 COLLECTIONS for premier pre-order experience!

**Instructions**:
1. Hero section with countdown timer (JavaScript)
2. Exclusive messaging UI emphasizing "All Collections in One Place"
3. **Collection Showcase** (NEW):
   - Unified 3D gallery showing products from BLACK ROSE, LOVE HURTS, and SIGNATURE
   - Collection tabs or sections to highlight each collection's theme
   - Seamless transitions between collection aesthetics
   - Product cards maintain collection branding (colors, styling)
4. 3D product gallery using LuxuryProductViewer:
   - Query products from ALL 3 collections via WooCommerce
   - Filter: `meta_query` with `_skyyrose_collection` IN ['black-rose', 'love-hurts', 'signature']
   - Display collection badges on each product
5. Pre-order form integration with WooCommerce:
   - Modify `wordpress-theme/skyyrose-2025/elementor-widgets/pre-order-form.php`
   - Multi-collection cart support
   - Collection selector dropdown
   - Variable product selection (size/color)
   - Payment processing (Stripe/PayPal)
6. Exclusivity indicators:
   - Limited quantity counter (from WooCommerce stock across all collections)
   - Live "X viewing" counter (WebSocket or polling)
   - Benefits list: "Exclusive access to ALL SkyyRose collections"
   - Testimonials section
7. Email automation (WooCommerce hooks):
   - Pre-order confirmation email with all collections
   - Launch notification when collections go live
   - Early access codes for Vault members

**Files to Modify**:
- `wordpress-theme/skyyrose-2025/template-vault.php`
- `wordpress-theme/skyyrose-2025/elementor-widgets/pre-order-form.php`
- Create: `wordpress-theme/skyyrose-2025/inc/pre-order-functions.php`

**Tools**: `/wordpress-ops` for WooCommerce integration, Context7 for WooCommerce API

---

#### **Task #5: LuxuryProductViewer Integration**
**Location**: Product pages and collection 3D sections

**Instructions**:
1. Convert `frontend/components/3d/LuxuryProductViewer.tsx` to WordPress-compatible
2. Two options:
   - **Option A**: Bundle React with Webpack, enqueue as dependency
   - **Option B**: Rewrite in vanilla Three.js (recommended for WordPress)
3. Features to maintain:
   - React Three Fiber scene setup (convert to pure Three.js)
   - Rose gold lighting (#B76E79 tint)
   - AccumulativeShadows
   - OrbitControls
   - Bloom + ToneMapping post-processing
   - AR button
   - Auto-rotate
4. Integrate into:
   - Single product pages (`single-product.php`)
   - Vault 3D gallery
   - Elementor widget (`elementor-widgets/immersive-scene.php`)

**Files to Create**:
- `wordpress-theme/skyyrose-2025/assets/js/luxury-product-viewer.js`
- Modify: `wordpress-theme/skyyrose-2025/single-product.php`

**Tools**: Context7 for Three.js documentation, `/component` for React conversion

---

#### **Task #7: AI Image Enhancement Pipeline**
**Location**: WordPress media library integration

**Instructions**:
1. Create WordPress plugin or theme functionality:
   - Hook into `upload_dir` filter
   - Hook into `wp_handle_upload` filter
   - Hook into `add_attachment` action
2. On image upload:
   - Apply luxury color grading (from `services/ai_image_enhancement.py`)
   - Generate blurhash placeholder
   - Create responsive image set (5 sizes)
   - Optional: background removal (toggle in admin)
   - Optional: 4x upscaling (toggle in admin)
3. Admin settings page:
   - Enable/disable AI enhancement
   - API keys configuration
   - Batch processing button (existing media library)
4. Create batch processing script:
   - `scripts/wordpress-media-pipeline.py`
   - Processes all existing product images
   - Updates WordPress metadata

**Files to Create**:
- `wordpress-theme/skyyrose-2025/inc/media-enhancement.php`
- `scripts/wordpress-media-pipeline.py`

**Tools**: Python `services/ai_image_enhancement.py`, WordPress media hooks

---

#### **Task #17: Immersive Template Enhancement**
**Location**: `wordpress-theme/skyyrose-2025/template-immersive.php`

**Instructions**:
1. Full-screen immersive experience template
2. Minimal UI (remove header/footer clutter)
3. Floating hamburger navigation
4. Support for:
   - Lookbook presentations
   - Runway show experiences
   - Virtual showroom tours
5. Section-based scroll (fullpage.js style)
6. Mobile gesture support

**Files to Modify**:
- `wordpress-theme/skyyrose-2025/template-immersive.php`

---

## 🛠️ TOOLS TO USE

Ralph Loop should coordinate these skills/tools:

- **Serena**: ALL file operations (read, create, modify)
- **Context7**: Query WordPress, WooCommerce, Elementor, Three.js docs
- **DevSkyy MCP**: `brand_context`, `wordpress_sync`, `3d_generate`
- **/wordpress-ops**: Theme integration patterns
- **/3d-generation**: GLB model generation
- **/immersive-architect:component**: React component patterns
- **/immersive-architect:theme-plan**: Architecture validation

---

## 📦 DEPENDENCIES AVAILABLE

All packages installed (108 total):

**JavaScript/TypeScript**:
- three (0.182.0)
- @react-three/fiber, @react-three/drei
- postprocessing (bloom, tone mapping)
- framer-motion
- gsap

**PHP/WordPress**:
- @wordpress/scripts
- @woocommerce/components
- Elementor widget APIs

**Python**:
- services/ai_image_enhancement.py (ready to use)
- FAL, Stability AI, Replicate, RemBG

---

## 🎨 BRAND CONTEXT

- **Primary Color**: #B76E79 (rose gold)
- **Tagline**: "Where Love Meets Luxury"
- **Location**: Oakland, CA
- **Collections**: BLACK ROSE, LOVE HURTS, SIGNATURE
- **Aesthetic**: Luxury + Rebellion

---

## 📁 KEY FILES

**Already Enhanced**:
- `wordpress-theme/skyyrose-2025/header.php` ✅
- `wordpress-theme/skyyrose-2025/footer.php` ✅
- `wordpress-theme/skyyrose-2025/template-collection.php` ✅ (product catalog ready)

**Ready for Enhancement**:
- `wordpress-theme/skyyrose-2025/template-vault.php`
- `wordpress-theme/skyyrose-2025/template-immersive.php`
- `wordpress-theme/skyyrose-2025/single-product.php`
- `wordpress-theme/skyyrose-2025/elementor-widgets/*`

**References**:
- `frontend/components/3d/LuxuryProductViewer.tsx`
- `frontend/lib/animations/luxury-transitions.ts`
- `services/ai_image_enhancement.py`
- `src/collections/*.ts`

---

## ✅ SUCCESS CRITERIA

Each task complete when:
- 3D scenes render at 60fps
- Mobile responsive
- WooCommerce integration functional
- Code follows WordPress coding standards
- Security: nonces, sanitization, escaping
- Accessibility: ARIA labels, keyboard navigation

---

## 🚀 EXECUTION ORDER

Recommended order for Ralph Loop:
1. Tasks #1, #2, #3 (Collection immersive sections) - can run in parallel
2. Task #5 (LuxuryProductViewer integration) - needed for Task #4
3. Task #4 (Vault page)
4. Task #7 (AI image pipeline)
5. Task #17 (Immersive template)

---

**Ready for Ralph Loop execution!**
