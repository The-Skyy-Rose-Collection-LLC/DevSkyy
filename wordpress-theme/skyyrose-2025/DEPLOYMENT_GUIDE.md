# SkyyRose 2025 WordPress Theme - Deployment Guide

## 🚀 Complete Production Deployment (Tonight-Ready)

This guide will take you from zero to live website in under 2 hours.

---

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] WordPress 6.0+ installed
- [ ] WooCommerce 8.0+ installed and activated
- [ ] PHP 8.0+ running with Sodium extension enabled
- [ ] MySQL 5.7+ or MariaDB 10.3+
- [ ] SSL certificate configured (HTTPS) - REQUIRED
- [ ] Domain pointed to hosting

### Security Requirements (v3.0.0)
- [ ] HTTPS enabled and enforced
- [ ] PHP Sodium extension available (for encryption)
- [ ] WordPress salts/keys regenerated for production
- [ ] Contact email configured in theme settings
- [ ] Rate limiting tested on AJAX endpoints
- [ ] CSRF tokens verified on all forms
- [ ] Security headers verified (see SECURITY_HARDENING_COMPLETE.md)

---

## 📦 Phase 1: Theme Installation (15 minutes)

### Step 1: Upload Theme Files

**Option A: Via FTP/SFTP**
```bash
# Upload entire skyyrose-2025 folder to:
/wp-content/themes/skyyrose-2025/
```

**Option B: Via WordPress Admin**
1. Compress `skyyrose-2025` folder as ZIP
2. Go to **Appearance > Themes > Add New > Upload Theme**
3. Upload ZIP file
4. Click **Activate**

### Step 2: Install Required Plugins

Go to **Plugins > Add New** and install:

1. **WooCommerce** (required)
   - Configure basic settings (currency, location, shipping)

2. **Contact Form 7** (recommended) OR **WPForms** (recommended)
   - For contact page form functionality

3. **Yoast SEO** OR **Rank Math** (recommended)
   - For SEO optimization

4. **WP Rocket** OR **W3 Total Cache** (optional)
   - For performance optimization

5. **Smush** OR **ShortPixel** (recommended)
   - For automatic image optimization

### Step 3: Theme Activation

1. Go to **Appearance > Themes**
2. Find **SkyyRose 2025**
3. Click **Activate**
4. You should see the theme header/footer immediately

---

## 🛍️ Phase 2: WooCommerce Setup (20 minutes)

### Step 1: Basic WooCommerce Settings

Navigate to **WooCommerce > Settings**:

**General Tab:**
- Store Address: Oakland, California
- Currency: USD ($)
- Currency Position: Left

**Products Tab:**
- Weight Unit: lb
- Dimensions Unit: in
- Enable product reviews: Yes

**Shipping Tab:**
- Create Shipping Zones:
  - **US Domestic**: Free shipping over $100, $8 flat rate under
  - **International**: $25 flat rate

**Payments Tab:**
- Enable Stripe/PayPal/Credit Card processing
- Test mode first, then switch to live

### Step 2: Import Product Data

1. Go to **WooCommerce > Products**
2. Click **Import** at the top
3. Upload `PRODUCT_DATA.csv` from theme folder
4. Map columns (should auto-detect)
5. Click **Run the importer**

**Expected Result:** 30 products imported across 3 collections

### Step 3: Configure Product Meta Fields

For each product, you'll need to add custom fields. Go to **Products > [Product Name] > Edit**:

In the **Product Data** metabox, add:
- **Regular Price** (already imported from CSV)
- **Inventory** (manage stock, set quantities)
- **Categories** (Tops, Bottoms, Outerwear, etc.)

In the **Custom Fields** section (scroll down):
- `_skyyrose_collection`: `black-rose` | `love-hurts` | `signature`
- `_product_badge`: `NEW` | `LIMITED` | `EXCLUSIVE` (optional)
- `_fabric_composition`: (from CSV)
- `_care_instructions`: (from CSV)

**Note:** This is tedious but crucial. Alternatively, use a plugin like **Advanced Custom Fields** to bulk-edit.

---

## 📄 Phase 3: Create Pages (30 minutes)

### Step 1: Create Main Pages

Go to **Pages > Add New** for each:

#### 1. Home Page
- **Title**: Home
- **Template**: SkyyRose Home (select from Template dropdown)
- **Publish** and set as homepage:
  - Go to **Settings > Reading**
  - Set "Your homepage displays" to "A static page"
  - Select "Home" as Homepage

#### 2. Black Rose Experience
- **Title**: Black Rose Experience
- **Slug**: `01-black-rose-garden`
- **Template**: Immersive Experience
- **Custom Fields**:
  - `_collection_type`: `black-rose`

