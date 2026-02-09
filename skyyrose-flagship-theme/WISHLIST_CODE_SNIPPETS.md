# Wishlist Code Snippets & Examples

Quick copy-paste code snippets for common wishlist customizations.

---

## PHP Code Snippets

### Display Wishlist Count Anywhere

```php
<?php
// Display wishlist count in any template
$count = skyyrose_get_wishlist_count();
echo sprintf( esc_html__( 'You have %d items in your wishlist', 'skyyrose-flagship' ), $count );
?>
```

### Custom Wishlist Button

```php
<?php
// Add custom wishlist button with your own markup
global $product;
$product_id = $product->get_id();
$in_wishlist = skyyrose_is_in_wishlist( $product_id );
?>

<button
  class="custom-wishlist-btn <?php echo $in_wishlist ? 'active' : ''; ?>"
  data-product-id="<?php echo esc_attr( $product_id ); ?>"
  type="button">
  <?php echo $in_wishlist ? 'Remove from Wishlist' : 'Add to Wishlist'; ?>
</button>
```

### Get Wishlist Items with Product Data

```php
<?php
$wishlist = skyyrose_get_wishlist_items();

if ( ! empty( $wishlist ) ) {
  foreach ( $wishlist as $product_id ) {
    $product = wc_get_product( $product_id );

    if ( $product ) {
      echo '<div class="wishlist-item">';
      echo '<h3>' . esc_html( $product->get_name() ) . '</h3>';
      echo '<p>' . $product->get_price_html() . '</p>';
      echo '<img src="' . esc_url( wp_get_attachment_url( $product->get_image_id() ) ) . '" />';
      echo '</div>';
    }
  }
}
?>
```

### Add Custom Hook After Wishlist Add

```php
<?php
// functions.php
add_action( 'skyyrose_added_to_wishlist', 'my_custom_wishlist_action', 10, 1 );

function my_custom_wishlist_action( $product_id ) {
  $product = wc_get_product( $product_id );

  // Send email notification
  $to = get_option( 'admin_email' );
  $subject = 'New Wishlist Item Added';
  $message = sprintf(
    'Product "%s" was added to a wishlist.',
    $product->get_name()
  );

  wp_mail( $to, $subject, $message );
}
?>
```

### Custom Widget Area for Wishlist

```php
<?php
// functions.php
function my_wishlist_sidebar() {
  register_sidebar( array(
    'name'          => __( 'Wishlist Sidebar', 'skyyrose-flagship' ),
    'id'            => 'wishlist-sidebar',
    'description'   => __( 'Appears on wishlist page', 'skyyrose-flagship' ),
    'before_widget' => '<div class="widget %2$s">',
    'after_widget'  => '</div>',
    'before_title'  => '<h3 class="widget-title">',
    'after_title'   => '</h3>',
  ) );
}
add_action( 'widgets_init', 'my_wishlist_sidebar' );
?>
```

### Get User's Wishlist from Anywhere

```php
<?php
// Get specific user's wishlist
function get_user_wishlist( $user_id ) {
  $key = 'wishlist_user_' . $user_id;
  return get_option( $key, array() );
}

// Usage
$user_id = 1;
$wishlist = get_user_wishlist( $user_id );
?>
```

---

## JavaScript Code Snippets

### Manually Trigger Add to Wishlist

```javascript
// Add product ID 123 to wishlist programmatically
jQuery.ajax({
  url: skyyRoseWishlist.ajaxUrl,
  type: 'POST',
  data: {
    action: 'skyyrose_add_to_wishlist',
    nonce: skyyRoseWishlist.nonce,
    product_id: 123
  },
  success: function(response) {
    if (response.success) {
      console.log('Added to wishlist!', response.data);
    }
  }
});
```

### Custom Toast Notification

```javascript
// Show custom notification
function showCustomToast(message, type) {
  const $toast = jQuery('#wishlist-toast');
  const $message = $toast.find('.wishlist-toast-message');

  $message.text(message);
  $toast.attr('data-type', type); // 'success' or 'error'
  $toast.addClass('show');

  setTimeout(function() {
    $toast.removeClass('show');
  }, 3000);
}

// Usage
showCustomToast('Item added!', 'success');
```

### Listen for Wishlist Events

```javascript
// Custom event when item is added
jQuery(document).on('click', '.wishlist-button', function() {
  const productId = jQuery(this).data('product-id');

  // Your custom logic here
  console.log('Wishlist button clicked for product:', productId);
});

// Listen for successful add
jQuery(document.body).on('skyyrose_wishlist_added', function(event, productId, count) {
  console.log('Product ' + productId + ' added. Total items: ' + count);
});
```

### Update Counter from Custom Code

