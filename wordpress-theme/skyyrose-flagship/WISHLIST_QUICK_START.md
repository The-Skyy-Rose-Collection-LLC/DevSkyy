# Wishlist Quick Start Guide

## Setup (5 minutes)

### Step 1: Create Wishlist Page
1. WordPress Admin → Pages → Add New
2. Title: "Wishlist"
3. Template: Select "Wishlist" from dropdown
4. Publish

### Step 2: Add Widget (Optional)
1. Appearance → Widgets
2. Drag "SkyyRose Wishlist" to sidebar
3. Configure and Save

### Step 3: Verify
1. Visit any product page
2. Look for heart icon
3. Click to add to wishlist
4. Check counter in header

## User Experience Flow

```
CUSTOMER JOURNEY:
─────────────────

1. Browse Products
   └─ See heart icon on product cards
      └─ Click heart → Item added (animation + toast)

2. View Wishlist
   └─ Click heart icon in header
      └─ See all wishlist items in grid layout

3. Take Action
   ├─ Remove individual items (X button)
   ├─ Move single item to cart
   ├─ Move all items to cart (bulk)
   ├─ Clear wishlist (bulk)
   └─ Share wishlist (native share or copy link)

4. Empty State
   └─ If no items, see CTA to start shopping
```

## Key Locations

### Files You Might Need to Customize:

```
Theme Root
├── page-wishlist.php          ← Wishlist page template
├── header.php                 ← Header with wishlist icon
│
├── assets/
│   ├── css/
│   │   └── wishlist.css       ← All wishlist styles
│   └── js/
│       └── wishlist.js        ← All wishlist functionality
│
└── inc/
    ├── wishlist-functions.php ← Backend logic
    └── class-wishlist-widget.php ← Widget
```

## Common Customizations

### Change Heart Icon Color
**File**: `assets/css/wishlist.css`
```css
.wishlist-button.in-wishlist .icon {
  fill: #ff4444;  /* Change this color */
  stroke: #ff4444; /* Change this color */
}
```

### Change Grid Columns
**File**: `assets/css/wishlist.css`
```css
.wishlist-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  /* Change 280px to adjust column width */
}
```

### Change Toast Duration
**File**: `assets/js/wishlist.js`
```javascript
setTimeout(function() {
  $toast.removeClass('show');
}, 3000); // Change 3000 to milliseconds you want
```

## Available PHP Functions

```php
// Add product to wishlist
skyyrose_add_to_wishlist( 123 );

// Remove product
skyyrose_remove_from_wishlist( 123 );

// Check if product is in wishlist
if ( skyyrose_is_in_wishlist( 123 ) ) {
  echo 'In wishlist!';
}

// Get all wishlist items
$items = skyyrose_get_wishlist_items();

// Get item count
$count = skyyrose_get_wishlist_count();

// Move to cart
skyyrose_move_to_cart( 123 );

// Clear all
skyyrose_clear_wishlist();

// Display wishlist button
get_template_part( 'template-parts/wishlist-button' );
```

## REST API Quick Reference

```bash
# Get wishlist
curl https://yoursite.com/wp-json/skyyrose/v1/wishlist

# Add to wishlist
curl -X POST https://yoursite.com/wp-json/skyyrose/v1/wishlist/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123}'

# Remove from wishlist
curl -X POST https://yoursite.com/wp-json/skyyrose/v1/wishlist/remove \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123}'

# Clear wishlist
curl -X POST https://yoursite.com/wp-json/skyyrose/v1/wishlist/clear
```

## Troubleshooting

### Counter Not Showing
1. Check if WooCommerce is active
2. Verify wishlist page exists
3. Clear cache
4. Hard refresh browser (Ctrl+F5)

### Heart Icon Not Working
1. Open browser console (F12)
2. Look for JavaScript errors
3. Verify `wishlist.js` is loaded
4. Check AJAX URL in network tab

### Styles Not Applied
1. Verify `wishlist.css` is enqueued
2. Clear theme cache
3. Check CSS specificity conflicts
4. Inspect element with DevTools

### Session Not Persisting
1. Enable WooCommerce sessions
2. Check PHP sessions are working
3. Verify cookies are enabled
4. Test in incognito mode

## Testing Checklist

Quick test to verify everything works:

- [ ] Heart icon appears on product cards
- [ ] Heart icon appears on single product page
- [ ] Clicking heart adds item (shows toast)
- [ ] Header counter updates
- [ ] Clicking header icon goes to wishlist page
- [ ] Product cards display correctly on wishlist page
- [ ] Remove button works
- [ ] Move to cart button works
- [ ] Bulk actions work
- [ ] Share button works
- [ ] Empty state shows when no items
- [ ] Widget displays items (if added)

## Support Resources

- **Full Documentation**: See `WISHLIST_IMPLEMENTATION.md`
- **Theme Functions**: See `inc/wishlist-functions.php`
- **Styles**: See `assets/css/wishlist.css`
- **JavaScript**: See `assets/js/wishlist.js`

## Need Help?

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| Items disappear after refresh | Enable WooCommerce sessions |
| Counter always shows 0 | Check if products are actually added |
| Share doesn't work | Try copying link manually |
| Styling broken | Check for CSS conflicts |
| AJAX errors | Verify nonce is valid |

---

**Last Updated**: February 8, 2026
**Theme Version**: 1.0.0
