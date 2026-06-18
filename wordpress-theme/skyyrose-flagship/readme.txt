=== SkyyRose ===
Contributors: skyyroseco
Tags: woocommerce, elementor, full-site-editing, fashion, ecommerce, luxury, accessibility-ready
Requires at least: 6.8
Tested up to: 6.8
Requires PHP: 8.2
Stable tag: 1.6.2
License: GPLv2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html

SkyyRose — Oakland-born luxury streetwear. Built by Corey Foster. Four cinematic collections (BLACK ROSE, LOVE HURTS, SIGNATURE, KIDS CAPSULE). Immersive Three.js + GSAP scenes, holographic product cards, AJAX search, WCAG 2.2 AA accessibility. Not a template — the SkyyRose brand made plain.

== Description ==

SkyyRose is a premium dark luxury WooCommerce theme built for fashion, streetwear, and lifestyle brands. The theme delivers immersive product experiences with a dark aesthetic, glassmorphism effects, holographic product cards, and configurable collection palettes. Compatible with Elementor, Gutenberg, and all major page builders.

= Features =

* **Dark Luxury Design System** — #0A0A0A page background with #111111 card surfaces for a rich, cinematic feel
* **4 Collection Pages** — Black Rose, Love Hurts, Signature, and Kids Capsule, each with unique color schemes and particle animations
* **3 Immersive Scene Experiences** — Hotspot-based product discovery within cinematic environments
* **Pre-Order Gateway** — Product modal, cart sidebar, and sign-in panel for upcoming releases
* **Full WooCommerce Integration** — Product pages, cart, and a 4-step checkout flow
* **Luxury Cursor** — Rose gold ring with sparkle trail on desktop
* **Cinematic Mode Toggle** — Immersive viewing mode for product and scene pages
* **Glassmorphism Navigation** — Frosted-glass header with scroll-triggered effects
* **Film Grain SVG Overlay** — Subtle texture applied to all pages
* **Self-Hosted Typography** — Cinzel, Playfair Display, Cormorant Garamond, Bebas Neue, and more — GDPR-compliant, no external requests
* **Responsive Design** — Breakpoints at 1200px, 768px, and 480px
* **WCAG 2.2 AA Accessibility** — Full prefers-reduced-motion support for animations and transitions
* **Security Hardened** — Content Security Policy, HSTS headers, XML-RPC disabled, nonce protection on all forms
* **Conditional Asset Loading** — Scripts and styles loaded per template for optimal performance
* **WordPress Customizer Integration** — Brand colors, social media URLs, and logo configurable from the Customizer
* **Toast Notification System** — Non-intrusive feedback for user actions (add to cart, form submission, errors)
* **Newsletter Subscription** — AJAX-powered email signup with validation
* **Contact Form** — Honeypot anti-spam field with AJAX submission

= Requirements =

* WordPress 6.8 or higher
* WooCommerce 9.9 or higher (required for e-commerce functionality)
* PHP 8.2 or higher
* Modern browser with CSS backdrop-filter support for glassmorphism effects

= Browser Support =

* Chrome 90+
* Firefox 88+
* Safari 14+
* Edge 90+
* Mobile Safari (iOS 14+)
* Chrome Mobile (Android 10+)

== Installation ==

1. Upload the `skyyrose` folder to `/wp-content/themes/`
2. Activate through Appearance > Themes in the WordPress admin
3. Install and activate WooCommerce for full e-commerce functionality
4. Set up navigation menus (Primary, Footer Shop, Footer Help, Footer Legal)
5. Create pages and assign templates via Page Attributes

= After Activation =

1. Navigate to Appearance > Customize to configure:
   - Brand colors (rose gold, gold accents)
   - Social media URLs
   - Site logo and identity

2. Create WooCommerce pages:
   - Shop, Cart, Checkout, My Account

3. Assign page templates:
   - Collection pages (Black Rose, Love Hurts, Signature, Kids Capsule)
   - Immersive scene pages
   - Pre-order gateway

4. Configure menus under Appearance > Menus:
   - Primary Navigation
   - Footer Shop
   - Footer Help
   - Footer Legal

== Frequently Asked Questions ==

= Is WooCommerce required? =

Yes. WooCommerce is required for the product pages, cart, and checkout functionality. The theme is built around WooCommerce integration.

= Does the theme work without JavaScript? =

Core content and navigation are accessible without JavaScript. Enhanced features like the luxury cursor, cinematic mode, particle animations, and AJAX form submissions require JavaScript.

= Can I customize the brand colors? =

