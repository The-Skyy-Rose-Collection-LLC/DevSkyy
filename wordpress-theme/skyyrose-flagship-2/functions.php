<?php
/**
 * SkyyRose Flagship 2 theme foundation.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

define( 'SKYYROSE2_VERSION', '2.3.6' );
define( 'SKYYROSE2_DIR', get_template_directory() );
define( 'SKYYROSE2_URI', get_template_directory_uri() );
define( 'SKYYROSE2_REWRITE_SCHEMA', '2026-08-04-1' );

require_once SKYYROSE2_DIR . '/inc/product-3d-viewer.php';
require_once SKYYROSE2_DIR . '/inc/builder-compat.php';
require_once SKYYROSE2_DIR . '/inc/woocommerce-integration.php';

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
	add_theme_support( 'wp-block-styles' );
	add_theme_support(
		'html5',
		array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' )
	);
	add_theme_support(
		'woocommerce',
		array(
			'thumbnail_image_width' => 720,
			'single_image_width'    => 1280,
			'product_grid'          => array(
				'default_rows'    => 3,
				'min_rows'        => 1,
				'max_rows'        => 8,
				'default_columns' => 3,
				'min_columns'     => 1,
				'max_columns'     => 4,
			),
		)
	);
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

/** Set the default measure used by WordPress and builder content. */
function skyyrose2_content_width() {
	$GLOBALS['content_width'] = (int) apply_filters( 'skyyrose2_content_width', 1200 );
}
add_action( 'after_setup_theme', 'skyyrose2_content_width', 0 );

