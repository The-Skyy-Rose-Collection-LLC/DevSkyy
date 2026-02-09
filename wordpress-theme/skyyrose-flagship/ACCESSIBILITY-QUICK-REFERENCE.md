# Accessibility Quick Reference Card

Quick reference for developers working with the SkyyRose Flagship Theme.

---

## Essential Functions

### Screen Reader Announcements
```javascript
// Announce message to screen readers
skyyRoseAnnounce('Item added to cart', 'polite');
skyyRoseAnnounce('Error: Form validation failed', 'assertive');
```

**Priority levels:**
- `polite` - Wait for current speech to finish
- `assertive` - Interrupt current speech

---

## Common ARIA Patterns

### Buttons
```html
<button
    type="button"
    aria-label="Close dialog"
    aria-pressed="false">
    <span aria-hidden="true">×</span>
</button>
```

### Links
```html
<a href="/products" aria-label="View all products">
    Shop Now
</a>
```

### Dropdowns
```html
<button
    aria-haspopup="true"
    aria-expanded="false"
    aria-controls="dropdown-menu">
    Menu
</button>
<ul id="dropdown-menu" aria-hidden="true">
    <!-- Menu items -->
</ul>
```

### Modals
```html
<div role="dialog"
     aria-modal="true"
     aria-labelledby="modal-title"
     aria-describedby="modal-desc">
    <h2 id="modal-title">Modal Title</h2>
    <p id="modal-desc">Modal description</p>
</div>
```

### Form Fields
```html
<label for="email">Email Address</label>
<input
    type="email"
    id="email"
    name="email"
    aria-required="true"
    aria-describedby="email-error">
<span id="email-error" class="form-error">
    Please enter a valid email
</span>
```

### Loading States
```html
<button aria-busy="true" aria-live="polite">
    Loading...
</button>
```

---

## Keyboard Event Handling

### Standard Pattern
```javascript
element.addEventListener('keydown', function(e) {
    switch(e.key) {
        case 'Enter':
        case ' ':
            e.preventDefault();
            element.click();
            break;
        case 'Escape':
            closeElement();
            break;
        case 'ArrowDown':
            navigateDown();
            break;
        case 'ArrowUp':
            navigateUp();
            break;
    }
});
```

### Menu Navigation
```javascript
// Tab through menu items
menuItem.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight') {
        nextItem.focus();
    }
    if (e.key === 'ArrowLeft') {
        prevItem.focus();
    }
});
```

---

## Focus Management

### Set Focus
```javascript
// Focus element and make it focusable
element.setAttribute('tabindex', '-1');
element.focus();
```

### Trap Focus in Modal
```javascript
function trapFocus(element) {
    const focusable = element.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    });
}
```

### Restore Focus
```javascript
// Store current focus
const previousFocus = document.activeElement;

// Later, restore focus
previousFocus.focus();
```

---

## CSS Classes

### Screen Reader Only
```html
<span class="screen-reader-text">
    Additional context for screen readers
</span>
```

### Skip Link
```html
<a class="skip-link screen-reader-text" href="#main">
    Skip to main content
</a>
```

### ARIA Live Region
```html
<div class="aria-live-region" aria-live="polite">
    Dynamic content announcements
</div>
```

### Form Error
```html
<span class="form-error">
    Error message text
</span>
```

---

## WooCommerce Patterns

### Add to Cart Button
```php
<button
    class="add_to_cart_button"
    aria-label="<?php echo esc_attr( sprintf(
        __( 'Add %s to cart', 'skyyrose-flagship' ),
        get_the_title()
    ) ); ?>">
    <?php _e( 'Add to Cart', 'skyyrose-flagship' ); ?>
</button>
```

### Quantity Input
```php
<label for="quantity-<?php echo $product->get_id(); ?>" class="screen-reader-text">
    <?php _e( 'Product quantity', 'skyyrose-flagship' ); ?>
</label>
<input
    type="number"
    id="quantity-<?php echo $product->get_id(); ?>"
    class="qty"
    name="quantity"
    aria-label="<?php esc_attr_e( 'Product quantity', 'skyyrose-flagship' ); ?>"
    inputmode="numeric"
    min="1">
```

### Product Image
```php
<?php
$product_name = get_the_title();
$image = get_the_post_thumbnail(
    $product->get_id(),
    'full',
    array(
        'alt' => $product_name,
        'title' => $product_name
    )
);
echo $image;
?>
```

---

## SEO Patterns

### Schema Markup
```php
<?php
$schema = array(
    '@context' => 'https://schema.org/',
    '@type'    => 'Product',
    'name'     => get_the_title(),
    'image'    => get_the_post_thumbnail_url(),
    'offers'   => array(
        '@type'  => 'Offer',
        'price'  => $product->get_price(),
    ),
);
?>
<script type="application/ld+json">
    <?php echo wp_json_encode( $schema, JSON_UNESCAPED_SLASHES ); ?>
</script>
```

### Open Graph Tags
```php
<meta property="og:title" content="<?php echo esc_attr( get_the_title() ); ?>" />
<meta property="og:description" content="<?php echo esc_attr( get_the_excerpt() ); ?>" />
<meta property="og:image" content="<?php echo esc_url( get_the_post_thumbnail_url() ); ?>" />
<meta property="og:url" content="<?php echo esc_url( get_permalink() ); ?>" />
```

