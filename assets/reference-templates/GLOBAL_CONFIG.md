# SKYYROSE GLOBAL CONFIGURATION & COMPONENT LIBRARY
# Version: 1.0.0
# Last Updated: 2024-12-11
# Platform: WordPress + WooCommerce + Elementor Pro
# Theme: Shoptimizer 2.9.0

---

## SITE CONFIGURATION

```yaml
site:
  name: "SkyyRose"
  tagline: "Where Love Meets Luxury"
  domain: "skyyrose.co"
  
  wordpress:
    version: "6.4+"
    theme: "Shoptimizer"
    theme_version: "2.9.0"
    
  plugins:
    required:
      - name: "Elementor Pro"
        version: "3.32.2+"
        purpose: "Page builder"
        
      - name: "WooCommerce"
        version: "8.0+"
        purpose: "E-commerce"
        
      - name: "Variation Swatches for WooCommerce"
        slug: "variation-swatches-for-woocommerce"
        purpose: "Color/size swatches"
        
      - name: "YITH WooCommerce Quick View"
        slug: "yith-woocommerce-quick-view"
        purpose: "Product quick view modal"
        
      - name: "YITH WooCommerce Wishlist"
        slug: "yith-woocommerce-wishlist"
        purpose: "Wishlist functionality"
        
    recommended:
      - name: "WP Rocket"
        purpose: "Caching & performance"
        
      - name: "ShortPixel"
        purpose: "Image optimization"
        
      - name: "Smash Balloon Instagram Feed"
        purpose: "Instagram integration"
        
      - name: "Klaviyo"
        purpose: "Email marketing"
        
      - name: "Judge.me / Loox"
        purpose: "Product reviews with photos"
        
      - name: "FiboSearch"
        purpose: "AJAX product search"
```

---

## GLOBAL DESIGN TOKENS

### Colors

```yaml
colors:
  # Brand Primary
  brand:
    black: "#0D0D0D"
    white: "#FAFAFA"
    cream: "#F5F3EF"
    gold: "#D4AF37"
    rose_gold: "#B76E79"
    silver: "#C0C0C0"
    
  # Collection Colors (UPDATED 2024-12-12)
  collections:
    # BLACK ROSE: Dark, Mysterious, Icy, Exclusive
    black_rose:
      primary: "#0D0D0D"          # Pure Black
      accent: "#C0C0C0"           # Metallic Silver
      accent_bright: "#E8E8E8"    # Bright Silver
      secondary: "#1A1A1A"        # Soft Black
      white: "#FAFAFA"            # Pure White
      chrome: "#A8A8A8"           # Chrome/Steel
      text: "#FAFAFA"
      
    # LOVE HURTS: Warm, Emotional, Authentic
    love_hurts:
      primary: "#8B3A3A"          # Deep Rose/Burgundy
      accent: "#D4A5A5"           # Soft Rose
      secondary: "#5C2828"        # Dark Burgundy
      background: "#FDF8F8"       # Warm Cream
      background_dark: "#1A1212"  # Warm Dark
      text_dark: "#2D1F1F"
      
    # SIGNATURE: Luxurious, Premium, Timeless
    signature:
      primary: "#0D0D0D"          # Black
      accent: "#D4AF37"           # Gold
      accent_secondary: "#B76E79" # Rose Gold
      accent_soft: "#C9A962"      # Soft Gold
      white: "#FAFAFA"            # Off-white
      cream: "#F5F3EF"            # Warm Grey
      text: "#0D0D0D"
      
  # Homepage Mixed Palette (combines all collections)
  homepage:
    black: "#0D0D0D"
    white: "#FAFAFA"
    cream: "#F5F3EF"
    gold: "#D4AF37"               # From SIGNATURE
    rose_gold: "#B76E79"          # From SIGNATURE
    silver: "#C0C0C0"             # From BLACK ROSE
    deep_rose: "#8B3A3A"          # From LOVE HURTS
    soft_rose: "#D4A5A5"          # From LOVE HURTS
      
  # UI Colors
  ui:
    success: "#059669"
    success_light: "#D1FAE5"
    warning: "#D97706"
    warning_light: "#FEF3C7"
    error: "#DC2626"
    error_light: "#FEE2E2"
    info: "#2563EB"
    
  # Greys
  grey:
    50: "#FAFAFA"
    100: "#F5F3EF"
    200: "#E5E5E5"
    300: "#D4D4D4"
    400: "#A3A3A3"
    500: "#6B6B6B"
    600: "#525252"
    700: "#404040"
    800: "#262626"
    900: "#171717"
```

