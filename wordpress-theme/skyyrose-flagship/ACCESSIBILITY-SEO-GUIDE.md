# Accessibility & SEO Implementation Guide

## Overview

The SkyyRose Flagship Theme implements comprehensive WCAG 2.1 AA compliance and advanced SEO optimization features to ensure maximum accessibility and search engine visibility.

---

## WCAG 2.1 AA Compliance Features

### 1. Semantic HTML5 Structure

All theme templates use proper semantic HTML5 elements:
- `<header>` for site header
- `<nav>` for navigation menus
- `<main>` for primary content
- `<article>` for posts and products
- `<aside>` for sidebars
- `<footer>` for site footer

### 2. ARIA Labels and Roles

#### Implemented ARIA Attributes:
- `aria-label` - Descriptive labels for interactive elements
- `aria-labelledby` - Associates elements with their labels
- `aria-describedby` - Provides additional descriptions
- `aria-expanded` - Indicates expandable element state
- `aria-haspopup` - Indicates popup/dropdown menus
- `aria-hidden` - Hides decorative elements from screen readers
- `aria-live` - Announces dynamic content changes
- `aria-current` - Indicates current page in breadcrumbs
- `aria-required` - Marks required form fields

#### Navigation ARIA Support:
```php
// Primary navigation has aria-label
'container_aria_label' => __( 'Primary Navigation', 'skyyrose-flagship' )

// Menu toggle has aria-expanded
<button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
```

### 3. Keyboard Navigation Support

#### Supported Keys:
- **Tab** - Navigate between interactive elements
- **Shift + Tab** - Navigate backwards
- **Enter** - Activate links and buttons
- **Space** - Activate buttons
- **Escape** - Close modals and dropdowns
- **Arrow Keys** - Navigate menu items

#### Implementation:
```javascript
// Menu keyboard navigation
menuToggle.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle.click();
    }
});
```

### 4. Focus Indicators

All interactive elements have visible focus indicators that meet WCAG 2.1 AA contrast requirements:

- **2px solid outline** with high contrast color (#0073aa)
- **2px offset** for better visibility
- **Box shadow** for additional emphasis
- **3px outline** in high contrast mode

```css
a:focus, button:focus, input:focus {
    outline: 2px solid #0073aa;
    outline-offset: 2px;
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px #0073aa;
}
```

### 5. Skip to Content Link

A skip link is provided at the top of every page:

```html
<a class="skip-link screen-reader-text" href="#primary">Skip to content</a>
```

- Hidden by default (screen reader only)
- Becomes visible when focused
- Allows keyboard users to skip navigation

### 6. Alt Text for Images

All images require alt text:

```php
function skyyrose_ensure_image_alt( $html, $post_id, $attachment_id ) {
    if ( strpos( $html, 'alt=' ) === false ) {
        $alt = get_post_meta( $attachment_id, '_wp_attachment_image_alt', true );
        if ( empty( $alt ) ) {
            $alt = get_the_title( $attachment_id );
        }
        $html = str_replace( '<img', '<img alt="' . esc_attr( $alt ) . '"', $html );
    }
    return $html;
}
```

### 7. Color Contrast Ratios

#### Text Contrast (4.5:1 minimum):
- Primary text: #000 on #fff (21:1)
- Secondary text: #333 on #fff (12.6:1)
- Muted text: #666 on #fff (5.7:1)

#### UI Elements Contrast (3:1 minimum):
- Borders: #666 on #fff (5.7:1)
- Focus indicators: #0073aa on #fff (4.5:1)

#### High Contrast Mode Support:
```css
@media (prefers-contrast: high) {
    a:focus, button:focus, input:focus {
        outline-width: 3px;
        outline-color: currentColor;
    }
}
```

### 8. Screen Reader Announcements

Dynamic content changes are announced to screen readers:

```javascript
// Announce cart updates
$(document.body).on('added_to_cart', function() {
    skyyRoseAnnounce('Product added to cart', 'polite');
});
```

#### ARIA Live Regions:
```html
<div id="skyyrose-announcer-polite" aria-live="polite" aria-atomic="true"></div>
<div id="skyyrose-announcer-assertive" aria-live="assertive" aria-atomic="true"></div>
```

### 9. Form Labels and Error Messages

All form fields have proper labels:

```html
<label for="quantity">Product quantity</label>
<input type="number" id="quantity" name="quantity" aria-required="true">
```

Error messages are clearly marked:

```css
.form-error {
    color: #d63638; /* WCAG AA compliant red */
    font-size: 0.875rem;
    margin-top: 0.25rem;
    display: block;
}
```

### 10. Accessible Modals and Overlays

Modals include:
- **Keyboard trap** - Tab cycles through modal elements
- **Escape key** - Closes modal
- **Focus management** - Focus moves to first element when opened
- **Focus restoration** - Returns focus to trigger element when closed

```javascript
modal.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        // Trap focus within modal
    }
    if (e.key === 'Escape') {
        closeModal();
    }
});
```

### 11. Reduced Motion Support

Respects user's motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
```

### 12. Touch Target Sizing

All interactive elements meet minimum 44x44px touch target size:

```css
.button, .btn, input[type='submit'] {
    min-height: 44px;
    min-width: 44px;
    padding: 12px 24px;
}
```

On mobile devices, targets are increased to 48px:

```css
@media (max-width: 768px) {
    .button { min-height: 48px; }
}
```

---

## SEO Optimization Features

### 1. Schema.org Markup

#### Product Schema:
```json
{
    "@context": "https://schema.org/",
    "@type": "Product",
    "name": "Product Name",
    "description": "Product description",
    "sku": "SKU123",
    "image": "https://example.com/image.jpg",
    "offers": {
        "@type": "Offer",
        "price": "99.99",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock"
    },
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.5",
        "reviewCount": "24"
    }
}
```

#### Organization Schema:
```json
{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Company Name",
    "url": "https://example.com",
    "logo": "https://example.com/logo.png",
    "sameAs": [
        "https://facebook.com/company",
        "https://twitter.com/company"
    ]
}
```

#### BreadcrumbList Schema:
```json
{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "https://example.com"
        }
    ]
}
```

### 2. Open Graph Tags

```html
<meta property="og:type" content="product" />
<meta property="og:title" content="Product Name" />
<meta property="og:description" content="Product description" />
<meta property="og:url" content="https://example.com/product" />
<meta property="og:image" content="https://example.com/image.jpg" />
<meta property="og:site_name" content="Site Name" />

