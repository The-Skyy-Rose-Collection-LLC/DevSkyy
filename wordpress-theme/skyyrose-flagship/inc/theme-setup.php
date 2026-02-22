<?php
/**
 * Theme Setup
 *
 * Registers theme supports, navigation menus, custom image sizes,
 * content width, widget areas, and WooCommerce HPOS compatibility.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Sets up theme defaults and registers support for various WordPress features.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_setup() {

	// Make the theme translatable.
	load_theme_textdomain( 'skyyrose-flagship', SKYYROSE_DIR . '/languages' );

	// Add default posts and comments RSS feed links to head.
	add_theme_support( 'automatic-feed-links' );

	// Let WordPress manage the document title.
	add_theme_support( 'title-tag' );

	// Enable support for Post Thumbnails on posts and pages.
	add_theme_support( 'post-thumbnails' );

	/*
	 * Custom image sizes.
	 *
	 * Product card: 3:4 ratio for collection grid cards.
	 * Product hero: 2:3 ratio for immersive hero sections.
	 * Legacy featured: general-purpose 16:9 hero image.
	 */
	add_image_size( 'product-card', 400, 533, true );
	add_image_size( 'product-hero', 1024, 1536, true );
	add_image_size( 'skyyrose-featured', 1200, 675, true );
	add_image_size( 'skyyrose-thumbnail', 400, 300, true );
	add_image_size( 'skyyrose-medium', 800, 600, true );

	/*
	 * Register navigation menus.
	 *
	 * primary      - Main header navigation
	 * footer-shop  - Footer column: Shop links
	 * footer-help  - Footer column: Help / support links
	 * footer-legal - Footer column: Legal / policy links
	 * mobile       - Mobile-specific navigation (legacy)
	 * top-bar      - Announcement / utility bar (legacy)
	 */
	register_nav_menus(
		array(
			'primary'      => esc_html__( 'Primary Menu', 'skyyrose-flagship' ),
			'footer-shop'  => esc_html__( 'Footer - Shop', 'skyyrose-flagship' ),
			'footer-help'  => esc_html__( 'Footer - Help', 'skyyrose-flagship' ),
			'footer-legal' => esc_html__( 'Footer - Legal', 'skyyrose-flagship' ),
			'footer'       => esc_html__( 'Footer Menu', 'skyyrose-flagship' ),
			'mobile'       => esc_html__( 'Mobile Menu', 'skyyrose-flagship' ),
			'top-bar'      => esc_html__( 'Top Bar Menu', 'skyyrose-flagship' ),
		)
	);

	// Switch default core markup to valid HTML5.
	add_theme_support(
		'html5',
		array(
			'search-form',
			'comment-form',
			'comment-list',
			'gallery',
			'caption',
			'style',
			'script',
			'navigation-widgets',
		)
	);

	// Core custom logo support.
	add_theme_support(
		'custom-logo',
		array(
			'height'      => 100,
			'width'       => 400,
			'flex-width'  => true,
			'flex-height' => true,
		)
	);

	// Selective refresh for widgets in the Customizer.
	add_theme_support( 'customize-selective-refresh-widgets' );

	// Wide and full alignment for the block editor.
	add_theme_support( 'align-wide' );

	// Editor styles.
	add_theme_support( 'editor-styles' );

	// Responsive embeds.
	add_theme_support( 'responsive-embeds' );

	// Custom line height, spacing, and units.
	add_theme_support( 'custom-line-height' );
	add_theme_support( 'custom-spacing' );
	add_theme_support( 'custom-units' );

	// WooCommerce support.
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );

	// Elementor support.
	add_theme_support( 'elementor' );
}
add_action( 'after_setup_theme', 'skyyrose_setup' );

/**
 * Declare WooCommerce HPOS (High-Performance Order Storage) compatibility.
 *
 * Ensures compatibility with WooCommerce 8.5+ Custom Order Tables feature.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_declare_woocommerce_hpos_compatibility() {
	if ( class_exists( '\Automattic\WooCommerce\Utilities\FeaturesUtil' ) ) {
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
			'custom_order_tables',
			SKYYROSE_DIR . '/functions.php',
			true
		);
	}
}
add_action( 'before_woocommerce_init', 'skyyrose_declare_woocommerce_hpos_compatibility' );

/**
 * Set the content width in pixels, based on the theme's design.
 *
 * @since  1.0.0
 * @global int $content_width
 * @return void
 */
function skyyrose_content_width() {
	$GLOBALS['content_width'] = apply_filters( 'skyyrose_content_width', 1200 );
}
add_action( 'after_setup_theme', 'skyyrose_content_width', 0 );