### Typography

```yaml
typography:
  fonts:
    heading:
      family: "'Cormorant Garamond', 'Playfair Display', Georgia, serif"
      fallback: "Georgia, serif"
      google_fonts: "Cormorant+Garamond:wght@400;500;600;700"
      
    body:
      family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
      fallback: "-apple-system, BlinkMacSystemFont, sans-serif"
      google_fonts: "Inter:wght@400;500;600"
      
  scale:
    # Mobile first, use clamp() for responsive
    display: "clamp(2.5rem, 8vw, 5rem)"      # 40-80px
    h1: "clamp(2rem, 6vw, 3.5rem)"           # 32-56px
    h2: "clamp(1.5rem, 4vw, 2.5rem)"         # 24-40px
    h3: "clamp(1.25rem, 3vw, 1.75rem)"       # 20-28px
    h4: "clamp(1rem, 2vw, 1.25rem)"          # 16-20px
    body_large: "1.125rem"                    # 18px
    body: "1rem"                              # 16px
    body_small: "0.875rem"                    # 14px
    caption: "0.75rem"                        # 12px
    micro: "0.625rem"                         # 10px
    
  weights:
    light: 300
    regular: 400
    medium: 500
    semibold: 600
    bold: 700
    
  line_heights:
    tight: 1.2
    normal: 1.5
    relaxed: 1.7
    loose: 2
    
  letter_spacing:
    tight: "-0.02em"
    normal: "0"
    wide: "0.05em"
    wider: "0.1em"
    widest: "0.15em"
    display: "0.2em"
    logo: "0.3em"
```

### Spacing

```yaml
spacing:
  # Base unit: 8px
  base: "8px"
  
  scale:
    0: "0"
    1: "4px"
    2: "8px"
    3: "12px"
    4: "16px"
    5: "20px"
    6: "24px"
    8: "32px"
    10: "40px"
    12: "48px"
    16: "64px"
    20: "80px"
    24: "96px"
    32: "128px"
    
  section_padding:
    desktop: "80px"
    tablet: "60px"
    mobile: "48px"
    
  container:
    max_width: "1200px"
    padding: "24px"
    padding_mobile: "16px"
```

### Breakpoints

```yaml
breakpoints:
  xs: "375px"    # Small mobile
  sm: "480px"    # Large mobile
  md: "768px"    # Tablet
  lg: "1024px"   # Desktop
  xl: "1280px"   # Large desktop
  2xl: "1440px"  # Wide desktop
```

### Shadows

```yaml
shadows:
  sm: "0 1px 2px rgba(0, 0, 0, 0.05)"
  md: "0 4px 6px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.05)"
  lg: "0 10px 15px rgba(0, 0, 0, 0.05), 0 4px 6px rgba(0, 0, 0, 0.05)"
  xl: "0 20px 25px rgba(0, 0, 0, 0.08), 0 10px 10px rgba(0, 0, 0, 0.04)"
  card_hover: "0 8px 24px rgba(0, 0, 0, 0.08)"
  modal: "0 25px 50px rgba(0, 0, 0, 0.15)"
```

### Animations

```yaml
animations:
  duration:
    instant: "0ms"
    fast: "150ms"
    normal: "300ms"
    slow: "500ms"
    slower: "700ms"
    
  easing:
    linear: "linear"
    ease: "ease"
    ease_in: "cubic-bezier(0.4, 0, 1, 1)"
    ease_out: "cubic-bezier(0, 0, 0.2, 1)"
    ease_in_out: "cubic-bezier(0.4, 0, 0.2, 1)"
    bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    
  transitions:
    default: "all 0.3s ease"
    fast: "all 0.15s ease"
    color: "color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease"
    transform: "transform 0.3s ease"
    opacity: "opacity 0.3s ease"
```

---

## GLOBAL CSS STYLES