### Breadcrumbs
```php
<nav aria-label="<?php esc_attr_e( 'Breadcrumb', 'skyyrose-flagship' ); ?>">
    <ol class="breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList">
        <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
            <a href="<?php echo esc_url( home_url( '/' ) ); ?>" itemprop="item">
                <span itemprop="name"><?php _e( 'Home', 'skyyrose-flagship' ); ?></span>
            </a>
            <meta itemprop="position" content="1" />
        </li>
    </ol>
</nav>
```

---

## Testing Shortcuts

### Browser DevTools
```
F12                  → Open DevTools
Ctrl/Cmd + Shift + P → Command palette
"Lighthouse"         → Run audit
"Contrast"           → Check contrast
```

### Screen Reader Shortcuts

**VoiceOver (Mac):**
```
Cmd + F5             → Toggle VoiceOver
Ctrl + Option + →    → Next item
Ctrl + Option + ←    → Previous item
Ctrl + Option + U    → Rotor (navigation menu)
```

**NVDA (Windows):**
```
Ctrl + Alt + N       → Start NVDA
Insert + Down        → Read from here
H                    → Next heading
B                    → Next button
F                    → Next form field
```

---

## Common Mistakes to Avoid

### ❌ Don't Do This
```html
<!-- Missing label -->
<input type="text" placeholder="Enter email">

<!-- Non-semantic button -->
<div onclick="doSomething()">Click me</div>

<!-- No keyboard support -->
<a href="#" onclick="openModal()">Open</a>

<!-- Inaccessible icon button -->
<button><i class="icon-close"></i></button>

<!-- Poor link text -->
<a href="/products">Click here</a>
```

### ✅ Do This Instead
```html
<!-- Proper label -->
<label for="email">Email Address</label>
<input type="email" id="email" placeholder="you@example.com">

<!-- Semantic button -->
<button type="button" onclick="doSomething()">Click me</button>

<!-- Keyboard accessible -->
<a href="#modal" role="button" aria-haspopup="dialog">Open</a>

<!-- Accessible icon button -->
<button aria-label="Close dialog">
    <i class="icon-close" aria-hidden="true"></i>
</button>

<!-- Descriptive link text -->
<a href="/products">View all products</a>
```

---

## Color Contrast Requirements

### Text
- **Normal text (< 18pt):** 4.5:1 minimum
- **Large text (≥ 18pt):** 3:1 minimum
- **Bold text (≥ 14pt):** 3:1 minimum

### UI Components
- **Borders, icons:** 3:1 minimum
- **Focus indicators:** 3:1 minimum
- **Active elements:** 3:1 minimum

### Safe Color Combinations
```css
/* Text on white background */
--text-primary: #000000;   /* 21:1 */
--text-secondary: #333333; /* 12.6:1 */
--text-muted: #666666;     /* 5.7:1 */

/* Interactive elements */
--link-color: #0073aa;     /* 4.5:1 */
--button-bg: #21759b;      /* 3.9:1 */
--error-color: #d63638;    /* 4.5:1 */
```

---

## Touch Target Sizing

### Minimum Sizes
```css
/* Standard elements */
button, a, input[type="submit"] {
    min-height: 44px;
    min-width: 44px;
}

/* Mobile devices */
@media (max-width: 768px) {
    button, a, input[type="submit"] {
        min-height: 48px;
    }
}
```

### Spacing
```css
/* Minimum spacing between touch targets */
.touch-target + .touch-target {
    margin-left: 8px; /* Minimum 8px gap */
}
```

---

## WordPress Hooks

### Add Accessibility Features
```php
// After header (breadcrumbs)
add_action( 'skyyrose_after_header', 'your_function' );

// Footer (ARIA live regions)
add_action( 'wp_footer', 'your_function' );

// Head (meta tags, schema)
add_action( 'wp_head', 'your_function' );
```

### Filter Examples
```php
// Modify navigation args
add_filter( 'wp_nav_menu_args', function( $args ) {
    if ( $args['theme_location'] === 'primary' ) {
        $args['container_aria_label'] = 'Main Navigation';
    }
    return $args;
} );

// Ensure image alt text
add_filter( 'post_thumbnail_html', function( $html, $post_id, $attachment_id ) {
    // Add alt text if missing
    return $html;
}, 10, 3 );
```

---

## Quick Test Commands

### Validate HTML
```bash
# Using W3C validator
curl -H "Content-Type: text/html; charset=utf-8" \
     --data-binary @page.html \
     https://validator.w3.org/nu/?out=json
```

### Test Contrast
```bash
# Chrome DevTools
1. Right-click element
2. Inspect
3. Click color swatch in Styles panel
4. View contrast ratio
```

### Test Keyboard Navigation
```
1. Unplug mouse
2. Press Tab repeatedly
3. Verify all elements are reachable
4. Verify focus indicator is visible
5. Test with Enter/Space keys
```

---

## Resources

- [WCAG Quick Ref](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Articles](https://webaim.org/articles/)
- [Schema.org](https://schema.org/)

---

**Print this page for quick desk reference!**