#### 3. Love Hurts Experience
- **Title**: Love Hurts Experience
- **Slug**: `02-love-hurts-castle`
- **Template**: Immersive Experience
- **Custom Fields**:
  - `_collection_type`: `love-hurts`

#### 4. Signature Experience
- **Title**: Signature Experience
- **Slug**: `03-signature-runway`
- **Template**: Immersive Experience
- **Custom Fields**:
  - `_collection_type`: `signature`

#### 5. Black Rose Collection
- **Title**: Black Rose Collection
- **Slug**: `black-rose`
- **Template**: Collection - Signature
- **Custom Fields**:
  - `_collection_type`: `black-rose`

#### 6. Love Hurts Collection
- **Title**: Love Hurts Collection
- **Slug**: `love-hurts`
- **Template**: Collection - Signature
- **Custom Fields**:
  - `_collection_type`: `love-hurts`

#### 7. Signature Collection
- **Title**: Signature Collection
- **Slug**: `signature`
- **Template**: Collection - Signature
- **Custom Fields**:
  - `_collection_type`: `signature`

#### 8. The Vault
- **Title**: The Vault
- **Slug**: `vault`
- **Template**: The Vault - Pre-Order
- **Note**: Products shown here need `_vault_preorder` meta = `1`

#### 9. About
- **Title**: About
- **Slug**: `about`
- **Template**: About SkyyRose

#### 10. Contact
- **Title**: Contact
- **Slug**: `contact`
- **Template**: Contact

### Step 2: Create Product Categories

Go to **Products > Categories** and create:

1. **Tops**
2. **Bottoms**
3. **Outerwear**
4. **Dresses**
5. **Accessories**
6. **Footwear**
7. **Hoodies** (sub-category of Tops)

### Step 3: Assign Categories to Products

Bulk edit products:
1. Go to **Products > All Products**
2. Select multiple products (checkbox)
3. Choose **Bulk Actions > Edit**
4. Assign categories

---

## 🧭 Phase 4: Navigation Menus (15 minutes)

### Step 1: Create Main Menu

Go to **Appearance > Menus**:

1. **Create New Menu**: "Main Menu"
2. **Add Menu Items**:
   - Home (/)
   - **Collections** (Custom Link: `#`)
     - Black Rose Experience (submenu)
     - Shop Black Rose (submenu)
     - Love Hurts Experience (submenu)
     - Shop Love Hurts (submenu)
     - Signature Experience (submenu)
     - Shop Signature (submenu)
   - **Pre-Order** (/vault)
   - **About** (/about)
   - **Contact** (/contact)
   - **Cart** (WooCommerce Cart page)

3. **Assign to Location**: Check "Primary Menu"
4. **Save Menu**

### Step 2: Create Footer Menu

1. **Create New Menu**: "Footer Menu"
2. **Add Menu Items**:
   - About
   - Contact
   - Shipping & Returns (create page)
   - Privacy Policy (create page)
   - Terms & Conditions (create page)

3. **Assign to Location**: Check "Footer Menu"
4. **Save Menu**

---

## 🎨 Phase 5: Branding & Assets (20 minutes)

### Step 1: Upload Site Logo

1. Go to **Appearance > Customize > Site Identity**
2. Upload SkyyRose logo (white, transparent PNG)
3. Set Site Title: "SkyyRose"
4. Set Tagline: "Where Love Meets Luxury"

### Step 2: Upload Collection Logos

Upload to **Media Library**:
- `BLACK-Rose-LOGO.PNG`
- `Love-Hurts-LOGO.PNG`
- `Signature-LOGO.PNG`

Place in: `/wp-content/uploads/2025/01/logos/`

### Step 3: Add Product Images

See **IMAGE_ASSETS.md** for:
- AI generation with Midjourney
- Free stock photo sources
- Image optimization tools

**Quick Start:**
1. Generate 4-6 images per product using Midjourney
2. Optimize with TinyPNG
3. Upload to WordPress Media Library
4. Assign to products via **Product Gallery**

---

## ⚙️ Phase 6: Essential Settings (10 minutes)

### WooCommerce Permalinks

1. Go to **Settings > Permalinks**
2. Select **Post name** structure
3. Save changes

### WooCommerce Pages

Ensure these pages are created (WooCommerce auto-creates):
- Shop
- Cart
- Checkout
- My Account

### Theme Settings

Go to **Appearance > Customize**:

**Site Identity:**
- Logo uploaded ✓
- Site title and tagline ✓

**Menus:**
- Main menu assigned ✓
- Footer menu assigned ✓

**Homepage Settings:**
- Static page: Home ✓

**Additional CSS (Optional):**
Add any custom brand colors or tweaks.

---

## 🔌 Phase 7: Contact Form Setup (15 minutes)

### Option A: Contact Form 7