```css
/* ========================================
   SKYYROSE GLOBAL STYLES
   ======================================== */

/* CSS Custom Properties */
:root {
  /* Colors */
  --color-black: #0D0D0D;
  --color-white: #FAFAFA;
  --color-cream: #F5F3EF;
  
  --color-black-rose-accent: #C9A962;
  --color-love-hurts-primary: #8B3A3A;
  --color-signature-primary: #6B6B6B;
  
  --color-success: #059669;
  --color-warning: #D97706;
  --color-error: #DC2626;
  
  /* Typography */
  --font-heading: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  
  /* Spacing */
  --spacing-base: 8px;
  --container-max: 1200px;
  --section-padding: 80px;
  --section-padding-mobile: 48px;
  
  /* Header */
  --header-height: 80px;
  --header-height-mobile: 60px;
  
  /* Transitions */
  --transition-default: all 0.3s ease;
}

/* Base Reset */
*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.5;
  color: var(--color-black);
  background: var(--color-white);
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: 400;
  line-height: 1.2;
  margin: 0 0 0.5em;
}

/* Links */
a {
  color: inherit;
  text-decoration: none;
  transition: var(--transition-default);
}

a:hover {
  color: var(--color-black);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 16px 32px;
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: none;
  cursor: pointer;
  transition: var(--transition-default);
}

.btn-primary {
  background: var(--color-black);
  color: var(--color-white);
}

.btn-primary:hover {
  background: #4A4A4A;
}

.btn-secondary {
  background: transparent;
  color: var(--color-black);
  border: 1px solid var(--color-black);
}

.btn-secondary:hover {
  background: var(--color-black);
  color: var(--color-white);
}

.btn-white {
  background: var(--color-white);
  color: var(--color-black);
}

.btn-white:hover {
  background: var(--color-cream);
}

/* Container */
.container {
  width: 100%;
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .container {
    padding: 0 16px;
  }
}

/* Section Spacing */
.section {
  padding: var(--section-padding) 0;
}

@media (max-width: 768px) {
  .section {
    padding: var(--section-padding-mobile) 0;
  }
}

/* Utility Classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.font-heading { font-family: var(--font-heading); }
.font-body { font-family: var(--font-body); }

.uppercase { text-transform: uppercase; }
.lowercase { text-transform: lowercase; }
.capitalize { text-transform: capitalize; }

.tracking-wide { letter-spacing: 0.05em; }
.tracking-wider { letter-spacing: 0.1em; }
.tracking-widest { letter-spacing: 0.2em; }

/* Visually Hidden (Accessibility) */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus States (Accessibility) */
:focus-visible {
  outline: 2px solid var(--color-black);
  outline-offset: 2px;
}
```

---

## COMPONENT LIBRARY

### Button Component

```yaml
button:
  variants:
    primary:
      background: "#0D0D0D"
      color: "#FAFAFA"
      hover_background: "#4A4A4A"
      hover_color: "#FAFAFA"
      
    secondary:
      background: "transparent"
      color: "#0D0D0D"
      border: "1px solid #0D0D0D"
      hover_background: "#0D0D0D"
      hover_color: "#FAFAFA"
      
    white:
      background: "#FAFAFA"
      color: "#0D0D0D"
      hover_background: "#F5F3EF"
      
    gold:
      background: "#C9A962"
      color: "#0D0D0D"
      hover_background: "#FAFAFA"
      
    rose:
      background: "#8B3A3A"
      color: "#FAFAFA"
      hover_background: "#5C2828"
      
  sizes:
    sm:
      padding: "10px 20px"
      font_size: "0.625rem"
    md:
      padding: "14px 28px"
      font_size: "0.75rem"
    lg:
      padding: "18px 40px"
      font_size: "0.75rem"
    xl:
      padding: "20px 48px"
      font_size: "0.875rem"
      
  base_styles:
    font_family: "Inter"
    font_weight: 500
    letter_spacing: "0.1em"
    text_transform: "uppercase"
    border_radius: "0"
    transition: "all 0.3s ease"
```

### Form Input Component

```yaml
input:
  base:
    font_family: "Inter"
    font_size: "0.875rem"
    padding: "14px 16px"
    border: "1px solid rgba(0, 0, 0, 0.2)"
    border_radius: "0"
    background: "#FFFFFF"
    color: "#0D0D0D"
    
  states:
    focus:
      border_color: "#0D0D0D"
      outline: "none"
    error:
      border_color: "#DC2626"
    disabled:
      background: "#F5F3EF"
      color: "#A3A3A3"
      
  placeholder:
    color: "rgba(0, 0, 0, 0.4)"
```

### Product Card Component

