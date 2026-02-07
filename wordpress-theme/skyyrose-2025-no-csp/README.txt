=== SkyyRose 2025 - Luxury Fashion WordPress Theme ===

Theme Name: SkyyRose 2025
Theme URI: https://skyyrose.com
Description: Premium WordPress theme for luxury streetwear and fashion brands. Features immersive 3D experiences, Elementor integration, and WooCommerce support.
Author: SkyyRose LLC
Author URI: https://skyyrose.com
Version: 2.0.0
License: GPLv2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html
Tags: luxury, fashion, streetwear, ecommerce, woocommerce, elementor, three-js, immersive, 3d

== Description ==

SkyyRose 2025 is a cutting-edge WordPress theme designed for luxury fashion and streetwear brands that demand visual excellence and immersive user experiences.

**KEY FEATURES:**

* Immersive 3D Experiences - Three.js and Babylon.js powered collection showcases
* 4 Custom Elementor Widgets - Immersive Scene, Product Hotspot, Collection Card, Pre-Order Form
* WooCommerce Integration - Complete e-commerce functionality with custom layouts
* Hybrid Split-View Catalog - Sticky filters + dynamic product preview
* Interactive Pre-Order System - Collection selector with email capture
* Theme Customizer - 40+ brand customization options
* Responsive Design - Mobile-first approach for all devices
* Performance Optimized - Lazy loading, script deferral, GPU acceleration
* SEO Optimized - Clean code, semantic HTML, fast loading

**INCLUDED:**

* Main homepage template with hero and collection cards
* 3 immersive collection experience pages (Black Rose, Love Hurts, Signature)
* Hybrid catalog page with split-view layout
* Pre-order/vault page with interactive selector
* Custom Elementor widgets category
* 3D scene configurations (futuristic garden, enchanted castle, fashion runway)
* AI model imagery generation guide
* Complete documentation

**REQUIREMENTS:**

* WordPress 6.0 or higher
* PHP 7.4 or higher
* WooCommerce 7.0 or higher
* Elementor 3.10 or higher (Elementor Pro recommended)
* MySQL 5.7 or MariaDB 10.2 or higher
* HTTPS support
* Pretty permalinks enabled

**RECOMMENDED PLUGINS:**

* Elementor Pro - Advanced widgets and theme builder
* WooCommerce - E-commerce functionality
* Contact Form 7 - Contact forms
* Yoast SEO - Search engine optimization
* WP Rocket - Caching and performance

**BROWSER SUPPORT:**

* Chrome (latest 2 versions)
* Firefox (latest 2 versions)
* Safari (latest 2 versions)
* Edge (latest 2 versions)
* Mobile browsers (iOS Safari, Chrome Mobile)

== Installation ==

**AUTOMATIC INSTALLATION:**

1. In WordPress admin, navigate to Appearance > Themes
2. Click "Add New" > "Upload Theme"
3. Choose the skyyrose-2025.zip file
4. Click "Install Now"
5. After installation, click "Activate"

**MANUAL INSTALLATION:**

1. Unzip skyyrose-2025.zip
2. Upload the 'skyyrose-2025' folder to /wp-content/themes/
3. Navigate to Appearance > Themes in WordPress admin
4. Find "SkyyRose 2025" and click "Activate"

**POST-INSTALLATION STEPS:**

1. Install and activate required plugins (WooCommerce, Elementor)
2. Import demo content (optional, via Tools > Import)
3. Navigate to Appearance > Customize to configure brand settings
4. Create pages using included templates:
   - Homepage (Template: SkyyRose Home)
   - Black Rose (Template: Immersive Experience, set meta: _collection_type = black-rose)
   - Love Hurts (Template: Immersive Experience, set meta: _collection_type = love-hurts)
   - Signature (Template: Immersive Experience, set meta: _collection_type = signature)
   - Collections (Template: SkyyRose Collection)
   - Vault (Template: The Vault - Pre-Order)
5. Configure WooCommerce settings (currency, shipping, payments)
6. Add products with collection meta (_skyyrose_collection: black-rose, love-hurts, or signature)

== Configuration ==

**THEME CUSTOMIZER:**

Navigate to Appearance > Customize to access 40+ customization options:

* Brand Identity - Logo, brand name, tagline
* Colors - Collection colors (Black Rose, Love Hurts, Signature)
* Typography - Heading font, body font, sizes
* Layout - Container width, sidebar position
* Homepage - Hero settings, featured collections
* Social Media - Links to social profiles
* Pre-Order - Email service integration (Mailchimp/Klaviyo)

**WOOCOMMERCE SETUP:**

1. WooCommerce > Settings > General - Set store location, currency
2. WooCommerce > Settings > Products - Enable SKU, reviews
3. WooCommerce > Settings > Shipping - Configure shipping zones
4. WooCommerce > Settings > Payments - Enable payment gateways
5. WooCommerce > Settings > Advanced - Set shop/cart/checkout pages

**PRODUCT SETUP:**

For each product, set these custom fields:

* _skyyrose_collection - Collection ID (black-rose, love-hurts, signature)
* _skyyrose_3d_model_url - URL to 3D model (optional)
* _vault_preorder - Set to '1' to show in vault page
* _vault_badge - Security badge text (default: "ENCRYPTED")
* _vault_quantity_limit - Max quantity available
* _vault_icon - Emoji or icon for vault display

**ELEMENTOR WIDGETS:**

Access SkyyRose widgets in Elementor editor under "SkyyRose Luxury" category:

