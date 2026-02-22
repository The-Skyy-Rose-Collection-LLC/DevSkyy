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
 * Product catalog data organized by collection.
 * Will be replaced with WooCommerce product queries in production.
 */
$gateway_products = array(
	// Black Rose Collection
	array(
		'id'              => 'br-001',
		'name'            => esc_html__( 'Midnight Thorns Necklace', 'skyyrose-flagship' ),
		'price'           => '$1,899',
		'collection'      => 'black-rose',
		'collection_label' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'sizes'           => 'S,M,L',
		'desc'            => esc_html__( 'Sterling silver chain with hand-crafted thorn pendants and black onyx centerpiece. A statement of dark elegance.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-1.jpg',
	),
	array(
		'id'              => 'br-002',
		'name'            => esc_html__( 'Cathedral Ring', 'skyyrose-flagship' ),
		'price'           => '$1,299',
		'collection'      => 'black-rose',
		'collection_label' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'sizes'           => '5,6,7,8,9',
		'desc'            => esc_html__( 'Gothic-inspired silver ring with cathedral arch detailing and obsidian stone setting.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-2.jpg',
	),
	array(
		'id'              => 'br-003',
		'name'            => esc_html__( 'Iron Garden Bracelet', 'skyyrose-flagship' ),
		'price'           => '$999',
		'collection'      => 'black-rose',
		'collection_label' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'sizes'           => 'S,M,L',
		'desc'            => esc_html__( 'Wrought iron-inspired silver bracelet with intertwining vine motifs and thorned accents.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-3.jpg',
	),
	array(
		'id'              => 'br-004',
		'name'            => esc_html__( 'Dark Bloom Earrings', 'skyyrose-flagship' ),
		'price'           => '$799',
		'collection'      => 'black-rose',
		'collection_label' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'sizes'           => 'OS',
		'desc'            => esc_html__( 'Dramatic drop earrings featuring oxidized silver petals and midnight-black crystal accents.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-4.jpg',
	),
	array(
		'id'              => 'br-005',
		'name'            => esc_html__( 'Shadow Vine Pendant', 'skyyrose-flagship' ),
		'price'           => '$1,499',
		'collection'      => 'black-rose',
		'collection_label' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'sizes'           => '16in,18in,20in',
		'desc'            => esc_html__( 'A cascading vine pendant in sterling silver with black diamond-cut stones.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-5.jpg',
	),

	// Love Hurts Collection
	array(
		'id'              => 'lh-001',
		'name'            => esc_html__( 'Crimson Heart Necklace', 'skyyrose-flagship' ),
		'price'           => '$2,199',
		'collection'      => 'love-hurts',
		'collection_label' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'sizes'           => '16in,18in,20in',
		'desc'            => esc_html__( 'Rose gold heart pendant encrusted with rubies and surrounded by thorned vines.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-1.jpg',
	),
	array(
		'id'              => 'lh-002',
		'name'            => esc_html__( 'Bleeding Rose Ring', 'skyyrose-flagship' ),
		'price'           => '$1,599',
		'collection'      => 'love-hurts',
		'collection_label' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'sizes'           => '5,6,7,8,9',
		'desc'            => esc_html__( 'A sculpted rose in rose gold with crimson enamel drip detailing and ruby center.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-2.jpg',
	),
	array(
		'id'              => 'lh-003',
		'name'            => esc_html__( 'Thorned Embrace Bracelet', 'skyyrose-flagship' ),
		'price'           => '$1,099',
		'collection'      => 'love-hurts',
		'collection_label' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'sizes'           => 'S,M,L',
		'desc'            => esc_html__( 'Interlocking thorn cuff in rose gold with garnet cabochons at each junction point.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-3.jpg',
	),
	array(
		'id'              => 'lh-004',
		'name'            => esc_html__( 'Passion Drop Earrings', 'skyyrose-flagship' ),
		'price'           => '$899',
		'collection'      => 'love-hurts',
		'collection_label' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'sizes'           => 'OS',
		'desc'            => esc_html__( 'Teardrop earrings in rose gold with crimson crystal drops that catch the light like flame.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-4.jpg',
	),
	array(
		'id'              => 'lh-005',
		'name'            => esc_html__( 'Velvet Flame Pendant', 'skyyrose-flagship' ),
		'price'           => '$1,799',
		'collection'      => 'love-hurts',
		'collection_label' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'sizes'           => '16in,18in,20in',
		'desc'            => esc_html__( 'A flame-shaped pendant in polished rose gold with gradient ruby pave setting.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-5.jpg',
	),

	// Signature Collection
	array(
		'id'              => 'sg-001',
		'name'            => esc_html__( 'Rose Gold Statement Necklace', 'skyyrose-flagship' ),
		'price'           => '$2,499',
		'collection'      => 'signature',
		'collection_label' => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'sizes'           => '16in,18in,20in',
		'desc'            => esc_html__( 'Our flagship statement piece in 18k rose gold with diamond accents and signature clasp.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/signature-product-1.jpg',
	),
	array(
		'id'              => 'sg-002',
		'name'            => esc_html__( 'Bridge View Cuff', 'skyyrose-flagship' ),
		'price'           => '$1,899',
		'collection'      => 'signature',
		'collection_label' => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'sizes'           => 'S,M,L',
		'desc'            => esc_html__( 'Architectural cuff bracelet inspired by the Bay Bridge, in polished rose gold and gold vermeil.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/signature-product-2.jpg',
	),
	array(
		'id'              => 'sg-003',
		'name'            => esc_html__( 'Golden Hour Earrings', 'skyyrose-flagship' ),
		'price'           => '$1,299',
		'collection'      => 'signature',
		'collection_label' => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'sizes'           => 'OS',
		'desc'            => esc_html__( 'Gradient earrings that transition from rose gold to warm gold, capturing the magic of golden hour.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/signature-product-3.jpg',
	),
	array(
		'id'              => 'sg-004',
		'name'            => esc_html__( 'Skyline Ring', 'skyyrose-flagship' ),
		'price'           => '$1,699',
		'collection'      => 'signature',
		'collection_label' => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'sizes'           => '5,6,7,8,9',
		'desc'            => esc_html__( 'A skyline silhouette etched into a wide band of 18k rose gold with champagne diamond baguettes.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/signature-product-4.jpg',
	),
	array(
		'id'              => 'sg-011',
		'name'            => esc_html__( 'Rose Gold Signature Beanie', 'skyyrose-flagship' ),
		'price'           => '$149',
		'collection'      => 'signature',
		'collection_label' => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'sizes'           => 'S/M,L/XL',
		'desc'            => esc_html__( 'Premium cashmere-blend beanie with embroidered SR monogram in rose gold thread.', 'skyyrose-flagship' ),
		'image'           => get_template_directory_uri() . '/assets/images/scenes/signature-beanie-1.jpg',
	),
);

get_header();
?>

<main id="primary" class="site-main">

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
			<a href="#" class="member-banner-cta" data-action="open-signin">
				<?php echo esc_html__( 'Sign In for Access', 'skyyrose-flagship' ); ?>
			</a>
		</div>

		<!-- Gateway Header -->
		<header class="gateway-header">
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
		</header>

		<!-- Product Section -->
		<section class="gateway-product-section">
			<div class="gateway-section-header">
				<h2><?php echo esc_html__( 'Pre-Order Collections', 'skyyrose-flagship' ); ?></h2>
				<p><?php echo esc_html__( 'Where Love Meets Luxury', 'skyyrose-flagship' ); ?></p>
			</div>

			<!-- Product Grid -->
			<div class="product-grid">
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
						role="button"
						tabindex="0"
						aria-label="<?php echo esc_attr( $product['name'] . ' — ' . $product['price'] ); ?>"
					>
						<div class="product-grid-image">
							<img
								src="<?php echo esc_url( $product['image'] ); ?>"
								alt="<?php echo esc_attr( $product['name'] ); ?>"
								loading="lazy"
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
						</div>
					</article>
				<?php endforeach; ?>
			</div>
		</section>

	</div><!-- .preorder-gateway-page -->

	<!-- Product Modal -->
	<div class="product-modal-overlay" aria-hidden="true">
		<div class="product-modal" role="dialog" aria-label="<?php esc_attr_e( 'Product details', 'skyyrose-flagship' ); ?>">
			<button class="product-modal-close" type="button" aria-label="<?php esc_attr_e( 'Close', 'skyyrose-flagship' ); ?>">&times;</button>
			<div class="modal-360-area">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>" alt="">
				<span class="modal-360-badge"><?php echo esc_html__( '360 Preview', 'skyyrose-flagship' ); ?></span>
			</div>
			<div class="modal-details">
				<h2 class="modal-product-name"></h2>
				<p class="modal-product-collection"></p>
				<p class="modal-product-price"></p>
				<p class="modal-product-desc"></p>
				<p class="modal-sizes-label"><?php echo esc_html__( 'Select Size', 'skyyrose-flagship' ); ?></p>
				<div class="modal-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
				<div class="modal-actions">
					<button class="modal-add-to-cart" type="button"><?php echo esc_html__( 'Add to Cart', 'skyyrose-flagship' ); ?></button>
					<button class="modal-wishlist-btn" type="button" aria-label="<?php esc_attr_e( 'Add to wishlist', 'skyyrose-flagship' ); ?>">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Cart Sidebar -->
	<div class="cart-sidebar-overlay" aria-hidden="true"></div>
	<aside class="cart-sidebar" role="dialog" aria-label="<?php esc_attr_e( 'Shopping cart', 'skyyrose-flagship' ); ?>">
		<div class="cart-sidebar-header">
			<h3 class="cart-sidebar-title"><?php echo esc_html__( 'Your Cart', 'skyyrose-flagship' ); ?></h3>
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
	</aside>

	<!-- Sign-In Panel -->
	<div class="signin-overlay" aria-hidden="true"></div>
	<aside class="signin-panel" role="dialog" aria-label="<?php esc_attr_e( 'Sign in', 'skyyrose-flagship' ); ?>">
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
	</aside>

	<!-- Collection Tabs (Fixed Bottom) -->
	<nav class="collection-tabs" aria-label="<?php esc_attr_e( 'Filter by collection', 'skyyrose-flagship' ); ?>">
		<button class="collection-tab active" type="button" data-collection="all">
			<?php echo esc_html__( 'All', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" data-collection="black-rose">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" data-collection="love-hurts">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</button>
		<button class="collection-tab" type="button" data-collection="signature">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</button>
	</nav>

</main><!-- #primary -->

<?php
// Enqueue gateway assets.
wp_enqueue_style(
	'skyyrose-preorder-gateway',
	get_template_directory_uri() . '/assets/css/preorder-gateway.css',
	array( 'skyyrose-style' ),
	SKYYROSE_VERSION
);

wp_enqueue_script(
	'skyyrose-preorder-gateway',
	get_template_directory_uri() . '/assets/js/preorder-gateway.js',
	array(),
	SKYYROSE_VERSION,
	true
);

get_template_part( 'template-parts/cinematic-toggle' );

get_footer();