```yaml
product_card:
  container:
    background: "#FFFFFF"
    border: "1px solid rgba(0, 0, 0, 0.05)"
    hover_border: "#0D0D0D"
    hover_shadow: "0 8px 24px rgba(0, 0, 0, 0.08)"
    transition: "all 0.3s ease"
    
  image:
    aspect_ratio: "3:4"
    background: "#F5F3EF"
    object_fit: "cover"
    hover_effect: "secondary_image_swap"
    
  badges:
    position: "top-left"
    margin: "8px"
    variants:
      new:
        background: "#0D0D0D"
        color: "#FAFAFA"
      sale:
        background: "#DC2626"
        color: "#FAFAFA"
      low_stock:
        background: "#D97706"
        color: "#FAFAFA"
      sold_out:
        overlay: true
        background: "rgba(0, 0, 0, 0.6)"
        color: "#FAFAFA"
        
  info:
    padding: "16px"
    title:
      font: "Inter"
      size: "0.875rem"
      weight: 500
      color: "#0D0D0D"
    price:
      font: "Inter"
      size: "0.875rem"
      color: "#6B6B6B"
    swatches:
      size: "12px"
      gap: "4px"
      border_radius: "50%"
```

### Badge Component

```yaml
badge:
  base:
    padding: "4px 8px"
    font_family: "Inter"
    font_size: "0.625rem"
    font_weight: 600
    letter_spacing: "0.05em"
    text_transform: "uppercase"
    
  variants:
    new:
      background: "#0D0D0D"
      color: "#FAFAFA"
    sale:
      background: "#DC2626"
      color: "#FAFAFA"
    low_stock:
      background: "#D97706"
      color: "#FAFAFA"
    limited:
      background: "#C9A962"
      color: "#0D0D0D"
    edition:
      background: "#0D0D0D"
      color: "#C9A962"
      border: "1px solid rgba(201, 169, 98, 0.3)"
```

---

## HEADER & NAVIGATION

```yaml
header:
  height:
    desktop: "80px"
    mobile: "60px"
    
  behavior:
    sticky: true
    transparent_on_hero: true
    shrink_on_scroll: true
    shrunk_height: "60px"
    backdrop_blur: "10px"
    
  layout:
    desktop: "nav-logo-icons"
    mobile: "hamburger-logo-icons"
    
  # ===========================================
  # SPINNING LOGO (CENTER)
  # ===========================================
  logo:
    type: "spinning_svg"
    file: "/assets/images/skyyrose-logo-spinner.svg"
    dimensions:
      desktop: "60px"
      mobile: "48px"
    animation:
      type: "continuous_rotate"
      duration: "8s"
      timing: "linear"
      pause_on_hover: true
    glow:
      enabled: true
      blur: "20px"
    colors_by_page:
      homepage:
        color: "#D4AF37"      # Gold
        glow: "rgba(212, 175, 55, 0.3)"
      black_rose:
        color: "#C0C0C0"      # Metallic Silver
        glow: "rgba(192, 192, 192, 0.3)"
      love_hurts:
        color: "#D4A5A5"      # Soft Rose
        glow: "rgba(212, 165, 165, 0.3)"
      signature:
        color: "#B76E79"      # Rose Gold
        glow: "rgba(183, 110, 121, 0.3)"
      shop:
        color: "#D4AF37"      # Gold
        glow: "rgba(212, 175, 55, 0.3)"
        
  elements:
    left:
      - type: "hamburger_menu"
        mobile_only: false
        color: "#FAFAFA"
      - type: "nav_links"
        desktop_only: true
        items:
          - label: "Shop"
            url: "/shop/"
          - label: "Collections"
            url: "#"
            megamenu: true
          - label: "About"
            url: "/about/"
            
    center:
      - type: "spinning_logo"
        # See logo config above
        
    right:
      - type: "search"
        icon: "search"
        color: "#FAFAFA"
      - type: "account"
        icon: "user"
        color: "#FAFAFA"
      - type: "cart"
        icon: "bag"
        color: "#FAFAFA"
        show_count: true
        count_badge:
          background: "#D4AF37"
          color: "#0D0D0D"
        
  megamenu:
    collections:
      columns:
        - title: "COLLECTIONS"
          links:
            - label: "BLACK ROSE"
              url: "/collection/black-rose/"
              badge: "LIMITED"
              badge_color: "#C0C0C0"
            - label: "LOVE HURTS"
              url: "/collection/love-hurts/"
            - label: "SIGNATURE"
              url: "/collection/signature/"
            - label: "Shop All"
              url: "/shop/"
        - title: "FEATURED"
          type: "product_showcase"
          products: 2
```

---

## FOOTER

