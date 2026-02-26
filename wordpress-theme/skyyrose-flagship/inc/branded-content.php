<?php
/**
 * Branded Content
 *
 * Defines brand constants, collection descriptions, and branded messaging
 * for empty cart, 404, checkout, and collection-specific CTAs.
 * All copy uses the SkyyRose voice: "Luxury Grows from Concrete."
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Brand Constants
 *--------------------------------------------------------------*/

if ( ! defined( 'SKYYROSE_BRAND_TAGLINE' ) ) {
	define( 'SKYYROSE_BRAND_TAGLINE', 'Luxury Grows from Concrete.' );
}

if ( ! defined( 'SKYYROSE_BRAND_COLOR_PRIMARY' ) ) {
	define( 'SKYYROSE_BRAND_COLOR_PRIMARY', '#B76E79' );
}

if ( ! defined( 'SKYYROSE_BRAND_COLOR_DARK' ) ) {
	define( 'SKYYROSE_BRAND_COLOR_DARK', '#0A0A0A' );
}

if ( ! defined( 'SKYYROSE_BRAND_COLOR_GOLD' ) ) {
	define( 'SKYYROSE_BRAND_COLOR_GOLD', '#D4AF37' );
}

if ( ! defined( 'SKYYROSE_BRAND_COMPANY' ) ) {
	define( 'SKYYROSE_BRAND_COMPANY', 'SkyyRose LLC' );
}

/*--------------------------------------------------------------
 * Collection Descriptions
 *--------------------------------------------------------------*/

/**
 * Get the branded description for a given collection.
 *
 * Returns an immutable copy of the collection description.
 * Used for meta descriptions, OG tags, and on-page copy.
 *
 * @since  3.1.0
 *
 * @param  string $collection Collection slug.
 * @return string Branded description.
 */
function skyyrose_get_collection_description( $collection ) {

	$descriptions = array(
		'black-rose'   => __( 'Dark elegance meets luxury streetwear. The Black Rose collection channels cathedral-inspired grandeur into pieces that command attention. Designed for those who wear their confidence.', 'skyyrose-flagship' ),
		'love-hurts'   => __( 'Where passion meets pain. The Love Hurts collection draws from castle-forged resilience, crafting garments that tell the story of love in its rawest form. Feel everything. Wear it proudly.', 'skyyrose-flagship' ),
		'signature'    => __( 'The quintessential SkyyRose experience. Our Signature collection brings city-inspired luxury to every moment. Timeless pieces that define who you are.', 'skyyrose-flagship' ),
		'kids-capsule' => __( 'Luxury fashion for the next generation. The Kids Capsule brings the SkyyRose standard of quality and design to the little ones who deserve nothing less.', 'skyyrose-flagship' ),
	);

	$sanitized = sanitize_key( $collection );

	if ( isset( $descriptions[ $sanitized ] ) ) {
		return $descriptions[ $sanitized ];
	}

	return __( 'Luxury Grows from Concrete. Explore the SkyyRose collection.', 'skyyrose-flagship' );
}

/*--------------------------------------------------------------
 * Branded Empty Cart Message
 *--------------------------------------------------------------*/

/**
 * Replace the default WooCommerce empty cart message with branded copy.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_branded_empty_cart_message() {

	$shop_url = function_exists( 'wc_get_page_id' )
		? get_permalink( wc_get_page_id( 'shop' ) )
		: home_url( '/shop/' );

	?>
	<div class="skyyrose-empty-cart" style="text-align: center; padding: 4rem 2rem;">
		<h2 class="skyyrose-empty-cart__heading">
			<?php esc_html_e( 'Your Cart is Waiting', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="skyyrose-empty-cart__tagline" style="color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; font-style: italic; font-size: 1.125rem; margin-bottom: 1rem;">
			<?php echo esc_html( SKYYROSE_BRAND_TAGLINE ); ?>
		</p>
		<p class="skyyrose-empty-cart__body">
			<?php esc_html_e( 'Your journey with SkyyRose starts here. Explore our collections and find pieces that speak to your story.', 'skyyrose-flagship' ); ?>
		</p>
		<p class="skyyrose-empty-cart__cta">
			<a href="<?php echo esc_url( $shop_url ); ?>" class="button wc-forward" style="background-color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; color: #fff; border: none; padding: 0.75rem 2rem;">
				<?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?>
			</a>
		</p>
	</div>
	<?php
}

if ( class_exists( 'WooCommerce' ) ) {
	remove_action( 'woocommerce_cart_is_empty', 'wc_empty_cart_message', 10 );
	add_action( 'woocommerce_cart_is_empty', 'skyyrose_branded_empty_cart_message', 10 );
}

/*--------------------------------------------------------------
 * Branded 404 Content
 *--------------------------------------------------------------*/

