<?php
/**
 * Elementor Integration
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
	// Add theme support for Elementor.
	add_theme_support( 'elementor' );

	// Add Elementor Pro features.
	add_theme_support( 'elementor-pro' );
}
add_action( 'after_setup_theme', 'skyyrose_add_elementor_support' );

/**
 * Register custom Elementor widgets.
 *
 * @since 1.0.0
 */
function skyyrose_register_elementor_widgets() {
	// Include widget files.
	$widget_files = glob( SKYYROSE_THEME_DIR . '/elementor/widgets/*.php' );

	if ( $widget_files ) {
		foreach ( $widget_files as $widget_file ) {
			require_once $widget_file;
		}
	}
}
add_action( 'elementor/widgets/widgets_registered', 'skyyrose_register_elementor_widgets' );

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
	// Use minified assets in production.
	$suffix = ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ) ? '' : '.min';

	wp_enqueue_style(
		'skyyrose-elementor-editor',
		SKYYROSE_ASSETS_URI . '/css/elementor-editor' . $suffix . '.css',
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
	// Use minified assets in production.
	$suffix = ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ) ? '' : '.min';

	wp_enqueue_script(
		'skyyrose-elementor',
		SKYYROSE_ASSETS_URI . '/js/elementor-frontend' . $suffix . '.js',
		array( 'jquery', 'elementor-frontend' ),
		SKYYROSE_VERSION,
		true
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
	if ( ! \Elementor\Plugin::$instance->preview->is_preview_mode() ) {
		echo '</div>';
	}
}
add_action( 'elementor/page_templates/canvas/after_content', 'skyyrose_elementor_canvas_content_close' );

/**
 * Add default Elementor schemes.
 *
 * @since 1.0.0
 */
function skyyrose_set_elementor_default_schemes() {
	// Set default color scheme.
	update_option(
		'elementor_scheme_color',
		array(
			'1' => '#000000', // Primary.
			'2' => '#666666', // Secondary.
			'3' => '#333333', // Text.
			'4' => '#ffffff', // Accent.
		)
	);

	// Set default typography scheme.
	update_option(
		'elementor_scheme_typography',
		array(
			'1' => array( // Primary Headline.
				'font_family' => 'Roboto',
				'font_weight' => '700',
			),
			'2' => array( // Secondary Headline.
				'font_family' => 'Roboto',
				'font_weight' => '600',
			),
			'3' => array( // Body Text.
				'font_family' => 'Roboto',
				'font_weight' => '400',
			),
			'4' => array( // Accent Text.
				'font_family' => 'Roboto',
				'font_weight' => '500',
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