```yaml
footer:
  background: "#F5F3EF"
  border_top: "1px solid rgba(0, 0, 0, 0.1)"
  padding:
    desktop: "60px 24px 40px"
    mobile: "48px 16px 32px"
    
  layout:
    columns:
      - title: "SHOP"
        links:
          - text: "All Products"
            url: "/shop/"
          - text: "BLACK ROSE"
            url: "/collection/black-rose/"
          - text: "LOVE HURTS"
            url: "/collection/love-hurts/"
          - text: "SIGNATURE"
            url: "/collection/signature/"
          - text: "New Arrivals"
            url: "/shop/?orderby=date"
            
      - title: "SUPPORT"
        links:
          - text: "Shipping & Delivery"
            url: "/shipping/"
          - text: "Returns & Exchanges"
            url: "/returns/"
          - text: "Size Guide"
            url: "/size-guide/"
          - text: "Contact Us"
            url: "/contact/"
          - text: "FAQ"
            url: "/faq/"
            
      - title: "COMPANY"
        links:
          - text: "Our Story"
            url: "/about/"
          - text: "Journal"
            url: "/journal/"
          - text: "Sustainability"
            url: "/sustainability/"
          - text: "Careers"
            url: "/careers/"
            
      - title: "CONNECT"
        type: "social"
        links:
          - text: "Instagram"
            url: "https://instagram.com/skyyrose"
            icon: "instagram"
          - text: "TikTok"
            url: "https://tiktok.com/@skyyrose"
            icon: "tiktok"
          - text: "Pinterest"
            url: "https://pinterest.com/skyyrose"
            icon: "pinterest"
            
  bottom_bar:
    copyright: "© {{year}} SkyyRose. All rights reserved."
    links:
      - text: "Privacy Policy"
        url: "/privacy-policy/"
      - text: "Terms of Service"
        url: "/terms/"
    payment_icons:
      - visa
      - mastercard
      - amex
      - paypal
      - apple_pay
      - google_pay
```

---

## WOOCOMMERCE SETTINGS

```yaml
woocommerce:
  shop:
    products_per_page: 16
    default_sorting: "menu_order"
    columns: 4
    columns_mobile: 2
    
  product:
    image_gallery: "thumbnails_below"
    zoom: true
    lightbox: true
    
  cart:
    cart_page: true
    mini_cart: true
    free_shipping_threshold: 150
    shipping_calculator: false
    
  checkout:
    guest_checkout: true
    create_account_default: true
    terms_and_conditions: true
    order_notes: false
    
  currency:
    code: "USD"
    symbol: "$"
    position: "left"
    decimal_separator: "."
    thousand_separator: ","
    decimals: 0
```

---

## PERFORMANCE TARGETS

```yaml
performance:
  core_web_vitals:
    lcp: "<2.5s"
    fid: "<100ms"
    cls: "<0.1"
    
  lighthouse:
    performance: ">90"
    accessibility: ">90"
    best_practices: ">90"
    seo: ">90"
    
  optimization:
    images:
      format: "WebP with JPEG fallback"
      quality: 85
      lazy_loading: true
      responsive_sizes: [400, 800, 1200, 1600]
      
    css:
      minify: true
      critical_css: true
      defer_non_critical: true
      
    javascript:
      minify: true
      defer: true
      async_non_critical: true
      
    caching:
      browser_cache: "1 year"
      page_cache: true
      object_cache: true
```

---

## AGENT INTEGRATION API

```yaml
agent_api:
  wordpress_rest:
    base: "{{SITE_URL}}/wp-json"
    endpoints:
      pages: "/wp/v2/pages"
      posts: "/wp/v2/posts"
      media: "/wp/v2/media"
      
  woocommerce_rest:
    base: "{{SITE_URL}}/wp-json/wc/v3"
    endpoints:
      products: "/products"
      categories: "/products/categories"
      orders: "/orders"
      
  elementor_api:
    template_import: "POST /elementor/v1/template/import"
    template_export: "GET /elementor/v1/template/export"
    
  authentication:
    type: "application_password"
    header: "Authorization: Basic {{BASE64_CREDENTIALS}}"
```

---

## FILE MANIFEST

```yaml
files:
  specifications:
    - path: "HOMEPAGE_SPEC.md"
      description: "Complete homepage specification"
      
    - path: "BLACK_ROSE_SPEC.md"
      description: "BLACK ROSE collection page specification"
      
    - path: "LOVE_HURTS_SPEC.md"
      description: "LOVE HURTS collection page specification"
      
    - path: "SIGNATURE_SPEC.md"
      description: "SIGNATURE collection page specification"
      
    - path: "PRODUCT_PAGE_SPEC.md"
      description: "Single product page (PDP) specification"
      
    - path: "SHOP_ARCHIVE_SPEC.md"
      description: "Shop/Archive page specification"
      
    - path: "GLOBAL_CONFIG.md"
      description: "This file - global configuration and components"
```

---

*End of Global Configuration*
