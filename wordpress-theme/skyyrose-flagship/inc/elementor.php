<?php
/**
 * Elementor Integration
 *
 * Registers custom SkyyRose widgets, editor styles, frontend scripts,
 * and brand-correct default schemes for the Elementor page builder.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register Elementor locations.
 *
 * @since 1.0.0
 *
 * @param object $elementor_theme_manager Elementor theme manager.
 */
function skyyrose_register_elementor_locations( $elementor_theme_manager ) {
	$elementor_theme_manager->register_all_core_location();
}
add_action( 'elementor/theme/register_locations', 'skyyrose_register_elementor_locations' );

/**
 * Add Elementor support.
 *
 * @since 1.0.0
 */
function skyyrose_add_elementor_support() {
	add_theme_support( 'elementor' );
	add_theme_support( 'elementor-pro' );
}
add_action( 'after_setup_theme', 'skyyrose_add_elementor_support' );

/**
 * Register custom Elementor widgets.
 *
 * Uses the modern Elementor 3.5+ `register` hook and method.
 *
 * @since 1.0.0
 * @since 3.3.0 Migrated from deprecated widgets_registered / register_widget_type.
 *
 * @param \Elementor\Widgets_Manager $widgets_manager Elementor widgets manager.
 */
function skyyrose_register_elementor_widgets( $widgets_manager ) {
	$widget_dir = SKYYROSE_THEME_DIR . '/elementor/widgets';

	$widget_map = array(
		'three-viewer.php'     => 'SkyyRose_Three_Viewer_Widget',
		'product-card.php'     => 'SkyyRose_Product_Card_Widget',
		'collection-hero.php'  => 'SkyyRose_Collection_Hero_Widget',
		'featured-product.php' => 'SkyyRose_Featured_Product_Widget',
		'lookbook.php'         => 'SkyyRose_Lookbook_Widget',
		'newsletter.php'       => 'SkyyRose_Newsletter_Widget',
		'testimonials.php'     => 'SkyyRose_Testimonials_Widget',
		'preorder-cta.php'     => 'SkyyRose_Preorder_CTA_Widget',
	);

	foreach ( $widget_map as $file => $class ) {
		$path = $widget_dir . '/' . $file;
		if ( file_exists( $path ) ) {
			require_once $path;
			if ( class_exists( $class ) ) {
				$widgets_manager->register( new $class() );
			}
		}
	}
}
add_action( 'elementor/widgets/register', 'skyyrose_register_elementor_widgets' );

/**
 * Add custom Elementor widget categories.
 *
 * @since 1.0.0
 *
 * @param object $elements_manager Elementor elements manager.
 */
function skyyrose_add_elementor_widget_categories( $elements_manager ) {
	$elements_manager->add_category(
		'skyyrose',
		array(
			'title' => esc_html__( 'SkyyRose Widgets', 'skyyrose-flagship' ),
			'icon'  => 'fa fa-plug',
		)
	);

	$elements_manager->add_category(
		'skyyrose-3d',
		array(
			'title' => esc_html__( 'SkyyRose 3D', 'skyyrose-flagship' ),
			'icon'  => 'fa fa-cube',
		)
	);
}
add_action( 'elementor/elements/categories_registered', 'skyyrose_add_elementor_widget_categories' );

/**
 * Enqueue Elementor editor styles.
 *
 * @since 1.0.0
 */
function skyyrose_elementor_editor_styles() {
	wp_enqueue_style(
		'skyyrose-elementor-editor',
		SKYYROSE_ASSETS_URI . '/css/elementor-editor.css',
		array(),
		SKYYROSE_VERSION
	);
}
add_action( 'elementor/editor/after_enqueue_styles', 'skyyrose_elementor_editor_styles' );

/**
 * Enqueue Elementor frontend scripts.
 *
 * @since 1.0.0
 */
