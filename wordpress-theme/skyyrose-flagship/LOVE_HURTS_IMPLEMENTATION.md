# Love Hurts Collection - Beauty & the Beast Enchanted Ballroom
## Implementation Documentation

### Overview
The Love Hurts Collection has been transformed into a **magical Beauty and the Beast-inspired 3D shopping experience** featuring an enchanted rose centerpiece, grand baroque ballroom, and immersive interactive elements.

---

## Files Created

### 1. **love-hurts-scene.js** (Main Scene)
**Location:** `/assets/js/three/love-hurts-scene.js`

**Features Implemented:**

#### Scene Architecture
- **Grand Baroque Ballroom**
  - 50x50 marble checkerboard floor with reflections
  - Ornate gold-leaf columns (6 pillars with bases, shafts, capitals)
  - Vaulted ceiling with curved geometry
  - Dark walls with decorative alcoves for product displays

#### The Enchanted Rose (Centerpiece)
- Glass cloche dome with realistic transparency/transmission
- Multi-layered rose with detailed petals (3 layers, 18+ petals)
- Golden stamens center
- Green stem with leaves
- Ornate golden pedestal base
- **Pulsing magical glow** (red/gold light intensity animation)
- **Rotating rose** (slow continuous rotation)
- Particle effects around rose

#### Lighting System
- **100 Floating Candles** (Hogwarts-inspired)
  - Distributed in cylindrical pattern above ballroom
  - Individual flickering animations (randomized phases)
  - Wax body, flame, and inner core geometry
  - Individual point lights with shadows
  - Realistic flicker effect

- **Crystal Chandelier**
  - Central golden sphere
  - 8 ornate arms with candles
  - 20 hanging crystal diamonds
  - Main spotlight with bloom effect

- **Stained Glass Windows** (4 windows)
  - Gothic arch frames
  - Colored glass (purple, crimson, gold, pink)
  - Rose pattern overlays
  - Colored spotlights streaming through
  - Moonlight from behind (cool blue)

- **General Lighting**
  - Ambient light (very dim for atmosphere)
  - Hemisphere light (moonlight)
  - Directional moonlight with shadows
  - Accent lights at room corners

#### Enchanted Objects (Beauty & Beast Easter Eggs)
1. **Lumière** - Floating candelabra with 3 arms
2. **Cogsworth** - Gold clock with moving hands
3. **Mrs. Potts & Chip** - Porcelain teapot and cup
4. **Magic Mirror** - Golden frame with reflective surface and glowing light
5. **Wardrobe** - Wooden wardrobe with doors slightly ajar
6. **Enchanted Book** - Belle's favorite book with magical glow

All objects have hover animations (floating/bobbing effect)

#### Particle Systems
1. **Rose Petals** (200 particles)
   - Falling from ceiling
   - Red to pink gradient colors
   - Gravity simulation
   - Reset when hitting floor

2. **Golden Sparkles** (500 particles)
   - Distributed throughout ballroom
   - Twinkling animation (size pulsing)
   - Additive blending for glow

3. **Purple Magical Mist** (100 particles)
   - Ground-level atmospheric fog
   - Slow rotation
   - Low opacity for mystery

#### Product Hotspots
- 6 product display locations (in alcoves)
- Glowing rose-shaped markers
- Pulsing golden rings
- Individual point lights
- Hover detection with cursor change
- Click interaction for product modal
- Magical burst effect on click

#### Post-Processing Effects
- **Unreal Bloom Pass**
  - Strength: 1.5
  - Radius: 0.4
  - Threshold: 0.85
  - Creates magical glow on lights and rose

- **Tone Mapping**
  - ACES Filmic tone mapping
  - Exposure: 1.2
  - Cinematic color grading

