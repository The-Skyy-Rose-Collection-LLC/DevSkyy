<?php
/**
 * SkyyRose Flagship 2 theme foundation.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

define( 'SKYYROSE2_VERSION', '2.3.1' );
define( 'SKYYROSE2_DIR', get_template_directory() );
define( 'SKYYROSE2_URI', get_template_directory_uri() );

/**
 * Resolve a theme-bundled, SOT-approved asset.
 *
 * @param string $path Path beneath assets/sot.
 * @return string
 */
function skyyrose2_sot_asset_uri( $path ) {
	return SKYYROSE2_URI . '/assets/sot/' . ltrim( $path, '/' );
}

/**
 * Resolve an exact snapshot from the current Scroll World sequence.
 *
 * @param string $path Snapshot filename.
 * @return string
 */
function skyyrose2_scroll_world_asset_uri( $path ) {
	return SKYYROSE2_URI . '/assets/scroll-world/' . ltrim( $path, '/' );
}

/** Theme supports and navigation slots. */
function skyyrose2_setup() {
	load_theme_textdomain( 'skyyrose-flagship-2', SKYYROSE2_DIR . '/languages' );
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'align-wide' );
	add_theme_support(
		'html5',
		array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' )
	);
	add_theme_support( 'custom-logo', array( 'height' => 80, 'width' => 320, 'flex-height' => true, 'flex-width' => true ) );
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
	register_nav_menus(
		array(
			'primary' => __( 'Primary Menu', 'skyyrose-flagship-2' ),
			'footer'  => __( 'Footer Menu', 'skyyrose-flagship-2' ),
		)
	);
}
add_action( 'after_setup_theme', 'skyyrose2_setup' );

/** Load self-hosted design system and progressive interactions. */
function skyyrose2_assets() {
	$suffix = defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ? '' : '.min';
	$mascot_suffix = file_exists( SKYYROSE2_DIR . '/assets/css/mascot.css' ) ? $suffix : '.min';

	wp_enqueue_style( 'skyyrose2-tokens', SKYYROSE2_URI . '/assets/css/design-tokens' . $suffix . '.css', array(), SKYYROSE2_VERSION );
	wp_enqueue_style( 'skyyrose2-theme', SKYYROSE2_URI . '/assets/css/theme' . $suffix . '.css', array( 'skyyrose2-tokens' ), SKYYROSE2_VERSION );
	wp_enqueue_script( 'skyyrose2-theme', SKYYROSE2_URI . '/assets/js/theme' . $suffix . '.js', array(), SKYYROSE2_VERSION, true );
	if ( ! ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
		wp_enqueue_style( 'skyyrose2-mascot', SKYYROSE2_URI . '/assets/css/mascot' . $mascot_suffix . '.css', array( 'skyyrose2-tokens' ), SKYYROSE2_VERSION );
		wp_enqueue_script( 'skyyrose2-mascot', SKYYROSE2_URI . '/assets/js/mascot' . $suffix . '.js', array(), SKYYROSE2_VERSION, true );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose2_assets' );

/** Handle client-service messages without exposing raw mail endpoints. */
function skyyrose2_contact_form_submit() {
	if ( 'POST' !== ( $_SERVER['REQUEST_METHOD'] ?? '' ) || empty( $_POST['skyyrose2_contact_submit'] ) ) {
		return;
	}
	if ( ! isset( $_POST['skyyrose2_contact_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose2_contact_nonce'] ) ), 'skyyrose2_contact' ) ) {
		wp_die( esc_html__( 'Security check failed.', 'skyyrose-flagship-2' ), '', array( 'response' => 403 ) );
	}
	$name    = sanitize_text_field( wp_unslash( $_POST['contact_name'] ?? '' ) );
	$email   = sanitize_email( wp_unslash( $_POST['contact_email'] ?? '' ) );
	$subject = sanitize_text_field( wp_unslash( $_POST['contact_subject'] ?? 'Client inquiry' ) );
	$message = sanitize_textarea_field( wp_unslash( $_POST['contact_message'] ?? '' ) );
	if ( ! $name || ! is_email( $email ) || ! $message ) {
		wp_safe_redirect( add_query_arg( 'contact_error', '1', wp_get_referer() ?: home_url( '/contact/' ) ) );
		exit;
	}
	$sent = wp_mail( get_option( 'admin_email' ), '[SkyyRose] ' . $subject, "Name: {$name}\nEmail: {$email}\n\n{$message}", array( 'Reply-To: ' . $email ) );
	wp_safe_redirect( add_query_arg( $sent ? 'contact_sent' : 'contact_error', '1', wp_get_referer() ?: home_url( '/contact/' ) ) );
	exit;
}
add_action( 'init', 'skyyrose2_contact_form_submit' );