```javascript
// Manually update wishlist counter
function updateWishlistCounter(count) {
  const $counter = jQuery('.wishlist-count');

  $counter.text(count);

  if (count > 0) {
    $counter.addClass('has-items');
  } else {
    $counter.removeClass('has-items');
  }
}

// Usage
updateWishlistCounter(5);
```

---

## CSS Customization Snippets

### Change Heart Color

```css
/* Custom heart colors */
.wishlist-button .icon {
  stroke: #0073aa; /* Outline color */
}

.wishlist-button.in-wishlist .icon {
  fill: #d4af37; /* Filled color */
  stroke: #d4af37;
}

.wishlist-button:hover .icon {
  stroke: #005177; /* Hover color */
}
```

### Customize Toast Notification

```css
/* Custom toast styling */
.wishlist-toast {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.wishlist-toast-message {
  color: #fff;
  font-weight: 600;
}

.wishlist-toast[data-type="success"] {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.wishlist-toast[data-type="error"] {
  background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
}
```

### Change Grid Layout

```css
/* 4 columns on desktop, 2 on tablet, 1 on mobile */
.wishlist-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
}

@media (max-width: 1024px) {
  .wishlist-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .wishlist-grid {
    grid-template-columns: 1fr;
  }
}
```

### Custom Product Card Hover Effect

```css
/* Fancy hover effect */
.wishlist-item {
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.wishlist-item::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent,
    rgba(212, 175, 55, 0.1),
    transparent
  );
  transform: rotate(45deg);
  transition: all 0.6s;
  opacity: 0;
}

.wishlist-item:hover::before {
  opacity: 1;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
  100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}
```

### Sticky Header Integration

```css
/* Make header actions sticky */
.header-actions {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.site-header.scrolled .header-actions {
  padding: 5px 20px;
  transition: padding 0.3s ease;
}
```

---

## Shortcode Examples

### Create Wishlist Count Shortcode

```php
<?php
// functions.php
function skyyrose_wishlist_count_shortcode() {
  $count = skyyrose_get_wishlist_count();
  return '<span class="wishlist-count-shortcode">' . esc_html( $count ) . '</span>';
}
add_shortcode( 'wishlist_count', 'skyyrose_wishlist_count_shortcode' );

// Usage in page/post:
// [wishlist_count]
?>
```

### Create Wishlist Link Shortcode

```php
<?php
// functions.php
function skyyrose_wishlist_link_shortcode( $atts ) {
  $atts = shortcode_atts( array(
    'text' => 'View Wishlist',
    'class' => 'wishlist-link'
  ), $atts );

  $url = get_permalink( get_page_by_path( 'wishlist' ) );
  $count = skyyrose_get_wishlist_count();

  return sprintf(
    '<a href="%s" class="%s">%s (%d)</a>',
    esc_url( $url ),
    esc_attr( $atts['class'] ),
    esc_html( $atts['text'] ),
    $count
  );
}
add_shortcode( 'wishlist_link', 'skyyrose_wishlist_link_shortcode' );

// Usage:
// [wishlist_link text="My Favorites" class="custom-class"]
?>
```

### Create Mini Wishlist Shortcode

```php
<?php
// functions.php
function skyyrose_mini_wishlist_shortcode( $atts ) {
  $atts = shortcode_atts( array(
    'limit' => 3
  ), $atts );

  $wishlist = array_slice( skyyrose_get_wishlist_items(), 0, intval( $atts['limit'] ) );

  if ( empty( $wishlist ) ) {
    return '<p>No items in wishlist.</p>';
  }

  $output = '<div class="mini-wishlist">';

  foreach ( $wishlist as $product_id ) {
    $product = wc_get_product( $product_id );
    if ( ! $product ) continue;

    $output .= '<div class="mini-wishlist-item">';
    $output .= '<a href="' . esc_url( $product->get_permalink() ) . '">';
    $output .= $product->get_image( 'thumbnail' );
    $output .= '<span>' . esc_html( $product->get_name() ) . '</span>';
    $output .= '</a>';
    $output .= '</div>';
  }

  $output .= '</div>';

  return $output;
}
add_shortcode( 'mini_wishlist', 'skyyrose_mini_wishlist_shortcode' );

// Usage:
// [mini_wishlist limit="5"]
?>
```

---

## REST API Integration Examples

### Fetch Wishlist with Fetch API

```javascript
// Get wishlist using Fetch API
fetch('/wp-json/skyyrose/v1/wishlist')
  .then(response => response.json())
  .then(data => {
    console.log('Wishlist items:', data.items);
    console.log('Total count:', data.count);
  })
  .catch(error => console.error('Error:', error));
```

### Add to Wishlist with Axios