<!-- Product-specific -->
<meta property="product:price:amount" content="99.99" />
<meta property="product:price:currency" content="USD" />
<meta property="product:availability" content="in stock" />
```

### 3. Twitter Cards

```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@username" />
<meta name="twitter:title" content="Product Name" />
<meta name="twitter:description" content="Product description" />
<meta name="twitter:image" content="https://example.com/image.jpg" />
```

### 4. Canonical URLs

Every page has a canonical URL to prevent duplicate content:

```php
function skyyrose_canonical_url() {
    if ( is_singular() ) {
        echo '<link rel="canonical" href="' . esc_url( get_permalink() ) . '" />';
    }
}
```

### 5. Meta Descriptions

Automatically generated meta descriptions for all pages:

```html
<meta name="description" content="Page description optimized for search engines" />
```

### 6. Title Tag Optimization

```php
function skyyrose_document_title( $title ) {
    if ( ! is_front_page() ) {
        $title .= ' | ' . get_bloginfo( 'name' );
    }
    if ( $paged >= 2 ) {
        $title .= ' | Page ' . $paged;
    }
    return $title;
}
```

### 7. Breadcrumb Navigation

Visual and structured breadcrumbs on all pages:

```html
<nav class="breadcrumb-navigation" aria-label="Breadcrumb">
    <ol class="breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList">
        <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
            <a href="/" itemprop="item">
                <span itemprop="name">Home</span>
            </a>
            <meta itemprop="position" content="1" />
        </li>
    </ol>
</nav>
```

### 8. XML Sitemap Integration

WordPress core sitemap is enabled with product enhancements:

```php
add_theme_support( 'core-sitemaps' );
```

Sitemap available at: `https://yoursite.com/wp-sitemap.xml`

### 9. Robots Meta Tags

```php
// Search and 404 pages
<meta name="robots" content="noindex,follow" />

// Attachment pages
<meta name="robots" content="noindex,nofollow" />
```

### 10. Structured Data for Collections

Product category pages include CollectionPage schema:

```json
{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Category Name",
    "description": "Category description",
    "url": "https://example.com/category"
}
```

---

## Testing & Validation

### Accessibility Testing Tools

1. **WAVE** - https://wave.webaim.org/
   - Comprehensive accessibility evaluation
   - Visual feedback on page elements
   - Contrast analysis

2. **Axe DevTools** - https://www.deque.com/axe/
   - Browser extension for developers
   - Automated accessibility testing
   - Detailed violation reports

3. **NVDA Screen Reader** - https://www.nvaccess.org/
   - Free screen reader for Windows
   - Test actual screen reader experience

4. **Google Lighthouse** - Built into Chrome
   - Accessibility score
   - Performance metrics
   - Best practices audit

5. **Color Contrast Analyzer** - https://www.tpgi.com/color-contrast-checker/
   - WCAG contrast ratio testing
   - Color blindness simulation

### SEO Testing Tools

1. **Google Rich Results Test** - https://search.google.com/test/rich-results
   - Validates structured data
   - Preview how content appears in search

2. **Google Search Console** - https://search.google.com/search-console
   - Monitor search performance
   - Submit sitemaps
   - Check indexing status

3. **Schema.org Validator** - https://validator.schema.org/
   - Validate JSON-LD markup
   - Check schema accuracy

