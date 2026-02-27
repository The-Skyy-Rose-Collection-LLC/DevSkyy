<?php
/**
 * Template Name: Pre-Order Gateway
 *
 * Ultra-dark luxury gateway with loading screen, SR monogram breathe animation,
 * collection tabs, product grid, product modal, cart sidebar, and sign-in panel.
 * Designed to match the drakerelated.com interaction pattern.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Product catalog data for the pre-order gateway.
 *
 * Sourced from the centralized catalog (inc/product-catalog.php).
 * Only includes products with active pre-orders.
 */
$collection_labels = array(
	'black-rose' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
	'love-hurts' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
	'signature'  => esc_html__( 'Signature', 'skyyrose-flagship' ),
);

$gateway_products = array();
$preorder_groups  = skyyrose_get_preorder_products();

foreach ( $preorder_groups as $collection_slug => $products ) {
	foreach ( $products as $p ) {
		$gateway_products[] = array(
			'id'               => $p['sku'],
			'name'             => $p['name'],
			'price'            => ( function_exists( 'get_woocommerce_currency_symbol' ) ? html_entity_decode( get_woocommerce_currency_symbol(), ENT_QUOTES, 'UTF-8' ) : '$' ) . number_format( $p['price'], 0 ),
			'collection'       => $p['collection'],
			'collection_label' => isset( $collection_labels[ $p['collection'] ] )
				? $collection_labels[ $p['collection'] ]
				: esc_html( ucwords( str_replace( '-', ' ', $p['collection'] ) ) ),
			'sizes'            => str_replace( '|', ',', $p['sizes'] ),
			'desc'             => $p['description'],
			'image'            => skyyrose_product_image_uri( ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'] ),
			'edition'          => (string) $p['edition_size'],
		);
	}
}

get_header();
?>

<main id="primary" class="site-main" role="main" tabindex="-1">

	<!-- Loading Screen -->
	<div class="preorder-loading" aria-hidden="true">
		<div class="loading-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
		<div class="loading-progress-track">
			<div class="loading-progress-bar"></div>
		</div>
		<div class="loading-text"><?php echo esc_html__( 'Curating Your Experience', 'skyyrose-flagship' ); ?></div>
	</div>

	<div class="preorder-gateway-page">

		<!-- Exclusive Member Banner -->
		<div class="member-banner">
			<span class="member-banner-text">
				<?php echo wp_kses(
					__( '<strong>Exclusive:</strong> Members get early access and 25% off pre-orders', 'skyyrose-flagship' ),
					array( 'strong' => array() )
				); ?>
			</span>
			<button type="button" class="member-banner-cta" data-action="open-signin">
				<?php echo esc_html__( 'Sign In for Access', 'skyyrose-flagship' ); ?>
			</button>
		</div>

		<!-- Countdown Timer -->
		<div class="preorder-countdown" aria-label="<?php esc_attr_e( 'Pre-order countdown', 'skyyrose-flagship' ); ?>">
			<span class="countdown-label"><?php echo esc_html__( 'Pre-Order Window Closes In', 'skyyrose-flagship' ); ?></span>
			<div class="countdown-timer" data-launch-date="<?php echo esc_attr( get_option( 'skyyrose_preorder_deadline', '2026-04-01T00:00:00' ) ); ?>">
				<div class="countdown-unit">
					<span class="countdown-value" data-unit="days">00</span>
					<span class="countdown-unit-label"><?php echo esc_html__( 'Days', 'skyyrose-flagship' ); ?></span>
				</div>
				<span class="countdown-separator">:</span>
				<div class="countdown-unit">
					<span class="countdown-value" data-unit="hours">00</span>
					<span class="countdown-unit-label"><?php echo esc_html__( 'Hours', 'skyyrose-flagship' ); ?></span>
				</div>
				<span class="countdown-separator">:</span>
				<div class="countdown-unit">
					<span class="countdown-value" data-unit="minutes">00</span>
					<span class="countdown-unit-label"><?php echo esc_html__( 'Min', 'skyyrose-flagship' ); ?></span>
				</div>
				<span class="countdown-separator">:</span>
				<div class="countdown-unit">
					<span class="countdown-value" data-unit="seconds">00</span>
					<span class="countdown-unit-label"><?php echo esc_html__( 'Sec', 'skyyrose-flagship' ); ?></span>
				</div>
			</div>
			<span class="countdown-pieces"><?php echo esc_html__( 'Limited numbered pieces — each item individually numbered', 'skyyrose-flagship' ); ?></span>
		</div>

		<!-- Conversion Intelligence: Viewers + Progress -->
		<div style="display:flex; justify-content:center; padding:0.5rem 0;">
			<div data-cie-viewers="42"></div>
		</div>
		<div data-cie-preorder-progress style="max-width:480px; margin:0 auto; padding:0 2rem 1rem;"></div>

		<!-- Gateway Header -->
		<div class="gateway-header" role="region" aria-label="<?php esc_attr_e( 'Pre-Order Controls', 'skyyrose-flagship' ); ?>">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="gateway-logo">
				<?php echo esc_html__( 'SKyyRose', 'skyyrose-flagship' ); ?>
			</a>
			<div class="gateway-actions">
				<button class="gateway-action-btn" type="button" data-action="open-signin" aria-label="<?php esc_attr_e( 'Sign in', 'skyyrose-flagship' ); ?>">
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
				</button>
				<button class="gateway-action-btn" type="button" data-action="open-cart" aria-label="<?php esc_attr_e( 'Open cart', 'skyyrose-flagship' ); ?>">
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
					<span class="cart-count-badge">0</span>
				</button>
			</div>
		</div><!-- .gateway-header -->

		<!-- Product Section -->
		<section class="gateway-product-section" aria-labelledby="gateway-section-title">
			<div class="gateway-section-header">
				<h2 id="gateway-section-title"><?php echo esc_html__( 'Pre-Order Collections', 'skyyrose-flagship' ); ?></h2>
				<p><?php echo esc_html__( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
			</div>

			<!-- Status region for filter announcements (screen readers only) -->
			<div class="product-grid-status screen-reader-text" role="status" aria-live="polite" aria-atomic="true"></div>
			<!-- Product Grid -->
			<div class="product-grid" id="product-grid-panel" aria-label="<?php esc_attr_e( 'Product grid', 'skyyrose-flagship' ); ?>">
				<?php foreach ( $gateway_products as $product ) :
					$badge_class = 'badge-' . $product['collection'];
				?>
					<article
						class="product-grid-card"
						data-collection="<?php echo esc_attr( $product['collection'] ); ?>"
						data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
						data-product-name="<?php echo esc_attr( $product['name'] ); ?>"
						data-product-price="<?php echo esc_attr( $product['price'] ); ?>"
						data-product-image="<?php echo esc_url( $product['image'] ); ?>"
						data-product-collection-label="<?php echo esc_attr( $product['collection_label'] ); ?>"
						data-product-desc="<?php echo esc_attr( $product['desc'] ); ?>"
						data-product-sizes="<?php echo esc_attr( $product['sizes'] ); ?>"
					>
						<div class="product-grid-image">
							<img
								src="<?php echo esc_url( $product['image'] ); ?>"
								alt="<?php echo esc_attr( $product['name'] ); ?>"
								loading="lazy"
								data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>"
							>
							<span class="product-grid-badge <?php echo esc_attr( $badge_class ); ?>">
								<?php echo esc_html( $product['collection_label'] ); ?>
							</span>
							<button
								class="product-grid-wishlist"
								type="button"
								data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
								aria-label="<?php echo esc_attr( sprintf( __( 'Add %s to wishlist', 'skyyrose-flagship' ), $product['name'] ) ); ?>"
							>
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
							</button>
						</div>
						<div class="product-grid-details">
							<h3 class="product-grid-name"><?php echo esc_html( $product['name'] ); ?></h3>
							<p class="product-grid-price"><?php echo esc_html( $product['price'] ); ?></p>
							<p class="product-grid-collection-label" data-label="<?php echo esc_attr( $product['collection'] ); ?>">
								<?php echo esc_html( $product['collection_label'] ); ?>
							</p>
							<?php if ( ! empty( $product['edition'] ) ) : ?>
								<p class="product-grid-edition">
									<?php
									/* translators: %s: number of limited pieces */
									echo esc_html( sprintf( __( 'Limited to %s pieces', 'skyyrose-flagship' ), $product['edition'] ) );
									?>
								</p>
							<?php endif; ?>
						</div>
						<button class="product-grid-view-btn" type="button" aria-haspopup="dialog" aria-label="<?php echo esc_attr( sprintf( __( 'View %s details', 'skyyrose-flagship' ), $product['name'] ) ); ?>">
							<?php esc_html_e( 'View Details', 'skyyrose-flagship' ); ?>
						</button>
					</article>
				<?php endforeach; ?>
			</div>
		</section>

	</div><!-- .preorder-gateway-page -->

	<!-- Product Modal -->
	<div class="product-modal-overlay" aria-hidden="true"></div>
	<div class="product-modal" id="product-modal-dialog" role="dialog" aria-modal="true" aria-hidden="true" inert aria-labelledby="modal-product-name">
		<button class="product-modal-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="modal-360-area">
			<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>" alt="<?php esc_attr_e( 'Product preview', 'skyyrose-flagship' ); ?>" width="400" height="400">
			<span class="modal-360-badge"><?php echo esc_html__( '360 Preview', 'skyyrose-flagship' ); ?></span>
		</div>
		<div class="modal-details">
			<h2 class="modal-product-name" id="modal-product-name"><?php esc_html_e( 'Product Details', 'skyyrose-flagship' ); ?></h2>
			<p class="modal-product-collection"></p>
			<p class="modal-product-price"></p>
			<p class="modal-product-desc"></p>
			<p class="modal-sizes-label" id="modal-sizes-label"><?php echo esc_html__( 'Select Size', 'skyyrose-flagship' ); ?></p>
			<div class="modal-sizes" role="group" aria-labelledby="modal-sizes-label"></div>
			<div class="modal-actions">
				<button class="modal-add-to-cart" type="button"><?php echo esc_html__( 'Add to Cart', 'skyyrose-flagship' ); ?></button>
				<button class="modal-wishlist-btn" type="button" aria-label="<?php esc_attr_e( 'Add to wishlist', 'skyyrose-flagship' ); ?>">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
				</button>
			</div>
		</div>
	</div>

	<!-- Cart Sidebar -->
	<div class="cart-sidebar-overlay" aria-hidden="true"></div>
	<div class="cart-sidebar" id="cart-sidebar-dialog" role="dialog" aria-modal="true" aria-hidden="true" inert aria-labelledby="cart-sidebar-title">
		<div class="cart-sidebar-header">
			<h3 class="cart-sidebar-title" id="cart-sidebar-title"><?php echo esc_html__( 'Your Cart', 'skyyrose-flagship' ); ?></h3>
			<button class="cart-sidebar-close" type="button" aria-label="<?php esc_attr_e( 'Close cart', 'skyyrose-flagship' ); ?>">&times;</button>
		</div>
		<div class="cart-items-list">
			<div class="cart-empty-msg">
				<p><?php echo esc_html__( 'Your cart is empty', 'skyyrose-flagship' ); ?></p>
				<p><?php echo esc_html__( 'Browse our collections and add your favorites.', 'skyyrose-flagship' ); ?></p>
			</div>
		</div>
		<div class="cart-sidebar-footer">
			<div class="cart-total-row">
				<span class="cart-total-label"><?php echo esc_html__( 'Total', 'skyyrose-flagship' ); ?></span>
				<span class="cart-total-amount">$0.00</span>
			</div>
			<button class="cart-checkout-btn" type="button"><?php echo esc_html__( 'Proceed to Checkout', 'skyyrose-flagship' ); ?></button>
		</div>
	</div>

	<!-- Sign-In Panel -->
	<div class="signin-overlay" aria-hidden="true"></div>
	<div class="signin-panel" id="signin-panel-dialog" role="dialog" aria-modal="true" aria-hidden="true" inert aria-label="<?php esc_attr_e( 'Sign in', 'skyyrose-flagship' ); ?>">
		<div class="signin-header">
			<h3 class="signin-title"><?php echo esc_html__( 'Welcome Back', 'skyyrose-flagship' ); ?></h3>
			<button class="signin-close" type="button" aria-label="<?php esc_attr_e( 'Close sign-in', 'skyyrose-flagship' ); ?>">&times;</button>
		</div>
		<div class="signin-body">
			<form class="signin-form" method="post" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>">
				<input type="hidden" name="action" value="skyyrose_signin">
				<?php wp_nonce_field( 'skyyrose_signin', 'skyyrose_signin_nonce' ); ?>

				<div class="signin-form-group">
					<label class="signin-label" for="signin-email"><?php echo esc_html__( 'Email', 'skyyrose-flagship' ); ?></label>
					<input
						id="signin-email"
						class="signin-input"
						type="email"
						name="email"
						placeholder="<?php esc_attr_e( 'you@example.com', 'skyyrose-flagship' ); ?>"
						required
						autocomplete="email"
					>
				</div>

				<div class="signin-form-group">
					<label class="signin-label" for="signin-password"><?php echo esc_html__( 'Password', 'skyyrose-flagship' ); ?></label>
					<input
						id="signin-password"
						class="signin-input"
						type="password"
						name="password"
						placeholder="<?php esc_attr_e( 'Your password', 'skyyrose-flagship' ); ?>"
						required
						autocomplete="current-password"
					>
				</div>

				<button class="signin-submit" type="submit"><?php echo esc_html__( 'Sign In', 'skyyrose-flagship' ); ?></button>
			</form>

			<div class="signin-divider"><?php echo esc_html__( 'or', 'skyyrose-flagship' ); ?></div>

			<div class="member-perks">
				<h4 class="member-perks-title"><?php echo esc_html__( 'Member Perks', 'skyyrose-flagship' ); ?></h4>
				<ul class="member-perks-list">
					<li><?php echo esc_html__( '48-hour early access to all launches', 'skyyrose-flagship' ); ?></li>
					<li><?php echo esc_html__( 'Up to 25% off pre-order pricing', 'skyyrose-flagship' ); ?></li>
					<li><?php echo esc_html__( 'Exclusive behind-the-scenes content', 'skyyrose-flagship' ); ?></li>
					<li><?php echo esc_html__( 'Priority customer service', 'skyyrose-flagship' ); ?></li>
					<li><?php echo esc_html__( 'Wishlist sync across devices', 'skyyrose-flagship' ); ?></li>
					<li><?php echo esc_html__( 'Invitation to private events', 'skyyrose-flagship' ); ?></li>
				</ul>
			</div>
		</div>
	</div>

	<!-- Collection Tabs (Fixed Bottom) -->
	<div class="collection-tabs" role="tablist" aria-label="<?php esc_attr_e( 'Filter by collection', 'skyyrose-flagship' ); ?>">
		<button class="collection-tab active" type="button" role="tab" aria-selected="true" tabindex="0" data-collection="all" id="tab-all">
			<?php echo esc_html__( 'All', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" role="tab" aria-selected="false" tabindex="-1" data-collection="black-rose" id="tab-black-rose">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" role="tab" aria-selected="false" tabindex="-1" data-collection="love-hurts" id="tab-love-hurts">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" role="tab" aria-selected="false" tabindex="-1" data-collection="signature" id="tab-signature">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</button>
	</div>

	<!-- Exclusive Incentive Popup — triggers after 15s or on exit intent -->
	<div class="incentive-popup-overlay" aria-hidden="true"></div>
	<div class="incentive-popup" id="incentive-popup-dialog" role="dialog" aria-modal="true" aria-hidden="true" inert aria-label="<?php esc_attr_e( 'Exclusive early access offer', 'skyyrose-flagship' ); ?>">
			<button class="incentive-popup-close" type="button" aria-label="<?php esc_attr_e( 'Close early access offer', 'skyyrose-flagship' ); ?>">&times;</button>
			<div class="incentive-popup-content">
				<div class="incentive-popup-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
				<h3 class="incentive-popup-title"><?php echo esc_html__( 'Unlock Early Access', 'skyyrose-flagship' ); ?></h3>
				<p class="incentive-popup-subtitle"><?php echo esc_html__( 'Get 25% off your first pre-order + 48hr early access to every collection drop.', 'skyyrose-flagship' ); ?></p>
				<form class="incentive-popup-form" method="post" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>">
					<input type="hidden" name="action" value="skyyrose_incentive_signup">
					<?php wp_nonce_field( 'skyyrose_incentive', 'skyyrose_incentive_nonce' ); ?>
					<label for="incentive-email" class="screen-reader-text"><?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?></label>
					<input
						id="incentive-email"
						class="incentive-popup-input"
						type="email"
						name="email"
						placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose-flagship' ); ?>"
						required
						autocomplete="email"
					>
					<label for="incentive-phone" class="screen-reader-text"><?php esc_html_e( 'Phone number (optional)', 'skyyrose-flagship' ); ?></label>
					<input
						id="incentive-phone"
						class="incentive-popup-input"
						type="tel"
						name="phone"
						placeholder="<?php esc_attr_e( 'Phone for SMS alerts (optional)', 'skyyrose-flagship' ); ?>"
						autocomplete="tel"
					>
					<button class="incentive-popup-submit" type="submit"><?php echo esc_html__( 'Get Early Access', 'skyyrose-flagship' ); ?></button>
				</form>
				<p class="incentive-popup-fine"><?php echo esc_html__( 'No spam. Unsubscribe anytime. Numbered pieces sell out fast.', 'skyyrose-flagship' ); ?></p>
		</div>
	</div>

</main><!-- #primary -->

<?php
// skyyRoseGateway is localized in inc/enqueue.php during wp_enqueue_scripts (before wp_head).
// wp_localize_script() called after wp_head is a no-op — data is silently dropped.

get_template_part( 'template-parts/cinematic-toggle' );

get_footer();
