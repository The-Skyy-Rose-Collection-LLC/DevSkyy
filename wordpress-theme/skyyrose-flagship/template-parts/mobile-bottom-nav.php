<?php
/**
 * Mobile Bottom Navigation Bar
 *
 * Fixed bottom nav for mobile devices with 5 items:
 * Home, Collections, Search, Cart, Account.
 *
 * Glass panel aesthetic matching SkyyRose dark opulence.
 * Renders on all pages — hidden above 768px via CSS.
 *
 * @package SkyyRose
 * @since   6.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Determine active state based on current page.
// Collection slugs are derived dynamically from the canonical catalog so that
// adding or removing a collection in skyyrose-catalog.csv automatically updates
// the active-state detection here — no template-list drift.
$mobile_nav_active = '';

if ( is_front_page() ) {
	$mobile_nav_active = 'home';
} elseif ( is_search() ) {
	$mobile_nav_active = 'search';
} elseif ( function_exists( 'is_cart' ) && is_cart() ) {
	$mobile_nav_active = 'cart';
} elseif ( function_exists( 'is_account_page' ) && is_account_page() ) {
	$mobile_nav_active = 'account';
} else {
	$mobile_nav_tpl   = get_page_template_slug();
	$collection_slugs = array();
	if ( function_exists( 'skyyrose_get_product_catalog' ) ) {
		$catalog = skyyrose_get_product_catalog();
		foreach ( $catalog as $product ) {
			if ( ! empty( $product['collection'] ) ) {
				$collection_slugs[ $product['collection'] ] = true;
			}
		}
	}
	$collection_templates = array();
	foreach ( array_keys( $collection_slugs ) as $slug ) {
		$collection_templates[] = 'template-collection-' . $slug . '.php';
	}
	if ( in_array( $mobile_nav_tpl, $collection_templates, true ) ) {
		$mobile_nav_active = 'collections';
	} elseif ( function_exists( 'is_shop' ) && ( is_shop() || is_product_category() || is_product_tag() ) ) {
		$mobile_nav_active = 'collections';
	}
}

// Cart count (WooCommerce-aware).
$mobile_nav_cart_count = 0;
if ( function_exists( 'WC' ) && WC()->cart ) {
	$mobile_nav_cart_count = WC()->cart->get_cart_contents_count();
}

// Build navigation URLs.
$mobile_nav_cart_url    = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );
$mobile_nav_account_url = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'myaccount' ) : home_url( '/my-account/' );

// Navigation items.
$mobile_nav_items = array(
	array(
		'id'    => 'home',
		'label' => __( 'Home', 'skyyrose' ),
		'url'   => home_url( '/' ),
		'icon'  => '<path d="M3 10.5L12 3l9 7.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10.5z"/><path d="M9 21V14h6v7"/>',
	),
	array(
		'id'    => 'collections',
		'label' => __( 'Collections', 'skyyrose' ),
		'url'   => home_url( '/collections/' ),
		'icon'  => '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
	),
	array(
		'id'    => 'search',
		'label' => __( 'Search', 'skyyrose' ),
		'url'   => home_url( '/?s=' ),
		'icon'  => '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>',
	),
	array(
		'id'    => 'cart',
		'label' => __( 'Cart', 'skyyrose' ),
		'url'   => $mobile_nav_cart_url,
		'icon'  => '<path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
	),
	array(
		'id'    => 'account',
		'label' => __( 'Account', 'skyyrose' ),
		'url'   => $mobile_nav_account_url,
		'icon'  => '<circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 0 0-16 0"/>',
	),
);

// SVG kses rules for inline icons.
$mobile_nav_svg_kses = array(
	'path'   => array(
		'd'    => true,
		'fill' => true,
	),
	'circle' => array(
		'cx'   => true,
		'cy'   => true,
		'r'    => true,
		'fill' => true,
	),
	'rect'   => array(
		'x'      => true,
		'y'      => true,
		'width'  => true,
		'height' => true,
		'rx'     => true,
		'fill'   => true,
	),
);
?>

<nav class="mobile-nav" aria-label="<?php esc_attr_e( 'Mobile navigation', 'skyyrose' ); ?>">
	<?php
	foreach ( $mobile_nav_items as $item ) :
		$is_active = ( $item['id'] === $mobile_nav_active );
		?>
		<a href="<?php echo esc_url( $item['url'] ); ?>"
			class="mobile-nav__item<?php echo $is_active ? ' mobile-nav__item--active' : ''; ?>"
			<?php echo $is_active ? 'aria-current="page"' : ''; ?>>
			<span class="mobile-nav__icon">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
					<?php echo wp_kses( $item['icon'], $mobile_nav_svg_kses ); ?>
				</svg>
				<?php if ( 'cart' === $item['id'] && $mobile_nav_cart_count > 0 ) : ?>
					<span class="mobile-nav__badge" aria-label="<?php echo esc_attr( sprintf( __( '%d items in cart', 'skyyrose' ), $mobile_nav_cart_count ) ); ?>">
						<?php echo esc_html( $mobile_nav_cart_count ); ?>
					</span>
				<?php endif; ?>
			</span>
			<span class="mobile-nav__label"><?php echo esc_html( $item['label'] ); ?></span>
		</a>
	<?php endforeach; ?>
</nav>
