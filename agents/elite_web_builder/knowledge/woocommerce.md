# WooCommerce Knowledge Base

## Product Types

### Simple Product
Single item, one price, one SKU. Most common type.

### Variable Product
Multiple variations (size, color). Each variant has own SKU, price, stock.
- Attributes: defined on product, used for variations
- Variations: specific attribute combinations with pricing

### Grouped Product
Collection of simple products displayed together. No cart button on group.

### External/Affiliate Product
Links to external URL. Buy button redirects to third-party site.

## Payment Gateways

### WooPayments (Stripe-powered)
- Built-in Stripe integration by WooCommerce
- No redirect: payment processed on-site
- Supports Apple Pay, Google Pay
- PCI compliant (SAQ A)

### Stripe Direct
- Test mode: use `sk_test_...` / `pk_test_...` keys
- Live mode: use `sk_live_...` / `pk_live_...` keys
- Webhook setup: `https://site.com/?wc-api=wc_stripe`
- Events: `payment_intent.succeeded`, `charge.refunded`

### PayPal
- Standard: redirect to PayPal
- Express Checkout: inline buttons
- IPN URL: `https://site.com/?wc-api=WC_Gateway_Paypal`

## Shipping Zones

### Configuration
1. **Domestic** (US): Flat rate, Free shipping over threshold
2. **International**: Flat rate per region, or calculated rates
3. **Local pickup**: Free, specify store address

### Free Shipping
- Coupon-based or minimum order amount
- Common: "Free shipping on orders over $100"
- Set via: WooCommerce → Settings → Shipping → Zone → Free Shipping

### Calculated Rates
- USPS, UPS, FedEx plugins for real-time rates
- Requires: package dimensions, weight, origin address

## Tax Configuration

### WooCommerce Tax
- Automated tax calculation by WooCommerce
- US sales tax by state/ZIP
- International VAT support

### Stripe Tax
- Alternative automated tax via Stripe
- Works with WooPayments
- Handles EU VAT, US sales tax, Canadian GST/HST

### Manual Tax Rates
- WooCommerce → Settings → Tax → Standard Rates
- Fields: Country, State, ZIP, Rate %, Tax Name, Priority
- Tax-inclusive pricing: Settings → Tax → "Yes, I will enter prices inclusive of tax"

## Cart & Checkout

### Block-Based Checkout (New)
- Uses WooCommerce Checkout block
- Extensible via `woocommerce/checkout` block
- Better performance, built-in validation

### Classic Shortcode Checkout (Legacy)
- Uses `[woocommerce_checkout]` shortcode
- Customizable via action hooks
- Being phased out

### Required Pages
- **Shop**: `woocommerce_shop_page_id`
- **Cart**: `woocommerce_cart_page_id`
- **Checkout**: `woocommerce_checkout_page_id`
- **My Account**: `woocommerce_myaccount_page_id`

## HPOS (High-Performance Order Storage)

### Overview
- New orders table: `wp_wc_orders` (NOT `wp_posts`)
- Separate from posts table for performance
- Migration path from legacy `wp_posts` storage

### Compatibility
- Check: `use_hpos_tables()` for conditional logic
- Declare compatibility: `\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility('custom_order_tables', __FILE__)`

## Key Hooks

### Cart Hooks
- `woocommerce_before_cart` — Before cart table
- `woocommerce_after_cart` — After cart table
- `woocommerce_cart_calculate_fees` — Add custom fees
- `woocommerce_before_calculate_totals` — Modify prices

### Checkout Hooks
- `woocommerce_checkout_process` — Validate checkout fields
- `woocommerce_checkout_order_processed` — After order created
- `woocommerce_payment_complete` — After successful payment
- `woocommerce_thankyou` — Thank you page display

### Product Hooks
- `woocommerce_before_single_product` — Before product page
- `woocommerce_after_single_product` — After product page
- `woocommerce_single_product_summary` — Product summary area
- `woocommerce_before_add_to_cart_form` — Before add to cart

## REST API

### Authentication
- Consumer Key + Consumer Secret (HTTP Basic Auth)
- Generate at: WooCommerce → Settings → Advanced → REST API

### Endpoints
- `GET /wc/v3/products` — List products
- `POST /wc/v3/products` — Create product
- `PUT /wc/v3/products/{id}` — Update product
- `GET /wc/v3/orders` — List orders
- `GET /wc/v3/customers` — List customers
- `GET /wc/v3/reports/sales` — Sales reports

## Common Mistakes
- Not setting store pages (Shop, Cart, Checkout, My Account)
- Wrong permalink structure (must be `/%postname%/` for pretty URLs)
- Missing shipping zones (no shipping = can't checkout physical products)
- Tax not enabled (customers confused by missing tax line)
- Not declaring HPOS compatibility in custom plugins
- Using `wp_posts` directly for orders (use WC_Order API)
- Not clearing WooCommerce transient cache after product changes
