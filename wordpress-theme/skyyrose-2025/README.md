# SkyyRose 2025 WordPress Theme

**Version**: 2.0.0
**Author**: SkyyRose Team
**License**: Proprietary
**WordPress**: 6.0+
**WooCommerce**: 8.0+
**PHP**: 8.0+

---

## 🎨 Overview

A complete, production-ready WordPress theme for **SkyyRose**, a luxury streetwear brand based in Oakland, California. Features three distinct collection experiences (Black Rose, Love Hurts, Signature), full WooCommerce integration, and stunning immersive templates.

**Tagline**: "Where Love Meets Luxury"

---

## ✨ Features

### Core Features
- ✅ **7 Custom Page Templates** (Home, Collections, Immersive Experiences, Vault, About, Contact, Product)
- ✅ **30 Pre-Loaded Products** (10 per collection with full descriptions)
- ✅ **WooCommerce Integration** (Cart, Checkout, Product pages)
- ✅ **Responsive Design** (Mobile-first, works beautifully on all devices)
- ✅ **AJAX Add to Cart** (Seamless shopping experience)
- ✅ **Contact Form** (Built-in with email notifications)
- ✅ **SEO Optimized** (Clean markup, semantic HTML5)
- ✅ **Performance Optimized** (Fast loading, lazy images)
- ✅ **Accessibility** (WCAG 2.1 AA compliant)

### Visual Features
- 🎨 **Collection-Specific Theming** (Dynamic colors per collection)
- 🌈 **CSS Gradients** (No images needed for launch)
- ✨ **Smooth Animations** (GSAP-powered, butter smooth)
- 🖼️ **Image Galleries** (Product images with lightbox)
- 🎭 **View Transitions API** (Modern page transitions)
- 📱 **Mobile Navigation** (Hamburger menu, touch-friendly)

### E-Commerce Features
- 🛒 **Full WooCommerce Support**
- 💳 **Payment Gateways Ready** (Stripe, PayPal)
- 📦 **Shipping Zones**
- 📊 **Product Categories & Tags**
- 🔖 **Product Badges** (NEW, LIMITED, EXCLUSIVE)
- 🏷️ **Custom Meta Fields** (Fabric, Care Instructions, Collection)
- 📸 **Product Galleries** (4-6 images per product)
- ⚡ **The Vault** (Pre-order system)

---

## 📁 File Structure

```
skyyrose-2025/
├── README.md                    # This file
├── DEPLOYMENT_GUIDE.md          # Complete deployment instructions
├── IMAGE_ASSETS.md              # Image sourcing guide
├── PRODUCT_DATA.csv             # WooCommerce product import file
├── style.css                    # Theme stylesheet
├── functions.php                # Theme functions & hooks
├── header.php                   # Site header with navigation
├── footer.php                   # Site footer with menus
├── index.php                    # Default template
├── page.php                     # Default page template
├── single.php                   # Default single post template
├── woocommerce.php              # WooCommerce template override
├── template-home.php            # Homepage template
├── template-collection.php      # Collection product grid
├── template-immersive.php       # Immersive collection experience
├── template-vault.php           # Pre-order/vault page
├── single-product.php           # Single product page
├── page-about.php               # About page
├── page-contact.php             # Contact page
└── assets/
    └── js/                      # JavaScript files (3D, animations, etc.)
```

---

## 🚀 Quick Start

### Requirements
- WordPress 6.0+
- WooCommerce 8.0+
- PHP 8.0+
- MySQL 5.7+ or MariaDB 10.3+
- SSL Certificate (HTTPS)

### Installation (5 minutes)

1. **Upload Theme**
   ```bash
   # Via FTP/SFTP
   Upload to: /wp-content/themes/skyyrose-2025/
   ```

2. **Activate Theme**
   - Go to **Appearance > Themes**
   - Click **Activate** on SkyyRose 2025

3. **Install Plugins**
   - WooCommerce (required)
   - Contact Form 7 or WPForms (optional)
   - Yoast SEO or Rank Math (recommended)

4. **Import Products**
   - Go to **WooCommerce > Products > Import**
   - Upload `PRODUCT_DATA.csv`
   - Map columns and import

5. **Create Pages**
   - Create pages with respective templates
   - See `DEPLOYMENT_GUIDE.md` for detailed instructions

6. **Set Menus**
   - Go to **Appearance > Menus**
   - Create Primary and Footer menus
   - Assign to locations

**Done! Your site is ready.**