/**
 * Canonical collection presentation data derived from each generated SOT view.
 *
 * Product truth still comes from WooCommerce. This map owns narrative and
 * verified non-product visual assignments only.
 *
 * @return array<string,array<string,mixed>>
 */
function skyyrose2_collections() {
	return array(
		'signature'    => array(
			'name'       => __( 'Signature', 'skyyrose-flagship-2' ),
			'kicker'     => __( 'The Origin', 'skyyrose-flagship-2' ),
			'headline'   => __( 'Where everything began.', 'skyyrose-flagship-2' ),
			'line'       => __( 'Oakland-born luxury. Gold light. First rose. Every piece carries the beginning forward.', 'skyyrose-flagship-2' ),
			'manifesto'  => __( 'Before the collection became a house, it was one idea: build something worthy of a daughter and rooted in The Town.', 'skyyrose-flagship-2' ),
			'hero'       => 'branding/hero/signature-golden-gate-yacht-1280w.webp',
			'portrait'   => 'scene-1-signature.webp',
			'portrait_source' => 'scroll-world',
			'lockup'     => 'images/lockups/signature-lockup.webp',
			'atmosphere' => 'images/logos/rose-gold-rose.webp',
			'lookbook'   => 'images/lookbook/lb-rose-hoodie-beanie-480w.webp',
			'world'      => array(
				array( 'image' => 'images/immersive/scene-signature-golden-gate.webp', 'label' => __( 'Golden Gate Salon', 'skyyrose-flagship-2' ), 'copy' => __( 'Gold-hour tailoring above Oakland water.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'branding/hero/signature-golden-gate-yacht-1280w.webp', 'label' => __( 'Bay Atelier', 'skyyrose-flagship-2' ), 'copy' => __( 'The city becomes the showroom.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-signature-oakland-atelier-gpt2.webp', 'label' => __( 'The First Atelier', 'skyyrose-flagship-2' ), 'copy' => __( 'Oakland labor turns into earned elegance.', 'skyyrose-flagship-2' ) ),
			),
		),
		'black-rose'   => array(
			'name'       => __( 'Black Rose', 'skyyrose-flagship-2' ),
			'kicker'     => __( 'Beauty Without Permission', 'skyyrose-flagship-2' ),
			'headline'   => __( 'Defining beauty through black.', 'skyyrose-flagship-2' ),
			'line'       => __( 'Silver-lit armor for people who learned to bloom where nobody expected beauty.', 'skyyrose-flagship-2' ),
			'manifesto'  => __( 'Black is not absence. Black holds depth, power, protection, and elegance. The rose survives because it knows its own value.', 'skyyrose-flagship-2' ),
			'hero'       => 'images/immersive/scene-black-rose-moon-court-gpt2.webp',
			'portrait'   => 'scene-2-black-rose.webp',
			'portrait_source' => 'scroll-world',
			'lockup'     => 'images/lockups/black-rose-lockup.webp',
			'atmosphere' => 'images/logos/black-roses-cloud-cluster.webp',
			'lookbook'   => 'images/immersive/scene-black-rose-moon-court-gpt2.webp',
			'world'      => array(
				array( 'image' => 'scene-2-black-rose.webp', 'source' => 'scroll-world', 'label' => __( 'Forbidden Garden', 'skyyrose-flagship-2' ), 'copy' => __( 'A black rose stands where rules end.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-black-rose-moon-court-gpt2.webp', 'label' => __( 'Midnight House', 'skyyrose-flagship-2' ), 'copy' => __( 'Quiet strength, cut in silver light.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-black-rose-moon-court-gpt2.webp', 'label' => __( 'The Silver Moon Court', 'skyyrose-flagship-2' ), 'copy' => __( 'Beauty stands protected, not hidden.', 'skyyrose-flagship-2' ) ),
			),
		),
		'love-hurts'   => array(
			'name'       => __( 'Love Hurts', 'skyyrose-flagship-2' ),
			'kicker'     => __( 'The Beast Speaks', 'skyyrose-flagship-2' ),
			'headline'   => __( 'Love leaves a mark.', 'skyyrose-flagship-2' ),
			'line'       => __( 'Beauty and the Beast retold from the Beast’s side—crimson, thorned, tender, unapologetic.', 'skyyrose-flagship-2' ),
			'manifesto'  => __( 'Some love heals. Some love scars. Both can shape the person who walks out wearing the truth.', 'skyyrose-flagship-2' ),
			'hero'       => 'branding/hero/beauty-and-beast-1280w.webp',
			'portrait'   => 'scene-3-love-hurts.webp',
			'portrait_source' => 'scroll-world',
			'lockup'     => 'images/lockups/love-hurts-lockup.webp',
			'atmosphere' => 'images/logos/heart-rose-composite.webp',
			'lookbook'   => 'images/lookbook/lb-love-hurts-varsity-480w.webp',
			'world'      => array(
				array( 'image' => 'images/immersive/scene-love-hurts-cathedral.webp', 'label' => __( 'Cathedral of Thorns', 'skyyrose-flagship-2' ), 'copy' => __( 'Reverence, rage, and one protected rose.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'branding/hero/beauty-and-beast-1280w.webp', 'label' => __( 'The Beast’s Chamber', 'skyyrose-flagship-2' ), 'copy' => __( 'The wound becomes the wardrobe.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-love-hurts-cracked-rose-gpt2.webp', 'label' => __( 'The Protected Wound', 'skyyrose-flagship-2' ), 'copy' => __( 'What cracked still guards what mattered.', 'skyyrose-flagship-2' ) ),
			),
		),
		'kids-capsule' => array(
			'name'       => __( 'Kids Capsule', 'skyyrose-flagship-2' ),
			'kicker'     => __( 'The Heir', 'skyyrose-flagship-2' ),
			'headline'   => __( 'Legacy starts early.', 'skyyrose-flagship-2' ),
			'line'       => __( 'Same house codes. New generation. Dark premium pieces built for the ones coming next.', 'skyyrose-flagship-2' ),
			'manifesto'  => __( 'The next generation should inherit more than a name. Give them confidence, imagination, and room to build their own throne.', 'skyyrose-flagship-2' ),
			'hero'       => 'images/immersive/scene-kids-capsule-runway.webp',
			'portrait'   => 'scene-4-kids-capsule.webp',
			'portrait_source' => 'scroll-world',
			'lockup'     => 'images/logos/sr-monogram-rose-gold.webp',
			'atmosphere' => 'images/logos/sr-monogram-rose-gold.webp',
			'lookbook'   => 'images/lookbook/lb-kid-black-rose-480w.webp',
			'world'      => array(
				array( 'image' => 'images/immersive/scene-kids-capsule-playroom.webp', 'label' => __( 'After-Dark Playroom', 'skyyrose-flagship-2' ), 'copy' => __( 'Imagination dressed with intention.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-kids-capsule-runway.webp', 'label' => __( 'First Runway', 'skyyrose-flagship-2' ), 'copy' => __( 'Small steps. Main-character energy.', 'skyyrose-flagship-2' ) ),
				array( 'image' => 'images/immersive/scene-kids-capsule-heir-runway-gpt2.webp', 'label' => __( 'The Heir’s Salon', 'skyyrose-flagship-2' ), 'copy' => __( 'Legacy becomes room to imagine bigger.', 'skyyrose-flagship-2' ) ),
			),
		),
	);
}

/** @param string $slug Collection slug. @return string */
function skyyrose2_collection_url( $slug ) {
	return home_url( '/collections/' . sanitize_title( $slug ) . '/' );
}

/** @return int Live cart count without assuming WooCommerce is active. */
function skyyrose2_cart_count() {
	return function_exists( 'WC' ) && WC()->cart ? WC()->cart->get_cart_contents_count() : 0;
}

/**
 * Query published products for reusable marketplace sections.
 *
 * @param int    $limit Product limit.
 * @param string $collection Product category slug.
 * @param bool   $featured Featured-only query.
 * @return array<int,WC_Product>
 */
function skyyrose2_get_products( $limit = 6, $collection = '', $featured = false ) {
	if ( ! function_exists( 'wc_get_products' ) ) {
		return array();
	}
	$args = array(
		'limit'   => absint( $limit ),
		'status'  => 'publish',
		'orderby' => 'date',
		'order'   => 'DESC',
	);
	if ( $collection ) {
		$args['category'] = array( sanitize_title( $collection ) );
	}
	if ( $featured ) {
		$args['featured'] = true;
	}
	return wc_get_products( $args );
}

/**
 * Render product cards with WooCommerce as product truth.
 *
 * @param int    $limit Product limit.
 * @param string $collection Category slug.
 * @param bool   $featured Featured-only query.
 */
function skyyrose2_product_cards( $limit = 6, $collection = '', $featured = false ) {
	$products = skyyrose2_get_products( $limit, $collection, $featured );
	if ( empty( $products ) && 'pre-order' === $collection ) {
		$products = skyyrose2_get_products( $limit, '', $featured );
	}
	if ( empty( $products ) && $featured ) {
		$products = skyyrose2_get_products( $limit, $collection, false );
	}
	if ( empty( $products ) ) {
		echo '<p class="sr2-empty">' . esc_html__( 'Next pieces entering the world soon.', 'skyyrose-flagship-2' ) . '</p>';
		return;
	}
	?>
	<div class="sr2-products">
		<?php foreach ( $products as $product ) : ?>
			<?php
			$product_url = get_permalink( $product->get_id() );
			$image_id    = $product->get_image_id();
			$categories  = wc_get_product_category_list( $product->get_id(), ' · ' );
			?>
			<article class="sr2-product" data-depth-card>
				<a class="sr2-product__image" href="<?php echo esc_url( $product_url ); ?>">
					<?php
					if ( $image_id ) {
						echo wp_kses_post( wp_get_attachment_image( $image_id, 'woocommerce_thumbnail', false, array( 'loading' => 'lazy', 'decoding' => 'async' ) ) );
					} else {
						echo '<span class="sr2-product__image-empty" aria-hidden="true"></span>';
					}
					?>
					<span class="sr2-product__view"><?php esc_html_e( 'View piece', 'skyyrose-flagship-2' ); ?></span>
				</a>
				<p class="sr2-product__meta"><?php echo $categories ? wp_kses_post( $categories ) : esc_html__( 'SkyyRose', 'skyyrose-flagship-2' ); ?></p>
				<h3><a href="<?php echo esc_url( $product_url ); ?>"><?php echo esc_html( $product->get_name() ); ?></a></h3>
				<div class="sr2-product__bottom">
					<span><?php echo wp_kses_post( $product->get_price_html() ); ?></span>
					<span><?php echo esc_html( $product->is_in_stock() ? __( 'Available', 'skyyrose-flagship-2' ) : __( 'Reserved', 'skyyrose-flagship-2' ) ); ?></span>
				</div>
			</article>
		<?php endforeach; ?>
	</div>
	<?php
}

/** Render collection runway with accessible native horizontal scroll. */
function skyyrose2_render_collection_rail() {
	$collections = skyyrose2_collections();
	?>
	<section class="sr2-worlds" aria-labelledby="sr2-worlds-title" data-horizontal-world>
		<header class="sr2-section-head sr2-section-head--split">
			<div><p><?php esc_html_e( 'Choose Your World', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-worlds-title"><?php esc_html_e( 'Four stories. One house.', 'skyyrose-flagship-2' ); ?></h2></div>
			<div class="sr2-rail-controls"><button type="button" data-rail-prev aria-label="<?php esc_attr_e( 'Previous collection', 'skyyrose-flagship-2' ); ?>">←</button><span data-rail-count>01 / 04</span><button type="button" data-rail-next aria-label="<?php esc_attr_e( 'Next collection', 'skyyrose-flagship-2' ); ?>">→</button></div>
		</header>
		<div class="sr2-worlds__stage" data-scroll-world-stage>
		<div class="sr2-worlds__rail" tabindex="0" aria-label="<?php esc_attr_e( 'Collection worlds. Scroll horizontally.', 'skyyrose-flagship-2' ); ?>" data-horizontal-rail>
			<?php foreach ( $collections as $index => $collection ) : ?>
				<?php
				if ( isset( $collection['portrait_source'] ) && 'scroll-world' === $collection['portrait_source'] ) {
					$portrait_uri = skyyrose2_scroll_world_asset_uri( $collection['portrait'] );
				} else {
					$portrait_uri = skyyrose2_sot_asset_uri( $collection['portrait'] );
				}
				?>
				<a class="sr2-world" data-collection="<?php echo esc_attr( $index ); ?>" href="<?php echo esc_url( skyyrose2_collection_url( $index ) ); ?>">
					<img src="<?php echo esc_url( $portrait_uri ); ?>" alt="" width="1920" height="1275" loading="<?php echo 0 === array_search( $index, array_keys( $collections ), true ) ? 'eager' : 'lazy'; ?>" decoding="async">
					<span class="sr2-world__shade" aria-hidden="true"></span>
					<span class="sr2-world__copy"><small><?php echo esc_html( sprintf( '%02d · %s', array_search( $index, array_keys( $collections ), true ) + 1, $collection['kicker'] ) ); ?></small><strong><?php echo esc_html( $collection['name'] ); ?></strong><em><?php echo esc_html( $collection['line'] ); ?></em><b><?php esc_html_e( 'Enter world', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></b></span>
				</a>
			<?php endforeach; ?>
		</div>
		<div class="sr2-rail-progress" aria-hidden="true"><span data-rail-progress></span></div>
		</div>
	</section>
	<?php
}

/** Render site header. */
function skyyrose2_header() {
	$bag_url = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );
	?>
	<header class="sr2-header" data-site-header>
		<button class="sr2-header__menu" type="button" aria-controls="sr2-menu" aria-expanded="false" data-sr2-menu><span></span><span><?php esc_html_e( 'Menu', 'skyyrose-flagship-2' ); ?></span></button>
		<a class="sr2-header__brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'SkyyRose home', 'skyyrose-flagship-2' ); ?>"><video class="sr2-header__brand-video" muted loop playsinline preload="metadata" poster="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webp' ) ); ?>" data-brand-spin aria-hidden="true"><source src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webm' ) ); ?>" type="video/webm"></video><span class="screen-reader-text"><?php esc_html_e( 'SkyyRose', 'skyyrose-flagship-2' ); ?></span></a>
		<a class="sr2-header__bag" href="<?php echo esc_url( $bag_url ); ?>"><?php esc_html_e( 'Bag', 'skyyrose-flagship-2' ); ?> <span aria-label="<?php esc_attr_e( 'items in bag', 'skyyrose-flagship-2' ); ?>"><?php echo esc_html( skyyrose2_cart_count() ); ?></span></a>
		<nav id="sr2-menu" class="sr2-header__nav" aria-label="<?php esc_attr_e( 'Primary navigation', 'skyyrose-flagship-2' ); ?>" data-sr2-nav>
			<div class="sr2-header__nav-main">
				<a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><span>01</span><?php esc_html_e( 'Collections', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>"><span>02</span><?php esc_html_e( 'Shop', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><span>03</span><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><span>04</span><?php esc_html_e( 'About', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><span>05</span><?php esc_html_e( 'Contact', 'skyyrose-flagship-2' ); ?></a>
			</div>
			<div class="sr2-header__nav-collections">
				<?php foreach ( skyyrose2_collections() as $slug => $collection ) : ?>
					<a data-collection="<?php echo esc_attr( $slug ); ?>" href="<?php echo esc_url( skyyrose2_collection_url( $slug ) ); ?>"><?php echo esc_html( $collection['name'] ); ?></a>
				<?php endforeach; ?>
			</div>
		</nav>
	</header>
	<?php
}

/** Render site footer. */
function skyyrose2_footer() {
	?>
	<footer class="sr2-footer">
		<div><a class="sr2-footer__brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'SkyyRose home', 'skyyrose-flagship-2' ); ?>"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/lockups/signature-lockup.webp' ) ); ?>" alt="" width="900" height="400" loading="lazy"></a><p><?php esc_html_e( 'Oakland, California · Independent luxury fashion.', 'skyyrose-flagship-2' ); ?></p></div>
		<nav aria-label="<?php esc_attr_e( 'Footer navigation', 'skyyrose-flagship-2' ); ?>"><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><?php esc_html_e( 'Shipping + Returns', 'skyyrose-flagship-2' ); ?></a><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>"><?php esc_html_e( 'Size Guide', 'skyyrose-flagship-2' ); ?></a><a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><?php esc_html_e( 'Support', 'skyyrose-flagship-2' ); ?></a></nav>
		<p class="sr2-footer__legal">© <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php esc_html_e( 'The Skyy Rose Collection LLC', 'skyyrose-flagship-2' ); ?></p>
	</footer>
	<?php
}

/** Route collection child pages without manual template assignment. */
function skyyrose2_collection_template( $template ) {
	if ( ! is_page() ) {
		return $template;
	}
	$slug = get_post_field( 'post_name', get_queried_object_id() );
	if ( array_key_exists( $slug, skyyrose2_collections() ) ) {
		$collection_template = SKYYROSE2_DIR . '/template-collection.php';
		if ( file_exists( $collection_template ) ) {
			return $collection_template;
		}
	}
	return $template;
}
add_filter( 'template_include', 'skyyrose2_collection_template', 20 );

/** Keep custom Woo wrappers structurally clean. */
function skyyrose2_woocommerce_wrappers() {
	remove_action( 'woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10 );
	remove_action( 'woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10 );
}
add_action( 'wp', 'skyyrose2_woocommerce_wrappers' );