/**
 * Register widget areas.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_widgets_init() {

	$widget_defaults = array(
		'before_widget' => '<section id="%1$s" class="widget %2$s">',
		'after_widget'  => '</section>',
		'before_title'  => '<h2 class="widget-title">',
		'after_title'   => '</h2>',
	);

	$sidebars = array(
		array(
			'name'        => esc_html__( 'Primary Sidebar', 'skyyrose-flagship' ),
			'id'          => 'sidebar-1',
			'description' => esc_html__( 'Add widgets here to appear in your sidebar.', 'skyyrose-flagship' ),
		),
		array(
			'name'        => esc_html__( 'Footer Area 1', 'skyyrose-flagship' ),
			'id'          => 'footer-1',
			'description' => esc_html__( 'First footer widget area.', 'skyyrose-flagship' ),
		),
		array(
			'name'        => esc_html__( 'Footer Area 2', 'skyyrose-flagship' ),
			'id'          => 'footer-2',
			'description' => esc_html__( 'Second footer widget area.', 'skyyrose-flagship' ),
		),
		array(
			'name'        => esc_html__( 'Footer Area 3', 'skyyrose-flagship' ),
			'id'          => 'footer-3',
			'description' => esc_html__( 'Third footer widget area.', 'skyyrose-flagship' ),
		),
		array(
			'name'        => esc_html__( 'Footer Area 4', 'skyyrose-flagship' ),
			'id'          => 'footer-4',
			'description' => esc_html__( 'Fourth footer widget area.', 'skyyrose-flagship' ),
		),
	);

	foreach ( $sidebars as $sidebar ) {
		register_sidebar( array_merge( $widget_defaults, $sidebar ) );
	}

	// WooCommerce shop sidebar (only if WooCommerce is active).
	if ( class_exists( 'WooCommerce' ) ) {
		register_sidebar(
			array_merge(
				$widget_defaults,
				array(
					'name'        => esc_html__( 'Shop Sidebar', 'skyyrose-flagship' ),
					'id'          => 'shop-sidebar',
					'description' => esc_html__( 'Widgets for WooCommerce shop pages.', 'skyyrose-flagship' ),
				)
			)
		);
	}
}
add_action( 'widgets_init', 'skyyrose_widgets_init' );

/**
 * Register Wishlist Custom Post Type.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_register_wishlist_cpt() {
	$args = array(
		'labels'              => array(
			'name'          => esc_html__( 'Wishlists', 'skyyrose-flagship' ),
			'singular_name' => esc_html__( 'Wishlist', 'skyyrose-flagship' ),
		),
		'public'              => false,
		'has_archive'         => false,
		'publicly_queryable'  => false,
		'show_ui'             => true,
		'show_in_menu'        => true,
		'show_in_nav_menus'   => false,
		'show_in_rest'        => true,
		'exclude_from_search' => true,
		'capability_type'     => 'post',
		'hierarchical'        => false,
		'rewrite'             => false,
		'supports'            => array( 'title', 'author' ),
		'menu_icon'           => 'dashicons-heart',
	);

	register_post_type( 'wishlist', $args );
}
add_action( 'init', 'skyyrose_register_wishlist_cpt' );

/**
 * Add custom body classes.
 *
 * @since 1.0.0
 *
 * @param  array $classes Existing body classes.
 * @return array Modified classes.
 */
function skyyrose_body_classes( $classes ) {

	if ( is_customize_preview() ) {
		$classes[] = 'customizer-preview';
	}

	if ( class_exists( 'WooCommerce' ) && is_woocommerce() ) {
		$classes[] = 'woocommerce-page';
	}

	$post_id = get_the_ID();
	if ( $post_id && did_action( 'elementor/loaded' ) && class_exists( '\Elementor\Plugin' ) ) {
		$elementor_instance = \Elementor\Plugin::$instance;
		if ( $elementor_instance && isset( $elementor_instance->documents ) ) {
			$document = $elementor_instance->documents->get( $post_id );
			if ( $document && method_exists( $document, 'is_built_with_elementor' ) && $document->is_built_with_elementor() ) {
				$classes[] = 'elementor-page';
			}
		}
	}

	if ( is_singular() ) {
		$classes[] = 'singular';
	}

	return $classes;
}
add_filter( 'body_class', 'skyyrose_body_classes' );

/**
 * Add a pingback URL auto-discovery header for singularly identifiable articles.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_pingback_header() {
	if ( is_singular() && pings_open() ) {
		printf( '<link rel="pingback" href="%s">', esc_url( get_bloginfo( 'pingback_url' ) ) );
	}
}
add_action( 'wp_head', 'skyyrose_pingback_header' );

/**
 * Disable WordPress.com asset optimization that causes MIME errors.
 *
 * @since 2.0.0
 * @return void
 */
function skyyrose_disable_wpcom_optimization() {
	add_filter( 'jetpack_photon_skip_image', '__return_true', 999 );
	add_filter( 'jetpack_implode_frontend_css', '__return_false', 999 );
	add_filter( 'js_do_concat', '__return_false', 999 );
	add_filter( 'css_do_concat', '__return_false', 999 );
}
add_action( 'init', 'skyyrose_disable_wpcom_optimization', 1 );
