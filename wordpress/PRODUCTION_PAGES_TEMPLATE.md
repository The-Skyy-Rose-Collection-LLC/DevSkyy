# Production Pages Template

After cleaning up old pages, create these production pages using the templates below.

## Pages to Create

| Slug | Title | Type | Status | Parent | Featured Image |
|------|-------|------|--------|--------|-----------------|
| / | Home | Page | Publish | - | SkyyRose Hero |
| /shop | Shop | Page | Publish | - | Products Hero |
| /experiences/signature | Signature Collection | Page | Publish | - | Signature Hero |
| /experiences/black-rose | Black Rose Collection | Page | Publish | - | Black Rose Hero |
| /experiences/love-hurts | Love Hurts Collection | Page | Publish | - | Love Hurts Hero |
| /about | About SkyyRose | Page | Publish | - | About Hero |
| /contact | Contact | Page | Publish | - | Contact Hero |

---

## 1. Home Page

**URL**: `/` or `/home`
**Slug**: (none, this is home)
**Template**: (Elementor or theme default)

```html
<!-- Hero Section -->
[collection_logo collection="signature" size="hero"]

<h1>Where Love Meets Luxury</h1>
<p>Experience the SkyyRose Collection - 3D-designed, AR-enabled fashion</p>

<!-- Call-to-Action -->
[button text="Explore Collections" url="/experiences/signature/" style="primary"]

<!-- Featured Collections Grid -->
<div class="collections-grid">
  <div class="collection-card">
    <h3>Signature Collection</h3>
    [collection_logo collection="signature" size="large"]
    <p>Rose gold elegance with sophisticated details</p>
    [button text="View Collection" url="/experiences/signature/"]
  </div>

  <div class="collection-card">
    <h3>Black Rose Collection</h3>
    [collection_logo collection="black-rose" size="large"]
    <p>Gothic sophistication with cosmic allure</p>
    [button text="View Collection" url="/experiences/black-rose/"]
  </div>

  <div class="collection-card">
    <h3>Love Hurts Collection</h3>
    [collection_logo collection="love-hurts" size="large"]
    <p>Passionate crimson with emotional depth</p>
    [button text="View Collection" url="/experiences/love-hurts/"]
  </div>
</div>

<!-- Latest Products -->
<h2>Latest Releases</h2>
[products limit="12" columns="4" orderby="date" order="DESC"]

<!-- Newsletter Signup -->
[newsletter_signup heading="Stay Updated" button_text="Subscribe"]
```

---

## 2. Signature Collection Experience Page

**URL**: `/experiences/signature`
**Slug**: `signature`
**Parent Page**: (Create `/experiences` parent first)

```html
[collection_logo collection="signature" size="hero"]

<h1>Signature Collection</h1>
<p class="subtitle">
  Rose gold elegance meets modern luxury. Each piece crafted with
  precision and elevated with 3D design and AR try-on technology.
</p>

<!-- Collection 3D Viewer -->
<h2>3D Experience</h2>
[skyyrose_collection_experience collection="signature" enable_ar="true"]

<!-- Product Showcase -->
<h2>Featured Pieces</h2>
[products category="19" columns="3" limit="9" orderby="popularity"]

<!-- Virtual Try-On -->
<h2>Try Before You Buy</h2>
<p>Use our AR virtual try-on feature to see how pieces look on you.</p>
[skyyrose_virtual_tryon product_id="all" category="signature" show_size_guide="true"]

<!-- Collection Story -->
<h2>The Story</h2>
<p>
  The Signature Collection represents the pinnacle of SkyyRose design.
  With rose gold accents and timeless elegance, each piece is designed
  to make a statement.
</p>

<!-- Size & Care Guide -->
[accordion title="Size Guide"]
[table_of_contents]

[accordion title="Care Instructions"]
Always hand wash in cold water. Air dry only.
```

---

## 3. Black Rose Collection Experience Page

**URL**: `/experiences/black-rose`
**Slug**: `black-rose`
**Parent Page**: `/experiences`

```html
[collection_logo collection="black-rose" size="hero"]

<h1>Black Rose Collection</h1>
<p class="subtitle">
  Dark. Elegant. Cosmic. Where gothic sophistication meets modern luxury.
  Explore our exclusive Black Rose collection with immersive 3D and AR.
</p>

<!-- Collection 3D Viewer -->
<h2>3D Experience</h2>
[skyyrose_collection_experience collection="black-rose" enable_ar="true"]

<!-- Product Showcase -->
<h2>Featured Pieces</h2>
[products category="20" columns="3" limit="9" orderby="popularity"]

<!-- Virtual Try-On -->
<h2>Virtual Try-On</h2>
<p>Experience the Black Rose Collection with AR technology</p>
[skyyrose_virtual_tryon product_id="all" category="black-rose" show_size_guide="true"]

<!-- Collection Philosophy -->
<h2>The Vision</h2>
<p>
  Inspired by cosmic mystery and gothic elegance, the Black Rose Collection
  pushes boundaries. Each design combines silver metallics with cosmic
  influences for a truly otherworldly aesthetic.
</p>
```

---

## 4. Love Hurts Collection Experience Page

**URL**: `/experiences/love-hurts`
**Slug**: `love-hurts`
**Parent Page**: `/experiences`

