# SKYYROSE UPDATED DESIGN TOKENS & SPINNING LOGO
# Version: 1.1.0
# Last Updated: 2024-12-12

---

## CORRECTED COLLECTION COLOR PALETTES

```yaml
colors:
  # ===========================================
  # BLACK ROSE COLLECTION
  # Mood: Dark, Mysterious, Exclusive, Icy
  # ===========================================
  black_rose:
    primary: "#0D0D0D"           # Pure Black
    accent: "#C0C0C0"            # Metallic Silver
    accent_bright: "#E8E8E8"     # Bright Silver
    secondary: "#1A1A1A"         # Soft Black
    white: "#FAFAFA"             # Pure White
    chrome: "#A8A8A8"            # Chrome/Steel
    gradient:
      dark: "linear-gradient(180deg, #0D0D0D 0%, #1A1A1A 50%, #0D0D0D 100%)"
      metallic: "linear-gradient(135deg, #C0C0C0 0%, #E8E8E8 50%, #C0C0C0 100%)"
    text:
      primary: "#FAFAFA"
      secondary: "rgba(250, 250, 250, 0.7)"
      accent: "#C0C0C0"
      
  # ===========================================
  # LOVE HURTS COLLECTION  
  # Mood: Warm, Emotional, Authentic, Bold
  # ===========================================
  love_hurts:
    primary: "#8B3A3A"           # Deep Rose/Burgundy
    accent: "#D4A5A5"            # Soft Rose
    secondary: "#5C2828"         # Dark Burgundy
    background_warm: "#1A1212"   # Warm Dark
    background_light: "#FDF8F8"  # Cream with Rose Tint
    text:
      primary: "#FAFAFA"
      dark: "#2D1F1F"
      muted: "rgba(250, 250, 250, 0.7)"
    gradient:
      warm: "linear-gradient(180deg, #5C2828 0%, #8B3A3A 50%, #1A1212 100%)"
      
  # ===========================================
  # SIGNATURE COLLECTION
  # Mood: Luxurious, Timeless, Premium, Bold
  # ===========================================
  signature:
    primary: "#0D0D0D"           # Black
    accent: "#D4AF37"            # Gold
    accent_secondary: "#B76E79"  # Rose Gold
    accent_alt: "#C9A962"        # Soft Gold
    white: "#FAFAFA"             # Off-white
    cream: "#F5F3EF"             # Warm Grey
    gradient:
      gold: "linear-gradient(135deg, #D4AF37 0%, #F5D77A 50%, #D4AF37 100%)"
      rose_gold: "linear-gradient(135deg, #B76E79 0%, #E8B4BC 50%, #B76E79 100%)"
    text:
      primary: "#0D0D0D"
      secondary: "#6B6B6B"
      gold: "#D4AF37"
      
  # ===========================================
  # HOMEPAGE MIXED PALETTE
  # Combines elements from all three collections
  # ===========================================
  homepage:
    # Primary Tones
    black: "#0D0D0D"
    white: "#FAFAFA"
    cream: "#F5F3EF"
    
    # Metallic Accents (from all collections)
    gold: "#D4AF37"              # From SIGNATURE
    rose_gold: "#B76E79"         # From SIGNATURE
    silver: "#C0C0C0"            # From BLACK ROSE
    
    # Warm Tones
    deep_rose: "#8B3A3A"         # From LOVE HURTS
    soft_rose: "#D4A5A5"         # From LOVE HURTS
    
    # Gradients
    hero_gradient: "linear-gradient(135deg, #0D0D0D 0%, #1A1A1A 40%, #2D1F1F 70%, #0D0D0D 100%)"
    metallic_accent: "linear-gradient(90deg, #C0C0C0 0%, #D4AF37 50%, #B76E79 100%)"
    
    # Section Backgrounds (alternating)
    section_dark: "#0D0D0D"
    section_light: "#FAFAFA"
    section_warm: "#FDF8F8"
    section_cream: "#F5F3EF"
```

---

## SPINNING LOGO COMPONENT

### Specification

```yaml
spinning_logo:
  type: "animated_header_logo"
  format: "svg_or_image"
  
  dimensions:
    desktop:
      width: "60px"
      height: "60px"
    mobile:
      width: "48px"
      height: "48px"
      
  animation:
    type: "continuous_rotate"
    duration: "8s"
    timing_function: "linear"
    direction: "normal"
    play_state: "running"
    # Pause on hover for elegance
    hover_behavior: "pause"
    
  logo_design:
    shape: "circular_rose_emblem"
    elements:
      - "stylized_rose"
      - "geometric_accent"
    colors:
      default: "#D4AF37"         # Gold
      on_dark: "#D4AF37"         # Gold on dark backgrounds
      on_light: "#0D0D0D"        # Black on light backgrounds
      
  glow_effect:
    enabled: true
    color: "rgba(212, 175, 55, 0.3)"
    blur: "20px"
    
  position:
    header: "center"
    z_index: 100
```