function skyyrose_elementor_frontend_scripts() {
	wp_enqueue_script(
		'skyyrose-elementor',
		SKYYROSE_ASSETS_URI . '/js/elementor-frontend.js',
		array( 'jquery', 'elementor-frontend' ),
		SKYYROSE_VERSION,
		true
	);

	wp_enqueue_style(
		'skyyrose-collection-v4',
		SKYYROSE_ASSETS_URI . '/css/collection-v4.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_enqueue_style(
		'skyyrose-design-tokens',
		SKYYROSE_ASSETS_URI . '/css/design-tokens.css',
		array(),
		SKYYROSE_VERSION
	);
}
add_action( 'elementor/frontend/after_enqueue_scripts', 'skyyrose_elementor_frontend_scripts' );

/**
 * Add custom Elementor conditions.
 *
 * @since 1.0.0
 *
 * @param object $conditions_manager Conditions manager.
 */
function skyyrose_add_elementor_conditions( $conditions_manager ) {
	// Add custom conditions here if needed.
}
add_action( 'elementor/theme/conditions/register', 'skyyrose_add_elementor_conditions' );

/**
 * Modify Elementor canvas page template.
 *
 * @since 1.0.0
 */
function skyyrose_elementor_canvas_content() {
	if ( ! class_exists( '\Elementor\Plugin' ) || ! \Elementor\Plugin::$instance || ! \Elementor\Plugin::$instance->preview ) {
		echo '<div class="elementor-canvas-wrapper">';
		return;
	}
	if ( ! \Elementor\Plugin::$instance->preview->is_preview_mode() ) {
		echo '<div class="elementor-canvas-wrapper">';
	}
}
add_action( 'elementor/page_templates/canvas/before_content', 'skyyrose_elementor_canvas_content' );

/**
 * Close Elementor canvas wrapper.
 *
 * @since 1.0.0
 */
function skyyrose_elementor_canvas_content_close() {
	if ( ! class_exists( '\Elementor\Plugin' ) || ! \Elementor\Plugin::$instance || ! \Elementor\Plugin::$instance->preview ) {
		echo '</div>';
		return;
	}
	if ( ! \Elementor\Plugin::$instance->preview->is_preview_mode() ) {
		echo '</div>';
	}
}
add_action( 'elementor/page_templates/canvas/after_content', 'skyyrose_elementor_canvas_content_close' );

/**
 * Set brand-correct Elementor default schemes.
 *
 * @since 1.0.0
 * @since 3.3.0 Updated to SkyyRose brand colors and typography.
 */
function skyyrose_set_elementor_default_schemes() {
	update_option(
		'elementor_scheme_color',
		array(
			'1' => '#0A0A0A', // Primary — dark base.
			'2' => '#B76E79', // Secondary — rose gold.
			'3' => '#FFFFFF', // Text — white on dark.
			'4' => '#D4AF37', // Accent — gold.
		)
	);

	update_option(
		'elementor_scheme_typography',
		array(
			'1' => array( // Primary Headline.
				'font_family' => 'Cinzel',
				'font_weight' => '900',
			),
			'2' => array( // Secondary Headline.
				'font_family' => 'Cinzel',
				'font_weight' => '700',
			),
			'3' => array( // Body Text.
				'font_family' => 'Inter',
				'font_weight' => '400',
			),
			'4' => array( // Accent / Labels.
				'font_family' => 'Bebas Neue',
				'font_weight' => '400',
			),
		)
	);
}
add_action( 'after_switch_theme', 'skyyrose_set_elementor_default_schemes' );

/**
 * Filter Elementor breakpoints.
 *
 * @since 1.0.0
 *
 * @param array $breakpoints Active breakpoints.
 * @return array Modified breakpoints.
 */
function skyyrose_elementor_breakpoints( $breakpoints ) {
	$breakpoints['mobile'] = 768;
	$breakpoints['tablet'] = 1024;

	return $breakpoints;
}
add_filter( 'elementor/breakpoints/get_breakpoints', 'skyyrose_elementor_breakpoints' );