/**
 * Output branded 404 page content.
 *
 * Provides a luxury-branded error page with navigation back to
 * collections. Called from 404.php template.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_branded_404_content() {
	?>
	<div class="skyyrose-404" style="text-align: center; padding: 4rem 2rem; max-width: 640px; margin: 0 auto;">
		<h1 class="skyyrose-404__heading" style="font-size: 4rem; color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; margin-bottom: 0.5rem;">
			404
		</h1>
		<h2 class="skyyrose-404__subheading">
			<?php esc_html_e( 'This Page Has Moved On', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="skyyrose-404__tagline" style="color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; font-style: italic; font-size: 1.125rem; margin-bottom: 1.5rem;">
			<?php echo esc_html( SKYYROSE_BRAND_TAGLINE ); ?>
		</p>
		<p class="skyyrose-404__body">
			<?php esc_html_e( 'The page you are looking for no longer exists or has been reimagined. Let us guide you back to the collection.', 'skyyrose-flagship' ); ?>
		</p>
		<nav class="skyyrose-404__nav" aria-label="<?php esc_attr_e( '404 Navigation', 'skyyrose-flagship' ); ?>" style="margin-top: 2rem;">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="button" style="margin: 0.5rem; background-color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; color: #fff; border: none; padding: 0.75rem 2rem; display: inline-block;">
				<?php esc_html_e( 'Return Home', 'skyyrose-flagship' ); ?>
			</a>
			<?php if ( function_exists( 'wc_get_page_id' ) ) : ?>
				<a href="<?php echo esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ); ?>" class="button" style="margin: 0.5rem; background-color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_DARK ); ?>; color: #fff; border: none; padding: 0.75rem 2rem; display: inline-block;">
					<?php esc_html_e( 'Shop Collections', 'skyyrose-flagship' ); ?>
				</a>
			<?php endif; ?>
		</nav>
	</div>
	<?php
}

/*--------------------------------------------------------------
 * Branded Checkout Messaging
 *--------------------------------------------------------------*/

/**
 * Add branded messaging above the checkout form.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_branded_checkout_header() {
	?>
	<div class="skyyrose-checkout-header" style="text-align: center; padding: 1.5rem 1rem 2rem; margin-bottom: 2rem; border-bottom: 1px solid #eee;">
		<p class="skyyrose-checkout-header__tagline" style="color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; font-style: italic; font-size: 1rem; margin: 0 0 0.5rem;">
			<?php echo esc_html( SKYYROSE_BRAND_TAGLINE ); ?>
		</p>
		<p class="skyyrose-checkout-header__message" style="font-size: 0.875rem; color: #666; margin: 0;">
			<?php esc_html_e( 'Secure checkout powered by SkyyRose. Your information is protected with industry-standard encryption.', 'skyyrose-flagship' ); ?>
		</p>
	</div>
	<?php
}

if ( class_exists( 'WooCommerce' ) ) {
	add_action( 'woocommerce_before_checkout_form', 'skyyrose_branded_checkout_header', 5 );
}

/**
 * Add branded thank-you messaging after checkout.
 *
 * @since 3.1.0
 *
 * @param int $order_id WooCommerce order ID.
 * @return void
 */
function skyyrose_branded_thankyou_message( $order_id ) {

	if ( ! $order_id ) {
		return;
	}

	?>
	<div class="skyyrose-thankyou" style="text-align: center; padding: 2rem 1rem; margin-bottom: 2rem;">
		<p class="skyyrose-thankyou__tagline" style="color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; font-style: italic; font-size: 1.125rem; margin-bottom: 0.5rem;">
			<?php echo esc_html( SKYYROSE_BRAND_TAGLINE ); ?>
		</p>
		<p class="skyyrose-thankyou__message">
			<?php esc_html_e( 'Thank you for choosing SkyyRose. Your order has been placed and is being prepared with care. Welcome to the family.', 'skyyrose-flagship' ); ?>
		</p>
	</div>
	<?php
}

if ( class_exists( 'WooCommerce' ) ) {
	add_action( 'woocommerce_thankyou', 'skyyrose_branded_thankyou_message', 5 );
}

/*--------------------------------------------------------------
 * Collection-Specific CTAs
 *--------------------------------------------------------------*/