For complete step-by-step instructions, see **DEPLOYMENT_GUIDE.md**

---

## 📄 Page Templates

### 1. Homepage (`template-home.php`)
- Hero section with animated gradients
- Collection preview cards (Black Rose, Love Hurts, Signature)
- CTA buttons to shop or explore

**Usage**: Set as static homepage in Settings > Reading

### 2. Collection Pages (`template-collection.php`)
- Product grid (8-10 products per collection)
- Filter by category (All, Tops, Bottoms, etc.)
- Add to cart functionality
- Collection-specific theming

**Requires**: `_collection_type` custom field (`black-rose`, `love-hurts`, or `signature`)

### 3. Immersive Experience (`template-immersive.php`)
- Full-screen collection aesthetic
- Featured product hotspots
- CSS-based animations (no 3D required for launch)
- View switcher to product grid

**Best For**:
- `/01-black-rose-garden`
- `/02-love-hurts-castle`
- `/03-signature-runway`

### 4. The Vault (`template-vault.php`)
- Pre-order page with tech aesthetic
- Rotating collection logos
- Exclusive product displays
- Futuristic design

**Requires**: Products with `_vault_preorder` meta = `1`

### 5. Single Product (`single-product.php`)
- Product gallery with thumbnails
- Collection-specific theming
- Fabric composition and care instructions
- Related products section
- AJAX add to cart

**Automatically** used for all WooCommerce products

### 6. About Page (`page-about.php`)
- Brand story section
- Core values (6 value cards)
- Founder quote
- CTA section

### 7. Contact Page (`page-contact.php`)
- Contact form (name, email, subject, message)
- Contact information cards
- FAQ accordion
- Social media links

---

## 🎨 Collections

### Black Rose
**Color**: #8B0000 (Crimson)
**Aesthetic**: Gothic, dark, mysterious
**Vibe**: "For the bold and resilient"

**Products** (10):
1. Thorn Hoodie - $95
2. Black Rose Sherpa - $185
3. Gothic Dress - $145
4. Distressed Tee - $55
5. Crimson Beanie - $35
6. Shadow Joggers - $75
7. Leather Jacket - $325
8. Rose Cap - $40
9. Combat Boots - $185
10. Ripped Jeans - $110

### Love Hurts
**Color**: #B76E79 (Rose Gold)
**Aesthetic**: Romantic, emotional, soft
**Vibe**: "Wear your heart"

**Products** (10):
1. Rose Hoodie - $95
2. Heartbreak Dress - $135
3. Emotional Crewneck - $85
4. Love Hurts Tee - $55
5. Pink Beanie - $35
6. Distressed Joggers - $75
7. Castle Jacket - $165
8. Heart Cap - $40
9. Platform Boots - $155
10. Vintage Jeans - $110

### Signature
**Color**: #D4AF37 (Gold)
**Aesthetic**: Minimal, luxury, timeless
**Vibe**: "The foundation of style"

**Products** (10):
1. Foundation Blazer - $425
2. Icon Trench - $595
3. Silhouette Dress - $350
4. Gold Label Tee - $75
5. Signature Shorts - $125
6. Premium Hoodie - $145
7. Luxury Joggers - $165
8. Designer Sneakers - $285
9. Gold Cap - $50
10. Tailored Pants - $225

---

## 🎯 Custom Meta Fields

### Product Meta (_skyyrose_collection)
- `black-rose`
- `love-hurts`
- `signature`

### Product Badges (_product_badge)
- `NEW`
- `LIMITED`
- `EXCLUSIVE`

### Additional Meta
- `_fabric_composition`: e.g., "80% Cotton, 20% Polyester"
- `_care_instructions`: e.g., "Machine wash cold, tumble dry low"
- `_vault_preorder`: `1` (shows in The Vault)
- `_skyyrose_3d_model_url`: URL to .glb/.gltf 3D model

**Admin Interface**: Custom meta box in product editor

---

## 🖼️ Image Assets

### Required Images
- **Collection Heroes**: 3 images (1920x1080px)
- **Product Photos**: 30 products × 4-6 images = 120-180 images (800x800px)
- **Collection Logos**: 3 logos (500x500px, transparent PNG)
- **Site Logo**: 1 logo (300x100px or 200x200px)

### Sourcing Strategies
1. **AI Generation**: Midjourney or DALL-E 3 (recommended)
2. **Stock Photos**: Unsplash, Pexels (free)
3. **CSS Gradients**: Fallback (built-in, no images needed)

