<?php
/**
 * Facebook SDK & Pixel Integration
 *
 * Loads the Facebook JavaScript SDK and Pixel for conversion tracking.
 * Fires standard events (PageView, ViewContent, AddToCart, InitiateCheckout)
 * and relays custom conversion events from the analytics beacon.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Facebook App & Pixel configuration.
 */
define( 'SKYYROSE_FB_APP_ID', '860288763161770' );
define( 'SKYYROSE_FB_SDK_VERSION', 'v18.0' );

/**
 * Inject Facebook Pixel base code into <head>.
 *
 * Uses wp_head at priority 5 (before most scripts) to ensure the pixel
 * fires as early as possible for accurate page-view tracking.
 */
function skyyrose_facebook_pixel_head() {
	if ( is_admin() ) {
		return;
	}
	?>
<!-- Facebook Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '<?php echo esc_js( SKYYROSE_FB_APP_ID ); ?>');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=<?php echo esc_attr( SKYYROSE_FB_APP_ID ); ?>&ev=PageView&noscript=1"
/></noscript>
<!-- End Facebook Pixel Code -->
	<?php
}
add_action( 'wp_head', 'skyyrose_facebook_pixel_head', 5 );

/**
 * Enqueue the Facebook SDK and initialize it.
 */
function skyyrose_enqueue_facebook_sdk() {
	if ( is_admin() ) {
		return;
	}

	wp_enqueue_script(
		'facebook-sdk',
		'https://connect.facebook.net/en_US/sdk.js',
		array(),
		null,
		true
	);

	wp_localize_script( 'facebook-sdk', 'skyyroseFB', array(
		'appId'   => SKYYROSE_FB_APP_ID,
		'version' => SKYYROSE_FB_SDK_VERSION,
	) );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_facebook_sdk' );

/**
 * Output the FB.init() call and standard event tracking in the footer.
 *
 * Fires WooCommerce-aware events:
 * - ViewContent on single product pages
 * - InitiateCheckout on checkout page
 * - AddToCart via delegated click listener
 */
function skyyrose_facebook_footer_scripts() {
	if ( is_admin() ) {
		return;
	}

	$fb_event_data = array();

	// ViewContent on single product pages.
	if ( function_exists( 'is_product' ) && is_product() ) {
		global $product;
		if ( $product ) {
			$fb_event_data = array(
				'event' => 'ViewContent',
				'data'  => array(
					'content_name'     => $product->get_name(),
					'content_ids'      => array( $product->get_sku() ?: (string) $product->get_id() ),
					'content_type'     => 'product',
					'value'            => (float) $product->get_price(),
					'currency'         => get_woocommerce_currency(),
				),
			);
		}
	}

	// InitiateCheckout on checkout page.
	if ( function_exists( 'is_checkout' ) && is_checkout() && ! is_order_received_page() ) {
		$fb_event_data = array(
			'event' => 'InitiateCheckout',
			'data'  => array(),
		);
	}
	?>
<script>
(function() {
	// Initialize Facebook SDK.
	if (typeof FB === 'undefined' && typeof skyyroseFB !== 'undefined') {
		window.fbAsyncInit = function() {
			FB.init({
				appId: skyyroseFB.appId,
				cookie: true,
				xfbml: true,
				version: skyyroseFB.version
			});
		};
	}

	// Fire page-specific standard events.
	<?php if ( ! empty( $fb_event_data ) ) : ?>
	if (typeof fbq !== 'undefined') {
		fbq('track', <?php echo wp_json_encode( $fb_event_data['event'] ); ?>, <?php echo wp_json_encode( $fb_event_data['data'] ); ?>);
	}
	<?php endif; ?>

	// AddToCart tracking via delegated click.
	document.addEventListener('click', function(e) {
		var btn = e.target.closest ? e.target.closest('.btn-add-to-cart, .single_add_to_cart_button, .add_to_cart_button') : null;
		if (!btn || typeof fbq === 'undefined') return;

		var panel = document.querySelector('.product-panel');
		var nameEl = panel ? panel.querySelector('.product-panel-name') : document.querySelector('.product_title');
		var priceEl = panel ? panel.querySelector('.product-panel-price') : document.querySelector('.price .amount');

		fbq('track', 'AddToCart', {
			content_name: nameEl ? nameEl.textContent.trim() : '',
			value: priceEl ? parseFloat(priceEl.textContent.replace(/[^0-9.]/g, '')) || 0 : 0,
			currency: 'USD'
		});
	});

	// Pre-order tracking (custom event).
	document.addEventListener('click', function(e) {
		var btn = e.target.closest ? e.target.closest('.btn-preorder, [data-preorder]') : null;
		if (!btn || typeof fbq === 'undefined') return;

		fbq('track', 'Lead', {
			content_name: 'Pre-Order',
			content_category: 'SkyyRose Pre-Order'
		});
	});
})();
</script>
	<?php
}
add_action( 'wp_footer', 'skyyrose_facebook_footer_scripts', 99 );