/** Load self-hosted design system and progressive interactions. */
function skyyrose2_assets() {
	$suffix = defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ? '' : '.min';

	wp_enqueue_style( 'skyyrose2-tokens', SKYYROSE2_URI . '/assets/css/design-tokens' . $suffix . '.css', array(), SKYYROSE2_VERSION );
	wp_enqueue_style( 'skyyrose2-theme', SKYYROSE2_URI . '/assets/css/theme' . $suffix . '.css', array( 'skyyrose2-tokens' ), SKYYROSE2_VERSION );
	wp_enqueue_script( 'skyyrose2-theme', SKYYROSE2_URI . '/assets/js/theme' . $suffix . '.js', array(), SKYYROSE2_VERSION, true );
	wp_script_add_data( 'skyyrose2-theme', 'strategy', 'defer' );

	// The mascot is deliberately initialized after the document is parsed. Its
	// non-critical stylesheet is requested by the mascot script, ahead of its
	// first possible appearance, rather than blocking the initial render.
	if ( ! ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
		wp_enqueue_script( 'skyyrose2-mascot', SKYYROSE2_URI . '/assets/js/mascot' . $suffix . '.js', array(), SKYYROSE2_VERSION, true );
		wp_script_add_data( 'skyyrose2-mascot', 'strategy', 'defer' );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose2_assets' );

/** Preload the responsive homepage LCP image before styles are printed. */
function skyyrose2_preload_home_hero() {
	if ( ! is_front_page() ) {
		return;
	}

	$hero_base = skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2' );
	$srcset    = sprintf(
		'%1$s-640w.webp 640w, %1$s-960w.webp 960w, %1$s-1440w.webp 1440w, %1$s.webp 1920w',
		esc_url( $hero_base )
	);

	printf(
		'<link rel="preload" as="image" href="%1$s" imagesrcset="%2$s" imagesizes="100vw" fetchpriority="high">' . "\n",
		esc_url( $hero_base . '-1440w.webp' ),
		esc_attr( $srcset )
	);
}
add_action( 'wp_head', 'skyyrose2_preload_home_hero', 1 );

/**
 * Return the approved, externally delivered About film URL.
 *
 * The film is intentionally hosted outside the theme archive so the installable
 * package remains small and does not duplicate a high-bitrate source asset.
 *
 * @return string
 */
function skyyrose2_about_film_url() {
	return esc_url( get_theme_mod( 'skyyrose2_about_film_url', '' ) );
}

/**
 * Register the externally delivered, muted About film field.
 *
 * @param WP_Customize_Manager $customize_manager Theme customizer manager.
 * @return void
 */
function skyyrose2_customize_about_film( $customize_manager ) {
	$customize_manager->add_section(
		'skyyrose2_about_film',
		array(
			'title'    => __( 'About Film', 'skyyrose-flagship-2' ),
			'priority' => 35,
		)
	);
	$customize_manager->add_setting(
		'skyyrose2_about_film_url',
		array(
			'sanitize_callback' => 'esc_url_raw',
		)
	);
	$customize_manager->add_control(
		'skyyrose2_about_film_url',
		array(
			'label'       => __( 'Muted About film URL', 'skyyrose-flagship-2' ),
			'description' => __( 'Use only the approved muted MP4 delivery URL. The film is opt-in and never autoplays.', 'skyyrose-flagship-2' ),
			'section'     => 'skyyrose2_about_film',
			'type'        => 'url',
		)
	);
}
add_action( 'customize_register', 'skyyrose2_customize_about_film' );

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
			'headline'   => __( 'Not basics. Blueprints.', 'skyyrose-flagship-2' ),
			'line'       => __( 'The first rose. The Oakland foundation. Signature is that night made permanent.', 'skyyrose-flagship-2' ),
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
			'headline'   => __( 'Defining beauty through the color black.', 'skyyrose-flagship-2' ),
			'line'       => __( 'A posture, a conviction, an Oakland truth made into fabric.', 'skyyrose-flagship-2' ),
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
			'headline'   => __( 'They called me Beast. They were right.', 'skyyrose-flagship-2' ),
			'line'       => __( 'The Hurts bloodline, the enchanted rose, and raw romance told from the Beast’s side.', 'skyyrose-flagship-2' ),
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
			'headline'   => __( 'The Heir to the throne.', 'skyyrose-flagship-2' ),
			'line'       => __( 'Luxury runs in the family: same craftsmanship, smaller silhouettes, legacy carried forward.', 'skyyrose-flagship-2' ),
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

/**
 * Resolve founder-selected collection context for a Pre-Order page.
 *
 * The supplied campaign film was visually verified against the catalog SOT as
 * br-006 / The Bomber Sherpa, a Black Rose garment. Editors may override the
 * default with page meta only when a later founder-approved verification
 * records a different collection.
 *
 * @param int $post_id Page ID.
 * @return string Approved collection slug or an empty string when unassigned.
 */
function skyyrose2_preorder_collection( $post_id ) {
	$allowed = array( 'signature', 'black-rose', 'love-hurts', 'kids-capsule' );
	$value   = sanitize_title( (string) get_post_meta( absint( $post_id ), 'skyyrose2_preorder_collection', true ) );
	$value   = $value ? $value : 'black-rose';

	return in_array( $value, $allowed, true ) ? $value : '';
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
	if ( empty( $products ) ) {
		$empty_message = 'pre-order' === $collection
			? __( 'No pieces are currently marked for pre-order.', 'skyyrose-flagship-2' )
			: __( 'Next pieces entering the world soon.', 'skyyrose-flagship-2' );
		echo '<p class="sr2-empty">' . esc_html( $empty_message ) . '</p>';
		return;
	}
	?>
	<div class="sr2-products">
		<?php foreach ( $products as $index => $product ) : ?>
			<?php
			get_template_part(
				'template-parts/product-card',
				null,
				array(
					'product'        => $product,
					'image_loading'  => 0 === $index ? 'eager' : 'lazy',
					'image_priority' => 0 === $index,
				)
			);
			?>
		<?php endforeach; ?>
	</div>
	<?php
}

/** Render collection runway with accessible native horizontal scroll. */
function skyyrose2_render_collection_rail() {
	$collections = skyyrose2_collections();
	?>
	<section class="sr2-worlds" aria-labelledby="sr2-worlds-title" data-horizontal-world data-pinned-scroll-world>
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
						<span class="sr2-world__copy"><small><?php echo esc_html( sprintf( '%02d · %s', array_search( $index, array_keys( $collections ), true ) + 1, $collection['kicker'] ) ); ?></small><img class="sr2-world__lockup" src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['lockup'] ) ); ?>" alt="<?php echo esc_attr( $collection['name'] ); ?>" width="900" height="400" loading="lazy" decoding="async"><strong><?php echo esc_html( $collection['name'] ); ?></strong><em><?php echo esc_html( $collection['line'] ); ?></em><b><?php esc_html_e( 'Enter world', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></b></span>
				</a>
			<?php endforeach; ?>
		</div>
		<div class="sr2-rail-progress" aria-hidden="true"><span data-rail-progress></span></div>
		</div>
	</section>
	<?php
}