### CSS Implementation

```css
/* ========================================
   SPINNING LOGO COMPONENT
   ======================================== */

/* Logo Container */
.skyyrose-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.skyyrose-logo__spinner {
  width: 60px;
  height: 60px;
  animation: spin 8s linear infinite;
  transition: filter 0.3s ease;
}

/* Pause on hover for elegance */
.skyyrose-logo:hover .skyyrose-logo__spinner {
  animation-play-state: paused;
}

/* Glow effect */
.skyyrose-logo__spinner {
  filter: drop-shadow(0 0 20px rgba(212, 175, 55, 0.3));
}

.skyyrose-logo:hover .skyyrose-logo__spinner {
  filter: drop-shadow(0 0 30px rgba(212, 175, 55, 0.5));
}

/* Spin Animation */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Mobile Size */
@media (max-width: 768px) {
  .skyyrose-logo__spinner {
    width: 48px;
    height: 48px;
  }
}

/* ========================================
   LOGO COLOR VARIANTS
   ======================================== */

/* Gold (Default - for dark backgrounds) */
.skyyrose-logo--gold .skyyrose-logo__spinner path,
.skyyrose-logo--gold .skyyrose-logo__spinner circle {
  fill: #D4AF37;
}

/* Silver (BLACK ROSE pages) */
.skyyrose-logo--silver .skyyrose-logo__spinner path,
.skyyrose-logo--silver .skyyrose-logo__spinner circle {
  fill: #C0C0C0;
}

.skyyrose-logo--silver .skyyrose-logo__spinner {
  filter: drop-shadow(0 0 20px rgba(192, 192, 192, 0.3));
}

/* Rose Gold (SIGNATURE pages) */
.skyyrose-logo--rose-gold .skyyrose-logo__spinner path,
.skyyrose-logo--rose-gold .skyyrose-logo__spinner circle {
  fill: #B76E79;
}

.skyyrose-logo--rose-gold .skyyrose-logo__spinner {
  filter: drop-shadow(0 0 20px rgba(183, 110, 121, 0.3));
}

/* Deep Rose (LOVE HURTS pages) */
.skyyrose-logo--deep-rose .skyyrose-logo__spinner path,
.skyyrose-logo--deep-rose .skyyrose-logo__spinner circle {
  fill: #D4A5A5;
}

.skyyrose-logo--deep-rose .skyyrose-logo__spinner {
  filter: drop-shadow(0 0 20px rgba(212, 165, 165, 0.3));
}

/* Black (for light backgrounds) */
.skyyrose-logo--black .skyyrose-logo__spinner path,
.skyyrose-logo--black .skyyrose-logo__spinner circle {
  fill: #0D0D0D;
}

.skyyrose-logo--black .skyyrose-logo__spinner {
  filter: drop-shadow(0 0 15px rgba(0, 0, 0, 0.2));
}

/* ========================================
   HEADER WITH SPINNING LOGO
   ======================================== */

.site-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: var(--header-height, 80px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  transition: all 0.3s ease;
}

/* Transparent header on hero sections */
.site-header--transparent {
  background: transparent;
}

/* Solid header on scroll */
.site-header--scrolled {
  background: rgba(13, 13, 13, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

/* Header Layout */
.site-header__left,
.site-header__right {
  flex: 1;
  display: flex;
  align-items: center;
}

.site-header__left {
  justify-content: flex-start;
}

.site-header__right {
  justify-content: flex-end;
}

.site-header__center {
  flex: 0 0 auto;
}

/* Navigation Links */
.site-header__nav {
  display: flex;
  gap: 32px;
}

.site-header__nav a {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #FAFAFA;
  text-decoration: none;
  transition: color 0.3s ease;
}

.site-header__nav a:hover {
  color: #D4AF37;
}

/* Header Icons */
.site-header__icons {
  display: flex;
  gap: 20px;
}

.site-header__icon {
  width: 20px;
  height: 20px;
  color: #FAFAFA;
  transition: color 0.3s ease;
  cursor: pointer;
}

.site-header__icon:hover {
  color: #D4AF37;
}

/* Cart Count Badge */
.site-header__cart {
  position: relative;
}

.site-header__cart-count {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 18px;
  height: 18px;
  background: #D4AF37;
  color: #0D0D0D;
  font-size: 0.625rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

/* Mobile Header */
@media (max-width: 768px) {
  .site-header {
    height: var(--header-height-mobile, 60px);
    padding: 0 16px;
  }
  
  .site-header__nav {
    display: none;
  }
  
  .site-header__icons {
    gap: 16px;
  }
}
```