**See `IMAGE_ASSETS.md` for complete guide with Midjourney prompts.**

---

## ⚙️ Customization

### Change Colors

Edit `style.css` or use **Appearance > Customize > Additional CSS**:

```css
:root {
    --black-rose: #YOUR_COLOR;
    --love-hurts: #YOUR_COLOR;
    --signature-gold: #YOUR_COLOR;
}
```

### Add Google Fonts

Already included in `functions.php`:
- **Inter**: Body text
- **Playfair Display**: Headings

To add more, edit `skyyrose_enqueue_assets()` in `functions.php`.

### Modify Navigation

Go to **Appearance > Menus**:
- Create/edit **Main Menu** (primary location)
- Create/edit **Footer Menu** (footer location)

### Contact Form Email

Default sends to `hello@skyyrose.co`

Change in `functions.php`, function `skyyrose_handle_contact_form()`:
```php
$to = 'your-email@example.com';
```

---

## 🔌 Plugin Compatibility

### Tested With:
- ✅ WooCommerce 8.x
- ✅ Contact Form 7
- ✅ Yoast SEO
- ✅ Rank Math SEO
- ✅ WP Rocket
- ✅ Smush
- ✅ Wordfence Security
- ✅ UpdraftPlus

### Recommended Plugins:
- **WooCommerce** (required)
- **Yoast SEO** or **Rank Math** (SEO)
- **Contact Form 7** or **WPForms** (forms)
- **WP Rocket** (caching)
- **Smush** (image optimization)
- **Wordfence** (security)
- **UpdraftPlus** (backups)

---

## 🚨 Troubleshooting

### Images Not Loading
- Check file permissions (755 for folders, 644 for files)
- Regenerate thumbnails: Plugins > Add New > Regenerate Thumbnails

### Menu Not Showing
- Go to **Appearance > Menus**
- Assign menu to "Primary Menu" location
- Save changes

### Add to Cart Not Working
- Ensure WooCommerce is active
- Check browser console for JavaScript errors
- Clear cache

### Contact Form Not Sending
- Check server email configuration
- Install **WP Mail SMTP** plugin
- Test with different email address

### Slow Page Load
- Install **WP Rocket** or **W3 Total Cache**
- Optimize images with **Smush**
- Enable lazy loading (built into WordPress 5.5+)

---

## 📊 Performance

**Target Metrics**:
- **PageSpeed Score**: 90+ (mobile), 95+ (desktop)
- **Load Time**: <3 seconds
- **First Contentful Paint**: <1.5 seconds
- **Largest Contentful Paint**: <2.5 seconds

**Optimization Checklist**:
- [ ] Enable caching
- [ ] Optimize images
- [ ] Minify CSS/JS
- [ ] Use CDN (optional)
- [ ] Enable lazy loading
- [ ] Limit plugins to essentials

---

## 🛡️ Security

### Built-In Security:
- Nonce verification on all forms
- Input sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

### Recommended:
- Install **Wordfence** or **Sucuri**
- Enable two-factor authentication
- Use strong passwords
- Keep WordPress/plugins updated
- Regular backups

---

## 📞 Support

### Documentation
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Image Assets**: `IMAGE_ASSETS.md`
- **Product Data**: `PRODUCT_DATA.csv`

### Contact
- **Email**: hello@skyyrose.co
- **Website**: skyyrose.co

### Resources
- WooCommerce Docs: https://woocommerce.com/documentation/
- WordPress Codex: https://codex.wordpress.org/

---

## 📝 Changelog

### Version 2.0.0 (January 30, 2025)
- ✨ Complete theme rebuild
- ✨ 7 custom templates
- ✨ 30 product import ready
- ✨ Full WooCommerce integration
- ✨ Contact form with AJAX
- ✨ Responsive navigation
- ✨ Collection-specific theming
- ✨ Performance optimization
- ✨ Security hardening
- 📄 Complete documentation

---

## 📄 License

Proprietary. All rights reserved.
© 2025 SkyyRose LLC

---

## 🎉 Credits

**Theme Development**: SkyyRose Team
**Design**: SkyyRose Creative
**Typography**: Google Fonts (Inter, Playfair Display)
**Icons**: Unicode Emoji
**Built With**: WordPress, WooCommerce, PHP, CSS3, JavaScript

---

**Thank you for choosing SkyyRose!**

Where Love Meets Luxury. 🌹✨

---

**Version**: 2.0.0
**Last Updated**: January 30, 2025
**Status**: Production Ready