/**
 * Return configured top-level menu items for a registered theme location.
 *
 * @param string $location Registered menu location.
 * @return array<int,WP_Post>
 */
function skyyrose2_menu_items( $location ) {
	$locations = get_nav_menu_locations();
	if ( empty( $locations[ $location ] ) ) {
		return array();
	}
	$items = wp_get_nav_menu_items( $locations[ $location ] );
	if ( ! is_array( $items ) ) {
		return array();
	}
	return array_values(
		array_filter(
			$items,
			static function ( $item ) {
				return 0 === (int) $item->menu_item_parent;
			}
		)
	);
}

/** Render site header. */
function skyyrose2_header() {
	$bag_url       = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );
	$primary_items = skyyrose2_menu_items( 'primary' );
	?>
	<header class="sr2-header" data-site-header>
		<button class="sr2-header__menu" type="button" aria-controls="sr2-menu" aria-expanded="false" data-sr2-menu><span></span><span><?php esc_html_e( 'Menu', 'skyyrose-flagship-2' ); ?></span></button>
		<a class="sr2-header__brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'SkyyRose home', 'skyyrose-flagship-2' ); ?>"><video class="sr2-header__brand-video" muted loop playsinline preload="metadata" poster="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webp' ) ); ?>" data-brand-spin aria-hidden="true"><source src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webm' ) ); ?>" type="video/webm"></video><span class="screen-reader-text"><?php esc_html_e( 'SkyyRose', 'skyyrose-flagship-2' ); ?></span></a>
		<a class="sr2-header__bag" href="<?php echo esc_url( $bag_url ); ?>"><?php esc_html_e( 'Bag', 'skyyrose-flagship-2' ); ?> <span aria-label="<?php esc_attr_e( 'items in bag', 'skyyrose-flagship-2' ); ?>"><?php echo esc_html( skyyrose2_cart_count() ); ?></span></a>
		<nav id="sr2-menu" class="sr2-header__nav" aria-label="<?php esc_attr_e( 'Primary navigation', 'skyyrose-flagship-2' ); ?>" data-sr2-nav>
			<div class="sr2-header__nav-main">
				<?php if ( $primary_items ) : ?>
					<?php foreach ( $primary_items as $index => $item ) : ?><a href="<?php echo esc_url( $item->url ); ?>"><span><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span><?php echo esc_html( $item->title ); ?></a><?php endforeach; ?>
				<?php else : ?>
					<a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><span>01</span><?php esc_html_e( 'Collections', 'skyyrose-flagship-2' ); ?></a>
					<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>"><span>02</span><?php esc_html_e( 'Shop', 'skyyrose-flagship-2' ); ?></a>
					<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><span>03</span><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship-2' ); ?></a>
					<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><span>04</span><?php esc_html_e( 'About', 'skyyrose-flagship-2' ); ?></a>
					<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><span>05</span><?php esc_html_e( 'Contact', 'skyyrose-flagship-2' ); ?></a>
				<?php endif; ?>
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
	$footer_items = skyyrose2_menu_items( 'footer' );
	?>
	<footer class="sr2-footer">
		<div><a class="sr2-footer__brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'SkyyRose home', 'skyyrose-flagship-2' ); ?>"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/lockups/signature-lockup.webp' ) ); ?>" alt="" width="900" height="400" loading="lazy"></a><p><?php esc_html_e( 'Oakland, California · Independent luxury fashion.', 'skyyrose-flagship-2' ); ?></p></div>
		<nav aria-label="<?php esc_attr_e( 'Footer navigation', 'skyyrose-flagship-2' ); ?>"><?php if ( $footer_items ) : ?><?php foreach ( $footer_items as $item ) : ?><a href="<?php echo esc_url( $item->url ); ?>"><?php echo esc_html( $item->title ); ?></a><?php endforeach; ?><?php else : ?><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><?php esc_html_e( 'Shipping + Returns', 'skyyrose-flagship-2' ); ?></a><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>"><?php esc_html_e( 'Size Guide', 'skyyrose-flagship-2' ); ?></a><a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><?php esc_html_e( 'Support', 'skyyrose-flagship-2' ); ?></a><?php endif; ?></nav>
		<p class="sr2-footer__legal">© <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php esc_html_e( 'The Skyy Rose Collection LLC', 'skyyrose-flagship-2' ); ?></p>
	</footer>
	<?php
}