1. **Immersive 3D Scene** - Three.js collection experiences
   - Scene Type: Black Rose Garden / Love Hurts Castle / Signature Runway
   - Physics: Enable/disable physics engine
   - Scroll Trigger: Camera animations on scroll
   - Auto-Rotate: Automatic camera rotation
   - Hotspots: Product markers in 3D space

2. **Product Hotspot** - Interactive product markers
   - Product: Select WooCommerce product
   - Position: X/Y coordinates
   - Pulse Animation: Enable/disable
   - Preview: Show product preview on hover

3. **Collection Card** - Animated collection previews
   - Collection: Black Rose / Love Hurts / Signature
   - Title, Tagline, Description
   - Background Image
   - Animation Style: Fade Up / Scale In / Slide In
   - Card Height: Responsive slider

4. **Pre-Order Form** - Email capture with perks
   - Form Title & Description
   - Collection Filter: All / specific collection
   - Email Service: Mailchimp / Klaviyo / ConvertKit / Database
   - Success Message
   - Member Perks: Repeater field for benefits list

== Customization ==

**CHANGING BRAND COLORS:**

1. Navigate to Appearance > Customize > Colors
2. Update collection colors:
   - Black Rose Collection: Default #8B0000
   - Love Hurts Collection: Default #B76E79
   - Signature Collection: Default #D4AF37
3. Click "Publish" to save

**ADDING YOUR LOGO:**

1. Navigate to Appearance > Customize > Brand Identity
2. Upload logo image (recommended: 200x60px PNG with transparency)
3. Set tagline (e.g., "Where Love Meets Luxury")
4. Click "Publish"

**CHANGING FONTS:**

1. Navigate to Appearance > Customize > Typography
2. Select Google Font for headings (default: Playfair Display)
3. Select Google Font for body text (default: Inter)
4. Adjust font sizes as needed
5. Click "Publish"

**CREATING IMMERSIVE PAGES:**

1. Create New Page in WordPress
2. Set Template to "Immersive Experience"
3. Add Custom Field: _collection_type with value black-rose, love-hurts, or signature
4. Use Elementor to add Immersive 3D Scene widget
5. Configure scene type, physics, and hotspots
6. Publish page

**CUSTOM CSS:**

Add custom CSS in Appearance > Customize > Additional CSS

Example - Change hover color:
```css
.collection-card:hover .collection-title {
    color: #YOUR_COLOR_HERE;
}
```

== Frequently Asked Questions ==

**Q: Do I need Elementor Pro?**
A: Elementor free version works, but Elementor Pro unlocks advanced features like theme builder, popup builder, and additional widgets.

**Q: Can I change the collection names?**
A: Yes, edit inc/theme-customizer.php to rename collections. Update all references to maintain consistency.

**Q: How do I add 3D models to products?**
A: Use the _skyyrose_3d_model_url custom field with a URL to your .glb or .gltf 3D model file. Host models on a CDN for best performance.

**Q: Does this theme work with Gutenberg?**
A: Yes, but it's optimized for Elementor. Immersive experiences require Elementor widgets.

**Q: Can I translate this theme?**
A: Yes, the theme is translation-ready. Use Loco Translate or WPML for translations.

**Q: How do I integrate Mailchimp/Klaviyo?**
A: Set your API keys in Appearance > Customize > Pre-Order Settings. The pre-order form will automatically send signups to your service.

**Q: Performance optimization tips?**
A:
- Install WP Rocket or similar caching plugin
- Use a CDN for images and 3D models
- Enable lazy loading for images
- Minify CSS/JS
- Use WebP image format
- Limit 3D model polygon count

**Q: Can I use this for non-fashion brands?**
A: Yes! Customize colors, fonts, and content to match any luxury brand. The immersive experiences adapt to any aesthetic.

== Changelog ==

= 2.0.0 - January 31, 2026 =
* Initial release
* Immersive 3D experiences with Three.js and Babylon.js
* 4 custom Elementor widgets
* WooCommerce integration
* Hybrid split-view catalog
* Interactive pre-order system
* Theme customizer with 40+ options
* Performance optimizations
* Mobile responsive design
* SEO optimizations
* Accessibility improvements

== Credits ==

**Technologies:**
* Three.js r160 - https://threejs.org/
* Babylon.js 6.0 - https://www.babylonjs.com/
* GSAP 3.12 with ScrollTrigger - https://greensock.com/gsap/
* Elementor - https://elementor.com/
* WooCommerce - https://woocommerce.com/

**Fonts:**
* Playfair Display - Google Fonts
* Inter - Google Fonts

**Icons:**
* Font Awesome - https://fontawesome.com/

== Support ==

For support, please visit:
* Documentation: https://skyyrose.com/docs
* Support Forum: https://skyyrose.com/support
* Email: support@skyyrose.com

== License ==

This theme is licensed under GPLv2 or later.
http://www.gnu.org/licenses/gpl-2.0.html

SkyyRose 2025 WordPress Theme, Copyright 2026 SkyyRose LLC
SkyyRose 2025 is distributed under the terms of the GNU GPL

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

== Resources ==

All resources included with this theme are either created by SkyyRose LLC
or are properly licensed for distribution:

* Screenshots - AI-generated or properly licensed stock photography
* Icons - Font Awesome (CC BY 4.0)
* Fonts - Google Fonts (Open Font License)
* Three.js - MIT License
* Babylon.js - Apache License 2.0
* GSAP - Standard License (free for GPLv2+ themes)

For a complete list of third-party resources and their licenses,
see docs/LICENSES.md