### SVG Logo Template

```svg
<!-- Spinning Rose Logo - Save as skyyrose-logo-spinner.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="skyyrose-logo__spinner">
  <!-- Outer Ring -->
  <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"/>
  
  <!-- Rose Petals (Stylized) -->
  <g fill="currentColor">
    <!-- Center Petal -->
    <path d="M50 15 C55 25, 60 35, 50 50 C40 35, 45 25, 50 15" opacity="0.9"/>
    
    <!-- Right Petal -->
    <path d="M85 50 C75 55, 65 60, 50 50 C65 40, 75 45, 85 50" opacity="0.8"/>
    
    <!-- Bottom Petal -->
    <path d="M50 85 C45 75, 40 65, 50 50 C60 65, 55 75, 50 85" opacity="0.9"/>
    
    <!-- Left Petal -->
    <path d="M15 50 C25 45, 35 40, 50 50 C35 60, 25 55, 15 50" opacity="0.8"/>
    
    <!-- Diagonal Petals -->
    <path d="M75 25 C68 32, 58 42, 50 50 C58 42, 68 32, 75 25" opacity="0.6" transform="rotate(45 50 50)"/>
    <path d="M75 25 C68 32, 58 42, 50 50 C58 42, 68 32, 75 25" opacity="0.6" transform="rotate(135 50 50)"/>
    <path d="M75 25 C68 32, 58 42, 50 50 C58 42, 68 32, 75 25" opacity="0.6" transform="rotate(225 50 50)"/>
    <path d="M75 25 C68 32, 58 42, 50 50 C58 42, 68 32, 75 25" opacity="0.6" transform="rotate(315 50 50)"/>
  </g>
  
  <!-- Center Circle -->
  <circle cx="50" cy="50" r="8" fill="currentColor"/>
  
  <!-- Inner Accent Ring -->
  <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" stroke-width="0.5" opacity="0.2"/>
</svg>
```

### HTML Implementation

```html
<!-- Header with Spinning Logo -->
<header class="site-header site-header--transparent" id="site-header">
  <!-- Left: Menu & Nav -->
  <div class="site-header__left">
    <button class="site-header__hamburger" aria-label="Menu">
      <span></span>
      <span></span>
      <span></span>
    </button>
    <nav class="site-header__nav">
      <a href="/shop/">Shop</a>
      <a href="/collections/">Collections</a>
      <a href="/about/">About</a>
    </nav>
  </div>
  
  <!-- Center: Spinning Logo -->
  <div class="site-header__center">
    <a href="/" class="skyyrose-logo skyyrose-logo--gold" aria-label="SkyyRose Home">
      <img src="/assets/images/skyyrose-logo-spinner.svg" alt="SkyyRose" class="skyyrose-logo__spinner" />
    </a>
  </div>
  
  <!-- Right: Icons -->
  <div class="site-header__right">
    <div class="site-header__icons">
      <button class="site-header__icon site-header__search" aria-label="Search">
        <svg><!-- Search Icon --></svg>
      </button>
      <a href="/my-account/" class="site-header__icon site-header__account" aria-label="Account">
        <svg><!-- Account Icon --></svg>
      </a>
      <a href="/cart/" class="site-header__icon site-header__cart" aria-label="Cart">
        <svg><!-- Cart Icon --></svg>
        <span class="site-header__cart-count">0</span>
      </a>
    </div>
  </div>
</header>
```

### JavaScript for Header Behavior

```javascript
// Header scroll behavior
document.addEventListener('DOMContentLoaded', function() {
  const header = document.getElementById('site-header');
  let lastScroll = 0;
  
  window.addEventListener('scroll', function() {
    const currentScroll = window.pageYOffset;
    
    // Add scrolled class after 50px
    if (currentScroll > 50) {
      header.classList.add('site-header--scrolled');
      header.classList.remove('site-header--transparent');
    } else {
      header.classList.remove('site-header--scrolled');
      header.classList.add('site-header--transparent');
    }
    
    lastScroll = currentScroll;
  });
});

// Change logo color based on page/section
function updateLogoColor(variant) {
  const logo = document.querySelector('.skyyrose-logo');
  logo.className = 'skyyrose-logo skyyrose-logo--' + variant;
}

// Usage examples:
// updateLogoColor('gold');      // Default / Homepage
// updateLogoColor('silver');    // BLACK ROSE pages
// updateLogoColor('rose-gold'); // SIGNATURE pages
// updateLogoColor('deep-rose'); // LOVE HURTS pages
```