#### Fog & Atmosphere
- Exponential fog (density: 0.015)
- Dark base color (#0A0A0A)
- Creates depth and mystery

#### Camera & Controls
- Perspective camera (60° FOV)
- Orbit controls with damping
- Min distance: 5, Max distance: 30
- Max polar angle restricted (no upside-down)
- Smooth camera transitions between sections
- Cinematic easing for navigation

#### Animations
- Rose pulsing glow (sin wave, 2 Hz)
- Rose rotation (0.2 rad/s)
- Glass cloche shimmer (opacity variation)
- Candle flickering (randomized per candle)
- Clock hands rotating (hour/minute speeds)
- Floating objects bobbing (sin wave)
- Particle falling/drifting
- Sparkle twinkling
- Hotspot pulsing (rings and lights)
- Stained glass light intensity variation

#### Interactive Features
- Mouse hover detection (raycasting)
- Product hotspot clicks
- Custom event dispatch for product modals
- Navigation between ballroom sections:
  - Grand Ballroom (overview)
  - Enchanted Rose (close-up)
  - Magic Mirror (mirror view)
  - Stained Glass (window view)

---

### 2. **scene-manager.js** (Utility)
**Location:** `/assets/js/three/scene-manager.js`

**Purpose:** Lifecycle management for Three.js scenes

**Features:**
- Scene registration system
- Scene switching with disposal
- Singleton pattern for global access
- Automatic cleanup on switch
- Memory leak prevention

---

### 3. **hotspot-system.js** (Utility)
**Location:** `/assets/js/three/hotspot-system.js`

**Purpose:** Reusable product hotspot interaction system

**Features:**
- Raycasting-based hover detection
- Click event handling
- Callback system (onHover, onClick, onHoverEnd)
- Cursor style management
- Easy hotspot addition/removal

---

### 4. **template-love-hurts.php** (WordPress Template)
**Location:** `/template-love-hurts.php`

**Features:**

#### UI Components
1. **Loading Screen**
   - Rose spinner animation
   - Loading progress bar
   - "Preparing enchanted ballroom" text
   - Auto-fade after 3 seconds

2. **Navigation Menu**
   - Collection title
   - 4 section navigation buttons
   - Golden theme styling
   - Hover effects

3. **Scene Instructions**
   - Mouse controls explanation
   - Product interaction guide
   - Easter egg hint

4. **Audio Controls**
   - Toggle button for background music
   - Placeholder for audio manager integration

5. **Easter Egg Tracker**
   - Counter (0/6 found)
   - List of 6 enchanted objects
   - Visual feedback when found
   - Glowing effect on discovery

6. **Product Modal (Magic Mirror)**
   - Golden ornate frame
   - Pulsing magical glow
   - Grid layout (image + info)
   - Product title, price, description
   - "Add to Cart" button
   - "View Full Details" button
   - Close button with rotation animation

#### Styling
- Dark romantic color palette
- Golden accents throughout
- Backdrop blur effects
- Smooth transitions
- Responsive design (desktop/mobile)
- CSS animations (spin, pulse, load progress)
- Cinzel serif font (fantasy aesthetic)

#### JavaScript Integration
- ES6 module imports
- Scene initialization
- Navigation button handlers
- Product modal AJAX fetch
- Event listeners for interactions
- Security: textContent instead of innerHTML

---

## Technical Specifications

### Performance Optimizations
- Shadow map sizes optimized (256-2048px)
- Particle count limits (100-500 per system)
- LOD ready (can be added for mobile)
- Efficient geometry reuse
- Material sharing where possible
- Post-processing passes limited to 2

### Browser Requirements
- WebGL 2.0 support
- Modern browser (Chrome, Firefox, Safari, Edge)
- Recommended: 60fps on desktop, 30fps on mobile

### Dependencies
- Three.js r150+
- OrbitControls
- EffectComposer
- RenderPass
- UnrealBloomPass

### Color Palette Used
```javascript
deepCrimson: #8B0000    // Rose, accents
royalGold: #FFD700      // Gold leaf, lights
richPurple: #4B0082     // Windows, shadows
midnightBlue: #191970   // Background
candleAmber: #FFBF00    // Candlelight
rosePink: #FF69B4       // Highlights, hotspots
antiqueGold: #C5B358    // Aged gold
shadowBlack: #0A0A0A    // Base darkness
```

---

## Usage Instructions

### For Developers

1. **Install Dependencies**
```bash
npm install three
```

2. **Import in WordPress**
Add to functions.php:
```php
wp_enqueue_script('three-js', 'path/to/three.module.js', [], null, true);
```

3. **Create Page**
- In WordPress admin, create new page
- Select "Love Hurts Collection - Enchanted Ballroom" template
- Publish

4. **Integrate Products**
Modify hotspot creation in `love-hurts-scene.js`:
```javascript
const productData = [
    { name: 'Product Name', pos: [x, y, z], id: 'wc-product-id' }
];
```

5. **AJAX Handler**
Add to functions.php:
```php
add_action('wp_ajax_get_product_data', 'handle_product_data');
add_action('wp_ajax_nopriv_get_product_data', 'handle_product_data');

function handle_product_data() {
    $product_id = $_GET['product_id'];
    $product = wc_get_product($product_id);

    wp_send_json([
        'title' => $product->get_name(),
        'price' => $product->get_price_html(),
        'description' => $product->get_description(),
        'image' => wp_get_attachment_url($product->get_image_id())
    ]);
}
```

### For Content Creators

1. **Navigate Sections**
   - Click navigation buttons to fly to different views
   - Use mouse to orbit around scene
   - Scroll to zoom in/out

2. **Product Interaction**
   - Hover over glowing rose markers
   - Click to open magic mirror modal
   - View product details
   - Add to cart directly from modal

3. **Easter Egg Hunt**
   - Explore ballroom to find 6 enchanted objects
   - Click objects to mark as "found"
   - Track progress in bottom-right counter

4. **Audio**
   - Toggle background music with speaker icon
   - Recommended: Add Beauty & Beast instrumental

---

## Future Enhancements

### Potential Additions
1. **Audio System**
   - Background waltz music
   - Ambient sounds (candles crackling, wind)
   - Interactive click sounds
   - Positional audio (3D sound)

2. **Advanced Interactions**
   - VR mode support
   - Touch controls for mobile
   - Gesture recognition
   - Voice commands

3. **Visual Effects**
   - Ray marching volumetric fog
   - God rays through windows
   - Real-time reflections (cube maps)
   - Depth of field bokeh

4. **Product Features**
   - AR try-on integration
   - 360° product viewer
   - Product customization
   - Size/color variants

5. **Social Features**
   - Screenshot sharing
   - Virtual shopping with friends
   - Gift wrapping options
   - Personalized messages

6. **Performance**
   - Progressive loading
   - LOD system for mobile
   - Texture compression
   - Instanced rendering for candles

---

## Troubleshooting

### Common Issues

**Scene doesn't load:**
- Check browser console for errors
- Verify Three.js is loaded
- Check file paths in imports
- Ensure container element exists

**Performance issues:**
- Reduce particle counts
- Lower shadow map sizes
- Disable bloom on mobile
- Reduce candle count

**Modal doesn't open:**
- Check AJAX endpoint
- Verify product IDs exist
- Check browser console
- Test network requests

**Shadows not showing:**
- Verify renderer.shadowMap.enabled = true
- Check light.castShadow = true
- Ensure mesh.castShadow/receiveShadow = true
- Increase shadow map size

---

## Credits & Inspiration

**Inspired by:**
- Disney's Beauty and the Beast (1991 & 2017)
- Palace of Versailles Hall of Mirrors
- Gothic cathedral architecture
- Baroque/Rococo design

**Technical References:**
- Three.js examples and documentation
- WebGL particle system tutorials
- Post-processing bloom techniques

---

## Summary

The Love Hurts Collection 3D experience is a **fully-realized Beauty and the Beast enchanted ballroom** featuring:

- Enchanted rose under glass with magical glow
- 100 floating candles with realistic flickering
- Grand baroque architecture with golden columns
- Stained glass windows with colored lighting
- 6 enchanted object Easter eggs
- 3 particle systems (petals, sparkles, mist)
- Interactive product hotspots
- Cinematic camera navigation
- Post-processed bloom effects
- Responsive UI with magic mirror modal

**This is a FLAGSHIP experience** - magical, immersive, and iconic!