/** Register virtual collection routes so staging does not require four hand-made pages. */
function skyyrose2_collection_rewrites() {
	add_rewrite_tag( '%skyyrose2_collections_index%', '([01])' );
	add_rewrite_tag( '%skyyrose2_collection%', '([^&]+)' );
	add_rewrite_rule( '^collections/?$', 'index.php?skyyrose2_collections_index=1', 'top' );
	add_rewrite_rule( '^collections/([^/]+)/?$', 'index.php?skyyrose2_collection=$matches[1]', 'top' );
}
add_action( 'init', 'skyyrose2_collection_rewrites' );

/** Flush the virtual collection routes when this theme is activated. */
function skyyrose2_flush_collection_rewrites() {
	skyyrose2_collection_rewrites();
	flush_rewrite_rules( false );
	update_option( 'skyyrose2_rewrite_schema', SKYYROSE2_REWRITE_SCHEMA, false );
}
add_action( 'after_switch_theme', 'skyyrose2_flush_collection_rewrites' );

/** Flush rewritten collection routes once after an in-place theme update. */
function skyyrose2_maybe_flush_collection_rewrites() {
	if ( SKYYROSE2_REWRITE_SCHEMA === get_option( 'skyyrose2_rewrite_schema' ) ) {
		return;
	}

	flush_rewrite_rules( false );
	update_option( 'skyyrose2_rewrite_schema', SKYYROSE2_REWRITE_SCHEMA, false );
}
add_action( 'init', 'skyyrose2_maybe_flush_collection_rewrites', 99 );

/** Mark only recognized virtual collection routes as successful before canonical redirects. */
function skyyrose2_prepare_virtual_collection_response() {
	$virtual_index = '1' === (string) get_query_var( 'skyyrose2_collections_index' );
	$virtual_slug  = sanitize_title( (string) get_query_var( 'skyyrose2_collection' ) );
	if ( ! $virtual_index && ! array_key_exists( $virtual_slug, skyyrose2_collections() ) ) {
		return;
	}

	global $wp_query;
	$wp_query->is_404 = false;
	status_header( 200 );
}
add_action( 'template_redirect', 'skyyrose2_prepare_virtual_collection_response', 0 );

/** Route collection child pages without manual template assignment. */
function skyyrose2_collection_template( $template ) {
	if ( '1' === (string) get_query_var( 'skyyrose2_collections_index' ) ) {
		$index_template = SKYYROSE2_DIR . '/template-collections-index.php';
		return file_exists( $index_template ) ? $index_template : $template;
	}

	$virtual_slug = sanitize_title( (string) get_query_var( 'skyyrose2_collection' ) );
	if ( $virtual_slug && array_key_exists( $virtual_slug, skyyrose2_collections() ) ) {
		$collection_template = SKYYROSE2_DIR . '/template-collection.php';
		return file_exists( $collection_template ) ? $collection_template : $template;
	}

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