---

## PAGE-SPECIFIC LOGO COLORS

```yaml
logo_colors_by_page:
  homepage:
    variant: "gold"
    color: "#D4AF37"
    glow: "rgba(212, 175, 55, 0.3)"
    
  black_rose:
    variant: "silver"
    color: "#C0C0C0"
    glow: "rgba(192, 192, 192, 0.3)"
    
  love_hurts:
    variant: "deep-rose"
    color: "#D4A5A5"
    glow: "rgba(212, 165, 165, 0.3)"
    
  signature:
    variant: "rose-gold"
    color: "#B76E79"
    glow: "rgba(183, 110, 121, 0.3)"
    
  shop:
    variant: "gold"
    color: "#D4AF37"
    glow: "rgba(212, 175, 55, 0.3)"
    
  product:
    variant: "inherit_from_collection"
    # Dynamically set based on product's collection
```

---

## WORDPRESS/ELEMENTOR INTEGRATION

### Elementor Widget Config

```json
{
  "elementor_widget": "container",
  "widget_name": "skyyrose-spinning-logo",
  "settings": {
    "content_width": "full",
    "flex_direction": "column",
    "flex_align_items": "center",
    "flex_justify_content": "center",
    "css_classes": "skyyrose-logo skyyrose-logo--gold"
  },
  "children": [
    {
      "elementor_widget": "image",
      "settings": {
        "image": {"url": "/assets/images/skyyrose-logo-spinner.svg"},
        "image_size": "custom",
        "image_custom_dimension": {"width": 60, "height": 60},
        "css_classes": "skyyrose-logo__spinner",
        "_animation": "none"
      }
    }
  ]
}
```

### Theme Functions (functions.php)

```php
<?php
/**
 * SkyyRose Spinning Logo Header
 */

// Enqueue spinning logo styles
function skyyrose_enqueue_logo_styles() {
    wp_enqueue_style(
        'skyyrose-spinning-logo',
        get_template_directory_uri() . '/assets/css/spinning-logo.css',
        array(),
        '1.0.0'
    );
    
    wp_enqueue_script(
        'skyyrose-header-js',
        get_template_directory_uri() . '/assets/js/header.js',
        array(),
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_logo_styles');

// Get logo variant based on current page
function skyyrose_get_logo_variant() {
    if (is_front_page()) {
        return 'gold';
    }
    
    if (is_product_category('black-rose') || is_page('black-rose')) {
        return 'silver';
    }
    
    if (is_product_category('love-hurts') || is_page('love-hurts')) {
        return 'deep-rose';
    }
    
    if (is_product_category('signature') || is_page('signature')) {
        return 'rose-gold';
    }
    
    // For single products, check their category
    if (is_product()) {
        global $product;
        $categories = wp_get_post_terms($product->get_id(), 'product_cat', array('fields' => 'slugs'));
        
        if (in_array('black-rose', $categories)) {
            return 'silver';
        } elseif (in_array('love-hurts', $categories)) {
            return 'deep-rose';
        } elseif (in_array('signature', $categories)) {
            return 'rose-gold';
        }
    }
    
    return 'gold'; // Default
}

// Output spinning logo
function skyyrose_spinning_logo() {
    $variant = skyyrose_get_logo_variant();
    ?>
    <a href="<?php echo home_url('/'); ?>" class="skyyrose-logo skyyrose-logo--<?php echo esc_attr($variant); ?>" aria-label="SkyyRose Home">
        <img src="<?php echo get_template_directory_uri(); ?>/assets/images/skyyrose-logo-spinner.svg" 
             alt="SkyyRose" 
             class="skyyrose-logo__spinner" />
    </a>
    <?php
}
```

---

## AGENT TASKS

```yaml
agent_tasks:
  - agent: "design_agent"
    task: "Create spinning rose logo SVG with proper paths"
    priority: "critical"
    specs:
      format: "SVG"
      viewbox: "0 0 100 100"
      style: "Geometric rose with elegant petals"
      colors: "Uses currentColor for flexibility"
      
  - agent: "wordpress_agent"
    task: "Implement header with spinning logo in Elementor Theme Builder"
    priority: "critical"
    
  - agent: "wordpress_agent"
    task: "Add PHP function for dynamic logo color based on page"
    priority: "high"
    
  - agent: "frontend_agent"
    task: "Add CSS for spin animation and color variants"
    priority: "high"
    
  - agent: "frontend_agent"
    task: "Add JavaScript for scroll behavior and logo color switching"
    priority: "medium"
```

---

*End of Spinning Logo & Updated Design Tokens Specification*