4. **Facebook Sharing Debugger** - https://developers.facebook.com/tools/debug/
   - Test Open Graph tags
   - Preview social shares

5. **Twitter Card Validator** - https://cards-dev.twitter.com/validator
   - Test Twitter Card markup
   - Preview tweets with cards

6. **PageSpeed Insights** - https://pagespeed.web.dev/
   - Core Web Vitals
   - Performance recommendations
   - Mobile usability

### Manual Testing Checklist

#### Keyboard Navigation Tests:
- [ ] Navigate entire site using Tab key only
- [ ] Test all buttons with Enter and Space keys
- [ ] Verify all dropdowns open/close with keyboard
- [ ] Test modal keyboard trap (Tab cycles within modal)
- [ ] Verify Escape key closes modals
- [ ] Check skip link appears on Tab and works
- [ ] Test form submission with keyboard only

#### Screen Reader Tests:
- [ ] Test with NVDA (Windows) or VoiceOver (Mac)
- [ ] Verify heading hierarchy is logical (H1 → H2 → H3)
- [ ] Check all images have descriptive alt text
- [ ] Verify form labels are announced
- [ ] Test ARIA live regions announce updates
- [ ] Check landmark roles are announced correctly
- [ ] Verify links have descriptive text

#### Visual Tests:
- [ ] Check focus indicators are visible on all elements
- [ ] Verify color contrast meets 4.5:1 for text
- [ ] Verify color contrast meets 3:1 for UI elements
- [ ] Test in high contrast mode
- [ ] Verify touch targets are at least 44x44px
- [ ] Check responsive design on mobile

#### SEO Validation:
- [ ] Run Google Rich Results Test on product pages
- [ ] Validate all schema markup
- [ ] Check meta descriptions are under 160 characters
- [ ] Verify canonical URLs are correct
- [ ] Test Open Graph tags with Facebook Debugger
- [ ] Validate Twitter Cards
- [ ] Check XML sitemap includes all pages
- [ ] Verify robots.txt is accessible

---

## Configuration

### Customizer Settings

Configure social media and contact information in **Appearance → Customize**:

#### Social Media (for Organization Schema):
- Facebook URL
- Twitter Handle & URL
- Instagram URL
- LinkedIn URL
- YouTube URL

#### Contact Information:
- Contact Phone Number
- Contact Email Address

### Theme Options

Access accessibility testing tools in **Appearance → A11y & SEO**:
- WCAG 2.1 AA compliance checklist
- SEO features checklist
- Quick testing tools
- Manual testing checklist

---

## Best Practices

### For Content Editors:

1. **Always add alt text to images**
   - Be descriptive but concise
   - Include relevant keywords naturally
   - For decorative images, use empty alt=""

2. **Use heading hierarchy properly**
   - Only one H1 per page (page title)
   - Don't skip heading levels
   - Use headings for structure, not styling

3. **Write descriptive link text**
   - ❌ "Click here"
   - ✅ "View our product catalog"

4. **Add captions to complex images**
   - Charts, graphs, infographics
   - Provide text alternative

5. **Create accessible tables**
   - Use table headers
   - Keep tables simple
   - Provide table summary if complex

### For Developers:

1. **Use semantic HTML**
   - Choose elements for meaning, not appearance
   - Use `<button>` for actions, `<a>` for links

2. **Don't rely on color alone**
   - Use icons, text, or patterns
   - Ensure information is conveyed in multiple ways

3. **Test with keyboard only**
   - Unplug your mouse
   - Navigate your implementation

4. **Test with screen reader**
   - Install NVDA or use VoiceOver
   - Listen to your content

5. **Maintain focus order**
   - Tab order should be logical
   - Don't use positive tabindex values

---

## Resources

### WCAG Guidelines:
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM WCAG Checklist](https://webaim.org/standards/wcag/checklist)

### Schema.org:
- [Schema.org Documentation](https://schema.org/)
- [Google Structured Data Guide](https://developers.google.com/search/docs/advanced/structured-data/intro-structured-data)

### Accessibility:
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [A11y Project](https://www.a11yproject.com/)

### SEO:
- [Google Search Central](https://developers.google.com/search)
- [Moz Beginner's Guide to SEO](https://moz.com/beginners-guide-to-seo)

---

## Support

For questions or issues related to accessibility and SEO features:

1. Check this documentation first
2. Run automated tests using the tools listed above
3. Review the manual testing checklist
4. Consult WCAG 2.1 AA guidelines for specific requirements

---

## Changelog

### Version 1.0.0
- Initial implementation of WCAG 2.1 AA compliance features
- Complete SEO optimization with Schema.org markup
- Accessibility testing tools page
- Comprehensive documentation

---

**Last Updated:** February 8, 2026
**WCAG Level:** AA (Level 2.1)
**SEO Compliance:** Full Schema.org, Open Graph, Twitter Cards
