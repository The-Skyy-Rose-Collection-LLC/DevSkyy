<?php
/**
 * SkyyRose Flagship Theme Functions
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Theme Constants
 */
define( 'SKYYROSE_VERSION', '1.0.0' );
define( 'SKYYROSE_THEME_DIR', get_template_directory() );
define( 'SKYYROSE_THEME_URI', get_template_directory_uri() );
define( 'SKYYROSE_ASSETS_URI', SKYYROSE_THEME_URI . '/assets' );

/**
 * Theme Setup
 *
 * Sets up theme defaults and registers support for various WordPress features.
 *
 * @since 1.0.0
 */
function skyyrose_setup() {
	/*
	 * Make theme available for translation.
	 */
	load_theme_textdomain( 'skyyrose-flagship', SKYYROSE_THEME_DIR . '/languages' );

	/*
	 * Add default posts and comments RSS feed links to head.
	 */
	add_theme_support( 'automatic-feed-links' );

	/*
	 * Let WordPress manage the document title.
	 */
	add_theme_support( 'title-tag' );

	/*
	 * Enable support for Post Thumbnails on posts and pages.
	 */
	add_theme_support( 'post-thumbnails' );

	/*
	 * Add custom image sizes.
	 */
	add_image_size( 'skyyrose-featured', 1200, 675, true );
	add_image_size( 'skyyrose-thumbnail', 400, 300, true );
	add_image_size( 'skyyrose-medium', 800, 600, true );

	/*
	 * Register navigation menus.
	 */
	register_nav_menus(
		array(
			'primary'   => esc_html__( 'Primary Menu', 'skyyrose-flagship' ),
			'footer'    => esc_html__( 'Footer Menu', 'skyyrose-flagship' ),
			'mobile'    => esc_html__( 'Mobile Menu', 'skyyrose-flagship' ),
			'top-bar'   => esc_html__( 'Top Bar Menu', 'skyyrose-flagship' ),
		)
	);

	/*
	 * Switch default core markup to output valid HTML5.
	 */
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
		)
	);

	/*
	 * Add theme support for selective refresh for widgets.
	 */
	add_theme_support( 'customize-selective-refresh-widgets' );

	/*
	 * Add support for core custom logo.
	 */
	add_theme_support(
		'custom-logo',
		array(
			'height'      => 100,
			'width'       => 400,
			'flex-width'  => true,
			'flex-height' => true,
		)
	);

	/*
	 * Add support for wide and full alignment.
	 */
	add_theme_support( 'align-wide' );

	/*
	 * Add support for editor styles.
	 */
	add_theme_support( 'editor-styles' );

	/*
	 * Add support for responsive embeds.
	 */
	add_theme_support( 'responsive-embeds' );

	/*
	 * Add support for custom line height controls.
	 */
	add_theme_support( 'custom-line-height' );

	/*
	 * Add support for custom spacing controls.
	 */
	add_theme_support( 'custom-spacing' );

	/*
	 * Add support for custom units.
	 */
	add_theme_support( 'custom-units' );

	/*
	 * Add support for WooCommerce.
	 */
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );

	/*
	 * Add support for Elementor.
	 */
	add_theme_support( 'elementor' );
}
add_action( 'after_setup_theme', 'skyyrose_setup' );

/**
 * Declare WooCommerce HPOS (High-Performance Order Storage) compatibility.
 *
 * This ensures compatibility with WooCommerce 8.5+ Custom Order Tables feature.
 *
 * @since 1.0.0
 */
function skyyrose_declare_woocommerce_hpos_compatibility() {
	if ( class_exists( '\Automattic\WooCommerce\Utilities\FeaturesUtil' ) ) {
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
			'custom_order_tables',
			__FILE__,
			true
		);
	}
}
add_action( 'before_woocommerce_init', 'skyyrose_declare_woocommerce_hpos_compatibility' );

/**
 * Set the content width in pixels, based on the theme's design and stylesheet.
 *
 * @since 1.0.0
 *
 * @global int $content_width
 */
function skyyrose_content_width() {
	$GLOBALS['content_width'] = apply_filters( 'skyyrose_content_width', 1200 );
}
add_action( 'after_setup_theme', 'skyyrose_content_width', 0 );

/**
 * Register widget areas.
 *
 * @since 1.0.0
 */
