<?php
/**
 * Facebook SDK & Pixel Integration
 *
 * Loads the Facebook JavaScript SDK and Pixel for conversion tracking.
 * Fires standard events (PageView, ViewContent, AddToCart, InitiateCheckout)
 * and relays custom conversion events from the analytics beacon.
 *
 * @package SkyyRose
 * @since   3.10.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Facebook App & Pixel configuration.
 *
 * App ID is read from wp_options for easy admin updates.
 * SDK version is safe to keep as a constant.
 */
if ( ! defined( 'SKYYROSE_FB_APP_ID' ) ) {
	$fb_app_id = get_option( 'skyyrose_fb_app_id', '' );
	define( 'SKYYROSE_FB_APP_ID', $fb_app_id );
}
if ( ! defined( 'SKYYROSE_FB_SDK_VERSION' ) ) {
	define( 'SKYYROSE_FB_SDK_VERSION', 'v18.0' );
}

/**
 * Inject Facebook Pixel base code into <head> — gated behind cookie consent.
 *
 * The pixel loader is deferred until the visitor has accepted tracking cookies.
 * On first visit the script tag is inert; once `skyyrose:consent:accepted` fires
 * (or `localStorage` already contains the consent flag) the pixel initialises.
 *
 * GDPR / CCPA: no tracking request leaves the browser before consent.
 *
 * @since 3.10.0
 * @since 6.6.0 Added consent gate.
 */
function skyyrose_facebook_pixel_head() {
	if ( is_admin() || empty( SKYYROSE_FB_APP_ID ) ) {
		return;
	}
	?>
<!-- Facebook Pixel Code — consent-gated -->
<script>
(function(){
	var pixelId = <?php echo wp_json_encode( SKYYROSE_FB_APP_ID ); ?>;

	function loadPixel() {
		if (window.__skyyFbLoaded) return;
		window.__skyyFbLoaded = true;

		!function(f,b,e,v,n,t,s)
		{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
		n.callMethod.apply(n,arguments):n.queue.push(arguments)};
		if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
		n.queue=[];t=b.createElement(e);t.async=!0;
		t.src=v;s=b.getElementsByTagName(e)[0];
		s.parentNode.insertBefore(t,s)}(window, document,'script',
		'https://connect.facebook.net/en_US/fbevents.js');
		fbq('init', pixelId);
		fbq('track', 'PageView');
	}

	/* Returning visitor who already consented. */
	if (localStorage.getItem('skyyrose_cookie_consent') === 'accepted') {
		loadPixel();
		return;
	}

	/* First visit — wait for consent event from the cookie banner. */
	document.addEventListener('skyyrose:consent:accepted', loadPixel);
})();
</script>
<!-- End Facebook Pixel Code -->
	<?php
}
add_action( 'wp_head', 'skyyrose_facebook_pixel_head', 5 );

/**
 * Pass Facebook SDK config to JS — consent-gated.
 *
 * The SDK script itself is no longer enqueued eagerly. It is loaded
 * on-demand by the consent-gated pixel loader in skyyrose_facebook_pixel_head().
 * We only pass the config object so footer scripts can read appId/version
 * after the SDK initialises.
 *
 * @since 3.10.0
 * @since 6.6.0 Removed unconditional SDK enqueue for GDPR compliance.
 */
function skyyrose_enqueue_facebook_sdk() {
	if ( is_admin() || empty( SKYYROSE_FB_APP_ID ) ) {
		return;
	}

	// Inline the config — no external script loaded until consent.
	wp_register_script( 'skyyrose-fb-config', false, array(), SKYYROSE_VERSION, true );
	wp_enqueue_script( 'skyyrose-fb-config' );
	wp_localize_script(
		'skyyrose-fb-config',
		'skyyroseFB',
		array(
			'appId'    => SKYYROSE_FB_APP_ID,
			'version'  => SKYYROSE_FB_SDK_VERSION,
			'currency' => function_exists( 'get_woocommerce_currency' ) ? get_woocommerce_currency() : 'USD',
		)
	);
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
	if ( is_admin() || empty( SKYYROSE_FB_APP_ID ) ) {
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
					'content_name' => $product->get_name(),
					'content_ids'  => array( $product->get_sku() ?: (string) $product->get_id() ),
					'content_type' => 'product',
					'value'        => (float) $product->get_price(),
					'currency'     => get_woocommerce_currency(),
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
	/* All footer FB events are consent-gated — nothing fires until the pixel
		has been loaded by skyyrose_facebook_pixel_head()'s consent handler. */
	function hasConsent() {
		return window.__skyyFbLoaded && typeof fbq !== 'undefined';
	}

	// Initialize Facebook SDK (deferred until consent).
	if (typeof FB === 'undefined' && typeof skyyroseFB !== 'undefined') {
		window.fbAsyncInit = function() {
			if (!hasConsent()) return;
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
	if (hasConsent()) {
		fbq('track', <?php echo wp_json_encode( $fb_event_data['event'] ); ?>, <?php echo wp_json_encode( $fb_event_data['data'] ); ?>);
	}
	<?php endif; ?>

	// Conversion tracking — single delegated listener (consent-gated).
	var currency = (typeof skyyroseFB !== 'undefined' && skyyroseFB.currency) ? skyyroseFB.currency : 'USD';
	document.addEventListener('click', function(e) {
		if (!e.target.closest || !hasConsent()) return;

		var addCart = e.target.closest('.btn-add-to-cart, .single_add_to_cart_button, .add_to_cart_button');
		if (addCart) {
			var panel = document.querySelector('.product-panel');
			var nameEl = panel ? panel.querySelector('.product-panel-name') : document.querySelector('.product_title');
			var priceEl = panel ? panel.querySelector('.product-panel-price') : document.querySelector('.price .amount');
			fbq('track', 'AddToCart', {
				content_name: nameEl ? nameEl.textContent.trim() : '',
				value: priceEl ? parseFloat(priceEl.textContent.replace(/[^0-9.]/g, '')) || 0 : 0,
				currency: currency
			});
			return;
		}

		var preorder = e.target.closest('.btn-preorder, [data-preorder]');
		if (preorder) {
			fbq('track', 'Lead', {
				content_name: 'Pre-Order',
				content_category: 'SkyyRose Pre-Order'
			});
		}
	});
})();
</script>
	<?php
}
add_action( 'wp_footer', 'skyyrose_facebook_footer_scripts', 99 );