1. Install **Contact Form 7** plugin
2. Go to **Contact > Contact Forms**
3. Edit default form with these fields:
   - Name (text, required)
   - Email (email, required)
   - Subject (select: General, Order Status, Product Question, etc.)
   - Message (textarea, required)

4. **Form Code:**
```html
<label>Your Name *
    [text* your-name]
</label>

<label>Email Address *
    [email* your-email]
</label>

<label>Subject *
    [select* your-subject "General Inquiry" "Order Status" "Product Question" "Collaboration" "Press & Media" "Other"]
</label>

<label>Message *
    [textarea* your-message]
</label>

[submit "Send Message"]
```

5. **Mail Settings:**
   - To: `hello@skyyrose.co`
   - From: `[your-name] <[your-email]>`
   - Subject: `Contact Form: [your-subject]`

6. Copy shortcode (e.g., `[contact-form-7 id="123"]`)
7. Edit **Contact** page
8. Paste shortcode in content area

### Option B: Use Custom AJAX Handler (Already in page-contact.php)

The contact page already has JavaScript form handling built-in. You just need to add this to `functions.php`:

```php
// Handle contact form submission
add_action('wp_ajax_skyyrose_contact_form', 'skyyrose_handle_contact_form');
add_action('wp_ajax_nopriv_skyyrose_contact_form', 'skyyrose_handle_contact_form');

function skyyrose_handle_contact_form() {
    // Verify nonce
    if (!isset($_POST['contact_nonce']) || !wp_verify_nonce($_POST['contact_nonce'], 'skyyrose_contact')) {
        wp_send_json_error('Security check failed');
    }

    // Sanitize inputs
    $name = sanitize_text_field($_POST['name']);
    $email = sanitize_email($_POST['email']);
    $subject = sanitize_text_field($_POST['subject']);
    $message = sanitize_textarea_field($_POST['message']);

    // Validate
    if (empty($name) || empty($email) || empty($subject) || empty($message)) {
        wp_send_json_error('All fields are required');
    }

    if (!is_email($email)) {
        wp_send_json_error('Invalid email address');
    }

    // Send email
    $to = 'hello@skyyrose.co';
    $email_subject = "SkyyRose Contact Form: $subject";
    $email_message = "Name: $name\n";
    $email_message .= "Email: $email\n";
    $email_message .= "Subject: $subject\n\n";
    $email_message .= "Message:\n$message";

    $headers = array('Reply-To: ' . $email);

    $sent = wp_mail($to, $email_subject, $email_message, $headers);

    if ($sent) {
        wp_send_json_success('Message sent successfully');
    } else {
        wp_send_json_error('Failed to send message. Please try again.');
    }
}
```

---

## 🚀 Phase 8: Pre-Launch Optimization (10 minutes)

### Step 1: Test All Links

- [ ] Homepage loads correctly
- [ ] All collection pages work
- [ ] Product pages display properly
- [ ] Add to cart functions
- [ ] Checkout process works
- [ ] Contact form submits

### Step 2: Mobile Responsiveness

Test on mobile devices or use:
- Chrome DevTools (F12 > Toggle Device Toolbar)
- BrowserStack (free trial)

### Step 3: Page Speed