function skyyrose_widgets_init() {
	register_sidebar(
		array(
			'name'          => esc_html__( 'Primary Sidebar', 'skyyrose-flagship' ),
			'id'            => 'sidebar-1',
			'description'   => esc_html__( 'Add widgets here to appear in your sidebar.', 'skyyrose-flagship' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h2 class="widget-title">',
			'after_title'   => '</h2>',
		)
	);

	register_sidebar(
		array(
			'name'          => esc_html__( 'Footer Area 1', 'skyyrose-flagship' ),
			'id'            => 'footer-1',
			'description'   => esc_html__( 'Add widgets here to appear in your footer.', 'skyyrose-flagship' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h2 class="widget-title">',
			'after_title'   => '</h2>',
		)
	);

	register_sidebar(
		array(
			'name'          => esc_html__( 'Footer Area 2', 'skyyrose-flagship' ),
			'id'            => 'footer-2',
			'description'   => esc_html__( 'Add widgets here to appear in your footer.', 'skyyrose-flagship' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h2 class="widget-title">',
			'after_title'   => '</h2>',
		)
	);

	register_sidebar(
		array(
			'name'          => esc_html__( 'Footer Area 3', 'skyyrose-flagship' ),
			'id'            => 'footer-3',
			'description'   => esc_html__( 'Add widgets here to appear in your footer.', 'skyyrose-flagship' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h2 class="widget-title">',
			'after_title'   => '</h2>',
		)
	);

	register_sidebar(
		array(
			'name'          => esc_html__( 'Footer Area 4', 'skyyrose-flagship' ),
			'id'            => 'footer-4',
			'description'   => esc_html__( 'Add widgets here to appear in your footer.', 'skyyrose-flagship' ),
			'before_widget' => '<section id="%1$s" class="widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h2 class="widget-title">',
			'after_title'   => '</h2>',
		)
	);

	// WooCommerce sidebar.
	if ( class_exists( 'WooCommerce' ) ) {
		register_sidebar(
			array(
				'name'          => esc_html__( 'Shop Sidebar', 'skyyrose-flagship' ),
				'id'            => 'shop-sidebar',
				'description'   => esc_html__( 'Add widgets here to appear in your shop pages.', 'skyyrose-flagship' ),
				'before_widget' => '<section id="%1$s" class="widget %2$s">',
				'after_widget'  => '</section>',
				'before_title'  => '<h2 class="widget-title">',
				'after_title'   => '</h2>',
			)
		);
	}
}
add_action( 'widgets_init', 'skyyrose_widgets_init' );

/**
 * Enqueue scripts and styles.
 *
 * @since 1.0.0
 */
function skyyrose_scripts() {
	// Main stylesheet.
	wp_enqueue_style(
		'skyyrose-style',
		get_stylesheet_uri(),
		array(),
		SKYYROSE_VERSION
	);

	// Custom styles.
	wp_enqueue_style(
		'skyyrose-custom',
		SKYYROSE_ASSETS_URI . '/css/custom.css',
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);

	// Three.js library.
	wp_enqueue_script(
		'threejs',
		SKYYROSE_ASSETS_URI . '/three/three.min.js',
		array(),
		'r150',
		true
	);

	// Main theme JavaScript.
	wp_enqueue_script(
		'skyyrose-main',
		SKYYROSE_ASSETS_URI . '/js/main.js',
		array( 'jquery' ),
		SKYYROSE_VERSION,
		true
	);

	// Three.js initialization script.
	wp_enqueue_script(
		'skyyrose-three-init',
		SKYYROSE_ASSETS_URI . '/js/three-init.js',
		array( 'threejs' ),
		SKYYROSE_VERSION,
		true
	);

	// Navigation script.
	wp_enqueue_script(
		'skyyrose-navigation',
		SKYYROSE_ASSETS_URI . '/js/navigation.js',
		array( 'jquery' ),
		SKYYROSE_VERSION,
		true
	);

	// Comment reply script.
	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}

	// Localize script with theme data.
	wp_localize_script(
		'skyyrose-main',
		'skyyRoseData',
		array(
			'ajaxUrl'    => admin_url( 'admin-ajax.php' ),
			'nonce'      => wp_create_nonce( 'skyyrose-nonce' ),
			'themeUri'   => SKYYROSE_THEME_URI,
			'assetsUri'  => SKYYROSE_ASSETS_URI,
			'modelsPath' => SKYYROSE_ASSETS_URI . '/models/',
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_scripts' );

/**
 * Enqueue admin scripts and styles.
 *
 * @since 1.0.0
 */
function skyyrose_admin_scripts() {
	wp_enqueue_style(
		'skyyrose-admin',
		SKYYROSE_ASSETS_URI . '/css/admin.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_enqueue_script(
		'skyyrose-admin',
		SKYYROSE_ASSETS_URI . '/js/admin.js',
		array( 'jquery' ),
		SKYYROSE_VERSION,
		true
	);
}
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );

/**
 * Load modular includes.
 */
// Core functionality - load these only if files exist
$core_includes = array(
	'/inc/template-functions.php',
	'/inc/customizer.php',
	'/inc/accessibility-seo.php',
);

foreach ( $core_includes as $file ) {
	$filepath = SKYYROSE_THEME_DIR . $file;
	if ( file_exists( $filepath ) ) {
		require_once $filepath;
	}
}

// Load WooCommerce functions if active.
if ( class_exists( 'WooCommerce' ) ) {
	if ( file_exists( SKYYROSE_THEME_DIR . '/inc/woocommerce.php' ) ) {
		require_once SKYYROSE_THEME_DIR . '/inc/woocommerce.php';
	}
	if ( file_exists( SKYYROSE_THEME_DIR . '/inc/wishlist-functions.php' ) ) {
		require_once SKYYROSE_THEME_DIR . '/inc/wishlist-functions.php';
	}
	if ( file_exists( SKYYROSE_THEME_DIR . '/inc/class-wishlist-widget.php' ) ) {
		require_once SKYYROSE_THEME_DIR . '/inc/class-wishlist-widget.php';
	}
}

// Load Elementor functions if active.
add_action( 'elementor/loaded', function() {
	if ( file_exists( SKYYROSE_THEME_DIR . '/inc/elementor.php' ) ) {
		require_once SKYYROSE_THEME_DIR . '/inc/elementor.php';
	}
} );

/**
 * Security enhancements.
 *
 * @since 1.0.0
 */
function skyyrose_security_enhancements() {
	// Remove WordPress version from head.
	remove_action( 'wp_head', 'wp_generator' );

	// Remove RSD link.
	remove_action( 'wp_head', 'rsd_link' );

	// Remove wlwmanifest.xml.
	remove_action( 'wp_head', 'wlwmanifest_link' );

	// Remove shortlink.
	remove_action( 'wp_head', 'wp_shortlink_wp_head' );

	// Disable XML-RPC.
	add_filter( 'xmlrpc_enabled', '__return_false' );
}
add_action( 'init', 'skyyrose_security_enhancements' );

/**
 * Add custom body classes.
 *
 * @since 1.0.0
 *
 * @param array $classes Classes for the body element.
 * @return array Modified classes.
 */
function skyyrose_body_classes( $classes ) {
	// Add class if we're viewing the Customizer.
	if ( is_customize_preview() ) {
		$classes[] = 'customizer-preview';
	}

	// Add class for WooCommerce pages.
	if ( class_exists( 'WooCommerce' ) && is_woocommerce() ) {
		$classes[] = 'woocommerce-page';
	}

	// Add class for Elementor pages (with null checks to prevent fatal errors).
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

	// Add singular class.
	if ( is_singular() ) {
		$classes[] = 'singular';
	}

	return $classes;
}
add_filter( 'body_class', 'skyyrose_body_classes' );

/**
 * Add a pingback url auto-discovery header for singularly identifiable articles.
 *
 * @since 1.0.0
 */
function skyyrose_pingback_header() {
	if ( is_singular() && pings_open() ) {
		printf( '<link rel="pingback" href="%s">', esc_url( get_bloginfo( 'pingback_url' ) ) );
	}
}
add_action( 'wp_head', 'skyyrose_pingback_header' );

/**
 * Performance optimizations.
 *
 * @since 1.0.0
 */
function skyyrose_performance_optimizations() {
	// Defer JavaScript loading.
	add_filter(
		'script_loader_tag',
		function( $tag, $handle ) {
			$defer_scripts = array( 'skyyrose-main', 'skyyrose-navigation', 'skyyrose-three-init' );
			if ( in_array( $handle, $defer_scripts, true ) ) {
				return str_replace( ' src', ' defer src', $tag );
			}
			return $tag;
		},
		10,
		2
	);

	// Preload critical assets.
	add_action(
		'wp_head',
		function() {
			echo '<link rel="preconnect" href="https://fonts.googleapis.com">';
			echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>';
		},
		1
	);
}
add_action( 'init', 'skyyrose_performance_optimizations' );

/**
 * Register Wishlist Custom Post Type.
 *
 * @since 1.0.0
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