```javascript
// Using Axios
axios.post('/wp-json/skyyrose/v1/wishlist/add', {
  product_id: 123
})
.then(function (response) {
  if (response.data.success) {
    alert('Added to wishlist!');
    updateCounter(response.data.count);
  }
})
.catch(function (error) {
  console.error('Error:', error);
});
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function WishlistCounter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    fetch('/wp-json/skyyrose/v1/wishlist')
      .then(res => res.json())
      .then(data => setCount(data.count));
  }, []);

  return (
    <div className="wishlist-counter">
      <span className="icon">♥</span>
      <span className="count">{count}</span>
    </div>
  );
}

export default WishlistCounter;
```

---

## Advanced Customizations

### Email Notification on Wishlist Add

```php
<?php
// functions.php
add_action( 'skyyrose_added_to_wishlist', 'send_wishlist_notification' );

function send_wishlist_notification( $product_id ) {
  $product = wc_get_product( $product_id );
  $user = wp_get_current_user();

  $to = $user->user_email;
  $subject = 'You added ' . $product->get_name() . ' to your wishlist';

  $message = sprintf(
    "Hi %s,\n\nYou added %s to your wishlist.\n\nPrice: %s\nView: %s\n\nBest regards,\nYour Store",
    $user->display_name,
    $product->get_name(),
    $product->get_price_html(),
    $product->get_permalink()
  );

  wp_mail( $to, $subject, $message );
}
?>
```

### Wishlist Analytics Tracking

```javascript
// Google Analytics tracking
jQuery(document).on('click', '.wishlist-button', function() {
  const productId = jQuery(this).data('product-id');
  const action = jQuery(this).hasClass('in-wishlist') ? 'remove' : 'add';

  // Send to Google Analytics
  if (typeof gtag !== 'undefined') {
    gtag('event', 'wishlist_' + action, {
      'event_category': 'Wishlist',
      'event_label': 'Product ' + productId,
      'value': productId
    });
  }
});
```

### Custom Wishlist Sorting

```php
<?php
// Sort wishlist by price
function get_sorted_wishlist( $order = 'ASC' ) {
  $wishlist = skyyrose_get_wishlist_items();
  $products = array();

  foreach ( $wishlist as $product_id ) {
    $product = wc_get_product( $product_id );
    if ( $product ) {
      $products[] = array(
        'id' => $product_id,
        'price' => $product->get_price(),
        'product' => $product
      );
    }
  }

  usort( $products, function( $a, $b ) use ( $order ) {
    if ( $order === 'ASC' ) {
      return $a['price'] <=> $b['price'];
    }
    return $b['price'] <=> $a['price'];
  });

  return $products;
}

// Usage
$sorted = get_sorted_wishlist( 'DESC' ); // High to low
?>
```

---

## Debugging Snippets

### Debug Wishlist Data

```php
<?php
// Temporary debugging - add to functions.php
add_action( 'wp_footer', 'debug_wishlist_data' );

function debug_wishlist_data() {
  if ( ! current_user_can( 'manage_options' ) ) {
    return;
  }

  $key = skyyrose_get_wishlist_key();
  $wishlist = skyyrose_get_wishlist_items();
  $count = skyyrose_get_wishlist_count();

  echo '<div style="position:fixed;bottom:0;right:0;background:#fff;padding:20px;border:2px solid #000;z-index:99999;">';
  echo '<strong>Wishlist Debug:</strong><br>';
  echo 'Key: ' . esc_html( $key ) . '<br>';
  echo 'Count: ' . esc_html( $count ) . '<br>';
  echo 'Items: ' . esc_html( implode( ', ', $wishlist ) );
  echo '</div>';
}
?>
```

### JavaScript Console Debugging

```javascript
// Add to browser console to debug
console.log('Wishlist Data:', skyyRoseWishlist);
console.log('Current Count:', jQuery('.wishlist-count').text());
console.log('In Wishlist Buttons:', jQuery('.wishlist-button.in-wishlist').length);

// Test AJAX endpoint
jQuery.post(skyyRoseWishlist.ajaxUrl, {
  action: 'skyyrose_get_wishlist_count',
  nonce: skyyRoseWishlist.nonce
}, function(response) {
  console.log('Server Count:', response);
});
```

---

## Tips & Best Practices

1. **Always sanitize input**: Use `absint()`, `sanitize_text_field()`, etc.
2. **Verify nonces**: Check AJAX nonces in all handlers
3. **Check permissions**: Verify user capabilities when needed
4. **Handle errors**: Add error handling to AJAX calls
5. **Cache wisely**: Consider caching wishlist counts
6. **Mobile first**: Test on mobile devices
7. **Accessibility**: Add ARIA labels to custom elements
8. **Performance**: Minimize database queries
9. **Security**: Validate all user input
10. **Documentation**: Comment your custom code

---

**Last Updated**: February 8, 2026