Yes. The WordPress Customizer includes settings for brand colors, social media URLs, and the site logo. The dark luxury palette (#0A0A0A backgrounds, rose gold accents) can be adjusted to match your brand.

= Is the theme accessible? =

Yes. The theme targets WCAG 2.2 AA compliance with semantic HTML, ARIA labels, keyboard navigation, focus indicators, and full prefers-reduced-motion support for users who disable animations.

= What about the luxury cursor on mobile? =

The luxury cursor (rose gold ring with sparkle trail) is desktop-only. It is automatically disabled on touch devices.

= How does conditional asset loading work? =

Each page template only loads the CSS and JavaScript it needs. Collection pages load particle animation scripts, immersive pages load scene scripts, and WooCommerce pages load cart/checkout scripts. This reduces page weight across the site.

= Is a skyyrose-template-kit.zip included for Elementor? =

No. The current release does not include a pre-built Elementor Template Kit zip. The docs/installation.html reference to skyyrose-template-kit.zip describes a planned deliverable that has not shipped yet. The recommended import path is the WC Blueprints JSON file at blueprints/skyyrose-demo-setup.json, which automates WooCommerce setup and site options. Full page and collection templates are assigned via Page Attributes in the WordPress editor — no Elementor kit is required to use the theme.

= What can I configure in the Customizer? =

The WordPress Customizer (Appearance > Customize) currently exposes three sections:

* Brand Identity — primary accent color, secondary color, footer logo, favicon
* Social Media — URLs for up to four social platforms
* Kids Capsule Launch — toggle between launch-mode teaser and live shop mode

Typography, header layout, footer layout, and collection palette overrides are controlled via CSS custom properties in assets/css/design-tokens.css (intended for child theme or custom CSS use). Refer to docs/customization.html for guidance on using the design token system.

== Screenshots ==

1. Homepage with dark luxury design system
2. Black Rose Collection page with particle effects
3. Immersive scene experience with product hotspots
4. Pre-order gateway with product modal
5. WooCommerce product page
6. 4-step checkout flow
7. Glassmorphism navigation with scroll effects
8. Luxury cursor with sparkle trail
9. WordPress Customizer panel
10. Mobile responsive layout

== Changelog ==

= 1.6.2 =
* Version triple sync: style.css, readme.txt Stable tag, and SKYYROSE_VERSION constant all set to 1.6.2
* Added missing third-party attributions: Lenis, Motion One, and 3 collection script fonts
* Freshness-guard pre-commit hook wired to prevent future version drift
* Marketplace docs audit: credits.html and LICENSE-ASSETS.txt completed

= 1.6.0 =
* SOT-first imagery pipeline: all product images now resolve through skyyrose-catalog.csv + per-SKU dossiers
* OpenAI Image 2 render pipeline (`scripts/oai_render/`) replaces prior generation workflow
* Product catalog conformed to 33-SKU canonical set; WooCommerce store synced to CSV
* Legal/policy pages published (shipping, returns, privacy, terms, accessibility)

= 1.5.29 =
* Navigation dropdown menus wired to Primary Navigation location
* Mobile nav overlay z-index and backdrop corrections
* Footer menu slug alignment (footer-shop, footer-help, footer-legal)

= 1.5.27 =
* Pre-order functions extracted to inc/woocommerce-preorder.php
* Store API v1 cart (assets/src/js/cart.js) retired; legacy enqueue removed from inc/woocommerce.php
* toast.js global window.skyyToast() API introduced; per-component toasts removed
* Hot-swap deploy script (scripts/deploy-theme.sh) replaces maintenance-mode deploy pattern

= 1.5.0 =
* Builder integrations refactored: shared scaffold (inc/builders/shared.php) for Divi, Beaver Builder, Bricks
* skyyrose_register_builder_compat() helper; Elementor retains full inline integration
* design-tokens.css enqueued globally at priority 10; duplicate per-builder enqueues removed
* Per-collection palette consolidated under [data-collection] selectors in design-tokens.css
* Legacy --col-* and --lp-* CSS alias variables retired

= 1.2.0 =
* Single scroll-reveal IntersectionObserver consolidated into premium-interactions.js
* Per-page reveal observers (landing-pages.js, about.js) retired; class list managed via revealSelectors
* About page reveal CSS aligned from .vis to .is-visible; source and .min.css drift repaired
* Theme page creation gated by SKYYROSE_SETUP_VERSION (inc/theme-activation-setup.php)

= 1.1.2 =
* Luxury cursor JS enqueue gated on skyyrose_get_current_template_slug() — suppressed on immersive templates
* Template slug helper (inc/enqueue.php) established as canonical mechanism for template-conditional enqueues
* Block patterns registered in inc/patterns.php; pattern files in patterns/ directory
* Builder detection: skyyrose_active_builder() returns normalized slug

= 1.1.0 =
* Builder palette callbacks use skyyrose_brand_colors() helper (inc/brand-colors.php)
* Elementor color schemes wired to brand palette; Google Fonts loading disabled in Elementor context
* skyyrose_nav_fallback() renamed from skyyrose_flagship_nav_fallback()
* Bootstrap order in functions.php: detection → shared → builder files

= 1.0.0 =
* Initial commercial release (April 12, 2026)
* Complete theme rebuild from PRD
* Full dark luxury design system (#0A0A0A backgrounds, glassmorphism, film grain)
* 4 collection pages (Black Rose, Love Hurts, Signature, Kids Capsule) with unique palettes and particle effects
* 3 immersive 3D scene experiences with Three.js product hotspots
* WooCommerce cart and 4-step checkout integration
* Luxury Cursor (rose gold ring + sparkle trail, desktop only) and Cinematic Mode
* Security hardened: CSP, HSTS, XML-RPC disabled, nonce protection on all forms
* AJAX form handlers for contact, newsletter, and sign-in
* Self-hosted typography — zero Google Fonts CDN requests (GDPR)
* Conditional asset loading per template
* WCAG 2.2 AA accessibility: skip link, ARIA labels, keyboard navigation, prefers-reduced-motion

== Upgrade Notice ==

= 1.6.2 =
Documentation and attribution update. No functional changes. Safe to apply without a backup.

= 1.0.0 =
Initial release. Requires WordPress 6.8+, WooCommerce 9.9+, and PHP 8.2+.

== Credits ==

= Typefaces =

All typefaces are self-hosted in /assets/fonts/ for GDPR compliance and performance.

* Inter — https://github.com/rsms/inter (SIL Open Font License 1.1)
* Playfair Display — https://github.com/clauseggers/Playfair-Display (SIL Open Font License 1.1)
* Cinzel — https://github.com/nicholasgross/Cinzel (SIL Open Font License 1.1)
* Cormorant Garamond — https://github.com/CatharsisFonts/Cormorant (SIL Open Font License 1.1)
* Bebas Neue — https://github.com/dharmatype/Bebas-Neue (SIL Open Font License 1.1)
* Barlow — https://github.com/jpt/barlow (SIL Open Font License 1.1)
* Oswald — https://github.com/googlefonts/OswaldFont (SIL Open Font License 1.1)
* DM Sans — https://github.com/googlefonts/dm-fonts (SIL Open Font License 1.1)
* Instrument Serif — https://fonts.google.com/specimen/Instrument+Serif (SIL Open Font License 1.1)
* Space Mono — https://github.com/googlefonts/spacemono (SIL Open Font License 1.1)

Collection script accent fonts (per-collection interior headings, self-hosted):

* Yellowtail — https://fonts.google.com/specimen/Yellowtail (SIL Open Font License 1.1) — Black Rose accent
* Kaushan Script — https://fonts.google.com/specimen/Kaushan+Script (SIL Open Font License 1.1) — Love Hurts accent
* Pinyon Script — https://fonts.google.com/specimen/Pinyon+Script (SIL Open Font License 1.1) — Signature + Kids Capsule accent

= JavaScript Libraries =

* Three.js r128 — https://threejs.org/ (MIT License)
* GSAP 3.12.5 — https://gsap.com/ (Standard GSAP License — not open source; permits use in unlimited commercial projects; redistribution of source files outside this theme is not permitted; see https://gsap.com/community/licensing/)
* Lenis 1.3.23 — https://github.com/darkroomengineering/lenis (MIT License)
* Motion One 11.18.2 — https://motion.dev/ (MIT License)

= Platforms =

* WooCommerce — https://woocommerce.com/ (GPL)
* WordPress — https://wordpress.org/ (GPL)

== Privacy Policy ==

SkyyRose does not collect personal data from website visitors beyond what WordPress and WooCommerce handle natively.

The theme includes:
* Local storage for user preferences (client-side only)
* No tracking cookies
* No external API calls beyond WooCommerce payment gateways (fonts are self-hosted)

== Theme URI ==

https://skyyrose.co

== Author ==

The Skyy Rose Collection LLC
https://skyyrose.co

== Copyright ==

SkyyRose Theme, Copyright 2026 The Skyy Rose Collection LLC
SkyyRose is distributed under the terms of the GNU GPL v2 or later.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses/gpl-2.0.html.