```html
[collection_logo collection="love-hurts" size="hero"]

<h1>Love Hurts Collection</h1>
<p class="subtitle">
  Passionate. Bold. Unforgettable. Explore crimson elegance
  with emotional depth and stunning 3D design.
</p>

<!-- Collection 3D Viewer -->
<h2>3D Experience</h2>
[skyyrose_collection_experience collection="love-hurts" enable_ar="true"]

<!-- Product Showcase -->
<h2>Featured Pieces</h2>
[products category="18" columns="3" limit="9" orderby="popularity"]

<!-- Virtual Try-On -->
<h2>Virtual Try-On</h2>
<p>Feel the passion with our AR virtual try-on experience</p>
[skyyrose_virtual_tryon product_id="all" category="love-hurts" show_size_guide="true"]

<!-- Collection Narrative -->
<h2>Where Passion Lives</h2>
<p>
  The Love Hurts Collection is bold, unapologetic, and deeply emotional.
  Crimson and gold create a narrative of passion and strength.
  Every piece tells a story of love, resilience, and beauty.
</p>
```

---

## 5. Shop Page

**URL**: `/shop`
**Slug**: `shop`

```html
<h1>Shop SkyyRose</h1>
<p>Explore our complete collection of luxury fashion with 3D design and AR technology</p>

<!-- Featured Collections Filter -->
<div class="collection-filter">
  [button text="All Products" url="/shop"]
  [button text="Signature" url="/shop?category=signature"]
  [button text="Black Rose" url="/shop?category=black-rose"]
  [button text="Love Hurts" url="/shop?category=love-hurts"]
</div>

<!-- Product Grid -->
[products columns="4" limit="24" orderby="popularity"]

<!-- Pagination -->
[pagination]

<!-- Virtual Try-On CTA -->
<div class="try-on-banner">
  <h2>Not Sure? Try It First!</h2>
  <p>Use our AR virtual try-on to see pieces before you buy</p>
  [button text="Start AR Try-On" url="/virtual-try-on/"]
</div>
```

---

## 6. About Page

**URL**: `/about`
**Slug**: `about`

```html
<h1>About SkyyRose</h1>

<h2>Our Story</h2>
<p>
  SkyyRose is a luxury fashion brand pushing the boundaries of design
  with 3D technology and augmented reality. Founded with a vision to
  create experiences, not just products.
</p>

<h2>Our Collections</h2>

### Signature Collection
Rose gold elegance with timeless designs for the sophisticated lover of luxury.

### Black Rose Collection
Gothic mystery meets cosmic adventure. For the bold and unapologetic.

### Love Hurts Collection
Passionate, red-hot luxury. For those who wear their hearts on their sleeves.

<h2>Why Choose SkyyRose?</h2>
- ✨ 3D-Designed Luxury Fashion
- 📱 AR Virtual Try-On Technology
- 🎨 Exclusive Collections
- 💫 Sustainable & Ethical
- 🌍 Global Shipping

<h2>Our Commitment</h2>
<p>
  We believe fashion is an experience. That's why every SkyyRose piece
  includes 3D models you can view and AR try-on technology to visualize
  your purchase before buying.
</p>

[team_members]
```

---

## 7. Contact Page

**URL**: `/contact`
**Slug**: `contact`

```html
<h1>Get in Touch</h1>
<p>Have questions? We'd love to hear from you.</p>

<!-- Contact Form -->
[contact_form
  to="hello@skyyrose.com"
  subject="New Contact from SkyyRose.co"
  success_message="Thanks for reaching out! We'll be in touch soon."
]

<!-- Contact Info -->
<div class="contact-info">
  <h3>📧 Email</h3>
  <p><a href="mailto:hello@skyyrose.com">hello@skyyrose.com</a></p>

  <h3>🌐 Social</h3>
  <ul>
    <li><a href="https://instagram.com/skyyrose">Instagram</a></li>
    <li><a href="https://tiktok.com/@skyyrose">TikTok</a></li>
    <li><a href="https://twitter.com/skyyrose">Twitter/X</a></li>
  </ul>

  <h3>🏪 Store</h3>
  <p>SkyyRose Flagship, The Luxury District</p>
</div>

<!-- FAQ -->
<h2>Frequently Asked Questions</h2>
[accordion_faq]
```

---

## How to Create Pages

### Via WordPress Admin (Recommended)

1. **Go to Pages → Add New**
2. **Add Title** (from table above)
3. **Set Slug** (if needed)
4. **Paste content** from templates above
5. **Set Parent Page** (if applicable)
6. **Publish**

### Via Script (Post-OAuth Setup)

```bash
python scripts/create_wordpress_pages.py
```

---

## Shortcodes Used

| Shortcode | Purpose | Example |
|-----------|---------|---------|
| `[collection_logo]` | Display rotating logo | `[collection_logo collection="signature" size="large"]` |
| `[skyyrose_collection_experience]` | 3D viewer + AR | `[skyyrose_collection_experience collection="signature" enable_ar="true"]` |
| `[skyyrose_virtual_tryon]` | Virtual try-on | `[skyyrose_virtual_tryon product_id="all" category="signature"]` |
| `[products]` | Product grid | `[products category="19" columns="3" limit="9"]` |
| `[button]` | Call-to-action | `[button text="Learn More" url="/about/"]` |
| `[contact_form]` | Contact form | `[contact_form to="email@example.com"]` |

See: `wordpress/shortcodes.py` for full documentation

---

## Parent Pages

Before creating collection pages, ensure parent page exists:

```
/experiences/
  - /experiences/signature/
  - /experiences/black-rose/
  - /experiences/love-hurts/
```

Create `/experiences` first as a parent page with this slug.