Run tests on:
- [Google PageSpeed Insights](https://pagespeed.web.dev/)
- [GTmetrix](https://gtmetrix.com/)

**Target:** 90+ on mobile, 95+ on desktop

**Quick Fixes:**
- Enable caching (WP Rocket or W3 Total Cache)
- Optimize images (Smush plugin)
- Enable lazy loading (built into WordPress 5.5+)

### Step 4: SEO Basics

Using **Yoast SEO** or **Rank Math**:

1. **Homepage:**
   - Title: "SkyyRose | Luxury Streetwear from Oakland"
   - Meta Description: "Where Love Meets Luxury. Oakland-born luxury streetwear with three distinct collections: Black Rose, Love Hurts, and Signature."

2. **Collection Pages:**
   - Title: "[Collection Name] Collection | SkyyRose"
   - Meta Description: Brief collection description

3. **Product Pages:**
   - Auto-generated from product name and description

4. **XML Sitemap:**
   - Generate via Yoast/Rank Math
   - Submit to Google Search Console

---

## 🔒 Phase 9: Security & Backup (5 minutes)

### Security Checklist

- [ ] Install **Wordfence Security** or **Sucuri**
- [ ] Enable two-factor authentication for admin
- [ ] Change default "admin" username
- [ ] Use strong passwords (20+ characters)
- [ ] Limit login attempts
- [ ] Hide WordPress version
- [ ] Disable XML-RPC if not needed

### Backup Setup

Install **UpdraftPlus** or **BackWPup**:
1. Schedule daily backups
2. Store backups offsite (Dropbox, Google Drive, AWS S3)
3. Test restore process once

---

## 🎉 Phase 10: Go Live! (5 minutes)

### Final Checklist

- [ ] All products imported (30 products)
- [ ] All pages created (10+ pages)
- [ ] Navigation menus configured
- [ ] Contact form working
- [ ] SSL certificate active (HTTPS)
- [ ] Google Analytics installed
- [ ] Facebook Pixel installed (optional)
- [ ] Social media links updated

### Launch Steps

1. **Remove "Coming Soon" or Maintenance Mode** (if active)
2. **Set Site to Public**:
   - Go to **Settings > Reading**
   - Uncheck "Discourage search engines"
3. **Clear All Caches**:
   - WordPress cache
   - Browser cache
   - CDN cache (if using Cloudflare)
4. **Test Live Site**:
   - Visit in incognito mode
   - Test checkout process with test order
5. **Announce Launch**:
   - Email newsletter
   - Social media posts
   - Press release (optional)

---

## 📊 Post-Launch Monitoring (First 24 Hours)

### Monitor These Metrics

- **Traffic**: Google Analytics
- **Errors**: Check error logs in hosting cPanel
- **Orders**: WooCommerce > Orders
- **Performance**: PageSpeed Insights
- **Uptime**: UptimeRobot (free monitoring)

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Images not loading | Check file permissions (755 for folders, 644 for files) |
| Checkout errors | Verify payment gateway test/live mode |
| Slow loading | Enable caching, optimize images |
| Menu not showing | Re-assign menu location in Customizer |
| Contact form not sending | Check SMTP settings or use WP Mail SMTP plugin |

---

## 🛠️ Advanced Customization (Optional)

### Add Google Fonts

Already included via `functions.php`:
- Inter (body text)
- Playfair Display (headings)

### Custom CSS

Go to **Appearance > Customize > Additional CSS**:

```css
/* Example: Override primary color */
:root {
    --signature-gold: #YOUR_COLOR;
}

/* Example: Adjust header */
.site-header {
    background: rgba(0, 0, 0, 0.95);
}
```

### Add Instagram Feed

1. Install **Smash Balloon Instagram Feed** plugin
2. Connect Instagram account
3. Add shortcode to footer or homepage

### Email Marketing Integration

Connect **Mailchimp** or **Klaviyo**:
1. Install respective plugin
2. Add signup form to footer
3. Create welcome email sequence

---

## 📞 Support & Resources

### Documentation
- WooCommerce Docs: https://woocommerce.com/documentation/
- WordPress Codex: https://codex.wordpress.org/

### Troubleshooting
- WordPress Support Forums: https://wordpress.org/support/
- WooCommerce Support: https://woocommerce.com/my-account/create-a-ticket/

### SkyyRose Theme Support
- Email: hello@skyyrose.co
- Documentation: This file
- Image Assets: `IMAGE_ASSETS.md`
- Product Data: `PRODUCT_DATA.csv`

---

## 🎯 Success Metrics (First 30 Days)

Track these KPIs:
- **Traffic**: Unique visitors
- **Conversion Rate**: % of visitors who purchase
- **Average Order Value**: Total revenue / number of orders
- **Bounce Rate**: % of single-page sessions
- **Cart Abandonment**: % of started checkouts not completed

**Targets:**
- Conversion Rate: 2-5% (industry average for fashion e-commerce)
- Average Order Value: $150-200 (based on product pricing)
- Bounce Rate: <50%
- Page Load Time: <3 seconds

---

## 🔄 Maintenance Schedule

### Daily
- [ ] Check for new orders
- [ ] Respond to contact form submissions
- [ ] Monitor error logs

### Weekly
- [ ] Review analytics
- [ ] Update product inventory
- [ ] Check for plugin updates
- [ ] Backup database

### Monthly
- [ ] Update WordPress core
- [ ] Update plugins and theme
- [ ] Review security logs
- [ ] Analyze sales data
- [ ] A/B test product descriptions or images

---

## 🚨 Emergency Contacts

If site goes down:
1. Check hosting status page
2. Contact hosting support
3. Check error logs in cPanel
4. Restore from backup if needed

**Hosting Support** (varies by provider):
- Bluehost: 888-401-4678
- SiteGround: Live chat
- WP Engine: Support portal

---

**Deployment Completed ✓**

Your SkyyRose luxury streetwear e-commerce site is now LIVE!

**Next Steps:**
1. Monitor first orders
2. Gather customer feedback
3. Iterate on product descriptions based on analytics
4. Plan marketing campaigns
5. Consider adding blog for SEO

---

**Last Updated**: January 30, 2025
**Version**: 2.0.0
**Deployment Time**: ~2 hours (with product images ready)

Good luck with your launch! 🚀✨