/**
 * Get the branded CTA (call-to-action) for a given collection.
 *
 * Returns an associative array with 'text', 'url', and 'description' keys.
 * Used in collection pages and marketing sections.
 *
 * @since 3.1.0
 *
 * @param  string $collection Collection slug.
 * @return array  CTA data with 'text', 'url', and 'description' keys.
 */
function skyyrose_get_collection_cta( $collection ) {

	$shop_base = function_exists( 'wc_get_page_id' )
		? get_permalink( wc_get_page_id( 'shop' ) )
		: home_url( '/shop/' );

	$ctas = array(
		'black-rose'   => array(
			'text'        => __( 'Enter the Cathedral', 'skyyrose-flagship' ),
			'url'         => home_url( '/collection-black-rose/' ),
			'description' => __( 'Discover the Black Rose collection. Dark elegance awaits.', 'skyyrose-flagship' ),
		),
		'love-hurts'   => array(
			'text'        => __( 'Feel Everything', 'skyyrose-flagship' ),
			'url'         => home_url( '/collection-love-hurts/' ),
			'description' => __( 'Explore the Love Hurts collection. Where passion meets pain.', 'skyyrose-flagship' ),
		),
		'signature'    => array(
			'text'        => __( 'Define Your Style', 'skyyrose-flagship' ),
			'url'         => home_url( '/collection-signature/' ),
			'description' => __( 'Shop the Signature collection. Timeless luxury, redefined.', 'skyyrose-flagship' ),
		),
		'kids-capsule' => array(
			'text'        => __( 'Shop for Little Ones', 'skyyrose-flagship' ),
			'url'         => home_url( '/collection-kids-capsule/' ),
			'description' => __( 'Explore the Kids Capsule. Luxury for the next generation.', 'skyyrose-flagship' ),
		),
	);

	$sanitized = sanitize_key( $collection );

	if ( isset( $ctas[ $sanitized ] ) ) {
		return $ctas[ $sanitized ];
	}

	return array(
		'text'        => __( 'Explore Collections', 'skyyrose-flagship' ),
		'url'         => esc_url( $shop_base ),
		'description' => __( 'Discover the world of SkyyRose. Luxury Grows from Concrete.', 'skyyrose-flagship' ),
	);
}

/**
 * Render a branded collection CTA button.
 *
 * Outputs an accessible, styled anchor element for a given collection.
 *
 * @since 3.1.0
 *
 * @param string $collection Collection slug.
 * @param string $style      Optional. Button style variant: 'primary' or 'outline'. Default 'primary'.
 * @return void
 */
function skyyrose_render_collection_cta( $collection, $style = 'primary' ) {

	$cta = skyyrose_get_collection_cta( $collection );

	$bg_color   = 'primary' === $style ? SKYYROSE_BRAND_COLOR_PRIMARY : 'transparent';
	$text_color = 'primary' === $style ? '#fff' : SKYYROSE_BRAND_COLOR_PRIMARY;
	$border     = 'primary' === $style ? 'none' : '2px solid ' . SKYYROSE_BRAND_COLOR_PRIMARY;

	printf(
		'<a href="%1$s" class="skyyrose-cta skyyrose-cta--%2$s" aria-label="%3$s" style="display: inline-block; padding: 0.75rem 2rem; background-color: %4$s; color: %5$s; border: %6$s; text-decoration: none; font-weight: 600; transition: opacity 0.3s ease;">%7$s</a>',
		esc_url( $cta['url'] ),
		esc_attr( $style ),
		esc_attr( $cta['description'] ),
		esc_attr( $bg_color ),
		esc_attr( $text_color ),
		esc_attr( $border ),
		esc_html( $cta['text'] )
	);
}

/*--------------------------------------------------------------
 * Brand Footer Tagline
 *--------------------------------------------------------------*/

/**
 * Add the SkyyRose tagline to the site footer.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_footer_tagline() {
	?>
	<p class="skyyrose-footer-tagline" style="text-align: center; color: <?php echo esc_attr( SKYYROSE_BRAND_COLOR_PRIMARY ); ?>; font-style: italic; font-size: 0.875rem; padding: 1rem 0; margin: 0;">
		<?php echo esc_html( SKYYROSE_BRAND_TAGLINE ); ?>
		&mdash;
		<?php echo esc_html( SKYYROSE_BRAND_COMPANY ); ?>
	</p>
	<?php
}
add_action( 'wp_footer', 'skyyrose_footer_tagline', 5 );
