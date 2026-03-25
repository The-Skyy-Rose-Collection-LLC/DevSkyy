<?php
/**
 * Plugin Name:       SkyyRose Virtual Experience
 * Plugin URI:        https://skyyrose.co
 * Description:       Registers the SkyyRose Experiences Landing page template and supporting functionality for immersive collection experiences.
 * Version:           1.0.0
 * Requires at least: 6.0
 * Requires PHP:      8.0
 * Author:            SkyyRose
 * Author URI:        https://skyyrose.co
 * License:           GPL-2.0-or-later
 * Text Domain:       skyyrose-virtual-experience
 *
 * @package SkyyRose_Virtual_Experience
 */

defined( 'ABSPATH' ) || exit;

define( 'SKYYROSE_VE_VERSION', '1.0.0' );
define( 'SKYYROSE_VE_DIR', plugin_dir_path( __FILE__ ) );
define( 'SKYYROSE_VE_URI', plugin_dir_url( __FILE__ ) );

/**
 * Register the Experiences Landing page template so WordPress recognises it
 * in the Page Attributes dropdown for any page.
 */
add_filter( 'theme_page_templates', 'skyyrose_ve_register_template' );
function skyyrose_ve_register_template( array $templates ): array {
	$templates[ SKYYROSE_VE_DIR . 'templates/template-experiences-landing.php' ] = __( 'SkyyRose Experiences Landing', 'skyyrose-virtual-experience' );
	return $templates;
}

/**
 * Tell WordPress where to load the template file from when the page
 * uses the "SkyyRose Experiences Landing" template.
 */
add_filter( 'template_include', 'skyyrose_ve_load_template' );
function skyyrose_ve_load_template( string $template ): string {
	if ( ! is_page() ) {
		return $template;
	}

	$page_template = get_page_template_slug( get_the_ID() );
	$plugin_template = SKYYROSE_VE_DIR . 'templates/template-experiences-landing.php';

	if ( $page_template === $plugin_template && file_exists( $plugin_template ) ) {
		return $plugin_template;
	}

	return $template;
}

/**
 * Activate: flush rewrite rules so /experience/ resolves correctly.
 */
register_activation_hook( __FILE__, 'skyyrose_ve_activate' );
function skyyrose_ve_activate(): void {
	flush_rewrite_rules();
}

/**
 * Deactivate: flush rewrite rules on removal.
 */
register_deactivation_hook( __FILE__, 'skyyrose_ve_deactivate' );
function skyyrose_ve_deactivate(): void {
	flush_rewrite_rules();
}
